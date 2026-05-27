# YOLO Inference Service

Lightweight FastAPI microservice that runs YOLO object detection and returns
**raw detections only** — no prices, no checkout logic, no Odoo integration.

This service is one component of the Retail Checkout Automation System.
The backend (`backend/`) is responsible for all business logic.

---

## Architecture rule

> The YOLO service must only perform object detection.  
> It must not calculate prices, create checkout items, connect to Odoo,  
> or handle cashier logic.  
> It returns: `class_id`, `class_name`, `confidence`, `bbox`,  
> `image_width`, `image_height`.

---

## Project structure

```
yolo_service/
├── app/
│   ├── __init__.py
│   ├── main.py        ← FastAPI app, routes
│   ├── config.py      ← Settings loaded from .env
│   ├── schemas.py     ← Pydantic request/response models
│   └── detector.py    ← YOLO model wrapper (loads once at startup)
├── models/
│   └── best.pt        ← Your trained weights (not committed to git)
├── test_images/       ← Drop test images here
├── requirements.txt
├── .env               ← Environment configuration
└── README.md
```

---

## Prerequisites

- Python 3.10 or newer
- Your trained YOLO weights placed at `models/best.pt`

---

## Setup

```bash
# 1. Navigate to the service directory
cd yolo_service

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and edit the environment file (already provided with defaults)
#    Adjust MODEL_PATH, CONFIDENCE_THRESHOLD, etc. if needed.
cp .env .env.local   # optional — .env is already present
```

---

## Running the service

```bash
# From inside yolo_service/
uvicorn app.main:app --host 0.0.0.0 --port 8061 --reload
```

The service will be available at `http://127.0.0.1:8061`.

Interactive API docs: `http://127.0.0.1:8061/docs`

---

## Endpoints

### `GET /health`

Returns service status and whether the model is loaded.

```bash
curl http://127.0.0.1:8061/health
```

Example response:

```json
{
  "status": "ok",
  "model_loaded": true,
  "model_path": "models/best.pt",
  "message": "YOLO inference service is running and model is loaded."
}
```

---

### `POST /detect`

Accepts a JPEG, PNG, or WEBP image and returns raw detections.

```bash
curl -X POST http://127.0.0.1:8061/detect \
  -F "file=@test_images/sample.jpg"
```

Example response:

```json
{
  "image_width": 1280,
  "image_height": 720,
  "detections": [
    {
      "class_id": 3,
      "class_name": "coca_cola_500ml",
      "confidence": 0.9123,
      "bbox": { "x1": 120.5, "y1": 80.2, "x2": 310.8, "y2": 420.1 }
    },
    {
      "class_id": 7,
      "class_name": "mineral_water_1l",
      "confidence": 0.8741,
      "bbox": { "x1": 400.0, "y1": 90.0, "x2": 560.0, "y2": 430.0 }
    }
  ],
  "model_path": "models/best.pt",
  "confidence_threshold": 0.25,
  "iou_threshold": 0.45,
  "image_size": 640
}
```

**Rejected file type** (returns HTTP 415):

```bash
curl -X POST http://127.0.0.1:8061/detect \
  -F "file=@document.pdf"
```

---

## Configuration (`.env`)

| Variable               | Default         | Description                              |
|------------------------|-----------------|------------------------------------------|
| `MODEL_PATH`           | `models/best.pt`| Path to YOLO weights (relative to `yolo_service/`) |
| `CONFIDENCE_THRESHOLD` | `0.25`          | Minimum confidence to keep a detection   |
| `IOU_THRESHOLD`        | `0.45`          | NMS IoU threshold                        |
| `IMAGE_SIZE`           | `640`           | Inference resolution in pixels           |
| `HOST`                 | `0.0.0.0`       | Bind address                             |
| `PORT`                 | `8061`          | Bind port                                |
| `DEBUG`                | `false`         | Enable verbose logging                   |

---

## Error cases

| Situation                        | HTTP status | Detail                                      |
|----------------------------------|-------------|---------------------------------------------|
| `models/best.pt` missing         | Service starts in degraded state; `/health` reports `model_loaded: false` |
| Unsupported file type            | 415         | Lists accepted MIME types                   |
| Corrupt / unreadable image       | 422         | Cannot decode image                         |
| Inference error                  | 500         | Internal error message                      |

---

## Notes for the thesis project

- The service runs on port **8061** by default to avoid conflicts with the
  Django backend (typically 8000) and Odoo (8069).
- The Django backend calls this service via `backend/apps/vision/yolo_client.py`.
- Keep this service stateless — no database, no session state.
