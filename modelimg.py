#!/usr/bin/env python3
import math
import os
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors
import glob

class modelsApp:
    # Configuration for YOLO Pipeline
    
    #yolo_model_weights = r'/home/ncai/Desktop/APP/best.pt'  # Path to YOLO model weights

    def __init__(self, master):
        self.master = master
        # Define GUI dimensions and colors as instance attributes
        self.BG_COLOR = "#2E3440"           # Dark blue-gray
        self.BUTTON_COLOR = "#5E81AC"       # Soft blue
        self.BUTTON_HOVER_COLOR = "#81A1C1"   # Lighter blue
        self.TEXT_COLOR = "#ECEFF4"         # Light gray
        self.main_width = 940
        self.main_height = 1080
        self.left_img_width = 480
        self.right_img_width = 500
        self.overall_width = self.left_img_width + self.main_width + self.right_img_width
        self.overall_height = self.main_height

        # For the loading overlay
        self.loading_overlay = None
        self.loading_animation_index = 0
        self.loading_cancelled = False

        # Selections
        self.selected_experiment = None
        self.selected_model_path = None
        self.experiment_buttons = []
        self.model_buttons = []

        self.setup_gui()
    
    
    
    
    @staticmethod
    def get_sorted_image_paths(base_dir):
        """Fetch images named '1.jpg' to '28.jpg' from the base directory."""
        image_paths = []
        for i in range(1, 29):
            image_name = f"{i}.jpg"
            path = os.path.join(base_dir, image_name)
            if os.path.exists(path):
                image_paths.append(path)
            else:
                print(f"Warning: {image_name} not found in {base_dir}.")
        return image_paths

    @staticmethod
    def annotate_image(image_path, model):
        """
        Run YOLO detection on an image, draw bounding boxes and labels,
        and return the annotated image along with the detected count.
        """
        image = Image.open(image_path)
        image_array = np.array(image)
        results = model(image_path, conf=0.5, verbose=False)
        annotator = Annotator(image_array, line_width=2)
        detected_count = 0
        for result in results:
            for box in result.boxes:
                xyxy = box.xyxy[0]
                conf = box.conf[0]
                cls = box.cls[0]
                label = f'{model.names[int(cls)]} {conf:.2f}'
                annotator.box_label(xyxy, label, color=colors(int(cls), True))
                detected_count += 1
        annotated_image = Image.fromarray(annotator.result())
        return annotated_image, detected_count

    @staticmethod
    def combine_images_grid(image_list, total_detected, output_dir):
        """
        Arrange the annotated images in a fixed grid pattern and overlay the total
        detected count. Assumes each image is 1280x720.
        """
        image_width, image_height = 1920, 1080
        pattern = [
            [1, 14, 15, 28],
            [2, 13, 16, 27],
            [3, 12, 17, 26],
            [4, 11, 18, 25],
            [5, 10, 19, 24],
            [6,  9, 20, 23],
            [7,  8, 21, 22]
        ]
        num_rows = len(pattern)
        num_columns = max(len(row) for row in pattern)
        combined_width = num_columns * image_width
        combined_height = num_rows * image_height

        combined_image = Image.new('RGB', (combined_width, combined_height))
        image_dict = {i: img for i, img in enumerate(image_list, start=1)}
        for row_idx, row in enumerate(pattern):
            for col_idx, num in enumerate(row):
                if num in image_dict:
                    img = image_dict[num]
                    x_offset = col_idx * image_width
                    y_offset = row_idx * image_height
                    combined_image.paste(img, (x_offset, y_offset))
        combined_image_array = np.array(combined_image)
        cv2.putText(
            combined_image_array,
            f"Total E.coli Detected: {total_detected}",
            (10, 100),
            cv2.FONT_HERSHEY_DUPLEX,
            4.8,
            (125, 246, 55),
            10
        )
        combined_image = Image.fromarray(combined_image_array)
        combined_image_path = os.path.join(output_dir,"combine_model_img.jpg")
        combined_image.save(combined_image_path)
        combined_image_path = os.path.join(output_dir, "result_"+str(total_detected)+".jpg")
        combined_image.save(combined_image_path)
        print(f"Combined image saved at {combined_image_path}")
    
    def process_images_yolo(self, base_dir, output_dir, model, on_image=None):
        """Run YOLO detection on sorted images and create the combined grid.
        on_image(index, total) is called after each image processed.
        """
        image_paths = modelsApp.get_sorted_image_paths(base_dir)
        annotated_images = []
        total_detected = 0
        total = len(image_paths)
        for idx, path in enumerate(image_paths, start=1):
            annotated, count = modelsApp.annotate_image(path, model)
            annotated_images.append(annotated)
            total_detected += count
            if on_image:
                on_image(idx, total)
        modelsApp.combine_images_grid(annotated_images, total_detected, output_dir)

    def update_main_image(self, output_dir):
        """
        Load the combined image from disk, resize it to fit the main display area,
        and update the main image label.
        """
        combined_image_path = os.path.join(output_dir, "combine_model_img.jpg")
        if os.path.exists(combined_image_path):
            try:
                img = Image.open(combined_image_path)
                # Proportional fit: preserve aspect ratio within preview area, but display at twice the size
                max_width = int(self.main_width * 0.8)
                max_height = int(self.main_height * 0.30)
                orig_width, orig_height = img.size
                if orig_width > 0 and orig_height > 0:
                    scale = min(max_width / orig_width, max_height / orig_height)
                    # Double the scale to make the image appear twice as large
                    scale = scale * 2
                    new_width = max(1, int(orig_width * scale))
                    new_height = max(1, int(orig_height * scale))
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self.main_image_label.config(image=tk_img, text="")
                self.main_image_label.image = tk_img
            except Exception as e:
                print("Error loading combined image:", e)
        else:
            print("Combined image not found!")

    def finish_processing(self, output_dir):
        """Called on the main thread when processing is complete."""
        if self.loading_overlay:
            self.hide_loading()
        self.update_main_image(output_dir)
        # Clear subfolder name when processing is complete
        self.subfolder_label.config(text="")

    def run_folder(self, base_dir, output_dir, model, total_images_in_run, progress_state):
        """Process a single subfolder, update progress, display result 5s."""
        if not os.path.isdir(base_dir):
            return 0
        image_paths = modelsApp.get_sorted_image_paths(base_dir)
        if not image_paths:
            return 0

        # Update subfolder name display
        subfolder_name = os.path.basename(base_dir)
        self.master.after(0, lambda: self.subfolder_label.config(text=f"Processing: {subfolder_name}"))

        def on_image(idx, total):
            progress_state['processed'] += 1
            self.update_progress_bar(progress_state['processed'], total_images_in_run)

        self.process_images_yolo(base_dir, output_dir, model, on_image=on_image)
        # Update image on main thread and force GUI refresh
        print(f"Processing completed for {os.path.basename(base_dir)}, updating image...")
        self.master.after(0, lambda: self.update_main_image(output_dir))
        self.master.update()  # Force immediate GUI update
        
        # Clear subfolder name after processing this folder
        self.master.after(0, lambda: self.subfolder_label.config(text=""))
        
        # Wait 5 seconds before moving to the next folder
        time_to_wait_ms = 5000
        done_event = threading.Event()
        def mark_done():
            done_event.set()
        self.master.after(time_to_wait_ms, mark_done)
        done_event.wait()
        return len(image_paths)

    def update_progress_bar(self, current, total):
        if total <= 0:
            return
        value = int((current / total) * 100)
        self.progress_var.set(value)
        self.progress_label.config(text=f"{current}/{total}")

    # ----- Methods for the animated loading overlay -----
    def show_loading(self):
        """Display an overlay with animated loading text and a cancel button."""
        # Create the overlay as a child of main_area so it stays within the main window area.
        self.loading_overlay = tk.Frame(self.main_area, bg="#333333")
        self.loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Create a label for the animated text.
        self.loading_label = tk.Label(self.loading_overlay, text="Loading", font=("Arial", 24), fg="white", bg="#333333")
        self.loading_label.pack(expand=True)
        
        # Create a Cancel button (inside the overlay) to cancel loading.
        self.loading_close_btn = tk.Button(self.loading_overlay, text="Cancel Loading", command=self.on_loading_cancel, font=("Arial", 14))
        self.loading_close_btn.pack(pady=10)
        
        # Start the simple text-based animation.
        self.loading_animation_index = 0
        self.animate_loading()

    def animate_loading(self):
        """Cycle the loading text to simulate an animation."""
        if self.loading_overlay is None:
            return
        # Cycle through 0-3 dots.
        dots = "." * (self.loading_animation_index % 4)
        self.loading_label.config(text=f"Loading{dots}")
        self.loading_animation_index += 1
        # Update every 500 ms.
        self.loading_overlay.after(500, self.animate_loading)

    def on_loading_cancel(self):
        """Handle the cancel button press on the loading overlay."""
        self.loading_cancelled = True
        self.hide_loading()
        # Note: The processing thread is still running in the background.
        # You may choose to ignore its results when complete.

    def hide_loading(self):
        """Remove the loading overlay."""
        if self.loading_overlay:
            self.loading_overlay.destroy()
            self.loading_overlay = None
    
    def select_model_file(self):
        print(" ")
    # ----- Global Close (bottom button) -----
    def on_global_close(self):
        """Cancel any loading and close the GUI."""
        if self.loading_overlay:
            self.on_loading_cancel()
        self.master.destroy()

    # ----- GUI Setup -----
    def setup_gui(self):
        # Set up the main window layout (using your original design)
        self.master.overrideredirect(True)
        self.master.geometry(f"{self.overall_width}x{self.overall_height}")
        self.master.configure(bg=self.BG_COLOR)
        self.master.resizable(False, False)

        # Custom title bar
        title_bar = tk.Frame(self.master, bg="white", relief="raised", bd=2, height=50)
        title_bar.pack(side="top", fill="x")
        try:
            icon_img = Image.open("/home/ncai/Desktop/APP/icon.png").resize((40, 40))
            icon = ImageTk.PhotoImage(icon_img)
        except Exception as e:
            print("Error loading icon:", e)
            icon = None
        title_label = tk.Label(title_bar, text=" Imaging", fg="black", bg="white",
                                font=("Arial", 30, "bold"), image=icon, compound="left")
        title_label.image = icon
        title_label.pack(side="left", padx=10, pady=5)
        #close_btn = tk.Button(title_bar, text="X", bg="red", fg="white", font=("Arial", 14, "bold"),
        #                      command=lambda: self.master.destroy(), relief="flat")
        #close_btn.pack(side="right", padx=10, pady=5)

        # Main content frame and global container
        content_frame = tk.Frame(self.master, bg=self.BG_COLOR)
        content_frame.pack(side="top", fill="both", expand=True)
        global_container = tk.Frame(content_frame, bg=self.BG_COLOR)
        global_container.grid(row=0, column=0, sticky="nsew")
        global_container.columnconfigure(0, weight=0)
        global_container.columnconfigure(1, weight=0)
        global_container.columnconfigure(2, weight=0)
        global_container.rowconfigure(0, weight=1)

        # Left Image
        try:
            left_image = Image.open("/home/ncai/Desktop/APP/image1.jpg")
        except Exception as e:
            print("Error loading left image:", e)
            left_image = Image.new("RGB", (self.left_img_width, self.main_height), color="gray")
        left_image = left_image.resize((self.left_img_width, self.main_height), Image.LANCZOS)
        left_photo = ImageTk.PhotoImage(left_image)
        left_label = tk.Label(global_container, image=left_photo, bg=self.BG_COLOR)
        left_label.image = left_photo
        left_label.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        # Main Area (Center)
        main_area = tk.Frame(global_container, width=self.main_width, height=self.main_height, bg=self.BG_COLOR)
        main_area.grid(row=0, column=1, padx=30, pady=1, sticky="nsew")
        main_area.grid_propagate(False)
        # Configure rows: subfolder label, image area, model buttons, folder buttons, controls
        main_area.rowconfigure(0, weight=0)  # Subfolder label row
        main_area.rowconfigure(1, weight=0, minsize=int(self.main_height * 0.30))  # Image row
        main_area.rowconfigure(2, weight=0)  # Model buttons row
        main_area.rowconfigure(3, weight=0)  # Folder buttons row
        main_area.rowconfigure(4, weight=0)  # Controls row
        main_area.columnconfigure(0, weight=1)
        
        # Add subfolder name label in its own row
        self.subfolder_label = tk.Label(main_area, bg=self.BG_COLOR, text="",
                                        fg=self.TEXT_COLOR, font=("Arial", 24, "bold"))
        self.subfolder_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="new")
        
        # Main image label in its own row
        self.main_image_label = tk.Label(main_area, bg=self.BG_COLOR, text="No image processed",
                                         fg=self.TEXT_COLOR, font=("Arial", 36))
        self.main_image_label.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="sew")
        # Save main_area as an attribute for placing the loading overlay.
        self.main_area = main_area
        
        # Row 2: Model selection as red/green toggle buttons
        model_frame = tk.Frame(main_area, bg=self.BG_COLOR)
        model_frame.grid(row=2, column=0, pady=(20,16), padx=(20,10), sticky="ew")
        button_strip = tk.Frame(model_frame, bg=self.BG_COLOR)
        button_strip.pack(anchor="center")
        self.model_files = sorted(glob.glob("/home/ncai/Desktop/APP/*.pt"))
        def set_model(btn, path):
            self.selected_model_path = path
            for b in self.model_buttons:
                b.config(bg="#aa0000", activebackground="#aa0000")
            btn.config(bg="#008000", activebackground="#008000")
        for path in self.model_files:
            btn = tk.Button(button_strip, text=os.path.basename(path), bg="#aa0000", fg="white", activebackground="#aa0000", relief="raised", font=("Arial", 24), height=1, width=14, command=lambda b=None, p=path: set_model(b or btn, p))
            # fix closure for btn
            def make_cmd(bref, pref):
                return lambda: set_model(bref, pref)
            btn.config(command=make_cmd(btn, path))
            btn.pack(side="left", padx=12, pady=0)
            self.model_buttons.append(btn)
        if self.model_files and not self.selected_model_path:
            # Prefer best_24.pt if available
            preferred = None
            for idx, p in enumerate(self.model_files):
                if os.path.basename(p) == "best_24.pt":
                    preferred = (idx, p)
                    break
            if preferred is not None:
                set_model(self.model_buttons[preferred[0]], preferred[1])
            else:
                set_model(self.model_buttons[0], self.model_files[0])

        # Row 3: Last six experiment_* folders as toggle buttons
        folder_frame = tk.Frame(main_area, bg=self.BG_COLOR)
        folder_frame.grid(row=3, column=0, padx=(20,10), pady=(20,40), sticky="ew")
        folder_strip = tk.Frame(folder_frame, bg=self.BG_COLOR)
        folder_strip.pack(anchor="center")
        all_folders = [d for d in glob.glob("experiment_*") if os.path.isdir(d)]
        def folder_key(name):
            try:
                return int(name.split("_")[-1])
            except Exception:
                return -1
        all_folders.sort(key=folder_key, reverse=True)
        last_six = all_folders[:3]
        def set_experiment(btn, name):
            self.selected_experiment = name
            for b in self.experiment_buttons:
                b.config(bg="#aa0000", activebackground="#aa0000")
            btn.config(bg="#008000", activebackground="#008000")
        for name in last_six:
            b = tk.Button(folder_strip, text=name, bg="#aa0000", fg="white", activebackground="#aa0000", relief="raised", font=("Arial", 24), height=1, width=14)
            def make_cmd(bref, nref):
                return lambda: set_experiment(bref, nref)
            b.config(command=make_cmd(b, name))
            b.pack(side="left", padx=12, pady=0)
            self.experiment_buttons.append(b)
        if last_six and not self.selected_experiment:
            set_experiment(self.experiment_buttons[0], last_six[0])

        # Row 4: Progress bar and controls (Process / Close)
        controls_frame = tk.Frame(main_area, bg=self.BG_COLOR)
        controls_frame.grid(row=4, column=0, padx=(20,10), pady=(8,100), sticky="ew")
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=0)
        controls_frame.columnconfigure(2, weight=0)
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(controls_frame, maximum=100, variable=self.progress_var, mode="determinate")
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0,10))
        self.progress_label = tk.Label(controls_frame, text="0/0", bg=self.BG_COLOR, fg=self.TEXT_COLOR, font=("Arial", 24))
        self.progress_label.grid(row=0, column=1, padx=(0,10))
        def start_processing():
            if not self.selected_experiment or not self.selected_model_path:
                return
            threading.Thread(target=self.process_selected_experiment, daemon=True).start()
        process_btn = tk.Button(controls_frame, text="Process", bg="#aa0000", fg="white", activebackground="#008000", font=("Arial", 24), height=1, command=start_processing)
        process_btn.grid(row=0, column=2)
        close_button = tk.Button(controls_frame, text="Close", command=self.on_global_close, font=("Arial", 24), height=1)
        close_button.grid(row=0, column=3, padx=10)

        # Right Image
        try:
            right_image = Image.open("/home/ncai/Desktop/APP/image2.jpg")
        except Exception as e:
            print("Error loading right image:", e)
            right_image = Image.new("RGB", (self.right_img_width, self.main_height), color="gray")
        right_image = right_image.resize((self.right_img_width, self.main_height), Image.LANCZOS)
        right_photo = ImageTk.PhotoImage(right_image)
        right_label = tk.Label(global_container, image=right_photo, bg=self.BG_COLOR)
        right_label.image = right_photo
        right_label.grid(row=0, column=2, padx=10, pady=5, sticky="nsew")

        # compute total images to enable progress bar upon click
    def process_selected_experiment(self):
        base = self.selected_experiment
        if not base:
            return
        model = YOLO(self.selected_model_path)
        # gather subfolders of the experiment
        exp_path = os.path.join(os.getcwd(), base)
        subfolders = [os.path.join(exp_path, d) for d in os.listdir(exp_path) if os.path.isdir(os.path.join(exp_path, d))]
        # only process folders (e.g., PetriDish*Data) that contain numbered images
        def count_images(folder):
            return len(modelsApp.get_sorted_image_paths(folder))
        subfolders = [f for f in subfolders if count_images(f) > 0]
        # Sort subfolders to process PetriDish1Data, PetriDish2Data, etc. in order
        def sort_key(folder_path):
            folder_name = os.path.basename(folder_path)
            if folder_name.startswith('PetriDish') and folder_name.endswith('Data'):
                try:
                    # Extract number from PetriDishXData
                    number = int(folder_name.replace('PetriDish', '').replace('Data', ''))
                    return number
                except ValueError:
                    return 999  # Put non-matching folders at the end
            return 999
        subfolders.sort(key=sort_key)
        # compute total images
        total_images = sum(count_images(f) for f in subfolders)
        progress_state = {'processed': 0}
        self.master.after(0, lambda: self.update_progress_bar(0, total_images))
        for folder in subfolders:
            self.run_folder(folder, folder, model, total_images, progress_state)
        # done
        self.master.after(0, lambda: self.update_progress_bar(total_images, total_images))


