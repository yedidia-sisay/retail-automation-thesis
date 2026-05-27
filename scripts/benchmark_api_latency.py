#!/usr/bin/env python3
"""
benchmark_api_latency.py
========================
Measure end-to-end backend latency for the checkout detection API.

For each image in IMAGE_DIR the script:
  1. Creates a fresh CheckoutSession via the API.
  2. POSTs the image to the detection endpoint.
  3. Records the timing breakdown returned by the backend (yolo_inference_ms,
     postprocess_ms, product_lookup_ms, receipt_build_ms, total_backend_ms).
  4. Records the client-side wall-clock time (client_total_ms).

Results are written to OUTPUT_CSV.  A summary table (mean / min / max / std)
is printed at the end.

Usage
-----
    # From the repo root (venv must be active):
    python scripts/benchmark_api_latency.py

    # Override defaults via CLI:
    python scripts/benchmark_api_latency.py \\
        --api-url http://127.0.0.1:8000 \\
        --image-dir explore/jan/dataset_split/images/test \\
        --output api_latency_results.csv \\
        --limit 20

Prerequisites
-------------
    pip install requests pandas
    # The Django backend must be running:
    cd backend && python manage.py runserver
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# ── Configuration (edit here or pass CLI flags) ────────────────────────────
# ---------------------------------------------------------------------------

API_BASE_URL = "http://127.0.0.1:8000"
IMAGE_DIR = "explore/jan/dataset_split/images/test"
OUTPUT_CSV = "api_latency_results.csv"

# ---------------------------------------------------------------------------

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

TIMING_COLUMNS = [
    "yolo_inference_ms",
    "postprocess_ms",
    "product_lookup_ms",
    "receipt_build_ms",
    "total_backend_ms",
    "client_total_ms",
]


def iter_images(directory: Path) -> list[Path]:
    return sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS)


def create_checkout_session(session: "requests.Session", api_base: str) -> int | None:
    """POST /api/checkout/sessions/ and return the new session id."""
    url = api_base.rstrip("/") + "/api/checkout/sessions/"
    try:
        resp = session.post(url, json={}, timeout=15)
        resp.raise_for_status()
        return int(resp.json()["id"])
    except Exception as exc:
        print(f"  [ERROR] Could not create checkout session: {exc}")
        return None


def detect_image(
    session: "requests.Session",
    api_base: str,
    checkout_session_id: int,
    image_path: Path,
) -> dict:
    """
    POST image to /api/vision/detect/ and return a result dict with timing fields.
    """
    url = api_base.rstrip("/") + "/api/vision/detect/"
    result: dict = {
        "image": image_path.name,
        "checkout_session_id": checkout_session_id,
        "http_status": None,
        "error": "",
        "yolo_inference_ms": None,
        "postprocess_ms": None,
        "product_lookup_ms": None,
        "receipt_build_ms": None,
        "total_backend_ms": None,
        "client_total_ms": None,
        "detections_count": None,
        "draft_items_count": None,
    }

    try:
        with image_path.open("rb") as fh:
            t0 = time.perf_counter()
            resp = session.post(
                url,
                data={"checkout_session_id": checkout_session_id},
                files={"image": (image_path.name, fh, "image/jpeg")},
                timeout=60,
            )
            t1 = time.perf_counter()

        result["client_total_ms"] = round((t1 - t0) * 1000.0, 3)
        result["http_status"] = resp.status_code

        if resp.status_code != 200:
            result["error"] = resp.text[:300]
            return result

        data = resp.json()
        timing = data.get("timing") or {}

        result["yolo_inference_ms"] = timing.get("yolo_inference_ms")
        result["postprocess_ms"] = timing.get("postprocess_ms")
        result["product_lookup_ms"] = timing.get("product_lookup_ms")
        result["receipt_build_ms"] = timing.get("receipt_build_ms")
        result["total_backend_ms"] = timing.get("total_backend_ms")
        result["detections_count"] = len(data.get("detections") or [])
        result["draft_items_count"] = len(data.get("draft_items") or [])

    except Exception as exc:
        result["error"] = str(exc)[:300]

    return result


def write_csv(records: list[dict], output_path: Path) -> None:
    try:
        import pandas as pd  # type: ignore

        df = pd.DataFrame(records)
        df.to_csv(output_path, index=False)
        print(f"\nResults written to: {output_path}")
    except ImportError:
        # Fallback: write with stdlib csv
        import csv

        if not records:
            return
        columns = list(records[0].keys())
        with output_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=columns)
            w.writeheader()
            w.writerows(records)
        print(f"\nResults written to: {output_path}  (pandas not available, used stdlib csv)")


def print_summary(records: list[dict]) -> None:
    print("\n" + "=" * 70)
    print("LATENCY SUMMARY  (milliseconds, successful requests only)")
    print("=" * 70)

    col_width = 22
    header = f"{'Column':<{col_width}}  {'Mean':>10}  {'Min':>10}  {'Max':>10}  {'StdDev':>10}"
    print(header)
    print("-" * len(header))

    for col in TIMING_COLUMNS:
        values = [
            float(r[col])
            for r in records
            if r.get(col) is not None and r.get("error", "") == ""
        ]
        if not values:
            print(f"  {col:<{col_width}}  {'N/A':>10}")
            continue
        mean = statistics.fmean(values)
        mn = min(values)
        mx = max(values)
        std = statistics.stdev(values) if len(values) > 1 else 0.0
        print(f"  {col:<{col_width}}  {mean:>10.2f}  {mn:>10.2f}  {mx:>10.2f}  {std:>10.2f}")

    print("=" * 70)

    total = len(records)
    errors = sum(1 for r in records if r.get("error"))
    print(f"\nTotal images processed : {total}")
    print(f"Successful             : {total - errors}")
    print(f"Failed                 : {errors}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark the checkout detection API end-to-end latency."
    )
    parser.add_argument(
        "--api-url",
        default=API_BASE_URL,
        help=f"Base URL of the Django backend (default: {API_BASE_URL})",
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=Path(IMAGE_DIR),
        help=f"Directory of test images (default: {IMAGE_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(OUTPUT_CSV),
        help=f"Output CSV path (default: {OUTPUT_CSV})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only process the first N images (0 = all)",
    )
    args = parser.parse_args(argv)

    image_dir = args.image_dir
    if not image_dir.exists():
        print(f"[ERROR] Image directory not found: {image_dir}", file=sys.stderr)
        return 2

    images = iter_images(image_dir)
    if not images:
        print(f"[ERROR] No images found in: {image_dir}", file=sys.stderr)
        return 3

    if args.limit and args.limit > 0:
        images = images[: args.limit]

    print(f"Backend URL  : {args.api_url}")
    print(f"Image dir    : {image_dir}  ({len(images)} images)")
    print(f"Output CSV   : {args.output}")
    print()

    try:
        import requests  # type: ignore
    except ImportError:
        print("[ERROR] 'requests' is not installed.  Run: pip install requests", file=sys.stderr)
        return 1

    http = requests.Session()

    records: list[dict] = []

    for idx, img_path in enumerate(images, start=1):
        # Each image gets its own checkout session so detections don't pile up.
        session_id = create_checkout_session(http, args.api_url)
        if session_id is None:
            print(f"  [{idx}/{len(images)}] SKIP  {img_path.name}  (could not create session)")
            records.append(
                {
                    "image": img_path.name,
                    "checkout_session_id": None,
                    "http_status": None,
                    "error": "Could not create checkout session",
                    **{c: None for c in TIMING_COLUMNS},
                    "detections_count": None,
                    "draft_items_count": None,
                }
            )
            continue

        result = detect_image(http, args.api_url, session_id, img_path)
        records.append(result)

        status_str = f"HTTP {result['http_status']}" if result["http_status"] else "ERROR"
        timing_str = (
            f"total_backend={result['total_backend_ms']} ms  "
            f"yolo={result['yolo_inference_ms']} ms  "
            f"client={result['client_total_ms']} ms"
            if result["total_backend_ms"] is not None
            else result["error"]
        )
        print(f"  [{idx:>3}/{len(images)}] {status_str}  {img_path.name}  {timing_str}")

    write_csv(records, args.output)
    print_summary(records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
