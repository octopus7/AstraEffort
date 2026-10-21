import unreal as u,json,datetime,time,traceback,hashlib,os
ROOT='D:/github/AstraEffort/ForestDemo/Work/medium'
report={'requested_at_utc':'2026-10-21T13:18:00Z','process_started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'working','no_asset_or_map_save':True}
def write():json.dump(report,open(ROOT+'/supplement_validation.json','w'),indent=2)
def hashes():
 manifest=json.load(open(ROOT+'/delivery_manifest.json'));out=[]
 for f in manifest['files']:
  path=f['file'];actual=hashlib.sha256(open(path,'rb').read()).hexdigest().upper()
  private=path.replace('D:\\github\\AstraEffort\\ForestDemo\\Content','D:\\github\\AstraEffort\\ForestDemo\\Saved\\Workers\\medium\\ForestDemo\\Content').replace('D:/github/AstraEffort/ForestDemo/Content','D:/github/AstraEffort/ForestDemo/Saved/Workers/medium/ForestDemo/Content')
  private_hash=hashlib.sha256(open(private,'rb').read()).hexdigest().upper()
  assert actual==f['sha256']==private_hash,path
  out.append({'file':path,'sha256':actual,'delivery_and_scratch_match_original':True})
 return out
try:
 report['hashes_before']=hashes()
 level=u.get_editor_subsystem(u.LevelEditorSubsystem);assert level.load_level('/Game/Maps/medium')
 reg=u.AssetRegistryHelpers.get_asset_registry();reg.search_all_assets(True)
 reg.scan_paths_synchronous(['/Game/Forest/medium','/Game/Maps'],force_rescan=True)
 assets=reg.get_assets_by_path('/Game/Forest/medium',recursive=True)
 for a in assets:u.load_asset(str(a.package_name))
 reg.scan_paths_synchronous(['/Game/Forest/medium','/Game/Maps'],force_rescan=True)
 opts=u.AssetRegistryDependencyOptions(True,True,True,True,True)
 todo=['/Game/Maps/medium']+[str(a.package_name) for a in assets];seen=set();edges={};bad=[]
 while todo:
  p=todo.pop()
  if p in seen:continue
  seen.add(p);deps=sorted(str(x) for x in reg.get_dependencies(p,opts));edges[p]=deps
  for d in deps:
   if d.startswith('/Game/'):
    if d.startswith('/Game/Forest/medium/') or d=='/Game/Maps/medium':todo.append(d)
    else:bad.append(d)
 redirects=[str(a.package_name) for a in assets if str(a.asset_class_path.asset_name)=='ObjectRedirector']
 ground=u.load_asset('/Game/Forest/medium/Meshes/GroundSmooth')
 slots=[{'slot':str(s.material_slot_name),'material':s.material_interface.get_path_name()} for s in ground.static_materials]
 expected={'/Game/Forest/medium/Materials/M_'+n for n in ['Grass','Moss','Path','Sand']}
 assert expected.issubset(set(edges['/Game/Forest/medium/Meshes/GroundSmooth']))
 assert expected=={s['material'].split('.')[0] for s in slots}
 assert not bad and not redirects
 report['registry']={'force_rescan':True,'hard_and_soft_packages':True,'searchable_and_management_references':True,'package_count':len(seen),'dependencies':edges,'forbidden_dependencies':bad,'owned_redirectors':redirects,'legacy_game_medium_references':[d for ds in edges.values() for d in ds if d.startswith('/Game/medium/')],'ground_material_slots':slots,'legacy_scratch_packages_not_referenced':len(reg.get_assets_by_path('/Game/medium',recursive=True))}
 write();level.editor_request_begin_play();phase=0;ticks=0;begin=time.time()
 def tick(dt):
  global phase,ticks,handle
  try:
   ticks+=1
   if time.time()-begin>60:raise RuntimeError('PIE timeout')
   if phase==0:
    if ticks<90 or not level.is_in_play_in_editor():return
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world();pc=u.GameplayStatics.get_player_controller(world,0);pawn=pc.get_controlled_pawn();assert pawn.get_controller()==pc
    pawn.set_actor_location(u.Vector(1200,-1400,210),False,True)
    hit=pawn.set_actor_location(u.Vector(1200,-1400,-500),True,False)
    report['hit_result_python_api']={'type':str(type(hit)),'to_tuple_doc':str(getattr(hit,'to_tuple',None).__doc__)};write()
    parts=hit.to_tuple();actor=parts[9];component=parts[10]
    mesh=component.get_editor_property('static_mesh')
    report['runtime']={'world':world.get_path_name(),'pawn':pawn.get_path_name(),'blocking_hit':bool(parts[0]),'initial_overlap':bool(parts[1]),'hit_time':parts[2],'hit_distance_cm':parts[3],'location':str(parts[4]),'impact_point':str(parts[5]),'hit_actor':actor.get_path_name(),'hit_component':component.get_path_name(),'hit_mesh':mesh.get_path_name(),'actual_pawn_location':str(pawn.get_actor_location()),'requested_target_z_cm':-500}
    assert parts[0] and not parts[1] and mesh.get_name()=='GroundSmooth'
    write();level.editor_request_end_play();phase=1
   elif phase==1 and not level.is_in_play_in_editor():
    report['runtime']['normal_pie_shutdown']=True;report['hashes_after']=hashes();report['status']='passed';report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();write();u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
   elif phase==2 and not level.is_in_play_in_editor():
    report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();write();u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
  except Exception:
   report['status']='needs_attention';report['error']=traceback.format_exc();write();level.editor_request_end_play();phase=2
 handle=u.register_slate_post_tick_callback(tick)
except Exception:
 report['status']='needs_attention';report['error']=traceback.format_exc();write();u.SystemLibrary.quit_editor()
