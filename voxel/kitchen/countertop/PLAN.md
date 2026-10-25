# Countertop native voxel implementation plan

**Goal:** Seven newly authored cozy kitchen models, each with genuine large and half occupancy and an actual 768px preview.

**Architecture:** A pure `make_assets()` builds palette-indexed grids. A local pipeline writes and reparses native VOX before temporary Blender surface extraction and rendering. A separate validator reopens every native and PNG file and checks native functionality, hashes, scale and evidence.

**Tech stack:** Existing read-only `voxelkit`, NumPy, isolated Blender 4.5 CPU, four threads.

**Spec:** `../BRIEF.md`. The explicit dispatch approves execution without another design gate. All writes stay in this batch; no Git or further delegation.

## Steps

- [x] Write and run saved-file contract checks with absent deliverables to establish the failure condition.
- [x] Author stand mixer, espresso machine, toaster, blender, stock pot, frying pan and cutting board with knife. Use cream/sage/oak, opaque glass, rounded stepped edges, plausible scale and native functional voids.
- [x] Write/reopen fourteen VOX150 files; check exact authored occupancy/palette roundtrip and half reduction.
- [x] Render reparsed native files with shared large-grid camera bounds, 768px Cycles CPU, 24 samples, AgX and four threads. Save no mesh or Blender files.
- [x] Inspect all fourteen actual previews individually; fix only demonstrated issues. Assemble a labeled half contact sheet from actual previews.
- [x] Revalidate final files, record UTC/KST timings, capture settings, hashes, visual observations and limitations. Submit for assigned cross-review.

## Review focus

Saved-file feature probes must catch filled bowls, blocked toaster slots, lost handle holes, blocked mixer working clearance and espresso cup clearance. Half grids must be exactly half each dimension with doubled voxel size and fewer occupied cells. Both cameras must agree. Products must contain only `.vox` and `.png`; evidence files must match their hashes. No smooth replacement geometry or generated scene evidence.