# 28-image layout used by the original model screen.
_PATTERN_28 = [
    [1, 14, 15, 28],
    [2, 13, 16, 27],
    [3, 12, 17, 26],
    [4, 11, 18, 25],
    [5, 10, 19, 24],
    [6, 9, 20, 23],
    [7, 8, 21, 22],
]


def list_numbered_jpg_paths(base_dir):
    """Return 1.jpg, 2.jpg, ... while each next file exists."""
    paths = []
    idx = 1
    while True:
        path = os.path.join(base_dir, f"{idx}.jpg")
        if not os.path.isfile(path):
            break
        paths.append(path)
        idx += 1
    return paths


def resolve_model_weights(model_path=None):
    """Pick YOLO weights from an explicit path, model/, or the desktop APP folder."""
    if model_path and os.path.isfile(model_path):
        return model_path
    code_dir = os.path.dirname(os.path.abspath(__file__))
    preferred = [
        os.path.join(code_dir, "model", "best_24H.pt"),
        os.path.join(code_dir, "model", "best_24.pt"),
        "/home/ncai/Desktop/APP/best_24.pt",
        "/home/ncai/Desktop/APP/best_24H.pt",
    ]
    for path in preferred:
        if os.path.isfile(path):
            return path
    found = sorted(glob.glob(os.path.join(code_dir, "model", "*.pt")))
    if found:
        return found[0]
    found = sorted(glob.glob("/home/ncai/Desktop/APP/*.pt"))
    if found:
        return found[0]
    raise FileNotFoundError("No YOLO weights found. Place a .pt file in the model folder.")


