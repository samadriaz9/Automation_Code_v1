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


def _capture_frame(cap, out_path, flush_frames=4, read_retries=5):
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

            ok_write = cv2.imwrite(out_path, frame)
            if not ok_write:
                raise RuntimeError("cv2.imwrite failed")
            return
        except Exception as exc:
            last_err = exc
            time.sleep(0.05)

    raise RuntimeError(f"USB camera capture failed after retries: {last_err}")


def start_imaging_capture_pattern(
    output_root=".",
    camera_device_index=0,
    rows=4,
    cols=4,
    camera_step_per_col=350,
    petri_step_per_row=300,
    camera_reset_each_row=True,
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
        image_idx = 1
        for r in range(int(rows)):
            for c in range(int(cols)):
                img_name = f"{image_idx}.jpg"
                out_path = os.path.join(output_dir, img_name)
                _capture_frame(cap, out_path)
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
        return output_dir
    finally:
        cap.release()

