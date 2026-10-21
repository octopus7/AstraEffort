from pathlib import Path
import json,hashlib,shutil,datetime
from PIL import Image,ImageStat
R=Path('D:/github/AstraEffort/ForestDemo');W=R/'Work/MountainStation/high/TexturePass';P=R/'Saved/Workers/MountainStation/high/Project'
def read(n):return json.loads((W/n).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,d):(W/n).write_text(json.dumps(d,indent=2),encoding='utf-8')
def dt(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
ue=read('ue_validation.json');uv=read('ue_uv_validation.json');rt=read('runtime_validation.json');islands=read('source_island_validation.json');im=read('imagegen_manifest.json');cap=read('Screenshots/capture_manifest.json');visual=read('visual_review.json');last=read('partition_timing.json')
assert read('world_partition_validation.json')['passed']
assert ue['passed'] and uv['passed'] and rt['passed'] and all(m['passed'] for m in islands['meshes']) and visual['passed']
assert last['exit_code']==0 and dt(ue['validated_at_utc'])>dt(read('refinement_evidence.json')['finished_at_utc'])
assert dt(rt['finished_at_utc'])>dt(ue['validated_at_utc'])
assert ue['checks']['background_constant_no_texture'] and ue['package_count']==43
first=json.loads((W.parent/'FirstDelivery/Screenshots/capture_manifest.json').read_text())
screens=[]
for c,old in zip(cap['captures'],first['captures']):
 for k in ['name','location_cm','rotation_pitch_yaw_roll','projection','orthographic_width_cm','horizontal_fov_degrees','resolution']:assert c[k]==old[k],(c['name'],k)
 p=W/'Screenshots'/c['name'];a=Image.open(p);assert a.size==(1920,1080);assert max(ImageStat.Stat(a.convert('RGB')).stddev)>10
 assert visual['screenshot_sha256'][c['name']]==sha(p)
 assert dt(c['captured_at_utc'])>dt(rt['finished_at_utc'])
 screens.append({'file':str(p.relative_to(W)),'sha256':sha(p),'resolution':list(a.size),'captured_at_utc':c['captured_at_utc']})
assert len(screens)==4 and len({s['sha256'] for s in screens})==4
for m in uv['meshes']:assert sha(W/'UEExport'/(m['mesh']+'.fbx'))==m['ue_export_sha256']
for t in im['calls']:assert sha(Path(t['workspace_path']))==t['sha256'] and sha(Path(t['original_path']))==t['sha256']
# Publish only the owned package tree and its own named map, after the isolated editor exit.
src=P/'Content/MountainStation/high';dst=R/'Content/MountainStation/high';files=list(src.rglob('*.uasset'));assert len(files)==42
assert not list(src.rglob('*.umap')) and not any('BuiltData' in f.name for f in files)
preserved={str(p.relative_to(W.parent)):sha(p) for p in (W.parent/'FirstDelivery').rglob('*') if p.is_file()}
for n in ['STATUS.json','RESULT.md']:
 p=W.parent/n
 if p.exists():preserved[n]=sha(p)
published=[]
for f in files:
 out=dst/f.relative_to(src);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,out);assert sha(f)==sha(out)
 published.append({'path':str(out.relative_to(R)),'private_sha256':sha(f),'published_sha256':sha(out)})
