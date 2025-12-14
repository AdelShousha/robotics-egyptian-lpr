"""
Database module for Neon PostgreSQL integration.

Handles connection and CRUD operations for license plate detections.
"""

import os
from datetime import datetime, date
from typing import List, Optional
from databases import Database

# Get database URL from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Create database instance
database = Database(DATABASE_URL) if DATABASE_URL else None


async def connect_db():
    """Connect to the database."""
    if database and not database.is_connected:
        await database.connect()
        print("Connected to Neon database")


async def disconnect_db():
    """Disconnect from the database."""
    if database and database.is_connected:
        await database.disconnect()
        print("Disconnected from Neon database")


async def insert_detection(
    car_image: str,
    lp_image: str,
    lp_number: str,
    confidence: float
) -> Optional[int]:
    """
    Insert a new detection record into the database.

    Args:
        car_image: Base64 encoded full car image
        lp_image: Base64 encoded license plate crop
        lp_number: Recognized Arabic plate text
        confidence: Detection confidence score

    Returns:
        The ID of the inserted record, or None if database not configured
    """
    if not database:
        print("Database not configured, skipping insert")
        return None

    query = """
        INSERT INTO detections (car_image, lp_image, lp_number, confidence, created_at)
        VALUES (:car_image, :lp_image, :lp_number, :confidence, :created_at)
        RETURNING id
    """
    values = {
        "car_image": car_image,
        "lp_image": lp_image,
        "lp_number": lp_number,
        "confidence": confidence,
        "created_at": datetime.utcnow()
    }

    result = await database.fetch_one(query=query, values=values)
    return result["id"] if result else None


async def get_all_detections() -> List[dict]:
    """
    Get all detections ordered by newest first.

    Returns:
        List of detection records
    """
    if not database:
        return []

    query = """
        SELECT id, car_image, lp_image, lp_number, confidence, created_at
        FROM detections
        ORDER BY created_at DESC
    """

    rows = await database.fetch_all(query=query)
    return [dict(row) for row in rows]


async def get_vehicles_today_count() -> int:
    """
    Get the count of vehicles detected today.

    Returns:
        Number of detections today
    """
    if not database:
        return 0

    query = """
        SELECT COUNT(*) as count
        FROM detections
        WHERE DATE(created_at) = :today
    """

    result = await database.fetch_one(query=query, values={"today": date.today()})
    return result["count"] if result else 0


async def get_last_detection_time() -> Optional[datetime]:
    """
    Get the timestamp of the most recent detection.

    Returns:
        Datetime of last detection, or None if no detections
    """
    if not database:
        return None

    query = """
        SELECT created_at
        FROM detections
        ORDER BY created_at DESC
        LIMIT 1
    """

    result = await database.fetch_one(query=query)
    return result["created_at"] if result else None
