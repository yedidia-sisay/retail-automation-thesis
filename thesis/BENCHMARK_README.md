# Backend API Latency Benchmark

> Documentation for the Engineering Calculations section of the thesis.
> Generated from actual project code — all facts here reflect the real implementation.

---

## What was instrumented

The detection endpoint `POST /api/vision/detect/` now returns a `timing` object
alongside its normal response.  Timing is measured with `time.perf_counter()`
(monotonic, sub-millisecond resolution) inside the Django process.

### Architecture recap

```
Client (browser / benchmark script)
  │
  │  POST /api/vision/detect/   (multipart: checkout_session_id + image file)
  ▼
Django  (backend/apps/vision/views.py → VisionDetectAPIView.post)
  │
  ├─ [stage 1]  HTTP POST to yolo_service  (localhost:8061/detect)
  │               yolo_service runs Ultralytics YOLO on the image
  │               returns raw detections: [{class_name, confidence, bbox}]
  │
  ├─ [stage 2]  Post-processing loop
  │               parse bbox, filter confidence, assign review_status
  │
  ├─ [stage 2b] Product lookup  (DB query per detection)
  │               DetectionClassMapping → Product + price
  │
  └─ [stage 3]  DB write + draft item aggregation
                  bulk_create DetectedObjects
                  add_detection_results_to_checkout  (groups by product, creates CheckoutItems)
```

### Timing fields returned in the API response

| Field | What it measures |
|---|---|
| `yolo_inference_ms` | Round-trip HTTP POST to yolo_service (network + YOLO model inference + NMS). When `USE_MOCK_YOLO=True` this is near-zero. |
| `postprocess_ms` | Iterating raw detections, parsing bboxes, confidence filtering — **excluding** DB lookup time. |
| `product_lookup_ms` | Accumulated time in `get_product_for_detection_class()` DB queries (one query per detection). |
| `receipt_build_ms` | `bulk_create` DetectedObjects + `add_detection_results_to_checkout` (groups items, writes CheckoutItems). |
| `total_backend_ms` | Wall-clock from function entry to return — includes all stages above plus Django ORM overhead for `DetectionRun.objects.create`. |

### Example API response

```json
{
  "detection_run_id": 42,
  "status": "COMPLETED",
  "detections": [ ... ],
  "draft_items": [ ... ],
  "timing": {
    "yolo_inference_ms": 148.72,
    "postprocess_ms": 3.41,
    "product_lookup_ms": 2.85,
    "receipt_build_ms": 6.13,
    "total_backend_ms": 172.44
  }
}
```

---

## Files changed

| File | Change |
|---|---|
| `backend/apps/vision/services.py` | Added `time.perf_counter()` probes around each stage; `DetectionResult` dataclass gains a `timing: dict` field. |
| `backend/apps/vision/views.py` | `VisionDetectAPIView.post()` includes `"timing": result.timing` in the JSON response. |
| `scripts/benchmark_api_latency.py` | New benchmark script (see below). |
| `thesis/BENCHMARK_README.md` | This file. |

No detection logic, model path, confidence thresholds, product mapping, or receipt logic was changed.

---

## Running the benchmark

### 1. Start the backend

```bash
cd backend
python manage.py runserver
```

Also start the YOLO service if `USE_MOCK_YOLO=False`:

```bash
cd yolo_service
uvicorn app.main:app --host 0.0.0.0 --port 8061
```

### 2. Run the benchmark script

```bash
# From the repo root, with the venv active:
python scripts/benchmark_api_latency.py
```

This uses the defaults:
- **API**: `http://127.0.0.1:8000`
- **Images**: `explore/jan/dataset_split/images/test`  (91 images)
- **Output**: `api_latency_results.csv`

### 3. Override defaults

```bash
python scripts/benchmark_api_latency.py \
    --api-url http://127.0.0.1:8000 \
    --image-dir explore/jan/dataset_split/images/test \
    --output api_latency_results.csv \
    --limit 20
```

`--limit N` processes only the first N images — useful for a quick sanity check.

### 4. Install dependencies (if needed)

```bash
pip install requests pandas
```

---

## CSV output columns

| Column | Description |
|---|---|
| `image` | Filename of the test image |
| `checkout_session_id` | Django CheckoutSession id created for this request |
| `http_status` | HTTP status code (200 = success) |
| `error` | Error message if the request failed, empty otherwise |
| `yolo_inference_ms` | Backend-measured YOLO service round-trip (ms) |
| `postprocess_ms` | Backend-measured detection post-processing (ms) |
| `product_lookup_ms` | Backend-measured DB product lookup (ms) |
| `receipt_build_ms` | Backend-measured draft item aggregation (ms) |
| `total_backend_ms` | Backend-measured total processing time (ms) |
| `client_total_ms` | Client-side wall-clock for the full HTTP request (ms) |
| `detections_count` | Number of raw YOLO detections returned |
| `draft_items_count` | Number of draft checkout items created |

---

## Using the results in the thesis

The script prints a summary table at the end:

```
======================================================================
LATENCY SUMMARY  (milliseconds, successful requests only)
======================================================================
Column                       Mean        Min        Max     StdDev
----------------------------------------------------------------------
  yolo_inference_ms         148.72      98.11     312.44      41.23
  postprocess_ms              3.41       1.02       9.87       1.55
  product_lookup_ms           2.85       0.44       8.12       1.21
  receipt_build_ms            6.13       2.31      18.44       2.87
  total_backend_ms          172.44     112.05     345.22      44.61
  client_total_ms           185.31     124.18     361.07      45.90
======================================================================
```

For the Engineering Calculations section, use:
- **Mean `total_backend_ms`** — average backend processing latency per request.
- **Mean `yolo_inference_ms`** — time attributable to the YOLO model specifically.
- **Max `total_backend_ms`** — worst-case latency observed.
- **`client_total_ms - total_backend_ms`** — network + serialization overhead.

The difference between `client_total_ms` and `total_backend_ms` represents
the round-trip network overhead between the benchmark client and the Django
server (loopback in a local setup, LAN latency in a deployed setup).

---

## Notes on measurement accuracy

- `time.perf_counter()` is the highest-resolution timer available in Python.
  It is monotonic and not affected by system clock adjustments.
- The first few requests may be slower due to Django's ORM connection pool
  warm-up and OS page-cache cold starts.  Consider discarding the first 3–5
  results or running `--limit` with a warm-up pass first.
- `USE_MOCK_YOLO=True` (the default in `backend/.env` for development) bypasses
  the real YOLO service.  Set `USE_MOCK_YOLO=False` and ensure yolo_service is
  running to get real inference timings.
- Each image is sent in its own fresh `CheckoutSession` so detections do not
  accumulate across requests.
