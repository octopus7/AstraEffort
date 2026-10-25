# Set03 production record

Status: **produced_unreviewed**. `review_status=deferred_by_user`.

- Start UTC: 2026-10-25T05:36:36.508155+00:00
- Start KST: 2026-10-25T14:36:36.508155+09:00
- Finish UTC: 2026-10-25T05:45:33.590331+00:00
- Finish KST: 2026-10-25T14:45:33.590331+09:00
- Elapsed wall seconds: 537.082
- Blender process seconds: 216.441
- Timing starts at recorded reference intake completion, before geometry authoring; process durations use Python perf_counter.

| Asset | Process seconds | Return code | Expected nonempty files |
|---|---:|---:|---|
| street_sweeper | 53.838 | 0 | True |
| pipe_inspection_robot | 50.981 | 0 | True |
| road_maintenance_depot | 54.096 | 0 | True |
| compact_pump_station | 57.526 | 0 | True |

Delivered paths are listed in [README.md](README.md) and in [delivery_manifest.json](delivery_manifest.json) with bytes and SHA256. Source and individual process logs are retained.

The source authors original ordinary mesh geometry from the four supplied `REF/Set03/*.png` design inputs. Rounded bodies and architecture use editable component meshes, bevels, curved sweeps, purpose-built cylindrical structures and named PBR palette materials. The models preserve functional reference structures: sweeper brushes/hopper/suction shoe, articulated inspection modules/camera/tether reel, open service bay/office/tool alcove, and paired volute pumps/manifold/valve/cabinet.

Only process completion and expected output existence/nonzero size were checked. Hashes are file inventory. Visual inspection, fresh BLEND reopen, GLB/FBX reimport, geometry validation, UV validation and independent review were deferred by the user. No claim of validated geometry, UVs, framing, material appearance or export roundtrips is made.

Known limitations: proportions and engineering details are simplified game art; materials are solid-color PBR; glass uses opaque reflective shading for a readable game palette; no rig, animation, collision or LODs. Renders are actual Cycles renders, 960×960 with 40 samples and denoising, but have not been inspected. Each metadata file contains direct authoring measurements and camera/render timestamps, not independent validation.

External references: only the four main-supplied PNGs and prompt text under `REF/Set03`. No other set, voxel, ForestDemo or shared live Blender scene was read or reused. No installation, image generation, Git operation or reviewer dispatch was performed.

The set is frozen after these four assets pending main integration and later user review.
