# Hardware Setup

## Overview

The hardware system uses an ESP32-CAM microcontroller with an ultrasonic sensor to automatically detect approaching vehicles and capture license plate images. This creates a compact, portable demonstration unit for the recognition system.

![Hardware Assembly](./images/hardware-assembly-photo.png)
*Caption: Complete assembled hardware showing ESP32-CAM, ultrasonic sensor, and power supply*

---

## Components List

| Component | Model/Specification | Quantity |
|-----------|---------------------|----------|
| Microcontroller | ESP32-CAM (AI-Thinker) | 1 |
| Camera Module | OV2640 (included with ESP32-CAM) | 1 |
| Ultrasonic Sensor | HC-SR04 | 1 |
| Voltage Regulator | 7805 (5V output) | 1 |
| Batteries | 18650 Li-ion (3.7V each) | 2 |
| Battery Holder | 2-cell 18650 holder | 1 |
| Resistors | 1kΩ (1/4W) | 3 |
| FTDI Programmer | USB-to-Serial (for programming) | 1 |
| Breadboard | Standard size | 1 |
| Jumper Wires | Male-to-male, male-to-female | Various |

---

## Wiring Diagram

![Wiring Diagram](./images/wiring-diagram.png)
*Caption: Complete wiring diagram showing all connections between components*

---

## GPIO Pin Assignments

### ESP32-CAM Pinout

| GPIO | Function | Connection |
|------|----------|------------|
| GPIO 13 | TRIG Output | HC-SR04 TRIG pin |
| GPIO 12 | ECHO Input | HC-SR04 ECHO (via voltage divider) |
| GPIO 4 | Flash LED | Built-in (PWM controlled) |
| GPIO 0 | Boot Mode | GND for programming |
| U0R | Serial RX | FTDI TX |
| U0T | Serial TX | FTDI RX |
| 5V | Power Input | 7805 output |
| GND | Ground | Common ground |

### Camera Pins (Internal to ESP32-CAM)

| Pin | GPIO |
|-----|------|
| PWDN | 32 |
| RESET | -1 (not used) |
| XCLK | 0 |
| SIOD | 26 |
| SIOC | 27 |
| Y9-Y2 | 35, 34, 39, 36, 21, 19, 18, 5 |
| VSYNC | 25 |
| HREF | 23 |
| PCLK | 22 |

---

## Power Supply

### Battery Configuration

Two 18650 batteries connected in series provide approximately 7.4V (nominal):

```
Battery 1 (+) ─────┐
    3.7V           │
Battery 1 (-) ─────┼───── Battery 2 (+)
                   │          3.7V
                   └───── Battery 2 (-)
                              │
                         7.4V Total
```

### Voltage Regulator (7805)

The 7805 regulates the battery voltage down to stable 5V:

| Pin | Name | Connection |
|-----|------|------------|
| 1 | Input | Battery positive (~7.4V) |
| 2 | Ground | Common ground |
| 3 | Output | 5V to ESP32-CAM and HC-SR04 |

![7805 Pinout](./images/7805-pinout.png)
*Caption: 7805 voltage regulator pinout (front view)*

**Note**: The 7805 requires at least 7V input for stable 5V output. Ensure batteries are charged above 3.5V each.

---

## Ultrasonic Sensor (HC-SR04)

### Specifications

| Parameter | Value |
|-----------|-------|
| Operating Voltage | 5V DC |
| Operating Current | 15mA |
| Measuring Range | 2cm - 400cm |
| Resolution | 0.3cm |
| Trigger Input | 10µs TTL pulse |
| Echo Output | 5V TTL signal |

### Connections

| HC-SR04 Pin | Connection |
|-------------|------------|
| VCC | 5V rail |
| TRIG | GPIO 13 (direct) |
| ECHO | GPIO 12 (via voltage divider) |
| GND | Common ground |

---

## Voltage Divider Circuit

**Critical**: The HC-SR04 ECHO pin outputs 5V, but ESP32 GPIO pins are 3.3V tolerant. A voltage divider is required to protect the ESP32.

### Circuit Design

