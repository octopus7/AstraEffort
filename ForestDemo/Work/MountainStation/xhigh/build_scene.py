import unreal as u, json, time, traceback
from pathlib import Path
from datetime import datetime, timezone
WORK=Path('D:/github/AstraEffort/ForestDemo/Work/MountainStation/xhigh')
ROOT='/Game/MountainStation/xhigh'
MAP='/Game/Maps/MountainStation_xhigh'
START=time.time()
def utc():return datetime.now(timezone.utc).isoformat()
def save_report(name,data):(WORK/'Evidence'/name).write_text(json.dumps(data,indent=2))
try:
 u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 assets=u.AssetToolsHelpers.get_asset_tools()
 palette=json.loads((WORK/'SourceArt/palette.json').read_text())
 materials={}
 for name,color in palette.items():
  path=ROOT+'/Materials/M_'+name
  mat=u.load_asset(path) or assets.create_asset('M_'+name,ROOT+'/Materials',u.Material,u.MaterialFactoryNew())
  u.MaterialEditingLibrary.delete_all_material_expressions(mat)
  rgb=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant3Vector,-240,0)
  rgb.set_editor_property('constant',u.LinearColor(*color,1))
  u.MaterialEditingLibrary.connect_material_property(rgb,'',u.MaterialProperty.MP_BASE_COLOR)
  rough=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant,-240,180)
  rough.set_editor_property('r',.78 if name not in ['Rail','Glass','Metal'] else .35)
  u.MaterialEditingLibrary.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
  mat.set_editor_property('two_sided',True)
  if name in ['Cream','Amber']:
   glow=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant3Vector,-230,350)
   glow.set_editor_property('constant',u.LinearColor(*[c*.055 for c in color],1))
   u.MaterialEditingLibrary.connect_material_property(glow,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
  u.MaterialEditingLibrary.recompile_material(mat);materials[name]=mat
  u.EditorAssetLibrary.save_loaded_asset(mat)
 imports=[];meshes={}
 for fbx in sorted((WORK/'SourceArt').glob('*.fbx')):
  task=u.AssetImportTask();task.filename=str(fbx);task.destination_path=ROOT+'/Meshes';task.destination_name='SM_'+fbx.stem;task.automated=True;task.replace_existing=True;task.save=True
  opt=u.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
  opt.automated_import_should_detect_type=False
  data=opt.static_mesh_import_data
  data.combine_meshes=True;data.auto_generate_collision=False;data.generate_lightmap_u_vs=False
  data.import_translation=u.Vector(0,0,0);data.import_rotation=u.Rotator(0,0,0);data.import_uniform_scale=1
  data.convert_scene=True;data.convert_scene_unit=True
  task.options=opt;assets.import_asset_tasks([task])
  paths=list(task.imported_object_paths)
  mesh=next((u.load_asset(p) for p in paths if isinstance(u.load_asset(p),u.StaticMesh)),None)
  if not mesh:raise RuntimeError('FBX mesh missing '+str(paths))
  slots=mesh.get_editor_property('static_materials');names=[]
  for i,slot in enumerate(slots):
   name=str(slot.material_slot_name);names.append(name)
   key=name.split('.')[0]
   if key not in materials:raise RuntimeError('Unknown material slot '+name)
   mesh.set_material(i,materials[key])
  body=mesh.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);body.set_editor_property('double_sided_geometry',True)
  u.EditorAssetLibrary.save_loaded_asset(mesh)
  meshes[fbx.stem]=mesh
  b=mesh.get_bounds();imports.append({'assembly':fbx.stem,'asset':mesh.get_path_name(),'material_slots':names,'bounds_origin_cm':[b.origin.x,b.origin.y,b.origin.z],'bounds_extent_cm':[b.box_extent.x,b.box_extent.y,b.box_extent.z],'collision':str(body.get_editor_property('collision_trace_flag'))})
 if not u.EditorLevelLibrary.new_level(MAP):raise RuntimeError('Could not create conventional level')
 actors=u.get_editor_subsystem(u.EditorActorSubsystem)
 for name,mesh in meshes.items():
  a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));a.set_actor_label('Alder_'+name)
  a.set_actor_scale3d(u.Vector(1,-1,1)) # Blender RH to UE LH: restore authored X/Y layout after FBX conversion.
  c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_collision_profile_name('BlockAll');c.set_mobility(u.ComponentMobility.STATIC)
 # Baseline native class is kept with its unmodified BeginPlay Hello behavior.
 logger_class=u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger')
 if not logger_class:raise RuntimeError('Native ScreenDebugLogger unavailable')
 logger=actors.spawn_actor_from_class(logger_class,u.Vector(-3800,-300,120));logger.set_actor_label('ScreenDebugLogger_Hello')
 player=actors.spawn_actor_from_class(u.PlayerStart,u.Vector(-3800,-300,135),u.Rotator(0,0,0));player.set_actor_label('PlayerStart_StationApproach')
 sun=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,8000),u.Rotator(pitch=-48,yaw=-40,roll=0));sun.set_actor_label('Sun_Afternoon')
 sun.light_component.set_mobility(u.ComponentMobility.MOVABLE);sun.light_component.set_intensity(3.2);sun.light_component.set_light_color(u.LinearColor(1,.91,.76,1));sun.light_component.set_editor_property('light_source_angle',3.0)
 sun.light_component.set_editor_property('dynamic_shadow_distance_movable_light',40000)
 sky=actors.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,5000));sky.set_actor_label('Sky_SoftFill');sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
 sky.light_component.set_intensity(.85)
 cubemap=u.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap')
 if cubemap:
  sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);sky.light_component.set_editor_property('cubemap',cubemap)
 else:
  sky.light_component.set_editor_property('sky_distance_threshold',150000)
  sky.light_component.set_editor_property('lower_hemisphere_is_black',False)
 # Pale matte environment dome. Owned material, built-in geometric sphere.
 sky_mat=assets.create_asset('M_Backdrop',ROOT+'/Materials',u.Material,u.MaterialFactoryNew())
 sky_mat.set_editor_property('two_sided',True);sky_mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
 e=u.MaterialEditingLibrary.create_material_expression(sky_mat,u.MaterialExpressionConstant3Vector,0,0);e.constant=u.LinearColor(.37,.48,.53,1)
 u.MaterialEditingLibrary.connect_material_property(e,'',u.MaterialProperty.MP_EMISSIVE_COLOR);u.MaterialEditingLibrary.recompile_material(sky_mat);u.EditorAssetLibrary.save_loaded_asset(sky_mat)
 dome=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));dome.set_actor_label('Sky_Backdrop')
 dome.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Sphere'));dome.static_mesh_component.set_material(0,sky_mat);dome.set_actor_scale3d(u.Vector(2000,2000,2000));dome.static_mesh_component.set_collision_profile_name('NoCollision');dome.set_actor_enable_collision(False);dome.static_mesh_component.set_cast_shadow(False)
 pp=actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector());pp.set_actor_label('Look_StableExposure');pp.set_editor_property('unbound',True)
 settings=pp.get_editor_property('settings')
 for key,val in {'override_auto_exposure_method':True,'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,'override_auto_exposure_bias':True,'auto_exposure_bias':0.0,'override_auto_exposure_apply_physical_camera_exposure':True,'auto_exposure_apply_physical_camera_exposure':False,'override_vignette_intensity':True,'vignette_intensity':0.08,'override_bloom_intensity':True,'bloom_intensity':.15,'override_motion_blur_amount':True,'motion_blur_amount':0.0,'override_ambient_occlusion_intensity':True,'ambient_occlusion_intensity':.7}.items():settings.set_editor_property(key,val)
 pp.set_editor_property('settings',settings)
 world=u.EditorLevelLibrary.get_editor_world();ws=world.get_world_settings();ws.set_editor_property('force_no_precomputed_lighting',True)
 u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(12000,-12000,16000),u.MathLibrary.find_look_at_rotation(u.Vector(12000,-12000,16000),u.Vector(0,0,0)))
 if not u.EditorLevelLibrary.save_current_level():raise RuntimeError('Map save failed')
 u.EditorAssetLibrary.save_directory(ROOT)
 save_report('build.json',{'success':True,'utc':utc(),'duration_seconds':time.time()-START,'map':MAP,'imports':imports,'skylight_cubemap':cubemap.get_path_name() if cubemap else None})
 print('ALDER_BUILD_SUCCESS')
except Exception:
 save_report('build_error.json',{'utc':utc(),'traceback':traceback.format_exc()});raise
