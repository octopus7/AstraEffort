# Forest ultra — approved anime tree self-improvement

Published for review.

Start UTC: 2026-10-21T15:30:53+00:00
Start KST: 2026-10-22T00:30:53+09:00
Finish UTC: 2026-10-21T16:24:27.478715+00:00
Finish KST: 2026-10-22T01:24:27.478715+09:00
Elapsed wall seconds at this record: 3214.478715
Measured UE queue wait: 126.290873 seconds; UE process execution: 908.826240 seconds. Native build is separately recorded in Execution/native-build.json. Image generation: 0 seconds.

This pass is outside the frozen initial/TexturePass comparison cutoff. No prior results, timing/token documents, screenshots or source artwork were edited.

## Change

Replaced only the 63 broadleaf StaticMeshActors with the approved BP_AnimeFoliageTree, reparented to /Script/ForestUltraTrees.ForestUltraAnimeTreeActor. Ten necessary assets (one BP, four meshes, two materials, three textures) were renamed and re-saved by UE into /Game/Forest/ultra/AnimeTree. Original actor positions and yaw are preserved within 1e-8; uniform size fitting keeps the model within old dimension bounds. The 871 other actors retain their recorded transforms, meshes and material references. Existing 978 content assets remain byte-identical; only the map and ten new assets are delivery changes.

The native port preserves source construction/runtime defaults, per-actor leaf/shadow MIDs, transform-driven gradient CPD, ten transient hidden shadow proxies per tree and the quarter-resolution shared canopy rim renderer. The six core source files differ only by declared namespacing/include/shader-path substitutions; the shader is byte-identical. IntegrationProposal contains the ten source/shader/descriptor files and r.CustomDepth=3 requirement. Shared installation and build are supervisor-owned.

## Evidence

- 24/24 fresh-map and runtime checks pass: non-World-Partition, no external/BuiltData packages, dynamic lighting, 100m footprint, owned recursive dependencies, correct native parent and 63 unique stencils.
- Source inspection: eight checks pass, including ten leaf clumps/ten shadow proxies, clamping, MID refresh, repeated refresh without proxy accumulation and complete asset closure.
- Actual PIE: all 63 traces hit each tree’s own Trunk component and mesh. All runtime trees have ten shadow proxies; parameter refresh passes. Player is possessed, horizontal movement works, and a blocking downward sweep hits the exact owned ground actor/component/mesh with no initial overlap; actual downward movement is 71.811877 cm. PIE ends normally.
- Eight actual before and fourteen actual after PNGs, 1920x1080, High scalability, D3D12 SM5. All eight common cameras match. No image editing.
- Rim on/off, guide translation and timed wind frames differ inside the canopy mask. See render_analysis.json and Screenshots/After/tree_rim_debug.png.
- Original /Game/Environment and /Script/TunaSweeper references: zero in recursive registry closure and serialized path scan. Fresh validation ran without original Content/Environment and without the temporary native redirect.
- 1091 frozen evidence files and approved original source/native/shader hashes remain unchanged. See file_audit.json.
- The final saved-palette render/PIE process exited normally before publication (Execution/ue-final-palette.json). One earlier idle launch had double-quoted ExecCmds; the human explicitly authorized stopping that exact owned process, and the incident is recorded in execution_incident.json.

## Paths

- Final map: ForestDemo/Content/Maps/ultra.umap
- New owned assets: ForestDemo/Content/Forest/ultra/AnimeTree/*.uasset
- Native integration proposal: ForestDemo/Work/ultra/SelfImprovement/IntegrationProposal
- All new reports/scripts/screenshots: ForestDemo/Work/ultra/SelfImprovement
- Private project: ForestDemo/Saved/Workers/ultra/SelfImprovement/ForestDemo

Publication state: 11 files copied and SHA-256 checked; publication.json records exact paths and supervisor plugin verification.

## Limitations and provenance

- The initial source-default lime palette was moderated through exposed per-instance gradient/clump/rim properties after visual review. Source BP/native defaults and algorithms remain unchanged. Some trees become shorter because the source is wider relative to height.
- The fixed lake camera already had a foreground trunk at its left edge; the new curved trunk occludes more of the upper-left corner. It was not moved to improve the comparison.
- Runtime CPD is not exposed to Python; no direct CPD getter pass is claimed. Native logic equality plus rendered guide movement supplies the available evidence.
- Packaged builds, non-D3D12 backends and manual controller input were not tested. Runtime checks use actual scripted PIE. Rendering time samples are evidence, not a performance benchmark.
- Baseline water/terrain/pines remain unchanged. Existing artistic water effects and limitations are inherited. Unused old broadleaf assets remain to preserve baseline content.
- Approved source: D:/github/extraction_shooter/TunaSweeper, specifically BP_AnimeFoliageTree and its necessary closure plus native anime actor/CanopyRim source and shader. It was never launched, saved, built or modified. See source_provenance.json and native_port_manifest.json.
- No Git/index/branch operations, no shared code/config edits by this worker, no shared Blender mutation, no cross-effort creative reads or references.

## Final color review correction

Original Before and all 15 initial After files remain hash-identical; InitialValidation preserves the earlier validation records. Two parameter-only candidates were rendered in Screenshots/PaletteStudy. The quieter moss candidate was selected from actual tree_detail and overview images. Final saved-map evidence is in Screenshots/Final: overview, top_down, lake, beach and tree_detail, all at the identical original cameras.

Scene-instance parameters: {"gradient_dark_color": [0.42, 0.61, 0.82, 1], "gradient_light_color": [0.55, 0.7, 0.9, 1], "gradient_strength": 1.0, "clump_shading_strength": 0.38, "rim_strength": 0.22, "rim_color": [0.38, 0.61, 0.51, 1], "rim_width_pixels": 18.0, "rim_brightness": 1.0}

The final fresh process verified all 63 saved actor parameter sets and all 630 leaf MIDs against these values. WindStrength=.75, LeafCardScale=.8, LeafDensity=.45, GradientWidth=400 and GradientExponent=1 remain unchanged. All 63 runtime trunk traces, player sweeps, shadow counts and runtime refresh passed again. No shader, native algorithm, mesh or texture was changed by this color correction.

The palette-only study produced all four images and logged a complete engine shutdown but returned process exit -1073741819 after log closure; no UE fatal call stack was logged. This is recorded as an unresolved one-off shutdown anomaly. The subsequent saved-map application and final fresh rendering/PIE process must both exit 0 before publication.
