# Repository instructions

Build a small local Python application for the Cavendish banana research prototype. Read [README.md](README.md) first; read [docs/HARDWARE.md](docs/HARDWARE.md) for device work and [docs/DATASET.md](docs/DATASET.md) for data, features, models, or evaluation work.

## Engineering rules

- Use Python, OpenCV, and Scikit-learn Random Forest for the documented pipeline. Keep bundle detection separate from ripeness/spoilage classification.
- Production inference is local on Raspberry Pi 4. Do not add cloud inference, a web backend, authentication, containers, or external accelerators unless explicitly requested.
- Keep acquisition, detection, feature extraction, fusion, classification, presentation, and storage behind narrow interfaces. Training and runtime use the same versioned extractor.
- Development must run without GPIO, Picamera2, camera hardware, sensors, models, or real data. Hardware imports and initialization belong only in selected hardware adapters.
- Reuse existing modules and contracts. Do not add generic abstractions or dependencies without a concrete need.

## Research and hardware integrity

- Never invent pins, ADCs, camera models, calibration constants, timings, label rubrics, model formats, measurements, or performance results. Record newly discovered blockers in the relevant retained documentation.
- Fixtures and mock values must be visibly synthetic. Missing/invalid inputs or models must return explicit unavailable/error outcomes, never plausible labels or defaults.
- MQ-135 data is gas response until the team supplies a verified calibration; do not call it ethylene. Weight is mass, not firmness or weight loss.
- Stage 7 is not automatically Spoiled. Labels and mixed-bundle rules come from the team.
- Keep physical bundle identities together across views and time during all train/validation/test splitting. Never present synthetic data as research evidence.

## Validation and documentation

- Validate units, UTC timestamps, IDs, provenance, schemas, and model compatibility at boundaries. Hardware mode must never fall back to mocks.
- Preserve raw images/traces and keep datasets, models, credentials, logs, captures, and machine-specific configuration out of Git.
- Run relevant checks after changes, normally `.venv/bin/python -m pytest`. State what ran and distinguish Mac checks from Pi/device and research validation.
- Update README, HARDWARE, or DATASET documentation when behavior, contracts, decisions, or dependencies change.
- Whenever implementation changes capabilities, dependencies, commands, or setup, update the relevant existing documentation in the same change; keep it brief and do not create additional Markdown files.
