from __future__ import annotations

import base64
from pathlib import Path
from threading import Event, Thread

import cv2
import numpy as np
import pytest

from banana_system.camera import (
    CameraCaptureError,
    CameraBusyError,
    CameraUnavailableError,
    Picamera2CameraAdapter,
    UnavailableCameraAdapter,
)
from banana_system.desktop import ImageLoadError, load_preview_image, preview_ppm_data


def test_unavailable_camera_never_simulates_or_writes_a_capture(tmp_path: Path) -> None:
    camera = UnavailableCameraAdapter()
    assert not camera.status().available
    destination = tmp_path / "capture.jpg"
    with pytest.raises(CameraUnavailableError, match="Picamera2"):
        camera.capture(destination)
    assert not destination.exists()


def test_existing_synthetic_photo_loads_without_changing_source() -> None:
    source = Path("data/fixtures/synthetic/images/synthetic-bundle-001.ppm")
    original = source.read_bytes()
    preview = load_preview_image(source)
    assert preview.source_path == source.resolve()
    assert preview.bgr.shape == (1, 1, 3)
    assert source.read_bytes() == original


def test_preview_data_is_a_tk_compatible_ppm_payload_and_scales() -> None:
    image = np.full((1000, 2000, 3), 127, dtype=np.uint8)
    ppm = base64.b64decode(preview_ppm_data(image, max_width=200, max_height=200))
    decoded = cv2.imdecode(np.frombuffer(ppm, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert decoded.shape[:2] == (100, 200)


def test_missing_or_invalid_photographs_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ImageLoadError, match="does not exist"):
        load_preview_image(tmp_path / "missing.jpg")
    invalid = tmp_path / "invalid.jpg"
    invalid.write_text("not an image", encoding="utf-8")
    with pytest.raises(ImageLoadError, match="could not decode"):
        load_preview_image(invalid)


class FakePicamera2:
    def __init__(self, metadata: dict[str, object] | None = None) -> None:
        self.metadata = metadata if metadata is not None else {"ExposureTime": 8200}
        self.configuration: object | None = None
        self.controls: dict[str, object] | None = None
        self.stopped = False
        self.closed = False

    def create_still_configuration(self, **kwargs: object) -> object:
        return kwargs

    def configure(self, configuration: object) -> None:
        self.configuration = configuration

    def start(self) -> None:
        return None

    def set_controls(self, controls: dict[str, object]) -> None:
        self.controls = controls

    def capture_file(self, destination: str) -> None:
        Path(destination).write_bytes(b"synthetic jpeg bytes")

    def capture_metadata(self) -> dict[str, object]:
        return self.metadata

    def stop(self) -> None:
        self.stopped = True

    def close(self) -> None:
        self.closed = True


def test_picamera_adapter_uses_jpeg_encoder_and_reports_actual_exposure(tmp_path: Path) -> None:
    fake = FakePicamera2()
    camera = Picamera2CameraAdapter(lambda: fake)

    result = camera.capture(tmp_path / "capture.jpg")

    assert fake.configuration == {"main": {"size": (800, 480)}}
    assert fake.controls == {"AeEnable": False, "ExposureTime": 8333}
    assert result.path.is_file()
    assert result.requested_exposure_us == 8333
    assert result.actual_exposure_us == 8200
    assert result.metadata == {"ExposureTime": 8200}
    camera.close()
    assert fake.stopped and fake.closed


def test_picamera_adapter_rejects_bad_output_or_missing_jpeg(tmp_path: Path) -> None:
    camera = Picamera2CameraAdapter(lambda: FakePicamera2())
    with pytest.raises(CameraCaptureError, match=".jpg"):
        camera.capture(tmp_path / "capture.png")
    camera.close()

    class NoFileCamera(FakePicamera2):
        def capture_file(self, destination: str) -> None:
            return None

    no_file = Picamera2CameraAdapter(NoFileCamera)
    with pytest.raises(CameraCaptureError, match="did not produce"):
        no_file.capture(tmp_path / "absent.jpg")
    no_file.close()


def test_picamera_adapter_accepts_missing_exposure_metadata_without_claiming_value(tmp_path: Path) -> None:
    camera = Picamera2CameraAdapter(lambda: FakePicamera2({"Other": "value"}))
    assert camera.capture(tmp_path / "capture.jpg").actual_exposure_us is None
    camera.close()


def test_picamera_adapter_rejects_a_second_capture_while_one_is_active(tmp_path: Path) -> None:
    started = Event()
    release = Event()

    class BlockingCamera(FakePicamera2):
        def capture_file(self, destination: str) -> None:
            started.set()
            assert release.wait(timeout=2)
            super().capture_file(destination)

    camera = Picamera2CameraAdapter(BlockingCamera)
    worker = Thread(target=camera.capture, args=(tmp_path / "first.jpg",))
    worker.start()
    assert started.wait(timeout=2)
    with pytest.raises(CameraBusyError, match="already in progress"):
        camera.capture(tmp_path / "second.jpg")
    release.set()
    worker.join(timeout=2)
    assert not worker.is_alive()
    camera.close()
