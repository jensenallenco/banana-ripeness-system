from __future__ import annotations

import base64
from pathlib import Path

import cv2
import numpy as np
import pytest

from banana_system.camera import CameraUnavailableError, UnavailableCameraAdapter
from banana_system.desktop import ImageLoadError, load_preview_image, preview_ppm_data


def test_unavailable_camera_never_simulates_or_writes_a_capture(tmp_path: Path) -> None:
    camera = UnavailableCameraAdapter()
    assert not camera.status().available
    destination = tmp_path / "capture.jpg"
    with pytest.raises(CameraUnavailableError, match="confirmed Pi OS/camera setup"):
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
