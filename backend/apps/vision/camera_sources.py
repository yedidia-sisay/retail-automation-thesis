"""Camera source abstraction layer.

The rest of the backend (views, services) should only call get_camera_source()
and then call .get_current_frame() on the returned object. The source type
(MOCK_FOLDER, USB, NETWORK) is an implementation detail hidden behind this
interface.

Adding a new source type later only requires:
1. Adding a new BaseCameraSource subclass here.
2. Adding the new choice to CameraConfig.SourceType.
3. Handling the new choice in get_camera_source().

Network / IP camera design
--------------------------
For NETWORK sources the frontend displays the live stream *directly* — the
browser renders the MJPEG stream (or RTSP via a proxy) without going through
Django on every frame.  Django is only involved when the cashier presses
"Capture": at that point the backend grabs a single frame from the stream,
saves it, and sends it to YOLO.

To avoid the 1-3 second reconnect penalty on every capture, NetworkCameraSource
keeps a *persistent* cv2.VideoCapture connection per stream URL in a
module-level registry.  The connection is re-opened automatically if it drops.
"""

from __future__ import annotations

import threading
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
        p = Path(folder_path)
        if not p.is_absolute():
            # Resolve relative paths against BASE_DIR so that paths like
            # "media/mock_camera/sku" work regardless of the process CWD.
            from django.conf import settings
            p = Path(settings.BASE_DIR) / p
        self._folder = p
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

# ---------------------------------------------------------------------------
# Network / IP camera source — persistent connection registry
# ---------------------------------------------------------------------------

# Module-level registry: stream_url → _PersistentCapture
# Keyed by URL so multiple CameraConfig rows pointing at the same stream
# share one connection.
_capture_registry: dict[str, "_PersistentCapture"] = {}
_registry_lock = threading.Lock()


class _PersistentCapture:
    """Wraps a cv2.VideoCapture and keeps it alive across multiple frame grabs.

    Thread-safe: a per-instance lock serialises concurrent reads.
    The connection is re-opened automatically if it drops.

    Buffer-drain strategy
    ---------------------
    MJPEG-over-HTTP streams buffer frames internally in OpenCV.  A single
    ``cap.read()`` returns the *oldest* buffered frame, which may be stale or
    partially decoded (producing the "Stream ends prematurely" warning and a
    corrupted image that YOLO cannot detect objects in).

    To get a *current* frame we drain the buffer by grabbing frames rapidly
    until the queue is empty, then decode the last one.  ``cap.grab()`` is
    used for the drain because it is much cheaper than ``cap.retrieve()`` —
    it advances the buffer pointer without decoding the frame.
    """

    # How many grab() calls to make to flush stale buffered frames.
    _DRAIN_FRAMES = 5

    def __init__(self, url: str) -> None:
        self._url = url
        self._cap = None
        self._lock = threading.Lock()

    def _open(self):
        """Open (or re-open) the VideoCapture.  Caller must hold self._lock."""
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise CameraSourceError(
                "OpenCV (opencv-python) is not installed. "
                "Install it with: pip install opencv-python-headless"
            ) from exc

        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

        cap = cv2.VideoCapture(self._url)
        if not cap.isOpened():
            raise CameraSourceError(
                f"Could not open network camera stream: {self._url}. "
                "Check the URL and that the camera is reachable."
            )
        self._cap = cap

    def _drain_and_read(self, cv2):
        """Flush stale buffered frames, then decode and return the freshest one.

        Caller must hold self._lock and self._cap must be open.
        Returns (ret, frame) like cap.read().
        """
        # Grab without decoding to advance past buffered frames.
        for _ in range(self._DRAIN_FRAMES):
            self._cap.grab()
        # Decode the frame that is now at the head of the buffer.
        return self._cap.retrieve()

    def read_frame(self) -> bytes:
        """Return the latest frame as JPEG bytes.  Re-opens on failure."""
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise CameraSourceError(
                "OpenCV (opencv-python) is not installed. "
                "Install it with: pip install opencv-python-headless"
            ) from exc

        with self._lock:
            if self._cap is None or not self._cap.isOpened():
                self._open()

            ret, frame = self._drain_and_read(cv2)
            if not ret or frame is None:
                # Buffer drain failed — try once more after re-opening.
                self._open()
                ret, frame = self._drain_and_read(cv2)
                if not ret or frame is None:
                    raise CameraSourceError(
                        f"Could not read frame from network camera: {self._url}."
                    )

            success, buffer = cv2.imencode(".jpg", frame)
            if not success:
                raise CameraSourceError("Failed to encode network camera frame as JPEG.")
            return bytes(buffer)

    def release(self) -> None:
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None


def _get_persistent_capture(url: str) -> "_PersistentCapture":
    """Return (creating if needed) the shared persistent capture for *url*."""
    with _registry_lock:
        if url not in _capture_registry:
            _capture_registry[url] = _PersistentCapture(url)
        return _capture_registry[url]


