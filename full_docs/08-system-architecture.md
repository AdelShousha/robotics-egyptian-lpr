# System Architecture

## Overview

The Egyptian License Plate Recognition system is a complete IoT-to-Cloud solution that combines edge hardware, machine learning, cloud services, and real-time visualization. This document describes the complete system architecture and data flow.

![System Architecture Overview](./images/system-architecture-overview.png)
*Caption: High-level system architecture showing all components and their interactions*

---

## Architecture Layers

### Layer 1: Edge Hardware (IoT)

The physical detection and capture system:

```
┌─────────────────────────────────────────────┐
│              HARDWARE LAYER                  │
│                                             │
│  ┌─────────────┐      ┌─────────────┐       │
│  │ HC-SR04     │      │ ESP32-CAM   │       │
│  │ Ultrasonic  │─────▶│ + OV2640    │       │
│  │ Sensor      │      │ Camera      │       │
│  └─────────────┘      └──────┬──────┘       │
│                              │              │
│                      ┌───────▼───────┐      │
│                      │ 7805 Voltage  │      │
│                      │ Regulator     │      │
│                      └───────┬───────┘      │
│                              │              │
│                      ┌───────▼───────┐      │
│                      │ 2x 18650      │      │
│                      │ Batteries     │      │
│                      └───────────────┘      │
└─────────────────────────────────────────────┘
```

**Functions**:
- Vehicle proximity detection (ultrasonic)
- Image capture (camera)
- WiFi transmission
- Local preview stream

---

### Layer 2: Cloud Backend (ML Processing)

The machine learning inference and API layer:

```
┌─────────────────────────────────────────────┐
│              BACKEND LAYER                   │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │          FastAPI Server              │    │
│  │                                      │    │
│  │  ┌────────────┐  ┌────────────┐     │    │
│  │  │ Plate      │  │ Arabic     │     │    │
│  │  │ Detection  │  │ OCR        │     │    │
│  │  │ YOLOv10    │  │ YOLOv10    │     │    │
│  │  └─────┬──────┘  └──────┬─────┘     │    │
│  │        │                │           │    │
│  │        └───────┬────────┘           │    │
│  │                │                    │    │
│  │        ┌───────▼───────┐            │    │
│  │        │  LPR Service  │            │    │
│  │        └───────────────┘            │    │
│  └─────────────────────────────────────┘    │
│                                             │
└─────────────────────────────────────────────┘
```

**Functions**:
- Image reception via REST API
- License plate detection
- Arabic character recognition
- Confidence scoring

---

### Layer 3: Data Persistence

Storage and database layer:

```
┌─────────────────────────────────────────────┐
│              STORAGE LAYER                   │
│                                             │
│  ┌──────────────────┐  ┌──────────────────┐ │
│  │    Cloudinary    │  │       Neon       │ │
│  │                  │  │                  │ │
│  │  ┌────────────┐  │  │  ┌────────────┐  │ │
│  │  │ Car Images │  │  │  │ Detections │  │ │
│  │  └────────────┘  │  │  │   Table    │  │ │
│  │  ┌────────────┐  │  │  └────────────┘  │ │
│  │  │Plate Crops │  │  │                  │ │
│  │  └────────────┘  │  │  PostgreSQL      │ │
│  │                  │  │                  │ │
│  │  CDN Delivery    │  │  Serverless      │ │
│  └──────────────────┘  └──────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

**Functions**:
- Image hosting (Cloudinary CDN)
- Detection records (PostgreSQL)
- Async database operations

---

### Layer 4: Presentation (Dashboard)

User interface layer:

```
┌─────────────────────────────────────────────┐
│            PRESENTATION LAYER                │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │         React Dashboard              │    │
│  │                                      │    │
│  │  ┌──────────┐  ┌──────────────────┐ │    │
│  │  │ Header   │  │ Detection Grid   │ │    │
│  │  │ Stats    │  │                  │ │    │
│  │  └──────────┘  │ ┌────┐ ┌────┐   │ │    │
│  │                │ │Card│ │Card│   │ │    │
│  │                │ └────┘ └────┘   │ │    │
│  │                │ ┌────┐ ┌────┐   │ │    │
│  │                │ │Card│ │Card│   │ │    │
│  │                │ └────┘ └────┘   │ │    │
│  │                └──────────────────┘ │    │
│  └─────────────────────────────────────┘    │
│                                             │
└─────────────────────────────────────────────┘
```

**Functions**:
- Real-time detection display
- Statistics and metrics
- Auto-refresh (30 seconds)

---

## Complete Data Flow

### End-to-End Process

```
 VEHICLE            ESP32-CAM           RAILWAY API          DATABASE         DASHBOARD
    │                   │                    │                   │                │
    │   Approaches      │                    │                   │                │
    │──────────────────▶│                    │                   │                │
    │                   │                    │                   │                │
    │               Ultrasonic               │                   │                │
    │               Detection                │                   │                │
    │                   │                    │                   │                │
    │               Distance < 15cm          │                   │                │
    │                   │                    │                   │                │
    │               Capture Image            │                   │                │
    │                   │                    │                   │                │
    │                   │  POST /recognize   │                   │                │
    │                   │───────────────────▶│                   │                │
    │                   │                    │                   │                │
    │                   │              Detect Plate              │                │
    │                   │              Run OCR                   │                │
    │                   │                    │                   │                │
    │                   │                    │  Upload Images    │                │
    │                   │                    │──────────────────▶│ (Cloudinary)   │
    │                   │                    │                   │                │
    │                   │                    │  Store Record     │                │
    │                   │                    │──────────────────▶│ (PostgreSQL)   │
    │                   │                    │                   │                │
    │                   │  Response          │                   │                │
    │                   │◀───────────────────│                   │                │
    │                   │                    │                   │                │
    │                   │                    │                   │ GET /dashboard │
    │                   │                    │                   │◀───────────────│
    │                   │                    │                   │                │
    │                   │                    │                   │  Return Data   │
    │                   │                    │                   │───────────────▶│
    │                   │                    │                   │                │
    │                   │                    │                   │          Display
    │                   │                    │                   │          Detection
    │                   │                    │                   │                │
