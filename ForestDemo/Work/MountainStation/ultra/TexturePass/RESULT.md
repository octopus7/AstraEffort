# Alder Pass — MountainStation / ultra — TexturePass

Ready for supervisor review. Published 130 owned packages after the private editor exited. FirstDelivery remains immutable (82 file hashes matched). No Git/index/branch operations were performed.

## Pass timing

- Start UTC: 2026-10-21T14:47:11.719394+00:00
- Start KST: 2026-10-21T23:47:11.719394+09:00
- Finish UTC: 2026-10-21T15:30:03.551119+00:00
- Finish KST: 2026-10-22T00:30:03.551119+09:00
- Wall time: 2571.832 seconds; UE mutex wait: 186.288 seconds; UE execution: 318.992 seconds.
- ImageGen: five independent parallel calls; summed calls 949s, wall union 208s, overlapping call time 741s.
- Token usage is unavailable for this pass; no invented estimate. Original delivery timing/token records were not reset.

| UE attempt | Mutex wait s | Execution s | Exit | Outcome |
|---|---:|---:|---:|---|
| build_01 | 56.581 | 17.124 | 0 | Python material-pin assertion; exit 0 was not treated as success |
| build_02 | 0.450 | 53.282 | -1073741819 | Saved assets, then shutdown access-violation exit; not accepted as final |
| build_03 | 0.318 | 44.877 | 0 | Corrected chart gaps imported and saved; clean exit |
| review_01 | 107.891 | 24.174 | 0 | Detected UV chart welding |
| review_02 | 0.214 | 24.593 | 0 | Recorded detailed UV mismatch diagnosis |
| review_03 | 0.340 | 25.675 | 0 | Chart checks passed; strict initial density threshold exposed pre-existing nonplanar terrain exception |
| review_04 | 20.495 | 129.269 | 0 | Full geometry/UV/material/package, PIE and four actual captures passed; clean exit |

## Deliverables and surface change

- Final map: `ForestDemo/Content/Maps/MountainStation_ultra.umap` (`/Game/Maps/MountainStation_ultra`).
- Owned assets: `ForestDemo/Content/MountainStation/ultra/`. Five TexturePass Texture2D assets, one master and 48 instances; original palette assets remain in the same owned root.
- New editable source: `TexturePass/SourceArt/AlderPass_Textured.blend` and 47 FBX files. Original source files remain unchanged.
- `Images/` preserves all five unedited generated PNGs; `images_manifest.json` records prompts, actual 1254×1254 dimensions, exact paths, timestamps and SHA-256 values.
- `Screenshots/{overview,top_down,platform,tracks}.png` and `capture_manifest.json` are actual 1920×1080 UE renders. Cameras and capture configuration match FirstDelivery; only capture times differ.

Wood, stone, bark, foliage and metal detail now modulate Base Color and Roughness through actual image samplers. Palette tints, 56 actor transforms, scene layout and source vertex/face/material hashes are preserved. The platform view visibly gains wood grain on walls/posts/planters and fine stone variation on paving. Overview changes are restrained; tracks show terrain/stone detail while retaining the dark tunnel composition. All four new images and their four archived counterparts were inspected.

## Validation evidence

All 47 owned placed meshes were read from a fresh UE process: **292,072 actual LOD0 triangles**, 154,459 used charts. Every imported triangle passed chart containment; independent allocation checks prove no inter-chart rectangle overlap. UV0 uses full precision. Each textured material resolved the expected image, actual dimensions and UV multiplier. Source and imported area are compared per mesh.
The target is **128 base texels per world metre**. Actual density lies within ±5% across 99.91627% of the measured scene surface area. Terrain has 32 nonplanar-quad triangles outside ±5%, covering 0.1909008% of terrain area, with triangle extremes 96.279–137.058 texels/m; its 1st–99th percentiles are 127.857–128.208. This is an explicit geometry-preserving exception, not an exact-uniform-density claim.
104,520 tiny imported triangles occupy less than one base texel and are reported individually in mesh aggregates. No within-chart triangle intersections exceed 0.05 pixel². Lettering has 54 numerical/subpixel intersection pairs, maximum 0.007602 pixel²; Conifers has two, maximum 0.0001684 pixel². These are not hidden as zero.

The original 8-pixel chart padding was insufficient for UE's fixed 1/1024 UV vertex-welding tolerance. A Blender→FBX roundtrip and exact source/imported coordinates identified the cause. Final padding is max(8, virtual side/1024), giving 8/16/32 pixels per side as needed. `DESIGN.md`, failed validation snapshots and diagnostic UV JSON preserve the evidence.

