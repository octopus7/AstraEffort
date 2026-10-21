# ForestDemo coordination

This repository is running four independently authored Unreal Engine 5.7 scene
tasks: medium, high, xhigh, ultra. The coordinating chat owns integration and Git.

## Worker ownership

A worker assigned EFFORT may write only:
- `ForestDemo/Content/EFFORT/**`
- `ForestDemo/Content/Maps/EFFORT.umap` (level files only in Maps)
- `ForestDemo/Work/EFFORT/**`
- ignored scratch/output under `ForestDemo/Saved/Workers/EFFORT/**`

Do not inspect, copy, reference, overwrite, or delete another effort's assets,
scripts, reports, or scratch project. `/Engine` built-in assets and baseline
`/Script/ForestDemo` classes may be shared read-only. All newly authored assets,
including generated textures, materials, meshes, and source artwork, belong to
the assigned effort. No cross-effort asset references are allowed.

Run asset production in a separate scratch UE project under your own ignored
scratch directory; never launch a saving/editor-generation session against the
shared ForestDemo project. Use separate background Blender processes if needed;
do not mutate the shared Blender MCP scene. Do not build shared binaries, change
shared Source/Config/Plugins/uproject, or alter main.umap. Keep final maps
non-World-Partition, without external actors or external object packages, so
all authored resources fit their ownership scope. Save and validate before
copying only your owned final deliverables out of scratch.
Use dynamic lighting; do not create map-adjacent baked-lighting BuiltData assets.
Recursively validate /Game dependencies: only /Game/EFFORT assets may be used by
your map, plus its own /Game/Maps/EFFORT package. Close the private editor before
publishing the validated Content/EFFORT directory and EFFORT.umap.

## Git and future work

Worker chats must never run git add/commit/reset/stash/checkout/merge/rebase/push,
change branches, or modify the Git index. The coordinating chat makes the first
delivery commit separately for each effort after validation. Later worker turns
must not commit autonomously; explicit new user authorization overrides this rule.
Do not stage other workers' in-progress files. Do not push unless requested.

## Completion record

Each worker writes `ForestDemo/Work/EFFORT/RESULT.md` with actual UTC and KST start
and finish timestamps, elapsed wall seconds, delivered paths, validation evidence,
known limitations, and any external references. Write `STATUS.json` with effort,
status, started_at_utc, finished_at_utc, elapsed_seconds, map, validation summary,
and blockers. Use status `working`, `needs_attention`, or `ready_for_review`.
No invented durations or claims of rendering/validation that did not occur.
Supervisor-owned coordination documents live directly under `ForestDemo/Work/`.

The user also requires one final comparison report with screenshots in
`ForestDemo/Work/SUPERVISION.md`. Workers provide actual UE rendered
`Work/EFFORT/Screenshots/{overview,top_down,lake,beach}.png` and a
`capture_manifest.json` documenting camera/render settings and timestamps.
Follow the common capture specification in SUPERVISION.md. Never replace scene
evidence with generated imagery. Supervisor must inspect the images and embed
them in that single report alongside analysis, timings, validation and limitations.
