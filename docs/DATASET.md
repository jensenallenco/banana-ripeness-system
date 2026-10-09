# Dataset collection and handoff

Status: the portable CSV validator and synthetic replay fixture are implemented. The team must still confirm labels, measurement protocol, column units, and real collection workflow before production collection. `data/templates/observations.csv` contains a header only.

## Identity and labels

`bundle_id` identifies the same physical bundle across angles, dates, and ripeness changes. `acquisition_id` identifies one image with its corresponding measurement window. Reusing a bundle on another day does not create an independent bundle. Track related/subdivided material when relevant so related samples cannot cross evaluation boundaries.

The team supplies a written Stage 1–7 rubric, Good/Spoiled rubric, adjudication process, and mixed-ripeness bundle rule. Record labeler and label-protocol version. Unknown labels remain blank and are excluded from supervised training. A brown spot or Stage 7 is not automatically a Spoiled label.

## Proposed observation fields

| Fields | Meaning |
| --- | --- |
| `acquisition_id`, `bundle_id`, `session_id` | Unique observation, physical bundle, collection session |
| `captured_at_utc`, `sensor_window_start_utc`, `sensor_window_end_utc` | ISO 8601 timestamps with UTC timezone; allow alignment checks |
| `image_path`, `sensor_trace_path` | Paths relative to dataset root; retain original image and measurement trace |
| `gas_response_value`, `gas_response_unit` | Recorded gas-response summary and explicit unit, such as ADC counts; do not mix units |
| `weight_g` | Calibrated bundle mass in grams |
| `ripeness_stage`, `spoilage_status` | Team-verified 1–7 and Good/Spoiled, independently labeled |
| `labeler_id`, `label_protocol_version` | Label provenance |
| `hardware_config_id`, `calibration_id` | Device/chamber settings and sensor calibration record |
| `is_synthetic`, `notes` | `true`/`false` provenance and acquisition/label observations |

One row describes one acquisition. The sensor summary and stability rule must be defined before training; record raw traces so different summaries can be audited. Do not pair a photograph with a different bundle's sensor data or silently reuse a stale reading. The acceptable timing window is pending the team's experimental protocol.

## Current validator behavior

`banana-system collection validate --manifest <path> [--dataset-root <path>]` is a non-mutating portable check. It requires all listed columns; validates stable identifier syntax and unique `acquisition_id` values; requires ISO 8601 UTC timestamps and a non-reversed sensor window; accepts only relative existing image/trace paths beneath the dataset root; and rejects non-finite gas/weight values, negative mass, absent gas-response units, malformed provenance, and invalid nonblank labels. It does not inspect, convert, rename, copy, calibrate, or otherwise alter original image and trace inputs.

Blank ripeness/spoilage labels are valid collection records and receive a training-suitability warning rather than a validation error. A record is also unsuitable for supervised research training if it is synthetic or lacks raw trace, calibration/hardware, or supplied-label provenance. These checks establish metadata completeness only; they do not establish experimental validity, timing tolerance, calibration quality, or label quality. The synthetic fixture under `data/fixtures/synthetic/` demonstrates this workflow and must never be used as research evidence.

## What the team supplies

- Original images, bundle identities, collection timestamps, and reviewed labels.
- Matched MQ-135 measurements and calibrated weight data, units, raw traces, and calibration/configuration records.
- Roboflow project/version information, annotations, detector training/export ownership, and available model artifacts.
- Stage/spoilage labeling criteria, mixed-bundle handling, chamber/lighting setup, and acquisition protocol.
- Dataset inventory showing independent bundles and acquisitions per class, with access/storage agreed.

Photographs and Roboflow annotations can support object detection, but alone do not supply the gas/weight features needed by the documented multimodal classifier.

## Splits and evaluation

Assign training, validation, and test membership by physical bundle before augmentation or model training. Every view and time observation of a bundle follows its group. Honor the same group boundaries in Roboflow detector datasets and Random Forest datasets. Never use a final-test bundle to train the detector upstream of the classifier.

Choose split sizes and stratification based on available independent groups and label coverage; do not invent a fixed sample count or guarantee balanced folds. Group-aware cross-validation may be used within training data when feasible. Keep a final held-out set separate from model selection. If sample coverage cannot support meaningful evaluation, report the limitation.

Fit learned preprocessing only on training data. Exclude bundle/session IDs, labels, filenames, collection dates, and synthetic flags from predictive features. Detect exact/near duplicates and overlapping groups. Measure ripeness and spoilage separately; record support and missing classes rather than hiding them.

## Feature registry

The portable Phase 3 implementation establishes the following initial visual-only schema. It is an engineering baseline, not evidence that these values predict ripeness or spoilage. Training and runtime must use this exact implementation and verify `schema_version = visual-v1`; any change requires a new schema version and retraining.

| Position | Name | Unit | Extraction and preprocessing |
| --- | --- | --- | --- |
| 1 | `hue_mean_deg` | degrees | Mean OpenCV HSV hue from an explicit BGR crop, multiplied by 2 (OpenCV hue range 0–179). |
| 2 | `saturation_mean_fraction` | fraction | Mean HSV saturation divided by 255. |
| 3 | `value_mean_fraction` | fraction | Mean HSV value divided by 255. |
| 4 | `gray_stddev_fraction` | fraction | Population standard deviation of OpenCV grayscale intensity divided by 255. |
| 5 | `laplacian_variance_normalized` | fraction_squared | Population variance of the `CV_64F` grayscale Laplacian, divided by 255². |

Input must be a non-empty three-channel `uint8` BGR image (OpenCV convention) and a caller-supplied in-bounds integer `x,y,width,height` crop. The original image is not changed. There is no background removal, pixel mask, color correction, illumination normalization, crop expansion, detector output, feature fusion, or classifier in this slice. Hue's ordinary arithmetic mean is retained as a simple initial baseline; its circular-statistics limitations must be evaluated on real data before claiming it is suitable.

Record sensor normalization and calibration provenance when sensor fusion is specified. Reject incompatible models or feature schemas at inference.

Preserve raw files unchanged. Keep datasets outside source control and put small synthetic fixtures in a clearly named test location. Store real-data versions, file checksums, split assignments, and collection/calibration metadata in the controlled dataset handoff.
