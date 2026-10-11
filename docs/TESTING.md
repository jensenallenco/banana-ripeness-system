# Verification and acceptance

Phase 1, portable Phase 2, and portable Phase 3 slices were verified on Mac on 2026-10-12 with Python 3.14.8, pytest 8.4.2, and OpenCV 4.14.0. `python -m pytest` ran 47 tests successfully after editable installation. Desktop tests cover explicit camera unavailability with no simulated output, existing-image loading without source mutation, scaled PPM preview preparation, and invalid image failure. The matching Homebrew Tk binding is installed; `import tkinter` reports Tk 9.1, and `banana-system desktop` rendered successfully. Visual QA found and fixed low-contrast dark-mode status text by applying a controlled light Tk theme. An existing 256×256 JPEG decoded successfully and was passed to the preloaded-photo desktop launch path; its source remained unmodified. CLI help and compilation completed successfully. Fusion, feature, collection, and scan verification remain as previously recorded. No Raspberry Pi, GPIO, camera, sensor, real dataset, detector, classifier, calibration, or research-performance validation has run. The remaining criteria below are intended for later phases.

## Software contracts

Development mode must import/run on a Mac without Pi libraries. Test matching acquisition identity/timing, input validity, feature ordering, schema compatibility, and explicit synthetic provenance. Test missing models, no detection, invalid crop, sensor timeout/invalid values, cancellation, repeated start, storage failure, and device cleanup when those features exist. Hardware mode must never use mocks as a fallback.

Select tests that detect meaningful contract violations; do not add placeholder tests merely to increase a count.

## Research evaluation

| Component | Required evidence |
| --- | --- |
| Bundle detector | Precision, recall, specified mAP/IoU convention, model version, held-out group membership |
| Ripeness classifier | Accuracy, macro precision/recall/F1, per-class support and confusion matrix for Stages 1–7 |
| Spoilage classifier | Accuracy, precision/recall/F1 with Spoiled explicitly positive, support and Good/Spoiled confusion matrix |
| Complete system | Success/failure counts, representative real scan logs, end-to-end and stage timings |

Use real labeled held-out bundles with no upstream training overlap. Log unique bundle counts as well as image/acquisition counts. Repeated views are correlated; report the unit of analysis and any aggregation rule. Record excluded/failed scans and reasons alongside conditional classifier metrics so successful scans alone cannot hide system failures.

Report detector and classifier metrics separately. The 95% target's exact acceptance interpretation is pending team agreement. Do not select models, tune thresholds, or fit preprocessing using final-test results. Confidence/probability estimates, if displayed, are not guaranteed correctness.

## Device acceptance

Verify individual camera/sensor/button/display/indicator behavior, calibration, matched acquisition, model/schema preflight, repeated scans, invalid-input handling, cancellation, storage behavior, and resource cleanup on the actual Pi. Cold-start the installed system with networking disabled and perform a real classification scan. Record commit/config/model IDs and actual timing/memory observations. Latency and repeatability limits must be agreed; none have been invented here.

## Result record

Every verification report states the commit, environment, configuration, dataset/model versions, command, expected behavior, actual outcome, and unresolved dependencies. Distinguish desktop software checks, on-device checks, and measured model performance.
