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

User priority update: when both themes are waiting for Unreal, Forest gets the
next slot before MountainStation. Never preempt or stop an already running UE.
Latest override: MountainStation/medium has the highest waiting priority, ahead
of Forest. Then Forest precedes the other MountainStation efforts. FIFO applies
within each priority. This applies to future queue slots only; active UE is never
preempted. The named chat is MountainStation medium — 산악 기차역 제작.
Use the supervisor's updated runner for new registrations; the runner may write
only scheduling metadata to shared ignored Saved/Coordination. This metadata is
not a creative resource and does not permit reading another worker's assets.
Already loaded legacy waiters must finish safely; never kill a launcher while
its UE child may still be active. Include priority-related delays in wait timing.

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

## Authorized Forest texture and beach follow-up

After all four Forest first deliveries are reviewed and individually committed,
the supervisor will dispatch a second pass to the same four Forest chats with
their original efforts. Do not start this pass before that supervisor dispatch.
MountainStation remains independent and its completion is not a prerequisite.

The second pass assigns UV islands with consistent texel density to placed props
such as trees and uses independently generated images as textures for their unique
surfaces. Each worker records its UV density target, measured density/scale,
padding, overlap checks and exceptions, plus image-generation prompts, original
outputs and surface mapping within its own Work directory. Newly authored UVs,
textures, materials and source images obey the same strict ownership boundaries;
no cross-effort or cross-theme reuse or inspection is allowed.

Improve beach detail with white foam, time-varying waves, and underwater bright
caustic patterns. Document whether refraction/caustics are simulated or artistic
approximations. Maintain the restrained rounded game art. Generated imagery is
allowed for asset textures; screenshots remain actual UE renders, never generated
scene evidence. Validate the updated saved map, runtime behavior, dependencies,
UVs and materials, and recapture the common views plus timed water evidence.

The supervisor preserves first-delivery evidence and screenshots under each
Forest worker's Work/<effort>/FirstDelivery before dispatch. Preserve original
start, completion, commit and frozen token records; record second-pass timings
and token deltas separately. Workers still never commit. Supervisor completion
includes this pass, its separate per-effort commits and before/after comparisons.

## Authorized MountainStation texture follow-up

After all four MountainStation first deliveries are reviewed and individually
committed, the supervisor dispatches a second UV/image-generated texture pass to
the same four chats with original efforts. Do not start before explicit dispatch.
Apply unique-surface UV islands and consistent measured texel density to station
architecture, rails/sleepers, platform, tunnel, trees and props. Record area/scale,
overlap/padding checks, density targets and measured exceptions, generation
prompts/originals and surface mapping in the assigned Work directory.
Use independently image-generated textures in actual UE materials, with no
cross-effort/theme reading or reuse. No Forest beach requirement is added here.
The supervisor archives first evidence under Work/MountainStation/EFFORT/FirstDelivery
and preserves initial timings/commit/tokens. Record second-pass time/imagegen/UE
wait/run separately and supply actual same-camera before/after renders.
Workers still never commit. Both themes' second passes are required for completion.

## Authorized ultra self-improvement after the comparison experiment

Latest user overrides (2026-10-22 KST) permit the existing Forest ultra and
MountainStation ultra chats to start their self-improvement passes after each
job's own comparison result is validated, committed and preserved. Neither waits
for the other efforts or final eight-map integration. Keep their existing model
and ultra effort. Medium, high and xhigh receive no self-improvement assignment.
The supervisor dispatches each pass explicitly once and records it in
coordination.json; workers must not start or restart a pass on their own.

Preserve each committed comparison Content/map and FirstDelivery/TexturePass
evidence before editing. Task-specific implementation instructions are managed
by the coordinating conversation and coordination.json. Workers may prepare
native support proposals in their owned SelfImprovement directory, but shared
Source/Plugins/Config/Binaries integration remains the supervisor's responsibility.

Keep comparison results separate from self-improvement. Do not add improvement
plans, progress, results, timings or tokens to SUPERVISION.md, or overwrite its
linked FirstDelivery/TexturePass evidence. Before the full comparison is frozen,
the token collector honors coordination.comparison_token_cutoffs. Improvement
accounting must use -NoWrite -IgnoreComparisonCutoffs and save only under
Work/UltraImprovementAccounting. Once the full comparison is frozen, never write
SUPERVISION.md or its token_usage.json again. Record its commit and evidence hashes
in coordination.json. Final comparison integration uses preserved comparison
commits in supervisor scratch, without overwriting either active ultra result.

The separate supervisor report is ForestDemo/Work/ULTRA_IMPROVEMENT.md, with one
section per theme. Each ultra worker writes new scripts, source, STATUS/RESULT,
logs, validation and actual before/after renders under its own Work/SelfImprovement.
Keep the same owned Content root, map and scratch scope. No cross-effort or
cross-theme creative resource inspection or reuse is allowed. Preserve required
scene contents, 100x100m scope and calm rounded game art. Record selected issues,
changes, actual UTC/KST times, wall time, UE wait/run, image-generation time and
parent/verified-child token increments. The finite improvement pass is not an
unbounded loop. Scene evidence remains actual UE rendering.

The supervisor alone validates and commits each improved result and the separate
report. All eight maps remain. Apply the latest machine queue priority above
without preempting a running UE process. Monitor only unfinished chats; submitted
results awaiting supervisor review are not active worker jobs. The heartbeat
continues until both improvement results and the separate report are verified and
committed, even if comparison work finishes earlier.
