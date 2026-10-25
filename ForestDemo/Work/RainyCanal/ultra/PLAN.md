# RainyCanal ultra implementation plan

> Execution: parent integration with three independent source-art agents, followed by independent whole-scene review. Apply executing-plans and verification-before-completion. User has approved autonomous implementation; no repeated design approval or Git operations.

**Goal:** A calm 100×100m rainy canal village with connected pedestrian routes, grounded architecture, wet materials, visible rain and animated canal/puddle ripples.

**Architecture:** New content-only private UE5.7 project. Original Blender FBX assets and original procedural textures; Python editor assembly. Dynamic lighting, opaque reflective canal/ripple materials and translucent material-driven rain. Only own asset root and own conventional map may be published after closed-editor validation.

**Spec:** ASSIGNMENT.md in this directory. Work/scratch isolation substitutes for a Git worktree; no scripts or creative resources from earlier themes are read or reused.

## Design and interfaces

- Metres in Blender, Z up; design X east, Y north. UE mapping is `(100*x,-100*y,100*z)`; rotation uses named pitch/yaw/roll. FBX unit import and orientation are verified before population.
- Straight 12m-wide canal runs north/south through the centre. Water z=-0.85m; quays/streets z=0. Canal walls, base and shore cover depth continuously.
- Stone bridge crosses at y=-15m; wooden bridge at y=28m. Both have 16m span, landing z=0 and open clear walk. Buildings sit outside quays, front toward canal; 8 primary houses/shops with weathered roofs, windows/eaves/downspouts.
- Two banks, stone-paved quays and connecting lanes to planted outer edges; trees, benches, lampposts, planters, bollards and a small boat/dock. Preserve readable walk routes and avoid prop/door clashes.
- Subagents own only Art/Architecture, Art/Props, Art/Textures and matching scratch folders. Mesh material slots are Stone, Cobble, PlasterCream, PlasterSage, PlasterRose, Timber, RoofSlate, RoofClay, Metal, WindowGlass, Leaf as applicable. UV0 unique island atlas; UV1 target128px/m at1024 for scale1, with placed-scale exceptions recorded.
- Parent owns Art/Landscape, design.py, bootstrap.py, assemble.py, capture.py, validate.py, Run-Canal.ps1, manifests, STATUS/RESULT, publication. No shared project mutation.

## Review focus

1. Saved maps must be self-contained: fresh-process recursive dependency whitelist and no external actor/object or BuiltData packages.
2. Bridge/shore/deck contacts and building foundations must meet geometry; check representative surface traces, bounds and actual close renders.
3. Rain and water graphs can exist without compiling: assert node connections, inspect compile/fallback logs and fixed-camera time-separated actual captures.
4. Wet surfaces must remain readable under overcast light: inspect canal and street views, distinguish plaster/stone/metal roughness, avoid uniformly mirror-like ground.
5. Animation can clip outside mesh bounds or rain under roofs: extend bounds, limit rain footprint/height where possible, document material-weather approximation and camera limits.

## Tasks

- [x] 1. Create fresh status and private project, evidence acceptance tests (initially absent/failing), design and owned path guards. Use no old theme sources.
- [x] 2. Build independent architecture/props/surfaces and parent landscape/weather meshes. FBX reimport/UV density/material slots/bounds QA, source provenance and previews.
- [x] 3. Import and assemble: only own paths, conventional map, dynamic light and player start, collision on ground/buildings/bridges, animated rain/water/puddles. Save and inspect first actual UE renders.
- [x] 4. Fresh-process reload and representative PIE possession/movement/collision; inspect full dependencies/UV/material graphs/effect bounds; fix concrete visual/validation defects.
- [x] 5. Capture1920×1080 overview/top_down/canal/rainy_street plus fixed-camera effect pairs and short actual frame sequence. Independent review; publication guard checks private shutdown and source/destination hashes.
- [x] 6. Write separate RESULT/STATUS ready_for_review with actual UTC/KST start/finish, queue wait/run logs, method/limits and reproducibility. No comparison accounting or Git commit.

## Operational ledger

- Started2026-10-22T14:53:36Z (first explicit clock reading after assignment inspection). Initial read preceded the reading.
- Ruling: user assignment authorizes routine design/execution and publication to owned Content/map; skip skill-default repeated approval, worktree/index/commit and shared documentation steps. Independent source agents complement parent integration; no separate chats.
- Pre-flight: mesh agents and parent texture materials share exact slot names and UV1 density; all FBX origins and front orientation are recorded in manifests. Parent converts Blender coordinate convention explicitly.

- Final delivery 2026-10-22T15:55:51.932422+00:00: all23 fresh-process checks,13 stills,80 actual frames,source QA,closed-editor71-package publication and separate report complete. Final assembler includes lighting/AO and coherent material projection; Landscape source reconstruction applies ramp then wall notch. No Git or comparison writes.
