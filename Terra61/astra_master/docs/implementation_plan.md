# Steam Station Implementation Plan

> For agentic workers: use the prescribed three-worker parallel asset workflow. User explicitly requested execution and roles; no further approval gate.

**Goal:** deliver a textured modular steam-era station with individual GLBs and an assembled scene.

**Architecture:** independent workers own separate module directories. Shared minimal geometry/GLB utilities are maintained by the main agent. References and generated textures come from the main agent; workers model, unwrap, validate and report. Main assembles, visually reviews and packages.

**Tech stack:** Python, NumPy, Pillow, glTF 2.0, local WebGL renderer.

**Spec:** docs/design.md

## Global constraints
- Exactly three workers, model gpt-6.1-terra, reasoning_effort max.
- Main creates images, assigns tasks, reviews and assembles.
- Texture-based detail takes priority over increased face counts.
- Meter scale, Z-up authoring; export Y-up with a single root transform.
- Every material-bearing mesh has valid UVs and embedded texture references.
- Every module gets a reusable standalone GLB and machine-readable metadata.
- No worker edits another worker's files. No nested agents.

## Review focus
- Correct asset orientation and platform/rail/vehicle heights.
- UV coverage and texture registration, no accidental repeated whole atlas on each face.
- Mesh is visible from planned camera; bounds and normals finite.
- Export buffers/accessors/embedded images match declared sizes and valid indices.
- GLB/preview assets load from local files without a remote CDN requirement.

## Tasks
- [x] Main: generate separate architecture, shed and infrastructure references; prepare shared atlas and geometry I/O contract.
- [x] Worker 1: architecture module family, glTF and geometry metadata; report bounds, triangle counts and texture usage.
- [x] Worker 2: steel/glass shed repeat bay and canopy components; same checks.
- [x] Worker 3: platform/track repeat kit; same checks.
- [x] Main: generate individual train and furnishings references and texture atlases while workers model.
- [x] Assign locomotive, carriage and furnishing tasks to available workers; validate reusable exports.
- [x] Main: assemble station, save scene GLB and local viewer, produce actual mesh renders and validate all21GLBs. Final archive delivery follows.
