"""Only run after fresh validation, visual review and closed-editor publication."""
import json, datetime, shutil, hashlib
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra'); OUT=ROOT/'TexturePass'
SCRATCH=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/ultra')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def utc(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).astimezone(datetime.timezone.utc)
validation=read(OUT/'validation.json');runtime=read(OUT/'runtime_validation.json');visual=read(OUT/'visual_review.json');motion=read(OUT/'water_motion_validation.json');publication=read(OUT/'publication.json');uv=read(OUT/'uv_summary.json');build=read(OUT/'build_result.json')
assert validation['success'] and runtime['success'] and runtime['normal_play_exit'] and visual['approved'] and motion['passed'] and publication['verified_copy'] and publication['private_editor_closed']
timings=[];execution=OUT/'Execution';execution.mkdir(exist_ok=True)
for p in sorted(SCRATCH.glob('texture-timing-*.json')):
 record=read(p)
 measured_wait=(utc(record['run_started_at_utc'])-utc(record['wait_started_at_utc'])).total_seconds()
 measured_run=(utc(record['finished_at_utc'])-utc(record['run_started_at_utc'])).total_seconds()
 assert abs(measured_wait-record['wait_seconds'])<.01 and abs(measured_run-record['execution_seconds'])<.01
 shutil.copy2(p,execution/p.name);timings.append(record)
