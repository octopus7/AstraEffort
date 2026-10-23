"""Private full-editor build + actual viewport capture. No shared project writes."""
import unreal as u, json, time, math, traceback, hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max')
SRC=ROOT/'Source'; ASSET='/Game/SnowyOnsen/max'; MAP='/Game/Maps/SnowyOnsen_max'
manifest=json.loads((SRC/'scene_manifest.json').read_text())
EAL=u.EditorAssetLibrary; tools=u.AssetToolsHelpers.get_asset_tools(); MEL=u.MaterialEditingLibrary
actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
editor=u.get_editor_subsystem(u.UnrealEditorSubsystem);sms=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
def now():return datetime.now(timezone.utc).isoformat()
def dump(name,value):(ROOT/'Validation'/name).write_text(json.dumps(value,indent=2,default=str),encoding='utf8')
def log(t):u.log('SNOWY_ONSEN '+str(t))
def node(m,cls,x=0,y=0):return MEL.create_material_expression(m,cls,x,y)
def const(m,value):
 n=node(m,u.MaterialExpressionConstant);n.set_editor_property('r',float(value));return n
def color(m,value):
 n=node(m,u.MaterialExpressionConstant3Vector);n.set_editor_property('constant',u.LinearColor(*value,1));return n
def link(a,b,inp,out=''):
 pin={'Coordinates':'UVs','Input':''}.get(inp,inp)
 assert MEL.connect_material_expressions(a,out,b,pin),(a.get_class().get_name(),b.get_class().get_name(),pin,list(MEL.get_material_expression_input_names(b)))
def prop(a,m,p,out=''):assert MEL.connect_material_property(a,out,p)
def mul(m,a,b):
 n=node(m,u.MaterialExpressionMultiply);link(a,n,'A');link(b,n,'B');return n
def spawn(cls,label,loc=(0,0,0),rot=None):
 a=actors.spawn_actor_from_class(cls,u.Vector(*loc),rot or u.Rotator(pitch=0,yaw=0,roll=0));a.set_actor_label(label);return a
def movable(component):component.set_mobility(u.ComponentMobility.MOVABLE)

