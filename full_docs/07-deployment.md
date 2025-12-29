# Deployment

## Overview

The Egyptian License Plate Recognition system is deployed across multiple cloud services for production operation:

| Service | Platform | Purpose |
|---------|----------|---------|
| Backend API | Railway | Image processing and ML inference |
| Dashboard | Railway | Real-time monitoring interface |
| Database | Neon | PostgreSQL data storage |
| Image Storage | Cloudinary | CDN for captured images |

![Deployment Architecture](./images/deployment-architecture.png)
*Caption: Cloud deployment architecture showing service connections*

---

## Railway Platform

Railway provides container-based hosting with automatic deployments from Git repositories.

### API Service

**URL**: `https://robotics-egyptian-lpr-production.up.railway.app`

#### Container Configuration

The API runs in a Docker container with the following setup:

```dockerfile
FROM python:3.11-slim

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and ML models
COPY api/ ./api/
COPY yolov10_license_plate_detection.pt .
COPY yolov10_Arabic_OCR.pt .

# Start server
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### Key Features

- **Auto-scaling**: Handles variable traffic loads
- **SSL/TLS**: Automatic HTTPS certificates
- **Environment Variables**: Secure secrets management
- **Logging**: Built-in request logging and monitoring

### Dashboard Service

The React dashboard is deployed as a static site:

- **Build Command**: `npm run build`
- **Output Directory**: `build/`
- **Framework**: Vite static site generation

---

## Neon PostgreSQL

Neon provides serverless PostgreSQL with:

- **Auto-suspend**: Database sleeps when inactive (cost savings)
- **Auto-scaling**: Compute scales with demand
- **Branching**: Database branches for development
- **Connection Pooling**: Efficient connection management

### Database Schema

```sql
CREATE TABLE detections (
    id SERIAL PRIMARY KEY,
    car_image VARCHAR(500),
    lp_image VARCHAR(500),
    lp_number VARCHAR(50),
    confidence FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Connection

The async PostgreSQL driver connects using:

```
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require
```

---

## Cloudinary CDN

Cloudinary handles image storage and delivery:

### Folder Structure

| Folder | Content |
|--------|---------|
| `lpr/cars` | Full vehicle images |
| `lpr/plates` | Annotated plate crops |

### Image Processing

- Automatic format optimization
- Responsive delivery
- Global CDN distribution
- Secure signed URLs

### Upload Flow

```
ESP32 captures image
        │
        ▼
FastAPI receives image
        │
        ▼
Process with YOLOv10
        │
        ▼
Upload to Cloudinary
        │
        ▼
Store URL in database
```

---

## Environment Configuration

### Required Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Neon | PostgreSQL connection string |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary | Account identifier |
| `CLOUDINARY_API_KEY` | Cloudinary | API authentication |
| `CLOUDINARY_API_SECRET` | Cloudinary | API secret key |
| `PORT` | Railway | Server port (auto-set) |
| `VITE_API_URL` | Dashboard | Backend API URL |

### Security Notes

- All secrets stored as Railway environment variables
- Database connections use SSL/TLS
- Cloudinary uploads use signed requests
- CORS configured for dashboard domain

---

## Service Communication

### Data Flow

```
┌──────────────┐     HTTPS      ┌──────────────┐
│   ESP32-CAM   │───────────────▶│  Railway API  │
└──────────────┘                 └──────┬───────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
            ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
            │   Cloudinary  │   │     Neon     │   │   Dashboard  │
            │   (Images)    │   │ (PostgreSQL) │   │   (React)    │
            └──────────────┘   └──────────────┘   └──────────────┘
```

### API Endpoints

| Endpoint | Method | Source | Purpose |
|----------|--------|--------|---------|
| `/api/recognize` | POST | ESP32 | Upload image for recognition |
| `/api/dashboard` | GET | Dashboard | Fetch detection records |

---

## Scaling Considerations

### Current Limits

| Resource | Limit |
|----------|-------|
| API Memory | 512MB |
| Request Timeout | 60 seconds |
| Database Connections | 100 pooled |
| Image Size | 10MB max |

### Performance Optimizations

- **Model Lazy Loading**: ML models loaded on first request
- **Connection Pooling**: Reuse database connections
- **Image Compression**: JPEG quality optimization
- **CDN Caching**: Static assets cached globally

---

## Monitoring

### Railway Dashboard

- Request logs and metrics
- Memory and CPU usage
- Deployment history
- Environment variable management

### Health Checks

The API provides a health endpoint:

```
GET /
Response: {"status": "ok", "message": "..."}
```

---

## Cost Structure

| Service | Pricing Model |
|---------|---------------|
| Railway | Usage-based (memory × time) |
| Neon | Free tier available, then usage-based |
| Cloudinary | Free tier (25GB), then storage + bandwidth |

---

## Deployment Diagram

![Full Deployment](./images/full-deployment-diagram.png)
*Caption: Complete deployment architecture with all services and connections*
