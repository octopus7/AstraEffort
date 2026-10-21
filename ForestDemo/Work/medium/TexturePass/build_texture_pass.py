import unreal as u,json,os,traceback,datetime
ROOT='D:/github/AstraEffort/ForestDemo/Work/medium/TexturePass';BASE='/Game/Forest/medium';E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary
report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'working'}
def node(mat,cls,**props):
 n=M.create_material_expression(mat,cls)
 for k,v in props.items():n.set_editor_property(k,v)
 return n
def link(a,b,p,out=''):M.connect_material_expressions(a,out,b,p)
def custom_input(name):
 i=u.CustomInput();i.set_editor_property('input_name',name);return i
def material(name):return E.load_asset(BASE+'/Materials/'+name) or u.AssetToolsHelpers.get_asset_tools().create_asset(name,BASE+'/Materials',u.Material,u.MaterialFactoryNew())
try:
 level=u.get_editor_subsystem(u.LevelEditorSubsystem);assert level.load_level('/Game/Maps/medium')
 u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 t=u.AssetImportTask();t.filename=ROOT+'/Source/surface_atlas.png';t.destination_path=BASE+'/Textures';t.destination_name='T_SurfaceAtlas';t.automated=True;t.save=True;t.replace_existing=True;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);tex=E.load_asset(BASE+'/Textures/T_SurfaceAtlas');assert tex
 tex.set_editor_property('srgb',True);tex.set_editor_property('never_stream',True)
 colors=json.load(open(ROOT+'/../layout.json'))['colors'];mats={}
 for name in ['Bark','Wood','Leaf','LeafLight','LeafBlue','Rock','RockLight','Moss','Flower']:
  mat=material('MT_'+name);M.delete_all_material_expressions(mat)
  sample=node(mat,u.MaterialExpressionTextureSample,texture=tex)
  tint=node(mat,u.MaterialExpressionConstant3Vector,constant=u.LinearColor(*colors[name]))
  blend=node(mat,u.MaterialExpressionLinearInterpolate,const_alpha=(.30 if name.startswith('Leaf') else .45));link(tint,blend,'A');link(sample,blend,'B','RGB');M.connect_material_property(blend,'',u.MaterialProperty.MP_BASE_COLOR)
  rough=node(mat,u.MaterialExpressionConstant,r=.83);M.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS);M.recompile_material(mat);mats[name]=mat
 water=material('MT_SeaAnimated');M.delete_all_material_expressions(water);water.set_editor_property('two_sided',True)
 pos=node(water,u.MaterialExpressionWorldPosition);tm=node(water,u.MaterialExpressionTime)
 colorcode='''float x=P.x; float y=P.y; float shore=-3350+200*sin(x*.0007); float d=max(0,shore-y); float w=sin(y*.025+x*.003-T*1.35); float w2=sin(y*.043-x*.005-T*1.8); float foam=pow(saturate(w*.5+.5),22)*.55+pow(saturate(w2*.5+.5),30)*.25; foam*=saturate(1-d/1800); float edge=(1-smoothstep(30,150,d+25*sin(T*1.4+x*.008))); foam=saturate(foam+edge*.9); float a=sin(x*.038+sin(y*.028+T*.6));float b=sin(y*.036+sin(x*.031-T*.7));float caustic=pow(saturate(1-abs(a*b)),28)*.15;float3 deep=float3(.12,.32,.34);float3 shallow=float3(.34,.49,.40);float3 c=lerp(shallow,deep,saturate(d/1400));c+=caustic*saturate(1-d/1800)*float3(.7,.85,.55);return lerp(c,float3(.83,.88,.79),foam);'''
 c=node(water,u.MaterialExpressionCustom,code=colorcode,output_type=u.CustomMaterialOutputType.CMOT_FLOAT3,inputs=[custom_input('P'),custom_input('T')]);link(pos,c,'P');link(tm,c,'T');M.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
 w=node(water,u.MaterialExpressionCustom,code='return float3(0,0,4*sin(P.y*.025+P.x*.003-T*1.35)+2*sin(P.y*.043-T*1.8));',output_type=u.CustomMaterialOutputType.CMOT_FLOAT3,inputs=[custom_input('P'),custom_input('T')]);link(pos,w,'P');link(tm,w,'T');M.connect_material_property(w,'',u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
 rough=node(water,u.MaterialExpressionConstant,r=.3);M.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS);M.recompile_material(water)
 ss=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);meshes={};uv=json.load(open(ROOT+'/uv_validation.json'))
 for name in [a['name'] for a in uv['meshes']]+['SeaWaves']:
  t=u.AssetImportTask();t.filename=ROOT+'/Source/'+name+'.fbx';t.destination_path=BASE+'/Meshes/TexturePass';t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True
  opt=u.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False;opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.auto_generate_collision=True;opt.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS;t.options=opt
  u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);mesh=E.load_asset(BASE+'/Meshes/TexturePass/'+name);assert mesh,name
  for i,s in enumerate(mesh.static_materials):mesh.set_material(i,water if name=='SeaWaves' else mats[str(s.material_slot_name).split('.')[0].split('_')[0]])
  if name=='SeaWaves':mesh.set_material(0,water)
  if name.startswith(('Tree','Rock','Shrub','Log')) and ss.get_simple_collision_count(mesh)+ss.get_convex_collision_count(mesh)==0:ss.add_simple_collisions(mesh,u.ScriptCollisionShapeType.NDOP26)
  settings=ss.get_lod_build_settings(mesh,0);settings.set_editor_property('use_full_precision_u_vs',True);ss.set_lod_build_settings(mesh,0,settings)
  meshes[name]=mesh
 actors=u.get_editor_subsystem(u.EditorActorSubsystem);changed=[]
 for a in actors.get_all_level_actors():
  if not isinstance(a,u.StaticMeshActor):continue
  comp=a.static_mesh_component;old=comp.static_mesh.get_name()
  if old=='Sea':comp.set_static_mesh(meshes['SeaWaves']);comp.set_material(0,water);changed.append({'actor':a.get_name(),'mesh':'SeaWaves'});continue
  if old not in {p['source'] for p in uv['meshes']}:continue
  scale=a.get_actor_scale3d().x;variant=old+'_S'+str(round(round(scale*10)/10*100));comp.set_static_mesh(meshes[variant]);a.set_actor_scale3d(u.Vector(1,1,1))
  for i,s in enumerate(meshes[variant].static_materials):comp.set_material(i,s.material_interface)
  changed.append({'actor':a.get_name(),'mesh':variant,'old_scale':scale,'new_scale':1})
 E.save_directory(BASE,only_if_is_dirty=False,recursive=True);assert level.save_current_level()
 report.update(status='passed',imported_mesh_count=len(meshes),modified_instances=changed,texture=tex.get_path_name(),materials={n:m.get_path_name() for n,m in mats.items()},water={'material':water.get_path_name(),'model':'Opaque stylized analytic waves, foam and caustic brightness; no physical refraction or traced caustics','wave_amplitude_cm':6},finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
except Exception:report.update(status='needs_attention',error=traceback.format_exc())
json.dump(report,open(ROOT+'/build_report.json','w'),indent=2);u.SystemLibrary.quit_editor()