```

---

## Detection Pipeline Detail

### Three-Stage ML Processing

```
Input Image (from ESP32)
         │
         ▼
┌────────────────────────┐
│   STAGE 1: Detection   │
│                        │
│   YOLOv10 License      │
│   Plate Detection      │
│                        │
│   Output: Bounding box │
│   of plate region      │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│   STAGE 2: Crop        │
│                        │
│   Extract plate region │
│   Resize to 640×640    │
│                        │
│   Output: Plate crop   │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│   STAGE 3: OCR         │
│                        │
│   YOLOv10 Arabic OCR   │
│   Detect characters    │
│   Sort right-to-left   │
│   Map to Arabic        │
│                        │
│   Output: Arabic text  │
│   + confidence score   │
└───────────┬────────────┘
            │
            ▼
    Final Result
    "أ ب ج ١ ٢ ٣"
    Confidence: 95.2%
```

---

## Technology Integration

### Communication Protocols

| Connection | Protocol | Security |
|------------|----------|----------|
| ESP32 → API | HTTPS | TLS 1.3 |
| API → Database | PostgreSQL | SSL |
| API → Cloudinary | HTTPS | API Key |
| Dashboard → API | HTTPS | CORS |

### Data Formats

| Transfer | Format |
|----------|--------|
| Image Upload | Multipart Form (JPEG) |
| API Response | JSON |
| Database | SQL |
| Dashboard Data | JSON |

---

## Technology Stack Summary

![Technology Stack](./images/technology-stack-diagram.png)
*Caption: Complete technology stack visualization*

### By Category

| Category | Technologies |
|----------|--------------|
| **Hardware** | ESP32-CAM, HC-SR04, 7805, 18650 |
| **ML/AI** | YOLOv10, Ultralytics, OpenCV |
| **Backend** | FastAPI, Python, Uvicorn |
| **Database** | PostgreSQL, Neon, AsyncPG |
| **Storage** | Cloudinary CDN |
| **Frontend** | React, TypeScript, Vite, Tailwind |
| **Deployment** | Railway, Docker |
| **Annotation** | Roboflow |

---

## System Characteristics

### Performance Metrics

| Metric | Value |
|--------|-------|
| Detection Accuracy | 97.5% mAP@50 |
| OCR Precision | 95.88% |
| End-to-end Latency | ~2-3 seconds |
| Dashboard Refresh | 30 seconds |

### Reliability Features

- WiFi auto-reconnection
- Database connection pooling
- Image fallback handling
- Error state recovery

### Scalability Points

- Horizontal API scaling (Railway)
- Database auto-scaling (Neon)
- CDN global distribution (Cloudinary)
- Stateless API design

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     EGYPTIAN LICENSE PLATE RECOGNITION                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────┐                                    ┌───────────────┐    │
│   │               │           WiFi/Internet            │               │    │
│   │   ESP32-CAM   │═══════════════════════════════════▶│  Railway API  │    │
│   │ + Ultrasonic  │           POST /recognize          │   (FastAPI)   │    │
│   │               │                                    │               │    │
│   └───────────────┘                                    └───────┬───────┘    │
│          │                                                     │            │
│          │ Camera                                              │            │
│          │ Stream                              ┌───────────────┼───────┐    │
│          ▼                                     │               │       │    │
│   ┌───────────────┐                    ┌───────▼─────┐ ┌───────▼─────┐│    │
│   │  Local Debug  │                    │ Cloudinary  │ │    Neon     ││    │
│   │  http://IP/   │                    │   (CDN)     │ │ PostgreSQL  ││    │
│   └───────────────┘                    └─────────────┘ └─────────────┘│    │
│                                                │               │       │    │
│                                                └───────────────┼───────┘    │
│                                                                │            │
│                                                        ┌───────▼───────┐    │
│                                                        │   Dashboard   │    │
│                                                        │   (React)     │    │
│                                                        │               │    │
│                                                        │ GET /dashboard│    │
│                                                        └───────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Demonstration Setup

The project is demonstrated using a miniature maket (model):

![Maket Setup](./images/demonstration-maket.png)
*Caption: Demonstration maket showing toy car with Egyptian license plate approaching the sensor*

**Components**:
- Toy car with printed Egyptian license plate
- ESP32-CAM mounted at plate level
- Ultrasonic sensor positioned to detect approaching vehicles
- Battery-powered portable operation

This allows showcasing the complete detection flow without requiring actual vehicles.
