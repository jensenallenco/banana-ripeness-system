# Verification and acceptance

Phase 1 and portable Phase 2 Mac verification completed on 2026-10-09 with Python 3.14.7 and pytest 8.4.2: `python -m pytest` ran 22 tests successfully after editable installation. The documented synthetic collection validation and replay commands completed successfully: the fixture was collection-valid, had one synthetic record, zero training-suitable records, and replay printed `predictions=none`. The development scan CLI also returned `status: unavailable`, `provenance: synthetic`, and no prediction fields because model artifacts are absent. `python -m compileall -q src tests` completed successfully. No Raspberry Pi, GPIO, camera, sensor, real dataset, detector, classifier, calibration, or research-performance validation has run. The remaining criteria below are intended for later phases.

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