class NetworkCameraSource(BaseCameraSource):
    """Reads frames from a network/IP camera stream.

    Live-stream display
    -------------------
    For MJPEG-over-HTTP cameras (e.g. IP Webcam app's ``/video`` endpoint) the
    frontend should display the stream *directly* in an ``<img>`` tag — the
    browser renders MJPEG natively without any backend involvement.

    Use ``get_stream_url()`` to retrieve the URL to hand to the frontend.
    Use ``get_snapshot_url()`` to get a single-frame snapshot URL (e.g.
    ``/shot.jpg`` on IP Webcam) if the camera exposes one.

    Frame capture for YOLO
    ----------------------
    ``get_current_frame()`` grabs one frame for detection.  For HTTP/HTTPS
    snapshot URLs (``/shot.jpg``) it uses a plain HTTP GET — fast and reliable.
    For RTSP or MJPEG stream URLs it uses a *persistent* cv2.VideoCapture so
    the reconnect penalty only happens once.

    Supported URL patterns
    ----------------------
    - ``rtsp://user:pass@192.168.1.x:554/stream``  → OpenCV persistent cap
    - ``http://192.168.1.x:8080/video``             → persistent OpenCV cap (MJPEG)
    - ``http://192.168.1.x:8080/shot.jpg``          → HTTP GET snapshot (fastest)
    - ``http://192.168.1.x:8080/?action=snapshot``  → HTTP GET snapshot
    """

    _HTTP_TIMEOUT = 10

    def __init__(self, stream_url: str, snapshot_url: str | None = None) -> None:
        self._stream_url = stream_url
        # If a dedicated snapshot URL is provided, use it for frame capture.
        # This avoids OpenCV buffer-stale issues with MJPEG streams entirely.
        self._snapshot_url = snapshot_url or None

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    def get_stream_url(self) -> str:
        """Return the URL the frontend should use to display the live stream."""
        return self._stream_url

    def _is_rtsp(self) -> bool:
        return self._stream_url.lower().startswith("rtsp://")

    def _looks_like_snapshot_url(self) -> bool:
        """True if the URL is a single-frame HTTP endpoint (not a stream)."""
        url_lower = self._stream_url.lower()
        snapshot_hints = (
            "/shot.jpg",
            "/snapshot",
            "/capture",
            "action=snapshot",
            "action=capture",
            ".jpg",
            ".jpeg",
            ".png",
        )
        return any(hint in url_lower for hint in snapshot_hints)

    # ------------------------------------------------------------------
    # Frame acquisition
    # ------------------------------------------------------------------

    def _fetch_snapshot_via_http(self, url: str) -> bytes:
        """Fetch a single JPEG frame via HTTP GET (for snapshot endpoints)."""
        try:
            import requests
        except ImportError as exc:
            raise CameraSourceError("requests library not available.") from exc

        try:
            resp = requests.get(url, timeout=self._HTTP_TIMEOUT)
        except requests.exceptions.ConnectionError as exc:
            raise CameraSourceError(
                f"Could not connect to camera at {url}. "
                "Check the URL and that the camera is reachable."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise CameraSourceError(
                f"Connection to camera timed out: {url}."
            ) from exc
        except Exception as exc:
            raise CameraSourceError(f"HTTP request to camera failed: {exc}") from exc

        if resp.status_code != 200:
            raise CameraSourceError(
                f"Camera returned HTTP {resp.status_code} for {url}."
            )

        content_type = resp.headers.get("Content-Type", "")
        if "image/" in content_type:
            return resp.content

        if "multipart" in content_type:
            return self._extract_jpeg_from_mjpeg_response(resp)

        # Unexpected content type — return whatever we got and let the caller
        # decide if it's usable.
        return resp.content

    @staticmethod
    def _extract_jpeg_from_mjpeg_response(resp) -> bytes:  # type: ignore[no-untyped-def]
        """Read the first JPEG frame out of an MJPEG multipart response."""
        SOI = b"\xff\xd8"
        EOI = b"\xff\xd9"
        buf = b""
        for chunk in resp.iter_content(chunk_size=4096):
            buf += chunk
            start = buf.find(SOI)
            end = buf.find(EOI, start + 2) if start != -1 else -1
            if start != -1 and end != -1:
                return buf[start: end + 2]
            if len(buf) > 1_000_000:
                raise CameraSourceError(
                    "Could not find a complete JPEG frame in the MJPEG stream."
                )
        raise CameraSourceError("MJPEG stream ended before a complete frame was received.")

    def get_current_frame(self) -> bytes:
        """Return the current frame as JPEG bytes.

        Strategy (in priority order):
        1. Dedicated snapshot URL (e.g. /shot.jpg) → plain HTTP GET.
           Always fresh, no buffering, no OpenCV involved.
        2. Snapshot-looking HTTP URL → plain HTTP GET.
        3. RTSP / MJPEG stream URL → persistent cv2.VideoCapture with
           buffer drain to avoid stale/corrupted frames.
        """
        # Priority 1: explicit snapshot URL configured by the user.
        if self._snapshot_url:
            return self._fetch_snapshot_via_http(self._snapshot_url)

        # Priority 2: the stream URL itself looks like a snapshot endpoint.
        if not self._is_rtsp() and self._looks_like_snapshot_url():
            return self._fetch_snapshot_via_http(self._stream_url)

        # Priority 3: persistent OpenCV connection with buffer drain.
        cap = _get_persistent_capture(self._stream_url)
        return cap.read_frame()


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
        snapshot = (getattr(camera_config, "snapshot_url", None) or "").strip() or None
        return NetworkCameraSource(stream_url=url, snapshot_url=snapshot)

    raise CameraSourceError(f"Unknown source_type: {source_type}")
