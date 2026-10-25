# VegetationPass independent implementation review

Initial review: 2026-10-22 14:13 UTC / 23:13 KST. Read-only review of WindmillFarm/ultra VegetationPass code, manifests, logs and actual UE screenshots. No UE/Blender/Git invocation, asset mutation, other-theme inspection or shared-document change was performed. This report is the only reviewer-written file.

## Initial decision

**Hold publication until the seven wind materials compile successfully and unobscured corn/wind evidence is recaptured.** Both defects were reported to the parent, who confirmed the causes and is correcting them. The current `validation.json` saying all checks pass is insufficient: its material check only recognizes the WPO node and code string, not a valid compiled input graph. Source geometry, ownership, planting counts and broad layout otherwise support the requested additions.

## Findings

### P1 — All seven wind materials fall back to the default material

`Execution/capture.log:1159–1178` explicitly records PCD3D_SM5 compilation failures for all four `M_Wind_Corn*` and all three `M_Wind_Meadow*` materials, followed by: `missing input 2 (V)`. The reviewed `wind_material()` attempts to connect the VertexColor node's output named `RGB` to custom input V. That connection is invalid for this node's reflected output; the parent confirmed the default output must be used and its connection result asserted.

This is visible in the actual overview, top-down and meadow images: all new vegetation appears nearly black/blue-grey, losing the authored green/gold material colors. The sampled meadow motion frames do not establish plant motion while the intended wind shader is not compiled. Repair all P/V/T connections, check compilation/fallback diagnostics, save, reload and recapture. A node/code-string check alone must not certify the wind requirement.

### P1 — Corn camera is occluded and cannot prove corn appearance or motion

The initial `corn.png`, `corn_motion_t0.png` and `corn_motion_t1.png` are filled by a near green surface. The camera at UE `[4300,-4050,570]` conflicts with the relocated orchard canopy near `[4100,-3900,...]`. No corn is inspectable in those three images. The parent has selected a replacement camera clear of the tree and barn. Recapture both corn motion frames with exactly the same unobscured camera and verify visible corn displacement, not merely differing file hashes.

### Minor — Make meadow wind bounds conservative at the smallest scale

The shader offsets positions in world centimetres. Its maximum horizontal X offset is bounded by approximately `22*0.88 + 2.1 = 21.46cm`. The inspected mesh import expands local bounds by 30cm horizontally, but the smallest recorded plume scale is 0.5855642, reducing that padding to about 17.57cm along an aligned axis. Increasing the meadow horizontal local extension to at least 40cm would conservatively cover the maximum world-space offset at that scale. This is a defensive culling observation; no actual disappearance was seen in the reviewed frames.

## Successful static and source checks

- `design.py` defines a separate 15×12m corn soil bed centred at design `(31,30)`, behind the barn, with its own short entrance and fence opening. The actual overview and top-down views show this fifth planting area separately from the four original fields. The primary dirt routes remain broad and visibly open.
- `assembly.json` records 210 corn plants: 70 each of `SM_CornA/B/C`, in 14 rows. It records 1,457 meadow clumps: 591 tall, 769 plume and 97 reed. The fresh-load validation's saved foliage counts match these exactly. The six meshes use UE instanced foliage rather than one actor per plant.
- Meadow placement filters reserve margins around existing paths, original fields, the corn bed/entrance, buildings, the mill and the corrected hay stack. This validation checks placement centres, not each animated leaf's full envelope. Small fringes can extend toward a route edge, but the shown primary paths are unobstructed. Vegetation collision is deliberately disabled; it does not create new blocking plant collision.
- All new meshes, textures, materials and foliage types use `/Game/WindmillFarm/ultra/**`; the map remains `/Game/Maps/WindmillFarm_ultra`. The private-project assertion and runner target the assigned WindmillFarm scratch. The source scripts/manifests contain no cross-theme creative-resource reuse. The new ground atlas starts from this same assignment's own atlas and alters the corn bed/entrance.
- The planned WPO formula is anchored correctly in principle: every displacement term is multiplied by `pow(saturate(V.r),1.7)`, which is exactly zero at a zero-height root. A shared spatial/temporal phase supplies coherent bend across material slots; G modulates small leaf/seed flutter. This is artistic vertex deformation, not physical simulation. Correct source coloring does not replace the required compiled/rendered evidence.
- The three corn sources were exported and reimported with two UV channels, retained vertex colors, root R=0 and maximum normalized-height error below 3e-8. Each has 2,168 triangles. Their area-equivalent unscaled UV1 densities are approximately 128px/m, with the recorded triangle range approximately 127.946–128.069px/m.
- The three meadow sources similarly report two valid UV channels and vertex-color height error below 3e-8. Tall/plume/reed have 1,396/1,400/2,284 triangles, with approximate heights 1.309/0.888/1.711m. Their readbacks report zero collapsed UV triangles, zero duplicate UV0 grid cells and approximately 128px/m UV1 density. The below-ground 4mm blade cross-section is an explicit root-gap allowance with R=0.
- Source texture and geometry provenance is original procedural work. No image-generation service or external images are claimed or evidenced. Source UV1 density is for unscaled assets: actual scales vary from approximately 0.931–1.050 for corn and 0.586–1.139 for meadow, so placed density varies inversely.

## Actual evidence inspected

Directly inspected initial actual UE PNGs: overview, top_down, corn, meadow, corn_motion_t0, corn_motion_t1, meadow_motion_t0 and meadow_motion_t1. The corn camera failure and dark fallback appearance above are visual findings, not inferred solely from code. The meadow forms provide visibly taller grasses and seed heads, but color/style assessment must be repeated after the shader repair.

