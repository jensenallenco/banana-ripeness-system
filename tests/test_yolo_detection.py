from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from banana_system.detection import (
    BananaRegion,
    ModelUnavailableError,
    StageDetection,
    UltralyticsStageDetector,
    annotate_stage_detections,
)


class FakeBox:
    cls = np.array([0])
    conf = np.array([0.875])
    xyxy = np.array([[1.2, 2.2, 7.8, 8.1]])


class FakeResult:
    boxes = [FakeBox()]


class FakeModel:
    names = {0: "stage 3", 1: "stage 5", 2: "stage 7"}
    ckpt = {"version": "8.4.175"}

    def predict(self, *, source: np.ndarray, verbose: bool) -> list[FakeResult]:
        assert source.shape == (10, 10, 3)
        assert not verbose
        return [FakeResult()]


def test_yolo_adapter_validates_metadata_and_converts_a_detection(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"not loaded by fake")
    detector = UltralyticsStageDetector(checkpoint, lambda _: (FakeModel(), "8.4.175"))

    detections = detector.detect(np.zeros((10, 10, 3), dtype=np.uint8))

    assert len(detections) == 1
    detection = detections[0]
    assert detection.label == "stage 3"
    assert detection.confidence == pytest.approx(0.875)
    assert detection.region.x == 1
    assert detection.region.y == 2
    assert detection.region.width == 7
    assert detection.region.height == 7
    assert "loaded" in detector.status()


def test_yolo_adapter_rejects_incompatible_checkpoint_metadata(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"not loaded by fake")

    class WrongLabels(FakeModel):
        names = {0: "stage 1"}

    detector = UltralyticsStageDetector(checkpoint, lambda _: (WrongLabels(), "8.4.175"))
    with pytest.raises(ModelUnavailableError, match="class mapping"):
        detector.detect(np.zeros((10, 10, 3), dtype=np.uint8))


def test_annotated_output_is_a_copy_with_detection_boxes() -> None:
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    stage_detection = StageDetection(
        region=BananaRegion(1, 2, 7, 7),
        label="stage 3",
        confidence=0.875,
        xyxy=(1.2, 2.2, 7.8, 8.1),
    )

    annotated = annotate_stage_detections(image, (stage_detection,))

    assert np.array_equal(image, np.zeros((10, 10, 3), dtype=np.uint8))
    assert not np.array_equal(annotated, image)
