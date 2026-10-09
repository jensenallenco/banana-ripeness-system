from __future__ import annotations

import csv
from pathlib import Path

import pytest

from banana_system.collection import replay_records, validate_manifest


FIELDS = [
    "acquisition_id", "bundle_id", "session_id", "captured_at_utc", "sensor_window_start_utc",
    "sensor_window_end_utc", "image_path", "sensor_trace_path", "gas_response_value",
    "gas_response_unit", "weight_g", "ripeness_stage", "spoilage_status", "labeler_id",
    "label_protocol_version", "hardware_config_id", "calibration_id", "is_synthetic", "notes",
]


def write_manifest(root: Path, **changes: str) -> Path:
    (root / "images").mkdir()
    (root / "traces").mkdir()
    (root / "images" / "bundle.jpg").write_bytes(b"original test input")
    (root / "traces" / "sensor.csv").write_text("raw,trace\n", encoding="utf-8")
    row = {
        "acquisition_id": "acquisition-001", "bundle_id": "bundle-001", "session_id": "session-001",
        "captured_at_utc": "2026-10-09T00:00:05Z", "sensor_window_start_utc": "2026-10-09T00:00:00Z",
        "sensor_window_end_utc": "2026-10-09T00:00:10Z", "image_path": "images/bundle.jpg",
        "sensor_trace_path": "traces/sensor.csv", "gas_response_value": "412.5", "gas_response_unit": "adc_counts",
        "weight_g": "123.4", "ripeness_stage": "4", "spoilage_status": "Good", "labeler_id": "labeler-1",
        "label_protocol_version": "protocol-1", "hardware_config_id": "hardware-1", "calibration_id": "calibration-1",
        "is_synthetic": "false", "notes": "",
    }
    row.update(changes)
    manifest = root / "observations.csv"
    with manifest.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(row)
    return manifest


def test_synthetic_fixture_validates_but_is_not_training_suitable() -> None:
    fixture = Path("data/fixtures/synthetic/observations.csv")
    report = validate_manifest(fixture)
    assert report.is_valid
    assert len(report.records) == 1
    assert report.synthetic_count == 1
    assert report.training_suitable_count == 0
    assert {issue.code for issue in report.issues} >= {"synthetic_provenance", "incomplete_labels", "missing_calibration_provenance"}
    replayed = replay_records(report)
    assert replayed[0].values["ripeness_stage"] == ""
    assert replayed[0].image_file.read_text(encoding="utf-8").startswith("P3")


def test_complete_real_record_is_training_suitable_without_mutating_inputs(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path)
    original_image = (tmp_path / "images" / "bundle.jpg").read_bytes()
    report = validate_manifest(manifest)
    assert report.is_valid
    assert report.training_suitable_count == 1
    assert not report.issues
    assert (tmp_path / "images" / "bundle.jpg").read_bytes() == original_image


@pytest.mark.parametrize(
    ("changes", "expected_code"),
    [
        ({"acquisition_id": "bad id"}, "invalid_identifier"),
        ({"captured_at_utc": "2026-10-09T00:00:05"}, "invalid_utc_timestamp"),
        ({"image_path": "../outside.jpg"}, "unsafe_path"),
        ({"gas_response_value": "nan"}, "non_finite_number"),
        ({"weight_g": "-1"}, "negative_mass"),
        ({"gas_response_unit": ""}, "missing_unit"),
        ({"ripeness_stage": "8"}, "invalid_ripeness_stage"),
        ({"spoilage_status": "Unknown"}, "invalid_spoilage_status"),
        ({"is_synthetic": "maybe"}, "invalid_provenance"),
    ],
)
def test_invalid_collection_values_are_rejected(tmp_path: Path, changes: dict[str, str], expected_code: str) -> None:
    report = validate_manifest(write_manifest(tmp_path, **changes))
    assert not report.is_valid
    assert expected_code in {issue.code for issue in report.issues}


def test_blank_labels_are_allowed_for_collection_but_block_training(tmp_path: Path) -> None:
    report = validate_manifest(write_manifest(tmp_path, ripeness_stage="", spoilage_status=""))
    assert report.is_valid
    assert report.training_suitable_count == 0
    assert "incomplete_labels" in {issue.code for issue in report.issues}


def test_replay_rejects_invalid_manifest(tmp_path: Path) -> None:
    report = validate_manifest(write_manifest(tmp_path, image_path="images/missing.jpg"))
    with pytest.raises(ValueError, match="validation errors"):
        replay_records(report)


def test_symlinked_input_cannot_escape_dataset_root(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path)
    external = tmp_path.parent / "outside-image.jpg"
    external.write_bytes(b"outside")
    image = tmp_path / "images" / "bundle.jpg"
    image.unlink()
    image.symlink_to(external)
    report = validate_manifest(manifest)
    assert not report.is_valid
    assert "unsafe_path" in {issue.code for issue in report.issues}
