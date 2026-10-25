# Set05 — Marine work

Four original rounded static mesh assets, produced from the main-owned [local reference images and prompts](REF/):

- [Catamaran workboat](catamaran_workboat/): separated twin hulls, pilothouse, winch, articulated deck crane, rails and marine fittings.
- [Underwater service robot](underwater_service_robot/): protective cage, buoyancy housing, four horizontal and two vertical thrusters, camera, manipulators and tether connector.
- [Docking lift platform](docking_lift_platform/): four load towers, overhead winches, cables, empty cradle, service walkways and operator booth.
- [Marine equipment workshop](marine_equipment_workshop/): barrel roof, two open maintenance bays, internal hoist, side office and ventilation.

Each asset folder contains its named `.blend`, `.glb`, `.fbx`, `metadata.json` and actual 960×960 `renders/hero.png` and `renders/rear.png`. BLEND keeps editable named meshes and rounding modifiers in `ASSET`; camera, lights and ground are in `STUDIO`. Exports contain asset geometry and solid PBR materials only. Units are meters; front is −Y, up is +Z. Per-component UVs use independent 0–1 layouts.

Review is **deferred_by_user**. Renders were generated for later review and not opened. No fresh reopen/reimport, geometry/UV validator or independent visual review was run. Production checks cover actual subprocess completion and required nonempty files only. [RESULT.md](RESULT.md), [STATUS.json](STATUS.json) and [delivery_manifest.json](delivery_manifest.json) record measured timing, outputs, file sizes, hashes and limitations.

Reproduce all four in independent background Blender 4.5.12 processes (four CPU threads each):

```powershell
& 'C:/Program Files/Blender Foundation/Blender 4.5/4.5/python/bin/python.exe' -X utf8 'D:/github/AstraEffort/Blender/Set05/run_build.py'
```

Geometry source: [build.py](build.py). Process wrapper: [run_build.py](run_build.py). Reference provenance remains in [REF/generation_manifest.json](REF/generation_manifest.json). No external model resources or texture dependencies were used.
