"""
YOLO Inference Service — FastAPI entry point.

Endpoints
---------
GET  /health   — liveness / readiness check
POST /detect   — run YOLO inference on an uploaded image

Architecture rule
-----------------
This service performs object detection ONLY.
It must not calculate prices, create checkout items,
connect to Odoo, or contain any cashier / business logic.
"""

import io
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.config import settings
from app.detector import ModelNotFoundError, YOLODetector, get_detector, init_detector
from app.schemas import DetectionResponse, HealthResponse

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Allowed MIME types ─────────────────────────────────────────────────────
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

# ── Lifespan (startup / shutdown) ──────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the YOLO model once at startup; release on shutdown."""
    logger.info("Starting YOLO inference service …")
    try:
        init_detector()
        logger.info("YOLO model ready.")
    except ModelNotFoundError as exc:
        # Log clearly but let the app start so /health can report the problem.
        logger.error("Model load failed: %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error during model load: %s", exc)

    yield  # ← service is running

    logger.info("Shutting down YOLO inference service.")


# ── Application ────────────────────────────────────────────────────────────

app = FastAPI(
    title="YOLO Inference Service",
    description=(
        "Lightweight object-detection microservice for the Retail Checkout project. "
        "Returns raw detections only — no prices, no checkout logic."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ── Routes ─────────────────────────────────────────────────────────────────


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["Utility"],
)
def health_check() -> HealthResponse:
    """
    Returns the service status and whether the model is loaded.
    Use this endpoint to verify the service is ready before sending images.
    """
    try:
        detector = get_detector()
        return HealthResponse(
            status="ok",
            model_loaded=detector.is_loaded,
            model_path=detector.model_path,
            message="YOLO inference service is running and model is loaded.",
        )
    except RuntimeError:
        return HealthResponse(
            status="degraded",
            model_loaded=False,
            model_path=str(settings.resolved_model_path()),
            message=(
                "Service is running but the model is not loaded. "
                f"Ensure '{settings.resolved_model_path()}' exists and restart the service."
            ),
        )


@app.post(
    "/detect",
    response_model=DetectionResponse,
    summary="Run YOLO object detection on an uploaded image",
    tags=["Detection"],
)
async def detect(
    file: UploadFile = File(..., description="Image file (JPEG, PNG, or WEBP)"),
    detector: YOLODetector = Depends(get_detector),
) -> DetectionResponse:
    """
    Accept an image file and return raw YOLO detections.

    **Returns** (per detection):
    - `class_id` — integer class index
    - `class_name` — human-readable label
    - `confidence` — score in [0, 1]
    - `bbox` — bounding box `{x1, y1, x2, y2}` in pixel coordinates

    **Also returns** image dimensions and the inference parameters used.
    """
    # ── 1. Validate content type ───────────────────────────────────────────
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                f"Accepted types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}."
            ),
        )

    # ── 2. Read and decode image ───────────────────────────────────────────
    raw_bytes = await file.read()
    try:
        image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not decode the uploaded file as an image.",
        )

    image_width, image_height = image.size

    # ── 3. Run detection ───────────────────────────────────────────────────
    try:
        detections = detector.detect(image)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Detection failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detection failed: {exc}",
        )

    logger.info(
        "Detected %d object(s) in image (%dx%d).",
        len(detections),
        image_width,
        image_height,
    )

    # ── 4. Return raw detections ───────────────────────────────────────────
    return DetectionResponse(
        image_width=image_width,
        image_height=image_height,
        detections=detections,
        model_path=detector.model_path,
        confidence_threshold=settings.confidence_threshold,
        iou_threshold=settings.iou_threshold,
        image_size=settings.image_size,
    )
