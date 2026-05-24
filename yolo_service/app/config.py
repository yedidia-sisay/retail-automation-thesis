"""
Configuration loaded from environment variables / .env file.
All inference parameters are centralised here so nothing is hard-coded
in the detection or routing logic.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always resolve paths relative to the yolo_service/ directory,
# regardless of where uvicorn is launched from.
_SERVICE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # ── Model ──────────────────────────────────────────────────────────────
    model_path: str = "models/best.pt"

    # ── Inference hyper-parameters ─────────────────────────────────────────
    confidence_threshold: float = 0.25   # minimum confidence to keep a detection
    iou_threshold: float = 0.45          # NMS IoU threshold
    image_size: int = 640                # inference resolution (pixels)

    # ── Service ────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8061
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=str(_SERVICE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    def resolved_model_path(self) -> Path:
        """Return model_path as an absolute Path, resolved from yolo_service/."""
        p = Path(self.model_path)
        if p.is_absolute():
            return p
        return (_SERVICE_DIR / p).resolve()


settings = Settings()
