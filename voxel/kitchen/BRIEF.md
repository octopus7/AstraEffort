# Kitchen voxel production brief

User dispatch (2026-10-25): create the proposed kitchen theme, native voxel data and preview images only; distribute work to exactly three gpt-6-astra/max subagents; main coordinates only. User requested Fast; the spawn API exposes no Fast flag, so Fast is not claimed. This direct instruction authorizes execution of the twenty proposals without another design gate.

## Deliverables and ownership

20 independently authored kitchen models, large and half = 40 native VOX files and 40 actual rendered PNG previews. Only .vox and .png are product outputs. Source scripts, palette, metadata, validation, capture manifests and timing/RESULT/STATUS records accompany them. Do not create .blend/.glb/.fbx/.obj/.umap or engine assets, reference image generation, rigging, animation or collision.

Main writes only kitchen coordination documents. All authoring, native verification, preview rendering and image inspection are performed by the three workers. Workers cannot spawn more agents, use Git, install packages, modify shared utilities or read other themes' creative resources. No ForestDemo or shared live Blender scene. During production each worker reads/writes only its batch plus this brief and generic voxel/_tools. Later explicitly assigned read-only same-kitchen cross-review is allowed; never reuse another batch's geometry.

| Worker / writable root | Exact slugs and labels |
|---|---|
| appliances / voxel/kitchen/appliances | double_door_fridge (양문형 냉장고), range_oven (가스레인지·오븐), microwave (전자레인지), dishwasher (식기세척기), range_hood (레인지 후드), rice_cooker (전기밥솥), electric_kettle (전기주전자) |
| furnishings / voxel/kitchen/furnishings | sink_cabinet (싱크대), kitchen_island (아일랜드 조리대), dish_cabinet (식기 수납장), kitchen_cart (이동식 주방 카트), dish_drying_rack (식기 건조대), knife_block (칼꽂이) |
| countertop / voxel/kitchen/countertop | stand_mixer (스탠드 믹서), espresso_machine (에스프레소 머신), toaster (토스터), blender (블렌더), stock_pot (양수 냄비), frying_pan (프라이팬), cutting_board_knife (도마·식칼 세트) |

Each batch: assets/SLUG/{large,half}/SLUG.vox, preview.png, metadata.json. Also build.py (pure make_assets()), preview_pipeline.py if needed, validate.py, palette.json, capture_manifest.json, validation.json, frozen_file_hashes.json, overview_half.png, RESULT.md, STATUS.json and logs. Batch overview is a clearly labeled contact sheet assembled from actual previews by that worker. No invented render evidence.

## Appearance

Coordinator choice where the user did not specify: cozy household kitchen, cream appliances, sage green cabinets, warm light oak, charcoal fittings, opaque blue-gray glass. Friendly, purposeful, restrained rounded stepped silhouettes. No smileys, hearts, clouds, ornamental faces, typography on models, smooth mesh substitutions or permanent diorama floor. Each model distinct and readable at half size. Purposeful functional openings should remain empty (sink basin, pot bowl, mixer clearance, handle loops, rack slots, pan bowl). A selected static open pose is fine for dishwasher/doors/lid when it improves understanding; no animation is implied. Treat glass as opaque palette color. All resources newly authored for kitchen.

Common palette indices (RGBA, fixed order; new shades only if necessary and documented):
0 empty (0,0,0,0)
1 cream (232,225,205,255)
2 sage (121,151,133,255)
3 dark sage (75,105,91,255)
4 warm oak (181,130,78,255)
5 pale oak (217,176,113,255)
6 charcoal (48,56,57,255)
7 metal (156,170,170,255)
8 dark metal (91,108,112,255)
9 opaque glass (92,133,145,255)
10 ceramic white (244,239,225,255)
11 warm accent (191,105,70,255)
12 dark cavity (35,42,44,255)
13 bread (217,164,85,255)
14 bread crust (151,94,48,255)
15 indicator (203,183,106,255)

## Native geometry and rendering

Use existing read-only voxel/_tools/voxelkit.py Grid, Asset, write_vox, read_vox, reduce_half, grid_stats. Read voxel/_tools/API.md as API documentation, but this brief overrides the old export requirement. DO NOT call run_theme(): it emits unwanted mesh files. Workers implement a minimal batch-local runner using existing blender_pipeline.build_surface and add_studio functions without modifying the shared utility.

Large has longest grid axis exactly 128, all axes even. Half has each axis exactly divided by 2, longest 64, cell size doubled and same physical grid extents. Native occupancy must actually reduce; no merely scaled mesh. Document any optional half_postprocess corrections. Choose plausible per-asset meter scale (fridge about 1.8-2m tall, kettle about .25-.35m tall), not the default 6.4m for every item. Front -Y, Z up. Thin functional elements should generally be at least 4 large voxels thick and gaps survive reduction.

Write each VOX, reparse it, validate occupancy/palette, then build render-only temporary in-memory geometry from the REOPENED file. Render both sizes using the same large-grid camera bounds with blender_pipeline.add_studio: 768x768 PNG, Cycles CPU, 24 samples, denoising, AgX, fixed 4 CPU threads. Do not save meshes or Blender scenes. Native SHA256 and PNG SHA256, camera/light/render settings and actual UTC timestamps must be captured. Reference imagery is not needed.

Blender: C:/Program Files/Blender Foundation/Blender 4.5/blender.exe
Python: C:/Program Files/Blender Foundation/Blender 4.5/4.5/python/bin/python.exe
Run isolated headless Blender with --background --factory-startup --threads 4 --python-exit-code 1. Own root/logs only. Parallel isolated CPU jobs permitted; do not kill other processes or modify system configuration.

## Validation and finite workflow

Workers validate all saved files: valid VOX150, dimensions, palette index bounds, no duplicate/out-of-grid coordinates, nonzero occupancy, full roundtrip comparison to authored grids, exact large/half grid and scale relationship, hash integrity and actual PNG size. Feature probes must read saved VOX data and check meaningful cavities/handles/clearances for each model where applicable, including half versions. Inspect every own preview with image tools and record observed findings. Fix demonstrated defects only. No speculative polish or optional camera production.

Record real UTC/KST start/finish, wall/build/render/validation seconds; never invent timings or claim GUI checks. Status working -> ready_for_review, blockers explicit. Main will arrange cross-review using these same three agents after production, without creating extra agents. Reviews write into the reviewer's own batch and are read-only for the target batch. Finish with concise message giving counts, checks, limitations and paths.
