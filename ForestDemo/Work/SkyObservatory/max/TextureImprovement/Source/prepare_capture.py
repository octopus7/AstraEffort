from pathlib import Path
import json
BASE=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max');ROOT=BASE/'TextureImprovement'
s=(BASE/'Source/validate_capture.py').read_text(encoding='utf-8')
s=s.replace('D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max\'','D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max/TextureImprovement\'')
s=s.replace("'source_validation.json'","'geometry_baseline.json'")
s=s.replace("'screenshots':4","'screenshots':len(specs)")
s=s.replace("'map':MAP,'captures':state['records']","'map':MAP,'texture_improvement':True,'captures':state['records']")
needle="     state['phase']='done';u.unregister_slate_post_tick_callback(HANDLE);u.SystemLibrary.quit_editor()"
replacement="""     texinfo=[]
     for path in u.EditorAssetLibrary.list_assets(ASSET+'/Textures',recursive=True,include_folder=False):
      tex=u.load_asset(path);w=tex.blueprint_get_size_x();h=tex.blueprint_get_size_y();assert (w,h)==(1024,1024),(path,w,h)
      texinfo.append({'asset':path,'actual_runtime_width':w,'actual_runtime_height':h,'srgb':tex.get_editor_property('srgb'),'mip_gen_settings':str(tex.get_editor_property('mip_gen_settings')),'power_of_two_mode':str(tex.get_editor_property('power_of_two_mode')),'address_x':str(tex.get_editor_property('address_x')),'address_y':str(tex.get_editor_property('address_y'))})
     write('texture_runtime_validation.json',{'textures':texinfo,'runtime_sizes_verified':True,'mip_counts_evidence':'UE ListTextures console output in this phase log; parsed independently after clean exit'})
     u.SystemLibrary.execute_console_command(world,'ListTextures -alphasort')
     state['phase']='done';u.unregister_slate_post_tick_callback(HANDLE);u.SystemLibrary.quit_editor()"""
assert needle in s;s=s.replace(needle,replacement)
(ROOT/'Source/validate_capture.py').write_text(s,encoding='utf-8')
old=json.loads((BASE/'Evidence/source_validation.json').read_text());geo={'bounds_m':old['bounds_m'],'groups':[{'name':g['name'],'bounds_m':g['bounds_m']} for g in old['groups']]}
(ROOT/'Evidence/geometry_baseline.json').write_text(json.dumps(geo,indent=2),encoding='utf-8')
p=ROOT/'ImageGen/generation_manifest.json';m=json.loads(p.read_text());m['wall_interval_seconds']=m['wall_interval_seconds']/1000 if m['wall_interval_seconds']>1000 else m['wall_interval_seconds'];p.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
print('CAPTURE_PREPARED')
