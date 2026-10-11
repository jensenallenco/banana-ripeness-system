"""Camera boundary. Real Pi adapters are intentionally absent until the team confirms one."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CameraStatus:
    available: bool
    message: str


class CameraUnavailableError(RuntimeError):
    pass


class CameraAdapter(Protocol):
    def status(self) -> CameraStatus: ...

    def capture(self, destination: Path) -> Path: ...


class UnavailableCameraAdapter:
    """Explicit placeholder; it never simulates a camera or writes an image."""

    def status(self) -> CameraStatus:
        return CameraStatus(
            available=False,
            message="Camera unavailable: the confirmed Pi OS/camera setup has not been supplied.",
        )

    def capture(self, destination: Path) -> Path:
        raise CameraUnavailableError(self.status().message)
