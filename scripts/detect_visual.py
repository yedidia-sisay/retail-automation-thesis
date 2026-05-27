#!/usr/bin/env python3
"""
detect_visual.py — Visual diagnostic for the capture → YOLO pipeline.

What it does:
  1. Logs into the Django backend (session auth)
  2. Hits POST /api/terminals/cashier-01/vision/detect-sku-frame/
  3. Fetches the saved frame image from media/
  4. Draws bounding boxes + labels on it
  5. Opens the result in your browser

Usage:
  .venv/bin/python scripts/detect_visual.py

Optional flags:
  --session-id N   use an existing checkout session instead of creating one
  --no-open        save the image but don't open the browser
  --out PATH       where to save the annotated image (default: /tmp/detect_visual.png)
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import webbrowser
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

# ── Config ────────────────────────────────────────────────────────────────────
BACKEND   = "http://localhost:8000"
TERMINAL  = "cashier-01"
USERNAME  = "adamreta"
PASSWORD  = "123"
MEDIA_DIR = Path(__file__).parent.parent / "backend" / "media"

# Colours per detection status
STATUS_COLOURS = {
    "AUTO_ACCEPTED":              "#00e676",   # green
    "NEEDS_REVIEW":               "#ffea00",   # yellow
    "REJECTED_LOW_CONFIDENCE":    "#ff5252",   # red
    "UNKNOWN_CLASS":              "#e040fb",   # purple
}
DEFAULT_COLOUR = "#29b6f6"  # blue fallback


# ── Helpers ───────────────────────────────────────────────────────────────────

def login(session: requests.Session) -> None:
    """Obtain a Django session cookie."""
    # First request gets the CSRF cookie (ensure_csrf_cookie on LoginView)
    session.get(f"{BACKEND}/api/auth/login/")
    csrftoken = session.cookies.get("csrftoken", "")

    r = session.post(
        f"{BACKEND}/api/auth/login/",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"X-CSRFToken": csrftoken, "Referer": BACKEND},
    )
    if r.status_code != 200:
        print(f"[ERROR] Login failed ({r.status_code}): {r.text}")
        sys.exit(1)
    print(f"[OK] Logged in as {USERNAME}")


def get_or_create_session(session: requests.Session, session_id: int | None) -> int:
    """Return an existing checkout session id or create a fresh one."""
    if session_id:
        print(f"[OK] Using existing checkout session {session_id}")
        return session_id

    csrftoken = session.cookies.get("csrftoken", "")
    r = session.post(
        f"{BACKEND}/api/checkout/sessions/",
        json={"terminal_id": TERMINAL},
        headers={"X-CSRFToken": csrftoken, "Referer": BACKEND},
    )
    if r.status_code not in (200, 201):
        print(f"[ERROR] Could not create checkout session ({r.status_code}): {r.text}")
        sys.exit(1)
    sid = r.json()["id"]
    print(f"[OK] Created checkout session {sid}")
    return sid


def run_detection(session: requests.Session, session_id: int) -> dict:
    """POST detect-sku-frame and return the full response dict."""
    csrftoken = session.cookies.get("csrftoken", "")
    r = session.post(
        f"{BACKEND}/api/terminals/{TERMINAL}/vision/detect-sku-frame/",
        json={"checkout_session_id": session_id},
        headers={"X-CSRFToken": csrftoken, "Referer": BACKEND},
    )
    if r.status_code not in (200, 201):
        msg = r.json().get("message", r.text)
        print(f"[WARN] detect-sku-frame returned {r.status_code}: {msg}")
        print("[INFO] Falling back to direct YOLO call on the most recent saved frame...")
        return run_detection_direct(session_id)
    data = r.json()
    print(f"[OK] Detection complete — run id {data.get('detection_run_id')}, "
          f"{len(data.get('detections', []))} raw detections, "
          f"{len(data.get('draft_items', []))} draft items")
    return data


def run_detection_direct(session_id: int) -> dict:
    """
    Fallback: pick the most recent frame from media/checkout_frames/ and
    send it straight to the YOLO service, bypassing the camera source.
    """
    frames_dir = MEDIA_DIR / "checkout_frames"
    if not frames_dir.exists() or not any(frames_dir.iterdir()):
        print("[ERROR] No saved frames found in media/checkout_frames/ either.")
        sys.exit(1)

    frame_path = sorted(frames_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)[0]
    print(f"[OK] Using most recent saved frame: {frame_path.name}")

    yolo_url = "http://localhost:8061/detect"
    with open(frame_path, "rb") as f:
        r = requests.post(yolo_url, files={"file": (frame_path.name, f, "image/jpeg")}, timeout=30)

    if r.status_code != 200:
        print(f"[ERROR] YOLO service returned {r.status_code}: {r.text}")
        sys.exit(1)

    yolo = r.json()
    detections = yolo.get("detections", [])
    print(f"[OK] YOLO returned {len(detections)} detection(s) directly")

    # Normalise to the same shape the Django endpoint returns
    for d in detections:
        d.setdefault("status", "AUTO_ACCEPTED")

    return {
        "detection_run_id": None,
        "status": "direct",
        "source_type": "direct-yolo",
        "message": f"Direct YOLO call on {frame_path.name}",
        "detections": detections,
        "draft_items": [],
        "_frame_path": str(frame_path),   # carry the path through
    }


def find_frame(run_id: int) -> Path | None:
    """
    Look up the DetectionRun image path via the API, then resolve it
    against the local media directory.
    """
    # The frame is stored under media/checkout_frames/
    # Walk the folder and pick the most-recently-modified file as a fallback.
    frames_dir = MEDIA_DIR / "checkout_frames"
    if not frames_dir.exists():
        return None
    files = sorted(frames_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def draw_detections(image_path: Path, detections: list[dict], draft_items: list[dict]) -> Image.Image:
    """Return a PIL image with bounding boxes and labels drawn on it."""
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    # Try to load a font; fall back to default if not available
    try:
        font      = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except OSError:
        font = font_small = ImageFont.load_default()

    iw, ih = img.size

    for det in detections:
        bbox   = det.get("bbox") or {}
        if isinstance(bbox, list):
            bbox = {"x1": bbox[0], "y1": bbox[1], "x2": bbox[2], "y2": bbox[3]} if len(bbox) == 4 else {}
        x1, y1 = float(bbox.get("x1", 0)), float(bbox.get("y1", 0))
        x2, y2 = float(bbox.get("x2", 0)), float(bbox.get("y2", 0))

        status     = det.get("status", "")
        class_name = det.get("class_name") or det.get("class_id", "?")
        confidence = float(det.get("confidence", 0))
        colour     = STATUS_COLOURS.get(status, DEFAULT_COLOUR)

        # Box
        draw.rectangle([x1, y1, x2, y2], outline=colour, width=3)
        # Semi-transparent fill
        draw.rectangle([x1, y1, x2, y2], fill=colour + "33")

        # Label background
        label = f"{class_name}  {confidence:.0%}  [{status}]"
        bbox_text = draw.textbbox((x1, y1 - 22), label, font=font)
        draw.rectangle(bbox_text, fill=colour + "cc")
        draw.text((x1, y1 - 22), label, fill="#000000", font=font)

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_x, legend_y = 10, 10
    for status_key, col in STATUS_COLOURS.items():
        draw.rectangle([legend_x, legend_y, legend_x + 16, legend_y + 16], fill=col)
        draw.text((legend_x + 22, legend_y), status_key, fill="#ffffff", font=font_small)
        legend_y += 22

    # ── Draft items summary (bottom bar) ─────────────────────────────────────
    if draft_items:
        bar_h = 28 + len(draft_items) * 22
        draw.rectangle([0, ih - bar_h, iw, ih], fill="#000000bb")
        draw.text((10, ih - bar_h + 6), "Draft items:", fill="#ffffff", font=font)
        for i, item in enumerate(draft_items):
            line = (f"  {item['product_name']}  ×{item['quantity']}"
                    f"  @ {item['unit_price']}  = {item['subtotal']}")
            draw.text((10, ih - bar_h + 28 + i * 22), line, fill="#00e676", font=font_small)

    return img


def print_summary(data: dict) -> None:
    """Pretty-print the detection result to the terminal."""
    print()
    print("─" * 60)
    print(f"  Detection run id : {data.get('detection_run_id')}")
    print(f"  Status           : {data.get('status')}")
    print(f"  Source type      : {data.get('source_type')}")
    print(f"  Message          : {data.get('message')}")
    print()

    detections = data.get("detections", [])
    if detections:
        print(f"  Raw detections ({len(detections)}):")
        for d in detections:
            bbox = d.get("bbox", {})
            if isinstance(bbox, list):
                bbox = {"x1": bbox[0], "y1": bbox[1], "x2": bbox[2], "y2": bbox[3]} if len(bbox) == 4 else {}
            print(f"    [{d.get('status','?'):30s}]  {str(d.get('class_name','?')):25s}"
                  f"  conf={float(d.get('confidence',0)):.2%}"
                  f"  bbox=({bbox.get('x1',0):.0f},{bbox.get('y1',0):.0f})"
                  f"→({bbox.get('x2',0):.0f},{bbox.get('y2',0):.0f})")
    else:
        print("  No raw detections.")

    print()
    draft_items = data.get("draft_items", [])
    if draft_items:
        print(f"  Draft items ({len(draft_items)}):")
        for item in draft_items:
            review = " ⚠ NEEDS REVIEW" if item.get("needs_review") else ""
            print(f"    {item['product_name']:30s}  ×{item['quantity']:>4}"
                  f"  @ {item['unit_price']:>8}  = {item['subtotal']:>10}{review}")
    else:
        print("  No draft items created.")
    print("─" * 60)
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Visual YOLO detection diagnostic")
    parser.add_argument("--session-id", type=int, default=None,
                        help="Reuse an existing checkout session id")
    parser.add_argument("--no-open", action="store_true",
                        help="Save the image but don't open the browser")
    parser.add_argument("--out", default="/tmp/detect_visual.png",
                        help="Output path for the annotated image")
    args = parser.parse_args()

    session = requests.Session()

    # 1. Auth
    login(session)

    # 2. Checkout session
    session_id = get_or_create_session(session, args.session_id)

    # 3. Run detection
    data = run_detection(session, session_id)

    # 4. Print summary
    print_summary(data)

    # 5. Find the saved frame
    run_id = data.get("detection_run_id")
    # Direct fallback carries the path explicitly
    if data.get("_frame_path"):
        frame_path = Path(data["_frame_path"])
    else:
        frame_path = find_frame(run_id)
    if not frame_path:
        print("[WARN] Could not find the saved frame in media/checkout_frames/.")
        print("       The annotated image cannot be generated.")
        sys.exit(0)

    print(f"[OK] Using frame: {frame_path.name}")

    # 6. Draw bounding boxes
    annotated = draw_detections(frame_path, data.get("detections", []), data.get("draft_items", []))

    # 7. Save
    out_path = args.out
    annotated.save(out_path)
    print(f"[OK] Annotated image saved → {out_path}")

    # 8. Open in browser
    if not args.no_open:
        webbrowser.open(f"file://{out_path}")
        print("[OK] Opened in browser.")


if __name__ == "__main__":
    main()
