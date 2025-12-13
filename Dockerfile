# Dockerfile for Egyptian License Plate Recognition API
# For deployment on Railway

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./api/
COPY yolov10_license_plate_detection.pt .
COPY yolov10_Arabic_OCR.pt .

# Set working directory to api
WORKDIR /app/api

# Railway uses PORT environment variable
ENV PORT=8000
EXPOSE $PORT

# Run the server (Railway sets PORT env var)
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