Recursive dependency inspection checked 130 packages with **zero foreign /Game dependencies**. Actual world `/Game/Maps/MountainStation_ultra.MountainStation_ultra` returned `WorldSettings.world_partition = None`; no query exception was converted into success. Lighting remains dynamic with `force_no_precomputed_lighting = true`. No external actor/object or map BuiltData packages are delivered.

Actual possessed native DefaultPawn and PlayerController were checked. Eight swept moves traversed the ramp. Three strict blocking tests used a clear start, the Pawn's own movement HitResult, positive travel, no initial overlap and exact hit actor/component/mesh agreement with an equal-radius Pawn-profile sphere trace. Terrain sampling came from actual section 0 triangles; its sole section has collision enabled. PIE ended normally. The unchanged native ScreenDebugLogger dispatched BeginPlay through a transient test subclass; visible on-screen Hello pixels were not asserted.

| Actual Pawn test | Travel cm | Blocking mesh | Initial overlap |
|---|---:|---|---|
| platform_downward | 611.23988 | SM_Platform | False |
| terrain_section_0 | 363.48939 | SM_Terrain | False |
| platform_front_side | 163.42281 | SM_PlatformCoping | False |

Detailed evidence: `uv_validation.json`, `source_uv_validation.json`, `allocation_validation.json`, `validation.json`, `Runtime/validation.json`, `Runtime/native_and_ramp.json`, `editor_closed_evidence.json`, `publication_manifest.json`, `first_delivery_immutability.json`, `visual_review.json`, and final engine logs in `Logs/`. Publication hashes match the validated private packages.

## Limits and interpretation

- A unique chart layout does not imply unique painted pixels: five generated images intentionally repeat. Virtual atlas sizes are coordinate scales, not huge texture allocations.
- Actual images are 1254px NPOT, despite the prompt asking for 2048. They are unresized, linear, Wrap, NeverStream, without mipmaps. Distant motion aliasing/streaming performance was not measured.
- Lettering, clock, glass, lamp emission and dark tunnel backing retain original special/solid materials; image texel density does not apply to those slots.
- UVs are polygon charts, so grain orientation can change across seams. No normal/displacement map or physical relief was added.
- Source contains 295,218 triangles; UE contains 292,072. Import triangulation/degenerate removal differs, especially font/foliage microgeometry. Source geometry hashes and scene transforms are identical, but exact per-triangle identity between source and UE is not claimed. All source/UE mesh area differences stayed below 0.5%.
- Existing terrain/path intersections, faceted slopes, tunnel darkness, scene composition and gameplay scope remain. No railway-operation simulation, Character locomotion or packaged-build certification is claimed.
- Validation used editor-readable LOD0 data. Allow CPU Access warnings concern cooked-build ProceduralMesh conversion; no packaged conversion was tested.

## References

No third-party scene or texture artwork was used. Sources are the worker's original AlderPass scene and five built-in ImageGen outputs. Local engine implementation references: `Runtime/Engine/Public/MeshBuild.h:61` (UV equality tolerance), `Developer/MeshBuilder/Private/StaticMeshBuilder.cpp:1541` (render-vertex merge), `Editor/UnrealEd/Private/Fbx/FbxStaticMeshImport.cpp:758` (V flip), and WorldSettings reflection for the direct WorldPartition query. Source authoring timestamps that include +09:00 are offset-aware; report timing above is normalized explicitly to UTC/KST.

## Actual UE screenshots

### overview

![overview](D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass/Screenshots/overview.png)

### top_down

![top_down](D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass/Screenshots/top_down.png)

### platform

![platform](D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass/Screenshots/platform.png)

### tracks

![tracks](D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass/Screenshots/tracks.png)

## Per-mesh imported density and coverage

Percentiles include all nonzero-area triangles, including subtexel triangles. The complete JSON also separates triangles with at least one base texel of area.

