# Development environments

## Current state

Phase 1 provides a runnable standard-library Python package, `pyproject.toml`, a validated development TOML configuration, a console CLI, and pytest contract tests. The portable Phase 2 portion adds a CSV manifest validator and synthetic replay command. There is no detector/classifier runtime, trained artifact, hardware driver, service, or dependency lockfile. The development TOML is consumed by the application; the hardware TOML remains intentionally non-operational.

## Proposed setup

| Area | Mac development | Raspberry Pi deployment |
| --- | --- | --- |
| Language | Python; exact supported range chosen in Phase 1 | Compatible Python from confirmed target OS |
| Inputs | Recorded images and explicit synthetic sensor fixtures | Pi Camera, MQ-135 via confirmed acquisition interface, HX711 |
| Presentation | Console first | Confirmed LCD/monitor and indicators |
| Processing | Shared OpenCV feature extraction and Scikit-learn code | Same feature/schema contract and local compatible detector |
| Hardware dependencies | Excluded from normal imports/install path | Device-specific adapters and OS packages |
| Validation | Core contracts and repeatable fixture tests | Physical calibration, real scans, offline startup and latency |

A recent supported 64-bit Raspberry Pi OS is a proposed target, not a confirmed installation. Verify it with the team before pinning device libraries. Evaluate Picamera2 for the confirmed camera/OS; follow the official OS-package installation guidance rather than installing Pi camera libraries on the Mac.

## Phase 1 environment work

Phase 1 supports Python `>=3.11,<3.15` and uses a `src` package. The runtime has no third-party dependencies; pytest is an optional development dependency. OpenCV and Scikit-learn are intentionally deferred until their documented phases need them. This Mac development range is not a Pi compatibility confirmation; the team must still provide the target OS/Python details before device dependencies are selected.

Use a project virtual environment and documented commands. Keep real configuration in ignored files; example configurations contain no credentials, guessed pins, or calibration values. Do not introduce Docker as a requirement for GPIO/camera operation.

Use the commands in the repository README. `banana-system scan --config config/development.example.toml` is a synthetic-only workflow and is expected to report `unavailable` until real model artifacts and their schema/runtime contracts are implemented. It must not be used as device or research validation.

`banana-system collection validate` and `collection replay` need only a CSV manifest and its local input files. They preserve those inputs and are intentionally model-free. The provided fixture demonstrates metadata validation/replay, not camera, sensor, calibration, or collection-protocol correctness.

## Deployment approach

The team obtains the same commit, installs the verified device dependencies and model artifacts, supplies its configuration/calibration files, and runs a hardware preflight. Do not install a background boot service until a manual end-to-end run succeeds. Establish restart/cleanup behavior before unattended use.

Confirm that the selected detector has a usable local artifact/runtime, acceptable Pi 4 resource requirements, and offline restart behavior. Roboflow dataset upload/training may require internet; production scanning must not.

## Primary technical references

Checked on 2026-10-09; verify compatibility again when selecting actual versions.

- [Raspberry Pi camera software and Picamera2](https://www.raspberrypi.com/documentation/computers/camera_software.html): current camera API and OS-package guidance.
- [Raspberry Pi analogue input tutorial](https://projects.raspberrypi.org/en/projects/rpi-adc): digital GPIO and ADC acquisition.
- [Raspberry Pi GPIO documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html): electrical/interface specifications.
- [Scikit-learn StratifiedGroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html): non-overlapping group splits; class balance may be constrained by the groups available.
- [Roboflow local model packages](https://inference-models.roboflow.com/how-to/local-packages/): local/cached loading routes; suitability still depends on the selected model and device.
