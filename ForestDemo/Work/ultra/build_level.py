import unreal as u, json, math, traceback
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra')
DATA=json.loads((ROOT/'scene_manifest.json').read_text())
ASSET='/Game/Forest/ultra'; MAP='/Game/Maps/ultra'
eas=u.get_editor_subsystem(u.EditorAssetSubsystem)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
meshed=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
assettools=u.AssetToolsHelpers.get_asset_tools()
ml=u.MaterialEditingLibrary

def prop(obj,name,val):obj.set_editor_property(name,val)
def v(pos):return u.Vector(pos[0]*100,-pos[1]*100,pos[2]*100)
def spawn(cls,label,pos,rot=None):
 a=actors.spawn_actor_from_class(cls,pos,rot or u.Rotator());a.set_actor_label(label);return a
def expr(mat,cls,x=0,y=0):return ml.create_material_expression(mat,cls,x,y)
def scalar(mat,n,x=0,y=0):
 e=expr(mat,u.MaterialExpressionConstant,x,y);prop(e,'r',n);return e
def vector(mat,c):
 e=expr(mat,u.MaterialExpressionConstant3Vector);prop(e,'constant',u.LinearColor(*c));return e
def connect(a,pin,b,input):
 if not ml.connect_material_expressions(a,pin,b,input):
  assert ml.connect_material_expressions(a,pin,b,''),'Unconnected '+b.get_class().get_name()+' '+input
def output(e,pin,mat,p):assert ml.connect_material_property(e,pin,p)

def create_mat(name,color):
 path=ASSET+'/Materials/M_'+name
 mat=eas.load_asset(path) if eas.does_asset_exist(path) else assettools.create_asset('M_'+name,ASSET+'/Materials',u.Material,u.MaterialFactoryNew())
 # The 5.7 helper removes while iterating its collection: drain fully.
 for _ in range(16):
  if ml.get_num_material_expressions(mat)==0:break
  ml.delete_all_material_expressions(mat)
 assert ml.get_num_material_expressions(mat)==0
 prop(mat,'two_sided',True)
 if name=='Terrain':
  color_node=expr(mat,u.MaterialExpressionVertexColor)
 else:
  a=vector(mat,tuple(c*.88 for c in color[:3])+(1,));b=vector(mat,tuple(c*1.08 for c in color[:3])+(1,))
  noise=expr(mat,u.MaterialExpressionNoise);prop(noise,'scale',.008 if name not in ['Lake','Sea'] else .002);prop(noise,'levels',2);prop(noise,'quality',1)
  lerp=expr(mat,u.MaterialExpressionLinearInterpolate);connect(a,'',lerp,'A');connect(b,'',lerp,'B');connect(noise,'',lerp,'Alpha');color_node=lerp
 output(color_node,'',mat,u.MaterialProperty.MP_BASE_COLOR)
 fill=expr(mat,u.MaterialExpressionMultiply);connect(color_node,'',fill,'A');prop(fill,'const_b',.25 if name in ['Lake','Sea'] else (.09 if name!='Terrain' else .035));output(fill,'',mat,u.MaterialProperty.MP_EMISSIVE_COLOR)
 rough=scalar(mat,.23 if name in ['Lake','Sea'] else (.65 if name=='Rock' else .86));output(rough,'',mat,u.MaterialProperty.MP_ROUGHNESS)
 if name in ['Lake','Sea']:
  # Calm opaque water: broad color variation and specular reflection.
  output(vector(mat,(0,0,1,1)),'',mat,u.MaterialProperty.MP_NORMAL)
  output(scalar(mat,.6),'',mat,u.MaterialProperty.MP_SPECULAR)
 ml.recompile_material(mat);eas.save_loaded_asset(mat)
 return mat

