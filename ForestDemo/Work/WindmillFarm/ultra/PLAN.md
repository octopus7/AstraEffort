# Old Windmill Farm Implementation Plan

> Agentic workers use scoped parallel asset authoring, followed by inline Unreal assembly and a fresh review. User ownership and no-Git instructions override skill defaults.

**Goal:** Deliver an independent, finished 100m farm scene and actual UE evidence.
**Architecture:** Procedural source meshes and textures are authored under Work; a new private UE project imports, assembles, saves and verifies them. Only validated Content and the named map are published after shutdown.
**Tech Stack:** Blender 4.5 Python, Python/Pillow/numpy, Unreal 5.7 Python and FBX importer.
**Spec:** DESIGN.md and ASSIGNMENT.md.

## Global constraints
- All writes stay in this WindmillFarm/ultra assignment; no shared or old creative assets.
- No Git or comparison accounting; shared Unreal runner, priority 2, no preemption.
- Dynamic lighting; owned /Game dependencies; conventional level without external packages.
- Source-art/render timings and actual UTC/KST times remain truthful.

## Review focus
- FBX units/orientation must yield metre-scale structures and a 100m plot.
- Surface UVs must exist; large ground tiling and deliberate repeated small details are disclosed.
- Visible dirt paths must remain walkable and clear of props.
- Shadow/capture exposure must preserve quiet colors and readable joinery.
- A fresh process must load the delivered map using only owned resources and Engine defaults.

## Tasks
- [x] 1. Record start, create isolated private content-only project and fail initial delivery checks (map/evidence absent).
- [x] 2. Author hero windmill sources and measure geometry/UVs in a separate Blender process.
- [x] 3. Author barn, tools, cart, fence and planting sources in another separate Blender process.
- [x] 4. Author terrain, irregular dirt/grass transitions, fields, orchard layout, textures and import/assembly code.
- [x] 5. Import assets, create owned materials, assemble and save the private level; inspect actual UE draft renders and resolve material composition defects.
- [x] 6. Fresh-process reload, PIE and collision, dependency/UV/material validation and four final 1920x1080 captures; inspect images.
- [x] 7. Review evidence, close private editor, publish owned files with hashes, write RESULT/STATUS and final reproducibility notes.

## Execution ledger
- Started from explicit new-theme dispatch; no old worker source was read or reused.
- Design and execution choices are delegated by ASSIGNMENT.md; no approval pause or Git steps.
- Reversible art authoring is verified by geometry/UV data and actual renders; tests focus on delivery guards and functional map/runtime invariants.

- Completed final review fixes for hay support/barrel clearance, fresh process verification, seven actual renders and owned publication/hash checks. Accepted microscopic tower UV and instance-scale density exceptions are documented in RESULT.md.
