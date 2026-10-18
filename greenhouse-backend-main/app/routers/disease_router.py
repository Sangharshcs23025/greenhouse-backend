import io
import json
import os
import numpy as np
from PIL import Image, ImageOps
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.auth import get_current_user_email, verify_device_key
from app.disease_treatments import get_treatment

router = APIRouter(prefix="/disease", tags=["Disease Detection"])

_model = None
_class_names = None

ML_DIR = os.path.join(os.path.dirname(__file__), "..", "ml")
MODEL_PATH = os.path.join(ML_DIR, "tomato_disease_model.h5")
CLASS_NAMES_PATH = os.path.join(ML_DIR, "class_names.json")


def get_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise HTTPException(status_code=503, detail="Disease detection model not found on server.")
        import tensorflow as tf
        _model = tf.keras.models.load_model(MODEL_PATH)
    return _model


def get_class_names():
    global _class_names
    if _class_names is None:
        with open(CLASS_NAMES_PATH) as f:
            _class_names = json.load(f)
    return _class_names


def classify_image_bytes(contents: bytes) -> dict:
    try:
        image = Image.open(io.BytesIO(contents))
        transposed = ImageOps.exif_transpose(image)
        if transposed is not None:
            image = transposed
        image = image.convert("RGB").resize((224, 224))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read image file")

    arr = np.expand_dims(np.array(image), axis=0)

    model = get_model()
    class_names = get_class_names()

    predictions = model.predict(arr)[0]
    top_idx = int(np.argmax(predictions))
    confidence = float(predictions[top_idx])
    disease_class = class_names[top_idx]

    advice = get_treatment(disease_class)
    low_confidence_warning = confidence < 0.55

    return {
        "disease": disease_class,
        "confidence": round(confidence, 2),
        "description": advice["description"],
        "treatment": advice["treatment"],
        "prevention": advice["prevention"],
        "low_confidence_warning": low_confidence_warning,
    }


@router.post("/detect", dependencies=[Depends(get_current_user_email)])
async def detect_disease(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    contents = await file.read()
    return classify_image_bytes(contents)


@router.post("/detect-device", dependencies=[Depends(verify_device_key)])
async def detect_disease_device(file: UploadFile = File(...)):
    """Allows ESP32-CAM or IoT nodes to directly post plant photos for disease classification."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    contents = await file.read()
    return classify_image_bytes(contents)