from pathlib import Path
R=Path('D:/github/AstraEffort/ForestDemo/Work/high');T=R/'TexturePass'
s=(R/'validate_capture.py').read_text(encoding='utf-8-sig').replace("ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/high')","ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/high/TexturePass')")
extra='''
ms=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
tex=u.EditorAssetLibrary.load_asset('/Game/Forest/high/TexturePass/Textures/T_GeneratedSurfaceAtlas')
assert tex
texture_audit={'generated_texture':tex.get_path_name(),'actual_texture_size':[tex.blueprint_get_size_x(),tex.blueprint_get_size_y()],'prop_actor_count':0,'unique_meshes':{},'materials':{}}
for actor in allactors:
 if isinstance(actor,u.StaticMeshActor) and '_UV' in actor.static_mesh_component.static_mesh.get_name():
  texture_audit['prop_actor_count']+=1;mesh=actor.static_mesh_component.static_mesh
  uvcount=ms.get_num_uv_channels(mesh,0);assert uvcount>=1
  texture_audit['unique_meshes'][mesh.get_path_name()]={'uv_channels':uvcount}
  for material in actor.static_mesh_component.get_materials():
   assert material and '/TexturePass/Materials/' in material.get_path_name()
   used=[t.get_path_name() for t in u.MaterialEditingLibrary.get_used_textures(material)]
   assert tex.get_path_name() in used,(material.get_path_name(),used)
   texture_audit['materials'][material.get_path_name()]=used
assert texture_audit['prop_actor_count']==742
exports=ROOT/'Source/UEExports';exports.mkdir(exist_ok=True)
for prefix in ['SM_Broadleaf_0_UV','SM_Rock_2_UV','SM_Grass_0_UV']:
 candidates=[p for p in texture_audit['unique_meshes'] if p.split('.')[-1].startswith(prefix)]
 chosen=min(candidates,key=lambda p:abs(int(p.split('_UV')[-1])-10000))
 mesh=u.EditorAssetLibrary.load_asset(chosen)
 task=u.AssetExportTask();task.object=mesh;task.filename=str(exports/(mesh.get_name()+'.fbx'));task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=u.StaticMeshExporterFBX()
 options=u.FbxExportOption();options.set_editor_property('collision',False);task.options=options
 assert u.Exporter.run_asset_export_task(task)
(ROOT/'texture_binding_validation.json').write_text(json.dumps(texture_audit,indent=2))
'''
s=s.replace('allactors=a.get_all_level_actors()','allactors=a.get_all_level_actors()\n'+extra)
s=s.replace("manifest={'map'", "shots += [dict(shots[-1],name='water_t0'),dict(shots[-1],name='water_t1')]\nmanifest={'map'")
s=s.replace("s['captured_at_utc']=utc();", "s['captured_at_utc']=utc();s['elapsed_capture_seconds']=time.monotonic()-state['started'];s['editor_world_seconds']=u.GameplayStatics.get_time_seconds(world);")
s=s.replace("a.destroy_actor(cap);u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False)","a.destroy_actor(cap);u.unregister_slate_post_tick_callback(handle);exec(compile((ROOT/'runtime_validate.py').read_text(encoding='utf-8-sig'),str(ROOT/'runtime_validate.py'),'exec'),globals())")
(T/'validate_capture.py').write_text(s,encoding='utf-8')
r=(R/'runtime_validate.py').read_text(encoding='utf-8-sig').replace("R=Path('D:/github/AstraEffort/ForestDemo/Work/high')","R=Path('D:/github/AstraEffort/ForestDemo/Work/high/TexturePass')").replace("'2026-10-21T12:41:24+00:00'","'2026-10-21T13:43:00+00:00'")
r='\n'.join(line for line in r.splitlines() if "Shot SHOWUI" not in line)
(T/'runtime_validate.py').write_text(r,encoding='utf-8')