```
ECHO (5V) ──────┬─────[1kΩ]─────┬─────[1kΩ]────[1kΩ]───── GND
                │               │
                │               └──────► GPIO 12 (3.3V)
                │
           HC-SR04 ECHO
```

### Voltage Calculation

Using the voltage divider formula:

```
V_out = V_in × (R2 / (R1 + R2))
V_out = 5V × (2kΩ / (1kΩ + 2kΩ))
V_out = 5V × (2/3)
V_out = 3.33V ✓ (safe for ESP32)
```

Where:
- R1 = 1kΩ (between ECHO and GPIO)
- R2 = 2kΩ (two 1kΩ in series, between GPIO and GND)

![Voltage Divider](./images/voltage-divider-circuit.png)
*Caption: Voltage divider circuit for ECHO pin protection*

---

## Detection Logic

### Trigger Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Trigger Distance | 15 cm | Maximum distance to trigger capture |
| Minimum Distance | 2 cm | Ignore very close readings (noise) |
| Debounce Delay | 3000 ms | Wait between captures |

### Distance Calculation

The ultrasonic sensor measures time-of-flight:

```
Distance = (Duration × Speed of Sound) / 2
Distance = (Duration × 0.034 cm/µs) / 2
```

Speed of sound = 343 m/s = 0.0343 cm/µs

### Multi-Sample Averaging

Three readings are taken and averaged for stability:

```cpp
for (int i = 0; i < 3; i++) {
    long dist = measureDistance();
    if (dist > 0 && dist < 400) {
        totalDistance += dist;
        validReadings++;
    }
    delay(10);
}
long avgDistance = totalDistance / validReadings;
```

---

## Camera Configuration

### Resolution Settings

| Condition | Resolution | Quality | Frame Buffers |
|-----------|------------|---------|---------------|
| With PSRAM | SVGA (800×600) | 10 | 2 |
| Without PSRAM | VGA (640×480) | 12 | 1 |

### Flash LED Control

The built-in flash LED (GPIO 4) supports PWM brightness control:

| Brightness | PWM Value | Description |
|------------|-----------|-------------|
| Off | 0 | No flash |
| 25% | 64 | Dim |
| 50% | 128 | Medium |
| 75% | 192 | Bright |
| 100% | 255 | Maximum |

---

## Programming Mode

### FTDI Connection

To program the ESP32-CAM, connect an FTDI USB-to-Serial adapter:

| FTDI Pin | ESP32-CAM Pin |
|----------|---------------|
| TX | U0R (RX) |
| RX | U0T (TX) |
| GND | GND |
| VCC | Not connected* |

*ESP32-CAM is powered by batteries/7805, not FTDI

### Boot Mode

For programming, GPIO 0 must be held LOW:

1. Connect GPIO 0 to GND
2. Press RST button or power cycle
3. Upload code via Arduino IDE
4. Disconnect GPIO 0 from GND
5. Press RST to run program

---

## Camera Stream Server

The ESP32 runs a web server for live preview:

- **URL**: `http://<ESP32-IP>/stream`
- **Port**: 80
- **Format**: MJPEG stream

This allows real-time viewing of the camera feed for debugging and alignment.

---

## WiFi Configuration

### Connection Parameters

```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
```

### Auto-Reconnection

If WiFi disconnects, the system automatically attempts reconnection before each capture.

---

## Image Transmission

When an object is detected within range:

1. Flash LED turns on (100ms warm-up)
2. Camera captures JPEG image
3. Flash LED turns off
4. Image sent via HTTPS POST to API
5. Response parsed for plate number and confidence

### API Request

```
POST https://robotics-egyptian-lpr-production.up.railway.app/api/recognize
Content-Type: multipart/form-data

[JPEG image data]
```

---

## Assembly Photos

![Breadboard Layout](./images/breadboard-layout.png)
*Caption: Recommended breadboard component layout*

![Final Assembly](./images/final-assembly.png)
*Caption: Completed prototype ready for testing*

![Maket Setup](./images/maket-demonstration.png)
*Caption: Demonstration setup with toy car and Egyptian license plate*
