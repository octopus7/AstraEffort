import unreal as u,json,datetime,os,traceback,time
ROOT='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/TexturePass'
MAP='/Game/Maps/MountainStation_high'
level=u.get_editor_subsystem(u.LevelEditorSubsystem);level.load_level(MAP)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
actor_sub=u.get_editor_subsystem(u.EditorActorSubsystem)
for cmd in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','sg.ShadingQuality 2','r.ScreenPercentage 100','r.DynamicRes.OperationMode 0','r.Shadow.Virtual.Enable 1','r.AntiAliasingMethod 2','DisableAllScreenMessages']:
 u.SystemLibrary.execute_console_command(world,cmd)
first=json.load(open('D:/github/AstraEffort/ForestDemo/Work/MountainStation/high/FirstDelivery/Screenshots/capture_manifest.json'))
cams={c['name'][:-4]:dict(location=c['location_cm'],rotation=c['rotation_pitch_yaw_roll'],**({'ortho':c['orthographic_width_cm']} if c['projection']=='orthographic' else {'fov':c['horizontal_fov_degrees']})) for c in first['captures']}
cams['top_down']['rotation']=[-90,0,0]
cap=actor_sub.spawn_actor_from_class(u.SceneCapture2D,u.Vector(0,0,20000));cap.set_actor_label('Temporary evidence capture')
comp=cap.capture_component2d
rt=u.RenderingLibrary.create_render_target2d(world,1920,1080,u.TextureRenderTargetFormat.RTF_RGBA8,u.LinearColor(.25,.3,.3,1),False)
comp.set_editor_property('texture_target',rt);comp.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
comp.set_editor_property('capture_every_frame',False);comp.set_editor_property('capture_on_movement',False)
comp.set_editor_property('always_persist_rendering_state',True)
manifest={'map':MAP,'engine':'Unreal Engine 5.7','render_method':'SceneCapture2D final color LDR, actual saved level','resolution':[1920,1080],'scalability':'High (2)','screen_percentage':100,'site_center_cm':[0,0,0],'ui':False,'captures':[]}
manifest['observed_quality_cvars']={k:u.SystemLibrary.get_console_variable_int_value(k) for k in ['sg.ViewDistanceQuality','sg.AntiAliasingQuality','sg.ShadowQuality','sg.GlobalIlluminationQuality','sg.ReflectionQuality','sg.PostProcessQuality','sg.TextureQuality','sg.EffectsQuality','sg.FoliageQuality','sg.ShadingQuality']}
manifest['observed_screen_percentage']=u.SystemLibrary.get_console_variable_float_value('r.ScreenPercentage')
queue=list(cams.items());frame=0;index=0;started=time.time()
def setcam(name,c):
 cap.set_actor_location(u.Vector(*c['location']),sweep=False,teleport=True);cap.set_actor_rotation(u.Rotator(pitch=c['rotation'][0],yaw=c['rotation'][1],roll=c['rotation'][2]),teleport_physics=True)
 comp.set_editor_property('projection_type',u.CameraProjectionMode.ORTHOGRAPHIC if 'ortho' in c else u.CameraProjectionMode.PERSPECTIVE)
 comp.set_editor_property('ortho_width',c.get('ortho',512));comp.set_editor_property('fov_angle',c.get('fov',70))
 u.log('SOLMARU_CAPTURE_CAMERA '+name+' '+str(cap.get_actor_location())+' '+str(cap.get_actor_rotation()))
 comp.capture_scene()
def tick(dt):
 global frame,index,handle
 try:
  frame+=1
  if frame==300:setcam(*queue[index])
  if frame>=300 and frame%10==0:comp.capture_scene()
  if frame>=480:
   name,c=queue[index];u.RenderingLibrary.export_render_target(world,rt,ROOT+'/Screenshots',name+'.png')
   manifest['captures'].append(dict(name=name+'.png',captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),location_cm=c['location'],rotation_pitch_yaw_roll=c['rotation'],projection='orthographic' if 'ortho' in c else 'perspective',orthographic_width_cm=c.get('ortho'),horizontal_fov_degrees=c.get('fov'),resolution=[1920,1080]))
   json.dump(manifest,open(ROOT+'/Screenshots/capture_manifest.json','w'),indent=2)
   index+=1;frame=299
   if index==len(queue):
    u.unregister_slate_post_tick_callback(handle);actor_sub.destroy_actor(cap);u.SystemLibrary.quit_editor();return
   setcam(*queue[index])
 except Exception:
  open(ROOT+'/capture_error.txt','w').write(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)

