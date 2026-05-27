#!/usr/bin/env python3
"""Benchmark YOLO inference speed for the thesis project.

Supports two modes:
- local  : run Ultralytics YOLO directly (reports preprocess/inference/postprocess)
- service: call the FastAPI yolo_service (reports end-to-end request latency)

Defaults are wired to this repo:
- images: explore/jan/dataset_split/images/test
- weights: yolo_service/models/best.pt

Example:
  source .venv/bin/activate
  python scripts/benchmark_yolo_inference.py --mode local --device cuda:0 --runs 3 --limit 50

Output:
  - CSV with one row per (image, run)
  - JSON metadata for reproducibility (versions, device, params)
"""

from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import platform
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class BenchmarkParams:
    mode: str
    weights: str
    images_dir: str
    imgsz: int
    conf: float
    iou: float
    device: str
    half: bool
    warmup: int
    runs: int
    limit: int
    service_url: str


def iter_images(images_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for p in sorted(images_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            paths.append(p)
    return paths


def percentile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    if q <= 0:
        return min(values)
    if q >= 100:
        return max(values)

    xs = sorted(values)
    k = (len(xs) - 1) * (q / 100.0)
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def summarize(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    return {
        "count": float(len(values)),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "p90": percentile(values, 90),
        "p95": percentile(values, 95),
        "p99": percentile(values, 99),
        "max": max(values),
        "min": min(values),
    }


def _maybe_torch_cuda_sync(device: str) -> None:
    try:
        import torch

        # Ultralytics accepts CUDA devices like "0" or "0,1".
        # We treat anything not explicitly CPU as CUDA *only if* torch sees CUDA.
        if device != "cpu" and torch.cuda.is_available():
            torch.cuda.synchronize()
    except Exception:
        return


def normalize_ultralytics_device(device: str) -> str:
    """Normalize CLI device strings into Ultralytics-friendly values.

    Ultralytics device examples:
      - "cpu"
      - "0" (CUDA GPU 0)
      - "0,1" (multi-GPU)

    This repo/user habit often uses "cuda:0"; we convert that to "0".
    If CUDA is not available, we fall back to "cpu".
    """

    d = (device or "").strip().lower()

    try:
        import torch

        cuda_ok = bool(torch.cuda.is_available())
    except Exception:
        cuda_ok = False

    if d in {"", "auto"}:
        return "0" if cuda_ok else "cpu"

    if d in {"cpu"}:
        return "cpu"

    if d in {"cuda", "gpu"}:
        return "0" if cuda_ok else "cpu"

    if d.startswith("cuda:"):
        d = d.split(":", 1)[1].strip()

    # If user requested CUDA devices but CUDA isn't available, fall back.
    if not cuda_ok:
        if d.isdigit() or "," in d:
            return "cpu"

    return d


def collect_env_metadata(params: BenchmarkParams) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version,
        "platform": platform.platform(),
        "params": asdict(params),
    }

    # Optional runtime details.
    try:
        import ultralytics

        meta["ultralytics_version"] = getattr(ultralytics, "__version__", "unknown")
    except Exception:
        pass

    try:
        import torch

        meta["torch_version"] = getattr(torch, "__version__", "unknown")
        meta["torch_cuda_version"] = getattr(torch.version, "cuda", None)
        meta["cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            meta["cuda_device_count"] = int(torch.cuda.device_count())
            # If device is 'cuda' or 'cuda:0', report the resolved index.
            try:
                idx = 0
                if ":" in params.device:
                    idx = int(params.device.split(":", 1)[1])
                meta["cuda_device_index"] = idx
                meta["cuda_device_name"] = torch.cuda.get_device_name(idx)
            except Exception:
                pass
    except Exception:
        pass

    return meta


def benchmark_local(
    image_paths: list[Path],
    params: BenchmarkParams,
    timeout_s: float,
) -> list[dict[str, Any]]:
    try:
        from ultralytics import YOLO
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Ultralytics is not available in this interpreter. "
            "Run with the repo root venv: source .venv/bin/activate"
        ) from exc

    weights_path = Path(params.weights)
    if not weights_path.exists():
        raise FileNotFoundError(f"Weights not found: {weights_path}")

    model = YOLO(str(weights_path))

    # Warm-up
    warm = min(params.warmup, len(image_paths))
    for p in image_paths[:warm]:
        _ = model.predict(
            source=str(p),
            imgsz=params.imgsz,
            conf=params.conf,
            iou=params.iou,
            device=params.device,
            half=params.half,
            verbose=False,
        )

    records: list[dict[str, Any]] = []

    for img_idx, img_path in enumerate(image_paths, start=1):
        for run_idx in range(1, params.runs + 1):
            # Optional timeout guard (very rough): stop if per-image exceeds timeout.
            start = time.perf_counter()
            _maybe_torch_cuda_sync(params.device)
            results = model.predict(
                source=str(img_path),
                imgsz=params.imgsz,
                conf=params.conf,
                iou=params.iou,
                device=params.device,
                half=params.half,
                verbose=False,
            )
            _maybe_torch_cuda_sync(params.device)
            end = time.perf_counter()

            total_ms = (end - start) * 1000.0

            r0 = results[0]
            speed = getattr(r0, "speed", {}) or {}
            boxes = getattr(r0, "boxes", None)
            detections = int(len(boxes)) if boxes is not None else 0

            records.append(
                {
                    "image": img_path.name,
                    "image_index": img_idx,
                    "run": run_idx,
                    "preprocess_ms": speed.get("preprocess"),
                    "inference_ms": speed.get("inference"),
                    "postprocess_ms": speed.get("postprocess"),
                    "total_ms": total_ms,
                    "detections": detections,
                }
            )

            if timeout_s > 0 and total_ms / 1000.0 > timeout_s:
                raise TimeoutError(
                    f"Single inference exceeded timeout ({timeout_s}s): {img_path.name}"
                )

        if img_idx % 10 == 0:
            print(f"[{img_idx}/{len(image_paths)}] local benchmark progress")

    return records


def benchmark_service(
    image_paths: list[Path],
    params: BenchmarkParams,
    timeout_s: float,
) -> list[dict[str, Any]]:
    import requests

    detect_url = params.service_url.rstrip("/") + "/detect"
    health_url = params.service_url.rstrip("/") + "/health"

    # Preflight
    health = requests.get(health_url, timeout=min(10.0, timeout_s or 10.0)).json()
    if not bool(health.get("model_loaded")):
        raise RuntimeError(
            f"yolo_service reachable but model_loaded=false. model_path={health.get('model_path')}"
        )

    records: list[dict[str, Any]] = []

    for img_idx, img_path in enumerate(image_paths, start=1):
        mime, _ = mimetypes.guess_type(str(img_path))
        mime = mime or "application/octet-stream"

        for run_idx in range(1, params.runs + 1):
            start = time.perf_counter()
            with img_path.open("rb") as f:
                resp = requests.post(
                    detect_url,
                    files={"file": (img_path.name, f, mime)},
                    timeout=timeout_s if timeout_s > 0 else None,
                )
            end = time.perf_counter()

            total_ms = (end - start) * 1000.0

            resp.raise_for_status()
            data = resp.json()
            detections = int(len(data.get("detections") or []))

            records.append(
                {
                    "image": img_path.name,
                    "image_index": img_idx,
                    "run": run_idx,
                    "total_ms": total_ms,
                    "detections": detections,
                    "http_status": int(resp.status_code),
                }
            )

        if img_idx % 10 == 0:
            print(f"[{img_idx}/{len(image_paths)}] service benchmark progress")

    return records


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        raise ValueError("No records to write")

    # Stable column order.
    columns: list[str] = []
    for r in records:
        for k in r.keys():
            if k not in columns:
                columns.append(k)

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        for r in records:
            w.writerow(r)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Benchmark YOLO inference speed.")
    parser.add_argument(
        "--mode",
        choices=["local", "service"],
        default="local",
        help="Benchmark mode: local (Ultralytics) or service (FastAPI).",
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=Path("explore/jan/dataset_split/images/test"),
        help="Directory of input images.",
    )
    parser.add_argument(
        "--weights",
        type=Path,
        default=Path("yolo_service/models/best.pt"),
        help="Path to YOLO weights (local mode only).",
    )
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size.")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold.")
    parser.add_argument("--iou", type=float, default=0.45, help="IoU threshold (NMS).")
    parser.add_argument(
        "--device",
        default="auto",
        help=(
            "Device for local mode: auto (default), cpu, cuda:0, or Ultralytics-style '0'/'0,1'. "
            "If CUDA is not available, auto/cuda requests fall back to cpu."
        ),
    )
    parser.add_argument(
        "--half",
        action="store_true",
        help="Use FP16 in local mode (only meaningful on CUDA).",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=5,
        help="Number of warm-up images (not timed).",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of timed runs per image.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="If set, only benchmark the first N images.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=0.0,
        help="Per-inference timeout in seconds (0 disables).",
    )
    parser.add_argument(
        "--service-url",
        default="http://127.0.0.1:8061",
        help="Base URL for service mode.",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=Path("explore/service_query/yolo_benchmark.csv"),
        help="Where to write the per-run CSV.",
    )
    parser.add_argument(
        "--meta-out",
        type=Path,
        default=Path("explore/service_query/yolo_benchmark_meta.json"),
        help="Where to write the metadata JSON.",
    )

    args = parser.parse_args(argv)

    if not args.images_dir.exists():
        print(f"Images dir not found: {args.images_dir}", file=sys.stderr)
        return 2

    image_paths = iter_images(args.images_dir)
    if args.limit and args.limit > 0:
        image_paths = image_paths[: args.limit]

    if not image_paths:
        print(f"No images found in: {args.images_dir}", file=sys.stderr)
        return 3

    resolved_device = normalize_ultralytics_device(str(args.device))
    if str(args.mode) == "local" and resolved_device == "cpu" and str(args.device).strip().lower() not in {
        "cpu",
        "auto",
        "",
    }:
        print(
            f"Warning: requested device '{args.device}' but CUDA is not available; using cpu.",
            file=sys.stderr,
        )

    params = BenchmarkParams(
        mode=str(args.mode),
        weights=str(args.weights),
        images_dir=str(args.images_dir),
        imgsz=int(args.imgsz),
        conf=float(args.conf),
        iou=float(args.iou),
        device=resolved_device,
        half=bool(args.half),
        warmup=int(args.warmup),
        runs=int(args.runs),
        limit=int(args.limit),
        service_url=str(args.service_url),
    )

    # Metadata (versions, device info, parameters)
    meta = collect_env_metadata(params)
    args.meta_out.parent.mkdir(parents=True, exist_ok=True)
    args.meta_out.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # Run
    t0 = time.perf_counter()
    if params.mode == "local":
        records = benchmark_local(image_paths, params, timeout_s=float(args.timeout))
    else:
        records = benchmark_service(image_paths, params, timeout_s=float(args.timeout or 60.0))
    t1 = time.perf_counter()

    write_csv(args.csv_out, records)

    # Print summary
    def _col(name: str) -> list[float]:
        xs: list[float] = []
        for r in records:
            v = r.get(name)
            if v is None:
                continue
            try:
                xs.append(float(v))
            except Exception:
                continue
        return xs

    total_ms = _col("total_ms")
    print("\nBenchmark summary (milliseconds)")
    print("total_ms:", summarize(total_ms))

    if params.mode == "local":
        print("preprocess_ms:", summarize(_col("preprocess_ms")))
        print("inference_ms:", summarize(_col("inference_ms")))
        print("postprocess_ms:", summarize(_col("postprocess_ms")))

    print(f"\nWrote CSV: {args.csv_out}")
    print(f"Wrote meta: {args.meta_out}")
    print(f"Wall time: {(t1 - t0):.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
