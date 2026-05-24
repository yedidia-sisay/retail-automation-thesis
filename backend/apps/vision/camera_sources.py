"""Camera source abstraction layer.

The rest of the backend (views, services) should only call get_camera_source()
and then call .get_current_frame() on the returned object. The source type
(MOCK_FOLDER, USB, NETWORK) is an implementation detail hidden behind this
interface.

Adding a new source type later only requires:
1. Adding a new BaseCameraSource subclass here.
2. Adding the new choice to CameraConfig.SourceType.
3. Handling the new choice in get_camera_source().
"""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.vision.models import CameraConfig

# Supported image extensions for mock folder scanning.
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class CameraSourceError(Exception):
    """Raised when a camera source cannot be read."""


class BaseCameraSource(ABC):
    """Abstract base for all camera sources.

    Subclasses must implement get_current_frame(), which returns the raw bytes
    of a JPEG-encoded image frame.
    """

    @abstractmethod
    def get_current_frame(self) -> bytes:
        """Return the current frame as raw JPEG bytes.

        Raises:
            CameraSourceError: if the frame cannot be read.
        """


# ---------------------------------------------------------------------------
# Mock folder source
# ---------------------------------------------------------------------------

class MockFolderCameraSource(BaseCameraSource):
    """Cycles through .jpg/.jpeg/.png images in a folder like a fake camera.

    The cycling is time-based: the image index advances every
    `frame_interval_ms` milliseconds, so repeated calls to get_current_frame()
    will return different images over time without any external state.
    """

    def __init__(self, folder_path: str, frame_interval_ms: int = 1000) -> None:
        self._folder = Path(folder_path)
        self._interval_ms = max(frame_interval_ms, 100)  # floor at 100 ms

    def _list_images(self) -> list[Path]:
        if not self._folder.exists():
            raise CameraSourceError(
                f"Mock camera folder does not exist: {self._folder}"
            )
        images = sorted(
            p for p in self._folder.iterdir()
            if p.is_file() and p.suffix.lower() in _IMAGE_EXTENSIONS
        )
        if not images:
            raise CameraSourceError(
                f"No images found in mock camera folder: {self._folder}. "
                "Add .jpg/.jpeg/.png files to use this source."
            )
        return images

    def get_current_frame(self) -> bytes:
        images = self._list_images()
        # Advance index based on wall-clock time so the feed "cycles" naturally.
        index = int(time.time() * 1000 / self._interval_ms) % len(images)
        image_path = images[index]
        try:
            return image_path.read_bytes()
        except OSError as exc:
            raise CameraSourceError(
                f"Could not read image file: {image_path}"
            ) from exc

    def get_current_frame_path(self) -> Path:
        """Return the filesystem path of the current frame (for saving to DetectionRun)."""
        images = self._list_images()
        index = int(time.time() * 1000 / self._interval_ms) % len(images)
        return images[index]


# ---------------------------------------------------------------------------
# USB camera source
# ---------------------------------------------------------------------------

class USBCameraSource(BaseCameraSource):
    """Reads a frame from a USB camera via OpenCV VideoCapture.

    Requires opencv-python to be installed. If OpenCV is not available, a
    clear CameraSourceError is raised so the caller can handle it gracefully.
    """

    def __init__(self, device_index: int) -> None:
        self._device_index = device_index

    def get_current_frame(self) -> bytes:
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise CameraSourceError(
                "OpenCV (opencv-python) is not installed. "
                "Install it with: pip install opencv-python-headless"
            ) from exc

        cap = cv2.VideoCapture(self._device_index)
        try:
            if not cap.isOpened():
                raise CameraSourceError(
                    f"Could not open USB camera at device index {self._device_index}. "
                    "Check that the device is connected and the index is correct."
                )
            ret, frame = cap.read()
            if not ret or frame is None:
                raise CameraSourceError(
                    f"Could not read frame from USB camera at device index {self._device_index}."
                )
            success, buffer = cv2.imencode(".jpg", frame)
            if not success:
                raise CameraSourceError("Failed to encode USB camera frame as JPEG.")
            return bytes(buffer)
        finally:
            cap.release()


# ---------------------------------------------------------------------------
# Network / IP camera source
# ---------------------------------------------------------------------------

class NetworkCameraSource(BaseCameraSource):
    """Reads a frame from a network/IP camera stream via OpenCV VideoCapture.

    Requires opencv-python to be installed. If OpenCV is not available, a
    clear CameraSourceError is raised so the caller can handle it gracefully.
    """

    def __init__(self, stream_url: str) -> None:
        self._stream_url = stream_url

    def get_current_frame(self) -> bytes:
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise CameraSourceError(
                "OpenCV (opencv-python) is not installed. "
                "Install it with: pip install opencv-python-headless"
            ) from exc

        cap = cv2.VideoCapture(self._stream_url)
        try:
            if not cap.isOpened():
                raise CameraSourceError(
                    f"Could not open network camera stream: {self._stream_url}. "
                    "Check the URL and that the camera is reachable."
                )
            ret, frame = cap.read()
            if not ret or frame is None:
                raise CameraSourceError(
                    f"Could not read frame from network camera: {self._stream_url}."
                )
            success, buffer = cv2.imencode(".jpg", frame)
            if not success:
                raise CameraSourceError("Failed to encode network camera frame as JPEG.")
            return bytes(buffer)
        finally:
            cap.release()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_camera_source(camera_config: "CameraConfig") -> BaseCameraSource:
    """Return the correct BaseCameraSource for the given CameraConfig.

    This is the only function the rest of the backend should call. It hides
    all source-type branching behind a single interface.

    Raises:
        CameraSourceError: if the config is invalid or the source cannot be
            constructed (e.g. missing required field).
    """
    from apps.vision.models import CameraConfig as CC  # local import to avoid circular

    source_type = camera_config.source_type

    if source_type == CC.SourceType.MOCK_FOLDER:
        folder = (camera_config.mock_folder_path or "").strip()
        if not folder:
            raise CameraSourceError(
                "mock_folder_path is required when source_type is MOCK_FOLDER."
            )
        return MockFolderCameraSource(
            folder_path=folder,
            frame_interval_ms=camera_config.frame_interval_ms or 1000,
        )

    if source_type == CC.SourceType.USB:
        if camera_config.usb_device_index is None:
            raise CameraSourceError(
                "usb_device_index is required when source_type is USB."
            )
        return USBCameraSource(device_index=camera_config.usb_device_index)

    if source_type == CC.SourceType.NETWORK:
        url = (camera_config.stream_url or "").strip()
        if not url:
            raise CameraSourceError(
                "stream_url is required when source_type is NETWORK."
            )
        return NetworkCameraSource(stream_url=url)

    raise CameraSourceError(f"Unknown source_type: {source_type}")
