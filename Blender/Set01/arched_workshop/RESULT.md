# Arched Workshop — delivery result

Status: complete; final model and renders approved by the parent after its independent visual and file checks. No model/export/render changes remain pending.

Recorded work start: **2026-10-23 09:37:09 UTC / 2026-10-23 18:37:09 KST** (reference inspection and start clock sample).  
Recorded finish: **2026-10-23 10:07:26 UTC / 2026-10-23 19:07:26 KST**.  
Elapsed wall time: **1817 seconds**.  
Final full build: 2026-10-23 09:56:25.640754–09:59:45.050914 UTC (199.410160 seconds).  
Final lighting capture: 2026-10-23 10:02:08.647708–10:04:13.565576 UTC.  
Final fresh-process validation began at 2026-10-23 10:04:28.808389 UTC; exit code 0.

## Deliverables

All paths are under `D:/github/AstraEffort/Blender/Set01/arched_workshop/`.

| File | Purpose | Size |
|---|---|---:|
| [arched_workshop.blend](arched_workshop.blend) | Editable named asset components plus separate studio | 15,647,833 bytes |
| [arched_workshop.glb](arched_workshop.glb) | Selected ASSET geometry and PBR materials | 5,368,372 bytes |
| [arched_workshop.fbx](arched_workshop.fbx) | Selected ASSET geometry and materials | 5,892,636 bytes |
| [build.py](build.py) | Complete deterministic authoring/export/render source | 39,643 bytes |
| [finish_lighting.py](finish_lighting.py) | Recorded final studio-only lighting correction | 2,163 bytes |
| [validate.py](validate.py) | Fresh native/export reopening and geometry checks | 7,826 bytes |
| [validation.json](validation.json) | Per-format measurements and SHA-256 checksums | Final passing report |
| [capture_manifest.json](capture_manifest.json) | Actual camera/settings/timestamp evidence | Three final views |
| [renders/hero.png](renders/hero.png) | Front-left actual Blender render | 1440 × 1080 |
| [renders/rear.png](renders/rear.png) | Rear-right actual Blender render | 1440 × 1080 |
| [renders/front_detail.png](renders/front_detail.png) | Lower front view showing the interior bench and vice | 1440 × 1080 |

The final three images were personally viewed through the image tool. The parent also inspected these three images and reported approval. Earlier build/validation logs and `validation_initial.json` preserve the initial findings; `validation.json` is the current final result. The automatically created `.blend1` is a backup, not a deliverable.

## Geometry and evidence

- **558 asset meshes; 184,984 evaluated triangles** in the saved BLEND and both imported exports. No unapplied asset modifiers.
- Overall bounds, including service cabinets, guttering and ramp: **7.489045 × 6.400000 × 4.499392 m**. Main shell: approximately 6.7 × 5.0 m. Asset minimum Z is exactly 0; front is negative Y. Native scene uses meters and Z up; GLB uses the format's standard coordinate conversion.
- True barrel-vault roof sheet, 17 curved standing seams, segmented thick ivory arch fascias and modeled gable infill. Geometry follows the barrel curve rather than using a shaped image.
- Masonry sections surround a genuine garage aperture. A lower ray passes through the façade and reaches the interior workbench at Y=1.3503 m; an upper ray hits the raised shutter at Y=-2.4380 m.
- Separate shutter slats, recessed glazing and mullions, personnel/rear doors, louvers, roof exhaust, hollow gutter profiles, bent downpipes and collars, exterior orange/graphite tool storage, two gooseneck practical lamps, foundation and sloped grooved ramp.
- Interior includes cabinet drawers, worktops, vice, hanging tools, shelving, bins, consumable tins, practical light strips and floor guide paint.
- **100% UV and material coverage; 27 named materials.** Component UV atlases use applied geometry, 66-degree smart projection and 0.015 normalized island margin.
- All formats have **0 zero-area geometry triangles, 0 zero-area UV triangles, 0 invalid corner-normal objects**, and no missing external image paths. Native and FBX meshes have no nonmanifold edges. GLB splits vertices at UV/normal seams; its geometry has no nonmanifold edges after a 1e-6 m position weld used only for validation.
- GLB and FBX contain no studio objects, cameras or lights. Both dimensions and triangle counts match the saved native asset. Parent independently repeated these checks and reported passing results.

## Actual execution

Private Blender 4.5.12 LTS CLI processes; CPU rendering, four threads, Cycles 32 samples with denoising. No shared Blender scene, image generation, child agents, Git operations or other asset directories were used.

The following command was executed for initial and corrected full builds, both exiting 0 (logs: `build.log`, `build_final.log`):

```powershell
& 'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe' -b --factory-startup -t 4 --python 'D:/github/AstraEffort/Blender/Set01/arched_workshop/build.py'
```

The initial inspection found a self-intersecting gable profile, 1,060 zero-area triangles from thin-detail bevel collapse and duplicate lamp poles, and an overly pale roof. The source was corrected and rebuilt. Validation then passed. Final render inspection also found an interior area emitter extending through the rear wall; its studio-only dimensions were reduced, eliminating the exterior light spill.

```powershell
& 'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe' -b --factory-startup -t 4 --python 'D:/github/AstraEffort/Blender/Set01/arched_workshop/finish_lighting.py'
& 'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe' -b --factory-startup -t 4 --python 'D:/github/AstraEffort/Blender/Set01/arched_workshop/validate.py'
```

Both final commands exited 0; logs are `finish_lighting.log` and `validate_final.log`. Blender's FBX importer emitted a nonfatal denied extension-cache write outside the workspace; import, measurement and validation completed. An early standalone `python` syntax probe was unavailable on PATH; Blender's own Python executed the source successfully.

## Limitations and reference

This is a static detailed asset: doors, shutter and drawers are separate editable meshes, without animation rigs, collision hulls or LODs. Solid PBR materials are used; there are no painted/baked texture maps. FBX material support is more limited than Blender/GLB, especially for glass transmission and emission; an engine may require shader adjustment. Studio illumination is intentionally excluded from geometry exports. The interior is furnished for the visible garage opening rather than a fully authored playable room.

The sole visual reference was the assigned, already-generated [arched_workshop.png](../../../REF/Set01/arched_workshop.png), read before modeling. Its actual absolute location is `D:/github/AstraEffort/REF/Set01/arched_workshop.png`. No other workers' references or creative resources were inspected.

