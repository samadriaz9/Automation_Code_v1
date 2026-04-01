import threading
import time


class USBCameraWorker:
    """Background USB camera capture worker."""

    def __init__(self, device_index=0):
        self.device_index = int(device_index)
        self._thread = None
        self._stop_event = threading.Event()
        self._cap = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            import cv2
        except Exception as exc:
            print(f"[USB Camera] OpenCV import failed: {exc}")
            return

        cap = cv2.VideoCapture(self.device_index)
        if not cap.isOpened():
            print(f"[USB Camera] Could not open /dev/video{self.device_index}")
            return

        self._cap = cap
        window_name = f"USB Camera (/dev/video{self.device_index})"
        print(f"[USB Camera] Started (/dev/video{self.device_index})")
        try:
            while not self._stop_event.is_set():
                ok, frame = cap.read()
                if not ok:
                    time.sleep(0.05)
                    continue

                # Pop-up live preview while the worker is running.
                cv2.imshow(window_name, frame)

                # keep UI responsive; allow 'q' to stop preview
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    self._stop_event.set()
                    break
        finally:
            try:
                cap.release()
            except Exception:
                pass
            try:
                cv2.destroyWindow(window_name)
            except Exception:
                try:
                    cv2.destroyAllWindows()
                except Exception:
                    pass
            self._cap = None
            print("[USB Camera] Stopped")

    def stop(self, join_timeout=2.0):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=float(join_timeout))
        self._thread = None


def start_usb_camera_thread(device_index=0):
    """Create and start a USB camera worker thread."""
    worker = USBCameraWorker(device_index=device_index)
    worker.start()
    return worker


def stop_usb_camera_thread(worker):
    """Stop a running USB camera worker safely."""
    if worker is None:
        return
    try:
        worker.stop()
    except Exception as exc:
        print(f"[USB Camera] Stop warning: {exc}")

