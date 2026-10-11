# Software architecture

Status: Phase 1 is implemented. The portable manifest validation/replay and desktop image-preview portions of Phase 2, plus explicit-region visual-feature/sensor-fusion portions of Phase 3, are implemented. Real detection, classification, persistent result storage, real camera/collection adapters, training, and hardware adapters remain proposed.

## Modules and contracts

| Module | Input and output | Boundary |
| --- | --- | --- |
| Configuration | Files → validated settings | Reject unset required hardware/model values for the requested operation |
| Acquisition adapters | Scan request → image and matched readings | Replay/mock on Mac; real devices on Pi; timestamp and identify every acquisition |
| Detection adapter | Image → bundle bounding box and score | Local model; distinguish no detection from runtime failure |
| Feature extractor | Detected region → ordered visual feature values | OpenCV; color and texture; identical code during training and inference |
| Feature fusion | Visual values + gas + grams → versioned feature vector | Enforce order, units, validity, and timing compatibility |
| Classification adapter | Feature vector → Stage and spoilage labels | Random Forest; dual-output estimator design remains pending |
| Orchestrator | Start/cancel → scan outcome | Own state, prevent concurrent scans, handle cleanup |
| Presentation adapters | Outcome → console/display/indicators | Console in development; exact device/output patterns pending |
| Storage | Acquisition/outcome → local records | Retain provenance, timings, schema and model versions; configurable image retention |
| Training/evaluation utilities | Real manifests and artifacts → models/reports | Separate from runtime; enforce group isolation |

### Phase 1 implemented boundary

`banana_system.config` validates the development TOML before a scan begins. `banana_system.acquisition` provides only the explicit `SyntheticFixtureAcquisition`; it is not selected in hardware mode. `banana_system.orchestrator` serializes scans, accepts a cancellation token, releases the selected acquisition adapter in a `finally` block, and presents every terminal outcome. It currently gates the workflow on a local model artifact: absent artifacts return `unavailable`; no detector, feature extraction, or classifier is fabricated. `banana_system.presentation` is console-only. The contracts retain UTC timestamps, stable generated scan/acquisition IDs, mode, and provenance.

### Portable Phase 2 boundary

`banana_system.collection` reads a CSV manifest and validates it without mutating the manifest, image, or raw sensor-trace inputs. It resolves only relative paths under an explicit dataset root, validates UTC timestamps and sensor values, and retains each valid row's original string values. Collection validity and supervised-training suitability are separate results: labels may be blank during collection, while synthetic provenance, incomplete labels, missing raw trace, label provenance, or calibration provenance block training suitability. Replay returns validated records for console inspection only and has no detection or prediction dependency.

`banana_system.desktop` is an independent Tk desktop presentation path. It loads a user-selected local photograph with OpenCV without copying or modifying it, renders a scaled preview, and shows camera/sensor/model availability plus image/capture locations. `banana_system.camera` defines a narrow camera adapter and explicit unavailable adapter. It does not import Pi libraries or provide a mock capture. The Capture control is disabled when the selected adapter reports unavailable; no capture writes or measurement/prediction code runs in that state.

### Portable Phase 3 boundary

`banana_system.detection` defines a local `BananaDetector` interface, `Detection`, and `BananaRegion`; no implementation, artifact loader, confidence convention, or fallback detector is supplied. `banana_system.features` validates a supplied `uint8` BGR image and an in-bounds region, then extracts the ordered `visual-v1` vector using OpenCV. It neither selects a region nor calls a detector. The feature extractor is a standalone function intended to be called unchanged by later training and inference code. The feature schema version must be validated against a future model artifact before prediction.

`banana_system.fusion` combines a `VisualObservation` and `MatchedSensorMeasurements` only when their acquisition ID, bundle ID, and synthetic/real provenance agree. It emits an ordered `multimodal-v1` vector, preserving the supplied gas-response unit and requiring mass in grams rather than converting it. Acquisition identity, timestamps, provenance, hardware configuration ID, and calibration ID stay as metadata rather than predictive features. No capture-to-sensor timing tolerance is imposed. Synthetic vectors carry a `synthetic_provenance` training-ineligibility reason; no fused output is a prediction.

Use `src/banana_system/` for the application package. Add subpackages when their implementation begins; avoid empty abstractions for every possible future device.

## Runtime workflow

The proposed classification state sequence is INITIALIZING, READY, ACQUIRING, DETECTING, EXTRACTING, CLASSIFYING, PRESENTING, then READY. Cancellation or an error exits through cleanup. A recovery returns to READY only after required dependencies pass checks; persistent device/model errors remain visible.

Keep dataset collection available as a separate operation without a trained detector or classifier. “Ready to collect” and “ready to classify” are distinct capabilities. Collection must not manufacture predictions.

In development, replayed inputs and fixture adapters exercise the same orchestration boundaries. Synthetic outcomes, if later added for tests, remain visibly synthetic. Hardware mode selects real adapters explicitly and cannot substitute synthetic readings.

## Outcome design

Proposed outcome statuses: `ok`, `no_bundle`, `invalid_input`, `unavailable`, `cancelled`, `error`. Store `scan_id`, mode, synthetic/real provenance, timestamps, stage timings, model IDs, feature schema version, and error code as applicable. Only a successful classifier invocation can set ripeness/spoilage predictions. Ground-truth labels belong to collection/evaluation data and must never be substituted for predictions.

A detected region is a bounding-box crop, not automatically a pixel mask. Background removal, feature choices, and treatment of multiple detected bundles must be selected and documented before production extraction. The proposed initial multiple-bundle behavior is to reject the scan and request one bundle.

## Artifact contract

Each trained artifact needs an immutable ID, checksum, source dataset version, training configuration, software versions, class mapping, ordered feature names/units, preprocessing version, and split manifest. Choose detector serialization/runtime only after checking the actual Roboflow model and Pi compatibility. Do not assume every Roboflow model supports the same export path.

Offline acceptance includes a restart and real scan with networking disabled after artifacts are installed. A cached inference package is a possible route, not proof that any selected model/runtime works offline on the Pi.
