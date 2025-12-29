# Egyptian License Plate Recognition System

## Project Overview

This project presents a complete end-to-end solution for automatic Egyptian license plate recognition, combining IoT hardware with deep learning computer vision. The system detects vehicles using an ultrasonic sensor, captures images with an ESP32-CAM microcontroller, processes them through a cloud-based AI backend, and displays results on a real-time monitoring dashboard.

![Project Overview Diagram](./images/project-overview-diagram.png)
*Caption: High-level system architecture showing the flow from vehicle detection to dashboard display*

---

## Problem Statement

Egyptian license plates present unique challenges for automated recognition systems:

- **Arabic Script**: Plates contain Arabic letters and Eastern Arabic numerals (٠١٢٣٤٥٦٧٨٩)
- **Standardized Format**: Egyptian plates follow a specific 6-7 character format
- **Variable Conditions**: Real-world capture involves varying lighting, angles, and distances
- **Limited Datasets**: Few publicly available datasets exist for Egyptian plate recognition

---

## Solution Approach

Our solution combines three main technologies:

1. **IoT Hardware Layer**: ESP32-CAM with ultrasonic proximity detection for automatic vehicle sensing
2. **AI/ML Backend**: Custom-trained YOLOv10 models for plate detection and Arabic OCR
3. **Web Dashboard**: Real-time monitoring interface displaying all detected plates

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Hardware** | ESP32-CAM | Image capture and WiFi transmission |
| **Hardware** | HC-SR04 Ultrasonic | Vehicle proximity detection |
| **ML Framework** | YOLOv10 | License plate detection & character recognition |
| **Backend** | FastAPI (Python) | REST API for image processing |
| **Database** | PostgreSQL (Neon) | Detection records storage |
| **Storage** | Cloudinary | Image CDN hosting |
| **Frontend** | React + TypeScript | Real-time dashboard |
| **Deployment** | Railway | Cloud hosting platform |
| **Annotation** | Roboflow | Dataset labeling and augmentation |

---

## Project Components

![Components Diagram](./images/components-diagram.png)
*Caption: Visual breakdown of the four main project components*

### 1. Computer Vision & ML
- Custom dataset of 1,800 Egyptian license plate images
- YOLOv10 model trained for plate detection (97.5% mAP@50)
- Arabic OCR model for character recognition

### 2. Backend API
- FastAPI server handling image processing requests
- Three-stage detection pipeline (detect plate → crop → OCR)
- Async database operations with PostgreSQL

### 3. Hardware System
- ESP32-CAM microcontroller with OV2640 camera
- Ultrasonic sensor for automatic capture triggering
- Battery-powered portable operation

### 4. Monitoring Dashboard
- React-based real-time interface
- Live detection feed with 30-second auto-refresh
- Dark theme optimized for monitoring

---

## Live Deployments

| Service | URL |
|---------|-----|
| **API Backend** | https://robotics-egyptian-lpr-production.up.railway.app |
| **Dataset** | https://universe.roboflow.com/vguard-vxduz/egyptian-license-plate-detection |

---

## Key Achievements

- **95.88% Precision** in license plate detection
- **93.98% Recall** rate for plate localization
- **97.50% mAP@50** detection accuracy
- **Real-time Processing** with cloud-based inference
- **Arabic Character Support** for authentic Egyptian plates

---

## Documentation Structure

This documentation is organized into the following sections:

1. **Overview** (this document)
2. **Dataset Preparation** - Data collection and annotation process
3. **Model Training** - YOLOv10 training methodology and results
4. **Backend API** - FastAPI server architecture
5. **Dashboard** - React frontend implementation
6. **Hardware Setup** - ESP32-CAM circuit and connections
7. **Deployment** - Cloud infrastructure setup
8. **System Architecture** - Complete data flow and integration
