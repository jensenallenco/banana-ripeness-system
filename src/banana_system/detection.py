"""Detector contracts and the optional local Ultralytics stage detector."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from math import ceil, floor, isfinite
from pathlib import Path
from threading import Lock
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray


class RegionValidationError(ValueError):
    pass


class ModelUnavailableError(RuntimeError):
    pass


class ModelCompatibilityError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class BananaRegion:
    """An explicit pixel bounding box: left/top origin with positive width and height."""

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (self.x, self.y, self.width, self.height)):
            raise RegionValidationError("region coordinates must be integers")
        if self.x < 0 or self.y < 0 or self.width <= 0 or self.height <= 0:
            raise RegionValidationError("region origin must be non-negative and dimensions must be positive")

    def validate_for(self, image: NDArray[np.uint8]) -> None:
        height, width = image.shape[:2]
        if self.x + self.width > width or self.y + self.height > height:
            raise RegionValidationError("region must lie entirely within the image")


@dataclass(frozen=True, slots=True)
class Detection:
    """A detector-provided banana region; no confidence is assumed by this generic contract."""

    region: BananaRegion


@dataclass(frozen=True, slots=True)
class StageDetection:
    """One model observation; never a synthesized bundle-level conclusion."""

    region: BananaRegion
    label: str
    confidence: float
    xyxy: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        if self.label not in EXPECTED_STAGE_LABELS:
            raise RegionValidationError(f"unsupported stage label: {self.label}")
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise RegionValidationError("detection confidence must be finite and between 0 and 1")
        if len(self.xyxy) != 4 or not all(isfinite(value) for value in self.xyxy):
            raise RegionValidationError("detection box coordinates must be finite")


class BananaDetector(Protocol):
    """Local detector adapter contract for a future confirmed model/runtime."""

    def detect(self, image: NDArray[np.uint8]) -> tuple[Detection, ...]: ...


class StageDetector(Protocol):
    def status(self) -> str: ...

    def detect(self, image: NDArray[np.uint8]) -> tuple[StageDetection, ...]: ...


EXPECTED_ULTRALYTICS_VERSION = "8.4.175"
EXPECTED_STAGE_LABELS = {"stage 3", "stage 5", "stage 7"}
EXPECTED_CLASS_NAMES = {0: "stage 3", 1: "stage 5", 2: "stage 7"}
DEFAULT_YOLO_MODEL_PATH = Path("models/banana_yolo26_best.pt")


class UnavailableStageDetector:
    """Explicit no-model state; it never emits a plausible label."""

    def __init__(self, message: str) -> None:
        self._message = message

    def status(self) -> str:
        return self._message

    def detect(self, image: NDArray[np.uint8]) -> tuple[StageDetection, ...]:
        raise ModelUnavailableError(self._message)


class UltralyticsStageDetector:
    """Lazy local inference adapter for the supplied three-stage YOLO checkpoint."""

    def __init__(
        self,
        model_path: Path = DEFAULT_YOLO_MODEL_PATH,
        loader: Callable[[Path], tuple[Any, str]] | None = None,
    ) -> None:
        self._model_path = model_path.expanduser().resolve()
        if not self._model_path.is_file():
            raise ModelUnavailableError(f"Model unavailable: checkpoint does not exist: {self._model_path}")
        self._loader = loader or self._load_ultralytics_model
        self._model: Any | None = None
        self._failure: str | None = None
        self._lock = Lock()

    def status(self) -> str:
        if self._failure is not None:
            return self._failure
        state = "loaded" if self._model is not None else "ready to load"
        return f"Stage model available: {self._model_path.name} ({state}; labels: stage 3, stage 5, stage 7)."

    def detect(self, image: NDArray[np.uint8]) -> tuple[StageDetection, ...]:
        image = validate_bgr_image(image)
        model = self._get_model()
        try:
            results = model.predict(source=image, verbose=False)
            if len(results) != 1:
                raise ModelCompatibilityError("model did not return exactly one result for one image")
            return tuple(self._convert_box(box, image) for box in results[0].boxes)
        except ModelCompatibilityError:
            raise
        except Exception as exc:
            raise RuntimeError(f"YOLO inference failed: {exc}") from exc

    def _get_model(self) -> Any:
        with self._lock:
            if self._failure is not None:
                raise ModelUnavailableError(self._failure)
            if self._model is not None:
                return self._model
            try:
                model, runtime_version = self._loader(self._model_path)
                if runtime_version != EXPECTED_ULTRALYTICS_VERSION:
                    raise ModelCompatibilityError(
                        f"Ultralytics {runtime_version} is installed; checkpoint requires {EXPECTED_ULTRALYTICS_VERSION}"
                    )
                checkpoint_version = getattr(model, "ckpt", {}).get("version")
                if checkpoint_version != EXPECTED_ULTRALYTICS_VERSION:
                    raise ModelCompatibilityError(
                        f"checkpoint reports Ultralytics {checkpoint_version!r}, expected {EXPECTED_ULTRALYTICS_VERSION}"
                    )
                names = {int(key): value for key, value in dict(model.names).items()}
                if names != EXPECTED_CLASS_NAMES:
                    raise ModelCompatibilityError(f"checkpoint class mapping is incompatible: {names!r}")
                self._model = model
                return model
            except (ModelCompatibilityError, ModelUnavailableError) as exc:
                self._failure = f"Stage model unavailable: {exc}"
                raise ModelUnavailableError(self._failure) from exc
            except Exception as exc:
                self._failure = f"Stage model unavailable: load failed: {exc}"
                raise ModelUnavailableError(self._failure) from exc

    @staticmethod
    def _load_ultralytics_model(model_path: Path) -> tuple[Any, str]:
        try:
            import ultralytics
            from ultralytics import YOLO
        except ImportError as exc:
            raise ModelUnavailableError("Ultralytics is not installed in this Python environment.") from exc
        return YOLO(str(model_path)), ultralytics.__version__

    @staticmethod
    def _convert_box(box: Any, image: NDArray[np.uint8]) -> StageDetection:
        try:
            class_id = int(box.cls[0])
            label = EXPECTED_CLASS_NAMES[class_id]
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = (float(value) for value in box.xyxy[0].tolist())
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise ModelCompatibilityError(f"invalid YOLO detection output: {exc}") from exc
        height, width = image.shape[:2]
        left = max(0, floor(x1))
        top = max(0, floor(y1))
        right = min(width, ceil(x2))
        bottom = min(height, ceil(y2))
        try:
            region = BananaRegion(left, top, right - left, bottom - top)
            region.validate_for(image)
            return StageDetection(region, label, confidence, (x1, y1, x2, y2))
        except RegionValidationError as exc:
            raise ModelCompatibilityError(f"invalid YOLO detection box: {exc}") from exc


def default_stage_detector(model_path: Path = DEFAULT_YOLO_MODEL_PATH) -> StageDetector:
    """Use the bundled local model only when both checkpoint and runtime are available."""
    try:
        return UltralyticsStageDetector(model_path)
    except ModelUnavailableError as exc:
        return UnavailableStageDetector(str(exc))


def annotate_stage_detections(image: NDArray[np.uint8], detections: tuple[StageDetection, ...]) -> NDArray[np.uint8]:
    """Draw individual image-based detections without deriving a single stage."""
    import cv2

    annotated = validate_bgr_image(image).copy()
    for detection in detections:
        region = detection.region
        color = {"stage 3": (45, 180, 45), "stage 5": (40, 170, 230), "stage 7": (45, 45, 210)}[detection.label]
        cv2.rectangle(annotated, (region.x, region.y), (region.x + region.width, region.y + region.height), color, 2)
        cv2.putText(
            annotated,
            f"{detection.label} {detection.confidence:.1%}",
            (region.x, max(18, region.y - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA,
        )
    return annotated


def validate_bgr_image(image: object) -> NDArray[np.uint8]:
    if not isinstance(image, np.ndarray):
        raise RegionValidationError("image must be a NumPy array")
    if image.dtype != np.uint8:
        raise RegionValidationError("image dtype must be uint8")
    if image.ndim != 3 or image.shape[2] != 3 or image.shape[0] == 0 or image.shape[1] == 0:
        raise RegionValidationError("image must be a non-empty HxWx3 BGR array")
    return image
