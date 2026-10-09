# Verification and acceptance

Phase 1, portable Phase 2, and the portable visual-feature slice of Phase 3 were verified on Mac on 2026-10-09 with Python 3.14.7, pytest 8.4.2, and OpenCV 4.14.0. `python -m pytest` ran 30 tests successfully after editable installation. Synthetic-image tests cover schema order, region-only extraction, color/texture values, non-mutation, invalid image dtype/shape, and invalid crop coordinates. The documented feature schema/extraction CLI completed successfully and printed `detection=not_run predictions=none`. The documented synthetic collection and scan checks remain as previously recorded. `python -m compileall -q src tests` completed successfully. No Raspberry Pi, GPIO, camera, sensor, real dataset, detector, classifier, calibration, or research-performance validation has run. The remaining criteria below are intended for later phases.

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
