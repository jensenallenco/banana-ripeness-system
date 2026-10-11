"""Versioned, model-free fusion of visual features with matched sensor measurements."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
import re

from .contracts import Provenance
from .features import FEATURE_SCHEMA_VERSION, FeatureVector, VISUAL_FEATURE_SCHEMA


MULTIMODAL_FEATURE_SCHEMA_VERSION = "multimodal-v1"
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


class FusionValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class VisualObservation:
    """Visual features plus identity/provenance retained outside predictive values."""

    acquisition_id: str
    bundle_id: str
    captured_at_utc: datetime
    provenance: Provenance
    features: FeatureVector

    def __post_init__(self) -> None:
        _validate_identity(self.acquisition_id, "acquisition_id")
        _validate_identity(self.bundle_id, "bundle_id")
        _require_utc(self.captured_at_utc, "captured_at_utc")
        if self.features.schema_version != FEATURE_SCHEMA_VERSION:
            raise FusionValidationError("visual feature schema is incompatible with multimodal-v1")


@dataclass(frozen=True, slots=True)
class MatchedSensorMeasurements:
    """Sensor values and provenance; gas response is not converted to a chemical concentration."""

    acquisition_id: str
    bundle_id: str
    window_start_utc: datetime
    window_end_utc: datetime
    provenance: Provenance
    gas_response_value: float
    gas_response_unit: str
    weight_g: float
    weight_unit: str
    hardware_config_id: str | None
    calibration_id: str | None

    def __post_init__(self) -> None:
        _validate_identity(self.acquisition_id, "acquisition_id")
        _validate_identity(self.bundle_id, "bundle_id")
        _require_utc(self.window_start_utc, "window_start_utc")
        _require_utc(self.window_end_utc, "window_end_utc")
        if self.window_end_utc < self.window_start_utc:
            raise FusionValidationError("sensor window cannot end before it starts")
        if not isfinite(self.gas_response_value) or not isfinite(self.weight_g):
            raise FusionValidationError("sensor values must be finite")
        if self.weight_g < 0:
            raise FusionValidationError("weight_g must be zero or greater")
        if not self.gas_response_unit.strip():
            raise FusionValidationError("gas_response_unit is required")
        if self.weight_unit != "g":
            raise FusionValidationError("weight_unit must be g; unit conversion is not implemented")
        if self.provenance is Provenance.REAL and (
            not _valid_optional_id(self.hardware_config_id) or not _valid_optional_id(self.calibration_id)
        ):
            raise FusionValidationError("real sensor measurements require hardware_config_id and calibration_id")


@dataclass(frozen=True, slots=True)
class MultimodalFeatureVector:
    """Ordered predictive values. Identity, timestamps, and provenance are intentionally metadata."""

    schema_version: str
    visual_schema_version: str
    names: tuple[str, ...]
    units: tuple[str, ...]
    values: tuple[float, ...]
    acquisition_id: str
    bundle_id: str
    provenance: Provenance
    captured_at_utc: datetime
    sensor_window_start_utc: datetime
    sensor_window_end_utc: datetime
    hardware_config_id: str | None
    calibration_id: str | None
    training_ineligibility_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        expected_names = tuple(feature.name for feature in VISUAL_FEATURE_SCHEMA) + (
            "gas_response_value",
            "weight_g",
        )
        if self.schema_version != MULTIMODAL_FEATURE_SCHEMA_VERSION:
            raise FusionValidationError("unexpected multimodal feature schema")
        if self.visual_schema_version != FEATURE_SCHEMA_VERSION or self.names != expected_names:
            raise FusionValidationError("feature names or visual schema are incompatible")
        if len(self.units) != len(self.names) or len(self.values) != len(self.names):
            raise FusionValidationError("feature values and units must match feature names")
        expected_visual_units = tuple(feature.unit for feature in VISUAL_FEATURE_SCHEMA)
        if self.units[:-2] != expected_visual_units:
            raise FusionValidationError("visual feature units are incompatible")
        if self.units[-1] != "g" or not self.units[-2].strip():
            raise FusionValidationError("gas-response and weight units are required")
        if not all(isfinite(value) for value in self.values):
            raise FusionValidationError("feature values must be finite")
        if self.values[-1] < 0:
            raise FusionValidationError("weight_g must be zero or greater")
        _validate_identity(self.acquisition_id, "acquisition_id")
        _validate_identity(self.bundle_id, "bundle_id")
        _require_utc(self.captured_at_utc, "captured_at_utc")
        _require_utc(self.sensor_window_start_utc, "sensor_window_start_utc")
        _require_utc(self.sensor_window_end_utc, "sensor_window_end_utc")
        if self.sensor_window_end_utc < self.sensor_window_start_utc:
            raise FusionValidationError("sensor window cannot end before it starts")
        if self.provenance is Provenance.REAL and (
            not _valid_optional_id(self.hardware_config_id) or not _valid_optional_id(self.calibration_id)
        ):
            raise FusionValidationError("real fused vectors require hardware_config_id and calibration_id")
        if self.provenance is Provenance.SYNTHETIC and "synthetic_provenance" not in self.training_ineligibility_reasons:
            raise FusionValidationError("synthetic fused vectors require synthetic_provenance ineligibility")

    def as_mapping(self) -> dict[str, float]:
        return dict(zip(self.names, self.values, strict=True))

    def unit_mapping(self) -> dict[str, str]:
        return dict(zip(self.names, self.units, strict=True))


def fuse_multimodal_features(
    visual: VisualObservation, sensors: MatchedSensorMeasurements
) -> MultimodalFeatureVector:
    """Fuse already-matched inputs without converting units or applying timing tolerances."""
    if visual.acquisition_id != sensors.acquisition_id:
        raise FusionValidationError("visual and sensor acquisition_id values must match")
    if visual.bundle_id != sensors.bundle_id:
        raise FusionValidationError("visual and sensor bundle_id values must match")
    if visual.provenance is not sensors.provenance:
        raise FusionValidationError("visual and sensor provenance must match")
    visual_units = tuple(feature.unit for feature in VISUAL_FEATURE_SCHEMA)
    reasons = ("synthetic_provenance",) if visual.provenance is Provenance.SYNTHETIC else ()
    return MultimodalFeatureVector(
        schema_version=MULTIMODAL_FEATURE_SCHEMA_VERSION,
        visual_schema_version=visual.features.schema_version,
        names=tuple(feature.name for feature in VISUAL_FEATURE_SCHEMA) + ("gas_response_value", "weight_g"),
        units=visual_units + (sensors.gas_response_unit, sensors.weight_unit),
        values=visual.features.values + (sensors.gas_response_value, sensors.weight_g),
        acquisition_id=visual.acquisition_id,
        bundle_id=visual.bundle_id,
        provenance=visual.provenance,
        captured_at_utc=visual.captured_at_utc,
        sensor_window_start_utc=sensors.window_start_utc,
        sensor_window_end_utc=sensors.window_end_utc,
        hardware_config_id=sensors.hardware_config_id,
        calibration_id=sensors.calibration_id,
        training_ineligibility_reasons=reasons,
    )


def _validate_identity(value: str, field_name: str) -> None:
    if not _IDENTIFIER.fullmatch(value):
        raise FusionValidationError(f"{field_name} must be a stable identifier")


def _valid_optional_id(value: str | None) -> bool:
    return value is not None and bool(_IDENTIFIER.fullmatch(value))


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise FusionValidationError(f"{field_name} must be timezone-aware")
