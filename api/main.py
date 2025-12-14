"""
Egyptian License Plate Recognition API

FastAPI backend for ESP32-CAM integration.
Accepts images and returns license plate recognition results.
"""

import cv2
import numpy as np
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
from contextlib import asynccontextmanager

# Import the LPR service
from lpr_service import LicensePlateRecognizer

# Import database functions
from database import (
    connect_db, disconnect_db, insert_detection,
    get_all_detections, get_vehicles_today_count, get_last_detection_time
)

# Import Cloudinary helper
from cloudinary_helper import upload_image

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    await connect_db()
    yield
    # Shutdown
    await disconnect_db()


app = FastAPI(
    title="Egyptian License Plate Recognition API",
    description="API for recognizing Egyptian license plates with Arabic characters",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global recognizer instance (lazy loaded)
recognizer: Optional[LicensePlateRecognizer] = None


class RecognitionResponse(BaseModel):
    """Response model for license plate recognition."""
    success: bool
    plate: str = ""
    confidence: float = 0.0
    error: Optional[str] = None


class DetectionItem(BaseModel):
    """Single detection record for dashboard."""
    id: int
    car_image: str
    lp_image: str
    lp_number: str
    confidence: float
    created_at: datetime


class DashboardResponse(BaseModel):
    """Response model for dashboard data."""
    vehicles_today: int
    last_detection: Optional[datetime] = None
    detections: List[DetectionItem]


def get_recognizer() -> LicensePlateRecognizer:
    """Get or create the recognizer instance (lazy loading)."""
    global recognizer
    if recognizer is None:
        # Try multiple locations for local model files
        script_dir = Path(__file__).parent
        parent_dir = script_dir.parent

        # Check parent directory first (development), then current directory (Docker/Railway)
        for base_dir in [parent_dir, script_dir, Path(".")]:
            lp_model = base_dir / "yolov10_license_plate_detection.pt"
            ocr_model = base_dir / "yolov10_Arabic_OCR.pt"

            if lp_model.exists() and ocr_model.exists():
                recognizer = LicensePlateRecognizer(
                    lp_model_path=str(lp_model),
                    ocr_model_path=str(ocr_model)
                )
                return recognizer

        raise RuntimeError("Model files not found. Please ensure yolov10_license_plate_detection.pt and yolov10_Arabic_OCR.pt are in the project directory.")
    return recognizer


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Egyptian License Plate Recognition API"}


@app.post("/api/recognize", response_model=RecognitionResponse)
async def recognize_plate(imageFile: UploadFile = File(...)):
    """
    Recognize license plate from uploaded image.

    Accepts multipart/form-data with an image file named 'imageFile'.
    Returns JSON with plate text and confidence. Stores result in database.
    """
    try:
        # Read image data
        contents = await imageFile.read()

        # Convert to numpy array
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return RecognitionResponse(
                success=False,
                error="Could not decode image"
            )

        # Get recognizer and process image
        rec = get_recognizer()
        result = rec.process_image_array(image)

        if result["success"]:
            # Upload images to Cloudinary
            car_image_url = upload_image(image, folder="lpr/cars")
            lp_image_url = ""
            if result["annotated_crop"] is not None:
                lp_image_url = upload_image(result["annotated_crop"], folder="lpr/plates")

            # Store URLs in database
            await insert_detection(
                car_image=car_image_url,
                lp_image=lp_image_url,
                lp_number=result["plate_text"],
                confidence=result["confidence"]
            )

            return RecognitionResponse(
                success=True,
                plate=result["plate_text"],
                confidence=result["confidence"]
            )
        else:
            return RecognitionResponse(
                success=False,
                error=result["error"]
            )

    except Exception as e:
        return RecognitionResponse(
            success=False,
            error=str(e)
        )


@app.post("/recognize")
async def recognize_plate_alt(imageFile: UploadFile = File(...)):
    """Alternative endpoint without /api prefix."""
    return await recognize_plate(imageFile)


@app.get("/api/dashboard", response_model=DashboardResponse)
async def get_dashboard_data():
    """
    Get dashboard data including all detections, today's count, and last detection time.

    Returns list of detections (newest first), vehicles detected today, and last detection timestamp.
    """
    detections = await get_all_detections()
    vehicles_today = await get_vehicles_today_count()
    last_detection = await get_last_detection_time()

    # Convert database rows to DetectionItem objects
    detection_items = [
        DetectionItem(
            id=d["id"],
            car_image=d["car_image"],
            lp_image=d["lp_image"],
            lp_number=d["lp_number"],
            confidence=d["confidence"],
            created_at=d["created_at"]
        )
        for d in detections
    ]

    return DashboardResponse(
        vehicles_today=vehicles_today,
        last_detection=last_detection,
        detections=detection_items
    )


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
