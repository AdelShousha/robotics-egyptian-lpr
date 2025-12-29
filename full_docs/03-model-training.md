# Model Training

## Overview

The Egyptian License Plate Recognition system uses two custom-trained YOLOv10 models:

1. **License Plate Detection Model**: Locates the plate region within an image
2. **Arabic OCR Model**: Recognizes individual characters on the cropped plate

---

## Model Architecture Selection

### Why YOLOv10?

YOLOv10 was selected for this project due to:

- **Real-time Performance**: Optimized for fast inference suitable for edge deployment
- **Accuracy**: State-of-the-art detection accuracy for object detection tasks
- **Lightweight Variants**: Nano (n) variant suitable for resource-constrained environments
- **End-to-end Design**: NMS-free architecture reduces post-processing complexity

### Model Variant: YOLOv10n (Nano)

| Specification | Value |
|---------------|-------|
| Parameters | ~2.3M |
| FLOPs | ~8.2G |
| Input Size | 640×640 |
| Suitable For | Edge devices, real-time applications |

---

## Training Configuration

### Common Training Parameters

```
Epochs: 150 (Versions 1 & 2), 70 (Version 3)
Batch Size: 8
Input Resolution: 640×640
Patience: 10 (early stopping)
Optimizer: AdamW (default)
```

### Augmentation Override

All built-in augmentations were disabled during training to rely solely on dataset-level augmentation:

| Parameter | Value |
|-----------|-------|
| HSV Hue/Sat/Val | 0 |
| Rotation | 0 |
| Translation | 0 |
| Scale | 0 |
| Shear | 0 |
| Perspective | 0 |
| Flip (LR/UD) | 0 |
| Mosaic | 0 |
| Mixup | 0 |
| Copy-paste | 0 |

This approach ensured consistent comparison between the three dataset augmentation strategies.

---

## Model Versions Comparison

Three models were trained using different dataset augmentation versions:

### Performance Results

| Model Version | Precision | Recall | mAP@50 | mAP@50-95 |
|---------------|-----------|--------|--------|-----------|
| **Noise-Blur-Crop** | **0.9588** | **0.9398** | **0.9750** | **0.7494** |
| Rotation-Shear-Noise | 0.9396 | 0.9253 | 0.9664 | 0.7273 |
| Full Augmentation | 0.9214 | 0.9081 | 0.9565 | 0.5966 |

![Training Comparison Chart](./images/training-comparison-chart.png)
*Caption: Performance metrics comparison across the three model versions*

### Best Model Selection

**Winner: Noise-Blur-Crop (Version 1)**

This model achieved the highest scores across all metrics:
- Highest precision (95.88%)
- Highest recall (93.98%)
- Highest mAP@50 (97.50%)
- Highest mAP@50-95 (74.94%)

The simpler augmentation strategy (noise, blur, crop) outperformed more aggressive augmentations, suggesting that excessive transformations may have introduced too much variation for the relatively small dataset.

---

## Training Curves

![Loss Curves](./images/training-loss-curves.png)
*Caption: Training and validation loss curves for the best performing model*

![mAP Curves](./images/training-map-curves.png)
*Caption: mAP@50 and mAP@50-95 progression during training*

---

## Arabic OCR Model

### Purpose
The OCR model detects and classifies individual characters within the cropped license plate image.

### Character Classes

The model recognizes 26 classes (16 Arabic letters + 10 Arabic numerals):

#### Arabic Letters
| Class | Arabic | Unicode |
|-------|--------|---------|
| a | أ | U+0623 |
| b | ب | U+0628 |
| g | ج | U+062C |
| d | د | U+062F |
| r | ر | U+0631 |
| s | س | U+0633 |
| ss | ص | U+0635 |
| tt | ط | U+0637 |
| aa | ع | U+0639 |
| f | ف | U+0641 |
| kk | ق | U+0642 |
| l | ل | U+0644 |
| m | م | U+0645 |
| n | ن | U+0646 |
| 00 | ه | U+0647 |
| w | و | U+0648 |
| y | ى | U+0649 |

#### Arabic Numerals
| Class | Arabic | Unicode |
|-------|--------|---------|
| 0 | ٠ | U+0660 |
| 1 | ١ | U+0661 |
| 2 | ٢ | U+0662 |
| 3 | ٣ | U+0663 |
| 4 | ٤ | U+0664 |
| 5 | ٥ | U+0665 |
| 6 | ٦ | U+0666 |
| 7 | ٧ | U+0667 |
| 8 | ٨ | U+0668 |
| 9 | ٩ | U+0669 |

### Character Extraction Process

1. Crop license plate region from detection model
2. Resize to 640×640 for OCR model input
3. Detect individual character bounding boxes
4. Sort characters right-to-left (Arabic reading direction)
5. Map Latin predictions to Arabic Unicode
6. Validate 6-7 character requirement

![OCR Detection Example](./images/ocr-detection-example.png)
*Caption: OCR model output showing detected character bounding boxes with Arabic labels*

---

## Model Validation

### Egyptian Plate Format Validation

The system enforces Egyptian license plate standards:

- **Minimum Characters**: 6
- **Maximum Characters**: 7
- **Format**: Letters followed by numbers

Detections not meeting these criteria are flagged as invalid.

### Confidence Scoring

The overall plate confidence is calculated as the mean confidence of all detected characters:

```
Total Confidence = Average(char1_conf, char2_conf, ..., charN_conf)
```

---

## Detection Pipeline

The complete detection pipeline operates in three stages:

```
Input Image
    │
    ▼
┌─────────────────────────┐
│  Stage 1: Plate Detection │
│  Model: yolov10_license_plate_detection.pt │
│  Output: Plate bounding box │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│  Stage 2: Crop & Resize  │
│  Crop plate region       │
│  Resize to 640×640       │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│  Stage 3: OCR            │
│  Model: yolov10_Arabic_OCR.pt │
│  Output: Character detections │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│  Post-processing         │
│  Sort RTL, map to Arabic │
│  Validate format         │
└─────────────────────────┘
    │
    ▼
Final Output: Arabic plate text + confidence
```

---

## Model Files

| File | Purpose | Size |
|------|---------|------|
| `yolov10_license_plate_detection.pt` | Plate region detection | ~5MB |
| `yolov10_Arabic_OCR.pt` | Character recognition | ~5MB |

---

## Sample Detection Results

![Detection Sample 1](./images/detection-sample-1.png)
*Caption: Successful detection showing plate localization and character recognition*

![Detection Sample 2](./images/detection-sample-2.png)
*Caption: Detection under challenging lighting conditions*

![Detection Sample 3](./images/detection-sample-3.png)
*Caption: Detection with annotated character bounding boxes*
