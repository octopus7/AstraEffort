# Ordinary rounded model set worker brief

The user explicitly authorized nine sets in three groups, one Astra/max worker per set, and instructed that review be deferred. Main owns references, dispatch and Git. Do not ask for further design approval or add review gates. Fast has no separate field in the agent API.

Read SET_BATCH_PLAN.md and your own set TASK.md/STATUS. Write only Blender/SetNN; read only REF/SetNN for creative references. No voxel, other set or ForestDemo creative resource reads/copies. Generic Blender/Python APIs are allowed; invent original geometry matching the assigned references. No shared Blender MCP scene, installations, worker Git, extra agents or image generation.

User also requested references beside each set. Main mirrors them in `Blender/SetNN/REF/`; treat this subfolder as read-only and link to it in your README. The original `REF/SetNN/` is retained.

Deliver four ordinary smooth/rounded mesh models, not voxels: BLEND with editable named parts, geometry-only GLB and FBX, meaningful per-part UVs and named solid PBR palette materials. Rounded bodywork, beveled building edges and sturdy functional details; no arbitrary hearts/clouds/smileys/faces. Do not add a shared diorama slab unless a foundation/deck belongs to the facility.

Each model goes in its own SLUG folder with SLUG.blend, SLUG.glb, SLUG.fbx, metadata.json and actual `renders/hero.png` / `renders/rear.png`. Use a neutral studio, soft area lighting and consistent front/rear three-quarter framing. 960x960 or 1024x1024 renders are suitable. Separate ASSET and STUDIO; export selected asset meshes only. Record intended meter dimensions and metadata from the authored scene; these are production measurements, not proof of independent validation.

Use isolated Blender 4.5.12 background processes, --factory-startup --threads 4 --python-exit-code 1. Blender: C:/Program Files/Blender Foundation/Blender 4.5/blender.exe. Bundled Python: C:/Program Files/Blender Foundation/Blender 4.5/4.5/python/bin/python.exe (-X utf8). Prefer a Python subprocess wrapper that captures the actual return code; PowerShell Start-Process ExitCode can become null after Refresh. Do not alter installed addons if unrelated warnings appear.

Skip visual inspection, fresh BLEND reopen/GLB/FBX reimport, geometry/UV validators and reviewer agents as requested. Generate previews for later review without opening them. Only check build/export process completion and that the expected files exist and are nonempty. If generation fails, fix that execution failure; do not start speculative quality passes.

Write concise RESULT.md, STATUS.json (`status: produced_unreviewed`, `review_status: deferred_by_user`), delivery_manifest.json listing each asset's paths, bytes and SHA256, build source and logs, actual UTC/KST start/end, wall and process timings. Never claim inspected, validated or tested. Hash recording is inventory, not validation. No invented timing. Freeze the set after producing all four assets; parent will commit together with two sibling sets. Await next explicit dispatch.
