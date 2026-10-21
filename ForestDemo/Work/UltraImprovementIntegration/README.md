# Shared native integration smoke (prepared; UE not run by author)

Run only after the final owned ultra publication and supervisor shared build succeed. This is a short integration check, not a replacement for the worker's feature/render/collision evidence. Run **ultra and medium in separate fresh processes**. Never open the shared project with UE. No project/config/plugin changes are made by the script.

## Prepare a supervisor private project

Use a project beneath `ForestDemo/Saved/Workers/Supervisor/`. Copy the supervisor's built shared project modules/config and enabled plugins with their matching module manifests. In particular, copy the actual shared `Plugins/ForestUltraTrees` source, shaders, descriptor, `Binaries/Win64/UnrealEditor-ForestUltraTrees.dll` and `UnrealEditor.modules` unchanged. Do not rebuild this copy. Include the published `/Game/Forest/ultra`, `/Game/Forest/medium`, `/Game/Maps/ultra`, `/Game/Maps/medium` packages. The script checks the selected map and its recursive own asset files against shared bytes at execution time. Keep the startup map empty/neutral so the medium process has never loaded ultra. PythonScriptPlugin and editor scripting must be enabled in this private project.

Prepare two JSON requests with unique output paths, for example:

```json
{
  "project": "D:/github/AstraEffort/ForestDemo/Saved/Workers/Supervisor/NativeSmoke/ForestDemo.uproject",
  "shared_project": "D:/github/AstraEffort/ForestDemo/ForestDemo.uproject",
  "case": "ultra",
  "output": "D:/github/AstraEffort/ForestDemo/Saved/Workers/Supervisor/NativeSmoke/ultra-smoke.json"
}
```

The second request uses `case: "medium"` and a distinct output. The environment variable `FOREST_ULTRA_SMOKE_REQUEST` contains the absolute JSON request path, inherited by UE. Use the supervisor-owned `Work/Tools/Run-UnrealIsolated.ps1` with the request's private `-Project`, separate `-LogPath`/`-TimingPath`, and editor arguments:

```powershell
$env:FOREST_ULTRA_SMOKE_REQUEST = 'D:/absolute/supervisor/request-ultra.json'
# Execute only when supervisor authorizes the actual smoke run:
# -EditorArguments @('-ExecutePythonScript=D:/github/AstraEffort/ForestDemo/Work/UltraImprovementIntegration/smoke_native.py', '-RenderOffscreen', '-d3d12', '-sm5')
```

Do not use `-nullrhi`, `-run=pythonscript`, another concurrent script, or an added quit command. This script uses `-ExecutePythonScript` editor ticks, sets `set_keep_python_script_alive(True)`, starts PIE, waits at least 30 callbacks, requests EndPIE, confirms the PIE world is gone, drains another 30 callbacks, then clears keep-alive for the command's built-in next-tick exit. It never calls synchronous `quit_editor()`. There is a 180-second phase deadline and 30-second EndPIE deadline, evaluated on ticks; a hung engine with no ticks still needs external supervision.

## Acceptance and honest scope

Require both output JSON `success: true`, both runner timing exit codes 0, and logs without fatal/failed native load/shader compile failures. A missing output is failure even if process exit is 0. The script cannot record its own eventual process exit. Retain requests, logs, timings and outputs outside the frozen comparison report.

- Confirms the actual loaded DLL Windows module path is the private plugin DLL and its SHA256 equals the shared build. Compares plugin source/shaders/descriptor/module manifest too.
- Loads the native actor class, disallows original TunaSweeper/CanopyRim/Environment references in active private project/plugin INI lines and recursive registry dependencies. This is scoped evidence, not a claim to enumerate the engine's entire redirect table.
- Scans all assets under the selected own root plus its map. Recursively checks hard/soft package and management references, own-root boundaries, saved file hashes, own-root redirectors, loaded world identity and direct WorldPartition None. Searchable-name relationships are excluded.
- In editor and actual possessed PIE: ultra has 63 native trees, each with 10 leaves, 10 tagged shadow proxies, BlockAll trunk, enabled custom depth and one unique valid stencil ID. Medium has zero native tree actors. No new camera captures, pawn travel, full collision-route test or parameter mutation are performed.
- **Medium renderer inactivity is source-backed inference, not a GPU measurement.** Styles/Owners are private and not reflected; no public style-count/pass-counter getter exists. The identical subsystem source initializes zero styles and the identical view-extension source only subscribes when a style has positive W. A fresh medium world with no native trees therefore meets the empty-style/no-subscription condition. No claim of zero subsystem objects, direct render-thread inspection, zero GPU timings or shader absence is made.

## API source verification

Verified against installed UE 5.7 headers/sources: `Engine/Source/Editor/LevelEditor/Public/LevelEditorSubsystem.h` (LoadLevel, EditorRequestBeginPlay/EndPlay, IsInPlayInEditor); `Engine/Source/Editor/UnrealEd/Public/Subsystems/UnrealEditorSubsystem.h` (GetEditorWorld/GetGameWorld); PythonScriptPlugin `EditorPythonScriptingLibrary.h` and `PySlate.cpp` (keep-alive and Slate callbacks); `IAssetRegistry.h` (dependencies/options); `BlueprintPathsLibrary.h`, `GameplayStatics.h`, Controller/Actor/PrimitiveComponent/World headers. Plugin reflected actor properties/GetLeafClumps and private style guard were read directly from the shared plugin source. No worker scripts were copied.

Offline checks (no Unreal imported/launched):

```powershell
& 'C:/Program Files/Epic Games/UE_5.7/Engine/Binaries/ThirdParty/Python3/Win64/python.exe' 'D:/github/AstraEffort/ForestDemo/Work/UltraImprovementIntegration/smoke_native.py' --self-test
```

This tests rejection of shared-project execution, sibling-prefix escape, foreign output, invalid map case and foreign/legacy asset roots. Runtime Python bindings and eventual editor exit still require the authorized smoke execution.
