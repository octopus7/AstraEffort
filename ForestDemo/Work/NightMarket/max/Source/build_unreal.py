import unreal as u, json, math, datetime, traceback
from pathlib import Path

WORK=Path(r'D:/github/AstraEffort/ForestDemo/Work/NightMarket/max')
DATA=json.loads((WORK/'Source'/'source_manifest.json').read_text(encoding='utf-8'))
ROOT='/Game/NightMarket/max'; MAP='/Game/Maps/NightMarket_max'
EVID=WORK/'Evidence'; EVID.mkdir(exist_ok=True)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(name,data):(EVID/name).write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')
def v(t):return u.Vector(*t)
def arr(t):return [float(t.x),float(t.y),float(t.z)]
assets=u.AssetToolsHelpers.get_asset_tools(); actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
def cmd(s):u.SystemLibrary.execute_console_command(u.EditorLevelLibrary.get_editor_world(),s)
def const(mat,val,x=0,y=0):
 n=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant,x,y);n.set_editor_property('r',val);return n
def col(mat,rgb,x=0,y=0):
 n=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant3Vector,x,y);n.set_editor_property('constant',u.LinearColor(*rgb,1));return n
def conn(n,mat,prop):u.MaterialEditingLibrary.connect_material_property(n,'',prop)
def spawn(cls,label,loc=(0,0,0),rot=(0,0,0)):
 a=actors.spawn_actor_from_class(cls,v(loc),u.Rotator(pitch=rot[0],yaw=rot[1],roll=rot[2]));a.set_actor_label(label);return a
def make_mat(name,info):
 m=u.load_asset(ROOT+'/Materials/M_NM_'+name) if u.EditorAssetLibrary.does_asset_exist(ROOT+'/Materials/M_NM_'+name) else assets.create_asset('M_NM_'+name,ROOT+'/Materials',u.Material,u.MaterialFactoryNew())
 u.MaterialEditingLibrary.delete_all_material_expressions(m)
 c=col(m,info['color'],-500,0)
 if info['texture']:
  tx=u.load_asset(ROOT+'/Textures/'+info['texture']);n=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionTextureSample,-700,180);n.set_editor_property('texture',tx)
  mul=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionMultiply,-220,0);u.MaterialEditingLibrary.connect_material_expressions(c,'',mul,'A');u.MaterialEditingLibrary.connect_material_expressions(n,'RGB',mul,'B');c=mul
 conn(c,m,u.MaterialProperty.MP_BASE_COLOR)
 conn(const(m,info['roughness'],-250,260),m,u.MaterialProperty.MP_ROUGHNESS)
 conn(const(m,info['metallic'],-250,350),m,u.MaterialProperty.MP_METALLIC)
 if info['emissive']:
  em=col(m,[f*info['emissive'] for f in info['color']],-250,500);conn(em,m,u.MaterialProperty.MP_EMISSIVE_COLOR)
 # All surfaces opaque; water is a low-roughness shallow artistic surface.
 u.MaterialEditingLibrary.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m);return m

