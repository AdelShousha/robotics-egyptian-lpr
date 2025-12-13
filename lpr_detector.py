"""
Egyptian License Plate Recognition - Local Testing Script

This script takes an image as input and:
1. Detects the license plate using YOLOv10
2. Recognizes Arabic characters using OCR model
3. Returns the plate number and annotated cropped image
"""

import cv2
import numpy as np
from ultralytics import YOLO
import supervision as sv
import os
from pathlib import Path


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
    """
    Sort detections by x-coordinate (right-to-left for Arabic) and return Arabic text.
    """
    if len(detections.xyxy) == 0:
        return ""

    # Get right x-coordinates for RTL ordering
    right_x_coords = detections.xyxy[:, 2]

    # Sort indices in descending order (rightmost first for RTL)
    sorted_indices = np.argsort(right_x_coords)[::-1]

    # Get sorted class names
    sorted_class_names = detections.data['class_name'][sorted_indices]

    # Map to Arabic characters
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

    def __init__(self,
                 lp_model_path: str = "yolov10_license_plate_detection.pt",
                 ocr_model_path: str = "yolov10_Arabic_OCR.pt"):
        """
        Initialize the recognizer with YOLO models.

        Args:
            lp_model_path: Path to license plate detection model
            ocr_model_path: Path to Arabic OCR model
        """
        print("Loading license plate detection model...")
        self.lp_model = YOLO(lp_model_path)
        print("Loading Arabic OCR model...")
        self.ocr_model = YOLO(ocr_model_path)
        print("Models loaded successfully!")

        # Annotators for visualization
        self.box_annotator = sv.BoxAnnotator(color=sv.Color.GREEN, thickness=2)
        self.label_annotator = sv.LabelAnnotator(color=sv.Color.GREEN, text_scale=0.5)

    def detect_license_plate(self, image: np.ndarray) -> tuple[np.ndarray | None, sv.Detections]:
        """
        Detect license plate in the image.

        Args:
            image: Input image as numpy array (BGR)

        Returns:
            Tuple of (cropped license plate image, detections)
        """
        results = self.lp_model(image)[0]
        detections = sv.Detections.from_ultralytics(results)

        if len(detections.xyxy) == 0:
            return None, detections

        # Get the detection with highest confidence
        best_idx = np.argmax(detections.confidence)
        x_min, y_min, x_max, y_max = detections.xyxy[best_idx].astype(int)

        # Crop the license plate
        lp_crop = image[y_min:y_max, x_min:x_max].copy()

        return lp_crop, detections

    def recognize_characters(self, lp_crop: np.ndarray) -> tuple[str, float, sv.Detections]:
        """
        Recognize characters in the license plate crop.

        Args:
            lp_crop: Cropped license plate image

        Returns:
            Tuple of (plate text in Arabic, confidence score, detections)
        """
        # Resize to model input size
        lp_resized = cv2.resize(lp_crop, (640, 640))

        # Run OCR
        results = self.ocr_model(lp_resized)[0]
        detections = sv.Detections.from_ultralytics(results)

        # Check validity
        is_valid = check_license_plate_validity(detections)
        if not is_valid:
            return "", -1.0, detections

        # Get Arabic text
        plate_text = get_sorted_class_names_in_arabic(detections)
        confidence = get_conf_level(detections)

        return plate_text, confidence, detections

    def create_annotated_crop(self, lp_crop: np.ndarray, detections: sv.Detections) -> np.ndarray:
        """
        Create an annotated image of the license plate with detected characters.

        Args:
            lp_crop: Cropped license plate image
            detections: OCR detections

        Returns:
            Annotated image
        """
        # Resize crop to match detection coordinates (640x640)
        annotated = cv2.resize(lp_crop.copy(), (640, 640))

        if len(detections.xyxy) == 0:
            return annotated

        # Create labels with Arabic characters
        labels = [map_prediction_to_arabic(name) for name in detections.data['class_name']]

        # Annotate
        annotated = self.box_annotator.annotate(scene=annotated, detections=detections)
        annotated = self.label_annotator.annotate(scene=annotated, detections=detections, labels=labels)

        return annotated

    def process_image(self, image_path: str) -> dict:
        """
        Process an image and return recognition results.

        Args:
            image_path: Path to the input image

        Returns:
            Dictionary containing:
            - success: bool
            - plate_text: str (Arabic characters)
            - confidence: float
            - annotated_crop: np.ndarray (annotated license plate image)
            - error: str (if any)
        """
        result = {
            "success": False,
            "plate_text": "",
            "confidence": 0.0,
            "annotated_crop": None,
            "error": None
        }

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            result["error"] = f"Could not load image: {image_path}"
            return result

        # Detect license plate
        lp_crop, lp_detections = self.detect_license_plate(image)
        if lp_crop is None:
            result["error"] = "No license plate detected in the image"
            return result

        # Recognize characters
        plate_text, confidence, ocr_detections = self.recognize_characters(lp_crop)
        if confidence < 0:
            result["error"] = "Could not recognize valid license plate (need 6-7 characters)"
            result["annotated_crop"] = self.create_annotated_crop(lp_crop, ocr_detections)
            return result

        # Create annotated crop
        annotated_crop = self.create_annotated_crop(lp_crop, ocr_detections)

        result["success"] = True
        result["plate_text"] = plate_text
        result["confidence"] = confidence
        result["annotated_crop"] = annotated_crop

        return result

    def process_image_array(self, image: np.ndarray) -> dict:
        """
        Process an image array and return recognition results.

        Args:
            image: Input image as numpy array (BGR)

        Returns:
            Same as process_image()
        """
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

        # Detect license plate
        lp_crop, lp_detections = self.detect_license_plate(image)
        if lp_crop is None:
            result["error"] = "No license plate detected in the image"
            return result

        # Recognize characters
        plate_text, confidence, ocr_detections = self.recognize_characters(lp_crop)
        if confidence < 0:
            result["error"] = "Could not recognize valid license plate (need 6-7 characters)"
            result["annotated_crop"] = self.create_annotated_crop(lp_crop, ocr_detections)
            return result

        # Create annotated crop
        annotated_crop = self.create_annotated_crop(lp_crop, ocr_detections)

        result["success"] = True
        result["plate_text"] = plate_text
        result["confidence"] = confidence
        result["annotated_crop"] = annotated_crop

        return result


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Egyptian License Plate Recognition")
    parser.add_argument("image", help="Path to input image")
    parser.add_argument("--output", "-o", help="Path to save annotated output image")
    parser.add_argument("--lp-model", default="yolov10_license_plate_detection.pt",
                        help="Path to license plate detection model")
    parser.add_argument("--ocr-model", default="yolov10_Arabic_OCR.pt",
                        help="Path to Arabic OCR model")

    args = parser.parse_args()

    # Initialize recognizer
    recognizer = LicensePlateRecognizer(
        lp_model_path=args.lp_model,
        ocr_model_path=args.ocr_model
    )

    # Process image
    result = recognizer.process_image(args.image)

    if result["success"]:
        print(f"\nLicense Plate: {result['plate_text']}")
        print(f"Confidence: {result['confidence']:.4f}")

        # Save output if specified
        if args.output:
            cv2.imwrite(args.output, result["annotated_crop"])
            print(f"Annotated image saved to: {args.output}")
        else:
            # Default output path
            input_path = Path(args.image)
            output_path = input_path.parent / f"{input_path.stem}_annotated{input_path.suffix}"
            cv2.imwrite(str(output_path), result["annotated_crop"])
            print(f"Annotated image saved to: {output_path}")
    else:
        print(f"\nError: {result['error']}")
        if result["annotated_crop"] is not None:
            # Save partial result
            input_path = Path(args.image)
            output_path = input_path.parent / f"{input_path.stem}_partial{input_path.suffix}"
            cv2.imwrite(str(output_path), result["annotated_crop"])
            print(f"Partial annotated image saved to: {output_path}")


if __name__ == "__main__":
    main()
