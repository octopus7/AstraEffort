# Phase B worker brief

User explicitly resumed the approved nine new themes. Existing 45 models / 90 variants are complete and frozen. Read EXPANSION_PLAN.md, BRIEF.md and _tools/API.md. Each worker receives one current theme; later themes require explicit main dispatch after predecessor acceptance and a ready reference. Main generates every image sequentially. No worker image generation.

Write only voxel/CURRENT_THEME. Read only its REF/voxel/CURRENT_THEME/reference.png and generic parent utilities/spec. Do not inspect or reuse any other theme creative assets, scripts, palette, references or previous Blender assets. No ForestDemo, Git/index/branch changes, installations, extra agents, or shared live Blender scene. Use separate headless Blender with four threads and --python-exit-code 1. Model and effort remain gpt-6-astra/max; no Fast flag is separately available.

Build four original models using pure make_assets() in build.py and generic voxelkit / blender_pipeline. Large grid longest axis128, every large axis even. Half axes exactly /2 (may be odd), doubled meters/cell and same physical grid extent. Native occupancy is authoritative, no merely scaled mesh substitute. Exports VOX, BLEND, GLB, FBX, metadata and same-camera actual preview for each size. Friendly rounded overall stepped silhouettes, blunt purposeful forms, recognizable function; no faces, smileys, hearts, clouds or childish decoration. Flat opaque palette materials; no smooth mesh/bevel substitution. No permanent common diorama base unless a real structural part of the model.

Finite workflow: author the four assets, run one build, inspect all eight actual primary previews, run independent verify_theme.py with fresh format imports, and add a few meaningful saved-native probes for critical openings/mechanisms. Fix demonstrated defects only, not speculative polish. No optional views. Sources and geometries can be simplified where half-resolution readability benefits, while preserving intended functions.

Submit frozen results: concise RESULT.md (roughly one page), STATUS.json ready_for_review, palette, source, capture manifest, validation files/logs. Record actual UTC/KST start/finish and wall time, measured build/validation time and known limitations; do not invent timing or GUI checks. Avoid copying every metadata field into several reports. All requested asset names and both sizes must be present. The main independently validates files and inspects every final preview before acceptance.

Blender: C:/Program Files/Blender Foundation/Blender 4.5/blender.exe
Python: C:/Program Files/Blender Foundation/Blender 4.5/4.5/python/bin/python.exe
Project: D:/github/AstraEffort
Use UTF-8 when reading/writing. Import generic tools from D:/github/AstraEffort/voxel/_tools.
