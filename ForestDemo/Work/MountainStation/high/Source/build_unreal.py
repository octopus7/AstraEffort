import unreal as u, os, json, math, datetime, traceback, time
script_started=time.time()
ROOT='D:/github/AstraEffort/ForestDemo/Work/MountainStation/high'
BASE='/Game/MountainStation/high'
MAP='/Game/Maps/MountainStation_high'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def prop(o,k,v):o.set_editor_property(k,v)
def log(s):u.log('SOLMARU: '+str(s))
try:
 data=json.load(open(ROOT+'/Source/source_manifest.json'))
 assets=u.AssetToolsHelpers.get_asset_tools();lib=u.EditorAssetLibrary
 materials={}
 for name,color in data['palette'].items():
  path=BASE+'/Materials/M_'+name
  m=lib.load_asset(path) if lib.does_asset_exist(path) else assets.create_asset('M_'+name,BASE+'/Materials',u.Material,u.MaterialFactoryNew())
  c=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant3Vector,-300,0);prop(c,'constant',u.LinearColor(*color,1))
  u.MaterialEditingLibrary.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
  r=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant,-300,150);prop(r,'r',.72 if name!='Rail' else .3)
  u.MaterialEditingLibrary.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS)
  if name=='Lamp':u.MaterialEditingLibrary.connect_material_property(c,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
  if name=='Rail':
   e=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant,-300,250);prop(e,'r',.65);u.MaterialEditingLibrary.connect_material_property(e,'',u.MaterialProperty.MP_METALLIC)
  prop(m,'two_sided',True);u.MaterialEditingLibrary.recompile_material(m);materials[name]=m;lib.save_loaded_asset(m)
 tasks=[]
 for item in data['assemblies']:
  t=u.AssetImportTask();prop(t,'filename',item['file']);prop(t,'destination_path',BASE+'/Meshes');prop(t,'destination_name',item['name']);prop(t,'automated',True);prop(t,'replace_existing',True);prop(t,'save',True)
  opt=u.FbxImportUI();prop(opt,'import_mesh',True);prop(opt,'import_textures',False);prop(opt,'import_materials',False);prop(opt,'import_as_skeletal',False);prop(opt,'mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH)
  sd=opt.get_editor_property('static_mesh_import_data');prop(sd,'combine_meshes',True);prop(sd,'auto_generate_collision',False);prop(sd,'generate_lightmap_u_vs',False)
  prop(t,'options',opt);tasks.append(t)
 assets.import_asset_tasks(tasks)
 sub=u.get_editor_subsystem(u.UnrealEditorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem)
 level.new_level(MAP)
 actors=u.get_editor_subsystem(u.EditorActorSubsystem)
 for a in actors.get_all_level_actors():actors.destroy_actor(a)
 mesh_records=[]
 for item in data['assemblies']:
  mesh=lib.load_asset(BASE+'/Meshes/'+item['name'])
  if not mesh:raise RuntimeError('Missing '+item['name'])
  for i,slot in enumerate(mesh.get_editor_property('static_materials')):
   name=str(slot.material_slot_name).split('.')[0]
   if name in materials:mesh.set_material(i,materials[name])
   else:log('UNKNOWN MATERIAL '+name)
  body=mesh.get_editor_property('body_setup');prop(body,'collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
  lib.save_loaded_asset(mesh)
  a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));a.set_actor_label(item['name'][3:]);comp=a.static_mesh_component;comp.set_static_mesh(mesh);comp.set_collision_profile_name('BlockAll')
  bounds=mesh.get_bounds();mesh_records.append({'name':item['name'],'origin':str(bounds.origin),'extent':str(bounds.box_extent),'collision':'complex_as_simple'})
 station_mesh=lib.load_asset(BASE+'/Meshes/SM_Station')
 mirrored_y=station_mesh.get_bounds().origin.y>0
 if mirrored_y:
  for a in actors.get_all_level_actors():
   if isinstance(a,u.StaticMeshActor):a.set_actor_scale3d(u.Vector(1,-1,1))
 log('FBX handedness normalization flip Y = '+str(mirrored_y))
 sky_mat=assets.create_asset('M_SkyBackdrop',BASE+'/Materials',u.Material,u.MaterialFactoryNew())
 if not sky_mat:sky_mat=lib.load_asset(BASE+'/Materials/M_SkyBackdrop')
 prop(sky_mat,'two_sided',True);prop(sky_mat,'shading_model',u.MaterialShadingModel.MSM_UNLIT)
 col=u.MaterialEditingLibrary.create_material_expression(sky_mat,u.MaterialExpressionConstant3Vector,-300,0);prop(col,'constant',u.LinearColor(.38,.49,.53,1));u.MaterialEditingLibrary.connect_material_property(col,'',u.MaterialProperty.MP_EMISSIVE_COLOR);u.MaterialEditingLibrary.recompile_material(sky_mat);lib.save_loaded_asset(sky_mat)
 sky_dome=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector());sky_dome.set_actor_label('Quiet blue backdrop');sky_dome.static_mesh_component.set_static_mesh(lib.load_asset('/Engine/BasicShapes/Sphere'));sky_dome.set_actor_scale3d(u.Vector(2000,2000,2000));sky_dome.static_mesh_component.set_material(0,sky_mat);sky_dome.static_mesh_component.set_collision_profile_name('NoCollision');prop(sky_dome.static_mesh_component,'cast_shadow',False)
 sky_dome.set_actor_enable_collision(False)
 # Shared engine-only background is presentation context, outside the 100m authored terrain.
 a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,-160));a.set_actor_label('PresentationGround');a.static_mesh_component.set_static_mesh(lib.load_asset('/Engine/BasicShapes/Plane'));a.set_actor_scale3d(u.Vector(3000,3000,1));a.static_mesh_component.set_material(0,materials['StoneLight']);a.static_mesh_component.set_collision_profile_name('NoCollision')
 a.set_actor_enable_collision(False)
 sun=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,5000),u.Rotator(pitch=-48,yaw=-35,roll=0));sun.set_actor_label('Warm afternoon sun');sun.light_component.set_mobility(u.ComponentMobility.MOVABLE);prop(sun.light_component,'intensity',4.0);prop(sun.light_component,'light_color',u.Color(255,235,207,255));prop(sun.light_component,'light_source_angle',4.0)
 sky=actors.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,2000));sky.set_actor_label('Soft mountain skylight');sky.light_component.set_mobility(u.ComponentMobility.MOVABLE);prop(sky.light_component,'intensity',1.0)
 prop(sky.light_component,'source_type',u.SkyLightSourceType.SLS_CAPTURED_SCENE);prop(sky.light_component,'sky_distance_threshold',10000.0)
 sky.light_component.recapture_sky()
 pp=actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector());prop(pp,'unbound',True)
 settings=pp.get_editor_property('settings')
 for k,v in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_bias',True),('auto_exposure_bias',1.0),('override_auto_exposure_apply_physical_camera_exposure',True),('auto_exposure_apply_physical_camera_exposure',False),('override_bloom_intensity',True),('bloom_intensity',.12),('override_vignette_intensity',True),('vignette_intensity',.12)]:
  try:prop(settings,k,v)
  except Exception as ex:log(str(ex))
 prop(pp,'settings',settings)
 start=actors.spawn_actor_from_class(u.PlayerStart,u.Vector(-600,-3300,120),u.Rotator(pitch=0,yaw=90,roll=0));start.set_actor_label('Arrival PlayerStart')
 cls=u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger');logger=actors.spawn_actor_from_class(cls,u.Vector(0,0,100));logger.set_actor_label('ScreenDebugLogger Hello')
 world=sub.get_editor_world();ws=world.get_world_settings();prop(ws,'force_no_precomputed_lighting',True)
 cameras={
 'overview':{'location':[12000,-12000,16000],'target':[0,0,0],'ortho':20000},
 'top_down':{'location':[0,0,20000],'rotation':[-90,0,0],'ortho':20000},
 'platform':{'location':[1550,220,275],'target':[-850,-180,260],'fov':70},
 'tracks':{'location':[1970,470,170],'target':[3050,875,280],'fov':70}}
 for name,cam in cameras.items():
  loc=u.Vector(*cam['location']);rot=u.Rotator(pitch=cam['rotation'][0],yaw=cam['rotation'][1],roll=cam['rotation'][2]) if 'rotation' in cam else u.MathLibrary.find_look_at_rotation(loc,u.Vector(*cam['target']))
  a=actors.spawn_actor_from_class(u.CameraActor,loc,rot);a.set_actor_label('Camera_'+name);comp=a.camera_component
  prop(comp,'projection_mode',u.CameraProjectionMode.ORTHOGRAPHIC if 'ortho' in cam else u.CameraProjectionMode.PERSPECTIVE)
  if 'ortho' in cam:prop(comp,'ortho_width',cam['ortho'])
  else:prop(comp,'field_of_view',cam['fov'])
  cam['rotation']=[rot.pitch,rot.yaw,rot.roll]
 level.save_current_level();lib.save_directory(BASE,only_if_is_dirty=False,recursive=True)
 json.dump({'created_at_utc':now(),'map':MAP,'meshes':mesh_records,'fbx_y_normalized':mirrored_y,'cameras':cameras,'build_script_seconds':time.time()-script_started},open(ROOT+'/build_evidence.json','w'),indent=2)
 log('BUILD_COMPLETE')
 exec(compile(open(ROOT+'/Source/validate_unreal.py').read(),ROOT+'/Source/validate_unreal.py','exec'),globals())
except Exception:
 log(traceback.format_exc());raise
