# ForestDemo reasoning-effort comparison

Supervisor setup started: 2026-10-21 21:09:14 KST (12:09:14 UTC).
Baseline: `7558c8f`. Four user-owned local chats, same configured default model,
with reasoning efforts medium, high, xhigh, ultra.

## Shared assignment

Independently build a 100 x 100 metre playable forest scene for UE 5.7, containing
a small lake, a distinct beach and suitable original props. Use softly rounded
forms and a restrained, calm game palette. Avoid cloud-shaped ornamentation,
faces, hearts, or similar decorative motifs. Natural atmospheric clouds are not
required. Scene design and prop construction are each worker's responsibility;
do not reuse another effort's work. Deliver a composed scene, not just a script.
Use UE centimetres (10,000 x 10,000 cm site), usable lighting, a player start,
appropriate ground collisions, and an intentional overview camera/viewpoint.
Preserve the baseline ScreenDebugLogger behavior in each map where practical.

## Isolation and integration

- Assets: `ForestDemo/Content/<effort>/**`.
- Map: `ForestDemo/Content/Maps/<effort>.umap`.
- Scripts, source artwork, evidence, result: `ForestDemo/Work/<effort>/**`.
- Private authoring project: `ForestDemo/Saved/Workers/<effort>/**` (ignored).
- Workers do not commit. Supervisor validates and commits each delivery separately.
- Keep baseline main during work. Once all four maps pass integration checks,
  supervisor retires main and selects medium as startup/default map in a separate
  integration commit, leaving exactly four scene maps.
- Do not change the selected effort or use subagents to create the scene; the
  comparison concerns each chat's own reasoning effort. No arbitrary time cap.

## Timing definitions

Dispatch time is when the supervisor requests chat creation. Worker active wall
time is actual worker start through its ready-for-review timestamp; it includes
tool waiting but excludes later supervisor review and commit time. Supervisor
also records dispatch-to-ready duration and commit time separately where available.
Missing timestamps remain unknown rather than estimated from a polling interval.

## Progress

| Effort | Chat | Dispatch (KST) | Worker start | Ready | Wall time | Status | Commit |
|---|---|---|---|---|---|---|---|
| medium | 01a15e5f-d4b8-7e53-b162-d84c019c5478 | 2026-10-21 12:11:37 | pending | pending | pending | working | pending |
| high | 01a15e5f-e4c8-7bc1-b8da-c01f6d6d175c | 2026-10-21 12:11:42 | pending | pending | pending | working | pending |
| xhigh | 01a15e5f-f174-72d3-bc4b-f9f812ebf7db | 2026-10-21 12:11:46 | pending | pending | pending | working | pending |
| ultra | 01a15e5f-fef9-7323-8733-3c0553c29d7e | 2026-10-21 12:11:49 | pending | pending | pending | working | pending |

## Supervisor log

- Prepared isolated ownership rules, per-worker delivery boundaries, and central
  commit control. Automatic follow-up will inspect progress and stay quiet unless
  completion, failure, a meaningful change, or a user decision needs attention.

- All four chats confirmed active. Supervisor heartbeat: forestdemo, every 5 minutes.
