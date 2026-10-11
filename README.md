# Cavendish Banana Ripeness and Spoilage System

Local research prototype for Cavendish banana bundles on Raspberry Pi 4. The intended pipeline is camera capture → local bundle detection → OpenCV visual features → gas-response and mass fusion → Scikit-learn Random Forest outputs for Stage 1–7 and Good/Spoiled. Detection and classification remain separate.

The repository is usable for Mac development without GPIO, a camera, sensors, models, or real data. It does not contain a trained detector/classifier or research results.

## Install

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
```

Python `>=3.11,<3.15` is supported. OpenCV is a runtime dependency; pytest is a development dependency. The desktop UI uses Tk:

```sh
.venv/bin/python -c 'import tkinter; print(tkinter.TkVersion)'
```

Homebrew Python may need the matching `python-tk` formula.

## Usage

```sh
# Synthetic scan: deliberately unavailable because models are absent.
.venv/bin/banana-system scan --config config/development.example.toml

# Validate/replay the synthetic collection fixture; no model is invoked.
.venv/bin/banana-system collection validate --manifest data/fixtures/synthetic/observations.csv
.venv/bin/banana-system collection replay --manifest data/fixtures/synthetic/observations.csv

# Inspect or extract visual-v1 from a caller-supplied region.
.venv/bin/banana-system features schema
.venv/bin/banana-system features extract \
  --image data/fixtures/synthetic/images/synthetic-bundle-001.ppm \
  --region 0,0,1,1

# Demonstrate synthetic visual/sensor fusion; no prediction is produced.
.venv/bin/banana-system fusion demo

# Open the desktop image-preview screen.
.venv/bin/banana-system desktop --image /path/to/development-photo.jpg

# Run checks.
.venv/bin/python -m pytest
```

The desktop screen can open existing local photographs without copying or analyzing them. On a Pi with the confirmed Picamera2 stack, it initializes the camera, captures a unique UTC-named JPEG under `--capture-directory`, reloads that saved file for preview, and shows its location. On a Mac or an unavailable/busy camera it remains usable for photo preview and shows an explicit camera state. Sensors and model output remain unavailable by design.

### Pi camera launch

The confirmed target is Debian 13 (Trixie) 64-bit, system Python 3.13.5, and Raspberry Pi Camera Module 3 Wide. Keep the team-installed Picamera2/libcamera stack attached to that system Python; do not add Picamera2 as a cross-platform project dependency. From a checkout whose system Python can import both `picamera2` and `cv2`:

```sh
python3 -c 'from picamera2 import Picamera2; import cv2; print("camera stack available")'
PYTHONPATH=src python3 -m banana_system.cli desktop --capture-directory captures
```

The adapter configures an 800×480 still stream and requests `ExposureTime=8333` µs with auto-exposure disabled. The request is not a guarantee: after each capture the screen reports `ExposureTime` from Picamera2 metadata, or `not reported`. The supplied reference's `BGR888` naming is not used for raw OpenCV arrays here: Picamera2 writes the JPEG and OpenCV reloads it as BGR, avoiding an unverified raw-channel swap.

## Architecture

| Area | Current responsibility |
| --- | --- |
| `config`, `contracts`, `orchestrator` | Validated development mode, typed outcomes, cancellation, cleanup, explicit unavailable results. |
| `acquisition`, `camera`, `desktop`, `presentation` | Synthetic acquisition, optional Picamera2 capture, desktop preview, and console UI. |
| `collection` | Non-mutating CSV manifest validation and replay. |
| `detection` | Detector and banana-region contracts only; no detector implementation. |
| `features` | OpenCV `visual-v1` extraction from an explicit BGR region. |
| `fusion` | Ordered `multimodal-v1` fusion of visual values, raw gas response, and mass in grams. |

Identity, timestamps, provenance, hardware configuration, and calibration IDs are metadata—not predictive features. Training and runtime must share the same versioned feature extractor and validate schema compatibility before prediction.

## Current capabilities and remaining work

Implemented: portable configuration, synthetic scan behavior, desktop photo preview and Picamera2 JPEG capture, collection validation/replay, explicit-region visual features, and multimodal fusion.

Still required: on-device camera acceptance; confirmed sensor interfaces; detector artifact/runtime; labels and matched real observations; model training/evaluation; model artifact loading; physical display/indicator behavior; and Pi/offline validation. See [docs/HARDWARE.md](docs/HARDWARE.md) and [docs/DATASET.md](docs/DATASET.md).

Synthetic fixtures are software tests only. They are marked synthetic, remain ineligible for supervised research training, and never establish performance or food-safety claims.
