# Set08 — Materials processing

Four original ordinary rounded mesh game assets. Palette: muted steel blue, warm pale gray, graphite, brushed steel and restrained copper-orange. Front is **-Y**, up is **Z**, and authored dimensions use meters.

| Asset | Local reference and prompt | Editable model | Geometry exports | Actual studio renders | Production metadata |
|---|---|---|---|---|---|
| Articulated welding mech | [Image](REF/articulated_welding_mech.png) · [Prompt](REF/articulated_welding_mech.prompt.txt) | [BLEND](articulated_welding_mech/articulated_welding_mech.blend) | [GLB](articulated_welding_mech/articulated_welding_mech.glb) · [FBX](articulated_welding_mech/articulated_welding_mech.fbx) | [Hero](articulated_welding_mech/renders/hero.png) · [Rear](articulated_welding_mech/renders/rear.png) | [JSON](articulated_welding_mech/metadata.json) |
| Cylindrical mixer | [Image](REF/cylindrical_mixer.png) · [Prompt](REF/cylindrical_mixer.prompt.txt) | [BLEND](cylindrical_mixer/cylindrical_mixer.blend) | [GLB](cylindrical_mixer/cylindrical_mixer.glb) · [FBX](cylindrical_mixer/cylindrical_mixer.fbx) | [Hero](cylindrical_mixer/renders/hero.png) · [Rear](cylindrical_mixer/renders/rear.png) | [JSON](cylindrical_mixer/metadata.json) |
| Rounded foundry workshop | [Image](REF/rounded_foundry_workshop.png) · [Prompt](REF/rounded_foundry_workshop.prompt.txt) | [BLEND](rounded_foundry_workshop/rounded_foundry_workshop.blend) | [GLB](rounded_foundry_workshop/rounded_foundry_workshop.glb) · [FBX](rounded_foundry_workshop/rounded_foundry_workshop.fbx) | [Hero](rounded_foundry_workshop/renders/hero.png) · [Rear](rounded_foundry_workshop/renders/rear.png) | [JSON](rounded_foundry_workshop/metadata.json) |
| Vertical material tower | [Image](REF/vertical_material_tower.png) · [Prompt](REF/vertical_material_tower.prompt.txt) | [BLEND](vertical_material_tower/vertical_material_tower.blend) | [GLB](vertical_material_tower/vertical_material_tower.glb) · [FBX](vertical_material_tower/vertical_material_tower.fbx) | [Hero](vertical_material_tower/renders/hero.png) · [Rear](vertical_material_tower/renders/rear.png) | [JSON](vertical_material_tower/metadata.json) |

The local [reference generation record](REF/generation_manifest.json) and all `REF/` files are parent-supplied, read-only design inputs. Original references also remain in [../../REF/Set08](../../REF/Set08).

Each native scene keeps named editable mesh parts and edge-bevel construction in **ASSET**. **STUDIO** contains only the neutral floor, soft area lights and orthographic cameras. Exports select ASSET meshes, with solid PBR materials, excluding studio geometry, lights and cameras. Per-component `UVMap` layouts are authored with angle-based projection and 2.5% island margin. No generated surface textures are used.

Production source: [build.py](build.py). Process runner: [run_builds.py](run_builds.py). [STATUS.json](STATUS.json), [RESULT.md](RESULT.md), [delivery_manifest.json](delivery_manifest.json) and [logs/](logs/) record actual timestamps, durations, subprocess return codes, expected file presence, sizes and hashes.

To reproduce in the assigned environment:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 4.5/4.5/python/bin/python.exe' -X utf8 'D:/github/AstraEffort/Blender/Set08/run_builds.py'
```

Each asset uses a separate Blender 4.5.12 process with `--background --factory-startup --threads 4 --python-exit-code 1`. Actual Cycles CPU renders are 960×960, 40 samples with denoising, neutral studio lighting, and matching front/rear three-quarter orthographic framing.

Review is **deferred by user instruction**. Generated previews have not been inspected; no fresh BLEND reopen, GLB/FBX reimport, geometry or UV validator, or reviewer agent was used. Completion checks cover only process return codes and expected nonempty files. The SHA256 manifest is an inventory, not a validation claim. Assets are static: no rigging, animation, collision or LODs.
