from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/status")
async def get_system_status():
    return {
        "timestamp": datetime.now().isoformat(),
        "status": "running",
        "version": "1.0.0"
    }

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}