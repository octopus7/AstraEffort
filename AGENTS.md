# ForestDemo coordination

This repository is running eight independently authored Unreal Engine 5.7 scene
tasks: Forest and MountainStation, each at medium, high, xhigh, ultra.
The coordinating chat owns integration and Git. Assignment identity is
`(theme, effort)`, never effort alone.

## Worker ownership

A worker assigned THEME and EFFORT may write only its table row:

| Theme | Assets | Level (only .umap in Maps) | Work | Ignored scratch |
|---|---|---|---|---|
| Forest | `ForestDemo/Content/Forest/EFFORT/**` | `ForestDemo/Content/Maps/EFFORT.umap` | `ForestDemo/Work/EFFORT/**` | `ForestDemo/Saved/Workers/EFFORT/**` |
| MountainStation | `ForestDemo/Content/MountainStation/EFFORT/**` | `ForestDemo/Content/Maps/MountainStation_EFFORT.umap` | `ForestDemo/Work/MountainStation/EFFORT/**` | `ForestDemo/Saved/Workers/MountainStation/EFFORT/**` |

Do not inspect, copy, reference, overwrite, or delete another effort's assets,
scripts, reports, or scratch project. `/Engine` built-in assets and baseline
`/Script/ForestDemo` classes may be shared read-only. All newly authored assets,
including generated textures, materials, meshes, and source artwork, belong to
the assigned theme and effort. No cross-effort or cross-theme asset references
are allowed, including Forest resources in MountainStation or the reverse.

Forest path change (2026-10-21 21:19:35 KST): add a Forest theme folder below
Content. Forest's only valid final asset root is `/Game/Forest/EFFORT/`; old
`/Game/EFFORT/` references must be migrated/rebuilt inside the private project,
resaved, and verified absent before publication. Do not move .uasset files with
filesystem operations alone. Map paths stay `/Game/Maps/EFFORT` and Work/Saved
paths stay unchanged. Record migration overhead without resetting work start time.

Run asset production in a separate scratch UE project under your own ignored
scratch directory; never launch a saving/editor-generation session against the
shared ForestDemo project. Use separate background Blender processes if needed;
do not mutate the shared Blender MCP scene. Do not build shared binaries, change
shared Source/Config/Plugins/uproject, or alter main.umap. Keep final maps
non-World-Partition, without external actors or external object packages, so
all authored resources fit their ownership scope. Save and validate before
copying only your owned final deliverables out of scratch.
Use dynamic lighting; do not create map-adjacent baked-lighting BuiltData assets.
Recursively validate /Game dependencies: only /Game/THEME/EFFORT assets may be
used by your map, plus its own map package from the table. Close the private editor
before publishing the validated owned asset directory and named .umap.

## Machine resource coordination

Eight jobs share one machine. Use the supervisor-owned read-only utility
`ForestDemo/Work/Tools/Run-UnrealIsolated.ps1` for future private Unreal processes.
It serializes UE execution using a named mutex, without sharing creative assets.
Already running editor jobs may finish. Do not kill another worker's processes.
Use your own scratch project, abslog and timing output paths. CPU-side source-art
authoring may continue independently. Record mutex wait seconds separately from
UE execution seconds and total wall time. Do not change this shared utility.

## Git and future work

Worker chats must never run git add/commit/reset/stash/checkout/merge/rebase/push,
change branches, or modify the Git index. The coordinating chat makes the first
delivery commit separately for each effort after validation. Later worker turns
must not commit autonomously; explicit new user authorization overrides this rule.
Do not stage other workers' in-progress files. Do not push unless requested.

## Completion record

Each worker writes `RESULT.md` under its Work path with actual UTC and KST start
and finish timestamps, elapsed wall seconds, delivered paths, validation evidence,
known limitations, and any external references. Write `STATUS.json` with effort,
status, started_at_utc, finished_at_utc, elapsed_seconds, map, validation summary,
and blockers. Use status `working`, `needs_attention`, or `ready_for_review`.
No invented durations or claims of rendering/validation that did not occur.
Supervisor-owned coordination documents live directly under `ForestDemo/Work/`.

The user also requires one final comparison report with screenshots in
`ForestDemo/Work/SUPERVISION.md`, with separate sections for both themes.
Workers provide actual UE rendered `Screenshots/` under their Work path:
Forest: `{overview,top_down,lake,beach}.png`;
MountainStation: `{overview,top_down,platform,tracks}.png`, plus a
`capture_manifest.json` documenting camera/render settings and timestamps.
Follow the common capture specification in SUPERVISION.md. Never replace scene
evidence with generated imagery. Supervisor must inspect the images and embed
them in that single report alongside analysis, timings, validation and limitations.

Final integration preserves all eight scene maps. Retire only baseline main.umap
after all eight results are validated; never delete the other theme's maps to
enforce the old four-map count. The default can remain /Game/Maps/medium.
