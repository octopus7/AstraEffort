import unreal as u,json,os,time,datetime,traceback,math
ROOT='D:/github/AstraEffort/ForestDemo/Work/medium/TexturePass'
os.makedirs(ROOT+'/Screenshots',exist_ok=True)
level=u.get_editor_subsystem(u.LevelEditorSubsystem);level.load_level('/Game/Maps/medium')
actors=u.get_editor_subsystem(u.EditorActorSubsystem);allactors=actors.get_all_level_actors()
reg=u.AssetRegistryHelpers.get_asset_registry();reg.search_all_assets(True)
reg.scan_paths_synchronous(['/Game/Forest/medium','/Game/Maps'],force_rescan=True)
opts=u.AssetRegistryDependencyOptions(True,True,True,True,True)
todo=['/Game/Maps/medium']+[str(a.package_name) for a in reg.get_assets_by_path('/Game/Forest/medium',recursive=True)]
seen=set();bad=[];edges={}
while todo:
 p=todo.pop()
 if p in seen:continue
 seen.add(p);deps=[str(x) for x in reg.get_dependencies(p,opts)];edges[p]=deps
 for d in deps:
  if d.startswith('/Game/'):
   if not (d.startswith('/Game/Forest/medium/') or d=='/Game/Maps/medium'):bad.append(d)
   else:todo.append(d)
ground=next(a for a in allactors if a.get_actor_label()=='Ground');bounds=ground.get_actor_bounds(False)
report={'reloaded':True,'actor_count':len(allactors),'ground_bounds_origin':str(bounds[0]),'ground_bounds_extent':str(bounds[1]),'ground_collision':str(ground.static_mesh_component.static_mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag')),'player_start':sum(isinstance(a,u.PlayerStart) for a in allactors),'logger':sum(a.get_class().get_name()=='ScreenDebugLogger' for a in allactors),'dependency_packages':len(seen),'bad_dependencies':bad,'dependencies':edges,'world_partition':str(u.EditorLevelLibrary.get_editor_world().get_world_settings().get_editor_property('world_partition')) if False else 'new_level non-World-Partition; no external package dirs'}
ss=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
report['solid_prop_simple_collision_counts']={}
for name in ['Tree0','Tree1','Tree2','Rock0','Rock1','Rock2','Shrub0','Shrub1','Log']:
 mesh=u.load_asset('/Game/Forest/medium/Meshes/'+name)
 report['solid_prop_simple_collision_counts'][name]=(ss.get_simple_collision_count(mesh)+ss.get_convex_collision_count(mesh))
json.dump(report,open(ROOT+'/validation.json','w'),indent=2)
assert all(n>0 for n in report['solid_prop_simple_collision_counts'].values())
report['mesh_instance_counts']={}
for a in allactors:
 if isinstance(a,u.StaticMeshActor):
  name=a.static_mesh_component.static_mesh.get_name();report['mesh_instance_counts'][name]=report['mesh_instance_counts'].get(name,0)+1
report['validated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not bad;assert abs(bounds[1].x-5000)<2 and abs(bounds[1].y-5000)<2;assert report['player_start']==1 and report['logger']==1
json.dump(report,open(ROOT+'/validation.json','w'),indent=2)
exec(open(ROOT+'/validate_textures.py').read(),globals())
world=u.EditorLevelLibrary.get_editor_world()
for cmd in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','r.ScreenPercentage 100','r.TextureStreaming 0']:
 u.SystemLibrary.execute_console_command(world,cmd)
capture=actors.spawn_actor_from_class(u.SceneCapture2D,u.Vector(12000,-12000,16000));comp=capture.get_component_by_class(u.SceneCaptureComponent2D)
rt=u.RenderingLibrary.create_render_target2d(world,1920,1080,u.TextureRenderTargetFormat.RTF_RGBA8)
comp.texture_target=rt;comp.capture_source=u.SceneCaptureSource.SCS_FINAL_COLOR_LDR;comp.capture_every_frame=False
comp.set_mobility(u.ComponentMobility.MOVABLE)
capture.root_component.set_mobility(u.ComponentMobility.MOVABLE)
comp.post_process_settings=next(a for a in allactors if isinstance(a,u.PostProcessVolume)).settings
comp.post_process_blend_weight=1.0
comp.set_editor_property('always_persist_rendering_state',True)
def height(x,y):
 h=.8+.7*math.sin(x*.073)*math.sin(y*.09)+1.9*math.exp(-((x-27)**2+(y-31)**2)/500)+1.3*math.exp(-((x+32)**2+(y-33)**2)/400)
 coast=-32+2*math.sin(x*.07)
 if y<coast+8:h=min(h,(y-coast)*.13)
 return h-2.4*math.exp(-(((x+15)/13)**2+((y-13)/10)**2)*1.8)
views=[('overview',(12000,-12000,16000),(0,0,0),'orthographic'),('top_down',(0,0,20000),None,'orthographic'),('lake',(-300,200,height(-3,2)*100+170),(-1700,1400,100),'perspective'),('beach',(1400,-2650,height(14,-26.5)*100+170),(-1000,-3600,50),'perspective')]
manifest={'site_center_cm':[0,0],'Z0_cm':0,'map':'/Game/Maps/medium','resolution':[1920,1080],'quality':'High (sg.*=2), screen percentage 100','capture_method':'SceneCapture2D FinalColorLDR, actual UE renderer','captures':[]}
manifest['closeup_eye_height_cm']=170
manifest['closeup_comparison_limit']='Lake and beach positions are site-specific; only height and horizontal FOV are normalized.'
views += [('water_t0',views[3][1],views[3][2],'perspective'),('water_t1',views[3][1],views[3][2],'perspective')]
index=0;frames=0;started=time.time()
def setup():
 name,loc,target,projection=views[index];rot=u.Rotator(pitch=-90,yaw=0,roll=0) if target is None else u.MathLibrary.find_look_at_rotation(u.Vector(*loc),u.Vector(*target))
 capture.set_actor_location_and_rotation(u.Vector(*loc),rot,False,False)
 comp.set_world_location_and_rotation(u.Vector(*loc),rot,False,False)
 comp.projection_type=u.CameraProjectionMode.ORTHOGRAPHIC if projection=='orthographic' else u.CameraProjectionMode.PERSPECTIVE;comp.ortho_width=20000;comp.fov_angle=70
 manifest['captures'].append({'name':name,'location_cm':loc,'actual_component_location':str(comp.get_world_location()),'rotation_pitch_yaw_roll':[rot.pitch,rot.yaw,rot.roll],'projection':projection,'ortho_width_cm':20000 if projection=='orthographic' else None,'horizontal_fov':70 if projection=='perspective' else None})
setup()
def tick(dt):
 global frames,index,handle
 try:
  frames+=1
  if frames%60==0:comp.capture_scene()
  if frames<240 or time.time()-started<25:return
  name=views[index][0];u.RenderingLibrary.export_render_target(world,rt,ROOT+'/Screenshots',name+'.png');manifest['captures'][-1]['captured_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();manifest['captures'][-1]['world_time_seconds']=u.GameplayStatics.get_time_seconds(world);json.dump(manifest,open(ROOT+'/Screenshots/capture_manifest.json','w'),indent=2)
  index+=1;frames=0
  if index==len(views):
   actors.destroy_actor(capture);u.unregister_slate_post_tick_callback(handle);exec(open(ROOT+'/runtime_validation.py').read(),globals());return
  setup()
 except Exception:
  open(ROOT+'/capture_error.txt','w').write(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)