| Mesh | UE triangles | P1 texels/m | P99 texels/m | Area outside ±5% | Padding px |
|---|---:|---:|---:|---:|---:|
| SM_Terrain | 20000 | 127.857 | 128.208 | 0.19090076% | 32.0000 |
| SM_TerrainSkirt | 1600 | 128.000 | 128.000 | 0.00000000% | 8.0000 |
| SM_Ballast | 3204 | 127.999 | 128.001 | 0.00000000% | 8.0000 |
| SM_Sleepers | 15876 | 127.858 | 128.033 | 0.00000000% | 8.0000 |
| SM_RailFasteners | 25272 | 127.856 | 128.035 | 0.00000000% | 8.0000 |
| SM_Rails | 12816 | 127.999 | 128.002 | 0.00000000% | 8.0000 |
| SM_Platform | 412 | 128.000 | 128.000 | 0.00000000% | 8.0000 |
| SM_PlatformCoping | 1096 | 128.000 | 128.002 | 0.00000000% | 8.0000 |
| SM_Paving | 9072 | 127.976 | 128.029 | 0.00000000% | 8.0000 |
| SM_AccessRamp | 10 | 128.000 | 128.000 | 0.00000000% | 8.0000 |
| SM_Railings | 1296 | 127.934 | 128.080 | 0.00000000% | 8.0000 |
| SM_Footpath | 2048 | 127.820 | 128.289 | 0.00000000% | 8.0000 |
| SM_StationStone | 216 | 127.998 | 128.003 | 0.00000000% | 8.0000 |
| SM_StationWalls | 110 | 127.999 | 128.002 | 0.00000000% | 8.0000 |
| SM_StationCladding | 4536 | 127.988 | 128.013 | 0.00000000% | 8.0000 |
| SM_StationTrim | 2808 | 127.868 | 128.027 | 0.00000000% | 8.0000 |
| SM_StationRoof | 216 | 127.866 | 128.029 | 0.00000000% | 8.0000 |
| SM_RoofSeams | 5508 | 127.865 | 128.039 | 0.00000000% | 8.0000 |
| SM_StationDoors | 356 | 127.997 | 128.002 | 0.00000000% | 8.0000 |
| SM_StationGlass | 420 | 127.997 | 128.002 | 0.00000000% | 8.0000 |
| SM_Canopy | 1512 | 127.862 | 128.034 | 0.00000000% | 8.0000 |
| SM_Signage | 950 | 127.871 | 128.007 | 0.00000006% | 8.0000 |
| SM_Lettering | 70796 | 127.883 | 128.119 | 0.00000000% | 8.0000 |
| SM_Clock | 2560 | 127.861 | 128.031 | 0.00000000% | 8.0000 |
| SM_Benches | 5184 | 127.995 | 128.007 | 0.00000000% | 8.0000 |
| SM_Lamps | 4480 | 127.976 | 128.017 | 0.00000000% | 8.0000 |
| SM_Luggage | 1296 | 127.992 | 128.005 | 0.00000000% | 8.0000 |
| SM_Timetable | 216 | 127.996 | 128.003 | 0.00000000% | 8.0000 |
| SM_FreightShed | 756 | 127.995 | 128.004 | 0.00000000% | 8.0000 |
| SM_Cargo | 6888 | 127.976 | 128.017 | 0.00000000% | 8.0000 |
| SM_Handcart | 1268 | 127.996 | 128.004 | 0.00000000% | 8.0000 |
| SM_TunnelInterior | 52 | 128.000 | 128.000 | 0.00000000% | 8.0000 |
| SM_TunnelMasonry | 2496 | 127.862 | 128.031 | 0.00000000% | 8.0000 |
| SM_TunnelRibs | 15552 | 127.854 | 128.037 | 0.00000000% | 8.0000 |
| SM_TunnelDarkness | 2 | 128.000 | 128.000 | 0.00000000% | 8.0000 |
| SM_TunnelHill | 2016 | 128.000 | 128.000 | 0.00000000% | 8.0000 |
| SM_Outcrops | 3000 | 127.999 | 128.001 | 0.00000000% | 16.0000 |
| SM_OutcropMoss | 1200 | 127.999 | 128.000 | 0.00000000% | 8.0000 |
| SM_Trunks | 8432 | 127.871 | 128.103 | 0.00000000% | 8.0000 |
| SM_Conifers | 34820 | 127.875 | 128.176 | 0.00000015% | 16.0000 |
| SM_Shrubs | 10200 | 127.998 | 128.001 | 0.00000000% | 8.0000 |
| SM_MeadowDetails | 5184 | 127.997 | 128.003 | 0.00000000% | 8.0000 |
| SM_Fences | 3780 | 127.992 | 128.010 | 0.00000000% | 8.0000 |
| SM_TrailSigns | 432 | 127.994 | 128.003 | 0.00000000% | 8.0000 |
| SM_Planters | 1224 | 127.998 | 128.001 | 0.00000000% | 8.0000 |
| SM_Bins | 688 | 127.998 | 128.001 | 0.00000000% | 8.0000 |
| SM_WaterTap | 216 | 127.997 | 128.006 | 0.00000000% | 8.0000 |
