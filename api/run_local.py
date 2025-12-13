#!/usr/bin/env python3
"""
Local development server for Egyptian License Plate Recognition API.

Usage:
    python run_local.py

The server will start at http://localhost:8000
Test endpoint: POST http://localhost:8000/api/recognize
"""

import uvicorn
import sys
from pathlib import Path

# Add parent directory to path to access models
sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    print("Starting Egyptian License Plate Recognition API...")
    print("Server will be available at: http://localhost:8000")
    print("API endpoint: POST http://localhost:8000/api/recognize")
    print("\nTest with curl:")
    print('  curl -X POST -F "imageFile=@your_image.jpg" http://localhost:8000/api/recognize')
    print("\nPress Ctrl+C to stop the server\n")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
