from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any, Optional

router = APIRouter()  # Data collection API routes

# Import global host_processor from main module
def get_host_processor():
    """Get the host processor instance from main module"""
    import main
    return getattr(main, 'host_processor', None)

@router.get("/status")
async def get_data_collection_status():
    return {
        "timestamp": datetime.now().isoformat(),
        "status": "active",
        "data_points_collected": 0,
        "last_collection_time": datetime.now().isoformat()
    }

@router.get("/latest")
async def get_latest_data():
    return {
        "timestamp": datetime.now().isoformat(),
        "value": 0,
        "source": "data_collection_api"
    }

@router.get("/history")
async def get_historical_data(
    start_time: str = None,
    end_time: str = None,
    limit: int = 100
):
    return {
        "data": [],
        "start_time": start_time,
        "end_time": end_time,
        "count": 0
    }

@router.get("/detector/{device_name}")
async def get_detector_data(device_name: str = "detector_1"):
    """
    Get complete detector data including wavelength, A/B channels
    This endpoint provides data that is not published to MQTT
    """
    host_processor = get_host_processor()

    if not host_processor:
        raise HTTPException(status_code=503, detail="Data processor not initialized")

    # Get detector data from processor (includes wavelength, channels, etc.)
    detector_data = host_processor.get_detector_data(device_name)

    if not detector_data:
        raise HTTPException(status_code=404, detail=f"Detector {device_name} not found or no data available")

    return detector_data

@router.get("/detector")
async def get_default_detector_data():
    """Get data for default detector (detector_1)"""
    return await get_detector_data("detector_1")

@router.get("/all-devices")
async def get_all_device_data():
    """Get latest data for all registered devices"""
    host_processor = get_host_processor()

    if not host_processor:
        raise HTTPException(status_code=503, detail="Data processor not initialized")

    return {
        "devices": host_processor.get_device_data(),
        "timestamp": datetime.now().isoformat()
    }