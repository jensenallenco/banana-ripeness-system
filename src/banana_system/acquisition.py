"""Development acquisition adapter. It is deliberately not a fallback for hardware."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .contracts import Acquisition, Provenance, ScanRequest, SensorReading, utc_now


@dataclass(slots=True)
class SyntheticFixtureAcquisition:
    """Explicit test/development fixture; values are synthetic and not research measurements."""

    fixture_name: str = "baseline"
    released: bool = False

    def acquire(self, request: ScanRequest, cancellation: "CancellationToken") -> Acquisition:
        if cancellation.is_cancelled:
            raise ScanCancelled()
        captured_at = utc_now()
        return Acquisition(
            acquisition_id=f"synthetic-{request.scan_id}",
            bundle_id="synthetic-bundle-001",
            captured_at_utc=captured_at,
            image_reference=f"synthetic://fixture/{self.fixture_name}",
            sensor_reading=SensorReading(
                gas_response_value=512.0,
                gas_response_unit="synthetic_adc_counts",
                weight_g=123.4,
                measured_at_utc=captured_at,
            ),
            provenance=Provenance.SYNTHETIC,
        )

    def close(self) -> None:
        self.released = True


class ScanCancelled(Exception):
    pass


class AcquisitionAdapter(Protocol):
    def acquire(self, request: ScanRequest, cancellation: "CancellationToken") -> Acquisition: ...

    def close(self) -> None: ...


class CancellationToken:
    def __init__(self) -> None:
        from threading import Event

        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()
