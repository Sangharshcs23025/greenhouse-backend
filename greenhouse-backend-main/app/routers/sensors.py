import json
from collections import defaultdict
from datetime import datetime
from typing import List, Optional, Dict, Set
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from app.database import sensor_readings_collection
from app.models.schemas import SensorReadingIn, SensorReadingOut
from app.auth import get_current_user_email, get_optional_user_email, verify_device_key

router = APIRouter(prefix="/sensors", tags=["Sensors"])


class SensorConnectionManager:
    def __init__(self):
        # Map device_id -> set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)

    async def connect(self, device_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[device_id].add(websocket)

    def disconnect(self, device_id: str, websocket: WebSocket):
        if device_id in self.active_connections:
            self.active_connections[device_id].discard(websocket)
            if not self.active_connections[device_id]:
                del self.active_connections[device_id]

    async def broadcast(self, device_id: str, message: dict):
        if device_id in self.active_connections:
            payload = json.dumps(message)
            dead_connections = []
            for connection in list(self.active_connections[device_id]):
                try:
                    await connection.send_text(payload)
                except Exception:
                    dead_connections.append(connection)
            for dead in dead_connections:
                self.disconnect(device_id, dead)


manager = SensorConnectionManager()


@router.post("/data", dependencies=[Depends(verify_device_key)])
async def post_sensor_data(reading: SensorReadingIn):
    doc = reading.dict() if hasattr(reading, "dict") else reading.model_dump()
    timestamp = reading.timestamp or datetime.utcnow()
    doc["timestamp"] = timestamp
    result = await sensor_readings_collection.insert_one(doc)

    # Immediately push to connected Flutter clients listening to this device_id
    broadcast_data = {
        "device_id": reading.device_id,
        "temperature": reading.temperature,
        "humidity": reading.humidity,
        "soil_moisture": reading.soil_moisture,
        "light_intensity": reading.light_intensity,
        "timestamp": timestamp.isoformat(),
        "id": str(result.inserted_id),
    }
    await manager.broadcast(reading.device_id, broadcast_data)

    return {"status": "stored", "id": str(result.inserted_id)}


@router.websocket("/ws/{device_id}")
async def websocket_sensors_endpoint(websocket: WebSocket, device_id: str):
    """
    Real-time bidirectional WebSocket stream for live sensor updates.
    As soon as the client connects, it receives the latest reading,
    and then receives pushed updates instantly whenever the device uploads new data.
    """
    await manager.connect(device_id, websocket)
    try:
        # Send latest stored reading on initial connect if present
        latest = await sensor_readings_collection.find_one({"device_id": device_id}, sort=[("timestamp", -1)])
        if latest:
            latest["id"] = str(latest["_id"])
            latest.pop("_id", None)
            if isinstance(latest.get("timestamp"), datetime):
                latest["timestamp"] = latest["timestamp"].isoformat()
            await websocket.send_text(json.dumps(latest))

        # Keep alive loop: accept pings or incoming heartbeat messages
        while True:
            text = await websocket.receive_text()
            if text == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}))
    except WebSocketDisconnect:
        manager.disconnect(device_id, websocket)
    except Exception:
        manager.disconnect(device_id, websocket)


@router.get("/latest", dependencies=[Depends(get_optional_user_email)])
async def get_latest_reading(device_id: str = Query(...)):
    doc = await sensor_readings_collection.find_one({"device_id": device_id}, sort=[("timestamp", -1)])
    if not doc:
        return {"detail": "No readings yet"}
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    if isinstance(doc.get("timestamp"), datetime):
        doc["timestamp"] = doc["timestamp"].isoformat()
    return doc


@router.get("/history", dependencies=[Depends(get_optional_user_email)])
async def get_history(device_id: str = Query(...), limit: int = Query(100, le=1000)):
    cursor = sensor_readings_collection.find({"device_id": device_id}).sort("timestamp", -1).limit(limit)
    results = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        if isinstance(doc.get("timestamp"), datetime):
            doc["timestamp"] = doc["timestamp"].isoformat()
        results.append(doc)
    return results