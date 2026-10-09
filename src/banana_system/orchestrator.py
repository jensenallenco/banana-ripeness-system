"""Serial scan lifecycle with explicit model availability and cleanup guarantees."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from threading import Lock
from uuid import uuid4

from .acquisition import AcquisitionAdapter, CancellationToken, ScanCancelled
from .config import AppConfig
from .contracts import Outcome, OutcomeStatus, ScanRequest, utc_now
from .presentation import PresentationAdapter


class ScanState(StrEnum):
    READY = "ready"
    ACQUIRING = "acquiring"
    PRESENTING = "presenting"


class ScanOrchestrator:
    def __init__(self, config: AppConfig, acquisition: AcquisitionAdapter, presenter: PresentationAdapter) -> None:
        self._config = config
        self._acquisition = acquisition
        self._presenter = presenter
        self._lock = Lock()
        self.state = ScanState.READY

    def scan(self, cancellation: CancellationToken | None = None) -> Outcome:
        token = cancellation or CancellationToken()
        scan_id = str(uuid4())
        started_at = utc_now()
        if not self._lock.acquire(blocking=False):
            return self._outcome(scan_id, OutcomeStatus.ERROR, started_at, "scan_in_progress", "A scan is already running.")
        acquisition = None
        try:
            if token.is_cancelled:
                return self._outcome(scan_id, OutcomeStatus.CANCELLED, started_at, "cancelled", "Scan cancelled before acquisition.")
            self.state = ScanState.ACQUIRING
            acquisition = self._acquisition.acquire(ScanRequest(scan_id, started_at), token)
            if token.is_cancelled:
                return self._outcome(scan_id, OutcomeStatus.CANCELLED, started_at, "cancelled", "Scan cancelled during acquisition.", acquisition)
            artifact = self._config.classifier_artifact
            if artifact is None or not artifact.is_file():
                return self._outcome(scan_id, OutcomeStatus.UNAVAILABLE, started_at, "model_unavailable", "Classification is unavailable because required local model artifacts are not configured.", acquisition)
            return self._outcome(scan_id, OutcomeStatus.UNAVAILABLE, started_at, "classifier_not_implemented", "Classifier loading is scheduled for Phase 4.", acquisition)
        except ScanCancelled:
            return self._outcome(scan_id, OutcomeStatus.CANCELLED, started_at, "cancelled", "Scan cancelled during acquisition.", acquisition)
        except Exception as exc:
            return self._outcome(scan_id, OutcomeStatus.ERROR, started_at, "scan_failed", f"Scan failed: {exc}", acquisition)
        finally:
            try:
                self._acquisition.close()
            finally:
                self._lock.release()
                self.state = ScanState.READY

    def _outcome(self, scan_id: str, status: OutcomeStatus, started_at: datetime, code: str, message: str, acquisition: object | None = None) -> Outcome:
        outcome = Outcome(scan_id, status, self._config.mode, self._config.input_provenance, started_at, utc_now(), acquisition, code, message)
        self._presenter.present(outcome)
        self._presenter.reset()
        return outcome
