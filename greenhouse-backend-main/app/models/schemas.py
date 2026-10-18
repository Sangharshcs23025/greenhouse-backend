from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime


# ---------- Auth ----------
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr


# ---------- Sensor data ----------
class SensorReadingIn(BaseModel):
    """What the ESP32 posts every cycle."""
    device_id: str
    temperature: float          # Celsius
    humidity: float             # %
    soil_moisture: float        # %
    light_intensity: float      # lux
    timestamp: Optional[datetime] = None


class SensorReadingOut(SensorReadingIn):
    id: str
    timestamp: datetime


# ---------- Device control ----------
class DeviceCommand(BaseModel):
    """What the app sends to change actuator state."""
    device_id: str
    actuator: Literal["pump", "fan", "light"]
    state: Literal["ON", "OFF"]


class DeviceState(BaseModel):
    device_id: str
    pump: Literal["ON", "OFF"] = "OFF"
    fan: Literal["ON", "OFF"] = "OFF"
    light: Literal["ON", "OFF"] = "OFF"
    last_updated: Optional[datetime] = None


# ---------- AI ----------
class PredictionRequest(BaseModel):
    temperature: float
    humidity: float
    soil_moisture: float
    light_intensity: float
    crop: Optional[str] = None


class PredictionResponse(BaseModel):
    recommendation: str
    irrigation_needed: bool
    predicted_growth_risk: str  # "low" | "medium" | "high"
    confidence: float