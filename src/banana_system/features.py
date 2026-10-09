"""Versioned OpenCV visual features shared by future training and local inference."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import cv2
import numpy as np
from numpy.typing import NDArray

from .detection import BananaRegion, validate_bgr_image


FEATURE_SCHEMA_VERSION = "visual-v1"


@dataclass(frozen=True, slots=True)
class FeatureDefinition:
    name: str
    unit: str
    extraction: str


VISUAL_FEATURE_SCHEMA: tuple[FeatureDefinition, ...] = (
    FeatureDefinition("hue_mean_deg", "degrees", "Mean OpenCV HSV hue channel multiplied by 2."),
    FeatureDefinition("saturation_mean_fraction", "fraction", "Mean HSV saturation channel divided by 255."),
    FeatureDefinition("value_mean_fraction", "fraction", "Mean HSV value channel divided by 255."),
    FeatureDefinition("gray_stddev_fraction", "fraction", "Population standard deviation of grayscale intensity divided by 255."),
    FeatureDefinition("laplacian_variance_normalized", "fraction_squared", "Population variance of CV_64F grayscale Laplacian divided by 255 squared."),
)


@dataclass(frozen=True, slots=True)
class FeatureVector:
    schema_version: str
    names: tuple[str, ...]
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if self.schema_version != FEATURE_SCHEMA_VERSION:
            raise ValueError("unexpected feature schema version")
        if self.names != tuple(feature.name for feature in VISUAL_FEATURE_SCHEMA):
            raise ValueError("feature names do not match the visual-v1 schema")
        if len(self.values) != len(self.names) or not all(isfinite(value) for value in self.values):
            raise ValueError("feature values must be finite and match the schema")

    def as_mapping(self) -> dict[str, float]:
        return dict(zip(self.names, self.values, strict=True))


def extract_visual_features(image: object, region: BananaRegion) -> FeatureVector:
    """Extract visual-v1 features from an already-selected banana region without mutating input."""
    bgr = validate_bgr_image(image)
    region.validate_for(bgr)
    crop = bgr[region.y : region.y + region.height, region.x : region.x + region.width]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    grayscale = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    hue_mean_deg = float(np.mean(hsv[:, :, 0], dtype=np.float64) * 2.0)
    saturation_mean = float(np.mean(hsv[:, :, 1], dtype=np.float64) / 255.0)
    value_mean = float(np.mean(hsv[:, :, 2], dtype=np.float64) / 255.0)
    gray_stddev = float(np.std(grayscale, dtype=np.float64) / 255.0)
    laplacian = cv2.Laplacian(grayscale, cv2.CV_64F)
    laplacian_variance = float(np.var(laplacian, dtype=np.float64) / (255.0**2))
    return FeatureVector(
        FEATURE_SCHEMA_VERSION,
        tuple(feature.name for feature in VISUAL_FEATURE_SCHEMA),
        (hue_mean_deg, saturation_mean, value_mean, gray_stddev, laplacian_variance),
    )
