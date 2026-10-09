"""Detector contracts. Concrete Roboflow/runtime integration remains intentionally absent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray


class RegionValidationError(ValueError):
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


class BananaDetector(Protocol):
    """Local detector adapter contract for a future confirmed model/runtime."""

    def detect(self, image: NDArray[np.uint8]) -> tuple[Detection, ...]: ...


def validate_bgr_image(image: object) -> NDArray[np.uint8]:
    if not isinstance(image, np.ndarray):
        raise RegionValidationError("image must be a NumPy array")
    if image.dtype != np.uint8:
        raise RegionValidationError("image dtype must be uint8")
    if image.ndim != 3 or image.shape[2] != 3 or image.shape[0] == 0 or image.shape[1] == 0:
        raise RegionValidationError("image must be a non-empty HxWx3 BGR array")
    return image
