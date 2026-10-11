# Dataset, features, artifacts, and evaluation

## Collection format

`data/templates/observations.csv` defines one row per acquisition. `bundle_id` identifies the same physical bundle across all views and dates; `acquisition_id` identifies one image and matched sensor window.

| Fields | Requirement |
| --- | --- |
| `acquisition_id`, `bundle_id`, `session_id` | Stable identifiers; acquisition IDs are unique within a manifest. |
| `captured_at_utc`, `sensor_window_start_utc`, `sensor_window_end_utc` | ISO 8601 UTC timestamps. The validator rejects reversed sensor windows; protocol-defined alignment remains pending. |
| `image_path`, `sensor_trace_path` | Relative paths under the dataset root; preserve original image and trace. |
| `gas_response_value`, `gas_response_unit`, `weight_g` | Finite values with explicit gas-response unit and mass in grams. Do not convert gas output to ethylene without verified calibration. |
| `ripeness_stage`, `spoilage_status` | Blank during collection or team-verified Stage 1–7 and Good/Spoiled. |
| `labeler_id`, `label_protocol_version` | Required provenance when labels are supplied. |
| `hardware_config_id`, `calibration_id` | Required for real training-ready measurements. |
| `is_synthetic`, `notes` | Explicit provenance and observations. |

Validate without modifying source inputs:

```sh
.venv/bin/banana-system collection validate --manifest path/to/observations.csv --dataset-root path/to/data
.venv/bin/banana-system collection replay --manifest path/to/observations.csv --dataset-root path/to/data
```

Blank labels are collection-valid but not suitable for supervised training. Synthetic records, missing raw traces, incomplete labels, or missing label/calibration provenance are also training-ineligible. The validator checks metadata completeness, not experimental validity or calibration quality.

## Labels and splits

The team supplies written Stage 1–7 and Good/Spoiled rubrics, label review/adjudication, and mixed-bundle rules. Stage 7 does not imply Spoiled.

Assign train, validation, and final-test membership by physical `bundle_id` before augmentation or model selection. Every view/time observation of a bundle stays in one group. Keep final-test groups out of detector training, feature selection, preprocessing fitting, and classifier tuning. Exclude IDs, labels, paths, dates, and synthetic flags from predictive features.

## Feature schemas

`visual-v1` takes a non-empty three-channel `uint8` BGR image and an explicit in-bounds `x,y,width,height` region. It does not select a region, remove background, mask pixels, correct color, or classify.

| Position | Name | Unit | Rule |
| --- | --- | --- |
| 1 | `hue_mean_deg` | degrees | Mean OpenCV HSV hue × 2. |
| 2 | `saturation_mean_fraction` | fraction | Mean HSV saturation ÷ 255. |
| 3 | `value_mean_fraction` | fraction | Mean HSV value ÷ 255. |
| 4 | `gray_stddev_fraction` | fraction | Population grayscale standard deviation ÷ 255. |
| 5 | `laplacian_variance_normalized` | fraction_squared | Population `CV_64F` grayscale Laplacian variance ÷ 255². |

`multimodal-v1` preserves positions 1–5, then appends:

| Position | Name | Unit | Rule |
| --- | --- | --- |
| 6 | `gas_response_value` | supplied `gas_response_unit` | Finite raw response; no normalization or chemical conversion. |
| 7 | `weight_g` | g | Finite non-negative mass already in grams. |

Fusion requires matching acquisition ID, bundle ID, and provenance. It retains timestamps, provenance, hardware configuration, and calibration IDs as metadata outside the vector. It deliberately applies no capture/sensor timing tolerance. Any extractor/schema/unit change requires a new schema version and model retraining.

## Model artifacts and evaluation

The supplied local detector checkpoint is `models/banana_yolo26_best.pt`. The desktop accepts it only with Ultralytics `8.4.175`, checkpoint metadata version `8.4.175`, and this exact mapping: `0: stage 3`, `1: stage 5`, `2: stage 7`. It is a detector output only: it draws individual boxes and reports each image-based stage/confidence. It does not supply spoilage, days-until-ripe, a single mixed-bundle stage, or research performance claims. Preserve the checkpoint outside Git and load only trusted artifacts.

Each release records immutable ID, checksum, detector/classifier format, class mapping, ordered feature names/units/schema versions, preprocessing version, source dataset and split manifest, training parameters, software versions, and evaluation report. The Mac runtime was exercised with `ultralytics==8.4.175`; availability of a compatible Ultralytics/PyTorch build for the confirmed Debian 13, Python 3.13.5 Raspberry Pi environment remains an on-device dependency.

Pending team handoff: D06 supplies matched real images/sensor records and independent bundle counts; D07 supplies annotation/training ownership and confirms a Pi-compatible Ultralytics/PyTorch runtime for this supplied artifact; D10 defines whether the proposed 95% target applies to each output, combined success, or another measure. Do not train a classifier until those inputs are available.

Evaluate detector and classifier separately on held-out real bundles. Report detector precision/recall and specified mAP/IoU convention; ripeness accuracy, macro precision/recall/F1, per-stage support, and confusion matrix; spoilage accuracy, precision/recall/F1 with Spoiled positive, support, and confusion matrix; and end-to-end failures/timing. Record excluded scans and unique bundle counts. Do not claim the proposed 95% target without the agreed held-out evaluation.
