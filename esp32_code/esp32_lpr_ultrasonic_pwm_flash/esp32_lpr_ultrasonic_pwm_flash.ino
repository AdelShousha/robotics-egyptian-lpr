/*
 * Egyptian License Plate Recognition - ESP32-CAM with Ultrasonic Sensor
 * VERSION: PWM Flash Control (Adjustable Brightness)
 *
 * Hardware:
 * - ESP32-CAM (AI-Thinker) with OV2640 camera
 * - HC-SR04 Ultrasonic sensor
 * - FTDI USB-to-Serial for programming
 * - 2x 18650 batteries in series + 7805 regulator for 5V power
 *
 * Connections:
 * - Ultrasonic TRIG: GPIO13
 * - Ultrasonic ECHO: GPIO12 (through voltage divider 5V->3.3V)
 * - Flash LED: GPIO4 (built-in)
 *
 * IMPORTANT: Use voltage divider on ECHO pin!
 * Echo (5V) --[1kΩ]--+--[2kΩ]-- GND
 *                    |
 *                    +---> GPIO12
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>
#include "esp_http_server.h"

// =============================================================================
// CONFIGURATION - MODIFY THESE VALUES
// =============================================================================

// WiFi credentials
const char* ssid = "SHome";
const char* password = "SHSH@1414#";

// API Server - Change this to your deployed server URL
// For local testing: "http://192.168.1.100:8000"
// For Vercel/Railway: "https://your-app.vercel.app" or "https://your-app.railway.app"
String serverName = "https://robotics-egyptian-lpr-production.up.railway.app";
String serverPath = "/api/recognize";

// Ultrasonic sensor pins
#define TRIG_PIN 13 // 5v
#define ECHO_PIN 12 // 3.3v

// Detection settings
#define TRIGGER_DISTANCE_CM 15    // Trigger when object is within this distance (cm)
#define MIN_DISTANCE_CM 2         // Minimum valid distance (ignore very close readings)
#define DEBOUNCE_DELAY_MS 3000    // Wait time between captures (milliseconds)

// Flash LED
#define FLASH_PIN 4
#define FLASH_BRIGHTNESS 64       // Flash brightness: 0-255 (0=off, 64=25%, 128=50%, 192=75%, 255=100%)

// =============================================================================
// CAMERA PIN DEFINITIONS (AI-Thinker ESP32-CAM)
// =============================================================================

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// =============================================================================
// GLOBAL VARIABLES
// =============================================================================

unsigned long lastCaptureTime = 0;
bool wifiConnected = false;

// =============================================================================
// SETUP FUNCTIONS
// =============================================================================

void setupCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // Use higher resolution for better plate recognition
  if (psramFound()) {
    config.frame_size = FRAMESIZE_SVGA;  // 800x600
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_VGA;   // 640x480
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  // Initialize camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return;
  }

  Serial.println("Camera initialized successfully!");
}

void setupWiFi() {
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
  }
}

void setupUltrasonic() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);
  Serial.println("Ultrasonic sensor initialized");
}

void setupFlash() {
  // Setup PWM for flash control (ESP32 Arduino Core 3.x API)
  ledcAttach(FLASH_PIN, 5000, 8);  // Pin, 5kHz frequency, 8-bit resolution (0-255)
  ledcWrite(FLASH_PIN, 0);  // Start with flash off
  Serial.println("Flash PWM initialized (adjustable brightness)");
}

// =============================================================================
// ULTRASONIC FUNCTIONS
// =============================================================================

long measureDistance() {
  // Send trigger pulse
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Read echo pulse duration
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms timeout

  // Calculate distance in cm
  // Speed of sound = 343 m/s = 0.0343 cm/µs
  // Distance = (duration * 0.0343) / 2
  long distance = duration * 0.034 / 2;

  return distance;
}

bool isObjectDetected() {
  // Take multiple readings for stability
  long totalDistance = 0;
  int validReadings = 0;

  for (int i = 0; i < 3; i++) {
    long dist = measureDistance();
    if (dist > 0 && dist < 400) {  // Valid range: 0-400cm
      totalDistance += dist;
      validReadings++;
    }
    delay(10);
  }

  if (validReadings == 0) {
    return false;
  }

  long avgDistance = totalDistance / validReadings;

  Serial.print("Distance: ");
  Serial.print(avgDistance);
  Serial.println(" cm");

  // Check if object is within trigger range
  return (avgDistance >= MIN_DISTANCE_CM && avgDistance <= TRIGGER_DISTANCE_CM);
}

// =============================================================================
// CAMERA AND API FUNCTIONS
// =============================================================================

void flashOn() {
  ledcWrite(FLASH_PIN, FLASH_BRIGHTNESS);  // Set to configured brightness
}

void flashOff() {
  ledcWrite(FLASH_PIN, 0);  // Turn off
}

String captureAndSendImage() {
  // Turn on flash for better image
  flashOn();
  delay(100);

  // Capture image
  camera_fb_t* fb = esp_camera_fb_get();
  flashOff();

  if (!fb) {
    Serial.println("Camera capture failed!");
    return "";
  }

  Serial.printf("Image captured: %d bytes\n", fb->len);

  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected, reconnecting...");
    setupWiFi();
    if (!wifiConnected) {
      esp_camera_fb_return(fb);
      return "";
    }
  }

  // Send to API
  String response = sendImageToAPI(fb);

  // Release frame buffer
  esp_camera_fb_return(fb);

  return response;
}

String sendImageToAPI(camera_fb_t* fb) {
  WiFiClientSecure client;
  client.setInsecure();  // Skip certificate verification for HTTPS

  HTTPClient http;

  String fullURL = serverName + serverPath;
  Serial.println("Sending to: " + fullURL);

  http.begin(client, fullURL);
  http.addHeader("Content-Type", "multipart/form-data; boundary=CircuitDigest");

  // Build multipart form data
  String filename = "plate_" + String(millis()) + ".jpg";
  String head = "--CircuitDigest\r\n";
  head += "Content-Disposition: form-data; name=\"imageFile\"; filename=\"" + filename + "\"\r\n";
  head += "Content-Type: image/jpeg\r\n\r\n";
  String tail = "\r\n--CircuitDigest--\r\n";

  uint32_t imageLen = fb->len;
  uint32_t extraLen = head.length() + tail.length();
  uint32_t totalLen = imageLen + extraLen;

  // Create buffer for the complete request body
  uint8_t* requestBody = (uint8_t*)malloc(totalLen);
  if (!requestBody) {
    Serial.println("Failed to allocate memory for request");
    http.end();
    return "";
  }

  // Copy head
  memcpy(requestBody, head.c_str(), head.length());
  // Copy image data
  memcpy(requestBody + head.length(), fb->buf, imageLen);
  // Copy tail
  memcpy(requestBody + head.length() + imageLen, tail.c_str(), tail.length());

  // Send POST request
  int httpResponseCode = http.POST(requestBody, totalLen);
  free(requestBody);

  String response = "";

  if (httpResponseCode > 0) {
    Serial.printf("HTTP Response code: %d\n", httpResponseCode);
    response = http.getString();
    Serial.println("Response: " + response);

    // Parse JSON response
    parseResponse(response);
  } else {
    Serial.printf("HTTP Error: %s\n", http.errorToString(httpResponseCode).c_str());
  }

  http.end();
  return response;
}

void parseResponse(String response) {
  // Parse JSON response
  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, response);

  if (error) {
    Serial.print("JSON parsing failed: ");
    Serial.println(error.c_str());
    return;
  }

  bool success = doc["success"];
  const char* plate = doc["plate"];
  float confidence = doc["confidence"];
  const char* imageUrl = doc["image_url"];
  const char* errorMsg = doc["error"];

  Serial.println("=================================");
  if (success) {
    Serial.println("License Plate Recognized!");
    Serial.print("Plate: ");
    Serial.println(plate);
    Serial.print("Confidence: ");
    Serial.print(confidence * 100, 1);
    Serial.println("%");
    if (imageUrl && strlen(imageUrl) > 0) {
      Serial.println("Image URL available (base64)");
    }
  } else {
    Serial.println("Recognition failed");
    if (errorMsg) {
      Serial.print("Error: ");
      Serial.println(errorMsg);
    }
  }
  Serial.println("=================================");
}

// =============================================================================
// CAMERA STREAM SERVER
// =============================================================================

#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

httpd_handle_t stream_httpd = NULL;

static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = NULL;
  esp_err_t res = ESP_OK;
  char *part_buf[64];

  res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
  if (res != ESP_OK) {
    return res;
  }

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      res = ESP_FAIL;
    } else {
      if (fb->format != PIXFORMAT_JPEG) {
        bool jpeg_converted = frame2jpg(fb, 80, &fb->buf, &fb->len);
        if (!jpeg_converted) {
          Serial.println("JPEG compression failed");
          res = ESP_FAIL;
        }
      }
      if (res == ESP_OK) {
        size_t hlen = snprintf((char *)part_buf, 64, _STREAM_PART, fb->len);
        res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
      }
      if (res == ESP_OK) {
        res = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
      }
      if (res == ESP_OK) {
        res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
      }
      esp_camera_fb_return(fb);
      if (res != ESP_OK) {
        break;
      }
    }
  }
  return res;
}

static esp_err_t index_handler(httpd_req_t *req) {
  const char* html = "<html><head><title>ESP32-CAM Stream</title></head>"
                     "<body style='background:#000;margin:0;display:flex;justify-content:center;align-items:center;height:100vh;'>"
                     "<img src='/stream' style='max-width:100%;max-height:100%;'>"
                     "</body></html>";
  httpd_resp_set_type(req, "text/html");
  return httpd_resp_send(req, html, strlen(html));
}

void startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;

  httpd_uri_t index_uri = {
    .uri       = "/",
    .method    = HTTP_GET,
    .handler   = index_handler,
    .user_ctx  = NULL
  };

  httpd_uri_t stream_uri = {
    .uri       = "/stream",
    .method    = HTTP_GET,
    .handler   = stream_handler,
    .user_ctx  = NULL
  };

  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &index_uri);
    httpd_register_uri_handler(stream_httpd, &stream_uri);
    Serial.println("Camera stream server started!");
    Serial.print("View stream at: http://");
    Serial.print(WiFi.localIP());
    Serial.println("/");
  }
}

// =============================================================================
// MAIN SETUP AND LOOP
// =============================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("========================================");
  Serial.println("Egyptian License Plate Recognition");
  Serial.println("ESP32-CAM with Ultrasonic Trigger");
  Serial.println("PWM Flash Control Version");
  Serial.println("========================================");

  // Initialize components
  setupFlash();
  setupCamera();
  setupUltrasonic();
  setupWiFi();

  // Start camera stream server (for debugging)
  if (wifiConnected) {
    startCameraServer();
  }

  Serial.println();
  Serial.println("System ready!");
  Serial.printf("Trigger distance: %d cm\n", TRIGGER_DISTANCE_CM);
  Serial.printf("Flash brightness: %d/255 (%d%%)\n", FLASH_BRIGHTNESS, (FLASH_BRIGHTNESS * 100) / 255);
  Serial.println("Waiting for object detection...");
}

void loop() {
  // Check if enough time has passed since last capture (debounce)
  unsigned long currentTime = millis();
  if (currentTime - lastCaptureTime < DEBOUNCE_DELAY_MS) {
    delay(100);
    return;
  }

  // Check for object detection
  if (isObjectDetected()) {
    Serial.println("Object detected! Capturing image...");
    lastCaptureTime = currentTime;

    String response = captureAndSendImage();

    if (response.length() > 0) {
      Serial.println("Image processed successfully");
    } else {
      Serial.println("Failed to process image");
    }

    Serial.println();
    Serial.println("Waiting for next detection...");
  }

  delay(200);  // Small delay between distance checks
}