f=P/'Content/Maps/MountainStation_high.umap';out=R/'Content/Maps/MountainStation_high.umap';shutil.copy2(f,out);assert sha(f)==sha(out)
published.append({'path':str(out.relative_to(R)),'private_sha256':sha(f),'published_sha256':sha(out)})
for p,h in preserved.items():assert sha(W.parent/p)==h
times=[dict(file=p.name,**json.loads(p.read_text(encoding='utf-8-sig'))) for p in sorted(W.glob('*_timing.json'))]
wait=sum(t['wait_seconds'] for t in times);execution=sum(t['execution_seconds'] for t in times)
finish=datetime.datetime.now(datetime.timezone.utc);start=dt('2026-10-21T14:47:23Z');elapsed=(finish-start).total_seconds();kst=datetime.timezone(datetime.timedelta(hours=9))
timing={'started_at_utc':start.isoformat(),'finished_at_utc':finish.isoformat(),'started_at_kst':start.astimezone(kst).isoformat(),'finished_at_kst':finish.astimezone(kst).isoformat(),'elapsed_seconds':elapsed,'ue_mutex_wait_seconds':wait,'ue_execution_seconds':execution,'ue_attempts':times,'imagegen_summed_seconds':im['summed_call_seconds'],'imagegen_union_seconds':im['union_wall_seconds'],'imagegen_overlap_seconds':im['parallel_overlap_seconds'],'accounting':'Image generation calls overlap each other; CPU authoring and review can overlap UE wait. Do not sum these categories to derive total elapsed. Includes failed attempts; model token usage is not measured by this worker.'}
dump('timing_summary.json',timing)
evidence={str(p.relative_to(W)):sha(p) for p in [W/'ue_validation.json',W/'ue_uv_validation.json',W/'runtime_validation.json',W/'source_uv_validation.json',W/'source_island_validation.json',W/'imagegen_manifest.json',W/'refinement_evidence.json',W/'visual_review.json',W/'world_partition_validation.json',W/'Screenshots/capture_manifest.json']}
dump('publication_manifest.json',{'published_at_utc':finish.isoformat(),'editor_exit_timing':last,'packages':published,'screenshots':screens,'evidence_sha256':evidence,'first_delivery_and_original_records_unchanged_during_publication':preserved,'passed':True})
totaltri=sum(m['all_triangles_inspected'] for m in uv['meshes']);area=sum(m['world_area_m2'] for m in uv['meshes']);smallarea=sum(m['subpixel_world_area_m2'] for m in uv['meshes']);degarea=sum(m['excluded_world_area_m2'] for m in uv['meshes'])
lines=['# MountainStation / high — second texture and UV pass','',f'Status: ready_for_review. Final owned map: `/Game/Maps/MountainStation_high`. Published {len(published)} packages (42 assets and one map). Original FirstDelivery and first-pass RESULT/STATUS were preserved. No Git mutation performed.','',
'## Actual timing','',f'- Start UTC: {start.isoformat()}; KST: {start.astimezone(kst).isoformat()}.',f'- Finish UTC: {finish.isoformat()}; KST: {finish.astimezone(kst).isoformat()}.',f'- Elapsed wall: {elapsed:.3f} s. UE mutex waits: {wait:.3f} s. UE process execution: {execution:.3f} s (all attempts).',f'- Five concurrent imagegen calls: {im["summed_call_seconds"]:.0f} summed call seconds, {im["union_wall_seconds"]:.0f} wall seconds, {im["parallel_overlap_seconds"]:.0f} overlap seconds. These are not additive with total wall time.', '- Per-attempt UTC timestamps, waits and execution: [timing_summary.json](timing_summary.json). Token use is not measured here.','',
'## Delivered changes','',
'Existing station, curved railway, platform, terrain, tunnel and props retain their geometry/layout. All 11 authored assemblies now have measured UV0 surface charts plus UV1 inspection layouts. Five actual generated original images are preserved byte-for-byte in Generated/, with prompts, returned paths, SHA-256, timestamps, material mapping and output dimensions in [imagegen_manifest.json](imagegen_manifest.json). No external textures or another effort’s resources were used.',
'', 'Source artwork: [Solmaru_Textured.blend](Solmaru_Textured.blend); imported meshes: FBX/; saved UE mesh roundtrip exports: UEExport/; reproducible scripts: Source/. Final shared deliverables: `Content/MountainStation/high/**` and `Content/Maps/MountainStation_high.umap`. [publication_manifest.json](publication_manifest.json) binds private/published package hashes to latest validation and actual render hashes.',
'', 'Generated material mapping: plaster → Plaster/Cream/Leather; wood → Wood/Trim/Ochre; stone → Stone/StoneLight/Gravel/Path/Dark/Earth/Brick; metal → Roof/RoofEdge/Metal/Rail; foliage → Grass/Hill/Leaf/LeafLight/Flower. Furniture leather was separated from wooden Ochre props. Palette normalization uses the original per-material color divided by the generated image’s mean linear RGB. Generated contribution: 10% Grass/Hill, 24% Leaf/LeafLight/Flower, 72% remaining mapped surfaces. Samples use UV0 at 1×.',
'', 'Visual review found that the presentation plane reused StoneLight, causing enlarged stone pattern outside the 100 m site. A dedicated constant M_PresentationGround restores its original color and roughness. Fresh-process graph verification confirms that this background uses no texture. The earlier evidence is retained in Attempts/BeforeVisualRefinement/. Terrain/tree generated textures remain connected with reduced contrast; no camera or geometry redesign was made.',
'', '## UV and saved-resource verification','',
f'Every LOD0 triangle of every saved authored assembly was exported from a fresh Unreal process and remeasured: {totaltri:,} triangles. Target: 128 px/m at the actual 1254×1254 source/loaded size, equivalent to a 9.796875 m repeat. Actor scales have absolute value 1; cm-to-meter conversion is independently checked against loaded UE bounds. Repeated parts are baked into assemblies and counted individually. Area-density = 1254 × sqrt(UV area / world area).',
'', '| Saved mesh | Triangles | Area-weighted px/m | ≥1px triangle P05–P95 | Subpixel triangles | Degenerate excluded |','|---|---:|---:|---:|---:|---:|']
for m in uv['meshes']:
 q=m['density_at_least_one_pixel_triangle_min_p05_p50_p95_max'];lines.append(f'| {m["mesh"]} | {m["all_triangles_inspected"]:,} | {m["density_px_m"]:.4f} | {q[1]:.2f}–{q[3]:.2f} | {m["subpixel_triangles"]:,} | {m["excluded_degenerate_triangles"]} |')
