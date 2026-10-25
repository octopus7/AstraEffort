# Canal — ready for review

Four original assets / eight native variants are frozen: `canal_boat`, `lock_gate`, `drawbridge`, `lockkeepers_house`. Deliverables are under `assets/<asset>/{large,half}/`: VOX, BLEND, GLB, FBX, metadata and actual 768px preview PNG. `build.py` contains pure `make_assets()`; `palette.json` records the restrained teal, limestone, timber and terracotta palette.

| Asset | Large grid | Half grid | Large cell |
|---|---|---|---|
| canal_boat | 48×128×58 | 24×64×29 | 0.065 m |
| lock_gate | 128×52×90 | 64×26×45 | 0.06 m |
| drawbridge | 84×128×104 | 42×64×52 | 0.065 m |
| lockkeepers_house | 128×104×128 | 64×52×64 | 0.05 m |

All large axes are even and longest 128; half axes divide exactly by two, cell size doubles, and physical grid extent is unchanged. No manual half edits. Geometry uses exposed voxel boundaries and flat opaque palette materials.

Validation passed: 8 native reparses, 24 fresh BLEND/GLB/FBX imports, 24 saved-native feature checks, and inspection of all 8 final primary previews. Bounds, palette assignments, exposed outward faces, surface area, triangles and file hashes passed. Four camera pairs match. See `validation_export.json`, `validation_features.json`, `visual_review.json`, `capture_manifest.json` and the logs.

The boat has an open recessed cargo well; gates have a continuous central gap and hand gears; the 30° raised bridge has an empty navigation corridor, pivots and counterweights; the house has a separate working-form control cabinet. One demonstrated large-bridge lift-link gap was corrected with a transverse deck-nose member, using a bridge-only rebuild. Before PNG/probe evidence is in `evidence/`; no superseded model binaries remain.

Actual start: 2026-10-25T05:01:44.530147+00:00 / 2026-10-25T14:01:44.530147+09:00. Finish: 2026-10-25T05:14:34.888730+00:00 / 2026-10-25T14:14:34.888730+09:00. Wall: **770.36 s**. Initial full build: **87.14 s**; selective bridge correction: **23.30 s**; fresh-import process: **9.16 s**; native probes: **0.50 s**. Worker image generation: **0 s**. Initial launcher exit code was unavailable; its timing is preserved honestly, and final correction/verification exited 0.

Limitations: static poses, opaque glazing, no rig/animation, collision, LOD chain or engine integration. Half resolution simplifies fine masonry seams and glazing trim; conservative reduction can expand a boundary by one large cell. No river/terrain base or optional views. Reference: only `REF/voxel/canal/reference.png`, documented in `source_manifest.json`; all scene evidence is actual Blender rendering. File freeze: `frozen_file_hashes.json`. Main owns final review and Git.
