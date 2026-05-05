from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.conf import settings


@dataclass
class _LazyModel:
	model: Any | None = None
	model_path: str | None = None


class YOLOClient:
	"""Thin wrapper around YOLO inference.

	- Mock mode allows backend pipeline testing without ultralytics installed.
	- Real mode loads a .pt model via ultralytics and runs prediction.
	"""

	_lazy: _LazyModel = _LazyModel()

	def detect(self, image_path: str) -> list[dict]:
		if getattr(settings, "USE_MOCK_YOLO", True):
			return self._mock_detect(image_path=image_path)
		return self._real_detect(image_path=image_path)

	def _mock_detect(self, image_path: str) -> list[dict]:
		# NOTE: Keep class names aligned with existing DetectionClassMapping fixtures.
		return [
			{
				"class_name": "coca_cola_500ml",
				"confidence": 0.91,
				"bbox": [120, 80, 300, 410],
			},
			{
				"class_name": "coca_cola_500ml",
				"confidence": 0.88,
				"bbox": [340, 90, 510, 420],
			},
		]

	def _get_or_load_model(self):
		model_path = getattr(settings, "YOLO_MODEL_PATH", "") or ""
		if not model_path:
			raise FileNotFoundError(
				"YOLO_MODEL_PATH is not configured. Set YOLO_MODEL_PATH or enable USE_MOCK_YOLO."
			)

		path = Path(model_path)
		if not path.exists():
			raise FileNotFoundError(
				f"YOLO model file not found at '{model_path}'. Set YOLO_MODEL_PATH correctly or enable USE_MOCK_YOLO."
			)

		if self._lazy.model is not None and self._lazy.model_path == model_path:
			return self._lazy.model

		# Import lazily so mock mode works without ultralytics installed.
		try:
			from ultralytics import YOLO  # type: ignore
		except Exception as exc:
			raise RuntimeError(
				"ultralytics is not installed but USE_MOCK_YOLO is False. Install ultralytics or enable USE_MOCK_YOLO."
			) from exc

		model = YOLO(str(path))
		self._lazy.model = model
		self._lazy.model_path = model_path
		return model

	def _real_detect(self, image_path: str) -> list[dict]:
		model = self._get_or_load_model()

		# `predict` returns a list of Results (one per image).
		results = model.predict(source=image_path, verbose=False)
		if not results:
			return []

		result = results[0]
		names = getattr(result, "names", {}) or {}
		boxes = getattr(result, "boxes", None)
		if boxes is None:
			return []

		xyxy = getattr(boxes, "xyxy", None)
		conf = getattr(boxes, "conf", None)
		cls = getattr(boxes, "cls", None)
		if xyxy is None or conf is None or cls is None:
			return []

		# Convert tensors to python lists.
		xyxy_list = xyxy.tolist() if hasattr(xyxy, "tolist") else list(xyxy)
		conf_list = conf.tolist() if hasattr(conf, "tolist") else list(conf)
		cls_list = cls.tolist() if hasattr(cls, "tolist") else list(cls)

		out: list[dict] = []
		for bbox, confidence, class_idx in zip(xyxy_list, conf_list, cls_list):
			# bbox is [x1,y1,x2,y2]
			class_id = int(class_idx)
			class_name = names.get(class_id, str(class_id))
			out.append(
				{
					"class_name": str(class_name),
					"confidence": float(confidence),
					"bbox": [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])],
				}
			)
		return out
