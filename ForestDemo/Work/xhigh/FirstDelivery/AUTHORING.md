# Quiet Cove source and reproduction

All geometry was authored for xhigh in make_art.py using a separate Blender 4.5 background process. No downloaded art, generated-image assets, marketplace assets, or other effort's work was used. The engine's /Engine/MapTemplates/Sky/DaylightAmbientCubemap is referenced read-only for ambient lighting, within the allowed built-in asset scope.

SourceArt/QuietCove_Source.blend contains the mesh prototypes, terrain and water geometry. Individual selected-object FBX exports preserve material slots. scene_manifest.json carries the original palette, reusable mesh metadata, deterministic distribution, required regions and terrain samples.

make_art.py builds 28 original meshes with seed 82161: three broadleaf trees, two layered pines, four boulders, two pebble clusters, three grass clumps, fern, reeds, small flowers, shrub, fallen log, stump, bench, dock, terrain, lake, sea and three surf ribbons. Geometry has smoothed normals and organically varied silhouettes. Terrain vertex colors blend muted grass, sand and a winding footpath without imported textures.

build_scene.py imports into /Game/Forest/xhigh and saves /Game/Maps/xhigh. Existing materials are reused; FBX mesh sources are reimported when rebuilding. A clean private scratch project regenerates everything. Export applies a Y handedness compensation so FBX coordinates match the scene manifest in UE; collision samples verify this relationship. The script creates dynamic sun/sky, atmosphere, fixed manual exposure, PlayerStart, baseline ScreenDebugLogger and overview CameraActor. Decorative meshes use NoCollision; terrain, trunks, rock and timber use complex static collision.

validate_scene.py reloads the map, traverses all /Game package dependencies, checks dimensions and important actors, tests terrain collision at seven coordinates, verifies decorative collision profiles and confirms no World Partition/external actor packages. capture_entry.py performs this validation in a fresh editor and starts capture_scene.py, which produces actual clean UE renders plus a camera manifest.

runtime_validate.py then starts actual PIE, checks PlayerController/DefaultPawn possession and spawn, performs a runtime terrain query and two pawn sweeps, requests a separate native Hello screenshot, and ends PIE normally. polish_and_capture.py contains the render-review correction pass: named pin connection assertions, terrain vertex color, valid water normal graph and daylight ambient fill.

Run UE only through the supervisor's read-only Work/Tools/Run-UnrealIsolated.ps1 with the xhigh scratch project. All queues, engine logs and timing files belong under Saved/Workers/xhigh. Never open the shared project for saving. The source project and asset import metadata still point to this work directory; final game assets are self-contained .uasset/.umap files.

Known scope: this is an environment level with baseline pawn behavior. It has no bespoke walking character, water buoyancy/swimming logic, AI navigation build or packaged-game performance certification. Water surfaces are opaque stylized materials; no third-party Water plugin dependency is introduced.
