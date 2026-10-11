# Decisions and unresolved details

Update this file when the user or team supplies evidence. Record the date, decision, source, and affected docs/configuration. A proposal is not a confirmed hardware fact.

## Confirmed baseline

| Decision | Source |
| --- | --- |
| Cavendish bundles; Stage 1–7 plus Good/Spoiled | Proposal Objectives and sections 3.4.1–3.4.2 |
| Roboflow-trained detection, OpenCV features, Scikit-learn Random Forest | Proposal sections 3.2 and 3.4 |
| Raspberry Pi 4 local offline inference, no external accelerator | Proposal section 3.2 |
| Team handles physical hardware and images; developer works remotely on code | User clarification in this conversation |
| 95% is a proposed target | Proposal sections 3.4.5 and Scope and Limitations |

## Proposed software defaults

Python `src` package, console-first development, replay/mock adapters, explicit mode selection, UTC timestamps, CSV collection manifest, configurable local logging, one bundle per scan, BCM software numbering, and rejection of ambiguous multiple-bundle scans. These are reversible recommendations. Exact versions, feature algorithms, timings, thresholds, and pins remain open.

## Phase 1 implementation decisions (2026-10-09)

| Decision | Rationale and affected scope |
| --- | --- |
| Support Python `>=3.11,<3.15` for the portable foundation. | Enables standard-library TOML parsing and modern typed contracts. This is a development choice, not confirmation of the Pi runtime; D01 remains open. |
| Keep Phase 1 runtime dependency-free; use pytest only for development tests. | No OpenCV, Scikit-learn, Pi camera, GPIO, or sensor package is needed before their implementation phases. |
| Development configuration accepts only explicit `mode = "development"`, `input_provenance = "synthetic"`, and console presentation. | Prevents accidental claims that fixture data is real and prevents hardware mode from silently using a mock adapter. |
| A synthetic fixture uses a `synthetic://` image reference and `synthetic_adc_counts` gas-response unit. | These are software fixtures only, not calibration values, chemical concentrations, sensor observations, or research evidence. |
| Missing/unimplemented model artifacts return `unavailable` with no ripeness/spoilage fields. | Preserves the outcome contract until detector, feature extraction, schema validation, and Random Forest classification are implemented in later phases. |

## Newly visible blockers

Phase 1 confirms that model availability alone is insufficient for prediction. Phase 3 still needs D07 to select a local detector/runtime and define a versioned visual-feature schema; Phase 4 still needs D05 and D06 for labels and matched data, and must define the Random Forest artifact/schema contract. No additional hardware-specific values were selected.

## Portable Phase 2 decisions (2026-10-09)

| Decision | Rationale and affected scope |
| --- | --- |
| Validate manifests without modifying, copying, or interpreting image and raw-trace inputs. | Preserves source evidence and keeps collection validation distinct from later preprocessing. |
| Require manifest paths to be relative, existing files underneath an explicit dataset root. | Prevents accidental path escape and catches incomplete handoffs without imposing an image format conversion. |
| Treat blank labels as collection-valid but supervised-training-ineligible. | Supports collection before team label review without manufacturing labels. |
| Reject invalid nonblank stages outside 1–7 and statuses outside Good/Spoiled. | Enforces the documented label vocabulary only; it does not define a stage rubric or equate Stage 7 with Spoiled. |
| Mark synthetic records permanently unsuitable for supervised research training. | Makes fixture provenance explicit and prevents synthetic data from being confused with experimental evidence. |

## Phase 2 unresolved dependencies

The validator intentionally does not set an acquisition timing tolerance, gas-response unit vocabulary, trace aggregation rule, calibration acceptance threshold, or labeling rubric; D03–D05 remain the authority for those decisions. D01–D04 also still block real camera/sensor/button adapters and component diagnostics. The current fixture is a portable software test only.

## Portable Phase 3 decisions (2026-10-09)

| Decision | Rationale and affected scope |
| --- | --- |
| Add `opencv-python-headless` and require a `uint8` BGR image at the feature boundary. | Matches OpenCV's standard in-memory convention while avoiding GUI requirements in development. Pi packaging remains unverified. |
| Define `BananaDetector` as an interface that returns regions only, without a universal confidence field. | A score convention must come from the confirmed detector artifact/runtime; no synthetic detection or confidence is emitted. |
| Use explicit caller-provided in-bounds `x,y,width,height` regions for `visual-v1`. | Keeps detection separate from feature extraction and avoids fabricating crops before a real detector exists. |
| Start `visual-v1` with five normalized HSV/grayscale/Laplacian summary values. | Provides a small deterministic baseline that is easy to version and reuse. It is not a validated feature-selection result and must be re-evaluated on real grouped data. |

