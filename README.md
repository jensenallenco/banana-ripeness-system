# Cavendish Banana Ripeness and Spoilage System

Portable Phase 1 foundation plus the portable portion of Phase 2 for the Raspberry Pi research prototype. It includes a typed Python scan workflow, validated development configuration, explicit synthetic fixtures, console presentation, a non-mutating dataset-manifest validator/replay workflow, and contract tests. It does **not** contain trained models, detector/classifier inference, or validated hardware drivers.

The research workflow is camera capture → banana-bundle detection using a Roboflow-trained model → OpenCV color and texture features → fusion with MQ-135 gas response and load-cell weight → Scikit-learn Random Forest → Stage 1–7 and Good/Spoiled outputs. Inference must run locally on a Raspberry Pi 4.

## Start here

1. Open this folder as the repository root in Codex.
2. Read [AGENTS.md](AGENTS.md) and [docs/PROJECT.md](docs/PROJECT.md).
3. Create a virtual environment and install the development package:

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install --upgrade pip
   .venv/bin/python -m pip install -e '.[dev]'
   ```

4. Run the portable development scan:

   ```sh
   .venv/bin/banana-system scan --config config/development.example.toml
   ```

   The command exits successfully with `status: unavailable` because no model artifacts are supplied. It prints `provenance: synthetic` and a notice that the fixture is not a research result; it never emits a ripeness stage or spoilage label.

5. Validate and replay the synthetic collection fixture. These commands never invoke a model or produce predictions:

   ```sh
   .venv/bin/banana-system collection validate --manifest data/fixtures/synthetic/observations.csv
   .venv/bin/banana-system collection replay --manifest data/fixtures/synthetic/observations.csv
   ```

   The fixture's blank labels are valid during collection, but it is reported as unsuitable for supervised training because it is synthetic and lacks real calibration provenance.

6. Run the contracts:

   ```sh
   .venv/bin/python -m pytest
   ```

7. Ask the research team for the items in [docs/HARDWARE.md](docs/HARDWARE.md) and [docs/DECISIONS.md](docs/DECISIONS.md) while independent software work proceeds.

## Repository guide

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Instructions Codex reads when working in this repository |
| `docs/PROJECT.md` | Objectives, scope, responsibilities, and evidence |
| `docs/ARCHITECTURE.md` | Module boundaries and scan behavior |
| `docs/DATASET.md` | Matched images, sensor readings, labeling, and splits |
| `docs/HARDWARE.md` | Hardware handoff and configuration requirements |
| `docs/DEVELOPMENT.md` | Mac development and Raspberry Pi deployment approach |
| `docs/TESTING.md` | Software, device, and research evaluation criteria |
| `docs/ROADMAP.md` | Phases and concrete completion criteria |
| `docs/DECISIONS.md` | Confirmed choices, proposed defaults, and open questions |
| `config/` | Non-operational configuration examples |
| `data/templates/` | Header-only collection template; no experimental data |
| `data/fixtures/synthetic/` | Explicit synthetic manifest, image, and trace for development validation/replay |
| `src/banana_system/` | Portable Python package and development adapters |
| `tests/`, `scripts/` | Contract tests and future training/evaluation utilities |
| `models/` | Artifact metadata guidance; model weights stay outside Git |

## Ownership

The research team supplies and assembles hardware, collects images and synchronized measurements, establishes labels, and performs device testing. The remote developer handles application code and software integration, with Random Forest training dependent on receiving usable labeled data. Roboflow detector training ownership still needs confirmation.

The paper's 95% accuracy is a research target. This starter makes no accuracy claim.

## Phase 1 boundary

The development adapter is deliberately the only runnable adapter. It provides one synthetic image reference and synthetic gas-response/weight fixture values, all marked with synthetic provenance. Hardware configuration is rejected rather than falling back to these fixtures. A missing local model produces an explicit `unavailable` outcome, not an invented detection, Stage, or Good/Spoiled result.

## Portable collection boundary

`collection validate` checks manifest identity fields, relative input paths, UTC timestamps, finite sensor values, units, labels, and provenance without modifying or copying source inputs. Blank labels are permitted for collection. The report separates collection validity from supervised-training suitability; synthetic, incomplete, or provenance-incomplete records are never presented as training-ready. `collection replay` only lists validated source records and states `predictions=none`.

No remote Git host has been configured. The ZIP is a portable starter; initialize Git after extraction if necessary. No software license has been selected; confirm ownership and sharing terms before public release.
