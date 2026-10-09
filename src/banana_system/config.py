"""Configuration loading and validation. Hardware remains intentionally unsupported in Phase 1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

from .contracts import Provenance, RunMode


class ConfigurationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PresentationConfig:
    backend: str


@dataclass(frozen=True, slots=True)
class AppConfig:
    schema_version: int
    mode: RunMode
    input_provenance: Provenance
    prediction_policy: str
    presentation: PresentationConfig
    classifier_artifact: Path | None = None


def load_config(path: Path) -> AppConfig:
    try:
        with path.open("rb") as config_file:
            raw = tomllib.load(config_file)
    except FileNotFoundError as exc:
        raise ConfigurationError(f"configuration file does not exist: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(f"invalid TOML in {path}: {exc}") from exc

    if raw.get("schema_version") != 1:
        raise ConfigurationError("schema_version must be 1")
    try:
        mode = RunMode(raw["mode"])
        provenance = Provenance(raw["input_provenance"])
    except (KeyError, ValueError) as exc:
        raise ConfigurationError("mode and input_provenance must be supported values") from exc
    if mode is not RunMode.DEVELOPMENT:
        raise ConfigurationError("hardware mode is not implemented in Phase 1; it cannot use fixtures")
    if provenance is not Provenance.SYNTHETIC:
        raise ConfigurationError("development mode requires explicit synthetic input_provenance")
    if raw.get("prediction_policy") != "unavailable_without_model":
        raise ConfigurationError("prediction_policy must be unavailable_without_model")
    presentation = raw.get("presentation")
    if not isinstance(presentation, dict) or presentation.get("backend") != "console":
        raise ConfigurationError("Phase 1 supports only presentation.backend = console")

    artifact = raw.get("models", {}).get("classifier_artifact")
    artifact_path = None
    if artifact not in (None, "", "UNSET"):
        artifact_path = (path.parent / str(artifact)).resolve()
    return AppConfig(1, mode, provenance, raw["prediction_policy"], PresentationConfig("console"), artifact_path)
