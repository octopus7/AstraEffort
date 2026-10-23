import unreal as u, json, time, traceback, math
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max')
ART=ROOT/'SourceArt'; EVID=ROOT/'Evidence'
ASSET='/Game/SkyObservatory/max'; MAP='/Game/Maps/SkyObservatory_max'
def write(name,obj):(EVID/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def log(s):u.log('SKYMAX '+str(s))
def prop(o,k,v):o.set_editor_property(k,v)
tools=u.AssetToolsHelpers.get_asset_tools(); actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
u.EditorPythonScripting.set_keep_python_script_alive(True)

def import_textures():
 tasks=[]
 for path in sorted((ART/'Textures').glob('*.png')):
  task=u.AssetImportTask();task.filename=str(path);task.destination_path=ASSET+'/Textures';task.automated=True;task.save=True;task.replace_existing=True;tasks.append(task)
 tools.import_asset_tasks(tasks)
 return {p.stem[2:]:u.load_asset(ASSET+'/Textures/'+p.stem) for p in (ART/'Textures').glob('*.png')}

def make_materials(textures):
 params=json.loads((ART/'materials.json').read_text());mats={}
 for name,p in params.items():
  path=ASSET+'/Materials/M_'+name
  mat=u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else tools.create_asset('M_'+name,ASSET+'/Materials',u.Material,u.MaterialFactoryNew())
  u.MaterialEditingLibrary.delete_all_material_expressions(mat)
  tex=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionTextureSample,-500,0);tex.texture=textures[name]
  u.MaterialEditingLibrary.connect_material_property(tex,'RGB',u.MaterialProperty.MP_BASE_COLOR)
  for y,value,target in [(200,p['roughness'],u.MaterialProperty.MP_ROUGHNESS),(300,p['metallic'],u.MaterialProperty.MP_METALLIC)]:
   node=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant,-300,y);node.r=value;u.MaterialEditingLibrary.connect_material_property(node,'',target)
  if name in ['Window','Star']:
   mult=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionMultiply,-100,-180);prop(mult,'const_b',2.2 if name=='Window' else 1.2)
   u.MaterialEditingLibrary.connect_material_expressions(tex,'RGB',mult,'A');u.MaterialEditingLibrary.connect_material_property(mult,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
  if name=='Lens':
   mult=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionMultiply,-100,-180);prop(mult,'const_b',.28)
   u.MaterialEditingLibrary.connect_material_expressions(tex,'RGB',mult,'A');u.MaterialEditingLibrary.connect_material_property(mult,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
  prop(mat,'two_sided',False);u.MaterialEditingLibrary.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat);mats[name]=mat
 return mats

