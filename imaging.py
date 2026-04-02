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


def _capture_frame(cap, out_path, flush_frames=4):
    """Grab a fresh frame and save JPG."""
    for _ in range(max(0, int(flush_frames))):
        cap.grab()
        time.sleep(0.01)

    ok, frame = cap.read()
    if not ok:
        raise RuntimeError("USB camera frame read failed")
    cv2.imwrite(out_path, frame)


def start_imaging_capture_pattern(
    output_root=".",
    camera_device_index=0,
    rows=4,
    cols=4,
    camera_step_per_col=350,
    petri_step_per_row=300,
    settle_seconds=0.15,
):
    """
    Capture one petri dish in a serpentine grid pattern.

    Pattern:
    - Camera moves across columns.
    - Petri stage shifts between rows.
    - Row direction alternates (serpentine) to reduce travel time.

    Returns:
        output_dir path containing captured images.
    """
    output_dir = _next_exp_dir(output_root)

    cap = cv2.VideoCapture(int(camera_device_index))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open USB camera /dev/video{camera_device_index}")

    try:
        image_idx = 1
        for r in range(int(rows)):
            left_to_right = (r % 2 == 0)

            for c in range(int(cols)):
                img_name = f"{image_idx}.jpg"
                out_path = os.path.join(output_dir, img_name)
                _capture_frame(cap, out_path)
                image_idx += 1
                time.sleep(settle_seconds)

                # Move camera for next column in this row (except last col).
                if c < cols - 1:
                    if left_to_right:
                        Camera_up(int(camera_step_per_col))
                    else:
                        Camera_down(int(camera_step_per_col))
                    time.sleep(settle_seconds)

            # End-of-row reposition
            if r < rows - 1:
                # Move petri stage for next row.
                petri_dishes_up(int(petri_step_per_row))
                time.sleep(settle_seconds)

                # Return camera to row start side.
                back_steps = int((cols - 1) * camera_step_per_col)
                if back_steps > 0:
                    if left_to_right:
                        Camera_down(back_steps)
                    else:
                        Camera_up(back_steps)
                    time.sleep(settle_seconds)

        print(f"[Imaging] Capture complete: {output_dir}")
        return output_dir
    finally:
        cap.release()

