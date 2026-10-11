# Hardware handoff

The team owns assembly, wiring, electrical verification, and on-device execution. The developer implements adapters against their confirmed interfaces.

## Required information

| Component | Team must provide before its real adapter is implemented |
| --- | --- |
| Raspberry Pi 4 | RAM, storage, OS name/version, architecture, Python version, available space, power supply |
| Pi Camera Module | Exact model, capture test image, working camera command, resolution, focus/exposure/white-balance settings |
| MQ-135 | Exact module/datasheet, analog output interface, ADC or equivalent acquisition device, reference/input range, connection diagram, warm-up/baseline protocol |
| Load cell | Capacity, mounting, wiring, known-weight calibration method |
| HX711 | Exact board, data/clock pins, gain/rate, raw test readings, tare and scale calibration record |
| LCD/Monitor | Exact model, interface (HDMI/I2C/SPI/etc.), resolution or character layout, address if relevant |
| Start button | GPIO assignment, numbering scheme, wiring/pull configuration, active level |
| LED | Number/type, pins, active level, agreed status meanings |
| Buzzer | Active/passive type, driver circuit, pin, active level, agreed duration/pattern |
| Lighting and chamber | Physical arrangement, fixed/switched lighting, background, camera distance, chamber volume, ventilation/reset procedure |
| Power distribution | Supply ratings, shared ground, module logic levels and driver arrangements |

Use BCM numbering as a proposed software convention, but record both BCM numbers and physical header pins in the team's wiring table. All current assignments are unset.

## MQ-135 interface gap

The provided list includes HX711 for the load cell, but no ADC for the MQ-135 analog output. Raspberry Pi GPIO is digital; confirm a suitable analog acquisition interface and electrical compatibility with the team. HX711 is not assumed to be an available general-purpose gas-sensor ADC. An MQ module's digital threshold output does not provide the continuous response contemplated by the paper.

Do not choose wiring or calibration constants from an unrelated tutorial. Preserve raw readings and units; converting gas response into a chemical concentration requires a validated calibration model that has not been supplied.

## Calibration and acquisition

The team must establish MQ conditioning/warm-up, clean-chamber baseline, sampling/stability criteria, exposure duration, and clearing between bundles. They must also establish HX711 tare, known-weight checks, overload behavior, and acceptable repeatability. These timings and tolerances are unknown; software will expose configurable settings once confirmed.

## Remote testing handoff

For each device check, send the Git commit, OS/Python/architecture, hardware configuration ID, calibration ID, exact command, sanitized log/traceback, and applicable photo/result. Do not send passwords or access keys in logs. Secure private remote access is optional; executing commands locally and returning evidence is sufficient.

Approve the wiring and verify components independently before activating the integrated hardware workflow. A Mac-only test does not establish GPIO or sensor correctness.

## Desktop camera handoff

The desktop screen is available through `banana-system desktop`, but its Capture control remains disabled until the camera information in D01 is supplied. To implement and verify the Pi adapter, provide the exact model, Pi OS/Python/architecture, a known-good test image, and the existing working camera command or code with its required package/install steps and capture settings. Do not send credentials.

After an adapter is implemented from that evidence, launch `.venv/bin/banana-system desktop --capture-directory captures`. Confirm camera status, one newly saved image, the preview, and the path displayed by the UI. The screen intentionally reports sensors/model as unavailable and must not be used to claim a measurement or prediction.
