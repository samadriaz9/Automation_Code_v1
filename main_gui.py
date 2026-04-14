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


def _bootstrap_gpio():
    """Best-effort GPIO baseline for GUI-driven runs."""
    try:
        GPIO.setwarnings(False)
    except Exception:
        pass
    try:
        GPIO.setmode(GPIO.BCM)
    except Exception:
        pass


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


def open_usb_camera_with_recovery(
    device_index=0,
    direct_tries=3,
    retry_wait_s=1.0,
    post_relay_wait_s=4.0,
    post_relay_tries=5,
):
    """
    Try to open camera multiple times, then power-cycle via relay and retry.
    Returns an opened capture or None.
    """
    for _ in range(max(1, int(direct_tries))):
        cap = open_usb_camera(device_index)
        if cap is not None:
            return cap
        time.sleep(float(retry_wait_s))

    run_relay(P7, 3)
    # Camera needs additional time after relay cycle to enumerate.
    time.sleep(float(post_relay_wait_s))

    for _ in range(max(1, int(post_relay_tries))):
        cap = open_usb_camera(device_index)
        if cap is not None:
            return cap
        time.sleep(float(retry_wait_s))
    return None


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

        self.cap = open_usb_camera_with_recovery(
            device_index=0,
            direct_tries=3,
            retry_wait_s=1.0,
            post_relay_wait_s=4.0,
            post_relay_tries=6,
        )

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
        self.root.minsize(960, 560)
        self.root.geometry(self._initial_geometry())
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        self._setup_styles()

        self.is_busy = False
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
        self.step_labels = [
            "Empty Syringe",
            "Change Media",
            "Adjust Syringe",
            "Petri Home",
            "Load Filter Paper",
            "Send to Assembly",
            "Pick Media Pad",
            "Pour Media",
            "Pick Filtration Unit",
            "Pick Filter Paper",
            "Shift Incubation",
            "Start Incubation",
            "Start Pictures",
            "Trash Transfer",
            "Sterilize",
        ]

        outer = ttk.Frame(root, padding=10, style="App.TFrame")
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        ttk.Label(
            outer,
            text="Automation Device - Main GUI",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        btn_row = ttk.Frame(outer, style="App.TFrame")
        btn_row.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        for i in range(3):
            btn_row.columnconfigure(i, weight=1)

        self.btn_step = ttk.Button(
            btn_row,
            text="Run Experiment Steps",
            command=self.open_step_popup,
            style="ActionBlue.TButton",
        )
        self.btn_step.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_all = ttk.Button(
            btn_row,
            text="Run Experiment",
            command=self.run_all_steps,
            style="ActionGreen.TButton",
        )
        self.btn_all.grid(row=0, column=1, sticky="ew", padx=4)

        self.btn_camera = ttk.Button(
            btn_row,
            text="Test Camera",
            command=self.open_camera_test,
            style="ActionOrange.TButton",
        )
        self.btn_camera.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(outer, textvariable=self.status_var, style="Status.TLabel").grid(
            row=3, column=0, sticky="w", pady=(6, 0)
        )

        self.log = tk.Text(
            outer,
            wrap=tk.WORD,
            height=16,
            font=("TkDefaultFont", 11),
            bg="#101826",
            fg="#E9F0FF",
            insertbackground="#E9F0FF",
            relief=tk.FLAT,
            padx=8,
            pady=8,
        )
        self.log.grid(row=2, column=0, sticky="nsew")

    def _setup_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("App.TFrame", background="#F3F6FB")
        style.configure("Title.TLabel", background="#F3F6FB", foreground="#16243A", font=("TkDefaultFont", 16, "bold"))
        style.configure("Status.TLabel", background="#F3F6FB", foreground="#233A5A", font=("TkDefaultFont", 11, "bold"))
        style.configure(
            "ActionBlue.TButton",
            font=("TkDefaultFont", 12, "bold"),
            padding=(10, 14),
            foreground="white",
            background="#1662D4",
            borderwidth=0,
        )
        style.map("ActionBlue.TButton", background=[("active", "#0F56BF")])
        style.configure(
            "ActionGreen.TButton",
            font=("TkDefaultFont", 12, "bold"),
            padding=(10, 14),
            foreground="white",
            background="#0C9E5E",
            borderwidth=0,
        )
        style.map("ActionGreen.TButton", background=[("active", "#09874F")])
        style.configure(
            "ActionOrange.TButton",
            font=("TkDefaultFont", 12, "bold"),
            padding=(10, 14),
            foreground="white",
            background="#D46A09",
            borderwidth=0,
        )
        style.map("ActionOrange.TButton", background=[("active", "#B45705")])
        style.configure("StepPopup.TButton", font=("TkDefaultFont", 11, "bold"), padding=(8, 10))

    def _run_with_gpio_retry(self, label, fn, *args, **kwargs):
        """Retry several times if GPIO allocation state is transiently invalid."""
        attempts = 4
        for attempt in range(1, attempts + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                msg = str(exc)
                if "GPIO not allocated" not in msg:
                    raise
                if attempt >= attempts:
                    raise
                self.write_log(
                    f"{label}: GPIO not allocated (try {attempt}/{attempts}), reinitializing GPIO"
                )
                # Do not call GPIO.cleanup() here: it can desync module-level
                # "_initialized" flags from real GPIO state and cause repeated failures.
                for reset_fn in (
                    media_dispensor_cleanup,
                    incubator_lid_cleanup,
                    suction_pipe_cleanup,
                    filteration_unit_cleanup,
                    filteration_cleanup,
                    petri_dishes_cleanup,
                    suction_lift_cleanup,
                    camera_cleanup,
                    filteration_suction_cleanup,
                    suction_cleanup,
                ):
                    try:
                        reset_fn()
                    except Exception:
                        pass
                _bootstrap_gpio()
                time.sleep(0.25)

    def _initial_geometry(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = min(sw, 1028)
        h = min(sh, 600)
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
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
        _bootstrap_gpio()
        self._run_with_gpio_retry("Media dispensor home", Media_dispensor_home)
        self._run_with_gpio_retry("Incubator lid home", incubator_lid_home)
        self._run_with_gpio_retry("Suction pipe home", suction_pipe_home)
        self._run_with_gpio_retry("Filteration unit config", filteration_unit_config)
        self._run_with_gpio_retry("Filteration flask config", filteration_flask_config)
        self._run_with_gpio_retry("Petri dishes home", petri_dishes_home)
        self._run_with_gpio_retry("Petri dishes down", petri_dishes_down, 1035)
        self._run_with_gpio_retry("Suction pump home", suction_pump_home)
        self._run_with_gpio_retry("Suction pump up", suction_pump_up, 400)
        self.initialized = True

    def open_step_popup(self):
        if self.is_busy:
            return
        popup = tk.Toplevel(self.root)
        popup.title("Run Experiment Steps")
        popup.geometry("980x560")
        popup.minsize(900, 520)
        popup.transient(self.root)

        wrapper = ttk.Frame(popup, padding=10)
        wrapper.pack(fill=tk.BOTH, expand=True)
        for c in range(3):
            wrapper.columnconfigure(c, weight=1)

        for idx in range(15):
            step_no = idx + 1
            label = self.step_labels[idx]
            btn = ttk.Button(
                wrapper,
                text=label,
                command=lambda n=step_no: self.run_specific_step(n),
                style="StepPopup.TButton",
            )
            r = idx // 3
            c = idx % 3
            btn.grid(row=r, column=c, sticky="ew", padx=6, pady=6)

        combo_btn = ttk.Button(
            wrapper,
            text="Incubate + Pictures",
            command=self.run_incubate_and_picture_flow,
            style="ActionBlue.TButton",
        )
        combo_btn.grid(row=5, column=0, columnspan=3, sticky="ew", padx=6, pady=(12, 6))

    def run_specific_step(self, step_no):
        if self.is_busy:
            return
        if step_no < 1 or step_no > 15:
            return
        self.set_busy(True, f"Running step {step_no}/15...")
        self.root.after(10, lambda: self._run_specific_step_worker(step_no))

    def run_incubate_and_picture_flow(self):
        if self.is_busy:
            return
        popup = tk.Toplevel(self.root)
        popup.title("Incubation Profile Setup")
        popup.geometry("980x560")
        popup.minsize(900, 520)
        popup.transient(self.root)

        frame = ttk.Frame(popup, padding=12, style="App.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        ttk.Label(frame, text="Round", style="Status.TLabel").grid(row=0, column=0, sticky="w", padx=6, pady=(4, 10))
        ttk.Label(frame, text="Temperature (C)", style="Status.TLabel").grid(row=0, column=1, sticky="w", padx=6, pady=(4, 10))
        ttk.Label(frame, text="Time (min)", style="Status.TLabel").grid(row=0, column=2, sticky="w", padx=6, pady=(4, 10))

        temp_vars = []
        time_vars = []

        def _spinbox(parent, var, step, min_v, max_v, precision):
            box = ttk.Frame(parent, style="App.TFrame")
            box.columnconfigure(1, weight=1)

            def _adjust(delta):
                try:
                    value = float(var.get())
                except Exception:
                    value = float(min_v)
                value = max(float(min_v), min(float(max_v), value + delta))
                var.set(f"{value:.{precision}f}" if precision > 0 else f"{int(round(value))}")

            minus_btn = tk.Button(
                box,
                text="-",
                width=3,
                bg="#D85151",
                fg="white",
                activebackground="#C44141",
                font=("TkDefaultFont", 13, "bold"),
                command=lambda: _adjust(-step),
            )
            minus_btn.grid(row=0, column=0, padx=(0, 6))

            value_lbl = tk.Label(
                box,
                textvariable=var,
                width=7,
                bg="#E8EEF8",
                fg="#1B2F4A",
                relief=tk.RIDGE,
                bd=2,
                font=("TkDefaultFont", 13, "bold"),
            )
            value_lbl.grid(row=0, column=1, sticky="ew")

            plus_btn = tk.Button(
                box,
                text="+",
                width=3,
                bg="#1C8E56",
                fg="white",
                activebackground="#187A4A",
                font=("TkDefaultFont", 13, "bold"),
                command=lambda: _adjust(step),
            )
            plus_btn.grid(row=0, column=2, padx=(6, 0))
            return box

        for i in range(5):
            round_no = i + 1
            t_var = tk.StringVar(value="37")
            m_var = tk.StringVar(value="1" if i == 0 else "0")
            temp_vars.append(t_var)
            time_vars.append(m_var)

            ttk.Label(frame, text=f"Round {round_no}", style="Status.TLabel").grid(
                row=round_no, column=0, sticky="w", padx=6, pady=8
            )
            _spinbox(frame, t_var, step=0.5, min_v=20.0, max_v=60.0, precision=1).grid(
                row=round_no, column=1, sticky="w", padx=6, pady=8
            )
            _spinbox(frame, m_var, step=1, min_v=0, max_v=120, precision=0).grid(
                row=round_no, column=2, sticky="w", padx=6, pady=8
            )

        def _start_flow():
            try:
                profiles = []
                for t_var, m_var in zip(temp_vars, time_vars):
                    temp = float(t_var.get().strip())
                    mins = float(m_var.get().strip())
                    if mins > 0:
                        profiles.append((temp, mins))
            except Exception:
                messagebox.showerror("Input Error", "Please enter valid numbers for temperatures and times.")
                return
            if not profiles:
                messagebox.showerror("Input Error", "Set at least one round with time > 0.")
                return

            popup.destroy()
            self.set_busy(True, "Running incubation profile + picture capture...")
            self.root.after(10, lambda: self._run_incubate_and_picture_worker(profiles))

        ttk.Button(frame, text="Start", style="ActionGreen.TButton", command=_start_flow).grid(
            row=6, column=1, sticky="ew", pady=(16, 4), padx=6
        )
        ttk.Button(frame, text="Cancel", style="ActionOrange.TButton", command=popup.destroy).grid(
            row=6, column=2, sticky="ew", pady=(16, 4), padx=6
        )

    def _run_incubate_and_picture_worker(self, profiles):
        try:
            self.write_log("Running combined flow: Shift -> Incubate -> Picture")
            for idx, (target_temp, minutes) in enumerate(profiles, start=1):
                self.write_log(f"Round {idx}: shift to incubation region")
                self.step_11()
                self.write_log(f"Round {idx}: incubate at {target_temp:.1f}C for {minutes:.2f} min")
                self._run_incubation(target_temp, minutes)
                self.write_log(f"Round {idx}: incubation complete, starting pictures")
                self.step_13()
            self.write_log("Final: returning incubator and stage home")
            incubator_lid_home()
            petri_dishes_home()
            self.write_log("Combined flow complete")
            self.root.after(0, lambda: self.set_busy(False, "Ready. Combined incubation+pictures completed."))
        except Exception as exc:
            self.write_log(f"ERROR: {exc}")
            self.root.after(0, lambda: self.set_busy(False, "Error occurred in combined flow."))

    def _run_specific_step_worker(self, step_no):
        try:
            self.ensure_initialized()
            step_fn = self.steps[int(step_no) - 1]
            step_fn()
            self.write_log(f"Step {step_no} complete")
            self.root.after(0, lambda: self.set_busy(False, f"Ready. Step {step_no} completed."))
        except Exception as exc:
            self.write_log(f"ERROR: {exc}")
            self.root.after(0, lambda: self.set_busy(False, "Error occurred. Check log."))

    def run_all_steps(self):
        if self.is_busy:
            return
        self.set_busy(True, "Running full experiment (15 steps)...")
        self.root.after(10, self._run_all_worker)

    def _run_all_worker(self):
        try:
            self.ensure_initialized()
            for idx in range(15):
                step_no = idx + 1
                self.write_log(f"Running step {step_no}/15")
                self.steps[idx]()
                self.write_log(f"Step {step_no} complete")
                if idx < 14:
                    time.sleep(2)  # Required delay between steps
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
        self._run_incubation(37, 1)

    def _run_incubation(self, target_temp, minutes):
        Start_incubation(float(target_temp), float(minutes))

    def _detect_camera_index(self, candidates=(0, 1, 2, 3)):
        """Return first currently openable USB camera index, else None."""
        for idx in candidates:
            cap = open_usb_camera(idx)
            if cap is None:
                continue
            try:
                ok, frame = cap.read()
                if ok and frame is not None:
                    return int(idx)
            finally:
                try:
                    cap.release()
                except Exception:
                    pass
        return None

    def step_13(self):
        self.write_log("Step 13: Start pictures")
        cam_idx = self._detect_camera_index()
        if cam_idx is None:
            # Recovery with relay on primary index, then probe again.
            cap = open_usb_camera_with_recovery(
                device_index=0,
                direct_tries=3,
                retry_wait_s=1.0,
                post_relay_wait_s=4.0,
                post_relay_tries=6,
            )
            if cap is not None:
                cam_idx = 0
                cap.release()
            else:
                cam_idx = self._detect_camera_index()
        if cam_idx is None:
            raise RuntimeError("Camera not available for imaging")
        self.write_log(f"Imaging camera index selected: /dev/video{cam_idx}")
        # Let camera stream stabilize before imaging sequence.
        time.sleep(3)

        Camera_home()
        Camera_down(2430)
        incubator_lid_home()
        petri_dishes_home()
        petri_dishes_down(3290)
        petri_dishes_up(330)
        imaging_ok = False
        imaging_errors = []
        for try_no in range(1, 4):
            try:
                start_imaging_capture_pattern(camera_device_index=cam_idx)
                imaging_ok = True
                break
            except Exception as exc:
                imaging_errors.append(str(exc))
                self.write_log(f"Imaging attempt {try_no}/3 failed: {exc}")
                # Device index can change after reconnect; probe before retry.
                new_idx = self._detect_camera_index()
                if new_idx is not None and new_idx != cam_idx:
                    cam_idx = new_idx
                    self.write_log(f"Switched imaging camera index to /dev/video{cam_idx}")
                time.sleep(2)
        if not imaging_ok:
            raise RuntimeError(f"Imaging failed after retries: {imaging_errors[-1]}")
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
    ExperimentApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
