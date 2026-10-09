from datetime import datetime

import pytest

from banana_system.contracts import Acquisition, Outcome, OutcomeStatus, Provenance, RunMode, SensorReading, utc_now


def test_sensor_contract_rejects_non_finite_values() -> None:
    with pytest.raises(ValueError, match="finite"):
        SensorReading(float("nan"), "adc_counts", 100.0, utc_now())


def test_non_success_outcome_cannot_contain_prediction() -> None:
    now = utc_now()
    with pytest.raises(ValueError, match="only an ok"):
        Outcome("scan", OutcomeStatus.UNAVAILABLE, RunMode.DEVELOPMENT, Provenance.SYNTHETIC, now, now, ripeness_stage=4)


def test_acquisition_requires_timezone_aware_timestamp() -> None:
    reading = SensorReading(1.0, "adc_counts", 1.0, utc_now())
    with pytest.raises(ValueError, match="timezone-aware"):
        Acquisition("a", "b", datetime.now(), "synthetic://fixture/x", reading, Provenance.SYNTHETIC)
