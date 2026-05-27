#!/usr/bin/env python3
"""Query the local YOLO FastAPI service for a folder of images and save
annotated copies with bounding boxes.

Default input:
  explore/jan/dataset_split/images/test

Default output:
  explore/service_query

Service:
  http://127.0.0.1:8061 (POST /detect with multipart field "file")

This script intentionally only saves images with drawn bounding boxes.
"""

from __future__ import annotations

import argparse
import mimetypes
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import requests
from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class ServiceUrls:
    base_url: str

    @property
    def health(self) -> str:
        return self.base_url.rstrip("/") + "/health"

    @property
    def detect(self) -> str:
        return self.base_url.rstrip("/") + "/detect"


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def iter_images(input_dir: Path) -> Iterable[Path]:
    for path in sorted(input_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
            yield path


def _color_for_class_id(class_id: int) -> tuple[int, int, int]:
    # Deterministic, reasonably distinct colors.
    palette = [
        (255, 60, 60),
        (60, 255, 60),
        (60, 140, 255),
        (255, 180, 60),
        (180, 60, 255),
        (60, 255, 220),
        (255, 60, 200),
        (200, 200, 60),
    ]
    return palette[class_id % len(palette)]


def draw_detections(image: Image.Image, detections: list[dict]) -> Image.Image:
    img = image.copy()
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.load_default()
    except Exception:  # noqa: BLE001
        font = None

    width, height = img.size
    stroke = max(2, min(width, height) // 400)

    for det in detections:
        bbox = det.get("bbox") or {}
        x1 = float(bbox.get("x1", 0))
        y1 = float(bbox.get("y1", 0))
        x2 = float(bbox.get("x2", 0))
        y2 = float(bbox.get("y2", 0))

        # Clamp + coerce.
        x1 = max(0.0, min(x1, float(width - 1)))
        y1 = max(0.0, min(y1, float(height - 1)))
        x2 = max(0.0, min(x2, float(width - 1)))
        y2 = max(0.0, min(y2, float(height - 1)))

        if x2 <= x1 or y2 <= y1:
            continue

        class_id = int(det.get("class_id", 0))
        class_name = str(det.get("class_name", class_id))
        conf = float(det.get("confidence", 0.0))

        color = _color_for_class_id(class_id)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=stroke)

        label = f"{class_name} {conf:.2f}"
        if font is not None:
            # textbbox is available in newer Pillow; fallback if missing.
            try:
                left, top, right, bottom = draw.textbbox((0, 0), label, font=font)
                text_w, text_h = right - left, bottom - top
            except Exception:  # noqa: BLE001
                text_w, text_h = draw.textsize(label, font=font)  # type: ignore[attr-defined]

            pad = 2
            tx1 = x1
            ty1 = max(0.0, y1 - (text_h + 2 * pad))
            tx2 = min(float(width - 1), x1 + text_w + 2 * pad)
            ty2 = min(float(height - 1), ty1 + text_h + 2 * pad)

            draw.rectangle([tx1, ty1, tx2, ty2], fill=color)
            draw.text((tx1 + pad, ty1 + pad), label, fill=(0, 0, 0), font=font)

    return img


def detect_one(urls: ServiceUrls, image_path: Path, timeout_s: float) -> dict:
    mime, _ = mimetypes.guess_type(str(image_path))
    mime = mime or "application/octet-stream"

    with image_path.open("rb") as f:
        resp = requests.post(
            urls.detect,
            files={"file": (image_path.name, f, mime)},
            timeout=timeout_s,
        )
    resp.raise_for_status()
    return resp.json()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Query yolo_service for detections and save boxed images.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("explore/jan/common"),
        help="Folder containing images to test.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("explore/test_query"),
        help="Folder where annotated images will be written.",
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8061",
        help="Base URL for yolo_service (default: http://127.0.0.1:8061).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="If set, only process the first N images.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing outputs (by default, skips).",
    )
    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="Skip GET /health preflight.",
    )

    args = parser.parse_args(argv)

    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir
    urls = ServiceUrls(base_url=args.url)

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_health:
        try:
            health = requests.get(urls.health, timeout=min(10.0, args.timeout)).json()
        except Exception as exc:  # noqa: BLE001
            print(
                "Could not reach yolo_service health endpoint. "
                f"Expected at: {urls.health}\n"
                "Start it with: cd yolo_service && uvicorn app.main:app --port 8061\n"
                f"Error: {exc}",
                file=sys.stderr,
            )
            return 3

        model_loaded = bool(health.get("model_loaded"))
        status = str(health.get("status", ""))
        if not model_loaded:
            print(
                f"yolo_service is reachable but model_loaded=false (status={status}).\n"
                f"Reported model_path: {health.get('model_path')}\n"
                "Fix the model path / weights and restart the service.",
                file=sys.stderr,
            )
            return 4

    images = list(iter_images(input_dir))
    if args.limit and args.limit > 0:
        images = images[: args.limit]

    if not images:
        print(f"No images found in {input_dir} (expected: {sorted(IMAGE_EXTS)}).")
        return 0

    processed = 0
    skipped = 0
    failed = 0

    for idx, image_path in enumerate(images, start=1):
        out_path = output_dir / f"{image_path.stem}_boxed.jpg"
        if out_path.exists() and not args.overwrite:
            skipped += 1
            continue

        try:
            data = detect_one(urls, image_path, timeout_s=args.timeout)
            detections = data.get("detections") or []

            with Image.open(image_path) as img:
                img = img.convert("RGB")
                boxed = draw_detections(img, detections)
                boxed.save(out_path, quality=95)

            processed += 1
            if idx % 10 == 0:
                print(f"[{idx}/{len(images)}] processed={processed} skipped={skipped} failed={failed}")

        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAILED: {image_path.name}: {exc}", file=sys.stderr)

    print(f"Done. processed={processed} skipped={skipped} failed={failed}")
    print(f"Output folder: {output_dir.resolve()}")
    return 0 if failed == 0 else 5


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