try:
 started=now();cmd('Interchange.FeatureFlags.Import.FBX 0')
 for sub in ['Meshes','Materials','Textures']:u.EditorAssetLibrary.make_directory(ROOT+'/'+sub)
 # Import deterministic authored PNGs through the full editor, with Slate available.
 tasks=[]
 for f in sorted((WORK/'Source'/'Textures').glob('*.png')):
  t=u.AssetImportTask();t.filename=str(f);t.destination_path=ROOT+'/Textures';t.automated=True;t.replace_existing=True;t.save=True;tasks.append(t)
 assets.import_asset_tasks(tasks)
 mats={n:make_mat(n,info) for n,info in DATA['materials'].items()}
 imported=[]
 for entry in DATA['meshes']:
  t=u.AssetImportTask();t.filename=str(WORK/'Source'/'Exports'/entry['file']);t.destination_path=ROOT+'/Meshes';t.destination_name=entry['name'];t.automated=True;t.replace_existing=True;t.save=True
  opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False
  sd=opt.static_mesh_import_data;sd.combine_meshes=True;sd.generate_lightmap_u_vs=False;sd.auto_generate_collision=False;sd.convert_scene=True;sd.convert_scene_unit=True;sd.force_front_x_axis=False
  sd.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
  t.options=opt;t.factory=u.FbxFactory();assets.import_asset_tasks([t])
  mesh=u.load_asset(ROOT+'/Meshes/'+entry['name'])
  if mesh is None:raise RuntimeError('Import missing '+entry['name'])
  slots=mesh.get_editor_property('static_materials')
  assigned=[]
  for i,slot in enumerate(slots):
   nm=str(slot.get_editor_property('material_slot_name'));im=str(slot.get_editor_property('imported_material_slot_name'))
   key=nm if nm in mats else im
   if key not in mats:raise RuntimeError('Unrecognized material slot '+entry['name']+' '+nm+' '+im)
   slot.set_editor_property('material_interface',mats[key]);slots[i]=slot;assigned.append(key)
  mesh.set_editor_property('static_materials',slots)
  u.EditorAssetLibrary.save_loaded_asset(mesh)
  bounds=mesh.get_bounds();imported.append({'name':entry['name'],'bounds_origin_cm':arr(bounds.origin),'bounds_extent_cm':arr(bounds.box_extent),'materials':assigned,'source':entry})
 # Determine actual exporter/importer axis conversion from all asymmetric assemblies.
 candidates=[]
 for swap in [False,True]:
  for sx in [-1,1]:
   for sy in [-1,1]:
    err=0
    for e in imported:
     s=e['source'];c=[(s['bounds_min_m'][i]+s['bounds_max_m'][i])*50 for i in range(3)]
     pred=[sx*c[1 if swap else 0],sy*c[0 if swap else 1],c[2]];err+=sum(abs(pred[i]-e['bounds_origin_cm'][i]) for i in range(3))
    candidates.append((err,swap,sx,sy))
 error,swap,sx,sy=min(candidates)
 if error>len(imported)*10:raise RuntimeError('Unexpected FBX unit/axis conversion '+str(min(candidates)))
 # Rotate imported front direction to face the negative Unreal Y entry camera.
 front=[sx*(-1 if swap else 0),sy*(0 if swap else -1)]
 yaw=-90-math.degrees(math.atan2(front[1],front[0]));a=math.radians(yaw)
 def xyz(p):
  xx=sx*p[1 if swap else 0]*100;yy=sy*p[0 if swap else 1]*100
  return [xx*math.cos(a)-yy*math.sin(a),xx*math.sin(a)+yy*math.cos(a),p[2]*100]
 levels.new_level(MAP,False)
 world=u.EditorLevelLibrary.get_editor_world();world.get_world_settings().set_editor_property('force_no_precomputed_lighting',True)
 mesh_checks=[]
 for e in imported:
  me=u.load_asset(ROOT+'/Meshes/'+e['name']);actor=spawn(u.StaticMeshActor,e['name'],rot=(0,yaw,0));co=actor.static_mesh_component;co.set_static_mesh(me);co.set_mobility(u.ComponentMobility.STATIC)
  origin,extent=actor.get_actor_bounds(False)
  n_uv=u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_num_uv_channels(me,0)
  mesh_checks.append({'name':e['name'],'actor_bounds_origin_cm':arr(origin),'actor_bounds_extent_cm':arr(extent),'uv_channels':n_uv,'material_count':co.get_num_materials(),'slot_names':e['materials'],'asset':me.get_path_name()})
 # Quiet dusk backdrop authored as material on the permitted Engine sphere.
 sky=u.load_asset(ROOT+'/Materials/M_NM_EveningSky') if u.EditorAssetLibrary.does_asset_exist(ROOT+'/Materials/M_NM_EveningSky') else assets.create_asset('M_NM_EveningSky',ROOT+'/Materials',u.Material,u.MaterialFactoryNew());u.MaterialEditingLibrary.delete_all_material_expressions(sky);sky.set_editor_property('two_sided',True);sky.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);sky.set_editor_property('is_sky',True)
 conn(col(sky,[.055,.11,.18]),sky,u.MaterialProperty.MP_EMISSIVE_COLOR);u.MaterialEditingLibrary.recompile_material(sky);u.EditorAssetLibrary.save_loaded_asset(sky)
 dome=spawn(u.StaticMeshActor,'Evening backdrop');dome.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Sphere'));dome.static_mesh_component.set_material(0,sky);dome.static_mesh_component.set_editor_property('cast_shadow',False);dome.static_mesh_component.set_editor_property('receives_decals',False);dome.set_actor_scale3d(v([800,800,800]))
 sun=spawn(u.DirectionalLight,'Cool blue-hour key',(0,0,10000),(-48,-32,0));lc=sun.get_component_by_class(u.DirectionalLightComponent);lc.set_mobility(u.ComponentMobility.MOVABLE);lc.set_intensity(2.3);lc.set_light_color(u.LinearColor(.51,.69,1.0,1));lc.set_editor_property('light_source_angle',5)
 skyl=spawn(u.SkyLight,'Evening ambient');sc=skyl.get_component_by_class(u.SkyLightComponent);sc.set_mobility(u.ComponentMobility.MOVABLE);sc.set_intensity(1.4);sc.set_editor_property('real_time_capture',True);sc.set_editor_property('lower_hemisphere_is_black',False)
 for i,li in enumerate(DATA['lights']):
  act=spawn(u.PointLight,'Warm pool %02d %s'%(i,li['name']),xyz(li['location']));lc=act.get_component_by_class(u.PointLightComponent);lc.set_mobility(u.ComponentMobility.MOVABLE);lc.set_editor_property('intensity_units',u.LightUnits.LUMENS);lc.set_intensity(li['intensity']);lc.set_light_color(u.LinearColor(*li['color'],1));lc.set_attenuation_radius(li['radius']*100);lc.set_editor_property('source_radius',35);lc.set_editor_property('soft_source_radius',50);lc.set_editor_property('cast_shadows',i<10)
 pp=spawn(u.PostProcessVolume,'NightMarket art direction');pp.set_editor_property('unbound',True);settings=pp.get_editor_property('settings')
 props={'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,'auto_exposure_bias':0.3,'auto_exposure_apply_physical_camera_exposure':False,'bloom_intensity':.25,'vignette_intensity':.12,'motion_blur_amount':0,'film_grain_intensity':0,'ambient_occlusion_intensity':.6,'dynamic_global_illumination_method':u.DynamicGlobalIlluminationMethod.LUMEN,'reflection_method':u.ReflectionMethod.LUMEN}
 for k,val in props.items():
  settings.set_editor_property(k,val);settings.set_editor_property('override_'+k,True)
 pp.set_editor_property('settings',settings)
 camera_defs=[
  {'name':'overview','location':[12000,-12000,16000],'target':[0,0,0],'orthographic':True,'ortho_width':20000},
  {'name':'top_down','location':[0,0,20000],'rotation':[-90,0,0],'orthographic':True,'ortho_width':20000},
  {'name':'market','location':xyz([0,-21,5.3]),'target':xyz([0,-3,2.8]),'orthographic':False,'fov':67},
  {'name':'alley','location':xyz([-25,-31,5.8]),'target':xyz([-16,10,4]),'orthographic':False,'fov':61}
 ]
 for cd in camera_defs:
  rot=u.Rotator(pitch=cd['rotation'][0],yaw=cd['rotation'][1],roll=cd['rotation'][2]) if 'rotation'in cd else u.MathLibrary.find_look_at_rotation(v(cd['location']),v(cd['target']))
  cam=actors.spawn_actor_from_class(u.CameraActor,v(cd['location']),rot);cam.set_actor_label('Capture_'+cd['name']);cc=cam.get_component_by_class(u.CameraComponent);cc.set_editor_property('aspect_ratio',1920/1080);cc.set_editor_property('constrain_aspect_ratio',True)
  if cd['orthographic']:cc.set_editor_property('projection_mode',u.CameraProjectionMode.ORTHOGRAPHIC);cc.set_editor_property('ortho_width',cd['ortho_width']);cc.set_editor_property('auto_calculate_ortho_planes',False);cc.set_editor_property('ortho_near_clip_plane',-40000);cc.set_editor_property('ortho_far_clip_plane',120000)
  else:cc.set_editor_property('field_of_view',cd['fov'])
  actual=cam.get_actor_rotation();cd['actual_rotation']=[actual.pitch,actual.yaw,actual.roll]
  if cd['name']=='top_down':assert abs(actual.pitch+90)<.01 and abs(actual.yaw)<.01 and abs(actual.roll)<.01,cd
 assert abs(sun.get_actor_rotation().pitch+48)<.01 and abs(sun.get_actor_rotation().yaw+32)<.01,'Directional light rotation mismatch'
 u.EditorAssetLibrary.save_directory(ROOT,False,True);levels.save_current_level()
 write('build_validation.json',{'started_at_utc':started,'finished_at_utc':now(),'map':MAP,'axis_conversion':{'summed_bounds_error_cm':error,'swap_xy':swap,'sx':sx,'sy':sy,'actor_yaw':yaw},'imported_assets':imported,'placed_meshes':mesh_checks,'camera_definitions':camera_defs,'world_partition':str(world.get_world_settings().get_editor_property('world_partition')),'static_lighting_disabled':world.get_world_settings().get_editor_property('force_no_precomputed_lighting'),'materials':len(mats)+1,'source_meshes':len(imported),'lights':len(DATA['lights'])+2})
 (WORK/'Source'/'camera_definitions.json').write_text(json.dumps(camera_defs,indent=2),encoding='utf-8')
 u.log('NIGHT_MARKET_BUILD_COMPLETE');u.SystemLibrary.quit_editor()
except Exception:
 write('build_error.json',{'at':now(),'traceback':traceback.format_exc()});u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
