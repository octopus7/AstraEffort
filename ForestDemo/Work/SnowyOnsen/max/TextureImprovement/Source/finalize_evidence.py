"""Finalize new-pass machine evidence without modifying source images/assets."""
import json,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
P=Path(r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max/TextureImprovement')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
now=datetime.now(timezone.utc).isoformat()
g=read(P/'ImageGen/generation_manifest.json')
for r in g['requests']:
 name=r['key'].title();selected=P/'ImageGen'/('T_IMG_'+name+'.png');original=Path(r['original_path']);assert sha(selected)==sha(original)
 d=selected.read_bytes();size=[int.from_bytes(d[16:20],'big'),int.from_bytes(d[20:24],'big')];assert size==[1254,1254]
 r.update(selected_relative_path='T_IMG_'+name+'.png',selected_original_sha256=sha(selected),original_sha256=sha(original),source_resolution=size,byte_identical_to_original=True)
 r['visual_inspection']='Inspected original flat albedo and real UE repeated close surfaces. Raw edge mismatch is measured in image_source_analysis; mirror addressing reverses motifs/slopes. No bitmap editing.'
 r['surface_mapping']='Wood/DarkWood 2.5m component grain UV; deterministic caps and bent centerlines' if name=='Timber' else 'Stone/Path 2.5m world triplanar' if name=='Stone' else 'Snow 5m world triplanar'
g['sum_request_duration_seconds']=sum(r['duration_seconds'] for r in g['requests']);write(P/'ImageGen/generation_manifest.json',g)
log=(P/'Logs/ue_03.log').read_text(encoding='utf8',errors='replace');records=[];stage='initial load'
for line in log.splitlines():
 if 'TEXTURE_RESIDENCY_AT_CAPTURE ' in line:stage=line.split('TEXTURE_RESIDENCY_AT_CAPTURE ')[1]
 if '/Game/SnowyOnsen/max/Textures/T_IMG_' not in line or ',PF_DXT1,' not in line:continue
 fields=line.split(']',2)[-1].strip().split(',');assert len(fields)==16
 records.append({'capture_stage':stage,'max_size':[int(fields[0]),int(fields[1])],'current_resident_size':[int(fields[4]),int(fields[5])],'format':fields[7],'asset':fields[9],'streaming_now':fields[10],'num_mips':int(fields[14]),'log_line':line})
resident=[r for r in records if r['capture_stage']!='initial load'];assert len(resident)==9
assert all(r['max_size']==[2048,2048] and r['current_resident_size']==[2048,2048] and r['num_mips']==12 for r in resident)
write(P/'Validation/texture_runtime_mips.json',{'at_utc':now,'source_log':'Logs/ue_03.log','source_image_size':[1254,1254],'UE_native_build_resize':'StretchToPowerOfTwo','actual_built_size':[2048,2048],'mip_levels':12,'source_pixels_edited':False,'records':records,'note':'Capture disables streaming to ensure residency, same as baseline capture. Assets retain never_stream=False. Native upsampling adds no source detail.'})
assert not re.search(r'Failed to compile Material|Missing Sine input|LogPython: Error:',log)
fresh=read(P/'Validation/fresh_reload_asset_match.json');assert fresh['status']=='passed' and fresh['all_captured_asset_hashes_match']
assert read(P/'Validation/ue_timing_04.json')['exit_code']==0
snapshot=read(P/'Validation/captured_asset_snapshot.json')
for row in snapshot['files']:assert sha(Path(row['private']))==row['sha256']
capture=read(P/'Screenshots/capture_manifest.json')
for r in capture['captures']:assert sha(P/'Screenshots'/r['file'])==r['sha256']
write(P/'Validation/render_validation_chain.json',{'at_utc':now,'clean_render_attempt':2,'final_capture_attempt':3,'final_capture_process_exit':-1073741819,'fresh_exact_asset_validator_attempt':4,'fresh_validator_exit':0,'same_asset_bytes_through_attempts_02_03_04':True,'file_count':46,'final_capture_manifest_sha256':sha(P/'Screenshots/capture_manifest.json'),'final_render_material_compile_warnings':0,'root_cause_of_post_log_close_native_failure':'Not established; no own Saved/Crashes artifact found. No claim of engine crash fix.','scope':'UE04 NullRHI validates saved map/dependencies/asset hashes only; actual visuals and resident mip evidence are UE02/03 D3D captures.'})
write(P/'Validation/worker_visual_review.json',{'at_utc':now,'worker_viewed_all_eight':True,'captures':{r['name']:r['sha256'] for r in capture['captures']},'blocking_findings':[],'observations':['Longitudinal timber grain follows deck boards, straight beams and curved rails.','Stone mineral variation and subdued snow remain readable in close views without overwhelming wide composition.','No conspicuous mirror tile fold observed in inspected wood/stone/snow close views; cap/bevel/bend UV phase seams remain deliberate exceptions.','Water broad stripes replaced by subtle organic moving variation; steam remains original crossed cards.'],'limitations':['Wood planar exceptions cover4.31% of Wood area, with localized anisotropy and phase seams.','Mirror repeat is2x each tile length and reverses slopes/motifs.','Opaque artistic water, no refraction/fluid simulation; crossed-card steam can reveal its planes.','Strong baseline warm window lighting and dark cliff fronts retained for same-light comparisons.']})
print('Final evidence: source originals unchanged,2048x2048/12mips resident,8capture hashes,46asset hashes,clean04.',flush=True)
