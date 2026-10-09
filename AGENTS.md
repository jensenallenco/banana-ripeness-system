# Codex repository instructions

## Context and reading order

Build the software for the Cavendish banana research prototype described in `docs/PROJECT.md`. The developer works remotely on a Mac; the research team owns physical hardware and experimental data collection.

Before the first implementation task, read `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, and `docs/ROADMAP.md`. Read `docs/DATASET.md` for data/ML changes, `docs/HARDWARE.md` for device changes, and `docs/TESTING.md` for validation. Read `docs/DEVELOPMENT.md` before environment changes.

User instructions take precedence. Preserve the latest user-authorized scope and incorporate confirmed team answers into the relevant docs.

## Architecture constraints

- Use Python, OpenCV, and Scikit-learn Random Forest for the documented multimodal classification pipeline. Roboflow supplies the detector preparation/training workflow; its exported or cached model executes locally.
- Keep detection and ripeness/spoilage classification separate. Do not replace the Random Forest with a CNN or turn the detector into a ripeness classifier without an explicit scope change.
- Production inference runs on Raspberry Pi 4 without a cloud API, external accelerator, or remote inference computer. Training and artifact preparation may happen elsewhere.
- Provide separate development and hardware adapters. Development mode must work without GPIO, Picamera2, a camera, or the physical sensors.
- Keep hardware imports and initialization inside selected hardware adapters, away from package imports and the application core.
- Keep acquisition, detection, feature extraction, classification, presentation, and storage behind narrow interfaces. Training and runtime share the same versioned feature extractor.
- Prefer a small local application. Do not add a web backend, cloud database, authentication system, or container stack unless the task requires it.

## Unknowns and research integrity

- Never invent GPIO pins, ADC models, camera models, sensor calibration constants, stage definitions, model formats, or experimental results. Record unresolved dependencies in `docs/DECISIONS.md` and keep their adapters unconfigured.
- Proceed with independent software work when hardware or data is missing. Only the dependent component remains blocked. Routine, reversible software defaults may be selected and documented without asking for repeated permission.
- Fixtures and mock sensor values must be marked synthetic. A fixture prediction is never a research result or model accuracy measurement.
- Missing, stale, non-finite, or invalid inputs must not become plausible defaults. Missing models must not produce a fabricated Stage or Good/Spoiled label. Return an explicit unavailable/error outcome.
- Treat MQ-135 output as gas response unless the team supplies a verified calibration and unit conversion. Do not claim it directly identifies ethylene or confirms spoilage. Weight is mass, not firmness; a single weight is not weight loss.
- Do not equate Stage 7 with Spoiled. The team establishes independent labels and mixed-bundle rules.
- Split by physical bundle identity, including its repeated views and observations over time. Keep test groups out of detector training, feature selection, and classifier tuning. Do not report 95% as achieved without held-out evaluation.

## Implementation and validation

- Implement only the current requested phase. Keep unfinished functionality visible rather than pretending it is complete.
- Validate configuration and feature/model schema compatibility before hardware activation or prediction. Hardware mode must never silently fall back to mocks.
- Use explicit units, UTC timestamps with timezone information, and stable sample/bundle identifiers. Persist mode and data provenance.
- Avoid overlapping scans; release device resources and reset outputs on cancellation or failure. Exact timing and output patterns stay configurable and pending team confirmation.
- Keep large datasets, trained models, credentials, logs, and machine-specific configuration out of Git. Preserve raw data and record derivation/version metadata.
- Test meaningful contracts and failure paths. Run the relevant checks after changes; report what actually ran and distinguish Mac verification from on-device verification.
- Update docs when contracts or decisions change. Keep `docs/ROADMAP.md` status accurate. Finish task reports with implemented behavior, verification, and remaining dependencies, using concise wording.
