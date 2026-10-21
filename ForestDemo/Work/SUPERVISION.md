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
| medium | pending | pending | pending | pending | pending | preparing | pending |
| high | pending | pending | pending | pending | pending | preparing | pending |
| xhigh | pending | pending | pending | pending | pending | preparing | pending |
| ultra | pending | pending | pending | pending | pending | preparing | pending |

## Supervisor log

- Prepared isolated ownership rules, per-worker delivery boundaries, and central
  commit control. Automatic follow-up will inspect progress and stay quiet unless
  completion, failure, a meaningful change, or a user decision needs attention.
