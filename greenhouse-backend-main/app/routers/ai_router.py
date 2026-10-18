import os
import joblib
import numpy as np
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.models.schemas import PredictionRequest, PredictionResponse
from app.auth import get_current_user_email

router = APIRouter(prefix="/ai", tags=["AI Recommendations"])

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "greenhouse_model.joblib")
_model = None
_crop_encoder = None
_risk_encoder = None


def get_model():
    global _model
    if _model is None and os.path.exists(MODEL_PATH):
        _model = joblib.load(MODEL_PATH)
    return _model


def get_encoders():
    global _crop_encoder, _risk_encoder
    crop_path = os.path.join(os.path.dirname(__file__), "..", "ml", "crop_encoder.joblib")
    risk_path = os.path.join(os.path.dirname(__file__), "..", "ml", "risk_encoder.joblib")
    if _crop_encoder is None and os.path.exists(crop_path):
        _crop_encoder = joblib.load(crop_path)
        _risk_encoder = joblib.load(risk_path)
    return _crop_encoder, _risk_encoder


def rule_based_fallback(data: PredictionRequest) -> PredictionResponse:
    irrigation_needed = data.soil_moisture < 35
    if data.temperature > 35 or data.soil_moisture < 20:
        risk = "high"
    elif data.temperature > 30 or data.soil_moisture < 35:
        risk = "medium"
    else:
        risk = "low"

    tips = []
    if irrigation_needed:
        tips.append("Soil moisture is low — irrigation recommended.")
    if data.temperature > 32:
        tips.append("Temperature is high — consider activating the fan.")
    if data.light_intensity < 20:
        tips.append("Light levels are low — consider grow lights.")
    if not tips:
        tips.append("Conditions are optimal. No action needed.")

    return PredictionResponse(
        recommendation=" ".join(tips),
        irrigation_needed=irrigation_needed,
        predicted_growth_risk=risk,
        confidence=0.6,
    )


@router.post("/predict", response_model=PredictionResponse, dependencies=[Depends(get_current_user_email)])
async def predict(data: PredictionRequest):
    model = get_model()
    crop_encoder, risk_encoder = get_encoders()

    crop = data.crop
    if model is not None and crop_encoder is not None and crop and crop.lower() in crop_encoder.classes_:
        crop_code = crop_encoder.transform([crop.lower()])[0]
        features = np.array([[crop_code, data.temperature, data.humidity, data.soil_moisture, data.light_intensity]])
        risk_code = model.predict(features)[0]
        risk = risk_encoder.inverse_transform([risk_code])[0]
        confidence = model.predict_proba(features).max()

        return PredictionResponse(
            recommendation=f"AI model trained for {crop}: conditions rated {risk} risk.",
            irrigation_needed=data.soil_moisture < 35,
            predicted_growth_risk=risk,
            confidence=round(float(confidence), 2),
        )

    return rule_based_fallback(data)


class SimulationRequest(BaseModel):
    temperature: float
    humidity: float
    soil_moisture: float
    light_intensity: float
    pump_on: bool = False
    fan_on: bool = False
    light_on: bool = False
    duration_minutes: int = 30


class SimulationResponse(BaseModel):
    projected_temperature: float
    projected_humidity: float
    projected_soil_moisture: float
    projected_light_intensity: float
    projected_risk: str
    explanation: str


@router.post("/simulate", response_model=SimulationResponse, dependencies=[Depends(get_current_user_email)])
async def simulate(req: SimulationRequest):
    """
    'What-If' engine — the predictive core of the digital twin.
    Projects forward what the greenhouse state WOULD look like if a given
    actuator combination were applied for `duration_minutes`.
    """
    t = req.duration_minutes

    if req.pump_on:
        soil = req.soil_moisture + 0.5 * t
    else:
        soil = req.soil_moisture - 0.05 * t
    soil = max(0.0, min(100.0, soil))

    if req.fan_on:
        temp = req.temperature - 0.1 * t
    else:
        temp = req.temperature + (0.03 * t if req.temperature > 28 else 0.01 * t)
    temp = max(10.0, min(50.0, temp))

    if req.fan_on:
        humidity = req.humidity - 0.15 * t
    else:
        humidity = req.humidity + 0.05 * t
    humidity = max(0.0, min(100.0, humidity))

    # Light is percentage-scale (0-100%), matching the ESP32's LDR reading
    if req.light_on:
        light = req.light_intensity + (80 - req.light_intensity) * min(1.0, t / 60)
    else:
        light = req.light_intensity - (req.light_intensity - 10) * min(1.0, t / 60)
    light = max(0.0, min(100.0, light))

    projected = PredictionRequest(
        temperature=temp, humidity=humidity, soil_moisture=soil, light_intensity=light
    )
    fallback = rule_based_fallback(projected)

    actions = []
    if req.pump_on:
        actions.append("pump ON")
    if req.fan_on:
        actions.append("fan ON")
    if req.light_on:
        actions.append("light ON")
    action_desc = ", ".join(actions) if actions else "no actuators active"

    explanation = (
        f"Simulated {t} minutes with {action_desc}. "
        f"Projected risk: {fallback.predicted_growth_risk}."
    )

    return SimulationResponse(
        projected_temperature=round(temp, 1),
        projected_humidity=round(humidity, 1),
        projected_soil_moisture=round(soil, 1),
        projected_light_intensity=round(light, 0),
        projected_risk=fallback.predicted_growth_risk,
        explanation=explanation,
    )