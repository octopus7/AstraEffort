# Forest ultra native anime tree migration

**Goal:** Replace the existing broadleaf actors with the approved BP_AnimeFoliageTree while preserving its construction, camera-facing foliage, gradient, wind, hidden shadow proxies and shared canopy rim renderer.

**Architecture:** Preserve source algorithms in a small namespaced runtime plugin, ForestUltraTrees. Build and test it only in a new owned scratch project. Temporary native class redirects load the original BP; UE saves all necessary assets under /Game/Forest/ultra/AnimeTree and removes redirectors. Remove temporary redirects before fresh reload. Shared plugin/renderer configuration integration belongs to the supervisor; no final publication with an unresolved native dependency.

**Scope and priorities:** (1) feature-preserving tree migration; (2) fit the source tree to existing broadleaf placements and calm palette without changing pines/lake/coast/layout; (3) produce actual comparable before/after renders and direct feature tests. This is one finite pass. No Git/index actions, other-effort reads, source-project writes/launches/builds, or shared project-code edits.

**Alternatives considered:** Raw asset copying cannot resolve the native parent. Actor-only BP conversion would require reconstructing transform callbacks, transient shadow components and render-graph compute/composite passes and carries avoidable fidelity risk. A narrow plugin preserves these source behaviors with only namespacing and shader-path changes.

- [x] Freeze hashes of own prior Work evidence and committed Content, and hash every approved source dependency.
- [x] Capture the unmodified committed scene through the existing private project into Screenshots/Before using the common cameras.
- [x] Build the minimal plugin in new scratch. Exercise construction, clamping, gradient coefficients, shadow counts, stencil allocation, cleanup and runtime refresh; verify rim/wind through actual rendered toggles/time samples.
- [x] Validate UE registry closure and raw BP default/component snapshot. Re-save assets and BP with the new native parent into owned content, remove redirectors and redirects, then reload without source paths.
- [x] Replace only broadleaf actors, preserving source placements and deriving scale from old bounds; retain pines, water materials and all terrain/props. Audit bounds, trunk collision and per-tree feature parameters.
- [x] Submit concrete tested plugin files/config requirements under IntegrationProposal. Record native integration dependency in STATUS; supervisor owns shared installation/build.
- [x] Fresh reload, BP compile, recursive dependencies, actual world_partition=None, no external/BuiltData packages, 100m footprint, real PIE pawn and tree/ground blocking hit identity, normal exit.
- [x] Render 1920x1080 overview/top_down/lake/beach plus close tree, rim on/off and wind time evidence into Screenshots/After. Visually review and record limitations.
- [x] Close private UE, verify source and prior evidence hashes unchanged, publish only owned content/map after native support is resolved, hash-check delivery, record UTC/KST and queue/run timing in RESULT/STATUS.

No new image generation is planned: the task explicitly authorizes the original tree's necessary art assets. Source copyright/provenance is preserved in the manifest; no authorship claim is made for imported assets or algorithms.

Final review correction: initial After evidence was frozen; two exposed-parameter palettes were compared. Moss was saved on 63 scene instances, 630 leaf MIDs checked on fresh reload, and five identical-camera Final renders captured. Actual PIE passed again and final process exited 0. Published only 10 AnimeTree assets and ultra.umap after supervisor native build integration. Supervisor owns its separate shared-build acceptance check.
