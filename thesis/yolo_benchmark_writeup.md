# YOLO inference benchmark (thesis write-up template)

Use this as a structured checklist / ready-to-paste methodology section.
Replace bracketed fields like **[FILL]** with your actual values.

## Goal

We benchmarked the inference latency of a YOLO-based object detector used in the retail checkout pipeline. The benchmark measures:

- **Model-only latency** (local Ultralytics run): preprocessing, neural network forward pass (inference), and postprocessing (NMS)
- Optionally, **end-to-end microservice latency** (HTTP): client→service request time, which includes image upload + server processing + JSON response

## Dataset / inputs

- **Image set**: `explore/jan/dataset_split/images/test`
- **Number of images**: **[FILL: N]**
- **Image formats**: JPG/PNG/WEBP (as present in the folder)
- **Image resolution**: not fixed; images kept at original size and resized internally by Ultralytics to `imgsz` (see parameters)

If reporting a figure/table, include representative sample images and/or the image size distribution.

## Model / weights

- **Model framework**: Ultralytics YOLO
- **Weights path**: `yolo_service/models/best.pt` (or **[FILL: alternative path]**)
- **Training run identifier**: **[FILL: run name / experiment ID]**
- **Model input size**: `imgsz = 640` (unless changed)

Important: report the exact model file checksum (recommended):

- SHA-256(`best.pt`) = **[FILL]**

## Benchmark implementation

We used the script [scripts/benchmark_yolo_inference.py](../scripts/benchmark_yolo_inference.py) in **local** mode (Ultralytics direct), which:

- Loads the model once
- Performs a warm-up phase (not measured)
- Runs inference on each test image
- Collects timing from two sources:
  - **Ultralytics timings**: `results[0].speed` fields (`preprocess`, `inference`, `postprocess`) in milliseconds
  - **Wall-clock latency**: measured with `time.perf_counter()` around the full prediction call

The script writes:

- A per-run CSV: `explore/service_query/yolo_benchmark.csv`
- A metadata JSON: `explore/service_query/yolo_benchmark_meta.json` (Python, Ultralytics, Torch versions, CUDA device name, and all parameters)

### Warm-up

Warm-up is required to avoid measuring one-time overhead (model load, CUDA context initialization, kernel compilation/caching). We used:

- Warm-up images: **[FILL: warmup]**
- Warm-up is excluded from reported statistics.

### Repetitions and reporting

- Runs per image: **[FILL: runs]**
- Reported statistics: mean, median, P90/P95/P99, min, max

If `runs > 1`, you can report either:

- (a) statistics over **all runs** (recommended for distribution), or
- (b) average-per-image then aggregate over images (reduces weight of repeated runs per image).

## Hardware

Report these at minimum:

- **CPU**: **[FILL: model, cores/threads]**
- **RAM**: **[FILL]**
- **GPU** (if used): **[FILL: GPU model + VRAM]**
- **Storage**: SSD/HDD (I/O can affect end-to-end service measurements)

For GPU benchmarks also report:

- CUDA version: **[FILL]**
- Driver version: **[FILL]**

## Software

Report exact versions (ideally copied from `yolo_benchmark_meta.json`):

- OS: **[FILL]**
- Python: **[FILL]**
- Ultralytics: **[FILL]**
- PyTorch: **[FILL]**

Also report whether you used:

- `device=cpu` or `device=cuda:0`
- FP32 vs FP16 (`--half`)

## Parameters

These parameters influence latency and must be stated:

- `imgsz`: input size used for inference
- `conf`: confidence threshold (affects how many boxes survive)
- `iou`: IoU threshold for NMS (affects postprocessing)
- `device`: CPU/GPU target
- `half`: FP16 enabled/disabled
- batch size: **[FILL]** (this script uses batch size 1; note explicitly)

## Measurement protocol (recommended for thesis)

To produce a defensible benchmark:

1. **Use a fixed environment**: same machine, same power mode, minimal background load
2. **Pin parameters**: same model weights and inference settings
3. **Warm-up**: exclude warm-up runs
4. **Use enough samples**: benchmark the entire test set or a clearly defined subset
5. **Report distributions**: include percentile values (P95 / P99), not only mean
6. **Separate metrics**:
   - Model-only inference time (compute)
   - End-to-end service time (compute + network/serialization)

## Interpreting results

- `inference_ms` approximates the neural network forward-pass cost.
- `postprocess_ms` depends on number of candidate detections and NMS settings; it can dominate for crowded scenes.
- End-to-end HTTP latency includes:
  - image encoding/transfer
  - server decoding
  - inference
  - JSON serialization + transfer back

## How to run (commands)

Local (Ultralytics direct):

- `source .venv/bin/activate`
- `python scripts/benchmark_yolo_inference.py --mode local --device cuda:0 --runs 3`

Service (end-to-end latency):

- Start service: `cd yolo_service && uvicorn app.main:app --host 0.0.0.0 --port 8061`
- Benchmark: `python scripts/benchmark_yolo_inference.py --mode service --runs 3`

## What to include in the thesis (minimum)

- Table: mean/median/P95 latency (ms) for `total_ms` and `inference_ms`
- Figure: latency distribution (histogram or boxplot)
- Short discussion of CPU vs GPU and FP16 vs FP32, if tested
- Clear statement of dataset, parameters, and environment (versions + hardware)
