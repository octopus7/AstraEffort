"""Private UE authoring pass; no shared project writes."""
import unreal as u, json, os, math, traceback, datetime
ROOT='D:/github/AstraEffort/ForestDemo/Work/xhigh'
DATA=json.load(open(ROOT+'/scene_manifest.json'))
DEST='/Game/Forest/xhigh'
ASSET=u.AssetToolsHelpers.get_asset_tools()
EAS=u.get_editor_subsystem(u.EditorActorSubsystem)
LES=u.get_editor_subsystem(u.LevelEditorSubsystem)
SMES=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
ML=u.MaterialEditingLibrary

def prop(o,n,v):o.set_editor_property(n,v)
def expression(m,cls,x=0,y=0):return ML.create_material_expression(m,cls,x,y)
def constant(m,value):
 n=expression(m,u.MaterialExpressionConstant);prop(n,'r',value);return n
def vector(m,col):
 n=expression(m,u.MaterialExpressionConstant3Vector);prop(n,'constant',u.LinearColor(*col,1));return n
def link(a,out,b,inp):
 if not ML.connect_material_expressions(a,out,b,inp):raise RuntimeError('Material pin connection failed: '+str(inp))
def output(n,slot,out=''):
 if not ML.connect_material_property(n,out,slot):raise RuntimeError('Material output connection failed: '+str(out))

def material(name,col):
 m=u.load_asset(DEST+'/Materials/M_'+name)
 if m:ML.delete_all_material_expressions(m)
 else:m=ASSET.create_asset('M_'+name,DEST+'/Materials',u.Material,u.MaterialFactoryNew())
 if name in ['Grass','LeafSage','LeafMoss','LeafLight','Reed','Petal']:
  prop(m,'two_sided',True)
 if name=='Terrain':
  n=expression(m,u.MaterialExpressionVertexColor);output(n,u.MaterialProperty.MP_BASE_COLOR)
 elif name.startswith('Water'):
  base=vector(m,col);light=vector(m,tuple(min(1,c*1.5+.03) for c in col))
  f=expression(m,u.MaterialExpressionFresnel);prop(f,'exponent',3.0);prop(f,'base_reflect_fraction',.1)
  lerp=expression(m,u.MaterialExpressionLinearInterpolate);link(base,'',lerp,'A');link(light,'',lerp,'B');link(f,'',lerp,'Alpha');output(lerp,u.MaterialProperty.MP_BASE_COLOR)
  output(constant(m,.70),u.MaterialProperty.MP_ROUGHNESS)
  output(constant(m,.02),u.MaterialProperty.MP_SPECULAR)
  # Subtle analytic wind ripples, no texture dependencies.
  pos=expression(m,u.MaterialExpressionWorldPosition)
  mask=expression(m,u.MaterialExpressionComponentMask);prop(mask,'r',True);prop(mask,'g',False);prop(mask,'b',False);link(pos,'',mask,'')
  mul=expression(m,u.MaterialExpressionMultiply);link(mask,'',mul,'A');link(constant(m,.006),'',mul,'B')
  sine=expression(m,u.MaterialExpressionSine);link(mul,'',sine,'')
  amp=expression(m,u.MaterialExpressionMultiply);link(sine,'',amp,'A');link(constant(m,.012),'',amp,'B')
  append=expression(m,u.MaterialExpressionAppendVector);link(amp,'',append,'A');link(constant(m,0),'',append,'B')
  norm=expression(m,u.MaterialExpressionAppendVector);link(append,'',norm,'A');link(constant(m,1),'',norm,'B');output(norm,u.MaterialProperty.MP_NORMAL)
 else:
  output(vector(m,col),u.MaterialProperty.MP_BASE_COLOR)
 if not name.startswith('Water'):output(constant(m,.88 if name!='Foam' else .6),u.MaterialProperty.MP_ROUGHNESS)
 ML.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m);return m

def spawn(cls,label,loc=(0,0,0),rotation=None):
 a=EAS.spawn_actor_from_class(cls,u.Vector(*loc),rotation or u.Rotator())
 a.set_actor_label(label);return a
def tag(a,s):prop(a,'tags',[u.Name(s),u.Name('xhigh')])
def mesh_actor(mesh,label,loc=(0,0,0),scale=(1,1,1),yaw=0,role='prop'):
 a=spawn(u.StaticMeshActor,label,loc,u.Rotator(pitch=0,yaw=yaw,roll=0));c=a.static_mesh_component
 c.set_static_mesh(mesh);a.set_actor_scale3d(u.Vector(*scale));c.set_mobility(u.ComponentMobility.STATIC)
 if role in ['water','understory','beach_grass','lake_reeds']:
  c.set_collision_profile_name('NoCollision')
 else:c.set_collision_profile_name('BlockAll')
 a.set_folder_path('xhigh/'+role);tag(a,role);return a

