# Hardware setup and handoff

The research team owns assembly, wiring, calibration, electrical checks, and on-device testing. The application only implements adapters against confirmed interfaces.

## Required handoff

| ID | Team must provide | Blocks |
| --- | --- | --- |
| D01 | Confirmed for the camera slice: Debian 13 (Trixie) 64-bit, system Python 3.13.5, Raspberry Pi Camera Module 3 Wide, Picamera2 reference code, 800×480 UI, and a requested 8333 µs exposure. Still provide Pi RAM/storage/power, a known-good device capture, focus/white-balance policy, and final package inventory. | On-device acceptance and reproducible device configuration. |
| D02 | Wiring diagram, physical pins and BCM numbers, active levels, pull configuration, and verified interfaces for button, LED, buzzer, and display. | GPIO and output adapters. |
| D03 | MQ-135 module/datasheet, ADC/interface, reference/input range, electrical compatibility, warm-up/baseline/reset process. | Gas acquisition. |
| D04 | Load-cell capacity/mounting/wiring; HX711 model, pins, gain/rate, tare, known-weight calibration, raw readings, and acceptable behavior. | Weight acquisition and fusion acceptance. |
| D05 | Chamber/lighting arrangement, camera distance, environmental/reset procedure, and acquisition protocol. | Repeatable collection and real feature use. |
| D08 | Display layout/interface and agreed LED/buzzer meanings and timing. | Device presentation. |

All pin assignments remain unset. BCM numbering is the proposed software convention; record both BCM and physical header positions. Do not select pins or electrical values from tutorials.

## Wiring and safety

Raspberry Pi GPIO is digital. The listed HX711 is for the load cell and must not be assumed to provide analogue MQ-135 acquisition. Confirm a suitable ADC and voltage compatibility before any gas adapter is written. Preserve raw sensor responses and units.

Verify power, common ground, logic levels, and each component independently before an integrated run. Do not activate GPIO/output code until the team has approved wiring.

## Calibration and acquisition

The team defines MQ conditioning, clean-chamber baseline, sampling/stability rule, clearing time, exposure duration, and timing alignment. The team also defines HX711 tare, known-weight checks, scale calibration, overload behavior, and repeatability. No timing tolerance, gas concentration conversion, or calibration constant is currently encoded.

Gas output remains a gas-response value unless a verified conversion is supplied. Record `hardware_config_id`, `calibration_id`, raw trace location, units, UTC timestamps, and bundle/acquisition IDs with every real observation.

## Pi desktop/camera verification

Target: Debian 13 (Trixie) 64-bit, system Python 3.13.5, Raspberry Pi Camera Module 3 Wide. Use the team-installed camera stack with the Pi's system Python. Get or update branch `main` from `https://github.com/jensenallenco/banana-ripeness-system.git`:

```sh
# New checkout
git clone https://github.com/jensenallenco/banana-ripeness-system.git
cd banana-ripeness-system
git switch main

# Existing checkout
git fetch origin
git switch main
git pull --ff-only origin main
```

From the repository root, verify the required environment, then launch directly from `src`:

```sh
python3 --version
python3 -c 'import platform; from picamera2 import Picamera2; import cv2; print(platform.platform()); print("camera stack available")'
PYTHONPATH=src python3 -m banana_system.cli desktop --capture-directory captures
```

This is intentionally not a hardware fallback: if Picamera2 or a camera is unavailable, Capture is disabled and the existing-photo workflow remains available. The adapter configures a still stream at 800×480, requests `AeEnable=False` and `ExposureTime=8333`, writes a unique JPEG, then the desktop previews that saved JPEG and displays its path. `8333` µs is a requested control only; record the `ExposureTime` value reported in capture metadata, or its absence.

For acceptance on the Pi, verify: camera status is available; each Capture writes a distinct timestamped JPEG under `captures/`; preview and displayed saved location match; repeated captures work without concurrent captures; camera-unavailable/busy and capture-failure messages are explicit; closing the window releases the camera; opening an existing image still works; sensors and model remain explicitly unavailable; and no prediction is shown. Use a color reference photograph or chart to confirm the saved JPEG has expected colors. Record commit, OS/Python/architecture, camera model, configuration/calibration IDs, command, output path, reported exposure metadata, and sanitized errors. This remains pending device verification.
