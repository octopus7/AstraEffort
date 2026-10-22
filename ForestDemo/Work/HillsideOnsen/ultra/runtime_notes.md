# Native Character runtime probe — technical handoff

**PIE duplication correction after verify_02:** the actual report recorded all seven prepared editor Characters, but the completed PIE world contained none of their tags. The parent successfully duplicated its nontransient capture actor. The probe now explicitly passes `bTransient=False` so its temporary Characters are included in PIE duplication. No save is performed after preparation; the private verification process exits without saving, and the parent compares package hashes. PIE Character paths and tags are additionally recorded before route selection. Syntax/import and pure measurement checks passed after this change; actual movement still requires the next parent UE run.

**API correction after the parent's actual verify01 run:** that run demonstrated that `GameplayStatics.begin_deferred_actor_spawn_from_class` and `GameplayStatics.break_hit_result` are absent from the Python library class. Installed `PyGenUtil.cpp:1615` explicitly filters `BlueprintInternalUseOnly`, `NativeBreakFunc`, and `NativeMakeFunc`. The runtime module now preplaces one tagged, temporary native Character per supplied route using the exposed `EditorActorSubsystem.spawn_actor_from_class(..., False)` before requesting PIE, then discovers the PIE duplicates by tag. All unused Characters have NoCollision, MOVE_NONE, disabled movement ticks and auto-activation, and no auto possession. Each selected route activates its own Character in place; no position setters are used. `HitResult.to_tuple()` exposes the registered native break outputs and replaces the missing library method. The parent handles the corresponding static-validator correction and the next actual engine run. Earlier source-header availability claims below must be read with this correction.

`runtime_probe.py` provides `start_runtime_probe(editor_world, routes, output_path, on_done=None)`.
The return value is a retained asynchronous `RuntimeProbe`. The callback receives the final report dictionary after JSON has been written. The module does not save any level, start an external UE process, request editor shutdown, or end PIE. The caller owns those lifecycle steps.

The module is source-audited against this machine's installed UE 5.7. Python syntax and pure route-validation/measurement helper checks passed using the engine's bundled Python. **No Unreal process was launched by this technical subtask. No route or collision test has yet been demonstrated in UE by these offline checks.** The parent's actual full-editor run must establish that evidence; `status=passed` requires actual progressing game-time samples and native Character motion.

## Integration

Import the module by adding only this assigned work folder to `sys.path`. Before calling it, load/save the finished map in the private project and obtain `editor_world` from `unreal.UnrealEditorSubsystem.get_editor_world()` while PIE is not active. The probe explicitly rejects existing PIE/SIE so it can request a known PlayInEditor session itself.

For `-ExecutePythonScript`, call `unreal.EditorPythonScripting.set_keep_python_script_alive(True)` in the bootstrap and then let the bootstrap return. A blocking Python polling/sleep loop prevents the necessary editor/game ticks. The source class is named `UEditorPythonScriptingLibrary`, but its **Python ScriptName is `EditorPythonScripting`**. Set keep-alive false only after the parent's asynchronous capture/validation work is finished, or quit explicitly.

Each route is a dictionary with:

- `name`: unique route name.
- `points`: two or more `[x, y, z]` positions in UE centimeters; **Z is the expected walkable surface height**, not capsule center. Each horizontal leg must be at least 50 cm.
- Optional `waypoint_tolerance_cm` (default 30), `surface_z_tolerance_cm` (35), `minimum_grounded_ratio` (0.90), `timeout_game_seconds`, `minimum_motion_cm`.
- Optional `obstacle_point`: location on a known solid obstacle's near face; the final waypoint must lie beyond the obstacle. This converts the route into an expected-stop test. Optional `obstacle_actor_label` requires the exact runtime actor label. `obstacle_tolerance_cm` defaults to 100 horizontally. Use a clear flat approach at least 150 cm long and a tall wall/rock face, not a climbable 35 cm step. The obstacle is supplied by the authored scene; the probe creates no obstacle geometry.

Use separate representative open-straight, continuous-ramp, and obstacle routes. Do not put corners through geometry: intermediate points explicitly describe each turn. No navigation mesh is required. The native Character walks directly toward the next point, with horizontal `add_movement_input`, normal floor projection, gravity and sweep collision. A ramp route's expected versus measured elevation change is visible in its point specification and `measurement.observed_elevation_change_cm`.

