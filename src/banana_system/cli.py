"""Command-line development entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from .acquisition import SyntheticFixtureAcquisition
from .collection import replay_records, validate_manifest
from .config import ConfigurationError, load_config
from .detection import BananaRegion, RegionValidationError
from .features import VISUAL_FEATURE_SCHEMA, extract_visual_features
from .orchestrator import ScanOrchestrator
from .presentation import ConsolePresenter


def main() -> int:
    parser = argparse.ArgumentParser(description="Cavendish banana development scanner")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan_parser = subparsers.add_parser("scan", help="run the synthetic scan workflow")
    scan_parser.add_argument("--config", type=Path, default=Path("config/development.example.toml"))
    collection_parser = subparsers.add_parser("collection", help="validate or replay a collection manifest without predictions")
    collection_parser.add_argument("action", choices=["validate", "replay"])
    collection_parser.add_argument("--manifest", type=Path, required=True)
    collection_parser.add_argument("--dataset-root", type=Path)
    features_parser = subparsers.add_parser("features", help="extract visual-v1 features from an explicit region; never detects or predicts")
    features_parser.add_argument("action", choices=["extract", "schema"])
    features_parser.add_argument("--image", type=Path)
    features_parser.add_argument("--region", help="Pixel region as x,y,width,height; required for extract.")
    args = parser.parse_args()
    if args.command == "collection":
        report = validate_manifest(args.manifest, args.dataset_root)
        print(f"manifest: {report.manifest_path}")
        print(f"collection_valid: {str(report.is_valid).lower()}")
        print(f"valid_records: {len(report.records)}")
        print(f"synthetic_records: {report.synthetic_count}")
        print(f"training_suitable_records: {report.training_suitable_count}")
        for issue in report.issues:
            print(f"{issue.severity}: row {issue.row_number} {issue.field} [{issue.code}] {issue.message}")
        if args.action == "replay" and report.is_valid:
            for record in replay_records(report):
                print(f"replay: acquisition_id={record.values['acquisition_id']} image_path={record.values['image_path']} provenance={'synthetic' if record.is_synthetic else 'real'} predictions=none")
        return 0 if report.is_valid else 1
    if args.command == "features":
        if args.action == "schema":
            print("schema_version: visual-v1")
            for feature in VISUAL_FEATURE_SCHEMA:
                print(f"{feature.name} [{feature.unit}]: {feature.extraction}")
            return 0
        if args.image is None or args.region is None:
            parser.error("features extract requires --image and --region")
        try:
            coordinates = tuple(int(value) for value in args.region.split(","))
            if len(coordinates) != 4:
                raise ValueError
            image = cv2.imread(str(args.image), cv2.IMREAD_COLOR)
            if image is None:
                parser.error(f"unable to read image: {args.image}")
            vector = extract_visual_features(image, BananaRegion(*coordinates))
        except (ValueError, RegionValidationError) as exc:
            parser.error(f"invalid feature input: {exc}")
        print(f"schema_version: {vector.schema_version}")
        for name, value in vector.as_mapping().items():
            print(f"{name}: {value:.12g}")
        print("provenance: input image only; detection=not_run predictions=none")
        return 0
    try:
        config = load_config(args.config)
    except ConfigurationError as exc:
        parser.error(str(exc))
    outcome = ScanOrchestrator(config, SyntheticFixtureAcquisition(), ConsolePresenter()).scan()
    return 0 if outcome.status.value in {"unavailable", "ok"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
