$ErrorActionPreference='Stop'
$w=$PSScriptRoot
$v=Get-Content "$w/saved_asset_validation.json" -Raw|ConvertFrom-Json -DateKind String
$r=Get-Content "$w/runtime_validation.json" -Raw|ConvertFrom-Json -DateKind String
$q=Get-Content "$w/visual_review.json" -Raw|ConvertFrom-Json -DateKind String
if(!$v.passed -or !$r.passed -or !$q.passed){throw 'Validation incomplete'}
$source=Get-Content "$w/shared_source_validation.json" -Raw|ConvertFrom-Json -DateKind String
$times=@(Get-ChildItem $w -Filter '*_timing.json'|ForEach-Object {Get-Content $_.FullName -Raw|ConvertFrom-Json -DateKind String})
$latest=$times|Sort-Object finished_at_utc|Select-Object -Last 1
if($latest.exit_code-ne0-or$latest.log-notlike'*audit*'){throw 'Final audit process not successfully closed'}
$private='D:/github/AstraEffort/ForestDemo/Saved/Workers/MountainStation/medium/Project/ForestDemo/Content';$public='D:/github/AstraEffort/ForestDemo/Content';$rel='MountainStation/medium/TexturePass/UVRevision';$map='Maps/MountainStation_medium.umap'
New-Item -ItemType Directory -Force "$public/$rel"|Out-Null
Copy-Item "$private/$rel/*" "$public/$rel" -Recurse -Force
Copy-Item "$private/$map" "$public/$map" -Force
$hashes=@();$files=@(Get-ChildItem "$private/MountainStation/medium" -Recurse -File)+@(Get-Item "$private/$map")
foreach($f in $files){$relative=[IO.Path]::GetRelativePath($private,$f.FullName).Replace('\','/');$a=(Get-FileHash $f.FullName).Hash;$b=(Get-FileHash "$public/$relative").Hash;if($a-ne$b){throw "Hash mismatch: $relative"};$hashes+=@{path=$relative;private_sha256=$a;published_sha256=$b;matches=$true}}
$hashes|ConvertTo-Json -Depth 5|Set-Content "$w/delivery_hashes.json" -Encoding utf8
$finish=[DateTimeOffset]::UtcNow;$start=[DateTimeOffset]::Parse('2026-10-21T15:18:30Z');$wall=($finish-$start).TotalSeconds;$wait=($times|Measure-Object wait_seconds -Sum).Sum;$exec=($times|Measure-Object execution_seconds -Sum).Sum
$time=@{revision_started_at_utc=$start.ToString('o');revision_finished_at_utc=$finish.ToString('o');revision_started_at_kst=$start.ToOffset([TimeSpan]::FromHours(9)).ToString('o');revision_finished_at_kst=$finish.ToOffset([TimeSpan]::FromHours(9)).ToString('o');additional_wall_seconds=$wall;additional_ue_wait_seconds=$wait;additional_ue_execution_seconds=$exec;new_imagegen_calls=0;attempts=$times;original_texture_started_at_utc='2026-10-21T14:46:41Z';original_ready_at_utc='2026-10-21T15:13:28.4507038+00:00';original_supplemental_at_utc='2026-10-21T15:15:09.762128+00:00'}
$time|ConvertTo-Json -Depth 8|Set-Content "$w/timing_summary.json" -Encoding utf8
$status=Get-Content "$w/STATUS.json" -Raw|ConvertFrom-Json -DateKind String;$status.status='ready_for_review';$status.finished_at_utc=$finish.ToString('o');$status.elapsed_seconds=$wall;$status|Add-Member validation @{saved_mesh=$v.passed;runtime=$r.passed;visual=$q.passed;direct_nonWP=$v.partition_is_none;shared_tree_instances=$v.tree_instances.Count;private_published_hash_matches=$hashes.Count} -Force;$status|ConvertTo-Json -Depth 7|Set-Content "$w/STATUS.json" -Encoding utf8
$parent=Split-Path $w;$ps=Get-Content "$parent/STATUS.json" -Raw|ConvertFrom-Json -DateKind String;$ps.status='ready_for_review';$ps|Add-Member revision_finished_at_utc $finish.ToString('o') -Force;$ps|Add-Member revision_validation $status.validation -Force;$ps|ConvertTo-Json -Depth 8|Set-Content "$parent/STATUS.json" -Encoding utf8
$p=$v.saved_uv_packing;$density=$v.saved_render_lod0.at_least_four_target_texels_density_px_m;$tree=$v.tree_uv_packing
$result=@"
# MountainStation / medium — connected UV and shared-tree revision

Latest delivery, ready for supervisor review. This supersedes the original TexturePass UV packing and screenshots. FirstDelivery and the original TexturePass start, first ready and supplemental timestamps remain preserved. No Git operation was performed.

## What changed
The rejected 88,574-island attempt is not the final asset. Intrinsic triangle unfolding now joins actual adjacent triangles, preserving edge lengths and face areas and cutting where cycles or overlap prevent a valid continuation. The final source has $($source.reports.station.actual_edge_connected_uv_islands) station/terrain islands and 8 islands on one tree prototype. Plane-equation grouping is not used to count islands.

All 64 tree placements now reference the same SM_PinePrototype asset (152 triangles) and the same materials. UVs are authored once on that prototype. These are 64 StaticMeshActor instances sharing mesh data, not a claim of a single ISM/HISM draw call. Ground positions and height variation remain. To standardize geometry, the original selected tree is uniformly scaled: canopy proportions follow height; trunk thickness and tiny top-cap radius consequently scale too, unlike the previous procedural fixed widths. No new image generation, theme or layout was introduced.

## UV allocation and density
UV0 uses an unfolded multi-tile coordinate domain. Every distinct island in a unique mesh receives its own rectangle, with 8 effective texel pixels of padding on each side. No unique-surface overlap is permitted. Only afterwards does the shader apply Frac to reuse the original generated surface atlas. Reuse of one prototype's UVs by multiple tree actors is explicitly intentional and separate from unique-mesh allocation.

Source station mesh: $($source.reports.station.triangles) triangles, $($source.reports.station.area_m2) square metres, $($source.reports.station.actual_edge_connected_uv_islands) actual connected UV islands, zero positive-area overlaps, minimum island bounding-box gap $($source.reports.station.minimum_island_bbox_gap_pixels_within_32px_search) effective pixels. Source tree: 152 triangles, 8 islands, zero overlaps. Detailed source data: shared_source_validation.json and shared_source_objects.csv; editable source: Source/SharedScene.blend, with separate station and prototype FBX exports.

Fresh-process saved UE RenderData LOD0: $($p.triangles) station triangles and $($p.actual_edge_connected_uv_islands) actual connected UV islands. Overlap pairs: $($p.positive_area_overlap_pairs); minimum bounding-box gap: $($p.minimum_island_bbox_gap_pixels_within_32px_search) effective pixels. Tree prototype: $($tree.triangles) triangles, $($tree.actual_edge_connected_uv_islands) islands, $($tree.positive_area_overlap_pairs) overlaps. Every triangle and actual shared edge is processed; this is not sampled. The checker uses exact position+UV edge connectivity, then a global triangle AABB sweep and strict SAT intersection test. Gaps are conservative bounding-box distances, with all pairs closer than 32 pixels covered. Shared boundaries inside an island are allowed.

The target remains 128 pixels/metre (448 usable atlas pixels per 3.5m repeat). For $($density.count) saved station triangles with at least four target texels, measured density is $($density.min)–$($density.max) pixels/metre, median $($density.median), outside 2% tolerance: $($density.outside_2_percent). Smaller triangles are reported separately without a uniform-precision claim. Glass/dark stay untextured but their geometric UVs are measured. Shader PackedUVScale reads saved custom primitive data 0: 1 for the unit-scale station, and each uniform actor scale for trees. All 64 saved tree transforms, shared mesh references, scalar values and all 9,728 expanded tree triangles were checked; resulting density is $($v.tree_instance_world_density.min)–$($v.tree_instance_world_density.max) pixels/metre.

Unreal removes near-degenerate faces during building. Source cleanup therefore precedes unfolding: area below 1e-8 square metres or minimum altitude below 0.1mm is removed, totaling $($source.removed_zero_area_faces) faces. This avoids deleting connectors after UV packing. It affects microscopic slivers, especially lettering; remaining small-face precision is explicitly reported. No normal/displacement maps were added. Frac-based image repetition and phase changes across seams can remain visible.

## Validation and evidence
Fresh reload directly read WorldSettings.world_partition: None. Actual world: $($v.world_path). All owned assets and the map were recursively checked; foreign /Game dependencies: $($v.foreign_dependencies.Count). Actual BaseColor graph traversal verifies texture coordinates, scale parameter, custom primitive data and Frac connectivity, as well as mesh material slots and used textures. Full-precision UV storage is enabled and verified.

The real possessed Pawn moved 200cm. Ground, ramp and platform sweeps block with initial_overlap=false and positive displacement; the exact actor/component/new mesh are recorded. PIE shut down normally. Four new 1920x1080 UE renders use the FirstDelivery cameras and were individually inspected. These are actual scene renders, not generated evidence. No baked lighting or external actor/object packages were published.

The private editor closed before publication. All $($hashes.Count) owned package hashes match private and published files. See delivery_hashes.json, evidence_hashes.json, saved_asset_validation.json, runtime_validation.json, visual_review.json and Screenshots/capture_manifest.json.

## Timing
Revision UTC: $($time.revision_started_at_utc) → $($time.revision_finished_at_utc).
Revision KST: $($time.revision_started_at_kst) → $($time.revision_finished_at_kst).
Additional wall: $wall seconds; additional UE queue wait: $wait seconds; additional UE execution: $exec seconds. Includes rejected attempts and corrections. New imagegen calls: 0. Original TexturePass start 14:46:41Z, first ready 15:13:28.4507038Z and supplemental 15:15:09.762128Z are not reset.

![Overview](Screenshots/overview.png)
![Top down](Screenshots/top_down.png)
![Platform](Screenshots/platform.png)
![Tracks](Screenshots/tracks.png)
"@
$result|Set-Content "$w/RESULT.md" -Encoding utf8
Add-Content "$parent/RESULT.md" -Value "`n## Superseding UV revision`nThe latest validated assets and captures are documented in [UVRevision/RESULT.md](UVRevision/RESULT.md). Original timestamps above are retained. The previous overlap policy and screenshots describe the superseded delivery, not the current map.`n" -Encoding utf8
$e=@(Get-ChildItem "$w/Source" -File|Where-Object {$_.Name-in@('SharedScene.blend','AlderPass_UV.fbx','PinePrototype.fbx','SurfaceAtlas.png')})+@(Get-ChildItem "$w/Screenshots" -File)+@(Get-Item "$w/saved_asset_validation.json","$w/runtime_validation.json","$w/shared_source_validation.json","$w/visual_review.json","$w/timing_summary.json")
$e|ForEach-Object {@{path=[IO.Path]::GetRelativePath($w,$_.FullName).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash;bytes=$_.Length}}|ConvertTo-Json -Depth 5|Set-Content "$w/evidence_hashes.json" -Encoding utf8
$status|ConvertTo-Json -Depth 7
