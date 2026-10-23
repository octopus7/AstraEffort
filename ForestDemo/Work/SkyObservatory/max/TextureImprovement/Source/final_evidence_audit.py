from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import json,hashlib,struct,re,math,time,shutil

BASE=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max')
ROOT=BASE/'TextureImprovement';E=ROOT/'Evidence'
PROJECT=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/SkyObservatory/max/Project')
PUBLIC=Path(r'D:/github/AstraEffort/ForestDemo/Content')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(name,obj):(E/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

# Original generated outputs are inspected only as immutable bytes and PNG headers.
# No pixels are edited, filtered, resized, or synthesized here.
generation=read(ROOT/'ImageGen/generation_manifest.json')['assets']+[read(ROOT/'ImageGen/auxiliary_generation_manifest.json')]
images=[]
for item in generation:
    image=ROOT/'ImageGen'/(item['name']+'_albedo_original.png');original=Path(item['generated_source_path'])
    data=image.read_bytes();size=list(struct.unpack('>II',data[16:24]));assert size==[1254,1254]
    assert sha(image)==sha(original)
    images.append({'name':item['name'],'selected_original':image.relative_to(ROOT).as_posix(),'generated_source_path':str(original),'sha256':sha(image),'bytes':len(data),'source_size':size,'unchanged_from_tool_output':True,'elapsed_seconds':item['elapsed_seconds']})
sources=read(E/'texture_source_manifest.json')['records'];assert len(sources)==13
for item in sources:
    p=ROOT/'SourceArt/Textures'/(item['texture']+'.png')
    assert sha(p)==item['source_sha256']==sha(Path(item['imagegen_original']))
runtime=read(E/'texture_runtime_validation.json')['textures'];assert len(runtime)==21
assert all(t['actual_runtime_width']==1024 and t['actual_runtime_height']==1024 and t['srgb'] for t in runtime)
rows=[]
for line in (E/'ue_phase03.log').read_text(errors='replace').splitlines():
    m=re.search(r'(/Game/SkyObservatory/max/Textures/[^,]+), (YES|NO), (YES|NO), (YES|NO), (\d+), (\d+), (YES|NO)',line)
    if m and 'PF_DXT1' in line:
        sizes=re.findall(r'(\d+)x(\d+)',line);assert sizes[:2]==[('1024','1024'),('1024','1024')]
        assert int(m[6])==11
        rows.append({'asset':m[1],'runtime_size':[1024,1024],'mip_count':int(m[6]),'pixel_format':'PF_DXT1','raw_ue_listtextures_line':line})
assert len(rows)==21 and len({r['asset'] for r in rows})==21
write('texture_final_validation.json',{'validated_at_utc':now(),'imagegen_original_count':5,'generated_originals':images,'changed_texture_sources':13,'unchanged_generated_source_copies':True,'source_resolution':[1254,1254],'native_ue_build_resolution':[1024,1024],'native_resize':'ResizeToSpecificResolution; no external image editing or padding','srgb_albedo':True,'runtime_texture_count':21,'runtime_mip_evidence':rows,'full_1024_to_1_mip_chain_verified':True,'tileability_claim':'Tileable swatches were requested and final UE surfaces were visually inspected; exact mathematical equality of opposite pixel boundaries is not claimed.'})

archive=read(BASE/'FirstDelivery/archive_manifest.json');checks=[]
for row in archive['evidence_files']:
    p=BASE/'FirstDelivery'/row['relative_path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'].lower()
    record={'relative_path':row['relative_path'],'sha256':sha(p),'archive_unchanged':True}
    if row['relative_path'] not in ['RESULT.md','STATUS.json']:
        active=BASE/row['relative_path'];assert active.stat().st_size==row['bytes'] and sha(active)==row['sha256'].lower();record['original_active_evidence_unchanged']=True
    checks.append(record)
assets=[]
for row in archive['asset_files']:
    p=Path(archive['content_snapshot'])/row['relative_path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'].lower()
    assets.append({'relative_path':row['relative_path'],'sha256':sha(p),'archive_unchanged':True})
write('first_delivery_preservation.json',{'validated_at_utc':now(),'baseline_commit':archive['baseline_commit'],'archived_work_files':len(checks),'archived_content_files':len(assets),'original_active_evidence_unchanged_except_authorized_result_status':True,'work_files':checks,'content_files':assets})

final=read(E/'saved_material_validation.json');assert final['all_21_materials_have_compiled_shader_statistics'] and final['private_package_hashes_before_after_equal']
lastlog=(E/'ue_phase05.log').read_text(errors='replace')
assert 'FINAL_SAVED_MATERIAL_VALIDATION_PASS' in lastlog
assert not any(x in lastlog for x in ['Failed to compile Material','missing input','LogPython: Error:'])
captures=read(ROOT/'Screenshots/capture_manifest.json');assert len(captures['captures'])==6
first_capture=min(datetime.fromisoformat(c['capture_requested_at_utc'].replace('Z','+00:00')) for c in captures['captures'])
for row in final['packages']:
    p=PROJECT/'Content'/row['relative_path'];assert sha(p)==row['sha256']
    assert datetime.fromtimestamp(p.stat().st_mtime,timezone.utc)<=first_capture
for c in captures['captures']:
    p=ROOT/'Screenshots'/c['file'];assert sha(p)==c['sha256'];assert struct.unpack('>II',p.read_bytes()[16:24])==(1920,1080)
baseline_captures=read(BASE/'FirstDelivery/Screenshots/capture_manifest.json')
camera_fields=['location_cm','rotation_degrees','projection','ortho_width_cm','fov_degrees']
camera_comparison=[]
for old in baseline_captures['captures']:
    new=next(c for c in captures['captures'] if c['name']==old['name'])
    assert all(old[k]==new[k] for k in camera_fields)
    camera_comparison.append({'name':old['name'],'all_camera_fields_exactly_equal':True,'baseline_sha256':old['sha256'],'improved_sha256':new['sha256']})
lighting=read(E/'lighting_camera_preservation.json');assert lighting['unchanged'] and lighting['before']==lighting['after']
write('capture_asset_identity.json',{'validated_at_utc':now(),'all_60_private_hashes_equal_fresh_saved_material_validation':True,'all_private_package_write_times_precede_final_capture_sequence':True,'final_capture_manifest_sha256':sha(ROOT/'Screenshots/capture_manifest.json'),'package_hash_source':'saved_material_validation.json','final_capture_count':6,'all_captured_png_sha256_verified':True,'lighting_exposure_existing_cameras_unchanged':True,'four_baseline_cameras_exactly_equal':camera_comparison,'scope':'Final screenshots captured after phase03 saves. Phase04 and05 only read saved assets. SHA256 before/after the final fresh validation is identical; no asset mutation or save followed final capture.'})

crashes=[]
pass_start=datetime.fromisoformat('2026-10-23T14:00:36.464+00:00').timestamp()
for p in sorted((PROJECT/'Saved/Crashes').rglob('*')):
    if p.is_file() and p.stat().st_mtime>=pass_start:
        out=E/'ShutdownDiagnostics'/p.relative_to(PROJECT/'Saved/Crashes');out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out);assert sha(out)==sha(p)
        crashes.append({'source':str(p),'copied_evidence':out.relative_to(ROOT).as_posix(),'sha256':sha(out),'bytes':p.stat().st_size})
write('shutdown_diagnostics.json',{'recorded_at_utc':now(),'nonzero_after_log_closed_attempts':[2,5],'native_exit_code':-1073741819,'final_capture_attempt':3,'final_capture_exit_code':0,'fresh_material_validation_attempt':5,'fresh_material_validation_completed_before_shutdown':True,'fresh_final_log_compile_errors':0,'native_crash_files_from_this_pass':crashes,'native_crash_context_note':'Only own Project/Saved/Crashes files dated within this pass are copied. No such file means no new native crash dump/context was emitted there; runner timings and complete native logs remain the exit evidence. Shutdown cause is unresolved, not claimed repaired.'})
print('FINAL_EVIDENCE_AUDIT_PASS',len(images),len(rows),len(checks),len(assets),len(crashes))