def import_all():
 EAL.make_directory(ASSET+'/Textures');EAL.make_directory(ASSET+'/Materials');EAL.make_directory(ASSET+'/Meshes')
 textures={};tasks=[]
 for name,info in manifest['materials'].items():
  if not info['texture']:continue
  t=u.AssetImportTask();t.filename=str(SRC/info['texture']);t.destination_path=ASSET+'/Textures';t.destination_name='T_'+name;t.automated=True;t.replace_existing=True;t.save=True;tasks.append((name,t))
 tools.import_asset_tasks([t for _,t in tasks])
 for name,t in tasks:
  tex=u.load_asset(ASSET+'/Textures/T_'+name);assert tex,name;textures[name]=tex
  if name=='Steam':tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_DEFAULT)
  EAL.save_loaded_asset(tex)
 log('textures imported')
 materials={}
 for name,info in manifest['materials'].items():
  p=ASSET+'/Materials/M_'+name;m=u.load_asset(p)
  if m:MEL.delete_all_material_expressions(m)
  else:m=tools.create_asset('M_'+name,ASSET+'/Materials',u.Material,u.MaterialFactoryNew())
  if name=='Steam':
   m.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT);m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);m.set_editor_property('two_sided',True)
   tx=node(m,u.MaterialExpressionTextureSample);tx.texture=textures[name]
   mask=node(m,u.MaterialExpressionTextureSample);mask.texture=textures[name]
   pan=node(m,u.MaterialExpressionPanner);pan.set_editor_property('speed_x',.025);pan.set_editor_property('speed_y',.07);link(pan,tx,'Coordinates')
   opacity=node(m,u.MaterialExpressionMultiply);link(tx,opacity,'A','R');link(mask,opacity,'B','A')
   opacity=mul(m,opacity,const(m,.40));fade=node(m,u.MaterialExpressionDepthFade);fade.set_editor_property('fade_distance_default',65.0);link(opacity,fade,'Opacity')
   prop(fade,m,u.MaterialProperty.MP_OPACITY);prop(color(m,(.72,.86,.91)),m,u.MaterialProperty.MP_EMISSIVE_COLOR)
  else:
   if name in textures:
    tx=node(m,u.MaterialExpressionTextureSample);tx.texture=textures[name];base=tx
   else:base=color(m,info['color'])
   if name=='Water':
    pan=node(m,u.MaterialExpressionPanner);pan.set_editor_property('speed_x',.015);pan.set_editor_property('speed_y',-.009);link(pan,tx,'Coordinates')
    tm=node(m,u.MaterialExpressionTime);sine=node(m,u.MaterialExpressionSine);sine.set_editor_property('period',5.7);link(tm,sine,'Input')
    offset=mul(m,sine,color(m,(0,0,1.3)));prop(offset,m,u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    prop(mul(m,base,const(m,.25)),m,u.MaterialProperty.MP_EMISSIVE_COLOR)
   if name=='Window':prop(mul(m,base,const(m,2.2)),m,u.MaterialProperty.MP_EMISSIVE_COLOR)
   prop(base,m,u.MaterialProperty.MP_BASE_COLOR);prop(const(m,.58 if name=='Water' else info['roughness']),m,u.MaterialProperty.MP_ROUGHNESS)
   prop(const(m,.05 if name=='Water' else .25),m,u.MaterialProperty.MP_SPECULAR)
  MEL.layout_material_expressions(m);MEL.recompile_material(m);EAL.save_loaded_asset(m);materials[name]=m
 log('materials created')
 meshes={}
 for info in manifest['meshes']:
  name=info['name'];task=u.AssetImportTask();task.filename=str(SRC/info['fbx']);task.destination_path=ASSET+'/Meshes';task.destination_name=name;task.automated=True;task.replace_existing=True;task.save=True
  opt=u.FbxImportUI()
  for key,value in {'import_mesh':True,'import_materials':False,'import_textures':False,'import_as_skeletal':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH}.items():opt.set_editor_property(key,value)
  data=opt.get_editor_property('static_mesh_import_data')
  for key,value in {'combine_meshes':True,'auto_generate_collision':False,'generate_lightmap_u_vs':False,'import_uniform_scale':1.0,'convert_scene':True,'normal_import_method':u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS}.items():data.set_editor_property(key,value)
  task.options=opt;tools.import_asset_tasks([task]);mesh=u.load_asset(ASSET+'/Meshes/'+name);assert mesh,(name,list(task.imported_object_paths))
  slots=list(mesh.get_editor_property('static_materials'))
  for slot in slots:
   key=str(slot.get_editor_property('material_slot_name'));assert key in materials,(name,key);slot.set_editor_property('material_interface',materials[key])
  mesh.set_editor_property('static_materials',slots)
  EAL.save_loaded_asset(mesh);meshes[name]=mesh;log('mesh imported '+name)
 return materials,meshes

def make_world(meshes):
 if EAL.does_asset_exist(MAP):
  assert levels.load_level(MAP)
  for a in actors.get_all_level_actors():
   if not isinstance(a,(u.WorldSettings,u.Brush)):actors.destroy_actor(a)
 else:assert levels.new_level(MAP)
 world=editor.get_editor_world();ws=world.get_world_settings();ws.set_editor_property('force_no_precomputed_lighting',True)
 assert ws.get_editor_property('world_partition') is None
 for name,mesh in meshes.items():
  a=spawn(u.StaticMeshActor,name);comp=a.static_mesh_component;comp.set_static_mesh(mesh);comp.set_editor_property('cast_shadow',name!='SM_Steam');a.tags=['SnowyOnsen','max','OriginalSource']
  if name=='SM_Steam':comp.set_editor_property('translucency_sort_priority',2)
 # Winter daylight with a soft warm grazing key and cool sky fill.
 sun=spawn(u.DirectionalLight,'WinterSun',rot=u.Rotator(pitch=-37,yaw=-42,roll=0));light=sun.get_component_by_class(u.DirectionalLightComponent);movable(light);light.set_intensity(5.0);light.set_light_color(u.LinearColor(1,.94,.86,1));light.set_editor_property('light_source_angle',5.0)
 sky=spawn(u.SkyLight,'WinterSky',(0,0,2500));sc=sky.get_component_by_class(u.SkyLightComponent);movable(sc);sc.set_intensity(1.5);sc.set_editor_property('real_time_capture',True)
 spawn(u.SkyAtmosphere,'WinterAtmosphere')
 fog=spawn(u.ExponentialHeightFog,'DistantWinterHaze',(0,0,-500));fc=fog.get_component_by_class(u.ExponentialHeightFogComponent);fc.set_editor_property('fog_density',.008);fc.set_editor_property('fog_height_falloff',.2);fc.set_editor_property('start_distance',7000.0);fc.set_editor_property('fog_inscattering_luminance',u.LinearColor(.42,.61,.72,1))
 # Local amber pools of light, fully dynamic.
 for i,(x,y,z) in enumerate(manifest['lights_m']):
  a=spawn(u.PointLight,'LanternGlow_%02d'%i,(x*100,y*100,z*100));lc=a.get_component_by_class(u.PointLightComponent);movable(lc);lc.set_intensity(130.0);lc.set_light_color(u.LinearColor(1,.43,.13,1));lc.set_attenuation_radius(420.0);lc.set_editor_property('cast_shadows',False)
 pp=spawn(u.PostProcessVolume,'CalmWinterGrade');pp.set_editor_property('unbound',True)
 settings=pp.get_editor_property('settings')
 for key,val in {'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,'auto_exposure_apply_physical_camera_exposure':False,'auto_exposure_bias':.7,'bloom_intensity':.25,'vignette_intensity':.13,'motion_blur_amount':0.0,'color_saturation':u.Vector4(1.03,1.03,1.03,1.03)}.items():
  settings.set_editor_property('override_'+key,True);settings.set_editor_property(key,val)
 pp.set_editor_property('settings',settings)
 camera=spawn(u.CameraActor,'CaptureCamera',(12000,-12000,16000));camera.get_component_by_class(u.CameraComponent).set_editor_property('aspect_ratio',16/9)
 EAL.save_directory(ASSET,only_if_is_dirty=False,recursive=True);assert levels.save_current_level()
 log('world saved')

def validate():
 assert levels.load_level(MAP)
 world=editor.get_editor_world();ws=world.get_world_settings()
 report={'at_utc':now(),'map':MAP,'world_partition_is_none':ws.get_editor_property('world_partition') is None,'force_no_precomputed_lighting':ws.get_editor_property('force_no_precomputed_lighting'),'mesh_checks':[],'editor_only_visualizers':[],'material_textures':{},'lights':[],'dependencies':{},'errors':[]}
 assert report['world_partition_is_none'];assert report['force_no_precomputed_lighting']
 allactors=actors.get_all_level_actors();meshpackages=set();matpackages=set();texpackages=set()
 for a in allactors:
  c=a.get_component_by_class(u.StaticMeshComponent)
  if c and c.static_mesh and c.get_editor_property('is_editor_only'):
   report['editor_only_visualizers'].append({'actor':a.get_actor_label(),'mesh':c.static_mesh.get_path_name(),'is_editor_only':True});c=None
  if c and c.static_mesh:
   mesh=c.static_mesh;pkg=mesh.get_path_name().split('.')[0];meshpackages.add(pkg);assert pkg.startswith(ASSET+'/'),(a.get_actor_label(),pkg)
   box=mesh.get_bounding_box();mn=box.min;mx=box.max;name=mesh.get_name();record={'mesh':pkg,'actor':a.get_actor_label(),'bounds_cm':{'min':[mn.x,mn.y,mn.z],'max':[mx.x,mx.y,mx.z]},'vertex_count_lod0':sms.get_number_verts(mesh,0),'uv_channels':sms.get_num_uv_channels(mesh,0),'materials':[]}
   assert record['uv_channels']>=1;assert record['vertex_count_lod0']>0
   source=next(i for i in manifest['meshes'] if i['name']==name);dims=[mx.x-mn.x,mx.y-mn.y,mx.z-mn.z];srcdims=[(b-a)*100 for a,b in zip(source['bounds_m']['min'],source['bounds_m']['max'])]
   loc=a.get_actor_location();scale=a.get_actor_scale3d();record['actor_location_cm']=[loc.x,loc.y,loc.z];record['actor_scale']=[scale.x,scale.y,scale.z];record['actor_rotation']=str(a.get_actor_rotation())
   assert all(abs(v-1)<1e-5 for v in record['actor_scale']);assert all(abs(v)<1e-5 for v in record['actor_location_cm'])
   record['authored_position_error_cm']=max(abs(v-src*100) for actual,key in [(record['bounds_cm']['min'],'min'),(record['bounds_cm']['max'],'max')] for v,src in zip(actual,source['bounds_m'][key]))
   assert record['authored_position_error_cm']<2.0,(name,record['authored_position_error_cm'])
   record['source_dimensions_cm']=srcdims;record['import_dimensions_cm']=dims;record['scale_error_cm']=max(abs(a-b) for a,b in zip(sorted(dims),sorted(srcdims)));assert record['scale_error_cm']<2.0,(name,record)
   for i in range(c.get_num_materials()):
    m=c.get_material(i);assert m,(name,i);mp=m.get_path_name().split('.')[0];assert mp.startswith(ASSET+'/');matpackages.add(mp);record['materials'].append(mp)
    ts=MEL.get_used_textures(m);report['material_textures'][mp]=[t.get_path_name().split('.')[0] for t in ts]
    for t in ts:
     tp=t.get_path_name().split('.')[0];assert tp.startswith(ASSET+'/');texpackages.add(tp)
   report['mesh_checks'].append(record)
  for lc in a.get_components_by_class(u.LightComponentBase):
   mobility=str(lc.get_editor_property('mobility'));report['lights'].append({'actor':a.get_actor_label(),'mobility':mobility});assert lc.get_editor_property('mobility')==u.ComponentMobility.MOVABLE
 assert len(meshpackages)==16
 reg=u.AssetRegistryHelpers.get_asset_registry();reg.scan_paths_synchronous([ASSET,'/Game/Maps'],force_rescan=True)
 options=u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=False,include_hard_management_references=False)
 todo=[MAP];seen=set()
 while todo:
  p=todo.pop()
  if p in seen:continue
  seen.add(p);deps=sorted(set(str(n) for n in reg.get_dependencies(p,options)));report['dependencies'][p]=deps
  for d in deps:
   if d.startswith('/Game/'):
    assert d==MAP or d.startswith(ASSET+'/'),('foreign dependency',p,d)
    todo.append(d)
 actual={p for p in seen if p.startswith('/Game/')}
 report['used_package_coverage']={'meshes':sorted(meshpackages),'materials':sorted(matpackages),'textures':sorted(texpackages),'recursive_game_packages':sorted(actual),'missing':sorted((meshpackages|matpackages|texpackages)-actual)}
 assert report['dependencies'][MAP], 'Empty map dependency graph is not validation'
 assert not report['used_package_coverage']['missing'],report['used_package_coverage']['missing']
 report['status']='passed';dump('unreal_validation.json',report);log('validation passed '+str(len(actual))+' game packages')

def capture():
 world=editor.get_editor_world();camera=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='CaptureCamera');cc=camera.get_component_by_class(u.CameraComponent)
 for cmd in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','sg.ShadingQuality 2','r.ScreenPercentage 100','r.DynamicRes.OperationMode 0','r.MotionBlurQuality 0','r.Streaming.PoolSize 2000','r.TextureStreaming 0','r.VSync 0']:
  u.SystemLibrary.execute_console_command(world,cmd)
 views=[
  {'name':'overview','location':[12000,-12000,16000],'target':[0,0,0],'ortho':20000},
  {'name':'top_down','location':[0,0,20000],'rotation':[-90,0,0],'ortho':20000},
  {'name':'onsen','location':[1450,-2850,1100],'target':[-150,-100,300],'fov':64},
  {'name':'village','location':[-1000,-3300,1050],'target':[-1200,1000,500],'fov':64},
  {'name':'water_t0','location':[100,-2270,650],'target':[-300,-850,170],'fov':58},
  {'name':'water_t1','location':[100,-2270,650],'target':[-300,-850,170],'fov':58},
 ]
 state={'index':0,'phase':'set','at':time.monotonic()+15,'busy':False,'task':None,'deadline':time.monotonic()+700,'records':[]}
 def tick(dt):
  if state['busy']:return
  state['busy']=True
  try:
   if time.monotonic()>state['deadline']:raise RuntimeError('Capture deadline exceeded')
   if time.monotonic()<state['at']:return
   i=state['index']
   if i>=len(views):
    (ROOT/'Screenshots'/'capture_manifest.json').write_text(json.dumps({'renderer':'UE5.7 actual editor viewport HighResScreenshot','resolution':[1920,1080],'quality':'High (all sg.* 2)','screen_percentage':100,'view_mode':'Lit','game_view':True,'ui_grid_debug':False,'motion':'artistic time-driven Water panner/WPO and Steam panner, not physical fluids','captures':state['records']},indent=2),encoding='utf8')
    u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor();return
   spec=views[i];path=ROOT/'Screenshots'/(spec['name']+'.png')
   if state['phase']=='set':
    if path.exists():path.unlink()
    loc=u.Vector(*spec['location']);rot=u.Rotator(pitch=spec['rotation'][0],yaw=spec['rotation'][1],roll=spec['rotation'][2]) if 'rotation' in spec else u.MathLibrary.find_look_at_rotation(loc,u.Vector(*spec['target']))
    camera.set_actor_location_and_rotation(loc,rot,False,False)
    cc.set_editor_property('projection_mode',u.CameraProjectionMode.ORTHOGRAPHIC if 'ortho' in spec else u.CameraProjectionMode.PERSPECTIVE)
    if 'ortho' in spec:cc.set_editor_property('ortho_width',spec['ortho'])
    else:cc.set_editor_property('field_of_view',spec['fov'])
    levels.pilot_level_actor(camera);levels.editor_set_game_view(True);u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT);u.AutomationLibrary.set_editor_active_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
    assert u.AutomationLibrary.get_editor_active_viewport_view_mode()==u.ViewModeIndex.VMI_LIT
    state['rotation']=[rot.pitch,rot.yaw,rot.roll];state['phase']='take';state['at']=time.monotonic()+9
   elif state['phase']=='take':
    # Advance state before capture: slate can re-enter from screenshot API.
    state['phase']='wait';state['at']=time.monotonic()+4;state['capture_utc']=now();state['capture_monotonic']=time.monotonic()
    state['task']=u.AutomationLibrary.take_high_res_screenshot(1920,1080,str(path),camera=None,force_game_view=True)
    log('capture requested '+spec['name'])
   else:
    if not path.exists():state['at']=time.monotonic()+2;return
    data=path.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';width=int.from_bytes(data[16:20],'big');height=int.from_bytes(data[20:24],'big');assert(width,height)==(1920,1080)
    record=dict(spec);record.update(rotation=state['rotation'],captured_at_utc=state['capture_utc'],monotonic_seconds=state['capture_monotonic'],file=path.name,sha256=hashlib.sha256(data).hexdigest(),width=width,height=height,active_view_mode=str(u.AutomationLibrary.get_editor_active_viewport_view_mode()))
    state['records'].append(record);state['index']+=1;state['phase']='set';state['at']=time.monotonic()+1
  except Exception:
   dump('capture_error.json',{'at_utc':now(),'traceback':traceback.format_exc()});u.log_error(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
  finally:state['busy']=False
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 handle=u.register_slate_post_tick_callback(tick)
 globals()['_capture_keepalive']=(tick,handle,state,camera)

if __name__=='__main__':
 try:
  log('begin '+now());u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
  materials,meshes=import_all();make_world(meshes);validate();capture()
 except Exception:
  dump('build_error.json',{'at_utc':now(),'traceback':traceback.format_exc()});u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
