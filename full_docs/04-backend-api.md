# Backend API

## Overview

The backend is built with FastAPI, a modern Python web framework optimized for building APIs. It handles image processing, license plate recognition, database storage, and serves data to the dashboard.

**Production URL**: `https://robotics-egyptian-lpr-production.up.railway.app`

---

## Architecture

![Backend Architecture](./images/backend-architecture.png)
*Caption: FastAPI backend architecture showing component interactions*

### Core Components

| Component | Responsibility |
|-----------|----------------|
| **FastAPI App** | HTTP request handling, routing |
| **LPR Service** | License plate detection and OCR |
| **Database Module** | PostgreSQL async operations |
| **Cloudinary Helper** | Image upload to CDN |

---

## API Endpoints

### Health Check

```
GET /
```

Returns server status confirmation.

**Response**:
```json
{
  "status": "ok",
  "message": "Egyptian License Plate Recognition API"
}
```

---

### License Plate Recognition

```
POST /api/recognize
```

Processes an uploaded image and returns detected license plate information.

**Request**: Multipart form data with image file

**Response**:
```json
{
  "success": true,
  "plate": "أ ب ج ١ ٢ ٣",
  "confidence": 0.95,
  "image_url": "https://cloudinary.com/...",
  "error": null
}
```

**Processing Flow**:
1. Receive image as multipart form data
2. Decode image to numpy array
3. Run through LPR detection pipeline
4. Upload car image and plate crop to Cloudinary
5. Store detection record in PostgreSQL
6. Return results to client

---

### Dashboard Data

```
GET /api/dashboard
```

Retrieves all detection records for dashboard display.

**Response**:
```json
{
  "vehicles_today": 42,
  "last_detection": "2024-12-24T15:30:45.123Z",
  "detections": [
    {
      "id": 1,
      "car_image": "https://cloudinary.com/car_123.jpg",
      "lp_image": "https://cloudinary.com/plate_123.jpg",
      "lp_number": "أ ب ج ١ ٢ ٣",
      "confidence": 0.95,
      "created_at": "2024-12-24T15:30:45.123Z"
    }
  ]
}
```

---

## License Plate Recognition Service

The LPR service implements the three-stage detection pipeline.

### Detection Pipeline

```
Image Input
    │
    ▼
┌────────────────────────────┐
│  1. License Plate Detection │
│  YOLOv10 model detects      │
│  plate bounding box         │
└────────────────────────────┘
    │
    ▼
┌────────────────────────────┐
│  2. Crop & Preprocess       │
│  Extract plate region       │
│  Resize to 640×640          │
└────────────────────────────┘
    │
    ▼
┌────────────────────────────┐
│  3. Arabic OCR              │
│  Detect individual chars    │
│  Map to Arabic Unicode      │
│  Sort right-to-left         │
└────────────────────────────┘
    │
    ▼
Output: Plate text + confidence
```

### Arabic Character Mapping

The OCR model outputs Latin class names that are mapped to Arabic Unicode:

```python
ARABIC_MAP = {
    'a': 'أ', 'b': 'ب', 'g': 'ج', 'd': 'د',
    'r': 'ر', 's': 'س', 'ss': 'ص', 'tt': 'ط',
    'aa': 'ع', 'f': 'ف', 'kk': 'ق', 'l': 'ل',
    'm': 'م', 'n': 'ن', '00': 'ه', 'w': 'و', 'y': 'ى',
    '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
    '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
}
```

### Plate Validation

Egyptian plates must contain 6-7 characters. Detections outside this range are flagged as invalid.

---

## Database Integration

### PostgreSQL with Neon

The system uses Neon's serverless PostgreSQL for persistent storage.

### Detection Record Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `car_image` | String | Cloudinary URL of vehicle image |
| `lp_image` | String | Cloudinary URL of plate crop |
| `lp_number` | String | Detected Arabic plate text |
| `confidence` | Float | Detection confidence (0-1) |
| `created_at` | DateTime | Timestamp (Egypt timezone UTC+2) |

### Database Operations

- **Insert Detection**: Store new plate recognition results
- **Get All Detections**: Retrieve records ordered by newest first
- **Count Today's Vehicles**: Count detections from current day
- **Get Last Detection Time**: Retrieve most recent timestamp

---

## Image Storage

### Cloudinary CDN

Processed images are uploaded to Cloudinary for persistent storage:

| Folder | Content |
|--------|---------|
| `lpr/cars` | Full vehicle images |
| `lpr/plates` | Cropped plate images with annotations |

**Benefits**:
- Global CDN for fast image delivery
- Automatic image optimization
- Secure HTTPS URLs
- No local storage requirements

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `python-multipart` | Form data parsing |
| `ultralytics` | YOLOv10 models |
| `opencv-python-headless` | Image processing |
| `numpy` | Array operations |
| `supervision` | Detection utilities |
| `asyncpg` | Async PostgreSQL driver |
| `databases` | Database abstraction |
| `cloudinary` | Image upload SDK |
| `python-dotenv` | Environment variables |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary account name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `PORT` | Server port (default: 8000) |

---

## Request Flow Diagram

![API Request Flow](./images/api-request-flow.png)
*Caption: Complete request flow from image upload to response*

```
ESP32-CAM                    FastAPI Backend
    │                              │
    │  POST /api/recognize         │
    │  [image file]                │
    │─────────────────────────────▶│
    │                              │
    │                     ┌────────┴────────┐
    │                     │ Decode Image    │
    │                     │ Run Detection   │
    │                     │ Run OCR         │
    │                     │ Upload Images   │
    │                     │ Store in DB     │
    │                     └────────┬────────┘
    │                              │
    │  Response JSON               │
    │  {success, plate, conf}      │
    │◀─────────────────────────────│
    │                              │
```
