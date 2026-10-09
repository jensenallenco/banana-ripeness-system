# Project scope and evidence

## Evidence and authority

The attached proposal, `Electives-Chap-1-3-TriCore-Systems (2).docx`, is the research source. Its project title is “AI and Sensor-Based Cavendish Banana Ripeness and Spoilage Detection System.” The implementation brief below derives from Objectives, Scope and Limitations, and sections 3.2–3.6; it is not a replacement for the proposal. The original document is not bundled into this software starter.

The user confirmed that the research team handles hardware and photographs, while the user handles code and likely software integration remotely. Dataset access is expected later, not verified as available now.

Later explicit user instructions and confirmed team decisions guide implementation. Record deviations from the research design in `DECISIONS.md` instead of silently changing the methodology. Proposed defaults in these docs are engineering recommendations, not claims that the paper specified them.

## Objective mapping

| Research objective | Software responsibility | Dependency and evidence of completion |
| --- | --- | --- |
| Locate banana bundles using a camera and Roboflow-trained detector | Capture/replay images, load local detector, return bundle region | Trained local model; annotated held-out detection evaluation |
| Classify seven ripeness stages and possible spoilage from image, gas, and weight features using Random Forest | Feature extraction, matched-data pipeline, training and classification | Team-approved labels and synchronized real measurements; separate metrics for both outputs |
| Deploy and evaluate locally on Raspberry Pi 4 | Hardware adapters, scan orchestration, result display, local storage and evaluation | Actual device tests, offline restart/scan, latency and functional records |

## Included

- Cavendish bundles as the classification unit; one bundle per scan is the proposed initial workflow.
- Camera, MQ-135, load cell/HX711, start button, LCD/monitor, LED, buzzer, controlled lighting.
- Stage 1–7 plus independent Good/Spoiled output from supervised classification.
- Mac development with synthetic fixtures and recorded-image replay.
- Research data collection support, local model inference, optional image/result retention, and measured evaluation.

## Outside the current scope

Other fruits/varieties, individual grading of every banana in a bundle, food-safety certification, a direct ethylene measurement claim, mechanical firmness sensing, automatic sorting equipment, cloud inference, a public web service, or a guaranteed accuracy result.

## Responsibilities

| Work | Owner |
| --- | --- |
| Purchase, wiring, chamber, lighting, electrical checks | Research team |
| Images, synchronized gas/weight collection, sample identity | Research team |
| Label definitions, label verification, experimental protocol | Research team |
| Roboflow annotations | Research team; confirm handoff |
| Roboflow detector training and export | Pending agreement |
| Python application and software integration | Remote developer |
| Random Forest training/evaluation code | Remote developer, once data and scope are confirmed |
| Device execution and physical acceptance testing | Research team, assisted remotely by developer |
| Research conclusions and submitted performance claims | Research team |

## Completion boundary

A successful mock run proves software behavior. A successful device run proves that integration works for that run. Research performance requires held-out real bundles and the agreed labeling protocol. Report these separately. The proposal explicitly treats 95% as a target to be measured, not a guaranteed result.
