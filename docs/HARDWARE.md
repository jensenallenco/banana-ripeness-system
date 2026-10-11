# Hardware setup and handoff

The research team owns assembly, wiring, calibration, electrical checks, and on-device testing. The application only implements adapters against confirmed interfaces.

## Required handoff

| ID | Team must provide | Blocks |
| --- | --- | --- |
| D01 | Pi RAM, storage, OS/version/architecture, Python, power; camera model, known-good image, working capture command/code, required packages, resolution, and exposure/focus/white-balance settings. | Camera adapter and device dependency selection. |
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

The current desktop command is:

```sh
.venv/bin/banana-system desktop --capture-directory captures
```

Today it correctly shows Camera unavailable and disables Capture because D01 is unresolved. It can still open a local image for preview.

After the team supplies D01 and a camera adapter is implemented, verify on the Pi: camera status is available; Capture writes a new timestamped image under `captures/`; preview and displayed saved location match; opening an existing image still works; sensors and model remain explicitly unavailable; and no prediction is shown. Record commit, OS/Python/architecture, camera model, configuration/calibration IDs, command, output path, and sanitized errors.
