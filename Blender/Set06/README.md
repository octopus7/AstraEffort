# Set06 — Forestry care

Four original ordinary rounded game meshes. Status and review state are recorded in [STATUS.json](STATUS.json); production timing and limitations are in [RESULT.md](RESULT.md). Review is deferred by user instruction.

| Asset | Reference / prompt | Editable / interchange | Actual studio renders | Production metadata |
|---|---|---|---|---|
| Tree transplanter | [PNG](REF/tree_transplanter.png) · [prompt](REF/tree_transplanter.prompt.txt) | [BLEND](tree_transplanter/tree_transplanter.blend) · [GLB](tree_transplanter/tree_transplanter.glb) · [FBX](tree_transplanter/tree_transplanter.fbx) | [Hero](tree_transplanter/renders/hero.png) · [Rear](tree_transplanter/renders/rear.png) | [JSON](tree_transplanter/metadata.json) |
| Nursery carrier robot | [PNG](REF/nursery_carrier_robot.png) · [prompt](REF/nursery_carrier_robot.prompt.txt) | [BLEND](nursery_carrier_robot/nursery_carrier_robot.blend) · [GLB](nursery_carrier_robot/nursery_carrier_robot.glb) · [FBX](nursery_carrier_robot/nursery_carrier_robot.fbx) | [Hero](nursery_carrier_robot/renders/hero.png) · [Rear](nursery_carrier_robot/renders/rear.png) | [JSON](nursery_carrier_robot/metadata.json) |
| Arched nursery greenhouse | [PNG](REF/arched_nursery_greenhouse.png) · [prompt](REF/arched_nursery_greenhouse.prompt.txt) | [BLEND](arched_nursery_greenhouse/arched_nursery_greenhouse.blend) · [GLB](arched_nursery_greenhouse/arched_nursery_greenhouse.glb) · [FBX](arched_nursery_greenhouse/arched_nursery_greenhouse.fbx) | [Hero](arched_nursery_greenhouse/renders/hero.png) · [Rear](arched_nursery_greenhouse/renders/rear.png) | [JSON](arched_nursery_greenhouse/metadata.json) |
| Forest watchtower | [PNG](REF/forest_watchtower.png) · [prompt](REF/forest_watchtower.prompt.txt) | [BLEND](forest_watchtower/forest_watchtower.blend) · [GLB](forest_watchtower/forest_watchtower.glb) · [FBX](forest_watchtower/forest_watchtower.fbx) | [Hero](forest_watchtower/renders/hero.png) · [Rear](forest_watchtower/renders/rear.png) | [JSON](forest_watchtower/metadata.json) |

[Source authoring script](build.py) · [Isolated subprocess runner](run_build.py) · [Process records](process_records.json) · [Delivery inventory](delivery_manifest.json) · [Main reference generation record](REF/generation_manifest.json)

Each BLEND separates ASSET from STUDIO. GLB and FBX export only selected ASSET meshes. Named solid-color PBR materials and per-component UVs are authored in meters. The two vehicles and two facilities are independent assets; no shared diorama is exported.

The renderer uses Cycles CPU, four threads, 24 samples with denoising, 960 × 960 orthographic framing, neutral ground and three broad area lights. Hero and rear PNGs are real Blender renders reserved for later review. They were not opened by the worker. Visual inspection, reopen/import checks and geometry/UV validation remain deferred.

Reproduce one asset with Blender 4.5.12:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe' --background --factory-startup --threads 4 --python-exit-code 1 --python 'D:/github/AstraEffort/Blender/Set06/build.py' -- tree_transplanter
```

The complete runner deliberately writes all four owned output directories. Do not rerun frozen outputs without a new dispatch. This set's references are read-only, main-owned inputs. No other set or voxel/ForestDemo resource is required.
