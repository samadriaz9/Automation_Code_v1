#!/usr/bin/env python3
"""
Single-dish imaging module.

Uses current hardware modules:
- camera slider: camera_module.py
- petri stage: petri_dishes.py

Call:
    start_imaging_capture_pattern(...)
to run the capture pattern and save images.
"""

import os
import io
import contextlib
import sys
import time

import cv2
import numpy as np

from camera_module import Camera_up, Camera_down
from petri_dishes import petri_dishes_up


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def _next_exp_dir(output_root="."):
    """Create and return next sequential experiment folder: exp_01, exp_02, ..."""
    output_root = _ensure_dir(output_root)
    idx = 1
    while True:
        name = f"exp_{idx:02d}"
        path = os.path.join(output_root, name)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=False)
            return path
        idx += 1


def _capture_frame(cap, out_path, flush_frames=4, read_retries=5, square_crop=False):
    """Grab a fresh frame and save JPG (with retries for noisy streams)."""
    flush_frames = max(0, int(flush_frames))
    read_retries = max(1, int(read_retries))

    last_err = None
    for _ in range(read_retries):
        try:
            # Drop a few frames so we get something closer to current position.
            for _ in range(flush_frames):
                with contextlib.redirect_stderr(io.StringIO()):
                    cap.grab()
                time.sleep(0.01)

            with contextlib.redirect_stderr(io.StringIO()):
                ok, frame = cap.read()
            if not ok or frame is None:
                raise RuntimeError("USB camera frame read failed")

            if bool(square_crop):
                frame = _crop_center_square(frame)

            ok_write = cv2.imwrite(out_path, frame)
            if not ok_write:
                raise RuntimeError("cv2.imwrite failed")
            return
        except Exception as exc:
            last_err = exc
            time.sleep(0.05)

    raise RuntimeError(f"USB camera capture failed after retries: {last_err}")


def _crop_center_square(frame):
    """Crop a frame to a centered square (best-effort for square output)."""
    h, w = frame.shape[:2]
    side = min(w, h)
    x0 = int((w - side) / 2)
    y0 = int((h - side) / 2)
    return frame[y0 : y0 + side, x0 : x0 + side]


def _build_mosaic_from_tiles(
    output_dir,
    rows,
    cols,
    mosaic_name="mosaic.jpg",
    flip_x=False,
    flip_y=False,
    axis_swap=False,
):
    """Stitch numbered tiles (1.jpg..rows*cols.jpg) into one big image.

    flip_x: mirror along X (left/right)
    flip_y: mirror along Y (top/bottom)
    axis_swap: swap meaning of capture row/col -> mosaic row/col
    """
    rows = int(rows)
    cols = int(cols)
    total = rows * cols
    if total <= 0:
        raise ValueError("rows*cols must be > 0")

    first_path = os.path.join(output_dir, "1.jpg")
    first = cv2.imread(first_path)
    if first is None:
        raise RuntimeError(f"Could not read first tile: {first_path}")

    tile_h, tile_w = first.shape[:2]
    tile_shape_tail = first.shape[2:] if len(first.shape) > 2 else ()

    # Mosaic output size depends on whether we swap axes.
    out_rows = cols if bool(axis_swap) else rows
    out_cols = rows if bool(axis_swap) else cols
    mosaic = np.zeros((out_rows * tile_h, out_cols * tile_w) + tile_shape_tail, dtype=first.dtype)

    for r in range(rows):
        for c in range(cols):
            # Capture order is row-major: r=0..rows-1, c=0..cols-1.
            tile_idx = r * cols + c + 1
            tile_path = os.path.join(output_dir, f"{tile_idx}.jpg")
            tile = cv2.imread(tile_path)
            if tile is None:
                raise RuntimeError(f"Could not read tile: {tile_path}")

            if tile.shape[0] != tile_h or tile.shape[1] != tile_w:
                tile = cv2.resize(tile, (tile_w, tile_h), interpolation=cv2.INTER_AREA)

            # Destination coordinates in the mosaic (with optional flips).
            # If axis_swap is True, treat capture "column" as mosaic row and
            # capture "row" as mosaic column.
            if bool(axis_swap):
                base_r = c
                base_c = r
                max_r = cols - 1
                max_c = rows - 1
            else:
                base_r = r
                base_c = c
                max_r = rows - 1
                max_c = cols - 1

            dest_r = (max_r - base_r) if bool(flip_y) else base_r
            dest_c = (max_c - base_c) if bool(flip_x) else base_c

            y0 = dest_r * tile_h
            x0 = dest_c * tile_w
            mosaic[y0 : y0 + tile_h, x0 : x0 + tile_w] = tile

    mosaic_path = os.path.join(output_dir, mosaic_name)
    ok = cv2.imwrite(mosaic_path, mosaic)
    if not ok:
        raise RuntimeError(f"Could not write mosaic: {mosaic_path}")
    return mosaic_path


