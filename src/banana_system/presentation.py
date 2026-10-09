"""Console presentation for development runs."""

from __future__ import annotations

from typing import Protocol

from .contracts import Outcome


class ConsolePresenter:
    def present(self, outcome: Outcome) -> None:
        print(f"scan_id: {outcome.scan_id}")
        print(f"status: {outcome.status}")
        print(f"mode: {outcome.mode}")
        print(f"provenance: {outcome.provenance}")
        if outcome.acquisition:
            print(f"acquisition_id: {outcome.acquisition.acquisition_id}")
            print(f"image_reference: {outcome.acquisition.image_reference}")
        if outcome.error_code:
            print(f"code: {outcome.error_code}")
        if outcome.message:
            print(f"message: {outcome.message}")
        if outcome.provenance.value == "synthetic":
            print("notice: synthetic fixture input; this is not a research result.")

    def reset(self) -> None:
        """Reserved for future device indicator reset; console has no persistent output."""


class PresentationAdapter(Protocol):
    def present(self, outcome: Outcome) -> None: ...

    def reset(self) -> None: ...
