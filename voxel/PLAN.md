# Voxel Themes Implementation Plan

> Workers follow the explicitly authorized three-agent sequential-queue workflow. No extra approval or Git actions.

**Goal:** 39 original colored voxel models in large and half resolutions, across nine themes.
**Architecture:** Main generates sequential reference sheets and read-only generic VOX/export tools; each worker owns one theme at a time, validating it before starting its next assigned theme.
**Tech Stack:** Python, NumPy, MagicaVoxel VOX, isolated Blender 4.5.12, GLB/FBX, actual PNG renders.
**Spec:** BRIEF.md.

## Tasks
- [x] Main: generic voxel I/O, primitive authoring, reduction, surface extraction, export/render tools and format checks.
- [x] Main: sequential references for farm, factory, antarctic; dispatch three max workers.
- [x] Worker 1: farm; after acceptance harbor; after acceptance mountain_railway.
- [x] Worker 2: factory; after acceptance mine; after acceptance spaceport.
- [x] Worker 3: antarctic; after acceptance desert; after acceptance underwater.
- [x] Main: remaining references sequentially before each corresponding modeling task.
- [x] Main: independent voxel/export validation, actual image inspection, review index and verified archive.

## Review focus
- True voxel occupancy rather than decorative cubes or scaled mesh substitutes.
- Large/half semantics and functional details preserved in both versions.
- Palette indexing and exported colors.
- No hidden internal cube faces, invalid bounds, missing surfaces or inverted normals.
- All 39 asset pairs and required files present; no generated imagery used as actual render evidence.
