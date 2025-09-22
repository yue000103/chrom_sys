"""
功能控制API
Function Control API
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "功能控制API运行正常"}