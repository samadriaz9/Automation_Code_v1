import os
import glob
import csv
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests  # For HTTP POST

# Constants
BG_COLOR = "#2E3440"
BUTTON_COLOR = "#5E81AC"
TEXT_COLOR = "#ECEFF4"
DATA_FILE = "image_metadata.csv"

class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("1920x1080")
        self.root.resizable(False, False)

        self.current_index = 0
        self.images = []
        self.image_data = {}

        self.load_metadata()

        # Title Bar
        title_bar = tk.Frame(root, bg="white", relief="raised", bd=2, height=50)
        title_bar.pack(side="top", fill="x")

        tk.Label(title_bar, text=" View Petri Dish Results", fg="black", bg="white",
                 font=("Arial", 20, "bold")).pack(side="left", padx=10, pady=5)

        close_btn = tk.Button(title_bar, text="✖", bg="white", fg="red",
                              command=root.destroy, border=0, font=("Arial", 16, "bold"))
        close_btn.pack(side="right", padx=10)

        # Layout
        container = tk.Frame(root, bg=BG_COLOR)
        container.pack(fill="both", expand=True)

        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=1)
        container.columnconfigure(2, weight=0)

        # Left image
        try:
            left_img = Image.open("/home/ncai/Desktop/APP/image1.jpg")
        except:
            left_img = Image.new("RGB", (480, 1080), "gray")
        left_img = left_img.resize((480, 1080))
        self.left_photo = ImageTk.PhotoImage(left_img)
        tk.Label(container, image=self.left_photo).grid(row=0, column=0, sticky="ns")

        # Center area
        self.center = tk.Frame(container, bg=BG_COLOR)
        self.center.grid(row=0, column=1, sticky="nsew", padx=10)

        self.image_name_label = tk.Label(self.center, text="", bg=BG_COLOR, fg=TEXT_COLOR,
                                         font=("Arial", 16, "bold"))
        self.image_name_label.pack(pady=(20, 10))

        self.image_label = tk.Label(self.center, bg=BG_COLOR)
        self.image_label.pack(pady=10)

        nav_frame = tk.Frame(self.center, bg=BG_COLOR)
        nav_frame.pack(pady=10)

        prev_btn = tk.Button(nav_frame, text="⯇ Previous", command=self.show_prev,
                             bg=BUTTON_COLOR, fg="white", width=12, font=("Arial", 13))
        prev_btn.pack(side="left", padx=20)

        next_btn = tk.Button(nav_frame, text="Next ⯈", command=self.show_next,
                             bg=BUTTON_COLOR, fg="white", width=12, font=("Arial", 13))
        next_btn.pack(side="left", padx=20)

        # Entry Fields
        entry_frame = tk.Frame(self.center, bg=BG_COLOR)
        entry_frame.pack(pady=10)

        tk.Label(entry_frame, text="Latitude:", bg=BG_COLOR, fg=TEXT_COLOR, font=("Arial", 13)).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.lat_entry = tk.Entry(entry_frame, width=25, font=("Arial", 13))
        self.lat_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(entry_frame, text="Longitude:", bg=BG_COLOR, fg=TEXT_COLOR, font=("Arial", 13)).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.lon_entry = tk.Entry(entry_frame, width=25, font=("Arial", 13))
        self.lon_entry.grid(row=1, column=1, padx=10, pady=5)

        # Buttons
        save_btn = tk.Button(entry_frame, text="💾 Save Location", command=self.save_location,
                             bg=BUTTON_COLOR, fg="white", font=("Arial", 13))
        save_btn.grid(row=2, column=0, columnspan=2, pady=10)

        send_btn = tk.Button(entry_frame, text="☁️ Send to Server", command=self.send_to_server,
                             bg="#A3BE8C", fg="white", font=("Arial", 13))
        send_btn.grid(row=3, column=0, columnspan=2, pady=5)

        # Right image
        try:
            right_img = Image.open("/home/ncai/Desktop/APP/image2.jpg")
        except:
            right_img = Image.new("RGB", (500, 1080), "gray")
        right_img = right_img.resize((500, 1080))
        self.right_photo = ImageTk.PhotoImage(right_img)
        tk.Label(container, image=self.right_photo).grid(row=0, column=2, sticky="nsew")

        # Load images
        self.load_images()
        self.show_image()

    def load_images(self):
        pattern = "/home/ncai/Desktop/APP/experiment_*/PetriDish*/result*.jpg"
        self.images = sorted(glob.glob(pattern))

    def show_image(self):
        if not self.images:
            self.image_label.config(image='')
            self.image_name_label.config(text="No images found")
            return

        path = self.images[self.current_index]
        img = Image.open(path)
        img.thumbnail((900, 700))
        photo = ImageTk.PhotoImage(img)

        self.image_label.config(image=photo)
        self.image_label.image = photo
        self.image_name_label.config(text=path)

        lat, lon = self.image_data.get(path, ("", ""))
        self.lat_entry.delete(0, tk.END)
        self.lon_entry.delete(0, tk.END)
        self.lat_entry.insert(0, lat)
        self.lon_entry.insert(0, lon)

    def show_prev(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image()

    def show_next(self):
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.show_image()

    def save_location(self):
        if not self.images:
            return
        path = self.images[self.current_index]
        lat = self.lat_entry.get().strip()
        lon = self.lon_entry.get().strip()
        self.image_data[path] = (lat, lon)
        self.save_metadata()
        messagebox.showinfo("Saved", "Location saved successfully.")

    def save_metadata(self):
        with open(DATA_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["image", "latitude", "longitude"])
            for img, (lat, lon) in self.image_data.items():
                writer.writerow([img, lat, lon])

    def load_metadata(self):
        if not os.path.exists(DATA_FILE):
            return
        with open(DATA_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.image_data[row["image"]] = (row["latitude"], row["longitude"])

    def send_to_server(self):
        if not self.images:
            messagebox.showwarning("Warning", "No images to send.")
            return

        path = self.images[self.current_index]
        lat = self.lat_entry.get().strip()
        lon = self.lon_entry.get().strip()

        if not lat or not lon:
            messagebox.showwarning("Missing Data", "Please enter both latitude and longitude.")
            return

        if not os.path.exists(path):
            messagebox.showerror("Error", f"Image not found: {path}")
            return

        try:
            url = "http://localhost/myserver/receive_data.php"  # Change to your real URL
            with open(path, "rb") as image_file:
                files = {"image_file": image_file}
                data = {
                    "image": path,
                    "latitude": lat,
                    "longitude": lon
                }
                response = requests.post(url, data=data, files=files)

            if response.status_code == 200:
                messagebox.showinfo("Success", "Image and data sent to server.")
            else:
                messagebox.showerror("Server Error", f"Status code: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))


# Run the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewerApp(root)
    root.mainloop()