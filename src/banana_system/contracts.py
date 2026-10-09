"""Typed, hardware-independent contracts used by the scan workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from math import isfinite


class RunMode(StrEnum):
    DEVELOPMENT = "development"
    HARDWARE = "hardware"


class Provenance(StrEnum):
    SYNTHETIC = "synthetic"
    REAL = "real"


class OutcomeStatus(StrEnum):
    OK = "ok"
    NO_BUNDLE = "no_bundle"
    INVALID_INPUT = "invalid_input"
    UNAVAILABLE = "unavailable"
    CANCELLED = "cancelled"
    ERROR = "error"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class SensorReading:
    """A matched sensor summary. Gas values remain a response, never a concentration claim."""

    gas_response_value: float
    gas_response_unit: str
    weight_g: float
    measured_at_utc: datetime

    def __post_init__(self) -> None:
        if not isfinite(self.gas_response_value) or not isfinite(self.weight_g):
            raise ValueError("sensor values must be finite")
        if not self.gas_response_unit.strip():
            raise ValueError("gas_response_unit is required")
        _require_utc(self.measured_at_utc, "measured_at_utc")


@dataclass(frozen=True, slots=True)
class Acquisition:
    """The raw, matched input to later detection and classification phases."""

    acquisition_id: str
    bundle_id: str
    captured_at_utc: datetime
    image_reference: str
    sensor_reading: SensorReading
    provenance: Provenance

    def __post_init__(self) -> None:
        if not self.acquisition_id.strip() or not self.bundle_id.strip():
            raise ValueError("acquisition_id and bundle_id are required")
        if not self.image_reference.strip():
            raise ValueError("image_reference is required")
        _require_utc(self.captured_at_utc, "captured_at_utc")


@dataclass(frozen=True, slots=True)
class ScanRequest:
    scan_id: str
    requested_at_utc: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.scan_id.strip():
            raise ValueError("scan_id is required")
        _require_utc(self.requested_at_utc, "requested_at_utc")


@dataclass(frozen=True, slots=True)
class Outcome:
    """A scan result. Predictions can exist only after a successful classifier invocation."""

    scan_id: str
    status: OutcomeStatus
    mode: RunMode
    provenance: Provenance
    started_at_utc: datetime
    finished_at_utc: datetime
    acquisition: Acquisition | None = None
    error_code: str | None = None
    message: str | None = None
    ripeness_stage: int | None = None
    spoilage_status: str | None = None

    def __post_init__(self) -> None:
        _require_utc(self.started_at_utc, "started_at_utc")
        _require_utc(self.finished_at_utc, "finished_at_utc")
        if self.finished_at_utc < self.started_at_utc:
            raise ValueError("finished_at_utc cannot precede started_at_utc")
        if self.status is not OutcomeStatus.OK and (
            self.ripeness_stage is not None or self.spoilage_status is not None
        ):
            raise ValueError("only an ok outcome may contain predictions")
        if self.status is OutcomeStatus.OK and (
            self.ripeness_stage is None or self.spoilage_status is None
        ):
            raise ValueError("an ok outcome requires both predictions")
        if self.acquisition and self.acquisition.provenance is not self.provenance:
            raise ValueError("outcome and acquisition provenance must match")


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