The full editor needs an active level viewport. `-run=pythonscript` commandlet mode is not sufficient. A single-player local PIE session is intended; networked/multiple-client PIE is outside this probe's verification scope. The parent must launch all Unreal processes through the assigned isolated runner. The module never launches one itself.

## What constitutes evidence

Before PIE, the probe uses `EditorActorSubsystem.spawn_actor_from_class` with `bTransient=False` to place a **distinct native `/Script/Engine.Character` for each route**. It finds the copied Characters in the distinct `UEDPIE_` world by unique tags and verifies their inactive positions have not moved before activation. Capsule radius is 28 cm, half-height 88 cm, walking speed 250 cm/s, maximum step 35 cm and maximum walkable slope 45 degrees. The Character has no visible skeletal mesh. This is capsule-based movement evidence rather than an animated avatar presentation. The temporary editor preparation is never saved; parent package hashes independently verify that saved content remains unchanged.

If the PIE player controller exists, it possesses the probe Character and possession is checked. The original PIE pawn's collision is temporarily disabled so it cannot obstruct the test; collision and possession are restored on completion. If no controller exists, `run_physics_with_no_controller=True` allows native CharacterMovement to process input and physics. No scene collision is disabled. `default_land_movement_mode` and the initial movement mode are WALKING; they are not continuously forced. Falling, floor support and nonwalking states are observed afterward.

Each route first requires 0.5 game seconds of grounded settling at the requested start height. The walk then records each observed advancing game tick: center/foot position, velocity, movement mode, falling/flying/swimming, movement base, target and previous input. A successful walk requires waypoint arrival at the expected surface height, at least five observed walk/input ticks, measured horizontal movement, the specified grounded ratio, and no suspicious positional discontinuity. There is no `set_actor_location`, `set_actor_transform`, navigation teleport, flying movement, or direct velocity assignment used to make progress. Activating the next preplaced Character is explicitly recorded as a reset, not counted as travel.

An obstacle pass additionally requires the Character to remain grounded and within a 4 cm horizontal window for at least one game second while input continues, horizontal speed at most 5 cm/s, and a contemporaneous native **capsule query** using the same Pawn profile. The query must identify a nonpenetrating, opposed blocking hit within 6 cm capsule travel and near the expected face, with matching actor label if provided. JSON calls this `capsule_trace_by_Pawn_profile_at_observed_character_position`; it does **not** claim an `OnComponentHit` event. This avoids a sparse-delegate Python binding limitation found during source inspection. It combines actual blocked motion with scene collision identification; a trace by itself is not accepted as runtime walking proof.

Failure paths include no PIE within 60 wall seconds, non-PIE world, lost PIE, stopped game clock, no ground support, incorrect surface height, falling below route, flying/swimming, timeout, no real progress, unexpected obstacle traversal, API exceptions and overall watchdog expiry. The callback is unregistered on completion. The JSON keeps per-route samples and blockers; read every route, not only the top-level `blockers` array. The module leaves PIE running for the caller.

## Installed API evidence

All paths below are local under `C:/Program Files/Epic Games/UE_5.7/Engine/`; line numbers were inspected during this subtask.

