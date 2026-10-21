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

The first UE attempt is preserved under `Evidence/Attempts/attempt01`, including
exact logs, reports, source scripts and an archive hash manifest. Its Python API
failure and native shutdown exit `-1073741819` are failures; the native exit's cause
has not been established. The helper now propagates the native exit explicitly.
`Test-ExitPropagation.ps1 -EvidenceDirectory <Evidence>` checks that behavior in
separate PowerShell processes with a fake runner; it never launches UE.

SoftObjectPath conversion uses `value.to_tuple()` and validates its one-string
shape. Installed UE source connects `SoftObjectPath.h`'s `HasNativeBreak` metadata
to `PyWrapperStruct.cpp`'s `to_tuple` implementation. `PyGenUtil.cpp` excludes
`NativeBreakFunc` from direct Python functions, so `SystemLibrary.break_soft_object_path`
is unavailable despite its C++ declaration. Runtime type/shape diagnostics are
recorded with the default-map checks.

The second attempt is preserved under `Evidence/Attempts/attempt02`. All eight
saved-map checks passed and the 1,756 candidate file hashes were unchanged, but
the process again returned access violation `-1073741819` after its log closed.
The exit-code gate correctly stopped the workflow before Hello automation.

The next controlled change removes only the final direct `quit_editor()` call.
Installed UE 5.7 source at
`Engine/Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/EditorUtilities/EditorPythonExecuter.cpp:44-47`
states that a full tick must occur after Python execution before closing the
editor. Its `RequestExit()` at lines 119-125 defers `QUIT_EDITOR`; the script now
returns to that built-in `-ExecutePythonScript` lifecycle. The direct API instead
calls `GEngine->Exec` immediately (`Engine/Source/Runtime/Engine/Private/KismetSystemLibrary.cpp:650`).
This identifies a lifecycle difference, not a proven cause of the access
violation. No crash stack was available; the repeated nonzero exit remains a
failure until a new controlled run exits normally. Saved-map assertions and the
native process exit-code gate are unchanged.
