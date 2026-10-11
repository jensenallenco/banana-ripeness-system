from __future__ import annotations

from datetime import datetime, timezone
from math import nan

import pytest

from banana_system.contracts import Provenance
from banana_system.features import FEATURE_SCHEMA_VERSION, FeatureVector, VISUAL_FEATURE_SCHEMA
from banana_system.fusion import (
    MULTIMODAL_FEATURE_SCHEMA_VERSION,
    FusionValidationError,
    MatchedSensorMeasurements,
    VisualObservation,
    fuse_multimodal_features,
)


NOW = datetime(2026, 10, 10, tzinfo=timezone.utc)


def make_visual(**changes) -> VisualObservation:
    vector = FeatureVector(
        FEATURE_SCHEMA_VERSION,
        tuple(feature.name for feature in VISUAL_FEATURE_SCHEMA),
        (60.0, 1.0, 0.75, 0.2, 0.1),
    )
    values = {
        "acquisition_id": "acquisition-001", "bundle_id": "bundle-001", "captured_at_utc": NOW,
        "provenance": Provenance.SYNTHETIC, "features": vector,
    }
    values.update(changes)
    return VisualObservation(**values)


def make_sensors(**changes) -> MatchedSensorMeasurements:
    values = {
        "acquisition_id": "acquisition-001", "bundle_id": "bundle-001", "window_start_utc": NOW,
        "window_end_utc": NOW, "provenance": Provenance.SYNTHETIC, "gas_response_value": 512.0,
        "gas_response_unit": "synthetic_adc_counts", "weight_g": 123.4, "weight_unit": "g",
        "hardware_config_id": None, "calibration_id": None,
    }
    values.update(changes)
    return MatchedSensorMeasurements(**values)


def test_fusion_preserves_stable_order_units_and_metadata_outside_features() -> None:
    vector = fuse_multimodal_features(make_visual(), make_sensors())
    assert vector.schema_version == MULTIMODAL_FEATURE_SCHEMA_VERSION
    assert vector.names == tuple(feature.name for feature in VISUAL_FEATURE_SCHEMA) + (
        "gas_response_value", "weight_g",
    )
    assert vector.values == (60.0, 1.0, 0.75, 0.2, 0.1, 512.0, 123.4)
    assert vector.unit_mapping()["gas_response_value"] == "synthetic_adc_counts"
    assert vector.unit_mapping()["weight_g"] == "g"
    assert vector.acquisition_id == "acquisition-001"
    assert vector.hardware_config_id is None
    assert "acquisition_id" not in vector.as_mapping()


def test_synthetic_fusion_remains_training_ineligible() -> None:
    vector = fuse_multimodal_features(make_visual(), make_sensors())
    assert vector.provenance is Provenance.SYNTHETIC
    assert vector.training_ineligibility_reasons == ("synthetic_provenance",)
    assert not hasattr(vector, "ripeness_stage")
    assert not hasattr(vector, "spoilage_status")


@pytest.mark.parametrize(
    ("visual_changes", "sensor_changes", "message"),
    [
        ({"acquisition_id": "other-acquisition"}, {}, "acquisition_id values must match"),
        ({"bundle_id": "other-bundle"}, {}, "bundle_id values must match"),
        ({"provenance": Provenance.REAL}, {}, "provenance must match"),
    ],
)
def test_mismatched_inputs_are_rejected(visual_changes, sensor_changes, message: str) -> None:
    with pytest.raises(FusionValidationError, match=message):
        fuse_multimodal_features(make_visual(**visual_changes), make_sensors(**sensor_changes))


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"gas_response_value": nan}, "finite"),
        ({"weight_g": nan}, "finite"),
        ({"weight_g": -1.0}, "zero or greater"),
        ({"gas_response_unit": ""}, "gas_response_unit"),
        ({"weight_unit": "kg"}, "conversion"),
        ({"provenance": Provenance.REAL}, "hardware_config_id"),
    ],
)
def test_invalid_sensor_inputs_are_rejected(changes, message: str) -> None:
    with pytest.raises(FusionValidationError, match=message):
        make_sensors(**changes)


def test_real_input_requires_and_preserves_provenance_metadata() -> None:
    visual = make_visual(provenance=Provenance.REAL)
    sensors = make_sensors(
        provenance=Provenance.REAL, hardware_config_id="hardware-1", calibration_id="calibration-1"
    )
    vector = fuse_multimodal_features(visual, sensors)
    assert vector.training_ineligibility_reasons == ()
    assert vector.hardware_config_id == "hardware-1"
    assert vector.calibration_id == "calibration-1"


def test_incompatible_visual_schema_is_rejected() -> None:
    class IncompatibleFeatures:
        schema_version = "visual-v0"

    with pytest.raises(FusionValidationError, match="incompatible"):
        VisualObservation("acquisition-001", "bundle-001", NOW, Provenance.SYNTHETIC, IncompatibleFeatures())
