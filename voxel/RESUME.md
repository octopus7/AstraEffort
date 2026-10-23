# Resume voxel production

User requested on 2026-10-24 KST: commit through output inspection, then stop; continue in a later conversation. Do not resume without a new user instruction.

Completed and parent-accepted: original nine themes (39 models) plus six useful additions, total 45 models / 90 true large+half variants. All primary previews were inspected and native plus fresh BLEND/GLB/FBX validation passed. EXPANSION_STATE.json accepted entries cover all six additions. Their images and prompts are in REF/voxel/THEME/additions. Original models are unchanged. All workers are idle and instructed to stop.

Next authorized but paused phase: nine NEW themes, 36 models / 72 variants. No new-theme reference or geometry has been produced. Main must generate nine theme reference sheets sequentially first/as dependencies permit, never delegate image generation. Existing Astra/max worker queues: worker1 forestry -> airfield -> canal; worker2 construction -> recycling -> camping; worker3 fire_rescue -> geothermal. Main authors bakery after all nine reference sheets are ready. Exact asset names and ownership are in EXPANSION_PLAN.md and EXPANSION_STATE.json. No separately selectable Fast setting exists in the agent API.

Use existing _tools/voxelkit.py and blender_pipeline.py with 128-longest large grids and 64-longest half grids, same physical grid extent. Background Blender four threads, --python-exit-code 1; main verifies with _tools/verify_theme.py and records acceptance with accept_expansion.py after personally inspecting every final primary image. Preserve all current hashes and evidence. Read _tools/API.md and BRIEF.md.

Current catalog: README.md / index.html / delivery_manifest.json = 45 models. delivery_manifest_first39.json and the local original ZIP preserve the initial 39. prepare_checkpoint.py records this pause; do not run legacy prepare_delivery.py over the current catalog. prepare_expanded_delivery.py is prepared for the final 81-model / 162-variant catalog, but must not run until all 15 expansion units are accepted. It was syntax-checked only; its runtime checks and archive packaging remain for that final stage.

No ForestDemo creative files, previous rounded Blender sets, shared live Blender scene or other work should be changed. This commit is only completed voxel models, references, sources, validation, previews and resume records. No push was requested.
