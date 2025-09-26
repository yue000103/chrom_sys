"""
硬件控制API
控制设备的mock模式和其他硬件操作
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import sqlite3
import os

from hardware.hardware_config import (
    hardware_manager,
    set_global_mock_mode,
    get_global_mock_mode
)

router = APIRouter(prefix="/api/hardware", tags=["hardware"])


class MockModeRequest(BaseModel):
    """Mock模式请求模型"""
    mock: bool
    device_id: Optional[str] = None


class MockModeResponse(BaseModel):
    """Mock模式响应模型"""
    success: bool
    mode: str
    device_id: Optional[str] = None
    message: str


@router.post("/mock-mode", response_model=MockModeResponse)
async def set_mock_mode(request: MockModeRequest):
    """
    设置设备的Mock模式
    - mock: True为模拟模式，False为联机模式
    - device_id: 可选，指定设备ID；如果不指定则设置全局模式
    """
    try:
        if request.device_id:
            # 设置特定设备的mock模式
            success = hardware_manager.set_device_mock_mode(request.device_id, request.mock)
            mode = "mock" if request.mock else "online"
            message = f"设备 {request.device_id} 已切换到{mode}模式"
        else:
            # 设置全局mock模式
            success = set_global_mock_mode(request.mock)
            mode = "mock" if request.mock else "online"
            message = f"全局已切换到{mode}模式"

        return MockModeResponse(
            success=success,
            mode=mode,
            device_id=request.device_id,
            message=message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mock-mode", response_model=Dict[str, Any])
async def get_mock_mode(device_id: Optional[str] = None):
    """
    获取设备的Mock模式状态
    - device_id: 可选，指定设备ID；如果不指定则获取全局模式
    """
    try:
        if device_id:
            mock = hardware_manager.get_device_mock_mode(device_id)
            return {
                "device_id": device_id,
                "mock": mock,
                "mode": "mock" if mock else "online"
            }
        else:
            mock = get_global_mock_mode()
            return {
                "global": True,
                "mock": mock,
                "mode": "mock" if mock else "online"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices-status", response_model=Dict[str, Any])
async def get_all_devices_status():
    """
    获取所有设备的状态和模式
    """
    try:
        global_mock = get_global_mock_mode()
        devices = {}

        # 从数据库读取所有设备配置
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "database", "chromatography.db")

        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            try:
                # 获取所有设备配置
                cursor.execute("SELECT device_id, device_name, device_type, status, is_mock FROM device_config")
                db_devices = cursor.fetchall()

                for device_id, device_name, device_type, status, is_mock in db_devices:
                    # 检查是否有特定的mock模式配置
                    device_mock = hardware_manager.get_device_mock_mode(device_id)

                    devices[device_id] = {
                        "device_name": device_name,
                        "device_type": device_type,
                        "status": status,
                        "mock": device_mock,
                        "mode": "mock" if device_mock else "online",
                        "db_is_mock": bool(is_mock)  # 数据库中的默认mock状态
                    }

                # 同时包含从device_mapping表获取的设备信息
                cursor.execute("SELECT device_code, controller_type, physical_id, device_description, is_active FROM device_mapping WHERE is_active = 1")
                mapping_devices = cursor.fetchall()

                for device_code, controller_type, physical_id, device_description, is_active in mapping_devices:
                    if device_code not in devices:  # 避免重复
                        device_mock = hardware_manager.get_device_mock_mode(device_code)
                        devices[device_code] = {
                            "device_name": device_description or device_code,
                            "device_type": controller_type,
                            "physical_id": physical_id,
                            "status": "active" if is_active else "inactive",
                            "mock": device_mock,
                            "mode": "mock" if device_mock else "online",
                            "source": "device_mapping"
                        }

            except Exception as e:
                # 如果数据库查询失败，回退到原来的方法
                for device_id, config in hardware_manager.device_configs.items():
                    devices[device_id] = {
                        "mock": config.mock_mode,
                        "mode": "mock" if config.mock_mode else "online"
                    }
            finally:
                conn.close()
        else:
            # 如果数据库不存在，使用内存中的配置
            for device_id, config in hardware_manager.device_configs.items():
                devices[device_id] = {
                    "mock": config.mock_mode,
                    "mode": "mock" if config.mock_mode else "online"
                }

        return {
            "global_mock": global_mock,
            "global_mode": "mock" if global_mock else "online",
            "devices": devices,
            "device_count": len(devices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-mock-mode")
async def reset_mock_mode():
    """
    重置所有设备到联机模式
    """
    try:
        # 设置全局为联机模式
        set_global_mock_mode(False)

        # 清除所有设备的特定配置
        hardware_manager.device_configs.clear()

        return {
            "success": True,
            "message": "所有设备已重置为联机模式"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))