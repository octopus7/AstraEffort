# Geothermal implementation plan

**Goal:** Four original geothermal models with native large/half occupancy and all requested exports and actual previews.
**Architecture:** Pure `make_assets()` returns new geometry through the parent voxelkit and Blender pipeline. Native grids remain authoritative; the independent parent verifier imports all saved formats.
**Tech stack:** Python, NumPy, isolated Blender 4.5, four CPU threads.
**Spec:** Phase B worker brief, expansion plan and generic API; current geothermal reference.

- [ ] Author protected tracked thermal rover with suspended sampler, stabilized lattice drill with manifold, hollow cooling tower with structural supports/pipes, and rounded glazed observatory with airlock/instruments.
- [ ] Run one complete isolated build of eight variants. Large axes are even with longest128; half axes exactly halve with doubled cell size.
- [ ] Inspect all eight actual primary previews; correct only demonstrated defects.
- [ ] Check saved-native functional openings and mechanisms, then freshly reimport BLEND/GLB/FBX for all variants.
- [ ] Record actual UTC/KST/wall/process timings, source/palette/captures/logs and concise ready-for-review evidence; freeze.

Sole write root is `voxel/geothermal`. No other-theme creative reads/reuse, shared Blender, image generation, installations, Git or extra agents. No lava landscape, smoke or common base. Flat opaque materials and exact stepped voxel boundaries remain intact.