## Phase 3 unresolved dependencies

D07 still blocks detector selection, serialization, artifact loading, local runtime compatibility, class handling, confidence convention, and real region validation. D05–D06 still block feature selection/evaluation against approved labels and matched observations. The team must also establish whether lighting/color correction or a crop/mask policy is required before research use. No feature values from synthetic fixtures are experimental results.

## Portable Phase 3 fusion decisions (2026-10-10)

| Decision | Rationale and affected scope |
| --- | --- |
| Create `multimodal-v1` as `visual-v1` values followed by raw gas response and mass in grams. | Gives future training and inference one explicit order without mixing identifiers or provenance into predictive features. |
| Preserve the supplied gas-response unit as vector metadata and require `weight_unit = "g"`. | The team has not supplied a gas calibration/unit conversion or a general unit-conversion policy. Fusion must reject incompatible mass units rather than silently transform them. |
| Require matching acquisition/bundle IDs and provenance, but do not compare capture time against the sensor window beyond timestamp validity. | Identity matching is available now; timing tolerance and sensor aggregation are protocol-dependent and remain open. |
| Require hardware/calibration IDs for real sensor inputs, while allowing their absence for explicitly synthetic fixtures. | Synthetic development data must remain runnable and visibly ineligible for training; it cannot imply a physical calibration. |

## Fusion unresolved dependencies

D03–D05 remain necessary to choose the approved gas-response unit/aggregation, calibration record requirements, sensor-window alignment/tolerance, weight workflow, and label protocol. D06 is necessary to evaluate whether `visual-v1`/`multimodal-v1` are suitable on real grouped data. A future model artifact must record and validate the exact gas unit, feature names/order, and schema versions before prediction.

## Desktop camera decisions (2026-10-12)

| Decision | Rationale and affected scope |
| --- | --- |
| Use a small Tk desktop screen with OpenCV decoding for image preview. | Supports local image development without adding a GUI framework or mixing presentation with camera/feature logic. |
| Keep the camera behind `CameraAdapter` and select only an explicit unavailable adapter today. | No confirmed Pi OS/camera model, working command, or team code exists in this repository. This prevents a fabricated camera integration or mock image capture. |
| Show Capture but disable it while the camera adapter is unavailable. | Makes the intended workflow visible while accurately communicating the dependency; opening an existing photograph remains usable independently. |
| Use timestamped `.jpg` destinations inside an ignored `captures/` directory for future capture adapters. | Avoids overwriting earlier captures. The current unavailable adapter creates no image. |
| Install the matching Homebrew `python-tk@3.14` binding for the active Python 3.14 interpreter. | Resolves the missing `_tkinter` module without changing the project's supported Python range or Python package dependencies. |

## Desktop camera blocker

D01 remains unresolved. The team must provide the actual Pi camera evidence and working code/command before a hardware adapter can be selected, implemented, or verified. The current UI's unavailable state is intentional and must not be interpreted as camera support.

## Team questions and dependent work

| ID | Missing answer | Owner | Blocks |
| --- | --- | --- | --- |
| D01 | Pi RAM, OS/version/architecture, camera model, Python | Team | Device dependency selection and camera driver |
| D02 | Verified circuit, numbering and GPIO/interface assignments | Team | Real GPIO adapters and output activation |
| D03 | MQ-135 module, ADC/interface, electrical compatibility | Team | Continuous gas acquisition |
| D04 | HX711/load-cell details and calibration; MQ acquisition/reset protocol | Team | Valid measured inputs and final fusion rules |
| D05 | Stage/spoilage rubrics and mixed-bundle labeling | Team | Supervised dataset acceptance and research evaluation |
| D06 | Matching sensor dataset availability/access and independent bundle counts | Team | Random Forest training and held-out performance |
| D07 | Roboflow project/version, training owner and local deployment format | Team + developer | Real detector adapter |
| D08 | Display type and contents; LED/buzzer meanings and timing | Team | Physical presentation adapters |
| D09 | Deadline, remote testing contact/access, final deliverables | Team + developer | Scheduling and full acceptance agreement |
| D10 | Whether 95% applies to each output, combined success, or another metric | Team | Formal performance acceptance |

## Developer decisions before relevant phases

Select the supported Python range and packaging in Phase 1. Select exact feature methods and detector runtime in Phase 3. Decide whether to use one multi-output Random Forest or two Random Forest estimators behind the same classification interface in Phase 4, and document the rationale. The paper specifies two outputs, not that estimator detail.

Before release, settle model licensing, artifact/dataset storage and access, code ownership, source-code license, retention rules, and measured resource requirements. These do not block the portable foundation.
