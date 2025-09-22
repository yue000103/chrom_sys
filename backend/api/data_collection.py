from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Dict, Any, Optional, List

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

@router.get("/device/{device_name}/parameter/{parameter_name}")
async def get_device_parameter(device_name: str, parameter_name: str):
    """
    Generic interface to get specific parameter information for a device
    Args:
        device_name: Name of the device (e.g., 'detector_1', 'pump_1')
        parameter_name: Name of the parameter (e.g., 'wavelength', 'flow_rate', 'pressure')
    Returns:
        Parameter value and metadata for the specified device
    """
    host_processor = get_host_processor()

    if not host_processor:
        raise HTTPException(status_code=503, detail="Data processor not initialized")

    try:
        # Get device parameter from processor
        parameter_data = host_processor.get_device_parameter(device_name, parameter_name)

        if parameter_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Parameter '{parameter_name}' not found for device '{device_name}'"
            )

        return {
            "device_name": device_name,
            "parameter_name": parameter_name,
            "value": parameter_data,
            "timestamp": datetime.now().isoformat()
        }

    except AttributeError:
        # Fallback if host_processor doesn't have get_device_parameter method
        device_data = host_processor.get_device_data()

        if device_name not in device_data:
            raise HTTPException(status_code=404, detail=f"Device '{device_name}' not found")

        device_info = device_data[device_name]

        if parameter_name not in device_info:
            raise HTTPException(
                status_code=404,
                detail=f"Parameter '{parameter_name}' not found for device '{device_name}'"
            )

        return {
            "device_name": device_name,
            "parameter_name": parameter_name,
            "value": device_info[parameter_name],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving parameter: {str(e)}")

@router.get("/device/{device_name}/parameters")
async def get_device_all_parameters(device_name: str):
    """
    Get all available parameters for a specific device
    Args:
        device_name: Name of the device
    Returns:
        All parameters and their values for the specified device
    """
    host_processor = get_host_processor()

    if not host_processor:
        raise HTTPException(status_code=503, detail="Data processor not initialized")

    try:
        device_data = host_processor.get_device_data()

        if device_name not in device_data:
            raise HTTPException(status_code=404, detail=f"Device '{device_name}' not found")

        return {
            "device_name": device_name,
            "parameters": device_data[device_name],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving device parameters: {str(e)}")