def _mosaic_slot(image_number, total):
    """Return row, column, grid rows, grid cols for a 1-based image number."""
    if total == 28:
        for row_idx, row in enumerate(_PATTERN_28):
            for col_idx, num in enumerate(row):
                if num == image_number:
                    return row_idx, col_idx, len(_PATTERN_28), len(_PATTERN_28[0])
        raise ValueError(f"Image {image_number} is outside the 28-image layout.")

    side = int(round(math.sqrt(total)))
    if side > 0 and side * side == total:
        # Same orientation as the camera mosaic: axis swap + flip Y.
        rows = cols = side
        mr = (image_number - 1) // cols
        mc = (image_number - 1) % cols
        dest_row = (cols - 1) - mc
        dest_col = mr
        return dest_row, dest_col, cols, rows

    cols = max(1, int(math.ceil(math.sqrt(total))))
    rows = int(math.ceil(total / cols))
    mr = (image_number - 1) // cols
    mc = (image_number - 1) % cols
    return mr, mc, rows, cols


def process_images_to_mosaic(image_paths, output_path, model_path=None, on_progress=None):
    """Run YOLO on numbered images and save one annotated mosaic PNG.

    on_progress(current, total, message) is called from the worker thread.
    """
    if not image_paths:
        raise RuntimeError("No images to process.")

    total = len(image_paths)
    if on_progress:
        on_progress(0, total, "Loading model...")

    weights = resolve_model_weights(model_path)
    model = YOLO(weights)
    canvas = None
    tile_w = tile_h = None
    total_detected = 0

    for done, path in enumerate(image_paths, start=1):
        image_number = int(os.path.splitext(os.path.basename(path))[0])
        annotated, count = modelsApp.annotate_image(path, model)
        total_detected += count
        if canvas is None:
            tile_w, tile_h = annotated.size
            _, _, grid_rows, grid_cols = _mosaic_slot(image_number, total)
            canvas = Image.new("RGB", (grid_cols * tile_w, grid_rows * tile_h), color="black")
        elif annotated.size != (tile_w, tile_h):
            annotated = annotated.resize((tile_w, tile_h), Image.BILINEAR)
        row, col, _, _ = _mosaic_slot(image_number, total)
        canvas.paste(annotated, (col * tile_w, row * tile_h))
        annotated.close()
        if on_progress:
            on_progress(done, total, f"Processed image {done} of {total}")

    if canvas is None:
        raise RuntimeError("No images to process.")

    if on_progress:
        on_progress(total, total, "Saving mosaic...")

    array = np.array(canvas)
    font_scale = max(1.6, tile_h / 240.0)
    thickness = max(2, int(round(tile_h / 90.0)))
    cv2.putText(
        array,
        f"Total E.coli Detected: {total_detected}",
        (20, max(40, int(tile_h * 0.12))),
        cv2.FONT_HERSHEY_DUPLEX,
        font_scale,
        (125, 246, 55),
        thickness,
    )
    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    Image.fromarray(array).save(output_path, "PNG")
    print(f"Result mosaic saved at {output_path} ({total_detected} detections)")
    return output_path, total_detected


if __name__ == "__main__":
    root = tk.Tk()
    app = modelsApp(root)
    root.mainloop()


