import unreal as u, os, json, datetime, time, traceback
W='D:/github/AstraEffort/ForestDemo/Work/MountainStation/medium/TexturePass'
OUT=W+'/Screenshots'; os.makedirs(OUT,exist_ok=True)
MAP='/Game/Maps/MountainStation_medium'
L=u.get_editor_subsystem(u.LevelEditorSubsystem); L.load_level(MAP)
E=u.get_editor_subsystem(u.EditorActorSubsystem); world=u.EditorLevelLibrary.get_editor_world()
trace_results={}
for name,x,y,z in [('entry',-1900,-1150,300),('ramp_mid',-1900,-600,300),('platform',-2200,400,300),('track_bed',1800,881,200)]:
 hit=u.SystemLibrary.line_trace_single(world,u.Vector(x,y,z),u.Vector(x,y,-500),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],u.DrawDebugTrace.NONE)
 trace_results[name]={'blocking_hit':bool(hit and hit.to_tuple()[0]),'hit_tuple':str(hit.to_tuple()) if hit else None}
json.dump(trace_results,open(W+'/collision_validation.json','w'),indent=2)
for cmd in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','r.ScreenPercentage 100','DisableAllScreenMessages','r.TextureStreaming 0']:
 u.SystemLibrary.execute_console_command(world,cmd)
cap=E.spawn_actor_from_class(u.SceneCapture2D,u.Vector(12000,-12000,16000)); comp=cap.capture_component2d
rt=u.RenderingLibrary.create_render_target2d(world,1920,1080,u.TextureRenderTargetFormat.RTF_RGBA8,u.LinearColor(.20,.26,.29,1),False,False)
comp.texture_target=rt; comp.capture_source=u.SceneCaptureSource.SCS_FINAL_COLOR_LDR
comp.capture_every_frame=True; comp.capture_on_movement=True
pp=comp.get_editor_property('post_process_settings')
pp.set_editor_property('override_auto_exposure_method',True); pp.set_editor_property('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL)
pp.set_editor_property('override_auto_exposure_bias',True); pp.set_editor_property('auto_exposure_bias',2.0)
pp.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True); pp.set_editor_property('auto_exposure_apply_physical_camera_exposure',False)
comp.set_editor_property('post_process_settings',pp); comp.post_process_blend_weight=1
shots=[('overview',[12000,-12000,16000],[0,0,0],True),('top_down',[0,0,20000],None,True),('platform',[-2100,520,242],[-500,180,280],False),('tracks',[1800,1100,170],[3200,1200,250],False)]
records=[]; index=0; stage=0; stamp=time.time(); begun=stamp
def setshot(i):
 name,pos,target,ortho=shots[i]
 baseline=json.load(open(os.path.dirname(W)+'/FirstDelivery/capture_manifest.json'))['shots'][i]
 rot=u.Rotator(**baseline['rotation_deg'])
 cap.set_actor_location_and_rotation(u.Vector(*pos),rot,False,False)
 comp.projection_type=u.CameraProjectionMode.ORTHOGRAPHIC if ortho else u.CameraProjectionMode.PERSPECTIVE
 comp.ortho_width=20000; comp.fov_angle=70
 return {'file':name+'.png','location_cm':pos,'rotation_deg':{'pitch':rot.pitch,'yaw':rot.yaw,'roll':rot.roll},'projection':'orthographic' if ortho else 'perspective','ortho_width_cm':20000 if ortho else None,'horizontal_fov':None if ortho else 70}
record=setshot(0)
def tick(dt):
 global index,stamp,record,stage
 try:
  if time.time()-stamp<25: return
  if stage==0:
   comp.capture_every_frame=False; comp.capture_scene(); stage=1; stamp=time.time()-22; return
  u.RenderingLibrary.export_render_target(world,rt,OUT,shots[index][0]+'.png')
  record['captured_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat(); records.append(record)
  index+=1
  if index==len(shots):
   json.dump({'map':MAP,'resolution':[1920,1080],'quality':'High (sg.* 2)','screen_percentage':100,'method':'UE SceneCapture2D FinalColorLDR, manual exposure, RGBA8 export','site_center_cm':[0,0,0],'shots':records,'capture_wall_seconds':time.time()-begun},open(OUT+'/capture_manifest.json','w'),indent=2)
   u.unregister_slate_post_tick_callback(handle)
   if True: u.SystemLibrary.quit_editor()
   else: exec(compile(open(W+'/runtime_ue.py',encoding='utf-8').read(),W+'/runtime_ue.py','exec'),globals())
   return
  record=setshot(index); comp.capture_every_frame=True; stamp=time.time(); stage=0
 except Exception:
  open(W+'/capture_error.txt','w').write(traceback.format_exc()); u.unregister_slate_post_tick_callback(handle); u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)



