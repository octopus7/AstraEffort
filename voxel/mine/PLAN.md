# Mine voxel production plan

**Goal:** Four independent original mine assets, each in native large/half voxel grids and VOX/BLEND/GLB/FBX with actual matching-camera previews.

**Spec and interface:** Parent assignment, `../BRIEF.md`, and `../_tools/API.md`. Large grids use even dimensions with longest axis 128; each half dimension is exactly divided by two and meters per voxel double. Conservative occupied-bound expansion of at most one large cell is allowed.

**Design:** Restrained olive, cream and charcoal with copper-orange functional accents. Rounded stepped silhouettes and mechanically readable details. Excavator has two track loops and an articulated arm ending in a truly hollow bucket; cart has an open tapered bed and four flanged wheels; elevator has four structural posts, an exposed sheave, continuous cable path, cage portal, stairs and winch; sorter has an open hopper feeding a sloped screening bed, bins and a short discharge belt.

**Ownership:** Write only `voxel/mine`. No reading/copying frozen factory creative source, other-theme assets, ForestDemo, Git or shared live Blender. Isolated background Blender uses four threads. No image generation or subagents. Spaceport remains queued.

- [x] View the mine reference and record actual start.
- [x] Author original grids and semantic feature checks.
- [x] Build through parent-owned voxelkit and exporter.
- [x] Inspect all eight actual previews and correct only functional defects.
- [x] Independently reparse native files and freshly verify BLEND/GLB/FBX.
- [x] Record actual counts, timing, limitations and evidence; freeze and submit.

Start: 2026-10-23T14:29:23Z / 2026-10-23T23:29:23+09:00.

Completed and submitted frozen at 2026-10-23T14:45:11.250225+00:00; all required checks passed.
