import datetime,json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parent
def read(n):return json.loads((R/n).read_text(encoding='utf-8'))
pub=read('publication_manifest.json');assert pub['passed']
uv=read('uv_validation.json');geo=read('improvement_geometry_validation.json');routes=read('Runtime/changed_routes.json');runtime=read('Runtime/validation.json');native=read('Runtime/native_and_ramp.json');pkg=read('validation.json')
assert all(x['passed'] for x in [uv,geo,routes,runtime,native])
s=read('STATUS.json');now=datetime.datetime.now(datetime.timezone.utc);kst=now.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
elapsed=(now-datetime.datetime.fromisoformat(s['started_at_utc'])).total_seconds();active=elapsed-s['paused_seconds']
timings=[(p.name,read(p.name)) for p in sorted(R.glob('timing_*.json')) if p.name!='timing_summary.json'];wait=sum(t['wait_seconds'] for _,t in timings);execution=sum(t['execution_seconds'] for _,t in timings)
triangles=sum(m['triangles_checked'] for m in uv['meshes']);area=sum(m['world_surface_area_m2'] for m in uv['meshes']);out_area=sum(m['world_surface_area_m2']*m['area_fraction_outside_5_percent'] for m in uv['meshes'])
stats={'finished_at_utc':now.isoformat(),'finished_at_kst':kst.isoformat(),'elapsed_wall_seconds_including_pause':elapsed,'user_pause_seconds':s['paused_seconds'],'elapsed_seconds_excluding_pause':active,'ue_mutex_wait_seconds':wait,'ue_execution_seconds':execution,'new_image_generation_calls':0,'new_image_generation_seconds':0,'parent_token_increment':None,'verified_child_token_increment':None,'token_note':'Supervisor accounting required; no token count estimated. Read-only technical audit child used; no art subagent.','timings':[dict(file=n,**t) for n,t in timings]}
(R/'timing_summary.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
logs=R/'Logs';logs.mkdir(exist_ok=True)
for _,t in timings:
    src=Path(t['log'])
    if src.exists():shutil.copy2(src,logs/(src.stem+'.txt'))
lines=[
'# MountainStation / ultra — SelfImprovement',
'',
'Finite worker pass complete; ready for supervisor review and integration. No commit or push was made after the explicit resume request. The previous stopped checkpoint remains preserved in commit f7f46b7 and Checkpoint/.',
'',
'## Scope and result',
'',
'Repaired terrain clipping along the footpath, blended gravel edges into meadow with imported corner colors, added a timber railway crossing, exposed sleepers above a trapezoidal ballast bed, rebuilt continuous rail foot/web/head profiles, and added two movable tunnel fill lights. The original 44 other mesh geometries and all 56 original actor placements are unchanged. Terrain remains a 100 × 100 m static mesh; station, platform, 1:12 access ramp, freight shed, trees and props remain.',
'',
f'Owned delivery: `ForestDemo/Content/MountainStation/ultra/**` and `ForestDemo/Content/Maps/MountainStation_ultra.umap` ({pub["package_count"]} packages). All publication bytes match the privately validated package inventory. The private editor was closed before copying. Full manifest: [publication_manifest.json](publication_manifest.json).',
'',
'## Validation evidence',
'',
f'- Saved map reloaded in a fresh UE process. World partition is absent; dynamic lighting is enabled; recursive dependencies contain no foreign /Game packages. No external-actor/object packages or BuiltData were published.',
f'- Actual imported footpath: {geo["path_triangle_centroid_and_edge_samples"]:,} centroid/edge samples, minimum terrain clearance {geo["minimum_path_terrain_clearance_cm"]:.3f} cm. Original source diagnostics found 13 penetrating samples out of 794, worst −39.758 cm. Sampling populations differ after retessellation; these are not equal-count tests.',
f'- {len(geo["rail_samples"])} actual rail/ballast/sleeper checks: exposed sleeper height {min(x["exposed_sleeper_cm"] for x in geo["rail_samples"]):.3f}–{max(x["exposed_sleeper_cm"] for x in geo["rail_samples"]):.3f} cm. Downward rail collision agrees with the imported head surface. Two movable fill lights verified.',
f'- All {len(uv["meshes"])} placed owned meshes / {triangles:,} imported triangles checked for UV chart containment, padding, material dimensions/scales and overlap. {100*(1-out_area/area):.5f}% of surface area is within ±5% of 128 effective base texels/m. Preserved terrain nonplanarity and tiny subpixel numerical intersections are itemized in [uv_validation.json](uv_validation.json).',
'- Saved soft-path material parent and VertexColor.R → Lerp → Multiply → BaseColor connections verified. Imported nonwhite vertex colors confirmed; numerical imported color ranges are not claimed. Source Blender/FBX color ranges are in color_source_diagnostics.json.',
f'- Actual possessed DefaultPawn: original arrival-ramp movement, native logger BeginPlay probe, positive blocking sweeps against terrain/platform, plus {sum(len(x["moves"]) for x in routes["routes"])} successful moves across three changed routes in both directions. See [Runtime](Runtime/changed_routes.json).',
'- All 201 FirstDelivery/TexturePass evidence files retain their original inventory and hashes. Comparison packages are preserved separately. New evidence is confined to SelfImprovement.',
'',
'## Actual before / after renders',
'',
'Six actual UE captures per state. Camera poses/projection/FOV, 1920 × 1080 resolution, manual exposure and quality CVars match exactly. After renders bind to the validated package manifest and package hashes were reconfirmed after capture. before_current is a rejected sky-only attempt and is excluded from comparison.',
'',
'| View | Before | After |',
'|---|---|---|']
for n in ['overview','top_down','platform','tracks','path_junction','crossing']:
    lines.append(f'| {n} | ![{n} before](Screenshots/before_fixed/{n}.png) | ![{n} after](Screenshots/after_final/{n}.png) |')
lines += ['', 'Visual findings are recorded in [visual_review.json](visual_review.json).','',
'## Timing and interruption','',
f'- Original start: {s["started_at_utc"]} UTC / {s["started_at_kst"]} KST.',
f'- User stop: {s["stopped_at_utc"]}; resumed: {s["resumed_at_utc"]} UTC / {s["resumed_at_kst"]} KST.',
f'- Finish: {now.isoformat()} UTC / {kst.isoformat()} KST.',
f'- Start-to-finish wall time: {elapsed:.3f} s; user-requested pause: {s["paused_seconds"]:.3f} s; time excluding pause: {active:.3f} s.',
f'- Recorded UE queue wait: {wait:.3f} s; UE execution: {execution:.3f} s. All attempts, failed runs and rejected capture costs are included. [timing_summary.json](timing_summary.json) contains individual runs.',
'- New image generation: 0 calls / 0 s. Existing owned TexturePass textures reused. Parent and verified-child token deltas require supervisor accounting; no counts are invented.',
'',
'## Corrections and limits','',
'Review found a real 12 cm path/ramp overlap, repaired by conforming path vertices below the original ramp surface. It also found a 14.99 cm penetration where Blender and UE triangulated nonplanar terrain differently; the path was rebuilt against the actual UE terrain triangles. Imported vertex colors were absent after mixed legacy/Interchange reimport; conversion bypassing task options was confirmed, but the exact color-loss mechanism was not established. The private Footpath asset was recreated through UE with explicit legacy FBX import; saved colors and material wiring then passed. Tangent-versus-color API misuse and initialization cleanup were corrected. Source export/backup failures required new output filenames; review04 used the prior geometry and is explicitly superseded. Failed attempts and logs are retained, including four unsuccessful UE processes with Windows access-violation shutdown exit codes; none count as successful validation.',
'',
'Movement evidence uses a 35 cm DefaultPawn sphere, with center positions 80 cm above crossing/ramp support and 150 cm above the steep repaired slope. Paths may detour laterally by up to 75 cm within verified supporting path surfaces. The original 80 cm-clearance steep-slope sweep was blocked by the path itself and remains a documented failed test; raising flight clearance does not establish walkability. It does not certify grounded Character walking, wheelchair accessibility along the mountain trail, or train operations. Terrain is a mesh rather than Landscape. Five inherited 1254² textures repeat over polygon UV charts, use no mipmaps/NeverStream, and are not uniquely painted atlases. Tiny UV numerical intersections and terrain density exceptions are reported. Tunnel depth remains dark; sparse landscape styling, triangulated steep path faces and visible 20 cm grid edges in close views remain limitations. Final fill intensities are 35 and 25 lumens, reduced after the first after-render showed excessive brightness. No additional external artwork was used; installed UE source was consulted for import/API behavior.',
'']
lines += ['Final scene validation (review09) exited 0. The separate final capture wrote all six PNGs, its successful manifest and post-capture package hash confirmation, then returned Windows access violation (-1073741819) after engine shutdown/log-close messages. The editor process was independently confirmed closed, all final PNGs were inspected and hashed, and all 137 published package hashes matched the validated inventory. Clean final-capture process exit is not claimed. This adds a fifth nonzero-exit process to the four earlier unsuccessful runs.','']
(R/'RESULT.md').write_text('\n'.join(lines),encoding='utf-8')
s.update(status='ready_for_review',finished_at_utc=now.isoformat(),finished_at_kst=kst.isoformat(),elapsed_seconds=elapsed,elapsed_seconds_excluding_pause=active,validation=f'{len(uv["meshes"])} meshes validated; actual runtime sweeps passed; 6 same-camera after renders inspected; {pub["package_count"]} package hashes matched after publication; frozen evidence unchanged.',blockers=[])
(R/'STATUS.json').write_text(json.dumps(s,indent=2),encoding='utf-8')
print(json.dumps({'status':s['status'],'triangles':triangles,'wall_excluding_pause_seconds':active,'ue_wait_seconds':wait,'ue_execution_seconds':execution}))
