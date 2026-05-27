# Latency Instrumentation — Implementation Summary

> This document is written for AI consumption.
> It describes exactly what was changed, why, and how to use the results.

---

## Project context

Cashier-assisted point-of-sale automation system.

- **Backend**: Django + Django REST Framework, running on `localhost:8000`
- **YOLO service**: Separate FastAPI microservice on `localhost:8061`
- **Detection flow**: Client POSTs image → Django → HTTP POST to yolo_service → raw detections → product DB lookup → draft checkout items → JSON response

The detection endpoint is `POST /api/vision/detect/`.

---

## What was changed (and what was NOT)

### Changed files

#### 1. `backend/apps/vision/services.py`

**What changed**: Added `import time` and `time.perf_counter()` probes around each major stage inside `run_detection_for_checkout()`. Added a `timing: dict` field to the `DetectionResult` dataclass.

**What did NOT change**: Detection logic, confidence thresholds (`0.80` auto-accept, `0.50` low-conf reject), product mapping, receipt/draft-item aggregation, audit logging, error handling, model path, YOLO client.

The five timing stages measured:

| Stage | Code location | What it covers |
|---|---|---|
| `yolo_inference_ms` | Around `client.detect_from_path(...)` | Full HTTP round-trip to yolo_service (includes YOLO model inference + NMS). Near-zero when `USE_MOCK_YOLO=True`. |
| `postprocess_ms` | Around the detection loop, minus DB time | Iterating raw detections, parsing bbox dicts, confidence filtering, building `DetectedObject` instances. |
| `product_lookup_ms` | Accumulated inside the loop around `get_product_for_detection_class(class_name)` | One DB query per detection to `DetectionClassMapping` → `Product`. |
| `receipt_build_ms` | Around the `transaction.atomic()` block | `DetectedObject.objects.bulk_create()` + `add_detection_results_to_checkout()` (groups by product, creates `CheckoutItem` records). |
| `total_backend_ms` | From function entry to return | All stages above plus `DetectionRun.objects.create()` and `ModelVersion` query at the top. |

#### 2. `backend/apps/vision/views.py`

**What changed**: One line added to `VisionDetectAPIView.post()` — `"timing": result.timing` in the `Response(...)` dict.

**What did NOT change**: Everything else.

#### 3. `scripts/benchmark_api_latency.py` (new file)

Benchmark script. See usage section below.

#### 4. `thesis/BENCHMARK_README.md` (new file)

Human-readable documentation.

---

## New API response format

`POST /api/vision/detect/` now returns:

```json
{
  "detection_run_id": 42,
  "status": "COMPLETED",
  "detections": [
    {
      "id": 1,
      "class_name": "coca_cola_500ml",
      "confidence": 0.91,
      "bbox_x1": 120.0,
      "bbox_y1": 80.0,
      "bbox_x2": 300.0,
      "bbox_y2": 410.0,
      "matched_product": 5,
      "review_status": "AUTO_ACCEPTED"
    }
  ],
  "draft_items": [
    {
      "product_id": 5,
      "product_name": "Coca Cola",
      "quantity": "2.000",
      "unit_price": "35.00",
      "subtotal": "70.00",
      "source": "VISION",
      "needs_review": false
    }
  ],
  "timing": {
    "yolo_inference_ms": 148.72,
    "postprocess_ms": 3.41,
    "product_lookup_ms": 2.85,
    "receipt_build_ms": 6.13,
    "total_backend_ms": 172.44
  }
}
```

The `timing` field is always present on a 200 response. All values are floats in milliseconds, rounded to 3 decimal places.

---

## Benchmark script

### Location

`scripts/benchmark_api_latency.py`

### What it does

For each image in the test set:
1. Creates a fresh `CheckoutSession` via `POST /api/checkout/sessions/`.
2. POSTs the image to `POST /api/vision/detect/`.
3. Records all `timing` fields from the response.
4. Records `client_total_ms` (wall-clock from just before the POST to just after).
5. Writes one row per image to a CSV file.
6. Prints a summary table (mean / min / max / std) for each timing column.

### Defaults

```python
API_BASE_URL = "http://127.0.0.1:8000"
IMAGE_DIR    = "explore/jan/dataset_split/images/test"   # 91 real test images
OUTPUT_CSV   = "api_latency_results.csv"
```

### Run command

```bash
# From repo root, venv active:
python scripts/benchmark_api_latency.py

# With overrides:
python scripts/benchmark_api_latency.py \
    --api-url http://127.0.0.1:8000 \
    --image-dir explore/jan/dataset_split/images/test \
    --output api_latency_results.csv \
    --limit 20
```

### Prerequisites

```bash
pip install requests pandas
# Backend must be running:
python backend/manage.py runserver
# YOLO service must be running (if USE_MOCK_YOLO=False):
uvicorn app.main:app --host 0.0.0.0 --port 8061   # from yolo_service/
```

---

## CSV output columns

| Column | Type | Description |
|---|---|---|
| `image` | str | Filename |
| `checkout_session_id` | int | Django session id created for this request |
| `http_status` | int | HTTP status code (200 = success) |
| `error` | str | Error message or empty string |
| `yolo_inference_ms` | float | Backend: YOLO service round-trip |
| `postprocess_ms` | float | Backend: detection post-processing |
| `product_lookup_ms` | float | Backend: DB product lookup |
| `receipt_build_ms` | float | Backend: draft item aggregation |
| `total_backend_ms` | float | Backend: total processing time |
| `client_total_ms` | float | Client: full HTTP request wall-clock |
| `detections_count` | int | Raw YOLO detections returned |
| `draft_items_count` | int | Draft checkout items created |

---

## Notes for thesis Engineering Calculations

- **`total_backend_ms`** is the primary latency metric — time the server spends processing one detection request.
- **`yolo_inference_ms`** isolates the YOLO model contribution. Typically dominates (>80% of total).
- **`client_total_ms - total_backend_ms`** = network + HTTP serialization overhead (near-zero on loopback).
- **`USE_MOCK_YOLO`** must be `False` in `backend/.env` to get real inference timings. With mock mode the YOLO stage is ~0 ms.
- Each image uses a fresh session, so results are independent.
- Discard the first 3–5 rows if Django's ORM connection pool is cold.

---

## Implementation notes for AI

- `DetectionResult` is a frozen dataclass. Adding `timing: dict = field(default_factory=dict)` is backward-compatible — existing callers that only access `.detection_run` and `.draft_items` are unaffected.
- The `postprocess_ms` value is computed as `(loop_end - loop_start) * 1000 - product_lookup_accumulated_ms` to avoid double-counting the DB time that happens inside the same loop.
- No Django migration is needed — no model fields were changed.
- The benchmark script creates one `CheckoutSession` per image. These sessions remain in `OPEN` status after the benchmark. They can be cleaned up with `python manage.py shell -c "from apps.checkout.models import CheckoutSession; CheckoutSession.objects.filter(status='OPEN').delete()"` if needed.
