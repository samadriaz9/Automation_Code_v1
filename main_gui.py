"""
Tkinter GUI for automation workflow.

Features:
- Responsive main window for different screen sizes
- Three primary actions:
  1) Run Experiment Steps (one step per click)
  2) Run Experiment (all 15 steps with 2s delay between steps)
  3) Test Camera (USB preview with Close button)
"""

import atexit
import gc
import signal
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
from PIL import Image, ImageTk
import RPi.GPIO as GPIO

from camera_module import Camera_home, Camera_down, cleanup as camera_cleanup
from filteration_flask import (
    Filteration_flask_up,
    filteration_flask_config,
    cleanup as filteration_cleanup,
)
from filteration_suction_pump import (
    filteration_suction_pump_on,
    filteration_suction_pump_off,
    cleanup as filteration_suction_cleanup,
)
from filteration_unit import Filteration_unit_up, filteration_unit_config, cleanup as filteration_unit_cleanup
from imaging import start_imaging_capture_pattern
from incubator_lid import incubator_lid_home, incubator_lid_up, cleanup as incubator_lid_cleanup
from incubation_module import Start_incubation
from media_dispensor import (
    Media_dispensor_home,
    Media_dispensor_up,
    Media_dispensor_down,
    cleanup as media_dispensor_cleanup,
)
from petri_dishes import (
    petri_dishes_home,
    petri_dishes_down,
    petri_dishes_up,
    cleanup as petri_dishes_cleanup,
)
from relay_control import P1, P7, run_relay, cleanup as relay_cleanup
from solinoid_value_drain import cleanup as drain_solenoid_cleanup
from solinoid_value_to_filteration import (
    solinoid_value_to_filteration,
    water_level_reached,
    cleanup as solenoid_cleanup,
)
from solinoid_waste import cleanup as waste_solenoid_cleanup
from suction_pipe import suction_pipe_home, suction_pipe_up, suction_pipe_down, cleanup as suction_pipe_cleanup
from suction_pump_up_down import (
    suction_pump_home,
    suction_pump_up,
    suction_pump_down,
    cleanup as suction_lift_cleanup,
)
from upper_suction_pump import upper_suction_pump_on, upper_suction_pump_off, cleanup as suction_cleanup


_shutdown_done = False


def shutdown_all():
    global _shutdown_done
    if _shutdown_done:
        return
    _shutdown_done = True
    print("\n[Shutdown] Releasing GPIO and stopping outputs...")

    for name, fn in (
        ("filteration_suction_pump", filteration_suction_cleanup),
        ("upper_suction_pump (DC)", suction_cleanup),
        ("suction_pump_up_down", suction_lift_cleanup),
        ("relay", relay_cleanup),
        ("solenoid", solenoid_cleanup),
        ("drain_solenoid", drain_solenoid_cleanup),
        ("waste_solenoid", waste_solenoid_cleanup),
        ("filteration_flask", filteration_cleanup),
        ("filteration_unit", filteration_unit_cleanup),
        ("petri_dishes", petri_dishes_cleanup),
        ("camera", camera_cleanup),
        ("media_dispensor", media_dispensor_cleanup),
        ("suction_pipe", suction_pipe_cleanup),
        ("incubator_lid", incubator_lid_cleanup),
    ):
        try:
            fn()
        except Exception as exc:
            print(f"  Cleanup warning ({name}): {exc}")

    gc.collect()
    try:
        GPIO.cleanup()
    except Exception:
        pass
    print("[Shutdown] Done.")


def _on_sigterm(signum, frame):
    shutdown_all()
    sys.exit(0)


signal.signal(signal.SIGTERM, _on_sigterm)
atexit.register(shutdown_all)


def open_usb_camera(device_index=0):
    idx = int(device_index)
    if sys.platform.startswith("linux"):
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
    else:
        cap = cv2.VideoCapture(idx)
    if not cap.isOpened():
        return None
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass
    return cap


class CameraTestWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("USB Camera Test")
        self.win.geometry("900x650")
        self.win.minsize(500, 350)
        self.win.protocol("WM_DELETE_WINDOW", self.on_close)

        container = ttk.Frame(self.win, padding=8)
        container.pack(fill=tk.BOTH, expand=True)
        self.preview = ttk.Label(container)
        self.preview.pack(fill=tk.BOTH, expand=True)
        ttk.Button(container, text="Close", command=self.on_close).pack(anchor=tk.E, pady=(8, 0))

        self.cap = open_usb_camera(0)
        if self.cap is None:
            run_relay(P7, 3)
            time.sleep(3)
            self.cap = open_usb_camera(0)

        if self.cap is None:
            messagebox.showerror("Camera", "Camera not available even after relay cycle.")
            self.win.after(50, self.win.destroy)
            return

        self.running = True
        self.photo = None
        self.update_frame()

    def update_frame(self):
        if not getattr(self, "running", False) or self.cap is None:
            return
        ok, frame = self.cap.read()
        if ok and frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            max_w = max(300, self.win.winfo_width() - 40)
            if w > max_w:
                scale = float(max_w) / float(w)
                rgb = cv2.resize(rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            img = Image.fromarray(rgb)
            self.photo = ImageTk.PhotoImage(img)
            self.preview.configure(image=self.photo)
        self.win.after(30, self.update_frame)

    def on_close(self):
        self.running = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        # Requirement: close should switch camera off through relay cycle.
        run_relay(P7, 3)
        self.win.destroy()


class ExperimentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Automation Device Controller")
        self.root.minsize(700, 500)
        self.root.geometry(self._initial_geometry())
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        self.is_busy = False
        self.current_step = 1
        self.initialized = False

        self.steps = [
            self.step_1,
            self.step_2,
            self.step_3,
            self.step_4,
            self.step_5,
            self.step_6,
            self.step_7,
            self.step_8,
            self.step_9,
            self.step_10,
            self.step_11,
            self.step_12,
            self.step_13,
            self.step_14,
            self.step_15,
        ]

        outer = ttk.Frame(root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        ttk.Label(
            outer,
            text="Automation Device - Main GUI",
            font=("TkDefaultFont", 14, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        btn_row = ttk.Frame(outer)
        btn_row.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        for i in range(3):
            btn_row.columnconfigure(i, weight=1)

        self.btn_step = ttk.Button(btn_row, text="Run Experiment Steps", command=self.run_single_step)
        self.btn_step.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_all = ttk.Button(btn_row, text="Run Experiment", command=self.run_all_steps)
        self.btn_all.grid(row=0, column=1, sticky="ew", padx=4)

        self.btn_camera = ttk.Button(btn_row, text="Test Camera", command=self.open_camera_test)
        self.btn_camera.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        self.status_var = tk.StringVar(value="Ready. Next step: 1/15")
        ttk.Label(outer, textvariable=self.status_var).grid(row=3, column=0, sticky="w", pady=(8, 0))

        self.log = tk.Text(outer, wrap=tk.WORD, height=18)
        self.log.grid(row=2, column=0, sticky="nsew")

    def _initial_geometry(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = int(sw * 0.75)
        h = int(sh * 0.75)
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 3)
        return f"{w}x{h}+{x}+{y}"

    def set_busy(self, busy, status_text):
        self.is_busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.btn_step.config(state=state)
        self.btn_all.config(state=state)
        self.btn_camera.config(state=state)
        self.status_var.set(status_text)

    def write_log(self, text):
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.root.update_idletasks()

    def ensure_initialized(self):
        if self.initialized:
            return
        self.write_log("Initial setup: bring all modules to home/start position")
        Media_dispensor_home()
        incubator_lid_home()
        suction_pipe_home()
        filteration_unit_config()
        filteration_flask_config()
        petri_dishes_home()
        petri_dishes_down(1035)
        suction_pump_home()
        suction_pump_up(400)
        self.initialized = True

    def run_single_step(self):
        if self.is_busy:
            return
        if self.current_step > 15:
            messagebox.showinfo("Experiment", "All 15 steps already completed.")
            return
        self.set_busy(True, f"Running step {self.current_step}/15...")
        threading.Thread(target=self._run_single_step_worker, daemon=True).start()

    def _run_single_step_worker(self):
        try:
            self.ensure_initialized()
            step_fn = self.steps[self.current_step - 1]
            step_fn()
            self.write_log(f"Step {self.current_step} complete")
            self.current_step += 1
            if self.current_step <= 15:
                next_text = f"Ready. Next step: {self.current_step}/15"
            else:
                next_text = "Ready. Experiment steps completed (15/15)"
            self.root.after(0, lambda: self.set_busy(False, next_text))
        except Exception as exc:
            self.write_log(f"ERROR: {exc}")
            self.root.after(0, lambda: self.set_busy(False, "Error occurred. Check log."))

    def run_all_steps(self):
        if self.is_busy:
            return
        self.set_busy(True, "Running full experiment (15 steps)...")
        threading.Thread(target=self._run_all_worker, daemon=True).start()

    def _run_all_worker(self):
        try:
            self.ensure_initialized()
            for idx in range(15):
                self.current_step = idx + 1
                self.write_log(f"Running step {self.current_step}/15")
                self.steps[idx]()
                self.write_log(f"Step {self.current_step} complete")
                if idx < 14:
                    time.sleep(2)  # Required delay between steps
            self.current_step = 16
            self.root.after(0, lambda: self.set_busy(False, "Ready. Full experiment completed (15/15)"))
        except Exception as exc:
            self.write_log(f"ERROR: {exc}")
            self.root.after(0, lambda: self.set_busy(False, "Error occurred during full run."))

    def open_camera_test(self):
        if self.is_busy:
            return
        CameraTestWindow(self.root)

    # ---------- 15 experiment steps ----------
    def step_1(self):
        self.write_log("Step 1: Empty Syringe")
        Media_dispensor_home()

    def step_2(self):
        self.write_log("Step 2: Change media")
        Media_dispensor_home()
        Media_dispensor_up(3500)

    def step_3(self):
        self.write_log("Step 3: Adjust syringe position")
        Media_dispensor_down(800)

    def step_4(self):
        self.write_log("Step 4: Bring petri dishes home")
        incubator_lid_home()
        petri_dishes_home()
        petri_dishes_down(1035)

    def step_5(self):
        self.write_log("Step 5: Put filter paper on filtration flask")
        suction_pipe_home()
        suction_pump_home()
        filteration_unit_config()
        filteration_flask_config()
        Filteration_flask_up(1140)
        suction_pipe_up(900)
        upper_suction_pump_on(22)
        time.sleep(2)
        suction_pipe_down(600)
        time.sleep(1)
        suction_pipe_home()
        suction_pump_up(1245)
        filteration_suction_pump_on(100)
        upper_suction_pump_off()
        suction_pipe_up(400)
        time.sleep(2)
        suction_pipe_home()

    def step_6(self):
        self.write_log("Step 6: Send filter paper to assembly")
        filteration_unit_config()
        filteration_flask_config()
        Filteration_flask_up(10)
        Filteration_unit_up(850)
        time.sleep(1)
        solinoid_value_to_filteration()
        filteration_suction_pump_on(90)
        time.sleep(20)

        retries = 0
        while water_level_reached():
            retries += 1
            filteration_suction_pump_off()
            self.write_log("Water level still FULL, retrying filtration pump cycle")
            if retries >= 5:
                raise RuntimeError("Water level still FULL after 5 retries in step 6")
            filteration_suction_pump_on(90)
            time.sleep(20)
        filteration_suction_pump_off()

    def step_7(self):
        self.write_log("Step 7: Pick up media pad and petri dishes")
        suction_pump_home()
        suction_pipe_home()
        suction_pipe_up(1025)
        upper_suction_pump_on(100)
        time.sleep(2)
        suction_pipe_down(1025)
        suction_pump_up(3065)
        suction_pipe_up(300)
        upper_suction_pump_off()

    def step_8(self):
        self.write_log("Step 8: Pouring media")
        petri_dishes_home()
        petri_dishes_down(300)
        Media_dispensor_down(800)
        time.sleep(2)
        petri_dishes_down(725)

    def step_9(self):
        self.write_log("Step 9: Pick up filtration unit")
        filteration_unit_config()
        filteration_flask_config()
        Filteration_flask_up(1130)

    def step_10(self):
        self.write_log("Step 10: Pick filter paper from filtration flask")
        suction_pipe_home()
        suction_pump_home()
        suction_pump_up(1265)
        suction_pipe_up(670)
        upper_suction_pump_on(30)
        time.sleep(3)
        suction_pipe_down(670)
        suction_pump_up(1805)
        suction_pipe_up(710)
        upper_suction_pump_off()
        time.sleep(3)
        suction_pipe_home()

    def step_11(self):
        self.write_log("Step 11: Shift for incubation")
        incubator_lid_home()
        petri_dishes_home()
        petri_dishes_down(3280)
        incubator_lid_up(200)

    def step_12(self):
        self.write_log("Step 12: Start incubation")
        run_relay(P1, 1)
        Start_incubation(37, 1)

    def step_13(self):
        self.write_log("Step 13: Start pictures")
        cap = open_usb_camera(0)
        if cap is None:
            run_relay(P7, 3)
            time.sleep(3)
            cap = open_usb_camera(0)
        if cap is None:
            raise RuntimeError("Camera not available for imaging")
        cap.release()

        Camera_home()
        Camera_down(2430)
        incubator_lid_home()
        petri_dishes_home()
        petri_dishes_down(3290)
        petri_dishes_up(330)
        start_imaging_capture_pattern()
        time.sleep(0.5)
        petri_dishes_home()
        petri_dishes_down(3290)
        incubator_lid_up(200)
        run_relay(P7, 3)
        time.sleep(3)

    def step_14(self):
        self.write_log("Step 14: Put in trash")
        incubator_lid_home()
        petri_dishes_home()
        petri_dishes_down(1025)
        suction_pipe_home()
        suction_pump_home()
        suction_pump_up(3055)
        suction_pipe_up(1010)
        upper_suction_pump_on(100)
        time.sleep(2)
        suction_pipe_home()
        suction_pump_down(930)
        upper_suction_pump_off()
        suction_pipe_up(800)
        for _ in range(20):
            suction_pump_up(120)
            suction_pump_down(120)
            time.sleep(0.01)
        time.sleep(2)

    def step_15(self):
        self.write_log("Step 15: Sterilize (placeholder)")

    def on_exit(self):
        shutdown_all()
        self.root.destroy()


def main():
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    ExperimentApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
