# Implementation roadmap

Phases 0 and 1 are complete. The portable manifest/replay and desktop image-preview portions of Phase 2, plus explicit-region visual-feature/sensor-fusion portions of Phase 3, are complete; hardware- and model-dependent work remains planned.

## Phase 0 — Repository brief

Completed: scope, responsibilities, architecture boundaries, pending decisions, collection template, configuration examples, and first-task prompt. Git initialization is local only; no remote repository is created.

## Phase 1 — Portable software foundation

Build the Python package, configuration validation, acquisition/outcome contracts, console presentation, fixture adapters, and basic scan orchestration. Provide a documented CLI development workflow and meaningful tests. Missing model support produces an explicit unavailable outcome; do not fabricate detection or classification.

Complete when the Mac development path works without Pi dependencies, preserves synthetic provenance, handles cancellation/errors/repeated start, and reports actual verification. This phase does not require the team's physical hardware or real dataset.

Completed 2026-10-09: added the Python `src` package and project metadata; validated development configuration; typed acquisition, outcome, and adapter contracts; synthetic-only fixture acquisition; console presentation; scan serialization, cancellation, error handling, and cleanup; documented CLI workflow; and contract tests. The development CLI returns an explicit `unavailable` outcome with no predictions when model artifacts are absent. Hardware mode remains rejected/unimplemented and has no mock fallback. Verification is recorded in the implementation report; no Pi or research-data validation has occurred.

## Phase 2 — Collection and hardware acquisition

Implement the manifest validator and collection workflow; add real acquisition/button adapters as each interface is confirmed. Collection does not depend on trained models. Provide component diagnostics and configurable calibration handling.

Complete when the team demonstrates matched real images/readings with valid identities, units, timing and calibration provenance, and invalid acquisition is recorded without predictions. Hardware specifics block only their dependent adapters.

Portable portion completed 2026-10-09: added a non-mutating CSV manifest validator, synthetic manifest/image/trace fixture, and model-free validation/replay CLI. It validates identifiers, relative existing input paths, UTC timestamps, finite sensor values, units, labels, and explicit provenance; it permits blank labels for collection and reports records unsuitable for supervised training. The synthetic replay prints `predictions=none`. This does not complete Phase 2: real collection adapters, component diagnostics, confirmed calibration handling, and team demonstration of matched real observations remain blocked by D01–D05 and real hardware/data handoff.

Desktop preview slice completed 2026-10-12: added a Tk image-preview screen with Open photograph, Capture, camera/model/sensor availability states, and source/capture locations. Development images load without copying or analysis; capture has no sensor or model dependency. The repository has no confirmed Pi camera setup or supplied working camera code, so Capture is explicitly disabled rather than simulated. This does not complete Phase 2: a real camera adapter, real capture verification, component diagnostics, confirmed calibration handling, and team demonstration of matched real observations remain blocked by D01–D05.

## Phase 3 — Local detection and visual features

Integrate the trained detector after format/runtime selection. Implement and version the color/texture feature extractor and fusion rules. Validate detection/crops and document multi-bundle/no-bundle handling.

Complete when a supplied model executes locally, visual extraction is repeatable, and training/runtime share the same ordered feature schema. Benchmark on Pi before selecting a deployment runtime as final.

Portable visual slice completed 2026-10-09: added the detector interface (without a detector implementation), validated explicit banana-region contract, and OpenCV `visual-v1` extraction with an ordered, documented color/texture schema. Synthetic-image tests verify deterministic region-only behavior and invalid-input rejection. The CLI can display the schema and extract values from a caller-provided region while reporting `detection=not_run predictions=none`.

Portable fusion slice completed 2026-10-10: added `multimodal-v1` fusion with fixed visual/gas/weight ordering, strict acquisition/provenance matching, explicit gas/weight units, finite-value checks, and separate metadata. The synthetic CLI demonstration remains training-ineligible and prints `predictions=none`. This does not complete Phase 3: a trained detector artifact/runtime, real detection/crop validation, feature evaluation on real data, protocol-confirmed sensor alignment/calibration rules, and Pi benchmarks remain blocked by D03–D07 and hardware/data handoff.

## Phase 4 — Supervised training and evaluation

Receive approved labels and matched real data. Establish group splits, choose the dual-output Random Forest design, implement training/export and held-out evaluation, and record artifacts/parameters/metrics.

Complete when both outputs have honest, reproducible evaluation with no cross-group leakage and no synthetic data presented as research evidence. If data is insufficient, document that result instead of claiming target performance.

## Phase 5 — Integrated Pi prototype

Add confirmed display/LED/buzzer behavior, classification workflow, logging/retention, offline startup, and end-to-end device verification. Add optional boot service only after manual validation.

Complete when the team supplies actual hardware evidence, offline restart/scan works, resource cleanup and recovery are demonstrated, and the release records the source commit, configuration, calibration, models, and limitations.
