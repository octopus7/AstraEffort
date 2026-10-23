# Harbor addition: empty repair dock

One original empty U-shaped boat repair dock is ready for review in large and half native voxel resolutions. Two sidewalls and the rear deck surround a lowered paved bay with an open front, three keel blocks and four hull stands in two pairs. A small cabinet, winch, ladder and mooring fittings complete the working structure. There is no boat, water or landscape.

## Actual timing

- Start UTC: 2026-10-23T15:44:38Z
- Start KST: 2026-10-24T00:44:38+09:00
- Finish UTC: 2026-10-23T15:57:55.918Z
- Finish KST: 2026-10-24T00:57:55.918+09:00
- Total worker wall: 797.918 seconds.

| Full Blender process | UTC start | UTC finish | Wall seconds | Exit |
|---|---|---|---:|---:|
| build | 2026-10-23T15:54:12.5116639+00:00 | 2026-10-23T15:54:32.4978250+00:00 | 19.985 | 0 |
| validation_export | 2026-10-23T15:55:52.2562238+00:00 | 2026-10-23T15:55:55.4205999+00:00 | 3.164 | 0 |
| validation_opening | 2026-10-23T15:55:55.4495990+00:00 | 2026-10-23T15:55:56.0475835+00:00 | 0.599 | 0 |

These process measurements include Blender startup and script execution. The parent utility separately measured 19.333 seconds inside build/export/render execution, 2.702 seconds inside export verification, and the native semantic check measured 0.174 seconds. Full scopes and times are in TIMING.json and process_*.json. One build, two required verification processes, no visual rebuild, no optional render angles and zero worker image-generation time.

## Models and files

| Variant | Grid XYZ | Occupied cells | Surface triangles | Physical grid XYZ (m) |
|---|---|---:|---:|---|
| large | 128 x 128 x 72 | 370,420 | 10,888 | 12.8 x 12.8 x 7.2 |
| half | 64 x 64 x 36 | 49,879 | 4,226 | 12.8 x 12.8 x 7.2 |

The large grid is 128 x 128 x 72. Half is exactly 64 x 64 x 36 with twice the cell size and the same physical grid extents. Conservative reduction may expand occupied boundaries by one original large cell. Native VOX is authoritative; half is a true lower-resolution occupied grid, not a scaled mesh. No manual half-grid edits were required.

assets/repair_dock/{large,half} each contains repair_dock.vox, repair_dock.blend, repair_dock.glb, repair_dock.fbx, metadata.json and preview.png: one asset, two variants, eight model-format files and two actual PNGs. Geometry source is build.py. validate_opening.py independently checks saved native files. palette.json and provenance.json preserve style and source/reference information; capture_manifest.json records real matching-camera render settings/times and hashes; DELIVERY.json inventories final hashes.

[Large preview](assets/repair_dock/large/preview.png) | [Half preview](assets/repair_dock/half/preview.png)

## Verification and actual image review

Both final previews were individually opened and inspected. The front entrance and lowered bay remain clear. All three keel blocks and the four support pads remain distinct, with purposeful A-frame timbers below. Cabinet, rear hauling winch, ladder, coping, mooring posts and external fenders remain readable at both resolutions. Fine plank/paving divisions, winch winding ridges and stand bracing become coarser in half. No demonstrated visual defect required a rebuild, and no optional views or polish passes were made.

validation_export.json reports passed=true, one asset, two variants and zero errors. The fresh native parser checked occupancy, palette indices, coordinates, counts and hashes. Both BLEND, GLB and FBX variants were freshly imported and compared with the authoritative voxel boundary. All six format imports report zero degenerate triangles, invalid boundary triangles, invalid material triangles and off-grid coordinates, with matching bounds and triangle counts.

validation_opening.json separately reparses the saved VOX without importing the authoring module. In both sizes it verifies an empty front-entry volume, an empty central upper working volume, a continuous low bay floor, exactly three disconnected centerline keel blocks above that floor, two disconnected stands in the left support strip and two in the right. The tested boxes, voxel counts and component sizes are recorded explicitly. This proves the opening and support counts in native occupancy, not only in a render.

## Limits and ownership

Static game-art structure only: no rig, winch animation, dry-dock water system, collision, LOD chain or engine integration. No engineering load rating is claimed. Materials use opaque flat palette colors on merged coplanar exterior voxel faces, so no texture UVs are needed. GLB/FBX contain asset geometry only; BLEND retains a separate STUDIO collection for reproducible previews. The bay paving and structural foundations are parts of the dock itself.

Only voxel/harbor/additions was authored. Accepted harbor originals and all other deliveries remained frozen. The accepted harbor palette was read only for authorized style continuity; no accepted creative source or geometry was inspected/copied. The sole visual reference is REF/voxel/harbor/additions/reference.png. No other theme, ForestDemo, Git, installation, shared live Blender scene, image generation or worker delegation was used.

The addition is frozen on submission. Forestry has not begun and waits for phase-A acceptance, reference readiness and explicit parent dispatch.