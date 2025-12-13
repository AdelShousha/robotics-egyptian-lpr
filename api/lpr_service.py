"""
License Plate Recognition Service Module

Core recognition logic for the FastAPI backend.
"""

import cv2
import numpy as np
from ultralytics import YOLO
import supervision as sv


# Arabic character mapping
ARABIC_MAPPING = {
    "a": "\u0623",   # أ
    "b": "\u0628",   # ب
    "kk": "\u0642",  # ق
    "ss": "\u0635",  # ص
    "s": "\u0633",   # س
    "tt": "\u0637",  # ط
    "o": "\u0639",   # ع
    "l": "\u0644",   # ل
    "r": "\u0631",   # ر
    "n": "\u0646",   # ن
    "m": "\u0645",   # م
    "00": "\u0647",  # ه
    "w": "\u0648",   # و
    "y": "\u0649",   # ى
    "g": "\u062c",   # ج
    "d": "\u062f",   # د
    "f": "\u0641",   # ف
    "1": "\u0661",   # ١
    "2": "\u0662",   # ٢
    "3": "\u0663",   # ٣
    "4": "\u0664",   # ٤
    "5": "\u0665",   # ٥
    "6": "\u0666",   # ٦
    "7": "\u0667",   # ٧
    "8": "\u0668",   # ٨
    "9": "\u0669",   # ٩
    "0": "\u0660",   # ٠
}


def map_prediction_to_arabic(letter: str) -> str:
    """Map Latin prediction to Arabic Unicode character."""
    return ARABIC_MAPPING.get(letter, "?")


def get_sorted_class_names_in_arabic(detections: sv.Detections) -> str:
    """Sort detections by x-coordinate (right-to-left for Arabic) and return Arabic text."""
    if len(detections.xyxy) == 0:
        return ""

    right_x_coords = detections.xyxy[:, 2]
    sorted_indices = np.argsort(right_x_coords)[::-1]
    sorted_class_names = detections.data['class_name'][sorted_indices]
    arabic_chars = [map_prediction_to_arabic(name) for name in sorted_class_names]

    return ' '.join(arabic_chars)


def check_license_plate_validity(detections: sv.Detections) -> bool:
    """Check if detection count is valid for Egyptian plates (6-7 characters)."""
    num_detections = len(detections.xyxy)
    return num_detections in {6, 7}


def get_conf_level(detections: sv.Detections) -> float:
    """Calculate average confidence level of detections."""
    if len(detections.confidence) == 0:
        return 0.0
    return float(detections.confidence.mean())


class LicensePlateRecognizer:
    """Egyptian License Plate Recognition class."""

    def __init__(self, lp_model_path: str, ocr_model_path: str):
        """
        Initialize the recognizer with YOLO models.

        Args:
            lp_model_path: Path to license plate detection model
            ocr_model_path: Path to OCR model
        """
        print(f"Loading license plate model from: {lp_model_path}")
        self.lp_model = YOLO(lp_model_path)
        print(f"Loading OCR model from: {ocr_model_path}")
        self.ocr_model = YOLO(ocr_model_path)
        print("Models loaded successfully!")

        self.box_annotator = sv.BoxAnnotator(color=sv.Color.GREEN, thickness=2)
        self.label_annotator = sv.LabelAnnotator(color=sv.Color.GREEN, text_scale=0.5)

    def detect_license_plate(self, image: np.ndarray):
        """Detect license plate in the image."""
        results = self.lp_model(image)[0]
        detections = sv.Detections.from_ultralytics(results)

        if len(detections.xyxy) == 0:
            return None, detections

        best_idx = np.argmax(detections.confidence)
        x_min, y_min, x_max, y_max = detections.xyxy[best_idx].astype(int)
        lp_crop = image[y_min:y_max, x_min:x_max].copy()

        return lp_crop, detections

    def recognize_characters(self, lp_crop: np.ndarray):
        """Recognize characters in the license plate crop."""
        lp_resized = cv2.resize(lp_crop, (640, 640))
        results = self.ocr_model(lp_resized)[0]
        detections = sv.Detections.from_ultralytics(results)

        is_valid = check_license_plate_validity(detections)
        if not is_valid:
            return "", -1.0, detections

        plate_text = get_sorted_class_names_in_arabic(detections)
        confidence = get_conf_level(detections)

        return plate_text, confidence, detections

    def create_annotated_crop(self, lp_crop: np.ndarray, detections: sv.Detections) -> np.ndarray:
        """Create an annotated image of the license plate with detected characters."""
        annotated = cv2.resize(lp_crop.copy(), (640, 640))

        if len(detections.xyxy) == 0:
            return annotated

        labels = [map_prediction_to_arabic(name) for name in detections.data['class_name']]
        annotated = self.box_annotator.annotate(scene=annotated, detections=detections)
        annotated = self.label_annotator.annotate(scene=annotated, detections=detections, labels=labels)

        return annotated

    def process_image_array(self, image: np.ndarray) -> dict:
        """Process an image array and return recognition results."""
        result = {
            "success": False,
            "plate_text": "",
            "confidence": 0.0,
            "annotated_crop": None,
            "error": None
        }

        if image is None:
            result["error"] = "Invalid image"
            return result

        lp_crop, lp_detections = self.detect_license_plate(image)
        if lp_crop is None:
            result["error"] = "No license plate detected in the image"
            return result

        plate_text, confidence, ocr_detections = self.recognize_characters(lp_crop)
        if confidence < 0:
            result["error"] = "Could not recognize valid license plate (need 6-7 characters)"
            result["annotated_crop"] = self.create_annotated_crop(lp_crop, ocr_detections)
            return result

        annotated_crop = self.create_annotated_crop(lp_crop, ocr_detections)

        result["success"] = True
        result["plate_text"] = plate_text
        result["confidence"] = confidence
        result["annotated_crop"] = annotated_crop

        return result
