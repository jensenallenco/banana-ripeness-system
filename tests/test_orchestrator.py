from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Event, Thread

from banana_system.acquisition import CancellationToken, SyntheticFixtureAcquisition
from banana_system.config import load_config
from banana_system.contracts import OutcomeStatus
from banana_system.orchestrator import ScanOrchestrator, ScanState


@dataclass
class RecordingPresenter:
    outcomes: list = field(default_factory=list)
    reset_count: int = 0

    def present(self, outcome) -> None:
        self.outcomes.append(outcome)

    def reset(self) -> None:
        self.reset_count += 1


def make_scanner(acquisition=None):
    config = load_config(Path("config/development.example.toml"))
    adapter = acquisition or SyntheticFixtureAcquisition()
    presenter = RecordingPresenter()
    return ScanOrchestrator(config, adapter, presenter), adapter, presenter


def test_missing_model_is_explicitly_unavailable_and_synthetic() -> None:
    scanner, adapter, presenter = make_scanner()
    outcome = scanner.scan()
    assert outcome.status is OutcomeStatus.UNAVAILABLE
    assert outcome.error_code == "model_unavailable"
    assert outcome.ripeness_stage is None
    assert outcome.spoilage_status is None
    assert outcome.acquisition is not None
    assert outcome.acquisition.provenance.value == "synthetic"
    assert adapter.released is True
    assert presenter.reset_count == 1


def test_pre_cancelled_scan_is_cancelled_and_releases_adapter() -> None:
    scanner, adapter, _ = make_scanner()
    token = CancellationToken()
    token.cancel()
    outcome = scanner.scan(token)
    assert outcome.status is OutcomeStatus.CANCELLED
    assert adapter.released is True
    assert scanner.state is ScanState.READY


class FailingAcquisition(SyntheticFixtureAcquisition):
    def acquire(self, request, cancellation):
        raise RuntimeError("fixture acquisition failed")


def test_acquisition_failure_is_reported_and_resources_are_released() -> None:
    scanner, adapter, presenter = make_scanner(FailingAcquisition())
    outcome = scanner.scan()
    assert outcome.status is OutcomeStatus.ERROR
    assert outcome.error_code == "scan_failed"
    assert "fixture acquisition failed" in outcome.message
    assert adapter.released is True
    assert presenter.reset_count == 1


class BlockingAcquisition(SyntheticFixtureAcquisition):
    def __init__(self) -> None:
        super().__init__()
        self.entered = Event()
        self.allow_finish = Event()

    def acquire(self, request, cancellation):
        self.entered.set()
        self.allow_finish.wait(timeout=2)
        return super().acquire(request, cancellation)


def test_overlapping_scan_is_rejected_and_later_scan_can_run() -> None:
    adapter = BlockingAcquisition()
    scanner, _, _ = make_scanner(adapter)
    thread = Thread(target=scanner.scan)
    thread.start()
    assert adapter.entered.wait(timeout=1)
    overlapping = scanner.scan()
    assert overlapping.status is OutcomeStatus.ERROR
    assert overlapping.error_code == "scan_in_progress"
    adapter.allow_finish.set()
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert scanner.state is ScanState.READY
