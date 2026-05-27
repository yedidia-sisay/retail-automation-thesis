"""
YOLODetector — loads the model once and exposes a single `detect` method.

Responsibilities:
  - Load models/best.pt at startup (raises if missing).
  - Accept a PIL Image and return raw Detection objects.
  - Apply confidence and IOU thresholds from config.

This module must NOT calculate prices, create checkout items,
connect to Odoo, or contain any business logic.
"""

import logging
from pathlib import Path
from typing import List

from PIL import Image

from app.config import settings
from app.schemas import BoundingBox, Detection

logger = logging.getLogger(__name__)


class ModelNotFoundError(RuntimeError):
    """Raised when models/best.pt does not exist at startup."""


class YOLODetector:
    """Singleton-style wrapper around an Ultralytics YOLO model."""

    def __init__(self) -> None:
        self._model = None
        self._model_path = settings.resolved_model_path()
        self._load_model()

    # ── Initialisation ─────────────────────────────────────────────────────

    def _load_model(self) -> None:
        """Load the YOLO model from disk.  Raises ModelNotFoundError if absent."""
        if not self._model_path.exists():
            raise ModelNotFoundError(
                f"YOLO model not found at '{self._model_path}'. "
                "Place your trained weights at models/best.pt before starting the service."
            )

        # Import here so the service can still start (and report a clear error)
        # even if ultralytics is not installed — though requirements.txt pins it.
        try:
            from ultralytics import YOLO  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "ultralytics is not installed. Run: pip install ultralytics"
            ) from exc

        logger.info("Loading YOLO model from '%s' …", self._model_path)
        self._model = YOLO(str(self._model_path))
        logger.info("Model loaded successfully.")

    # ── Public API ─────────────────────────────────────────────────────────

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def model_path(self) -> str:
        return str(self._model_path)

    def detect(self, image: Image.Image) -> List[Detection]:
        """
        Run inference on a PIL Image and return a list of Detection objects.

        Parameters
        ----------
        image : PIL.Image.Image
            The image to run detection on.

        Returns
        -------
        List[Detection]
            Raw detections filtered by confidence_threshold and iou_threshold.
            Empty list when nothing is detected above the threshold.
        """
        if self._model is None:
            raise RuntimeError("Model is not loaded.")

        results = self._model.predict(
            source=image,
            conf=settings.confidence_threshold,
            iou=settings.iou_threshold,
            imgsz=settings.image_size,
            verbose=False,
        )

        detections: List[Detection] = []

        for result in results:
            if result.boxes is None:
                continue

            class_names = result.names  # dict[int, str]

            for box in result.boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                detections.append(
                    Detection(
                        class_id=cls_id,
                        class_name=class_names.get(cls_id, str(cls_id)),
                        confidence=round(conf, 4),
                        bbox=BoundingBox(
                            x1=round(x1, 2),
                            y1=round(y1, 2),
                            x2=round(x2, 2),
                            y2=round(y2, 2),
                        ),
                    )
                )

        return detections


# ── Module-level singleton (created during FastAPI lifespan) ───────────────
# Initialised to None; replaced by `get_detector()` after startup.
_detector_instance: YOLODetector | None = None


def get_detector() -> YOLODetector:
    """Return the module-level detector instance (dependency-injectable).

    Raises HTTP 503 when the model failed to load at startup so that callers
    receive a clean JSON error instead of an unhandled 500.
    """
    from fastapi import HTTPException

    if _detector_instance is None or not _detector_instance.is_loaded:
        raise HTTPException(
            status_code=503,
            detail=(
                "YOLO model is not loaded. "
                f"Ensure '{settings.model_path}' exists and restart the service."
            ),
        )
    return _detector_instance


def init_detector() -> YOLODetector:
    """Create and cache the detector singleton.  Called once during startup."""
    global _detector_instance
    _detector_instance = YOLODetector()
    return _detector_instance
