from pathlib import Path
from typing import Optional, Any

import io
import json

import cv2
import numpy as np
import tensorflow as tf
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

CROPPER_MODEL_PATH = MODEL_DIR / "yolo_cropper_vegetable_display.pt"
DIGIT_MODEL_PATH = MODEL_DIR / "yolo_digit_reader.pt"
VEGETABLE_CLASSIFIER_PATH = MODEL_DIR / "vegetable_classifier.h5"
CLASS_INDICES_PATH = MODEL_DIR / "class_indices.json"


app = FastAPI(
    title="Weighted Product Vision API",
    description="API service for vegetable detection, digital scale display reading, and weight extraction.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


cropper_model: Optional[YOLO] = None
digit_model: Optional[YOLO] = None
vegetable_classifier: Optional[Any] = None
class_map: Optional[dict[int, str]] = None


@app.on_event("startup")
def load_models():
    global cropper_model, digit_model, vegetable_classifier, class_map

    missing = []

    if not CROPPER_MODEL_PATH.exists():
        missing.append(str(CROPPER_MODEL_PATH))

    if not DIGIT_MODEL_PATH.exists():
        missing.append(str(DIGIT_MODEL_PATH))

    if not VEGETABLE_CLASSIFIER_PATH.exists():
        missing.append(str(VEGETABLE_CLASSIFIER_PATH))

    if not CLASS_INDICES_PATH.exists():
        missing.append(str(CLASS_INDICES_PATH))

    if missing:
        raise RuntimeError("Missing model files: " + ", ".join(missing))

    cropper_model = YOLO(str(CROPPER_MODEL_PATH))
    digit_model = YOLO(str(DIGIT_MODEL_PATH))
    vegetable_classifier = tf.keras.models.load_model(str(VEGETABLE_CLASSIFIER_PATH))

    with open(CLASS_INDICES_PATH, "r", encoding="utf-8") as f:
        raw_indices = json.load(f)

    class_map = normalize_class_indices(raw_indices)

    print("Weighted-product models loaded successfully.")
    print("Cropper classes:", cropper_model.names)
    print("Digit model classes:", digit_model.names)
    print("Vegetable classes:", class_map)


def normalize_class_indices(raw_indices: dict) -> dict[int, str]:
    """
    Supports either:
    {"carrot": 0, "potato": 1}
    or:
    {"0": "carrot", "1": "potato"}
    """

    index_to_class = {}

    for key, value in raw_indices.items():
        if isinstance(value, int):
            index_to_class[value] = key
        else:
            try:
                index_to_class[int(key)] = str(value)
            except ValueError:
                pass

    return index_to_class


async def read_uploaded_image(file: UploadFile) -> np.ndarray:
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    try:
        pil_image = Image.open(io.BytesIO(content)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {exc}")

    rgb = np.array(pil_image)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    return bgr


def crop_box(image: np.ndarray, xyxy, margin: int = 10):
    h, w = image.shape[:2]

    x1, y1, x2, y2 = [int(v) for v in xyxy]

    x1 = max(0, x1 - margin)
    y1 = max(0, y1 - margin)
    x2 = min(w, x2 + margin)
    y2 = min(h, y2 + margin)

    crop = image[y1:y2, x1:x2]

    return crop, [x1, y1, x2, y2]


def get_best_box_by_class(result, target_class_name: str):
    if result.boxes is None or len(result.boxes) == 0:
        return None, None

    best_box = None
    best_confidence = -1.0

    for box in result.boxes:
        class_id = int(box.cls[0].item())
        class_name = result.names.get(class_id, str(class_id))
        confidence = float(box.conf[0].item())

        if class_name == target_class_name and confidence > best_confidence:
            best_confidence = confidence
            best_box = box.xyxy[0].cpu().numpy()

    if best_box is None:
        return None, None

    return best_box, best_confidence


def classify_vegetable(vegetable_crop: np.ndarray):
    if vegetable_classifier is None:
        raise HTTPException(status_code=500, detail="Vegetable classifier is not loaded.")

    if class_map is None:
        raise HTTPException(status_code=500, detail="Class map is not loaded.")

    if vegetable_crop is None or vegetable_crop.size == 0:
        return "N/A", 0.0

    input_shape = vegetable_classifier.input_shape

    target_h = int(input_shape[1])
    target_w = int(input_shape[2])

    rgb_crop = cv2.cvtColor(vegetable_crop, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb_crop, (target_w, target_h))

    arr = resized.astype("float32") / 255.0
    arr = np.expand_dims(arr, axis=0)

    predictions = vegetable_classifier.predict(arr, verbose=0)[0]

    class_id = int(np.argmax(predictions))
    confidence = float(predictions[class_id])

    class_name = class_map.get(class_id, f"class_{class_id}")

    return class_name, confidence


def read_display_digits(display_crop: np.ndarray, confidence_threshold: float = 0.25):
    if digit_model is None:
        raise HTTPException(status_code=500, detail="Digit YOLO model is not loaded.")

    if display_crop is None or display_crop.size == 0:
        return "N/A", None, 0.0, []

    result = digit_model(display_crop, conf=confidence_threshold, verbose=False)[0]

    if result.boxes is None or len(result.boxes) == 0:
        return "N/A", None, 0.0, []

    detections = []

    for box in result.boxes:
        class_id = int(box.cls[0].item())
        class_name = result.names.get(class_id, str(class_id))
        confidence = float(box.conf[0].item())
        xyxy = box.xyxy[0].cpu().numpy()

        x1, y1, x2, y2 = xyxy
        x_center = float((x1 + x2) / 2.0)

        if class_name.startswith("digit_"):
            value = class_name.replace("digit_", "")
        elif class_name == "dot":
            value = "."
        else:
            continue

        detections.append(
            {
                "class_id": class_id,
                "class_name": class_name,
                "value": value,
                "confidence": confidence,
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "x_center": x_center,
            }
        )

    detections.sort(key=lambda d: d["x_center"])

    text = ""
    dot_used = False

    for det in detections:
        if det["value"] == ".":
            if not dot_used:
                text += "."
                dot_used = True
        else:
            text += det["value"]

    if text == "" or text == ".":
        return "N/A", None, 0.0, detections

    try:
        weight_kg = float(text)
    except ValueError:
        weight_kg = None

    avg_confidence = float(np.mean([d["confidence"] for d in detections])) if detections else 0.0

    return text, weight_kg, avg_confidence, detections


@app.get("/")
def root():
    return {
        "message": "Weighted Product Vision API is running.",
        "docs": "/docs",
        "health": "/health",
        "predict": "/predict/weighted",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_dir": str(MODEL_DIR),
        "files": {
            "cropper_exists": CROPPER_MODEL_PATH.exists(),
            "digit_model_exists": DIGIT_MODEL_PATH.exists(),
            "vegetable_classifier_exists": VEGETABLE_CLASSIFIER_PATH.exists(),
            "class_indices_exists": CLASS_INDICES_PATH.exists(),
        },
        "loaded": {
            "cropper_loaded": cropper_model is not None,
            "digit_model_loaded": digit_model is not None,
            "vegetable_classifier_loaded": vegetable_classifier is not None,
            "class_map_loaded": class_map is not None,
        },
    }


@app.post("/predict/weighted")
async def predict_weighted(
    file: UploadFile = File(...),
    cropper_confidence: float = 0.25,
    digit_confidence: float = 0.25,
):
    if cropper_model is None:
        raise HTTPException(status_code=500, detail="Cropper model is not loaded.")

    image = await read_uploaded_image(file)

    cropper_result = cropper_model(image, conf=cropper_confidence, verbose=False)[0]

    vegetable_box, vegetable_crop_conf = get_best_box_by_class(
        cropper_result,
        "vegetable",
    )

    display_box, display_crop_conf = get_best_box_by_class(
        cropper_result,
        "display",
    )

    response = {
        "source": "weighted_product_pipeline",
        "vegetable": "N/A",
        "vegetable_confidence": 0.0,
        "measurement_yolo": "N/A",
        "weight_kg": None,
        "measurement_yolo_confidence": 0.0,
        "cropper_vegetable_confidence": vegetable_crop_conf,
        "cropper_display_confidence": display_crop_conf,
        "vegetable_bbox": None,
        "display_bbox": None,
        "digit_detections": [],
        "status": "ok",
        "warnings": [],
    }

    if vegetable_box is None:
        response["warnings"].append("No vegetable region detected.")
    else:
        vegetable_crop, vegetable_bbox = crop_box(image, vegetable_box, margin=20)
        vegetable_name, vegetable_confidence = classify_vegetable(vegetable_crop)

        response["vegetable"] = vegetable_name
        response["vegetable_confidence"] = vegetable_confidence
        response["vegetable_bbox"] = vegetable_bbox

    if display_box is None:
        response["warnings"].append("No scale display region detected.")
    else:
        display_crop, display_bbox = crop_box(image, display_box, margin=10)

        display_text, weight_kg, digit_avg_confidence, digit_detections = read_display_digits(
            display_crop,
            confidence_threshold=digit_confidence,
        )

        response["measurement_yolo"] = display_text
        response["weight_kg"] = weight_kg
        response["measurement_yolo_confidence"] = digit_avg_confidence
        response["display_bbox"] = display_bbox
        response["digit_detections"] = digit_detections

    if response["vegetable"] == "N/A" or response["weight_kg"] is None:
        response["status"] = "needs_manual_review"

    return response