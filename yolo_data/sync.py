#!/usr/bin/env python3
"""
Copy only images that have corresponding YOLO label files.

Run this script INSIDE your YOLO folder (the one containing `labels/`).
Example:
  python3 sync_images_from_labels.py /path/to/original_images

It will copy matching images into:
  ./images/   (created if missing)

Matching rule:
  labels/<stem>.txt  -> original_images/<stem>.(jpg|jpeg|png|bmp|webp|tif|tiff)

If multiple image extensions exist for the same stem, the first found is used.
"""

from __future__ import annotations
import argparse
import shutil
from pathlib import Path

IMAGE_EXTS = [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"]

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("original_images_dir", type=str, help="Folder containing the original images")
    parser.add_argument("--labels-dir", type=str, default="labels", help="Labels directory (default: labels)")
    parser.add_argument("--out-images-dir", type=str, default="images", help="Output images directory (default: images)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be copied without copying")
    args = parser.parse_args()

    yolo_root = Path.cwd()
    labels_dir = (yolo_root / args.labels_dir).resolve()
    out_images_dir = (yolo_root / args.out_images_dir).resolve()
    original_dir = Path(args.original_images_dir).expanduser().resolve()

    if not labels_dir.is_dir():
        raise SystemExit(f"ERROR: labels dir not found: {labels_dir}")
    if not original_dir.is_dir():
        raise SystemExit(f"ERROR: original images dir not found: {original_dir}")

    out_images_dir.mkdir(parents=True, exist_ok=True)

    label_files = sorted(labels_dir.glob("*.txt"))
    if not label_files:
        raise SystemExit(f"ERROR: no .txt label files found in {labels_dir}")

    copied = 0
    missing = 0
    already = 0

    for lf in label_files:
        stem = lf.stem

        src = None
        for ext in IMAGE_EXTS:
            candidate = original_dir / f"{stem}{ext}"
            if candidate.exists():
                src = candidate
                break

        if src is None:
            missing += 1
            continue

        dst = out_images_dir / src.name
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            already += 1
            continue

        if args.dry_run:
            print(f"[DRY] copy: {src} -> {dst}")
        else:
            shutil.copy2(src, dst)
        copied += 1

    print("\nDone.")
    print(f"Labels found: {len(label_files)}")
    print(f"Copied:       {copied}")
    print(f"Already OK:   {already}")
    print(f"Missing img:  {missing}")

    if missing:
        print("\nMissing image stems (first 20):")
        # Show a few missing stems to help debug naming/extension issues
        shown = 0
        for lf in label_files:
            stem = lf.stem
            if not any((original_dir / f"{stem}{ext}").exists() for ext in IMAGE_EXTS):
                print(f"  - {stem}")
                shown += 1
                if shown >= 20:
                    break

if __name__ == "__main__":
    main()

