# Quietwater Grove source workflow

All distances are centimetres. The site is centred at (0, 0), bounded by ±5000 in X/Y. The comparison camera ground reference is Z0 = 300. The ocean surface is Z = 78; the independent inland pond is Z = 162. No downloaded art, generated image substitutes, or other effort content is used.

`make_art.py` runs in a private Blender 4.5 background process. It writes the original `Source/QuietwaterGrove.blend`, 22 reusable FBX meshes, a muted colour palette, and deterministic placement manifest `scene.json`. The scene uses continuous sampled terrain, five tree variants, four mossy boulder variants, grass variants, fern, reeds, fallen log, bridge, trail marker, flower clump and ripple ribbons.

`bootstrap.py` extracts only baseline project Source/Config/uproject from commit 7558c8f and copies the existing baseline Binaries into `Saved/Workers/high/ForestDemo`. The scratch project keeps the same native module identity so ScreenDebugLogger works without rebuilding shared code. The current final asset root is `/Game/Forest/high`; the initial `/Game/high` root was migrated with Unreal APIs in `migrate_assets.py` after the user's path change.

`build_level.py` runs through UnrealEditor-Cmd in editor mode with `-ExecutePythonScript`, `-RenderOffscreen`, `-unattended`, `-nop4`, `-NoSound`. Legacy FBX import is selected in scratch DefaultEngine.ini with `Interchange.FeatureFlags.Import.FBX=0`; its editor subsystem is unavailable in pure commandlet mode. Imported FBX local Y is reflected, so the scene actors compensate with negative local Y scale. Terrain uses complex-as-simple collision; substantial props use convex collision; small foliage and water do not block.

`finalize_scene.py` records coordinate correction and landmark bounds. `validate_capture.py` reloads the saved level, recursively checks hard/soft /Game dependencies, checks footprint and collision, and renders clean 1920×1080 SceneCapture2D PNGs. Its HitResult native-break API is `hit.to_tuple()` in this engine version. The screenshot camera actor is transient and is never saved in the final map.

Required final assets are copied only after the private editor exits. The coordinating chat owns all Git staging and commits.