def import_meshes(mats):
 tasks=[]
 for path in sorted((ART/'Meshes').glob('*.fbx')):
  options=u.FbxImportUI();options.import_mesh=True;options.import_materials=False;options.import_textures=False;options.import_as_skeletal=False
  options.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;options.automated_import_should_detect_type=False
  data=options.static_mesh_import_data
  prop(data,'combine_meshes',True);prop(data,'generate_lightmap_u_vs',False);prop(data,'auto_generate_collision',False)
  prop(data,'normal_import_method',u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
  prop(data,'convert_scene',True);prop(data,'convert_scene_unit',True);prop(data,'import_uniform_scale',1.0)
  task=u.AssetImportTask();task.filename=str(path);task.destination_path=ASSET+'/Meshes';task.destination_name=path.stem;task.automated=True;task.save=True;task.replace_existing=True;task.options=options;tasks.append(task)
 tools.import_asset_tasks(tasks)
 imported=[];smss=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
 for path in sorted((ART/'Meshes').glob('*.fbx')):
  mesh=u.load_asset(ASSET+'/Meshes/'+path.stem);assert isinstance(mesh,u.StaticMesh),path
  slots=list(mesh.get_editor_property('static_materials'))
  for slot in slots:
   n=str(slot.material_slot_name);key=n if n in mats else n.split('_')[0]
   assert key in mats,(mesh.get_name(),n);slot.material_interface=mats[key]
  prop(mesh,'static_materials',slots)
  settings=smss.get_lod_build_settings(mesh,0);prop(settings,'use_full_precision_u_vs',True);prop(settings,'generate_lightmap_u_vs',False)
  smss.set_lod_build_settings(mesh,0,settings)
  u.EditorAssetLibrary.save_loaded_asset(mesh);imported.append(mesh)
 return imported

def spawn(cls,label,location=(0,0,0),rotation=None):
 a=actors.spawn_actor_from_class(cls,u.Vector(*location),rotation or u.Rotator(pitch=0,yaw=0,roll=0));a.set_actor_label(label);return a
def look_at(location,target):return u.MathLibrary.find_look_at_rotation(u.Vector(*location),u.Vector(*target))
def make_scene(meshes):
 assert levels.new_level(MAP,False)
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();ws=world.get_world_settings();prop(ws,'force_no_precomputed_lighting',True)
 for mesh in meshes:
  a=actors.spawn_actor_from_object(mesh,u.Vector(0,0,0),u.Rotator(pitch=0,yaw=0,roll=0));a.set_actor_label(mesh.get_name())
  comp=a.get_component_by_class(u.StaticMeshComponent);comp.set_mobility(u.ComponentMobility.STATIC)
  if mesh.get_name()=='SM_CloudLayer':prop(comp,'cast_shadow',False)
 sun=spawn(u.DirectionalLight,'Dusk_Warm_Key',rotation=u.Rotator(pitch=-22,yaw=-36,roll=0))
 lc=sun.get_component_by_class(u.DirectionalLightComponent);lc.set_mobility(u.ComponentMobility.MOVABLE);lc.set_intensity(4.0);lc.set_light_color(u.LinearColor(1.0,.76,.53,1))
 prop(lc,'atmosphere_sun_light',True);prop(lc,'light_source_angle',3.0)
 fill=spawn(u.DirectionalLight,'Moon_Cool_Fill',rotation=u.Rotator(pitch=-35,yaw=145,roll=0))
 fc=fill.get_component_by_class(u.DirectionalLightComponent);fc.set_mobility(u.ComponentMobility.MOVABLE);fc.set_intensity(.65);fc.set_light_color(u.LinearColor(.38,.56,1.0,1));prop(fc,'cast_shadows',False)
 sky=spawn(u.SkyLight,'Dusk_Ambient');sk=sky.get_component_by_class(u.SkyLightComponent);sk.set_mobility(u.ComponentMobility.MOVABLE);prop(sk,'real_time_capture',True);sk.set_intensity(.85)
 atmosphere=spawn(u.SkyAtmosphere,'Evening_Sky')
 ac=atmosphere.get_component_by_class(u.SkyAtmosphereComponent);prop(ac,'rayleigh_scattering_scale',1.8);prop(ac,'mie_scattering_scale',1.2)
 fog=spawn(u.ExponentialHeightFog,'Soft_Lower_Atmosphere',(0,0,-2300));fg=fog.get_component_by_class(u.ExponentialHeightFogComponent)
 prop(fg,'fog_density',.007);prop(fg,'fog_height_falloff',.12);prop(fg,'fog_inscattering_luminance',u.LinearColor(.15,.20,.31,1));prop(fg,'fog_max_opacity',.55)
 pp=spawn(u.PostProcessVolume,'Calm_Dusk_Grade');prop(pp,'unbound',True);s=pp.get_editor_property('settings')
 for k,v in {'override_auto_exposure_method':True,'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,'override_auto_exposure_bias':True,'auto_exposure_bias':.6,'override_auto_exposure_apply_physical_camera_exposure':True,'auto_exposure_apply_physical_camera_exposure':False,'override_bloom_intensity':True,'bloom_intensity':.25,'override_vignette_intensity':True,'vignette_intensity':.12}.items():prop(s,k,v)
 prop(pp,'settings',s)
 # Local warm pools accompany emissive windows; all authored lights are movable.
 for i,p in enumerate([(-500,-340,850),(700,-600,900),(-3200,-1700,720),(1500,-3100,650),(3300,1400,1050),(-2700,3500,1450)]):
  a=spawn(u.PointLight,'Warm_Lantern_Pool_'+str(i),p);c=a.get_component_by_class(u.PointLightComponent);c.set_mobility(u.ComponentMobility.MOVABLE);c.set_intensity(4500 if i<4 else 2500);c.set_light_color(u.LinearColor(1,.44,.13,1));prop(c,'attenuation_radius',1100);prop(c,'source_radius',90);prop(c,'cast_shadows',False)
 # Fixed common cameras are exact; detail cameras are authored perspective views.
 specs=[('overview',(12000,-12000,16000),(0,0,0),20000),('top_down',(0,0,20000),(0,0,0),20000),('observatory',(4300,-5100,3500),(-200,100,1000),None),('bridge',(4200,-3300,1800),(1000,-700,300),None)]
 manifest=[]
 for name,pos,target,ortho in specs:
  rot=u.Rotator(pitch=-90,yaw=0,roll=0) if name=='top_down' else look_at(pos,target)
  cam=spawn(u.CameraActor,'Capture_'+name,pos,rot);cc=cam.get_component_by_class(u.CameraComponent)
  prop(cc,'aspect_ratio',16/9);prop(cc,'constrain_aspect_ratio',False)
  if ortho:prop(cc,'projection_mode',u.CameraProjectionMode.ORTHOGRAPHIC);prop(cc,'ortho_width',ortho)
  else:prop(cc,'field_of_view',48.0)
  manifest.append({'name':name,'location_cm':pos,'rotation_degrees':{'pitch':rot.pitch,'yaw':rot.yaw,'roll':rot.roll},'target_cm':target,'projection':'orthographic' if ortho else 'perspective','ortho_width_cm':ortho,'fov_degrees':None if ortho else 48.0})
 write('camera_specs.json',manifest)
 actors.clear_actor_selection_set();assert levels.save_current_level();u.EditorAssetLibrary.save_directory(ASSET,only_if_is_dirty=False,recursive=True)
 log('BUILD_SAVED')

def run_build():
 try:
  begin=time.time();tex=import_textures();mats=make_materials(tex);meshes=import_meshes(mats);make_scene(meshes)
  write('build_summary.json',{'textures':len(tex),'materials':len(mats),'meshes':len(meshes),'build_seconds':time.time()-begin,'saved_map':MAP})
  # The validation/capture phase opens the saved package afresh after a transient blank world.
  u.EditorLoadingAndSavingUtils.new_blank_map(False)
  assert levels.load_level(MAP)
  exec(compile((ROOT/'Source/validate_capture.py').read_text(encoding='utf-8'),str(ROOT/'Source/validate_capture.py'),'exec'),globals())
 except Exception:
  write('build_error.json',{'traceback':traceback.format_exc(),'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())});u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()

if __name__=='__main__':run_build()
