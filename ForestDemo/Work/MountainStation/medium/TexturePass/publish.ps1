$ErrorActionPreference='Stop'
$work=Join-Path $PSScriptRoot '.'
$validation=Get-Content (Join-Path $work 'saved_asset_validation.json') -Raw | ConvertFrom-Json -DateKind String
$runtime=Get-Content (Join-Path $work 'runtime_validation.json') -Raw | ConvertFrom-Json -DateKind String
$review=Get-Content (Join-Path $work 'visual_review.json') -Raw | ConvertFrom-Json -DateKind String
if(!$validation.passed -or !$runtime.passed -or !$review.passed){throw 'Validation incomplete'}
$timings=@(Get-ChildItem $work -Filter '*_timing.json' | ForEach-Object {Get-Content $_.FullName -Raw | ConvertFrom-Json -DateKind String})
if(!($timings | Where-Object {$_.log -like '*texture_audit*' -and $_.exit_code -eq 0})){throw 'No finished successful audit process'}
$private='D:/github/AstraEffort/ForestDemo/Saved/Workers/MountainStation/medium/Project/ForestDemo/Content'
$public='D:/github/AstraEffort/ForestDemo/Content'
$relative='MountainStation/medium/TexturePass'
New-Item -ItemType Directory -Force (Join-Path $public $relative) | Out-Null
Copy-Item -Path (Join-Path $private "$relative/*") -Destination (Join-Path $public $relative) -Recurse -Force
$map='Maps/MountainStation_medium.umap'
Copy-Item -LiteralPath (Join-Path $private $map) -Destination (Join-Path $public $map) -Force
$hashes=@()
$files=@(Get-ChildItem (Join-Path $private 'MountainStation/medium') -Recurse -File)+@(Get-Item (Join-Path $private $map))
foreach($file in $files){
 $rel=[IO.Path]::GetRelativePath($private,$file.FullName).Replace('\','/')
 $destination=Join-Path $public $rel
 $a=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
 $b=(Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
 if($a -ne $b){throw "Private/published hash mismatch: $rel"}
 $hashes+=@{path=$rel;private_sha256=$a;published_sha256=$b;matches=$true}
}
$hashes | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $work 'delivery_hashes.json') -Encoding utf8
$evidence=@(Get-ChildItem (Join-Path $work 'Source') -File | Where-Object {$_.Extension -ne '.blend1'})+@(Get-ChildItem (Join-Path $work 'Screenshots') -File)+@(Get-Item (Join-Path $work 'saved_asset_validation.json'))+@(Get-Item (Join-Path $work 'runtime_validation.json'))
$evidence | ForEach-Object {@{path=[IO.Path]::GetRelativePath($work,$_.FullName).Replace('\','/');sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash;bytes=$_.Length}} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $work 'evidence_hashes.json') -Encoding utf8
$finish=[DateTimeOffset]::UtcNow;$start=[DateTimeOffset]::Parse('2026-10-21T14:46:41Z');$elapsed=($finish-$start).TotalSeconds
$wait=($timings|Measure-Object -Property wait_seconds -Sum).Sum;$execution=($timings|Measure-Object -Property execution_seconds -Sum).Sum
$time=@{started_at_utc=$start.ToString('o');finished_at_utc=$finish.ToString('o');started_at_kst=$start.ToOffset([TimeSpan]::FromHours(9)).ToString('o');finished_at_kst=$finish.ToOffset([TimeSpan]::FromHours(9)).ToString('o');elapsed_wall_seconds=$elapsed;ue_mutex_wait_seconds=$wait;ue_execution_seconds=$execution;imagegen_tool_seconds=26;imagegen_calls=1;imagegen_overlap_seconds=0;ue_attempts=$timings}
$time | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $work 'timing_summary.json') -Encoding utf8
$uv=$validation.saved_render_lod0;$density=$uv.at_least_four_target_texels_density_px_m
$status=@{theme='MountainStation';effort='medium';pass='TexturePass';status='ready_for_review';started_at_utc=$start.ToString('o');finished_at_utc=$finish.ToString('o');elapsed_seconds=$elapsed;map='/Game/Maps/MountainStation_medium';validation=@{saved_assets=$validation.passed;runtime=$runtime.passed;visual_review=$review.passed;hash_matches=$hashes.Count;render_triangles=$uv.audited_triangles;foreign_game_dependencies=$validation.foreign_dependencies.Count};blockers=@()}
$status|ConvertTo-Json -Depth 6|Set-Content (Join-Path $work 'STATUS.json') -Encoding utf8
$result=@"
# MountainStation / medium — TexturePass

Ready for supervisor review. The existing Alder Pass geometry, layout, lights and four comparison cameras are retained. FirstDelivery and its initial timings are untouched. No Git operation was performed.

## Timing
- UTC start: $($time.started_at_utc); finish: $($time.finished_at_utc).
- KST start: $($time.started_at_kst); finish: $($time.finished_at_kst).
- Actual wall: $elapsed seconds; UE queue wait: $wait seconds; UE execution: $execution seconds, including failed attempts.
- Imagegen: one real call, 26.0 tool-reported seconds, no parallel calls or overlap. The exact end clock was not sampled; imagegen_manifest.json explicitly distinguishes later completion observation from an exact finish timestamp. Token accounting remains supervisor-owned.

## Delivered
- /Game/Maps/MountainStation_medium
- /Game/MountainStation/medium/TexturePass: new UV mesh, 20 materials, one generated six-surface albedo atlas.
- Source/AlderPass_UV.blend, Source/AlderPass_UV.fbx, unchanged generated Source/SurfaceAtlas.png and exact Source/imagegen_prompt.txt.
- Four actual UE screenshots and Screenshots/capture_manifest.json; validation, full source-object CSV, mapping and SHA-256 manifests beside this report.

## UV and material evidence
All 1,247 authored Blender objects were measured after applying world transforms. Source geometry has 124,742 triangles and 45,905.11295 square metres of surface area, including terrain and the plinth. UV0 uses face-plane metric coordinates at 128 pixels/metre, with a 3.5m physical repeat. Each source panel is 512 square pixels with a 32px guard on every edge, leaving 448 square usable pixels.

Fresh UE process inspection read the saved mesh's actual RenderData LOD0, rather than reusing the source report: $($uv.audited_triangles) triangles, $($uv.world_surface_area_m2) square metres, $($validation.uv_sets) UV sets, UV island result $($validation.uv_islands_result). All valid render triangles were checked; this is not a sample. For $($density.count) triangles covering at least four target texels, density is $($density.min)–$($density.max) pixels/metre, median $($density.median); outside 2% tolerance: $($density.outside_2_percent). $($uv.tiny_triangle_count) smaller triangles remain explicitly excluded from that tolerance claim. The five additional outliers are small extruded lettering sides on the two platform nameboards and freight label (white material slot 7), each under 0.001 square metres and under two target pixels wide. They are retained as explicit special-surface exceptions, verified by material and position. Full values and each exception triangle are in saved_asset_validation.json.

UVs intentionally overlap across charts and repeated props; this is a repeating surface map, not uniquely packed baked artwork. There is no between-island padding. Coplanar triangles have coherent coordinates, while curved faceted surfaces can show texture phase seams. Tiny bevels and lettering may collapse below one texel. Glass and dark materials stay untextured but their UV geometry is audited; the Engine backdrop is excluded. Source chart-group counts group plane equations and are not a claim of connected-island counts.

The generated atlas supplies timber, cream plaster, aggregate stone, teal painted metal, bark and conifer needles. Material mapping covers building walls/roof, rail/ties, platform/tunnel, trees and props. Surface colours blend the atlas with the original palette (18–60% texture weight). The actual saved mesh slot materials, BaseColor input nodes and compiled used-texture references were checked. This pass adds albedo only, with scalar roughness; it does not claim authored normal/displacement maps or photorealism.

## Runtime and scope validation
Fresh saved-map reload passed. Recursive dependencies were checked for the map and every asset under the owned theme/effort root, including retained legacy assets: zero foreign /Game references. Dynamic lighting and the original non-World-Partition scene structure remain. No baked-lighting or external actor/object package is delivered.

The actual player controller possessed the baseline Pawn. It moved 200cm from its spawn. Downward sweeps against terrain, ramp and platform each report blocking=true, initial_overlap=false, positive movement and the exact hit actor, component and new SM_AlderPass_UV mesh. These are actual Pawn movement sweeps, with normal PIE shutdown. Evidence is runtime_validation.json; runtime_hello.png documents the debug overlay. This validates the three stated surface positions, not every possible traversal route.

Private UE exited before publication. All $($hashes.Count) owned private/published package hashes agree (delivery_hashes.json). Source and evidence hashes are in evidence_hashes.json. FirstDelivery assets were not overwritten inside its archive.

## Visual inspection
All four final UE renders were inspected individually; baseline positions, projections and lenses match exactly. The same supplied rotation values differ by at most 0.000001374 degrees after UE Rotator constructor float rounding, explicitly recorded in the manifest. See visual_review.json for observations and limitations. Wide shots retain the original silhouette; close views show timber, plaster and stone texture while maintaining the stylized scene. Generated source artwork is never presented as scene evidence.

![Overview](Screenshots/overview.png)
![Top down](Screenshots/top_down.png)
![Platform](Screenshots/platform.png)
![Tracks](Screenshots/tracks.png)

## Failures and references
Two apply attempts failed on UE material input-pin naming (Frac and texture coordinates); the third saved successfully after resolving actual pin names. The first audit failed on UE's triangle-ID Python naming; its error handler also reused a global package variable, so only that exact owned process was stopped. Two subsequent audits measured the density exceptions; the final audit validates the exact lettering exception scope rather than claiming all triangles satisfy tolerance. Subsequent attempts and outcomes are retained in timing_summary.json and failure records. No other's process or asset was touched.

Technical references: installed Unreal Engine 5.7 GeometryScript MeshAssetFunctions.h / MeshQueryFunctions.h, MaterialEditingLibrary.h, and the shared read-only Run-UnrealIsolated.ps1 runner. No external visual reference was used. Source imagery was generated independently for MountainStation/medium through image_gen.imagegen.
"@
$result | Set-Content (Join-Path $work 'RESULT.md') -Encoding utf8
Write-Output ($status|ConvertTo-Json -Depth 6)