The initial capture manifest records corn motion at world times 29.215443566s / 31.214790680s, and meadow motion at 33.211066961s / 35.249845479s. Camera parameters match within each pair. This proves spaced captures, not successful wind behavior. The initial capture's `validation.json` at 23:10:33.968477 KST reports 22 checks true, including saved load, owned dependencies, non-WP/no external packages, 100m footprint and original PIE/collision checks, but does not detect the material fallback.

The parent will apply a shader-log/input-graph gate, fresh saved-map/runtime validation, visible wind-pair checks and publication hashes. This reviewer has not yet inspected corrected materials/images or a published delivery. Preserve this initial finding history when appending the correction decision.

## Correction review and current decision

Reviewed 2026-10-22 14:24 UTC / 23:24 KST. **No remaining publication blocker was found in this review.** The two initial P1 findings, conservative-bounds observation and a subsequent early-overview color issue are resolved by the evidence below. Delivery can proceed through the parent's final hash/publication checks. This decision covers the private saved result and captured evidence; the reviewer has not independently inspected a later published copy.

- **Wind material fallback resolved.** `assemble_vegetation.py:24–25` now connects the default VertexColor output to V and asserts each P/V/T connection. `capture_vegetation.py:23–24` inspects the connected input graph, including its VertexColor input. The final saved-map validation recognizes all seven wind materials and all six imported meshes' vertex colors. Searches of the final `Execution/polish.log` and `Execution/overview.log` found none of the initial material-compile, missing-input or default-material fallback messages. Direct inspection of the corrected corn/meadow close-ups and motion evidence shows the intended green leaves, gold corn and pale seed heads.
- **Corn visibility resolved.** The final corn camera is UE `[3800,-1900,550]`, aimed at `[3100,-3000,110]`, FOV 50 degrees. The reviewed corn close-up and motion endpoints show the field clearly; the former full-frame canopy obstruction is absent.
- **Wind bounds resolved.** `ue_polish.py:43` saves positive and negative meadow bounds extensions of `(40,40,5)`cm. `validation.json` records minimum scale-adjusted horizontal padding of 23.4226cm for plume, 31.4371cm for reed and 31.2126cm for tall, each exceeding the shader's conservative 21.46cm maximum X offset. Corn's smallest recorded padding is 27.9291cm against its 17.06cm bound. The new `wind_bounds_cover_motion` check passes.
- **Overview color resolved by a later actual capture.** Initial corrected captures still showed grey-blue corn in the first overview despite properly colored subsequent views. The final overview was recaptured after close corn/meadow warm-up views, at the same original camera `[7800,10500,7200]`, target `[0,-200,100]`, FOV 48. Its manifest timestamp is `2026-10-22T14:21:27.685598+00:00`. Direct inspection now shows green corn in the separate field behind the barn, green/gold meadow vegetation, the original four fields, open central paths and the retained calm rounded architecture/trees. The reviewed final overview SHA-256 is `b686cb5b6005c73af97b48841a336cf989c1c265a9da4ff288a831780e2e238d`. The previous first-frame color concern is not present in this replacement.

### Final saved-load and runtime evidence

The final polish validation is timestamped `2026-10-22T23:17:31.368406+09:00` (14:17:31 UTC). Its `all_passed` is true and all 23 individual checks are true, including saved-map reload, 100m footprint, owned dependencies, non-World-Partition/no external packages, foliage counts, wind material input graphs, imported vertex colors, placement/path checks, wind bounds, original prop contact, PIE possession, ground/building collision, blocked pawn sweep, pawn movement and ended PIE. Saved counts are exactly 210 corn in 14 rows and 1,457 meadow clumps, matching the source assembly. The corn bed is still 15×12m at design `(31,30)`.

`Execution/polish_timing.json` records process exit 0 at 14:17:35.7636411 UTC, after 70.5765538 seconds of execution and 0.2844804 seconds of queue wait. The separate overview process exits 0 at 14:21:31.4230569 UTC, after 32.8448082 seconds of execution and 0.2279973 seconds of wait. These exit codes support the explicit validation and image evidence; they are not used as standalone success criteria.

### Actual motion and image review

Directly inspected corrected overview, top-down, corn and meadow images, both fixed-camera wind pairs, and frame 000/frame 031 of each final motion sequence. Corn and meadow leaf/seed positions visibly change while the cameras remain fixed. The final pair world-time differences are approximately 1.90524 seconds for corn and 1.91222 seconds for meadow. Each longer sequence contains 32 actual UE frames at 1280×720; its first-to-last captured world-time span is 6.62640 seconds for corn and 6.60999 seconds for meadow. The 13 still-image PNG headers were independently checked as 1920×1080.

`Motion/video_manifest.json` records 32-frame MP4 encodings at approximately 4.678/4.690fps, durations 6.840/6.823 seconds, and documents normalization of slight capture timing variation without interpolated or generated frames. This review inspected the source-frame endpoints and manifest, not continuous MP4 playback. Pixel differences can include shadows and temporal rendering; the visible plant changes, correctly connected root-weighted WPO and retained imported vertex colors together support the requested wind effect.

### Remaining limitations, none blocking this addition

Wind remains artistic material WPO with fixed roots, not physical plant simulation; new vegetation deliberately has no blocking collision. Clearance validation concerns planting centres rather than every animated leaf, and the visually reviewed primary paths are open. Stated 128px/m source UV density is for unscaled geometry and varies inversely with placed scale. The low-frame-rate clips demonstrate motion and should not be represented as smooth 30/60fps gameplay recordings. The prior explicitly disclosed microscopic MillTower UV exceptions remain outside this pass; no strict universal zero-overlap claim is justified. Runtime evidence is the scripted possession, sweep and movement sequence, not a human walkthrough. No new actionable visual/contact issue was found in the reviewed final images.
