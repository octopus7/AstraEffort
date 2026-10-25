# Set03 — urban maintenance

Status: **produced_unreviewed**. Review: **deferred_by_user**.

Four original editable rounded mesh assets, geometry-only GLB/FBX and neutral 960×960 studio renders. The images have been generated but not inspected.

| Asset | Editable / exports | Preview images for later review |
|---|---|---|
| street_sweeper | [BLEND](street_sweeper/street_sweeper.blend) · [GLB](street_sweeper/street_sweeper.glb) · [FBX](street_sweeper/street_sweeper.fbx) | [Hero](street_sweeper/renders/hero.png) · [Rear](street_sweeper/renders/rear.png) |
| pipe_inspection_robot | [BLEND](pipe_inspection_robot/pipe_inspection_robot.blend) · [GLB](pipe_inspection_robot/pipe_inspection_robot.glb) · [FBX](pipe_inspection_robot/pipe_inspection_robot.fbx) | [Hero](pipe_inspection_robot/renders/hero.png) · [Rear](pipe_inspection_robot/renders/rear.png) |
| road_maintenance_depot | [BLEND](road_maintenance_depot/road_maintenance_depot.blend) · [GLB](road_maintenance_depot/road_maintenance_depot.glb) · [FBX](road_maintenance_depot/road_maintenance_depot.fbx) | [Hero](road_maintenance_depot/renders/hero.png) · [Rear](road_maintenance_depot/renders/rear.png) |
| compact_pump_station | [BLEND](compact_pump_station/compact_pump_station.blend) · [GLB](compact_pump_station/compact_pump_station.glb) · [FBX](compact_pump_station/compact_pump_station.fbx) | [Hero](compact_pump_station/renders/hero.png) · [Rear](compact_pump_station/renders/rear.png) |

[Production record](RESULT.md) · [Status](STATUS.json) · [File inventory](delivery_manifest.json) · [Build source](build.py)

Reproduce all four with the bundled Python: `"C:/Program Files/Blender Foundation/Blender 4.5/4.5/python/bin/python.exe" -X utf8 run_batch.py`. This overwrites the owned generated files.

Native files separate `ASSET` and `STUDIO`. Each mesh part has a meaningful primitive, planar or parameterized UV layout. Materials are named solid PBR palette surfaces. Static assets only; no rig, animation, collision or LOD delivery.

Main-supplied design inputs are preserved in the local [REF folder](REF/): [sweeper](REF/street_sweeper.png), [inspection robot](REF/pipe_inspection_robot.png), [depot](REF/road_maintenance_depot.png), and [pump station](REF/compact_pump_station.png). These inputs are separate from the actual generated studio renders.
