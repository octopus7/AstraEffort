# Forestry — ready for review

Four original models and eight native variants are frozen under `assets/{logging_harvester,timber_forwarder,sawmill,log_rack}/{large,half}/`. Every variant contains VOX 150, BLEND, GLB, FBX, actual `preview.png`, and `metadata.json`.

| Model | Large grid | Half grid |
|---|---|---|
| logging_harvester | 128×96×128 | 64×48×64 |
| timber_forwarder | 80×128×120 | 40×64×60 |
| sawmill | 128×128×118 | 64×64×59 |
| log_rack | 128×70×104 | 64×35×52 |

Large cells are 0.05m; half cells are 0.10m with identical physical grid extent. Native colored occupancy is authoritative. The restrained green/ochre/timber palette, stepped curves, and functional geometry were newly authored in `build.py`; no other theme resources were read or reused. Reference input: `REF/voxel/forestry/reference.png` only.

One isolated four-thread Blender build completed with exit 0. All eight primary renders were directly inspected. `validation_export.json` records **24 fresh BLEND/GLB/FBX checks** across eight variants, including native hashes, correct palette indexing, bounds, exact exposed boundaries, outward normals, materials, triangles and export studio exclusion. `validation_features.json` records **56 passing saved-native probes**, including the harvester throat/four rollers, open forwarder grapple/stakes, sawmill portal/rollers/blade, rack log gaps and six cradles. All four camera pairs match. No correction or extra render pass was required.

Actual tracked start: **2026-10-23T16:30:32Z / 2026-10-24T01:30:32+09:00**. Finish: **2026-10-23T16:44:37.744296+00:00 / 2026-10-24T01:44:37.744296+09:00**. Wall: **845.744s**. Build process: **86.959s**, including **79.052s** of rendering. Fresh-format verifier process: **15.264s**. Native feature probes: **0.387s**. No UE process or worker image-generation process was used. Exact commands and UTC process timing are in `build_process.json` and `verify_process.json`; logs, palette, capture manifest, source and visual notes are retained here.

Limits: static opaque palette assets; no rig, animation, collision, LOD chain or game-engine integration. The sawmill blade is partly hidden by the right portal post in the common view, while the open portal and feed rollers remain readable. Conservative half reduction may expand occupied bounds by one large cell (0.05m). No GUI inspection is claimed. Parent acceptance remains pending; no later theme was started.
