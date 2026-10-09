"""Non-mutating manifest validation and replay for dataset collection workflows."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
import re


REQUIRED_FIELDS = frozenset(
    {
        "acquisition_id",
        "bundle_id",
        "session_id",
        "captured_at_utc",
        "sensor_window_start_utc",
        "sensor_window_end_utc",
        "image_path",
        "sensor_trace_path",
        "gas_response_value",
        "gas_response_unit",
        "weight_g",
        "ripeness_stage",
        "spoilage_status",
        "labeler_id",
        "label_protocol_version",
        "hardware_config_id",
        "calibration_id",
        "is_synthetic",
        "notes",
    }
)
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_PATH_SUFFIXES = frozenset({".bmp", ".jpeg", ".jpg", ".png", ".ppm", ".tif", ".tiff"})


@dataclass(frozen=True, slots=True)
class ManifestIssue:
    row_number: int
    field: str
    code: str
    message: str
    severity: str = "error"


@dataclass(frozen=True, slots=True)
class CollectionRecord:
    """Raw manifest values and resolved input locations; no values are transformed or persisted."""

    row_number: int
    values: dict[str, str]
    image_file: Path
    sensor_trace_file: Path | None
    is_synthetic: bool
    training_suitable: bool
    training_blockers: tuple[str, ...]


@dataclass(slots=True)
class ManifestReport:
    manifest_path: Path
    dataset_root: Path
    records: list[CollectionRecord] = field(default_factory=list)
    issues: list[ManifestIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def training_suitable_count(self) -> int:
        return sum(record.training_suitable for record in self.records)

    @property
    def synthetic_count(self) -> int:
        return sum(record.is_synthetic for record in self.records)


def validate_manifest(manifest_path: Path, dataset_root: Path | None = None) -> ManifestReport:
    """Validate a collection manifest without copying, changing, or interpreting raw inputs."""
    manifest_path = manifest_path.resolve()
    root = (dataset_root or manifest_path.parent).resolve()
    report = ManifestReport(manifest_path, root)
    try:
        manifest_file = manifest_path.open(newline="", encoding="utf-8")
    except OSError as exc:
        report.issues.append(ManifestIssue(0, "manifest", "manifest_unreadable", str(exc)))
        return report

    with manifest_file:
        reader = csv.DictReader(manifest_file)
        fieldnames = set(reader.fieldnames or [])
        for missing in sorted(REQUIRED_FIELDS - fieldnames):
            report.issues.append(ManifestIssue(0, missing, "missing_column", "Required column is absent."))
        if report.issues:
            return report
        seen_acquisition_ids: set[str] = set()
        for row_number, raw_row in enumerate(reader, start=2):
            row = {key: (value or "").strip() for key, value in raw_row.items() if key is not None}
            row_issues = _validate_row(row_number, row, root, seen_acquisition_ids)
            report.issues.extend(row_issues)
            if any(issue.severity == "error" for issue in row_issues):
                continue
            is_synthetic = row["is_synthetic"].lower() == "true"
            blockers = _training_blockers(row, is_synthetic)
            for blocker in blockers:
                report.issues.append(ManifestIssue(row_number, "training", blocker, _blocker_message(blocker), "warning"))
            report.records.append(
                CollectionRecord(
                    row_number=row_number,
                    values=row,
                    image_file=_resolve_input_path(row["image_path"], root),
                    sensor_trace_file=_resolve_input_path(row["sensor_trace_path"], root)
                    if row["sensor_trace_path"]
                    else None,
                    is_synthetic=is_synthetic,
                    training_suitable=not blockers,
                    training_blockers=tuple(blockers),
                )
            )
    return report


def replay_records(report: ManifestReport) -> tuple[CollectionRecord, ...]:
    """Return validated records for inspection only; this never invokes a model or writes files."""
    if not report.is_valid:
        raise ValueError("cannot replay a manifest with validation errors")
    return tuple(report.records)


def _validate_row(row_number: int, row: dict[str, str], root: Path, seen_ids: set[str]) -> list[ManifestIssue]:
    issues: list[ManifestIssue] = []
    for field_name in ("acquisition_id", "bundle_id", "session_id"):
        if not _IDENTIFIER.fullmatch(row[field_name]):
            issues.append(ManifestIssue(row_number, field_name, "invalid_identifier", "Use 1–128 letters, digits, dots, hyphens, or underscores; begin with a letter or digit."))
    acquisition_id = row["acquisition_id"]
    if acquisition_id in seen_ids:
        issues.append(ManifestIssue(row_number, "acquisition_id", "duplicate_acquisition_id", "acquisition_id must be unique within a manifest."))
    elif _IDENTIFIER.fullmatch(acquisition_id):
        seen_ids.add(acquisition_id)

    timestamps = {name: _parse_utc(row[name]) for name in ("captured_at_utc", "sensor_window_start_utc", "sensor_window_end_utc")}
    for field_name, value in timestamps.items():
        if value is None:
            issues.append(ManifestIssue(row_number, field_name, "invalid_utc_timestamp", "Use an ISO 8601 timestamp with a UTC offset (Z or +00:00)."))
    if all(timestamps.values()) and timestamps["sensor_window_start_utc"] > timestamps["sensor_window_end_utc"]:
        issues.append(ManifestIssue(row_number, "sensor_window_end_utc", "invalid_sensor_window", "sensor_window_end_utc must not precede sensor_window_start_utc."))

    image_file = _validate_input_path(row_number, "image_path", row["image_path"], root, required=True)
    trace_file = _validate_input_path(row_number, "sensor_trace_path", row["sensor_trace_path"], root, required=False)
    issues.extend(image_file)
    issues.extend(trace_file)
    if not image_file and Path(row["image_path"]).suffix.lower() not in _PATH_SUFFIXES:
        issues.append(ManifestIssue(row_number, "image_path", "unsupported_image_suffix", "Image path must have a supported image suffix."))

    for field_name in ("gas_response_value", "weight_g"):
        try:
            value = float(row[field_name])
        except ValueError:
            issues.append(ManifestIssue(row_number, field_name, "invalid_number", "A finite numeric value is required."))
            continue
        if not isfinite(value):
            issues.append(ManifestIssue(row_number, field_name, "non_finite_number", "A finite numeric value is required."))
        elif field_name == "weight_g" and value < 0:
            issues.append(ManifestIssue(row_number, field_name, "negative_mass", "weight_g must be zero or greater."))
    if not row["gas_response_unit"]:
        issues.append(ManifestIssue(row_number, "gas_response_unit", "missing_unit", "gas_response_unit is required and must describe the recorded response."))
    if row["is_synthetic"].lower() not in {"true", "false"}:
        issues.append(ManifestIssue(row_number, "is_synthetic", "invalid_provenance", "is_synthetic must be true or false."))
    _validate_labels(row_number, row, issues)
    return issues


def _validate_labels(row_number: int, row: dict[str, str], issues: list[ManifestIssue]) -> None:
    stage = row["ripeness_stage"]
    spoilage = row["spoilage_status"]
    if stage and stage not in {str(value) for value in range(1, 8)}:
        issues.append(ManifestIssue(row_number, "ripeness_stage", "invalid_ripeness_stage", "ripeness_stage must be blank or one of 1 through 7."))
    if spoilage and spoilage not in {"Good", "Spoiled"}:
        issues.append(ManifestIssue(row_number, "spoilage_status", "invalid_spoilage_status", "spoilage_status must be blank, Good, or Spoiled."))


def _training_blockers(row: dict[str, str], is_synthetic: bool) -> list[str]:
    blockers: list[str] = []
    if is_synthetic:
        blockers.append("synthetic_provenance")
    if not row["ripeness_stage"] or not row["spoilage_status"]:
        blockers.append("incomplete_labels")
    if (row["ripeness_stage"] or row["spoilage_status"]) and (not row["labeler_id"] or not row["label_protocol_version"]):
        blockers.append("missing_label_provenance")
    if not row["sensor_trace_path"]:
        blockers.append("missing_sensor_trace")
    if not row["hardware_config_id"] or not row["calibration_id"]:
        blockers.append("missing_calibration_provenance")
    return blockers


def _blocker_message(blocker: str) -> str:
    return {
        "synthetic_provenance": "Synthetic records are not suitable for supervised research training.",
        "incomplete_labels": "Blank labels are allowed during collection but make this record unsuitable for supervised training.",
        "missing_label_provenance": "Labels require labeler_id and label_protocol_version before supervised training.",
        "missing_sensor_trace": "A raw sensor trace is required before supervised training.",
        "missing_calibration_provenance": "hardware_config_id and calibration_id are required before supervised training.",
    }[blocker]


def _parse_utc(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed


def _validate_input_path(row_number: int, field: str, value: str, root: Path, required: bool) -> list[ManifestIssue]:
    if not value:
        return [ManifestIssue(row_number, field, "missing_path", "A relative path is required.")] if required else []
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return [ManifestIssue(row_number, field, "unsafe_path", "Path must be relative to the dataset root and cannot escape it.")]
    resolved = _resolve_input_path(value, root)
    if not resolved.is_relative_to(root):
        return [ManifestIssue(row_number, field, "unsafe_path", "Path must resolve beneath the dataset root.")]
    if not resolved.is_file():
        return [ManifestIssue(row_number, field, "missing_input_file", "Referenced input file does not exist under the dataset root.")]
    return []


def _resolve_input_path(value: str, root: Path) -> Path:
    return (root / value).resolve()
