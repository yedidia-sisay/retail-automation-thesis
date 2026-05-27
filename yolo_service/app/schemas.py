"""
Pydantic schemas for request / response contracts.

The YOLO service returns raw detections only.
No prices, no checkout logic, no Odoo references.
"""

from typing import List
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Pixel-space bounding box in [x1, y1, x2, y2] format (top-left / bottom-right)."""

    x1: float = Field(..., description="Left edge (pixels)")
    y1: float = Field(..., description="Top edge (pixels)")
    x2: float = Field(..., description="Right edge (pixels)")
    y2: float = Field(..., description="Bottom edge (pixels)")


class Detection(BaseModel):
    """A single object detection result."""

    class_id: int = Field(..., description="Integer class index from the model")
    class_name: str = Field(..., description="Human-readable class label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence [0, 1]")
    bbox: BoundingBox = Field(..., description="Bounding box in pixel coordinates")


class DetectionResponse(BaseModel):
    """Full response returned by POST /detect."""

    image_width: int = Field(..., description="Width of the submitted image in pixels")
    image_height: int = Field(..., description="Height of the submitted image in pixels")
    detections: List[Detection] = Field(default_factory=list, description="List of raw detections")
    model_path: str = Field(..., description="Path of the model that produced these results")
    confidence_threshold: float = Field(..., description="Confidence threshold used for this run")
    iou_threshold: float = Field(..., description="IOU threshold used for this run")
    image_size: int = Field(..., description="Inference image size used for this run")


class HealthResponse(BaseModel):
    """Response returned by GET /health."""

    status: str
    model_loaded: bool
    model_path: str
    message: str