def start_imaging_capture_pattern(
    output_root=".",
    camera_device_index=0,
    rows=6,
    cols=6,
    camera_step_per_col=100,
    petri_step_per_row=100,
    camera_reset_each_row=True,
    square_crop=True,
    square_grid=True,
    save_mosaic=True,
    mosaic_name="mosaic.jpg",
    settle_seconds=0.15,
):
    """
    Capture one petri dish in a matrix/raster grid pattern.

    Assumptions:
    - Current camera position is the start-of-row for column 0.
    - Current petri stage position is the start-of-grid for row 0.

    Motion:
    - Slide across each row by moving camera towards "up" for each next column.
    - Shift to the next row by moving petri dishes towards "up".
    - Optionally reset camera back to column 0 after each row (needed to keep a square coverage area).

    Returns:
        output_dir path containing captured images.
    """
    output_dir = _next_exp_dir(output_root)

    idx = int(camera_device_index)
    if sys.platform.startswith("linux"):
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
    else:
        cap = cv2.VideoCapture(idx)
    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open USB camera index {idx} (/dev/video{idx}). "
            "Ensure no other code holds the device (stop preview threads first). "
            "If the device is not at video0, pass camera_device_index=..."
        )

    # Best-effort: request consistent resolution for decoding/saving.
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    except Exception:
        pass

    try:
        if bool(square_grid):
            petri_step_per_row = int(camera_step_per_col)

        image_idx = 1
        for r in range(int(rows)):
            for c in range(int(cols)):
                img_name = f"{image_idx}.jpg"
                out_path = os.path.join(output_dir, img_name)
                _capture_frame(cap, out_path, square_crop=bool(square_crop))
                image_idx += 1
                time.sleep(settle_seconds)

                # Move camera for next column in this row (except last col).
                if c < cols - 1:
                    Camera_up(int(camera_step_per_col))
                    time.sleep(settle_seconds)

            # End-of-row reposition
            if r < rows - 1:
                # Move petri stage for next row.
                petri_dishes_up(int(petri_step_per_row))
                time.sleep(settle_seconds)

                # Reset camera to column 0 for the next row (keeps square coverage).
                if bool(camera_reset_each_row):
                    back_steps = int((cols - 1) * camera_step_per_col)
                    if back_steps > 0:
                        Camera_down(back_steps)
                    time.sleep(settle_seconds)

        print(f"[Imaging] Capture complete: {output_dir}")
        if bool(save_mosaic):
            # Generate multiple orientations so you can pick the correct one quickly.
            # (The physical "up" direction vs image "top" direction can be opposite.)
            variants = []
            # row-major layout variants
            variants.extend(
                [
                    ("row_normal", False, False, mosaic_name),
                    ("row_flipX", True, False, f"flipX_{mosaic_name}"),
                    ("row_flipY", False, True, f"flipY_{mosaic_name}"),
                    ("row_flipXY", True, True, f"flipXY_{mosaic_name}"),
                ]
            )
            # axis-swapped layout variants (if camera columns map to mosaic rows)
            variants.extend(
                [
                    ("swap_normal", False, False, f"swap_{mosaic_name}"),
                    ("swap_flipX", True, False, f"swap_flipX_{mosaic_name}"),
                    ("swap_flipY", False, True, f"swap_flipY_{mosaic_name}"),
                    ("swap_flipXY", True, True, f"swap_flipXY_{mosaic_name}"),
                ]
            )

            for _, flip_x, flip_y, name in variants:
                path = _build_mosaic_from_tiles(
                    output_dir=output_dir,
                    rows=int(rows),
                    cols=int(cols),
                    mosaic_name=name,
                    flip_x=flip_x,
                    flip_y=flip_y,
                    axis_swap=bool(name.startswith("swap_")),
                )
                print(f"[Imaging] Mosaic saved: {path}")
        return output_dir
    finally:
        cap.release()

