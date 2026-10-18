from fastapi import APIRouter, Depends
from datetime import datetime
from app.database import devices_collection
from app.models.schemas import DeviceCommand, DeviceState
from app.auth import get_current_user_email, verify_device_key

router = APIRouter(prefix="/devices", tags=["Device Control"])


@router.post("/command", dependencies=[Depends(get_current_user_email)])
async def send_command(cmd: DeviceCommand):
    """Called from the Flutter 'Device Control' screen (e.g. toggle pump ON)."""
    await devices_collection.update_one(
        {"device_id": cmd.device_id},
        {"$set": {cmd.actuator: cmd.state, "last_updated": datetime.utcnow()}},
        upsert=True,
    )
    return {"status": "command queued", "actuator": cmd.actuator, "state": cmd.state}


@router.get("/state", response_model=DeviceState)
async def get_state(device_id: str):
    """
    Polled by BOTH the ESP32 (to know what to actuate) and the Flutter app
    (to reflect current switch positions in the UI).
    """
    doc = await devices_collection.find_one({"device_id": device_id})
    if not doc:
        return DeviceState(device_id=device_id)
    return DeviceState(**doc)