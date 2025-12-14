"""
Cloudinary helper module for image uploads.

Handles uploading images to Cloudinary and returning URLs.
"""

import os
import cv2
import numpy as np
from pathlib import Path

# Load .env file for local development
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Configure Cloudinary
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
    api_key=os.environ.get("CLOUDINARY_API_KEY", ""),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", ""),
    secure=True
)

def is_cloudinary_configured() -> bool:
    """Check if Cloudinary credentials are configured."""
    return all([
        os.environ.get("CLOUDINARY_CLOUD_NAME"),
        os.environ.get("CLOUDINARY_API_KEY"),
        os.environ.get("CLOUDINARY_API_SECRET")
    ])


def upload_image(image: np.ndarray, folder: str = "lpr") -> str:
    """
    Upload an OpenCV image to Cloudinary.

    Args:
        image: OpenCV image (numpy array)
        folder: Cloudinary folder name

    Returns:
        URL of the uploaded image
    """
    if not is_cloudinary_configured():
        print("Cloudinary not configured, returning empty URL")
        return ""

    # Encode image to JPEG bytes
    _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    image_bytes = buffer.tobytes()

    # Upload to Cloudinary
    result = cloudinary.uploader.upload(
        image_bytes,
        folder=folder,
        resource_type="image"
    )

    return result.get("secure_url", "")
