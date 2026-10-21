import unreal as u, json, math, traceback
from pathlib import Path
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/high')
data=json.loads((ROOT/'scene.json').read_text())
E=u.EditorAssetLibrary
actorsys=u.get_editor_subsystem(u.EditorActorSubsystem)
levelsys=u.get_editor_subsystem(u.LevelEditorSubsystem)
meshsub=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
def log(s):u.log('HIGH: '+str(s))
def prop(o,k,v):o.set_editor_property(k,v)
def material(name,color):
 path='/Game/Forest/high/Materials'
 existing=E.load_asset(path+'/M_'+name)
 if existing:return existing
 asset=u.AssetToolsHelpers.get_asset_tools().create_asset('M_'+name,path,u.Material,u.MaterialFactoryNew())
 prop(asset,'two_sided',True)
 rgb=u.MaterialEditingLibrary.create_material_expression(asset,u.MaterialExpressionConstant3Vector,-500,0)
 prop(rgb,'constant',u.LinearColor(*color,1));u.MaterialEditingLibrary.connect_material_property(rgb,'',u.MaterialProperty.MP_BASE_COLOR)
 rough=u.MaterialEditingLibrary.create_material_expression(asset,u.MaterialExpressionConstant,-500,200)
 prop(rough,'r',.24 if name.startswith('Water') else .86);u.MaterialEditingLibrary.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
 if name.startswith('Water'):
  noise=u.MaterialEditingLibrary.create_material_expression(asset,u.MaterialExpressionNoise,-600,-300)
  prop(noise,'scale',.015)
  bump=u.MaterialEditingLibrary.create_material_expression(asset,u.MaterialExpressionBumpOffset,-200,-300)
  # Broad colour remains restrained; shallow roughness catches dynamic skylight.
 if name=='Foam':
  u.MaterialEditingLibrary.connect_material_property(rgb,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
 u.MaterialEditingLibrary.recompile_material(asset);E.save_loaded_asset(asset);return asset
materials={n:material(n,c) for n,c in data['palette'].items()}
meshes={}
for f in sorted((ROOT/'Source/FBX').glob('*.fbx')):
 existing=E.load_asset('/Game/Forest/high/Meshes/'+f.stem)
 if existing:
  meshes[f.stem]=existing
  continue
 task=u.AssetImportTask();prop(task,'filename',str(f));prop(task,'destination_path','/Game/Forest/high/Meshes');prop(task,'destination_name',f.stem);prop(task,'automated',True);prop(task,'replace_existing',True);prop(task,'save',True)
 opts=u.FbxImportUI();prop(opts,'import_mesh',True);prop(opts,'import_materials',False);prop(opts,'import_textures',False);prop(opts,'import_as_skeletal',False);prop(opts,'mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH)
 smopts=opts.get_editor_property('static_mesh_import_data');prop(smopts,'combine_meshes',True);prop(smopts,'auto_generate_collision',False);prop(smopts,'generate_lightmap_u_vs',False)
 prop(task,'options',opts);prop(task,'factory',u.FbxFactory());u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
 asset=E.load_asset('/Game/Forest/high/Meshes/'+f.stem)
 if not asset:raise RuntimeError('Missing '+f.stem)
 slots=asset.get_editor_property('static_materials')
 for i,slot in enumerate(slots):
  n=str(slot.get_editor_property('material_slot_name')).removeprefix('M_')
  if n in materials:asset.set_material(i,materials[n])
  else:log('Unknown material '+n)
 if f.stem in ['SM_Terrain','SM_EarthRim','SM_Bridge']:
  prop(asset.get_editor_property('body_setup'),'collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 elif any(w in f.stem for w in ['Broadleaf','Fir','Rock','FallenLog','TrailPost']):
  meshsub.add_simple_collisions(asset,u.ScriptingCollisionShapeType.NDOP26)
 E.save_loaded_asset(asset);meshes[f.stem]=asset
log('Terrain bounds '+str(meshes['SM_Terrain'].get_bounds()))
assert abs(meshes['SM_Terrain'].get_bounds().box_extent.x-5000)<5,'Wrong import units'
levelsys.new_level('/Game/Maps/high')
for a in data['actors']:
 actor=actorsys.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*a['location']),u.Rotator(pitch=0,yaw=a['yaw'],roll=0))
 actor.set_actor_label(a['label']);comp=actor.static_mesh_component;comp.set_static_mesh(meshes[a['mesh']]);actor.set_actor_scale3d(u.Vector(a['scale'][0],-a['scale'][1],a['scale'][2]))
 prop(comp,'mobility',u.ComponentMobility.STATIC)
 solid=any(w in a['mesh'] for w in ['Terrain','EarthRim','Broadleaf','Fir','Rock','FallenLog','Bridge','TrailPost'])
 comp.set_collision_profile_name('BlockAll' if solid else 'NoCollision')
 if a['mesh'] in ['SM_Lake','SM_Sea','SM_Ripple']:prop(comp,'cast_shadow',False)
 actor.tags=[u.Name('high'),u.Name(a['mesh'])]
sun=actorsys.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,7000),u.Rotator(pitch=-42,yaw=-35,roll=0));sun.set_actor_label('Late afternoon sun')
lc=sun.light_component;prop(lc,'mobility',u.ComponentMobility.MOVABLE);prop(lc,'intensity',20000.0);prop(lc,'light_color',u.Color(255,239,213,255));prop(lc,'light_source_angle',3.0)
sky=actorsys.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,3500));sky.set_actor_label('Soft skylight');sc=sky.light_component;prop(sc,'mobility',u.ComponentMobility.MOVABLE);prop(sc,'intensity',1000.0);prop(sc,'real_time_capture',False);prop(sc,'source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);prop(sc,'cubemap',u.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap.DaylightAmbientCubemap'))
actorsys.spawn_actor_from_class(u.SkyAtmosphere,u.Vector(0,0,0))
fog=actorsys.spawn_actor_from_class(u.ExponentialHeightFog,u.Vector(0,0,-200));fc=fog.get_component_by_class(u.ExponentialHeightFogComponent);prop(fc,'fog_density',.007);prop(fc,'fog_height_falloff',.2)
pp=actorsys.spawn_actor_from_class(u.PostProcessVolume,u.Vector(0,0,0));prop(pp,'unbound',True)
settings=pp.get_editor_property('settings');prop(settings,'override_auto_exposure_method',True);prop(settings,'auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL);prop(settings,'override_auto_exposure_bias',True);prop(settings,'auto_exposure_bias',-1.0);prop(settings,'override_bloom_intensity',True);prop(settings,'bloom_intensity',.12);prop(settings,'override_vignette_intensity',True);prop(settings,'vignette_intensity',.1);prop(pp,'settings',settings)
start=actorsys.spawn_actor_from_class(u.PlayerStart,u.Vector(*data['start']),u.Rotator(pitch=0,yaw=85,roll=0));start.set_actor_label('PlayerStart - trail arrival')
logger=u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger');assert logger
actorsys.spawn_actor_from_class(logger,u.Vector(650,-1900,400)).set_actor_label('ScreenDebugLogger - Hello')
loc=u.Vector(12000,-12000,16300);target=u.Vector(0,0,300);rot=u.MathLibrary.find_look_at_rotation(loc,target)
cam=actorsys.spawn_actor_from_class(u.CameraActor,loc,rot);cam.set_actor_label('Overview - Quietwater Grove');cc=cam.get_component_by_class(u.CameraComponent);prop(cc,'projection_mode',u.CameraProjectionMode.ORTHOGRAPHIC);prop(cc,'ortho_width',20000)
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(loc,rot)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();ws=world.get_world_settings();prop(ws,'force_no_precomputed_lighting',True)
levelsys.save_current_level();E.save_directory('/Game/Forest/high',only_if_is_dirty=False,recursive=True)
(ROOT/'build_summary.json').write_text(json.dumps({'actors':len(actorsys.get_all_level_actors()),'meshes':len(meshes),'terrain_bounds':str(meshes['SM_Terrain'].get_bounds()),'map':'/Game/Maps/high'},indent=2))
log('BUILD_COMPLETE')


