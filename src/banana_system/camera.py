"""Camera boundary and the optional Raspberry Pi Picamera2 adapter."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Protocol


DEFAULT_CAPTURE_SIZE = (800, 480)
REQUESTED_EXPOSURE_US = 8333


@dataclass(frozen=True, slots=True)
class CameraStatus:
    available: bool
    message: str


@dataclass(frozen=True, slots=True)
class CaptureResult:
    """A saved image and the camera metadata associated with that capture."""

    path: Path
    requested_exposure_us: int
    actual_exposure_us: int | None
    metadata: Mapping[str, object]


class CameraUnavailableError(RuntimeError):
    pass


class CameraBusyError(RuntimeError):
    pass


class CameraCaptureError(RuntimeError):
    pass


class CameraAdapter(Protocol):
    def status(self) -> CameraStatus: ...

    def capture(self, destination: Path) -> CaptureResult: ...

    def close(self) -> None: ...


class UnavailableCameraAdapter:
    """Explicit placeholder; it never simulates a camera or writes an image."""

    def __init__(self, message: str = "Camera unavailable: Picamera2 is not installed or no Pi camera is available.") -> None:
        self._message = message

    def status(self) -> CameraStatus:
        return CameraStatus(available=False, message=self._message)

    def capture(self, destination: Path) -> CaptureResult:
        raise CameraUnavailableError(self.status().message)

    def close(self) -> None:
        return None


class Picamera2CameraAdapter:
    """Pi-only camera adapter, imported lazily so Mac development remains portable.

    Picamera2's ``BGR888`` name is not a safe reason to assume a NumPy byte
    order: on this stack it is commonly exposed as RGB bytes. This adapter
    deliberately uses Picamera2's JPEG encoder and never passes a raw camera
    array to OpenCV. The desktop reloads the saved JPEG using ``cv2.imread``,
    whose result is BGR, so no unverified channel swap is applied.
    """

    def __init__(
        self,
        picamera_factory: Callable[[], Any] | None = None,
        *,
        capture_size: tuple[int, int] = DEFAULT_CAPTURE_SIZE,
        requested_exposure_us: int = REQUESTED_EXPOSURE_US,
    ) -> None:
        if capture_size[0] <= 0 or capture_size[1] <= 0:
            raise ValueError("capture_size dimensions must be positive")
        if requested_exposure_us <= 0:
            raise ValueError("requested_exposure_us must be positive")
        if picamera_factory is None:
            try:
                from picamera2 import Picamera2
            except ImportError as exc:
                raise CameraUnavailableError(
                    "Camera unavailable: Picamera2 is not installed in this Python environment."
                ) from exc
            picamera_factory = Picamera2

        self._capture_size = capture_size
        self._requested_exposure_us = requested_exposure_us
        self._capture_lock = Lock()
        self._closed = False
        self._camera: Any | None = None
        camera: Any | None = None
        try:
            camera = picamera_factory()
            configuration = camera.create_still_configuration(main={"size": capture_size})
            camera.configure(configuration)
            camera.start()
            # The control is a request. capture_metadata() reports what libcamera used.
            camera.set_controls({"AeEnable": False, "ExposureTime": requested_exposure_us})
            self._camera = camera
        except Exception as exc:
            self._cleanup_camera(camera)
            raise CameraUnavailableError(f"Camera unavailable: initialization failed: {exc}") from exc

    def status(self) -> CameraStatus:
        if self._closed:
            return CameraStatus(False, "Camera unavailable: camera session is closed.")
        if self._capture_lock.locked():
            return CameraStatus(False, "Camera busy: capture is in progress.")
        return CameraStatus(
            True,
            f"Available: Pi camera ready at {self._capture_size[0]}×{self._capture_size[1]}; "
            f"requested exposure {self._requested_exposure_us} µs.",
        )

    def capture(self, destination: Path) -> CaptureResult:
        if self._closed or self._camera is None:
            raise CameraUnavailableError("Camera unavailable: camera session is closed.")
        if not self._capture_lock.acquire(blocking=False):
            raise CameraBusyError("Camera busy: capture is already in progress.")
        try:
            destination = destination.expanduser().resolve()
            if destination.suffix.lower() not in {".jpg", ".jpeg"}:
                raise CameraCaptureError("camera destination must be a .jpg or .jpeg file")
            destination.parent.mkdir(parents=True, exist_ok=True)
            self._camera.capture_file(str(destination))
            if not destination.is_file() or destination.stat().st_size == 0:
                raise CameraCaptureError("camera did not produce a JPEG file")
            metadata = dict(self._camera.capture_metadata())
            actual_exposure = metadata.get("ExposureTime")
            if isinstance(actual_exposure, bool) or not isinstance(actual_exposure, int):
                actual_exposure = None
            return CaptureResult(destination, self._requested_exposure_us, actual_exposure, metadata)
        except (CameraCaptureError, CameraUnavailableError):
            raise
        except Exception as exc:
            raise CameraCaptureError(f"capture failed: {exc}") from exc
        finally:
            self._capture_lock.release()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._cleanup_camera(self._camera)
        self._camera = None

    @staticmethod
    def _cleanup_camera(camera: Any | None) -> None:
        if camera is None:
            return
        try:
            camera.stop()
        except Exception:
            pass
        try:
            camera.close()
        except Exception:
            pass


def default_camera_adapter() -> CameraAdapter:
    """Select real camera support when the Picamera2 stack is present."""
    try:
        return Picamera2CameraAdapter()
    except CameraUnavailableError as exc:
        return UnavailableCameraAdapter(str(exc))
