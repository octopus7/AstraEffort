# Committed comparison integration

This supervisor-only workflow freezes all eight comparison scenes from an explicit
Git commit. It never copies current worker Content, saved editor state, or native
self-improvement proposals. Preparation and verification are separate commands.

1. Run `Prepare-ComparisonSnapshot.ps1 -BaselineCommit <full SHA> -ApplyFinalDefaults`.
   It creates a new `Saved/Workers/Supervisor/Integration-<SHA>-comparison/Project`, preserves
   the original Git archive and file inventory, then changes only its two default
   map settings to `/Game/Maps/medium` and removes its baseline `main.umap`.
   Shared Content/Source/Config are never changed. Existing snapshots are never
   overwritten. The existing baseline native binaries are copied only after every
   shared native Source matches the committed Source snapshot after LF normalization,
   with both raw hashes, canonical hashes, binary hashes and the original source
   commit recorded. This is not reproducible-build
   proof; the separate native Hello automation must pass.
2. Supervisor reviews `Evidence/baseline_snapshot.json`, `candidate_snapshot.json`,
   `native_binary_seed.json`, and `request.json`. The only baseline/candidate
   changes must be `Config/DefaultEngine.ini` and `Content/Maps/main.umap`.
3. Only after authorization, run `Run-ComparisonVerification.ps1 -RequestPath <request.json>`.
   Both UE processes use the existing serialized runner. The supervisor path has
   queue priority Unknown=2 and remains inside its orphan-process guard scope.
   Do not bypass a queue/CIM permission failure or terminate another UE process.
4. Review saved-map and native-automation reports and actual process logs. Exit 0
   alone is insufficient. The script requires eight successful saved-map loads,
   live configured medium defaults, native logger/PlayerStart presence, reflected
   non-WP, recursive ownership (including old roots and native module references),
   no redirectors/external/BuiltData, unchanged candidate hashes, and the exact
   native `HelloOnBeginPlay` automation Success marker.

This integration does not replace each worker's actual render, PIE and collision
evidence. It never claims an on-screen pixel observation from an automation test.
Initial startup world is recorded separately from loading the actual configured
default value. No UE launch occurs during preparation.

The optional `-SnapshotLabel` selects a new preserved snapshot name when a previous
preparation attempt exists; existing snapshots are never deleted automatically.
