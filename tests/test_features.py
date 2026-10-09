from __future__ import annotations

import numpy as np
import pytest

from banana_system.detection import BananaRegion, RegionValidationError, validate_bgr_image
from banana_system.features import FEATURE_SCHEMA_VERSION, VISUAL_FEATURE_SCHEMA, extract_visual_features


def test_feature_schema_is_versioned_and_ordered() -> None:
    assert FEATURE_SCHEMA_VERSION == "visual-v1"
    assert [feature.name for feature in VISUAL_FEATURE_SCHEMA] == [
        "hue_mean_deg",
        "saturation_mean_fraction",
        "value_mean_fraction",
        "gray_stddev_fraction",
        "laplacian_variance_normalized",
    ]
    assert [feature.unit for feature in VISUAL_FEATURE_SCHEMA] == [
        "degrees", "fraction", "fraction", "fraction", "fraction_squared"
    ]


def test_features_use_only_the_explicit_region_without_mutating_image() -> None:
    image = np.zeros((6, 6, 3), dtype=np.uint8)
    image[2:4, 1:3] = (0, 255, 255)  # BGR yellow: OpenCV hue 30, saturation/value 255.
    original = image.copy()
    vector = extract_visual_features(image, BananaRegion(1, 2, 2, 2))
    values = vector.as_mapping()
    assert vector.schema_version == "visual-v1"
    assert values["hue_mean_deg"] == pytest.approx(60.0)
    assert values["saturation_mean_fraction"] == pytest.approx(1.0)
    assert values["value_mean_fraction"] == pytest.approx(1.0)
    assert values["gray_stddev_fraction"] == pytest.approx(0.0)
    assert values["laplacian_variance_normalized"] == pytest.approx(0.0)
    assert np.array_equal(image, original)


def test_texture_features_respond_to_synthetic_intensity_variation() -> None:
    checker = np.zeros((4, 4, 3), dtype=np.uint8)
    checker[::2, ::2] = 255
    checker[1::2, 1::2] = 255
    values = extract_visual_features(checker, BananaRegion(0, 0, 4, 4)).as_mapping()
    assert values["gray_stddev_fraction"] == pytest.approx(0.5)
    assert values["laplacian_variance_normalized"] > 0.0


@pytest.mark.parametrize(
    ("image", "region", "message"),
    [
        (np.zeros((2, 2), dtype=np.uint8), BananaRegion(0, 0, 1, 1), "HxWx3"),
        (np.zeros((2, 2, 3), dtype=np.float32), BananaRegion(0, 0, 1, 1), "uint8"),
        (np.zeros((2, 2, 3), dtype=np.uint8), BananaRegion(1, 1, 2, 1), "entirely"),
    ],
)
def test_invalid_images_and_regions_are_rejected(image, region, message: str) -> None:
    with pytest.raises(RegionValidationError, match=message):
        extract_visual_features(image, region)


def test_invalid_region_dimensions_and_non_array_image_are_rejected() -> None:
    with pytest.raises(RegionValidationError, match="positive"):
        BananaRegion(0, 0, 0, 1)
    with pytest.raises(RegionValidationError, match="NumPy"):
        validate_bgr_image("not an image")