def build():
 materials={name:create_mat(name,c) for name,c in DATA['palette'].items()}
 materials['Terrain']=create_mat('Terrain',DATA['palette']['Grass'])
 tasks=[]
 for name,meta in DATA['assets'].items():
  if eas.does_asset_exist(ASSET+'/Meshes/'+name):continue
  task=u.AssetImportTask();prop(task,'filename',str(ROOT/'SourceArt'/(name+'.fbx')));prop(task,'destination_path',ASSET+'/Meshes');prop(task,'destination_name',name);prop(task,'automated',True);prop(task,'replace_existing',True);prop(task,'save',True)
  options=u.FbxImportUI();prop(options,'import_mesh',True);prop(options,'import_as_skeletal',False);prop(options,'import_materials',False);prop(options,'import_textures',False);prop(options,'import_animations',False);prop(options,'automated_import_should_detect_type',False);prop(options,'mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH)
  md=options.static_mesh_import_data;prop(md,'combine_meshes',True);prop(md,'auto_generate_collision',False);prop(md,'generate_lightmap_u_vs',False);prop(md,'vertex_color_import_option',u.VertexColorImportOption.REPLACE);prop(md,'normal_import_method',u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
  prop(task,'options',options);prop(task,'factory',u.FbxFactory());tasks.append(task)
 assettools.import_asset_tasks(tasks)
 meshes={};mesh_report={}
 for name,meta in DATA['assets'].items():
  mesh=eas.load_asset(ASSET+'/Meshes/'+name)
  if not mesh:raise RuntimeError('Missing mesh '+name)
  meshes[name]=mesh
  for i,m in enumerate(meta['materials']):mesh.set_material(i,materials['Terrain' if name=='SM_Ground' else m])
  body=mesh.get_editor_property('body_setup')
  if meta['collision']=='complex' or name.startswith(('SM_Broadleaf','SM_Pine')):
   prop(body,'collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
  elif meta['collision']=='simple':
   meshed.remove_collisions(mesh)
   meshed.add_simple_collisions(mesh,u.ScriptingCollisionShapeType.NDOP26)
  eas.save_loaded_asset(mesh)
  bounds=mesh.get_bounds();mesh_report[name]={'origin':str(bounds.origin),'extent':str(bounds.box_extent),'collision':str(body.get_editor_property('collision_trace_flag')),'slots':[str(s.material_slot_name) for s in mesh.static_materials]}
 (ROOT/'mesh_import_report.json').write_text(json.dumps(mesh_report,indent=2))
 ground=meshes['SM_Ground'].get_bounds()
 assert abs(ground.box_extent.x*2-10000)<1 and abs(ground.box_extent.y*2-10000)<1, str(ground)
 if eas.does_asset_exist(MAP):
  assert levels.load_level(MAP)
  for old in actors.get_all_level_actors():
   if old.get_class().get_name() not in ['WorldSettings','Brush','DefaultPhysicsVolume']:actors.destroy_actor(old)
 else:assert levels.new_level(MAP)
 world=unreal_world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
 ws=world.get_world_settings();prop(ws,'force_no_precomputed_lighting',True)
 for i,item in enumerate(DATA['placements']):
  actor=spawn(u.StaticMeshActor,item['label']+' %04d'%i,v(item['location']),u.Rotator(pitch=0,yaw=-item['yaw'],roll=0))
  comp=actor.static_mesh_component;comp.set_static_mesh(meshes[item['asset']]);actor.set_actor_scale3d(u.Vector(*item['scale']))
  comp.set_mobility(u.ComponentMobility.STATIC)
  if DATA['assets'][item['asset']]['collision']=='none':comp.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
  else:comp.set_collision_profile_name('BlockAll')
  actor.set_folder_path('Quietwater/'+('Understory' if item['label']=='Understory' else 'Environment'))
  if i%100==0:u.log('ULTRA_PLACED '+str(i))
 light=spawn(u.DirectionalLight,'Sun • soft late morning',u.Vector(0,0,9000),u.Rotator(pitch=-42,yaw=-42,roll=0))
 lc=light.light_component;lc.set_mobility(u.ComponentMobility.MOVABLE);lc.set_intensity(4.0);lc.set_light_color(u.LinearColor(1,.91,.78,1));prop(lc,'light_source_angle',3.0);prop(lc,'atmosphere_sun_light',True)
 sky=spawn(u.SkyLight,'Sky fill',u.Vector(0,0,3000));sc=sky.light_component;sc.set_mobility(u.ComponentMobility.MOVABLE);sc.set_intensity(1.25);prop(sc,'real_time_capture',False);prop(sc,'source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);prop(sc,'cubemap',eas.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'))
 spawn(u.SkyAtmosphere,'Clear quiet sky',u.Vector())
 fog=spawn(u.ExponentialHeightFog,'Light aerial perspective',u.Vector(0,0,-100))
 prop(fog.component,'fog_density',.002);prop(fog.component,'fog_height_falloff',.15)
 pp=spawn(u.PostProcessVolume,'Quietwater exposure and color',u.Vector());prop(pp,'unbound',True)
 settings=pp.get_editor_property('settings')
 for key,value in {'override_auto_exposure_method':True,'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,'override_auto_exposure_bias':True,'auto_exposure_bias':0.0,'override_auto_exposure_apply_physical_camera_exposure':True,'auto_exposure_apply_physical_camera_exposure':False,'override_bloom_intensity':True,'bloom_intensity':.12,'override_vignette_intensity':True,'vignette_intensity':.12,'override_motion_blur_amount':True,'motion_blur_amount':0.0}.items():
  prop(settings,key,value)
 prop(pp,'settings',settings)
 start=spawn(u.PlayerStart,'PlayerStart • coastal trail',v(DATA['player_start_m']),u.Rotator(pitch=0,yaw=-75,roll=0))
 logger_cls=u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger');assert logger_cls
 spawn(logger_cls,'ScreenDebugLogger • Hello',u.Vector(0,0,250))
 camera=spawn(u.CameraActor,'Overview • Quietwater Grove',u.Vector(12000,-12000,16000),u.MathLibrary.find_look_at_rotation(u.Vector(12000,-12000,16000),u.Vector()))
 camera.camera_component.set_projection_mode(u.CameraProjectionMode.ORTHOGRAPHIC);camera.camera_component.set_ortho_width(20000)
 prop(camera,'auto_activate_for_player',u.AutoReceiveInput.DISABLED)
 u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(10900,12700,11900),u.MathLibrary.find_look_at_rotation(u.Vector(10900,12700,11900),u.Vector(0,0,200)))
 assert levels.save_current_level()
 eas.save_directory(ASSET,only_if_is_dirty=False,recursive=True)
 (ROOT/'build_result.json').write_text(json.dumps({'map':MAP,'actors':len(actors.get_all_level_actors()),'mesh_assets':len(meshes),'materials':len(materials),'footprint_cm':[ground.box_extent.x*2,ground.box_extent.y*2],'saved':True},indent=2))
 u.log('ULTRA_BUILD_SUCCESS')
if not globals().get('SKIP_BUILD',False):
 try:build()
 except Exception:
  (ROOT/'build_error.txt').write_text(traceback.format_exc());raise
 finally:
  u.SystemLibrary.quit_editor()