generation=read(OUT/'Generated/generation_records.json')
for r in generation:
 a=datetime.datetime.strptime(r['started_at']['current_time'],'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=datetime.timezone.utc)
 b=datetime.datetime.strptime(r['finished_at']['current_time'],'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=datetime.timezone.utc)
 assert (b-a).total_seconds()==r['elapsed_seconds']
 assert hashlib.sha256((OUT/r['owned_original']).read_bytes()).hexdigest().upper()==r['sha256']
status=read(OUT/'STATUS.json');start=utc(status['started_at_utc']);now=datetime.datetime.now(datetime.timezone.utc);kst=datetime.timezone(datetime.timedelta(hours=9))
summary={'checks_passed':len(validation['checks']),'dependency_packages':validation['checks']['recursive_game_dependencies']['detail']['packages_checked'],'dependency_violations':0,'uv_meshes':922,'uv_area_weighted_density_range_px_m':[uv['density_min'],uv['density_max']],'uv_overlap_count':0,'minimum_island_gap_pixels':uv['minimum_padding_gap'],'generated_images':4,'saved_texture_size':[1254,1254],'actual_ue_images':7,'resolution':[1920,1080],'water_motion':motion['passed'],'pie_possession_and_sweep':runtime['player_test']['passed'],'normal_play_exit':runtime['normal_play_exit'],'published_files':len(publication['files']),'sha256_copy_match':True}
status.update(status='ready_for_review',finished_at_utc=now.isoformat(),finished_at_kst=now.astimezone(kst).isoformat(),elapsed_seconds=(now-start).total_seconds(),validation=summary,blockers=[],ue_queue_wait_seconds=sum(r['wait_seconds'] for r in timings),ue_execution_seconds=sum(r['execution_seconds'] for r in timings),imagegen_call_latency_seconds={r['name']:r['elapsed_seconds'] for r in generation},token_delta=None,token_note='Worker tools do not expose reliable per-pass token usage; supervisor retains original frozen record and computes the delta.')
(OUT/'STATUS.json').write_text(json.dumps(status,indent=2))
root=read(ROOT/'STATUS.json');frozen=read(ROOT/'FirstDelivery/STATUS.json')
for key in ['started_at_utc','started_at_kst','finished_at_utc','finished_at_kst','elapsed_seconds']:assert root.get(key)==frozen.get(key),'First-delivery timing changed: '+key
root['status']='ready_for_review';root['phase']='texture_pass_complete';root['texture_pass']=status;root['texture_pass']['first_delivery_commit']='f335695925b1ff23ea8633dee9449274f3378159'
(ROOT/'STATUS.json').write_text(json.dumps(root,indent=2))
lines=[
'# Quietwater Grove — Forest ultra texture pass',
'',
'Status: **ready_for_review**. No Git/index operations were performed. Supervisor owns the second-pass commit.',
'',
'## Actual timing',
'',
f'- Started UTC: {start.isoformat()}; KST: {start.astimezone(kst).isoformat()}.',
f'- Finished UTC: {now.isoformat()}; KST: {now.astimezone(kst).isoformat()}.',
f'- Elapsed wall seconds: {status["elapsed_seconds"]:.3f}.',
f'- UE queue/mutex wait: {status["ue_queue_wait_seconds"]:.3f}s; execution: {status["ue_execution_seconds"]:.3f}s. All attempts included; per-run UTC records are in `Execution/`.',
'- Built-in image_gen observed call latency: '+', '.join(f'{r["name"]} {r["elapsed_seconds"]:.0f}s' for r in generation)+'. Canopy/Stone/Wood calls overlapped; their durations must not be added to wall time.',
'- `timing_correction.json` preserves the erroneous interim elapsed value and its UTC correction. The initial start timestamp is unchanged. Capture and queue timestamps were checked using UTC-aware parsing.',
'- Per-pass token delta is unavailable to worker tools; supervisor should compute it against the preserved first-delivery token record.',
'',
'## Delivered paths',
'',
'- `ForestDemo/Content/Maps/ultra.umap`.',
'- `ForestDemo/Content/Forest/ultra/`: original owned assets plus 922 UV mesh variants and four generated-image textures; updated materials.',
'- `ForestDemo/Work/ultra/TexturePass/`: source FBX, original images, prompts, scripts, audit data and actual screenshots.',
'- Frozen `FirstDelivery/` and original root `RESULT.md` are unchanged. Root STATUS retains the original timing fields and adds a separate texture_pass record.',
'',
'## Validation evidence',
'',
f'- Fresh saved-map process: {summary["checks_passed"]} checks passed; {summary["dependency_packages"]} packages recursively checked, zero forbidden /Game dependencies. No old /Game/ultra refs, World Partition, external actor/object packages or baked-lighting data.',
f'- 922 scale-baked prop variants preserve original saved positions/rotations; final actor scales are all 1. Total measured world surface area {uv["world_area_m2"]:.3f}m², summed UV area {uv["uv_area_sum"]:.6f} across separate atlases.',
f'- Target 32px/m; per-mesh measured area-weighted range {uv["density_min"]:.8f}–{uv["density_max"]:.8f}px/m. {int(uv["island_count"]):,} triangle islands, zero overlapping bounding boxes, minimum separation {uv["minimum_padding_gap"]:.6f}px. Independent FBX re-import measurements are in `uv_fbx_validation.json`.',
'- UE UV channels/full precision, material slot mapping, four actual 1254×1254 textures and solid-prop collision were checked after asset compilation completed. Generation prompts/raw originals/SHA256 are in `Generated/generation_records.json`.',
'- Actual PIE created a PlayerController with possessed pawn, moved it through a horizontal sweep, blocked downward movement on terrain, traced trees/rocks/ground and exited play normally. See `runtime_validation.json`.',
f'- Actual downward HitResult: blocking_hit=true, initial_overlap=false, hit fraction {runtime["player_test"]["downward_sweep_hit"]["time"]:.6f}, hit distance {runtime["player_test"]["downward_sweep_hit"]["distance_cm"]:.6f}cm; actual pawn displacement {runtime["player_test"]["downward_sweep_hit"]["actual_move_distance_cm"]:.6f}cm. Hit actor, component and static mesh all equal the owned SM_Ground. This is not only a final-position test.',
f'- Seven original UE SceneCapture2D images at 1920×1080: overview, top_down, lake, beach, hero, water_t0, water_t1. Common camera/render settings are preserved. Fixed water camera world-time separation {motion["shader_world_time_delta_seconds"]:.3f}s; {motion["changed_percent"]:.2f}% of sampled pixels changed by at least 12 summed RGB units. Visual review confirmed water detail changes; the numeric difference can also contain temporal rendering noise.',
f'- Private editor closed before publication; {len(publication["files"])} files copied and SHA256 matched. See `publication.json`.',
'',
'## Limitations and interpretation',
'',
'- Sea/lake waves, crest foam and ground caustics are animated artistic shaders, not physical refraction or ray-traced caustic transport. Ground and water use world-space detail rather than prop atlas density.',
'- Final foam is integrated into the sea material with soft animated cellular breakup; legacy thin surf ribbons are hidden. The analytic crest bands retain some periodicity. `normal_audit.json` confirms continuous shared-vertex normals in broadleaf, pine and rock FBX samples; texture contrast was reduced after actual render review.',
'- Triangle islands trade paint continuity for exact metric density and a simple provable overlap check. Very small faces can be subpixel. 32 existing zero-area triangles are excluded from density; UE removes degenerate geometry. Nondegenerate per-triangle measurements range 31.8926–32.0937px/m due to precision on tiny faces.',
'- Original NPOT texture outputs remain unchanged, with NoMipmaps/NeverStream. This has a memory/aliasing tradeoff. Per-placement mesh variants also increase asset count and reduce mesh sharing.',
'- `texture_source_links.json` connects each raw image output and SHA256 to its preserved original, UE texture and material-binding evidence. `publication.json` includes these links and hashes of the final evidence files.',
'- Surface images modulate the retained palette through luminance. Small petal/iron/sand accents retain their first-pass materials; prop UVs are still unique. No hand-painted seam continuity or physical texture scale for these untextured accents is claimed.',
'- Native Hello logger presence/PIE lifecycle is verified through the existing baseline class; clean render captures exclude debug text.',
'',
'## References',
'',
'- Built-in image_gen tool, this effort’s own first-pass source geometry and scene scripts, UE5.7 installed engine headers/source for Python/material APIs, and Blender 4.5 background FBX import/export.',
'- `/Engine/MapTemplates/Sky/DaylightAmbientCubemap` and baseline `/Script/ForestDemo.ScreenDebugLogger` are shared read-only engine/project resources. No external or other-effort asset references.',
'',
'![Texture-pass overview](Screenshots/overview.png)',
'',
'![Beach with animated water](Screenshots/beach.png)',
]
(OUT/'RESULT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'status':status['status'],'finished_at_utc':status['finished_at_utc'],'elapsed_seconds':status['elapsed_seconds'],'summary':summary},indent=2))
