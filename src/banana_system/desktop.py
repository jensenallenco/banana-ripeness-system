"""Small desktop image-preview screen, usable with existing development photographs."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from .camera import CameraAdapter, CaptureResult, default_camera_adapter


class ImageLoadError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PreviewImage:
    source_path: Path
    bgr: NDArray[np.uint8]


def load_preview_image(path: Path) -> PreviewImage:
    """Load an existing local photograph without changing or copying its source file."""
    path = path.expanduser().resolve()
    if not path.is_file():
        raise ImageLoadError(f"image file does not exist: {path}")
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ImageLoadError(f"OpenCV could not decode image: {path}")
    return PreviewImage(path, image)


def preview_png_data(image: NDArray[np.uint8], max_width: int = 760, max_height: int = 250) -> str:
    """Convert BGR pixels to Tk-compatible PNG data, retaining aspect ratio."""
    height, width = image.shape[:2]
    scale = min(max_width / width, max_height / height, 1.0)
    if scale < 1.0:
        image = cv2.resize(image, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise ImageLoadError("could not prepare image preview")
    return base64.b64encode(encoded.tobytes()).decode("ascii")


class DesktopApplication:
    """Tk UI kept separate from image and camera contracts for Mac/Pi portability."""

    def __init__(
        self, root: object, camera: CameraAdapter, capture_directory: Path, initial_preview: PreviewImage | None = None
    ) -> None:
        import tkinter as tk
        from tkinter import filedialog, ttk

        self._tk = tk
        self._filedialog = filedialog
        self._root = root
        self._camera = camera
        self._capture_directory = capture_directory.expanduser().resolve()
        self._preview_photo: object | None = None
        self._image_path: Path | None = None

        root.title("Cavendish Banana System")
        root.geometry("800x480")
        root.minsize(800, 480)
        root.configure(background="#f8fafc")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background="#f8fafc")
        style.configure("TLabel", background="#f8fafc", foreground="#1f2937")
        style.configure("Title.TLabel", background="#f8fafc", foreground="#111827", font=("TkDefaultFont", 18, "bold"))
        style.configure("Status.TLabel", background="#f8fafc", foreground="#4b5563")
        style.configure("TButton", padding=(12, 7))
        style.configure("Preview.TLabel", background="#ffffff", foreground="#4b5563", relief="solid", borderwidth=1)

        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Image capture", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            frame,
            text="Load a development photograph or capture from a configured Pi camera. No sensors or model are required.",
            style="Status.TLabel",
            wraplength=760,
        ).pack(anchor="w", pady=(2, 8))

        controls = ttk.Frame(frame)
        controls.pack(fill="x")
        ttk.Button(controls, text="Open photograph", command=self._open_photograph).pack(side="left")
        self._capture_button = ttk.Button(controls, text="Capture", command=self._capture)
        self._capture_button.pack(side="left", padx=(8, 0))

        self._camera_status = tk.StringVar()
        self._image_location = tk.StringVar(value="Image location: no image selected")
        self._save_location = tk.StringVar(value=f"Capture destination: {self._capture_directory}")
        self._notice = tk.StringVar(value="Sensors: not connected — image capture is independent.")
        self._capture_in_progress = False
        self._apply_camera_status()
        ttk.Label(frame, textvariable=self._camera_status, style="Status.TLabel", wraplength=760).pack(anchor="w", pady=(8, 1))
        ttk.Label(frame, textvariable=self._notice, style="Status.TLabel", wraplength=760).pack(anchor="w", pady=1)
        ttk.Label(frame, text="Model: unavailable — no prediction is generated.", style="Status.TLabel").pack(anchor="w", pady=1)
        ttk.Label(frame, textvariable=self._image_location, style="Status.TLabel", wraplength=760).pack(anchor="w", pady=(6, 1))
        ttk.Label(frame, textvariable=self._save_location, style="Status.TLabel", wraplength=760).pack(anchor="w", pady=1)

        self._preview_label = ttk.Label(
            frame, text="Open a photograph to preview it.", anchor="center", style="Preview.TLabel"
        )
        self._preview_label.pack(fill="both", expand=True, pady=(8, 0))
        root.protocol("WM_DELETE_WINDOW", self._close)
        if initial_preview is not None:
            self._show_image(initial_preview, captured=False)

    def _apply_camera_status(self) -> None:
        status = self._camera.status()
        self._camera_status.set(f"Camera: {status.message}")
        self._capture_button.state(["!disabled"] if status.available and not self._capture_in_progress else ["disabled"])

    def _open_photograph(self) -> None:
        selected = self._filedialog.askopenfilename(
            title="Open development photograph",
            filetypes=[("Images", "*.bmp *.jpeg *.jpg *.png *.ppm *.tif *.tiff"), ("All files", "*.*")],
        )
        if not selected:
            return
        try:
            self._show_image(load_preview_image(Path(selected)), captured=False)
        except ImageLoadError as exc:
            self._notice.set(f"Image unavailable: {exc}")

    def _capture(self) -> None:
        if self._capture_in_progress:
            return
        self._capture_in_progress = True
        self._capture_button.state(["disabled"])
        self._notice.set("Capturing image…")
        try:
            self._capture_directory.mkdir(parents=True, exist_ok=True)
            filename = datetime.now(timezone.utc).strftime("capture-%Y%m%dT%H%M%S%fZ.jpg")
            destination = self._capture_directory / filename
            result = self._camera.capture(destination)
            self._show_image(load_preview_image(result.path), captured=True)
            self._notice.set(self._capture_notice(result))
        except (OSError, RuntimeError, ImageLoadError) as exc:
            self._notice.set(f"Capture unavailable: {exc}")
        finally:
            self._capture_in_progress = False
            self._apply_camera_status()

    @staticmethod
    def _capture_notice(result: CaptureResult) -> str:
        actual = "not reported" if result.actual_exposure_us is None else f"{result.actual_exposure_us} µs"
        return f"Captured JPEG. Requested exposure: {result.requested_exposure_us} µs; camera metadata: {actual}."

    def _show_image(self, preview: PreviewImage, captured: bool) -> None:
        self._preview_photo = self._tk.PhotoImage(data=preview_png_data(preview.bgr), format="PNG")
        self._preview_label.configure(image=self._preview_photo, text="")
        self._image_path = preview.source_path
        self._image_location.set(f"Image location: {preview.source_path}")
        if captured:
            self._save_location.set(f"Saved image location: {preview.source_path}")
        else:
            self._notice.set("Development photograph loaded. It has not been copied or analyzed.")

    def _close(self) -> None:
        self._camera.close()
        self._root.destroy()


def run_desktop(capture_directory: Path, initial_image: Path | None = None) -> None:
    """Start the desktop UI, using Pi camera support only when Picamera2 is available."""
    try:
        import tkinter as tk
    except ImportError as exc:
        raise RuntimeError("Tkinter is unavailable in this Python installation") from exc
    initial_preview = load_preview_image(initial_image) if initial_image is not None else None
    root = tk.Tk()
    DesktopApplication(root, default_camera_adapter(), capture_directory, initial_preview)
    root.mainloop()