lines+=['',f'All {sum(m["reconstructed_islands"] for m in islands["meshes"]):,} source charts were reconstructed from saved UV continuity and checked: zero inter-island bounding-box overlaps or gaps below 31.96 source pixels. All saved-UE triangles remain within those chart bounds; 31.7092 px conservative roundtrip separation. Charts sit outside 0–1 and intentionally reuse texture samples through Wrap; this is not a unique baked atlas. UV1 is normalized inspection-only and has proportionally smaller padding. No baked lighting is generated.',
'',f'Subpixel triangles occupy {smallarea:.6f} m² ({smallarea/area*100:.6f}% of measured area); excluded degenerate triangles occupy {degarea:.12f} m². Source and saved-UE degenerate counts differ because import removes/retriangulates tiny faces. Detailed min/P05/median/P95/max, per-material areas, actual actor transforms, mesh bounds and exported-file hashes are in [ue_uv_validation.json](ue_uv_validation.json), [source_uv_validation.json](source_uv_validation.json) and [source_island_validation.json](source_island_validation.json).',
'', 'Fresh reload: all recursive /Game dependencies remain within the owned theme/effort plus its map; 43 packages checked; all 11 meshes have two UV channels and full precision UVs; all generated textures are found upstream of BaseColor in the saved material graphs. Presentation background is constant. See [ue_validation.json](ue_validation.json). Direct loaded WorldSettings.world_partition is None, with the exact owned map world path verified in a subsequent read-only process: [world_partition_validation.json](world_partition_validation.json).',
'', '## Runtime evidence','', 'Fresh PIE world, controller/pawn possession, arrival PlayerStart, 300 cm platform movement and normal PIE shutdown passed. Downward sweeps moved the pawn before contact, returned blocking hits with initial_overlap=false, and identified the actual actor/component/mesh:', '', '| Site | Actual pawn travel cm | HitResult distance cm | Actor / mesh |','|---|---:|---:|---|']
for s in rt['sweeps']:lines.append(f'| {s["site"]} | {s["actual_travel_cm"]:.3f} | {s["hit_result"]["distance_cm"]:.3f} | {s["hit_result"]["actor_label"]} / {s["hit_result"]["mesh"].split(".")[-1]} |')
lines+=['','Full native HitResult fields and paths: [runtime_validation.json](runtime_validation.json). Native ScreenDebugLogger presence in active PIE was observed; no separate on-screen Hello observation or instrumented BeginPlay count is claimed.','',
'## Actual UE captures','', 'Latest saved scene rendered at 1920×1080, High (all observed scalability CVars = 2), screen percentage 100, no UI. All four camera transforms, projection, FOV and orthographic width match FirstDelivery exactly. [capture_manifest.json](Screenshots/capture_manifest.json) records actual timestamps and settings. All four images were visually inspected after material refinement.','']
for n in ['overview','top_down','platform','tracks']:lines += [f'### {n}', '',f'![{n}](Screenshots/{n}.png)','']
lines+=['## Limitations and attempts','',
'- Original imagegen requests asked for 1024²; actual outputs are 1254². They remain unchanged and imported with NoMipmaps, so distant detail may alias. Tile seam continuity has not been numerically certified.',
'- Curved/beveled normal patches preserve area density, not every local direction. Tiny bevel triangles can have large min/max distortion. Within-chart triangle intersections were not exhaustively tested; inter-chart nonoverlap was checked. Glass, Lamp, SkyBackdrop and PresentationGround are intentionally untextured exceptions.',
'- First import attempt failed on an unavailable Lerp const_alpha property; fixed with an explicit Constant node. First runtime attempt failed because HitResult was expected to expose 19 fields; UE 5.7 exposes 18. Both are retained as attempted execution in timings; process exit zero alone is not treated as validation success. Latest checks all pass.',
'- Visual refinement added one dedicated background material; all other changes stay within this effort. Supervisor owns integration, Git and the consolidated cross-theme report.','']
(W/'RESULT.md').write_text('\n'.join(lines),encoding='utf-8')
dump('STATUS.json',{'theme':'MountainStation','effort':'high','status':'ready_for_review','started_at_utc':start.isoformat(),'finished_at_utc':finish.isoformat(),'elapsed_seconds':elapsed,'map':'/Game/Maps/MountainStation_high','validation':{'fresh_ue_reload':True,'owned_packages':43,'all_11_mesh_uv_audit':True,'material_graphs_and_background':True,'runtime_blocking_sweeps':True,'four_matching_1920x1080_cameras':True,'visual_inspection':True,'private_published_hashes_equal':True},'ue_mutex_wait_seconds':wait,'ue_execution_seconds':execution,'blockers':[]})
print(json.dumps({'status':'ready_for_review','packages':len(published),'triangles':totaltri,'elapsed_seconds':elapsed,'ue_wait_seconds':wait,'ue_execution_seconds':execution,'map_sha256':sha(out)},indent=2))
