# Set04 — Aerial logistics

Status: **produced_unreviewed**. Review: **deferred_by_user**.

Four original ordinary rounded mesh models, with named editable parts, individually authored component UVs and a warm ivory / slate blue / graphite / ochre PBR palette. Local [reference images and prompts](REF/) informed the silhouettes; no source meshes or other sets were read or reused. Native files separate ASSET and STUDIO. GLB and FBX export only selected asset meshes.

| Asset | Geometry | Actual studio renders | Design input |
|---|---|---|---|
| `twin_rotor_cargo_drone` | [BLEND](twin_rotor_cargo_drone/twin_rotor_cargo_drone.blend) · [GLB](twin_rotor_cargo_drone/twin_rotor_cargo_drone.glb) · [FBX](twin_rotor_cargo_drone/twin_rotor_cargo_drone.fbx) | [hero](twin_rotor_cargo_drone/renders/hero.png) · [rear](twin_rotor_cargo_drone/renders/rear.png) | [reference](REF/twin_rotor_cargo_drone.png) |
| `airport_cargo_tug` | [BLEND](airport_cargo_tug/airport_cargo_tug.blend) · [GLB](airport_cargo_tug/airport_cargo_tug.glb) · [FBX](airport_cargo_tug/airport_cargo_tug.fbx) | [hero](airport_cargo_tug/renders/hero.png) · [rear](airport_cargo_tug/renders/rear.png) | [reference](REF/airport_cargo_tug.png) |
| `circular_drone_hangar` | [BLEND](circular_drone_hangar/circular_drone_hangar.blend) · [GLB](circular_drone_hangar/circular_drone_hangar.glb) · [FBX](circular_drone_hangar/circular_drone_hangar.fbx) | [hero](circular_drone_hangar/renders/hero.png) · [rear](circular_drone_hangar/renders/rear.png) | [reference](REF/circular_drone_hangar.png) |
| `low_control_building` | [BLEND](low_control_building/low_control_building.blend) · [GLB](low_control_building/low_control_building.glb) · [FBX](low_control_building/low_control_building.fbx) | [hero](low_control_building/renders/hero.png) · [rear](low_control_building/renders/rear.png) | [reference](REF/low_control_building.png) |

The renders are actual Cycles CPU images at 960 × 960, 40 samples and four threads. They were generated for later review and were not opened or inspected. Only Blender subprocess completion and the existence of the 24 expected nonempty output files were checked. No fresh BLEND reopening, GLB/FBX reimport, geometry/UV validators or reviewer tasks were performed. Byte counts and SHA256 entries in [delivery_manifest.json](delivery_manifest.json) are an inventory, not independent validation.

Each asset's metadata records authored scene dimensions, parts and material values, UV method, camera settings and actual render timing. UVs use separate per-component surface islands after bevel authoring; overlap, stretch and export roundtrip quality remain unreviewed. Materials are solid PBR colors with opaque stylized glazing. No texture maps, rigs, animation, collision or LODs are supplied. Unseen rear structures are original functional interpretations.

Recorded work start: 2026-10-25T05:40:53+00:00 UTC / 2026-10-25T14:40:53+09:00 KST. Finish: 2026-10-25T05:48:36.162220+00:00 UTC / 2026-10-25T14:48:36.162220+09:00 KST. Wall: 463.162 s. Blender subprocess total: 216.038 s. Detailed per-asset timings: [process_timings.json](process_timings.json). Recorded work start is the initial clock checkpoint during the task setup.

Reproduction: [build.py](build.py), driven by [run_build.py](run_build.py), using Blender 4.5.12 background factory startup with four threads. Build logs are in [logs/](logs/). No image generation, installation, shared live Blender session, Git operation or sub-agent was used. This set is frozen after production pending the main coordinator's group commit.