| Source path and line | Evidence |
|---|---|
| `Source/Editor/LevelEditor/Public/LevelEditorSubsystem.h:77` | `EditorRequestBeginPlay` is `BlueprintCallable`; Python name is `editor_request_begin_play`. |
| `Source/Editor/LevelEditor/Private/LevelEditorSubsystem.cpp:264` | Implementation obtains an active editor viewport and explicitly sets `EPlaySessionWorldType::PlayInEditor`; the separate `EditorPlaySimulate` implementation at 195 sets `SimulateInEditor`. |
| `Source/Editor/UnrealEd/Public/Subsystems/UnrealEditorSubsystem.h:49` | `GetGameWorld` is callable. |
| `Source/Editor/UnrealEd/Private/Subsystems/UnrealEditorSubsystem.cpp:20` | Editor `GetGameWorld` obtains `GEditor->GetPIEWorldContext()->World()`, not the editor world. |
| `Source/Runtime/Engine/Classes/Kismet/GameplayStatics.h:66` | Deferred spawn and finish-spawn have `BlueprintInternalUseOnly` and are not Python-exported. The module no longer calls them. |
| `Source/Editor/UnrealEd/Public/Subsystems/EditorActorSubsystem.h:227` | Exposed `SpawnActorFromClass` accepts class, location, rotation and `bTransient`; the module calls it before PIE. |
| `Source/Runtime/Engine/Classes/GameFramework/Character.h:240` | Native Character is a nonabstract `UCLASS`, BlueprintType, with walking ability; `CharacterMovement` and `CapsuleComponent` reflected properties are at 260 and 264. |
| `Source/Runtime/Engine/Classes/Components/CapsuleComponent.h:47` | `SetCapsuleSize` callable; actual scaled radius/half-height getters at 98 and 105. |
| `Source/Runtime/Engine/Classes/GameFramework/CharacterMovementComponent.h:494` | `bRunPhysicsWithNoController` explicitly supports movement without a controller; reflected read/write at 500. |
| `Source/Runtime/Engine/Classes/GameFramework/CharacterMovementComponent.h:1256` | `SetMovementMode` is exposed; `GetMovementBase` at 1383, `SetWalkableFloorAngle` at 1927. |
| `Source/Runtime/Engine/Classes/GameFramework/Pawn.h:475` | Character automatically handles AddMovementInput; exposed signature at 483. |
| `Source/Runtime/Engine/Classes/GameFramework/Controller.h:205` | `K2_GetPawn` has explicit ScriptName `GetControlledPawn`, hence Python `get_controlled_pawn`; `Possess` is exposed at 280. |
| `Source/Runtime/Engine/Classes/GameFramework/NavMovementComponent.h:171` | Falling, grounded, swimming and flying accessors are exposed. |
| `Source/Runtime/Engine/Private/Components/CharacterMovementComponent.cpp:3766` | Grounded predicate checks walking/navwalking mode plus updated component; probe additionally requires a non-null movement base. |
| `Source/Runtime/Engine/Classes/Kismet/KismetSystemLibrary.h:1620` | `CapsuleTraceSingleByProfile` accepts world, start/end, radius, half-height, profile, complex flag, ignore list and debug mode. Probe uses simple collision and Pawn profile. |
| `Source/Runtime/Engine/Classes/Kismet/GameplayStatics.h:1079` | `BreakHitResult` defines the 18 native break fields; it is not a Python class method. `HitResult.to_tuple()` uses this registered native break. |
| `Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyWrapperStruct.cpp:995` | `to_tuple()` delegates to `BreakStruct`; known HitResult indices are 0 blocking, 1 overlap, 3 distance, 5 impact point, 7 impact normal, 9 actor, 10 component. |
| `Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyGenUtil.cpp:1615` | Python function exposure excludes `BlueprintInternalUseOnly`, `NativeBreakFunc` and `NativeMakeFunc`; header BlueprintCallable alone does not prove Python availability. |
| `Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyGenUtil.cpp:1150` | `PackReturnValues` converts bool-plus-output functions to output on true or None on false. Therefore capsule trace returns `HitResult` or None, not `(bool, HitResult)`. |
| `Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyConversion.cpp:1144` | Explicit TODO says sparse delegates are not handled. `OnComponentHit` is declared as sparse in `PrimitiveComponent.h:229`; the module therefore does not depend on that callback. |
| `Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PySlate.cpp:198` | Exact exported `register_slate_pre_tick_callback(callable)` and `unregister_slate_pre_tick_callback(handle)` signatures. Callable receives one float. |
| `Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyWrapperObject.cpp:1129` | `get_world()` is available on Python wrapped objects. |
| `Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/EditorUtilities/EditorPythonScriptingLibrary.h:12` | `ScriptName="EditorPythonScripting"`; `SetKeepPythonScriptAlive` is exposed at 30 and documented as controlling automatic editor close. |
| `Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/EditorUtilities/EditorPythonExecuter.cpp:73` | The command-line script executor exits when keep-alive is false. |

## Checks actually performed

The engine-bundled standalone Python executable parsed the module and imported it without Unreal bindings, using `sys.dont_write_bytecode=True` so no additional files were authored. Pure helper checks confirmed a two-leg 600 cm route length, rejection of empty/single-point/vertical-only/nonfinite routes, rejection of waypoint tolerance exceeding leg length, nonpositive timeouts and invalid grounded thresholds. Independently specified sample data produced 400 cm measured horizontal travel, 80 cm elevation gain and a 0.5 grounded-time ratio. A 2000 cm one-second positional discontinuity was flagged. Empty/zero-duration samples could not claim grounded walking. These are code checks, not simulated UE evidence.

Only `runtime_probe.py` and this note were authored by the technical subtask. It did not inspect other efforts/themes, mutate shared assets/configuration, execute Unreal, or run Git mutations.
