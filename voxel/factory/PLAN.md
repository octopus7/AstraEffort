# Factory voxel implementation plan

**Goal:** Four independent, detailed industrial voxel assets at 128-cell and 64-cell longest-axis resolutions, with the same physical dimensions.

**Architecture:** `build.py` authors colored integer grids through the parent-owned `voxelkit` API. The grid is authoritative. The common exporter creates native VOX, surface-only BLEND/GLB/FBX and matching-camera previews; independent tools reparse VOX and freshly import exports.

**Spec:** `../BRIEF.md`, `../_tools/API.md`, and the assigned factory reference.

**Execution:** The user has already authorized direct production. The parent specifically assigned geometry authoring before tools are ready, then builds and independent validation. No Git, installations, subagents, shared Blender session, or cross-theme reads.

## Design decisions

- Shared restrained palette: mustard enamel, slate blue structure, warm ivory access panels, graphite rubber and dark steel mechanics.
- Production machine: rounded press crown, open work throat, exposed ram, die bed, side guards, right control pedestal and rear hydraulic service details.
- Conveyor: actual loop belt and two end rollers, four supported legs, drive motor, two industrial crates.
- Forklift: two long separate forks, paired mast rails, four tires, open cab, seat/steering wheel, rear counterweight and useful service panel.
- Generator: rounded cabinet, two skid rails and forklift pockets, louvered end grilles, access doors, rear cable/service panel, bent exhaust and lifting eyes.
- Minimum important mechanical thickness is four large-grid cells. Small bolts/slats may simplify at half resolution; functional gaps must remain readable.

## Work sequence

- [x] Read brief/API and visually inspect only the factory reference.
- [x] Author `build.py` and `STATUS.json` with actual start time.
- [x] Wait for common tools-ready notification, then build through isolated Blender CLI using four threads.
- [x] Inspect all eight actual preview images. Correct material, silhouette, or topology defects in voxel geometry as needed.
- [x] Run parent-owned native VOX verification and fresh GLB/FBX import verification.
- [x] Record actual counts, timestamps, timings, validation and limitations in `RESULT.md` and `STATUS.json`; submit and freeze factory files.

## Verification focus

Grid dtype/indexing; dimensions and two-to-one resolution; repeated occupancy/palette after VOX parse; no duplicate/out-of-grid cells; exposed-surface mesh only; valid outward normals/materials; finite nonzero faces; fresh export bounds and triangle counts; absence of studio objects in exports; readable machine throat, fork separation, cab, belt rollers and grilles at both resolutions.

## Ledger

- 2026-10-23T14:05:47Z: Actual factory work started; reference read and viewed.
- Ruling: parent/user sequencing overrides generic approval, worktree, commit and test-first workflow. Geometry is authored now through the documented stable API; meaningful artifact/geometry validation follows tool availability. Scope remains exclusively `voxel/factory`.

- 2026-10-23T14:26:59.341220+00:00: All eight variants, required formats and rendered evidence verified; RESULT/STATUS finalized for parent review. Files frozen on submission.
