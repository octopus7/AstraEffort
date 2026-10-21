import unreal as u, os, json, traceback
ROOT='D:/github/AstraEffort/ForestDemo/Work/medium'
data=json.load(open(ROOT+'/layout.json'))
E=u.EditorAssetLibrary
def log(s):u.log('MEDIUM: '+str(s))
try:
 u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 mats={}
 for n,c in data['colors'].items():
  m=E.load_asset('/Game/Forest/medium/Materials/M_'+n) or u.AssetToolsHelpers.get_asset_tools().create_asset('M_'+n,'/Game/Forest/medium/Materials',u.Material,u.MaterialFactoryNew())
  m.set_editor_property('two_sided',n in ['Water','Foam'])
  ex=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant3Vector,-200,0);ex.set_editor_property('constant',u.LinearColor(*c));u.MaterialEditingLibrary.connect_material_property(ex,'',u.MaterialProperty.MP_BASE_COLOR)
  rough=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant,-200,160);rough.set_editor_property('r',.28 if n=='Water' else .85);u.MaterialEditingLibrary.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
  u.MaterialEditingLibrary.recompile_material(m);mats[n]=m
 meshes={};ss=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
 for file in sorted(os.listdir(ROOT+'/Source')):
  if not file.endswith('.fbx'):continue
  n=file[:-4];t=u.AssetImportTask();t.filename=ROOT+'/Source/'+file;t.destination_path='/Game/Forest/medium/Meshes';t.destination_name=n;t.automated=True;t.save=True;t.replace_existing=True
  opt=u.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False
  opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.auto_generate_collision=True;t.options=opt
  opt.static_mesh_import_data.vertex_color_import_option=u.VertexColorImportOption.REPLACE
  u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);mesh=E.load_asset('/Game/Forest/medium/Meshes/'+n);assert mesh,n
  for idx,slot in enumerate(mesh.static_materials):
   name=str(slot.material_slot_name).split('.')[0];mesh.set_material(idx,mats.get(name,mats['Grass']))
  body=mesh.get_editor_property('body_setup')
  if n=='Ground':body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
  elif n.startswith(('Tree','Rock','Shrub')) or n=='Log':
   if (ss.get_simple_collision_count(mesh)+ss.get_convex_collision_count(mesh))==0:ss.add_simple_collisions(mesh,u.ScriptCollisionShapeType.NDOP26)
  meshes[n]=mesh
 level=u.get_editor_subsystem(u.LevelEditorSubsystem)
 if E.does_asset_exist('/Game/Maps/medium'):E.delete_asset('/Game/Maps/medium')
 assert level.new_level('/Game/Maps/medium')
 actors=u.get_editor_subsystem(u.EditorActorSubsystem)
 def spawn(cls,name,loc=(0,0,0),rot=(0,0,0)):
  a=actors.spawn_actor_from_class(cls,u.Vector(*loc),u.Rotator(pitch=rot[0],yaw=rot[1],roll=rot[2]));a.set_actor_label(name);return a
 def prop(n,loc,scale=1,rot=0):
  a=spawn(u.StaticMeshActor,n,loc,(0,rot,0));c=a.static_mesh_component;c.set_static_mesh(meshes[n]);a.set_actor_scale3d(u.Vector(scale,scale,scale));
  if n in ['Lake','Sea'] or n.startswith('Tuft') or n=='Reeds':c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
  return a
 for n in ['Ground','Lake','Sea']:prop(n,(0,0,0))
 for item in data['layout']:prop(item['mesh'],(item['x'],item['y'],item['z']),item['scale'],item['rot'])
 sun=spawn(u.DirectionalLight,'Warm afternoon sun',(0,0,8000),(-48,-32,0));sun.light_component.set_editor_property('intensity',6.0);sun.light_component.set_editor_property('light_color',u.Color(255,240,212,255));sun.light_component.set_mobility(u.ComponentMobility.MOVABLE);sun.light_component.set_editor_property('atmosphere_sun_light',True)
 sun.light_component.set_editor_property('forward_shading_priority',1)
 sky=spawn(u.SkyLight,'Soft sky fill',(0,0,1000));sky.light_component.set_mobility(u.ComponentMobility.MOVABLE);sky.light_component.set_editor_property('intensity',1.1);sky.light_component.set_editor_property('real_time_capture',False);sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);sky.light_component.set_editor_property('cubemap',u.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'))
 spawn(u.SkyAtmosphere,'Sky atmosphere')
 fill=spawn(u.DirectionalLight,'Soft opposing fill',(0,0,6000),(-35,145,0));fill.light_component.set_mobility(u.ComponentMobility.MOVABLE);fill.light_component.set_editor_property('intensity',1.8);fill.light_component.set_editor_property('cast_shadows',False)
 fog=spawn(u.ExponentialHeightFog,'Distant haze',(0,0,-200));fog.component.set_editor_property('fog_density',.003)
 pp=spawn(u.PostProcessVolume,'Stable exposure');pp.set_editor_property('unbound',True);settings=pp.settings;settings.set_editor_property('override_auto_exposure_method',True);settings.set_editor_property('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL);settings.set_editor_property('override_auto_exposure_bias',True);settings.set_editor_property('auto_exposure_bias',0.0);settings.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True);settings.set_editor_property('auto_exposure_apply_physical_camera_exposure',False);pp.settings=settings
 start=spawn(u.PlayerStart,'PlayerStart | meadow path',(1100,-1400,210),(0,90,0))
 cls=u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger');assert cls;spawn(cls,'ScreenDebugLogger | Hello')
 camloc=u.Vector(10900,-13700,11600);target=u.Vector(0,0,0);camrot=u.MathLibrary.find_look_at_rotation(camloc,target)
 cam=actors.spawn_actor_from_class(u.CameraActor,camloc,camrot);cam.set_actor_label('Overview | Willow Cove');cam.camera_component.set_editor_property('field_of_view',48.0)
 u.EditorLevelLibrary.set_level_viewport_camera_info(camloc,camrot)
 E.save_directory('/Game/Forest/medium',only_if_is_dirty=False,recursive=True);level.save_current_level();log('BUILD SUCCESS')
except Exception:
 log(traceback.format_exc());raise