def main():
 u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 u.EditorAssetLibrary.make_directory(DEST+'/Meshes');u.EditorAssetLibrary.make_directory(DEST+'/Materials')
 materials={name:(u.load_asset(DEST+'/Materials/M_'+name) or material(name,col)) for name,col in DATA['palette'].items()}
 meshes={}
 for name,info in DATA['meshes'].items():
  task=u.AssetImportTask();prop(task,'filename',ROOT+'/SourceArt/'+name+'.fbx');prop(task,'destination_path',DEST+'/Meshes');prop(task,'destination_name',name)
  prop(task,'automated',True);prop(task,'replace_existing',True);prop(task,'save',True)
  opts=u.FbxImportUI();prop(opts,'import_mesh',True);prop(opts,'import_materials',False);prop(opts,'import_textures',False);prop(opts,'import_as_skeletal',False)
  prop(opts,'mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH);prop(opts,'automated_import_should_detect_type',False)
  sd=opts.static_mesh_import_data;prop(sd,'combine_meshes',True);prop(sd,'generate_lightmap_u_vs',False);prop(sd,'auto_generate_collision',False)
  prop(sd,'vertex_color_import_option',u.VertexColorImportOption.REPLACE);prop(sd,'normal_import_method',u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
  prop(task,'factory',u.FbxFactory());prop(task,'options',opts);ASSET.import_asset_tasks([task])
  mesh=u.load_asset(DEST+'/Meshes/'+name)
  if not mesh:raise RuntimeError('Missing import '+name)
  slots=mesh.get_editor_property('static_materials')
  for i,s in enumerate(slots):
   slot=str(s.material_slot_name)
   if slot not in materials:raise RuntimeError('Unknown material slot '+name+': '+slot)
   mesh.set_material(i,materials[slot])
  body=mesh.get_editor_property('body_setup');prop(body,'collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
  u.EditorAssetLibrary.save_loaded_asset(mesh);meshes[name]=mesh
  u.log('XHIGH_IMPORTED '+name)
 # Explicit empty non-partition world. There is no template asset content to inherit.
 if u.EditorAssetLibrary.does_asset_exist('/Game/Maps/xhigh'):
  if not LES.load_level('/Game/Maps/xhigh'):raise RuntimeError('reload level failed')
  for actor in EAS.get_all_level_actors():
   if not isinstance(actor,u.WorldSettings) and actor.get_class()!=u.Brush.static_class():EAS.destroy_actor(actor)
 elif not LES.new_level('/Game/Maps/xhigh',False):raise RuntimeError('new_level failed')
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();ws=world.get_world_settings();prop(ws,'force_no_precomputed_lighting',True)
 for n in ['SM_Terrain','SM_Sea','SM_Lake','SM_Surf_0','SM_Surf_1','SM_Surf_2']:
  u.log('XHIGH_SPAWNING '+n)
  mesh_actor(meshes[n],n,role='terrain' if n=='SM_Terrain' else 'water')
 for i,inst in enumerate(DATA['instances']):
  mesh_actor(meshes[inst['mesh']],'%s_%04d'%(inst['mesh'],i),[p*100 for p in inst['location']],inst['scale'],inst['yaw'],inst['role'])
 start=spawn(u.PlayerStart,'PlayerStart_TrailArrival',[p*100 for p in DATA['regions']['player_m']],u.Rotator(pitch=0,yaw=85,roll=0));tag(start,'player_start')
 logger=spawn(u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger'),'ScreenDebugLogger_Hello');tag(logger,'baseline_hello')
 sun=spawn(u.DirectionalLight,'QuietCove_Sun',(0,0,3000),u.Rotator(pitch=-46,yaw=-38,roll=0));sun.light_component.set_mobility(u.ComponentMobility.MOVABLE)
 prop(sun.light_component,'intensity',4.0);prop(sun.light_component,'light_color',u.Color(255,238,213,255));prop(sun.light_component,'light_source_angle',2.7)
 sky=spawn(u.SkyLight,'QuietCove_SkyLight');sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
 prop(sky.light_component,'intensity',.9);prop(sky.light_component,'real_time_capture',False)
 prop(sky.light_component,'source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
 prop(sky.light_component,'cubemap',u.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'))
 spawn(u.SkyAtmosphere,'QuietCove_Atmosphere')
 fog=spawn(u.ExponentialHeightFog,'QuietCove_DistanceHaze',(0,0,-800))
 prop(fog.component,'fog_density',.012);prop(fog.component,'fog_height_falloff',.18)
 pp=spawn(u.PostProcessVolume,'QuietCove_Color');prop(pp,'unbound',True)
 settings=pp.get_editor_property('settings')
 for k,v in {'override_auto_exposure_method':True,'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,
 'override_auto_exposure_bias':True,'auto_exposure_bias':0.0,'override_auto_exposure_apply_physical_camera_exposure':True,
 'auto_exposure_apply_physical_camera_exposure':False,'override_bloom_intensity':True,'bloom_intensity':.15,
 'override_vignette_intensity':True,'vignette_intensity':.12,'override_motion_blur_amount':True,'motion_blur_amount':0.0}.items():prop(settings,k,v)
 prop(pp,'settings',settings)
 camera=spawn(u.CameraActor,'Overview_QuietCove',(12000,-12000,16000))
 rot=u.MathLibrary.find_look_at_rotation(camera.get_actor_location(),u.Vector(0,0,0));camera.set_actor_rotation(rot,False)
 prop(camera.camera_component,'projection_mode',u.CameraProjectionMode.ORTHOGRAPHIC);prop(camera.camera_component,'ortho_width',20000)
 u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(11800,-14700,11700),u.MathLibrary.find_look_at_rotation(u.Vector(11800,-14700,11700),u.Vector(0,0,200)))
 LES.save_current_level();u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
 json.dump({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actors':len(EAS.get_all_level_actors()),'meshes':len(meshes),'materials':len(materials),'map':'/Game/Maps/xhigh'},open(ROOT+'/build_summary.json','w'),indent=2)
 u.log('XHIGH_BUILD_COMPLETE')

try:main()
except Exception:
 with open(ROOT+'/build_error.txt','w') as f:f.write(traceback.format_exc())
 u.log_error(traceback.format_exc());raise
finally:
 if not globals().get('XHIGH_BUILD_KEEP',False):u.SystemLibrary.quit_editor()
