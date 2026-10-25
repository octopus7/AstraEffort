# Service mech implementation plan

**Goal:** Deliver the approved 2.8 m rounded maintenance mech from the supplied reference.

**Architecture:** A deterministic Blender Python build creates individually named mechanical components in `ASSET`; cameras, lights, and floor remain in `STUDIO`. Real beveled geometry and solid PBR materials support editable source and self-contained geometry exports.

**Tech stack:** Blender 4.5.12 LTS, Python, Cycles CPU with four threads.

**Spec:** `TASK.md`; visual reference `D:/github/AstraEffort/REF/Set01/service_mech.png`, directly inspected 2026-10-23.

## Constraints and review focus

- Write only this directory; private CLI, no shared scene or Git mutations.
- Front negative Y, Z up, meters, ground at Z=0, approximately 2.8 m high.
- Keep the oval ivory chest, dark recessed sensor, substantial sage shoulder rotors, mechanical joints, broad feet, gripper, rotary tool, and rear cooling/power pack recognizable.
- Check silhouette and functional connections in actual front/side and rear renders.
- Check finite nonempty geometry, useful mesh separation, UV/material coverage, applied exported modifiers, missing external paths, dimensions, and evaluated triangles.
- Reopen the saved blend and independently import both exports. Exclude every studio object from exports.

## Execution

- [x] Build all geometry, materials, studio, exports, and initial actual renders using `build.py`.
- [x] Inspect both actual render images and correct visible issues.
- [x] Reopen `.blend`, import `.glb` and `.fbx` in a new private process, and save `validation.json`.
- [x] Record actual timing, commands, evidence, and limitations in `RESULT.md`.

The parent supplied the approved design and direct execution method. No additional design approval or delegation is needed. Commits are excluded by the assignment.
