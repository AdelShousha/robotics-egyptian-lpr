# Dataset Preparation

## Overview

The foundation of our Egyptian License Plate Recognition system is a custom dataset specifically created for Egyptian plates. This section documents the data collection, annotation, and augmentation processes.

---

## Dataset Statistics

| Metric | Value |
|--------|-------|
| **Total Images** | 1,800+ |
| **Annotation Type** | Bounding boxes |
| **Platform** | Roboflow |
| **Classes** | License plate region |
| **Format** | YOLOv10 compatible |

**Dataset Link**: [Egyptian License Plate Detection on Roboflow Universe](https://universe.roboflow.com/vguard-vxduz/egyptian-license-plate-detection)

---

## Data Collection Process

### Image Sources
Images were manually collected from various sources to ensure diversity:

- Different vehicle types (cars, trucks, buses, motorcycles)
- Various lighting conditions (daylight, evening, artificial lighting)
- Multiple angles and distances
- Different Egyptian governorates and plate styles

![Sample Dataset Images](./images/dataset-samples.png)
*Caption: Sample images from the collected dataset showing variety in angles, lighting, and plate types*

### Egyptian License Plate Characteristics

Egyptian license plates follow a standardized format:

- **Character Count**: 6-7 characters
- **Script**: Arabic letters and Eastern Arabic numerals
- **Layout**: Letters on left, numbers on right
- **Colors**: White background with blue/black text (private vehicles)

![Egyptian Plate Format](./images/egyptian-plate-format.png)
*Caption: Standard Egyptian license plate format showing character arrangement*

---

## Annotation Process

### Roboflow Annotation Tool

All 1,800 images were manually annotated using Roboflow's annotation interface:

1. **Bounding Box Annotation**: Each license plate region was marked with a rectangular bounding box
2. **Class Labeling**: Single class "license_plate" for detection
3. **Quality Control**: Manual review of all annotations for accuracy

![Annotation Example](./images/annotation-example.png)
*Caption: Roboflow annotation interface showing bounding box placement on a license plate*

### Annotation Guidelines

- Boxes tightly fit around the plate region
- Include slight padding for edge characters
- Mark partially visible plates when >50% visible
- Exclude severely occluded or blurry plates

---

## Dataset Augmentation

Three different augmentation strategies were tested to determine optimal training conditions:

### Version 1: Noise-Blur-Crop
| Augmentation | Value |
|--------------|-------|
| Crop | 0-20% zoom |
| Blur | Up to 1px |
| Noise | Up to 1.5% pixels |

### Version 2: Rotation-Shear-Noise
| Augmentation | Value |
|--------------|-------|
| Rotation | -10° to +10° |
| Shear | ±10° horizontal & vertical |
| Noise | Up to 1.5% pixels |

### Version 3: Full Augmentation
| Augmentation | Value |
|--------------|-------|
| Rotation | -10° to +10° |
| Shear | ±10° horizontal & vertical |
| Brightness | -20% to +20% |
| Exposure | -10% to +10% |
| Blur | Up to 1px |
| Noise | Up to 1.5% pixels |

![Augmentation Comparison](./images/augmentation-comparison.png)
*Caption: Visual comparison of the three augmentation strategies applied to the same source image*

---

## Dataset Split

The dataset was divided into training, validation, and test sets:

| Split | Percentage | Purpose |
|-------|------------|---------|
| **Training** | 70% | Model learning |
| **Validation** | 20% | Hyperparameter tuning |
| **Test** | 10% | Final evaluation |

---

## Arabic Character Dataset (OCR)

A separate dataset was prepared for the Arabic OCR model:

### Supported Characters

**Arabic Letters (16)**:
| Latin | Arabic | Name |
|-------|--------|------|
| a | أ | Alef |
| b | ب | Ba |
| g | ج | Jeem |
| d | د | Dal |
| r | ر | Ra |
| s | س | Seen |
| ss | ص | Sad |
| tt | ط | Ta |
| aa | ع | Ain |
| f | ف | Fa |
| kk | ق | Qaf |
| l | ل | Lam |
| m | م | Meem |
| n | ن | Noon |
| 00 | ه | Ha |
| w | و | Waw |
| y | ى | Ya |

**Arabic Numerals (10)**:
| Western | Arabic |
|---------|--------|
| 0 | ٠ |
| 1 | ١ |
| 2 | ٢ |
| 3 | ٣ |
| 4 | ٤ |
| 5 | ٥ |
| 6 | ٦ |
| 7 | ٧ |
| 8 | ٨ |
| 9 | ٩ |

---

## Data Quality Considerations

### Challenges Addressed
- **Blur**: Motion blur from moving vehicles
- **Occlusion**: Partial plate visibility
- **Lighting**: Shadows and reflections
- **Angle**: Perspective distortion
- **Distance**: Resolution variation

### Quality Metrics
- All images manually reviewed
- Minimum resolution requirements enforced
- Corrupt or unusable images removed
- Annotation consistency verified

![Quality Examples](./images/dataset-quality-examples.png)
*Caption: Examples of challenging images in the dataset - blur, occlusion, and lighting variations*
