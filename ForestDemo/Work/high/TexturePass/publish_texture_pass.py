"""Run only after fresh-process validation and visual review have succeeded."""
from pathlib import Path
import json,datetime,hashlib,shutil,re
R=Path('D:/github/AstraEffort/ForestDemo/Work/high/TexturePass')
P=Path('D:/github/AstraEffort/ForestDemo')
S=P/'Saved/Workers/high'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
start=datetime.datetime(2026,10,21,13,43,tzinfo=datetime.timezone.utc)
validation=read(R/'validation.json');binding=read(R/'texture_binding_validation.json')
runtime=read(R/'runtime_validation.json');uv=read(R/'uv_audit.json')
roundtrip=read(R/'ue_uv_roundtrip_validation.json');temporal=read(R/'water_temporal_validation.json')
visual=read(R/'visual_review.json');assert visual['status']=='passed'
capture=read(R/'Screenshots/capture_manifest.json')
for repair_name in ['ue_uv_precision_repair.json','seabed_depth_validation.json']:
 repaired=datetime.datetime.fromisoformat(read(R/repair_name)['saved_at_utc'])
 assert datetime.datetime.fromisoformat(validation['checked_at_utc'])>repaired
 assert datetime.datetime.fromisoformat(capture['capture_started_at_utc'])>repaired
assert not validation['forbidden_dependencies'] and not validation['external_packages'] and validation['dynamic_lighting']
assert validation['world_partition'] is None and not validation['redirector_packages'] and not validation['old_root_dependencies'] and not validation['built_data_files']
assert binding['prop_actor_count']==742 and len(binding['unique_meshes'])==228
assert roundtrip['status']=='passed' and temporal['same_camera_verified']
assert runtime['status'] in ['runtime_checks_passed_pending_native_log_review','passed']
assert runtime['checks']['pie_ended'] and runtime['checks']['pawn_possessed_by_player_0']
assert runtime['checks']['runtime_ground_collision']['sweep_blocking_hit']
log=(S/'texture_validation.log').read_text(errors='replace')
assert re.search(r'Test Completed\. Result=\{Success\}.*HelloOnBeginPlay',log)
assert 'LogExit: Exiting.' in log and 'LogPython: Error:' not in log
assert 'Failed to compile Material' not in log
timing=read(S/'texture_validation_timing.json');assert timing['exit_code']==0
runtime['status']='passed';runtime['checks']['native_hello_automation_result']='Success';runtime['checks']['normal_editor_exit']=True
write(R/'runtime_validation.json',runtime)
for name in ['texture_build','texture_validation','seabed_depth','uv_precision']:
 shutil.copy2(S/(name+'.log'),R/(name+'.log'))
 shutil.copy2(S/(name+'_timing.json'),R/(name+'_timing.json'))
timings=[read(p) for p in sorted(R.glob('*_timing.json'))]
assert len(timings)>=5
first=P/'Work/high/FirstDelivery'
frozen={str(p.relative_to(first)):digest(p) for p in first.rglob('*') if p.is_file()}
assert frozen
src=S/'ForestDemo/Content';owned=src/'Forest/high'
files=list(owned.rglob('*'));files=[p for p in files if p.is_file()]+[src/'Maps/high.umap']
validation_inputs=read(R/'validation_input_hashes.json')['files']
current_inputs={str(p.relative_to(src)).replace('\\','/'):digest(p) for p in files}
assert validation_inputs==current_inputs,'Content changed during read-only validation'
assert all('BuiltData' not in str(p) and '__External' not in str(p) for p in files)
assert all(p.suffix in ['.uasset','.umap'] for p in files)
published=[]
for f in files:
 rel=f.relative_to(src);dest=P/'Content'/rel
 assert str(rel).replace('\\','/').startswith('Forest/high/') or str(rel).replace('\\','/')=='Maps/high.umap'
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
 h=digest(f);assert digest(dest)==h
 published.append({'path':str(dest.relative_to(P)).replace('\\','/'),'sha256':h,'bytes':dest.stat().st_size})
