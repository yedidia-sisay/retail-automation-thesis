"""
YOLOClient — Django-side HTTP client for the external YOLO inference service.

Architecture rule
-----------------
The YOLO service (yolo_service/) performs object detection only.
This client posts an image file to that service and returns the raw
detection list.  All business logic (price lookup, checkout item creation,
Odoo integration) lives in the backend, NOT here.

Usage
-----
    from apps.vision.yolo_client import YOLOClient

    client = YOLOClient()

    # From a file path:
    detections = client.detect_from_path("/tmp/frame.jpg")

    # From an open file-like object (e.g. Django InMemoryUploadedFile):
    detections = client.detect_from_file(request.FILES["image"])

Each detection dict contains:
    {
        "class_id":   int,
        "class_name": str,
        "confidence": float,          # 0.0 – 1.0
        "bbox": {
            "x1": float, "y1": float,
            "x2": float, "y2": float,
        },
    }

The response also includes image_width, image_height, and the inference
parameters used — available via detect_full() if you need them.

Configuration (Django settings or environment)
----------------------------------------------
YOLO_SERVICE_URL   — base URL of the YOLO service
                     default: "http://127.0.0.1:8061"
YOLO_SERVICE_TIMEOUT — request timeout in seconds (default: 30)
USE_MOCK_YOLO      — if True, skip the HTTP call and return fixture data
                     useful for unit tests and CI (default: True)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, BinaryIO

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Defaults ───────────────────────────────────────────────────────────────
_DEFAULT_SERVICE_URL = "http://127.0.0.1:8061"
_DEFAULT_TIMEOUT = 30  # seconds


def _service_url() -> str:
    return getattr(settings, "YOLO_SERVICE_URL", _DEFAULT_SERVICE_URL).rstrip("/")


def _timeout() -> int:
    return int(getattr(settings, "YOLO_SERVICE_TIMEOUT", _DEFAULT_TIMEOUT))


def _use_mock() -> bool:
    return bool(getattr(settings, "USE_MOCK_YOLO", True))


# ── Client ─────────────────────────────────────────────────────────────────


class YOLOServiceError(Exception):
    """Raised when the YOLO service returns an error or is unreachable."""


class YOLOClient:
    """
    HTTP client that posts images to the external YOLO inference service
    and returns raw detection results.

    The client is stateless — create one instance per request or share a
    single instance; both patterns are safe.
    """

    # ── Public API ─────────────────────────────────────────────────────────

    def detect_from_path(self, image_path: str | Path) -> list[dict]:
        """
        Run detection on a local file path.

        Parameters
        ----------
        image_path : str | Path
            Absolute or relative path to a JPEG, PNG, or WEBP image.

        Returns
        -------
        list[dict]
            Raw detection dicts (see module docstring for schema).
        """
        if _use_mock():
            return self._mock_detections()

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: '{path}'")

        with path.open("rb") as fh:
            return self._post_image(fh, filename=path.name)

    def detect_from_file(self, file_obj: BinaryIO, filename: str = "image.jpg") -> list[dict]:
        """
        Run detection on an open file-like object (e.g. Django UploadedFile).

        Parameters
        ----------
        file_obj : BinaryIO
            Readable binary stream.
        filename : str
            Filename hint used to set the correct MIME type on the request.

        Returns
        -------
        list[dict]
            Raw detection dicts.
        """
        if _use_mock():
            return self._mock_detections()

        return self._post_image(file_obj, filename=filename)

    def detect_full(self, image_path: str | Path) -> dict[str, Any]:
        """
        Like detect_from_path but returns the full response payload,
        including image_width, image_height, and inference parameters.

        Returns
        -------
        dict
            Full JSON response from POST /detect.
        """
        if _use_mock():
            return self._mock_full_response()

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: '{path}'")

        with path.open("rb") as fh:
            return self._post_image_full(fh, filename=path.name)

    def health(self) -> dict[str, Any]:
        """
        Call GET /health on the YOLO service.

        Returns
        -------
        dict
            Health response payload.

        Raises
        ------
        YOLOServiceError
            If the service is unreachable or returns a non-200 status.
        """
        url = f"{_service_url()}/health"
        try:
            response = requests.get(url, timeout=_timeout())
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise YOLOServiceError(
                f"YOLO service health check failed ({url}): {exc}"
            ) from exc

    # ── Internal helpers ───────────────────────────────────────────────────

    def _post_image(self, file_obj: BinaryIO, filename: str) -> list[dict]:
        """Post image to /detect and return the detections list."""
        return self._post_image_full(file_obj, filename)["detections"]

    def _post_image_full(self, file_obj: BinaryIO, filename: str) -> dict[str, Any]:
        """Post image to /detect and return the full response dict."""
        url = f"{_service_url()}/detect"
        content_type = _mime_type_for(filename)

        try:
            response = requests.post(
                url,
                files={"file": (filename, file_obj, content_type)},
                timeout=_timeout(),
            )
        except requests.ConnectionError as exc:
            raise YOLOServiceError(
                f"Cannot connect to YOLO service at '{url}'. "
                "Is the service running? Check YOLO_SERVICE_URL in settings."
            ) from exc
        except requests.Timeout as exc:
            raise YOLOServiceError(
                f"YOLO service request timed out after {_timeout()}s."
            ) from exc
        except requests.RequestException as exc:
            raise YOLOServiceError(f"YOLO service request failed: {exc}") from exc

        if response.status_code == 415:
            raise YOLOServiceError(
                f"YOLO service rejected the file type for '{filename}'. "
                "Use JPEG, PNG, or WEBP images."
            )

        if not response.ok:
            raise YOLOServiceError(
                f"YOLO service returned HTTP {response.status_code}: {response.text[:200]}"
            )

        data = response.json()
        logger.debug(
            "YOLO service returned %d detection(s) for '%s'.",
            len(data.get("detections", [])),
            filename,
        )
        return data

    # ── Mock data (for tests / CI) ─────────────────────────────────────────

    @staticmethod
    def _mock_detections() -> list[dict]:
        """
        Fixture detections returned when USE_MOCK_YOLO=True.
        Class names should match DetectionClassMapping fixtures in the DB.
        """
        return [
            {
                "class_id": 0,
                "class_name": "coca_cola_500ml",
                "confidence": 0.91,
                "bbox": {"x1": 120.0, "y1": 80.0, "x2": 300.0, "y2": 410.0},
            },
            {
                "class_id": 0,
                "class_name": "coca_cola_500ml",
                "confidence": 0.88,
                "bbox": {"x1": 340.0, "y1": 90.0, "x2": 510.0, "y2": 420.0},
            },
        ]

    @staticmethod
    def _mock_full_response() -> dict[str, Any]:
        return {
            "image_width": 1280,
            "image_height": 720,
            "detections": YOLOClient._mock_detections(),
            "model_path": "models/best.pt",
            "confidence_threshold": 0.25,
            "iou_threshold": 0.45,
            "image_size": 640,
        }


# ── Convenience function ───────────────────────────────────────────────────


def _mime_type_for(filename: str) -> str:
    """Return the MIME type based on file extension."""
    ext = Path(filename).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")
