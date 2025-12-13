"""
Egyptian License Plate Recognition API

FastAPI backend for ESP32-CAM integration.
Accepts images and returns license plate recognition results.
"""

import base64
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

# Import the LPR service
from lpr_service import LicensePlateRecognizer

app = FastAPI(
    title="Egyptian License Plate Recognition API",
    description="API for recognizing Egyptian license plates with Arabic characters",
    version="1.0.0"
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
    image_url: str = ""
    error: Optional[str] = None


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


def image_to_base64(image: np.ndarray) -> str:
    """Convert OpenCV image to base64 data URL."""
    _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    base64_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_str}"


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Egyptian License Plate Recognition API"}


@app.post("/api/recognize", response_model=RecognitionResponse)
async def recognize_plate(imageFile: UploadFile = File(...)):
    """
    Recognize license plate from uploaded image.

    Accepts multipart/form-data with an image file named 'imageFile'.
    Returns JSON with plate text, confidence, and annotated image as base64.
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
            # Convert annotated crop to base64
            image_url = ""
            if result["annotated_crop"] is not None:
                image_url = image_to_base64(result["annotated_crop"])

            return RecognitionResponse(
                success=True,
                plate=result["plate_text"],
                confidence=result["confidence"],
                image_url=image_url
            )
        else:
            # Include partial image if available
            image_url = ""
            if result["annotated_crop"] is not None:
                image_url = image_to_base64(result["annotated_crop"])

            return RecognitionResponse(
                success=False,
                error=result["error"],
                image_url=image_url
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


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