assert frozen=={str(p.relative_to(first)):digest(p) for p in first.rglob('*') if p.is_file()}
write(R/'published_manifest.json',{'editor_exit_verified_before_publish':True,'validated_inputs_byte_identical_after_validation':True,'validation_input_manifest':'validation_input_hashes.json','first_delivery_preserved_files':len(frozen),'files':published})
finish=datetime.datetime.now(datetime.timezone.utc);kst=datetime.timezone(datetime.timedelta(hours=9));elapsed=(finish-start).total_seconds()
densities=[i['actual_chart_mean_px_per_m'] for i in uv['instances']]
sampled_densities=[a['measured_native_px_per_m'] for m in roundtrip['meshes'].values() for a in m['actual_saved_actor_density_checks']]
summary={'fresh_process_map_reload':True,'recursive_packages':validation['owned_packages_checked'],'forbidden_dependencies':0,'world_partition':False,'redirectors':0,'old_root_dependencies':0,'built_data_files':0,'uv_prop_actors':742,'uv_variants':228,'actual_texture_resolution':binding['actual_texture_size'],'saved_ue_uv_roundtrip_mesh_samples':3,'saved_ue_uv_roundtrip_actor_samples':len(sampled_densities),'source_uv_overlap_pairs':0,'saved_ue_sample_uv_overlap_pairs':0,'source_density_native_px_per_m_range':[min(densities),max(densities)],'saved_ue_sample_density_native_px_per_m_range':[min(sampled_densities),max(sampled_densities)],'source_minimum_chart_spacing_native_pixels':4,'source_minimum_outer_margin_native_pixels':2,'common_camera_pngs':4,'fixed_camera_water_time_pngs':2,'actual_pie_spawn_possession_movement_collision':True,'native_hello_beginplay':'Success','normal_editor_exit':True,'published_hash_verified_files':len(published),'first_delivery_preserved_files':len(frozen)}
status={'theme':'Forest','effort':'high','phase':'texture_pass','status':'ready_for_review','started_at_utc':start.isoformat(),'started_at_kst':start.astimezone(kst).isoformat(),'finished_at_utc':finish.isoformat(),'finished_at_kst':finish.astimezone(kst).isoformat(),'elapsed_seconds':elapsed,'imagegen_seconds':28,'ue_queue_wait_seconds':sum(t['wait_seconds'] for t in timings),'ue_execution_seconds':sum(t['execution_seconds'] for t in timings),'ue_attempts':len(timings),'map':'/Game/Maps/high','validation':summary,'blockers':[]}
write(R/'STATUS.json',status)
root=read(P/'Work/high/STATUS.json');root['status']='ready_for_review';root['phase']='texture_pass';root['texture_pass']=status;root['texture_pass_finished_at_utc']=finish.isoformat();write(P/'Work/high/STATUS.json',root)
result=f'''# Forest/high texture and beach pass

Status: ready_for_review. Separate second pass; first delivery commit `90ea6f99d308328340a732bf55357293f8a23088` and frozen FirstDelivery files are preserved. No Git operations were performed.

## Actual timing

- UTC: {start.isoformat()} to {finish.isoformat()}.
- KST: {start.astimezone(kst).isoformat()} to {finish.astimezone(kst).isoformat()}.
- Elapsed wall time: {elapsed:.3f} seconds, including queue waits and repairs.
- Imagegen: 1 actual call, 28 seconds by UTC clock (tool reported 27.4 seconds).
- UE queue wait: {status['ue_queue_wait_seconds']:.3f} seconds; execution: {status['ue_execution_seconds']:.3f} seconds across {len(timings)} attempts. Early script API failures are retained in attempt logs; process exit 0 alone was not treated as a pass.

## Delivered changes

- `Content/Forest/high/TexturePass/`: 228 UV mesh variants, a caustics seabed mesh, the original generated atlas, 23 palette materials and 2 water/caustics materials.
- `Content/Maps/high.umap`: 742 prop references updated; animated sea and underwater caustics added. Original composition, terrain footprint, pond and separate beach retained.
- `Work/high/TexturePass/Source/`: original imagegen pixels, authoring blend/FBXs, and 3 saved-UE FBX exports.
- `Screenshots/`: overview, top_down, lake, beach, water_t0 and water_t1; actual UE 1920×1080 captures with camera/time metadata.
- {len(published)} owned asset/map files hash-matched after the private editor closed. {len(frozen)} FirstDelivery files remained byte-identical during publication.

## UV and texture evidence

The generated image is actually 1254×1254, with 627×627 pixels per surface region; no upscaled pixels are counted. `imagegen_prompt.txt`, `imagegen_record.json`, `material_mapping.json` and the unmodified original document provenance and quadrant-to-material mapping. The UE binding audit confirms all 742 placed prop actors, 228 unique meshes and their used materials reference the generated texture.

Source UV charts have no positive-area overlaps. Chart area is normalized to 16 native pixels/metre, with 1.04-ratio world-scale buckets. Source-measured placed chart-average density spans {min(densities):.6f}–{max(densities):.6f} px/m; minimum chart rectangle spacing is 4 pixels, while minimum outer page margin is 2 pixels. `uv_audit.json` records surface/UV areas, bounds, scale factors, density errors and per-triangle percentiles. All variants use explicitly authored triangles and full-precision UE UVs to prevent import triangulation and half-precision distortion.

The quantitative saved-UE roundtrip audit covers exactly three mesh variants (broadleaf, rock and grass), representing {len(sampled_densities)} actual actors. Their FBX centimetre unit metadata, converted geometry areas in metres and actual saved actor scales independently determine density: {min(sampled_densities):.6f}–{max(sampled_densities):.6f} native px/m. Dimensions and geometry-unit ratios also have explicit pass thresholds. These samples passed UV area and positive-overlap checks. This sampled result is not a quantitative roundtrip claim for all 228 variants; the full set has separate texture-binding, UV-channel and precision checks. See `ue_uv_roundtrip_validation.json`.

## Water and runtime evidence

Sea shading combines two sine displacements (5cm + 2cm amplitude), moving white shoreline/crest foam, translucent color and mild refraction. A separate seabed sheet carries animated bright caustic-like interference patterns. Its maximum world Z is 64cm, at least 7cm below the theoretical lowest animated sea surface. These are artistic approximations, not a physical water or refracted-light simulation. Fixed-camera images are {temporal['wall_capture_interval_seconds']:.3f} seconds apart; {temporal['changed_pixel_fraction_over_1_255']*100:.3f}% of pixels differ by more than 1/255 in at least one channel. See temporal JSON and visual review.

Fresh-process saved-map validation checked {validation['owned_packages_checked']} recursive packages with zero forbidden dependencies, dynamic lighting, directly checked null WorldPartition, no external packages/BuiltData, no ObjectRedirector assets or old /Game/high references, 100m terrain bounds and blocking traces. Actual PIE verified PlayerStart spawn/possession, movement, downward blocking sweep, end-play and normal editor exit. The baseline native HelloOnBeginPlay test returned Success; no claim is made that Hello was captured in the clean screenshots. See validation/runtime JSONs and the full validation log.

## Limits and exceptions

- Repeated instances intentionally reuse their prop UV layout. Unique surfaces within a mesh do not overlap.
- Curved projected charts have triangle-level density variation even though chart averages are normalized. Grass_0 uses separate triangle charts to remove folded-projection overlap.
- Terrain, earth rim, lake, sea and ripple geometry retain their original UVs; this pass's unique-surface requirement applies to placed props.
- Native 627-pixel regions and 4-pixel padding limit close-up detail/mip isolation; small plants have few texels. The palette blend preserves the original stylized appearance.
- DefaultPawn uses floating movement; no walking Character was added. Refraction and caustics are view/shader approximations.
- External references: none. Only own first-pass artwork, engine built-ins, and this pass's actual imagegen output were used.
'''
(R/'RESULT.md').write_text(result,encoding='utf-8')
root_result=P/'Work/high/RESULT.md';original_result=root_result.read_text(encoding='utf-8').split('\n\n## Texture pass completed\n\n')[0]
root_result.write_text(original_result+'\n\n## Texture pass completed\n\nSeparate second-pass record: [TexturePass/RESULT.md](TexturePass/RESULT.md). Finished '+finish.isoformat()+'. Original first-delivery timestamps above are retained.\n',encoding='utf-8')
plan=(R/'PLAN.md').read_text(encoding='utf-8-sig');(R/'PLAN.md').write_text(plan.replace('- [ ]','- [x]'),encoding='utf-8')
print(json.dumps(status,indent=2))
