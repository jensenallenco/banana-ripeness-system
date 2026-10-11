# Cavendish Banana Ripeness and Spoilage System

Local Raspberry Pi research prototype for camera capture, local banana-stage detection, future visual/sensor features, and future classifiers. The desktop currently supports photograph preview, optional Pi camera capture, and local image-based YOLO observations. It does not produce spoilage, sensor, days-until-ripe, or research-performance results.

## Mac and Windows development

Development photo preview works without GPIO, Picamera2, physical sensors, a trained classifier, or real sensor data. Python `>=3.11,<3.15` is supported.

macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev,yolo]'
.venv/bin/banana-system desktop --image stage_3_image_1.jpg
.venv/bin/python -m pytest
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e '.[dev,yolo]'
.venv\Scripts\banana-system.exe desktop --image stage_3_image_1.jpg
.venv\Scripts\python.exe -m pytest
```

Tk is required for the desktop UI. Homebrew Python may need the matching `python-tk` formula.

### Local image analysis

Place the separately handed-off, trusted checkpoint at `models/banana_yolo26_best.pt`; it is deliberately ignored by Git. The optional `yolo` extra installs `ultralytics==8.4.175`. At load time the app requires runtime and checkpoint version `8.4.175` plus exactly `0: stage 3`, `1: stage 5`, `2: stage 7`.

Open a photograph, then select **Analyze**. The app draws every returned box and reports each stage, confidence, and coordinates. Multiple detections remain separate; no single bundle-stage result is invented. A successful Pi capture starts the same analysis automatically. Missing model/runtime, inference errors, and no detections are explicit states; preview and capture remain usable without analysis.

Verified on Mac: the supplied checkpoint ran under Ultralytics 8.4.175 on all three supplied chamber photographs. This is a runtime check, not detector evaluation or a research claim. See [docs/DATASET.md](docs/DATASET.md) for exact scope and remaining evaluation work.

## Raspberry Pi setup and launch

Target: Debian 13 (Trixie) 64-bit, system Python 3.13.5, Raspberry Pi Camera Module 3 Wide. Use one virtual environment created from that system Python with `--system-site-packages`: Picamera2/libcamera remain visible from the distribution installation while the same interpreter installs and runs YOLO.

```sh
git clone https://github.com/jensenallenco/banana-ripeness-system.git
cd banana-ripeness-system
git switch main

# On later updates:
git pull --ff-only origin main

python3 --version
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[yolo]'
.venv/bin/python -c 'from picamera2 import Picamera2; import cv2, ultralytics, torch; assert ultralytics.__version__ == "8.4.175"; print("camera and YOLO runtime available", torch.__version__)'
test -f models/banana_yolo26_best.pt
.venv/bin/banana-system desktop --capture-directory captures
```

Do not install Picamera2 from PyPI or use `python3` for one component and `.venv/bin/python` for another. The checkpoint must be copied to `models/banana_yolo26_best.pt` separately; it is not in the repository and no replacement weights are downloaded.

The camera uses an 800×480 still stream, requests `ExposureTime=8333` µs with auto-exposure disabled, saves a unique JPEG, reloads it for preview, displays its saved path, then automatically analyzes it when the model/runtime is available. Capture metadata reports actual `ExposureTime` when available; the request is not a guarantee.

Pi acceptance, still pending: verify an available camera; unique JPEGs for consecutive captures; displayed saved paths; automatic boxes/labels/confidences after each successful capture; explicit busy/unavailable/failure states; image-preview operation without model support; and camera release on close. Verify saved JPEG colors with a reference image. Do not claim Pi completion until this is run on the device.

## Architecture and pending work

| Area | Current responsibility |
| --- | --- |
| `camera`, `desktop` | Optional Picamera2 capture, photo preview, and automatic local analysis. |
| `detection` | Validated local YOLO adapter for image-based stages 3, 5, and 7. |
| `collection`, `features`, `fusion` | Manifest validation, explicit-region visual features, and non-predictive sensor fusion. |
| `contracts`, `config`, `orchestrator` | Typed development outcomes, configuration, cancellation, and explicit unavailable states. |

Pending: hardware sensor sampling/calibration, labels and matched real observations, detector evaluation, trained ripeness/spoilage classifiers, spoilage handling, days-until-ripe, display/indicator behavior, and Pi/device validation. Stage 7 is not Spoiled. See [docs/HARDWARE.md](docs/HARDWARE.md) and [docs/DATASET.md](docs/DATASET.md).
