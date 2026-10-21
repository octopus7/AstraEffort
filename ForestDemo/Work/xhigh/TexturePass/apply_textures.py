"""Apply generated textures and animated shallow water in private UE editor."""
import unreal as u, json, os, datetime, traceback
ROOT='D:/github/AstraEffort/ForestDemo/Work/xhigh'
PHASE=ROOT+'/TexturePass';DEST='/Game/Forest/xhigh'
DATA=json.load(open(ROOT+'/scene_manifest.json'))
UV=json.load(open(PHASE+'/SourceArt/uv_report.json'))
AT=u.AssetToolsHelpers.get_asset_tools();ML=u.MaterialEditingLibrary
LES=u.get_editor_subsystem(u.LevelEditorSubsystem);EAS=u.get_editor_subsystem(u.EditorActorSubsystem)
def prop(o,n,v):o.set_editor_property(n,v)
def expr(m,c):return ML.create_material_expression(m,c)
def scalar(m,x):
 n=expr(m,u.MaterialExpressionConstant);prop(n,'r',x);return n
def vec(m,x):
 n=expr(m,u.MaterialExpressionConstant3Vector);prop(n,'constant',u.LinearColor(*x,1));return n
def link(a,out,b,inp):
 assert ML.connect_material_expressions(a,out,b,inp), 'Material connection '+inp
def output(n,p):assert ML.connect_material_property(n,'',p),str(p)
def custom(m,code,inputs,typ=u.CustomMaterialOutputType.CMOT_FLOAT3):
 n=expr(m,u.MaterialExpressionCustom);prop(n,'code',code);prop(n,'output_type',typ)
 ci=[]
 for name in inputs:
  item=u.CustomInput();prop(item,'input_name',name);ci.append(item)
 prop(n,'inputs',ci)
 for name,value in inputs.items():link(value,'',n,name)
 return n
def texobj(m,tex):
 n=expr(m,u.MaterialExpressionTextureObject);prop(n,'texture',tex);return n
def timepos(m):return expr(m,u.MaterialExpressionTime),expr(m,u.MaterialExpressionWorldPosition)
def mat(name):
 m=u.load_asset(DEST+'/Materials/M_'+name)
 if m:ML.delete_all_material_expressions(m)
 else:m=AT.create_asset('M_'+name,DEST+'/Materials',u.Material,u.MaterialFactoryNew())
 return m
def finish(m):ML.layout_material_expressions(m);ML.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)

SURFACES={
 'Bark':'bark','BarkLight':'bark','LeafSage':'foliage','LeafMoss':'foliage','LeafLight':'foliage','Pine':'foliage','PineTips':'foliage',
 'Stone':'stone','StoneLight':'stone','StoneDark':'stone','Grass':'foliage','Reed':'foliage','RushTip':'bark','Petal':'foliage','Wood':'wood','EndGrain':'wood','Sand':'stone','Path':'stone'}

def surface_material(name,tex):
 m=mat(name);prop(m,'two_sided',True)
 uv=expr(m,u.MaterialExpressionTextureCoordinate)
 density=expr(m,u.MaterialExpressionScalarParameter)
 prop(density,'parameter_name','PlacedTexelDensityScale');prop(density,'default_value',1.0)
 prop(density,'use_custom_primitive_data',True);prop(density,'primitive_data_index',0)
 coord=expr(m,u.MaterialExpressionMultiply);link(uv,'',coord,'A');link(density,'',coord,'B')
 n=custom(m,'float3 s=Texture2DSample(Tex,TexSampler,UV).rgb; float l=dot(s,float3(.299,.587,.114)); return Tint*(.68+1.08*sqrt(max(l,.001)));',{'Tex':texobj(m,tex),'UV':coord,'Tint':vec(m,DATA['palette'][name])})
 output(n,u.MaterialProperty.MP_BASE_COLOR);output(scalar(m,.90),u.MaterialProperty.MP_ROUGHNESS);output(scalar(m,.10),u.MaterialProperty.MP_SPECULAR)
 finish(m);return m

def ground_material(textures):
 m=mat('Terrain');t,p=timepos(m);color=expr(m,u.MaterialExpressionVertexColor)
 n=custom(m,'float s=Texture2DSample(Grain,GrainSampler,P.xy*.00102).r; return Tint*(.94+.15*s);',{'Grain':texobj(m,textures['stone']),'P':p,'Tint':color})
 output(n,u.MaterialProperty.MP_BASE_COLOR);output(scalar(m,.94),u.MaterialProperty.MP_ROUGHNESS)
 # Actual seabed/pond-bed receives the bright caustic layer; translucent water covers it.
 code='''float2 q=P.xy*.0008; q+=float2(sin(P.y*.004+T*.5),cos(P.x*.003-T*.4))*.012;
float a=Texture2DSample(C,Csampler,q+float2(T*.013,T*.009)).r;
float b=Texture2DSample(C,Csampler,q*1.13+float2(-T*.011,T*.007)).r;
float lake=1-smoothstep(.93,1.12,length((P.xy-float2(-1800,1400))/float2(1420,1030)));
float sea=(1-smoothstep(-2,35,P.z))*(1-smoothstep(-1600,-1300,P.y));
float bed=max(sea,lake*(1-smoothstep(170,200,P.z)));
float depthSoft=lerp(1-smoothstep(100,380,-P.z),.65,lake);
return float3(.68,.90,.73)*pow(max(a,b),2.4)*bed*depthSoft*.24;'''.replace('Csampler','CSampler')
 output(custom(m,code,{'C':texobj(m,textures['caustics']),'P':p,'T':t}),u.MaterialProperty.MP_EMISSIVE_COLOR)
 finish(m);return m

def water_material(name):
 m=mat(name);prop(m,'blend_mode',u.BlendMode.BLEND_TRANSLUCENT)
 prop(m,'translucency_lighting_mode',u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
 prop(m,'two_sided',True);prop(m,'tangent_space_normal',False)
 t,p=timepos(m)
 output(custom(m,'float a=sin(P.x*.006+P.y*.009-T*1.25); float b=sin(P.x*.011-P.y*.004+T*.83); return Tint*(.89+.11*a)+float3(.035,.055,.050)*pow(saturate(.5+.5*b),7);',{'P':p,'T':t,'Tint':vec(m,DATA['palette'][name])}),u.MaterialProperty.MP_BASE_COLOR)
 output(custom(m,'return normalize(float3(.055*cos(P.x*.006+P.y*.009-T*1.25),.065*cos(P.x*.011-P.y*.004+T*.83),1));',{'P':p,'T':t}),u.MaterialProperty.MP_NORMAL)
 amp=2.5 if name=='WaterSea' else .8
 output(custom(m,'return float3(0,0,A*(sin(P.x*.006+P.y*.009-T*1.25)+.45*sin(P.x*.011-P.y*.004+T*.83)));',{'P':p,'T':t,'A':scalar(m,amp)}),u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
 output(scalar(m,.46),u.MaterialProperty.MP_ROUGHNESS);output(scalar(m,.06),u.MaterialProperty.MP_SPECULAR)
 fade=expr(m,u.MaterialExpressionDepthFade);prop(fade,'fade_distance_default',65.0);prop(fade,'opacity_default',.72 if name=='WaterSea' else .68)
 output(fade,u.MaterialProperty.MP_OPACITY)
 finish(m);return m

def foam_material():
 m=mat('Foam');prop(m,'blend_mode',u.BlendMode.BLEND_TRANSLUCENT);prop(m,'two_sided',True)
 prop(m,'translucency_lighting_mode',u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
 t,p=timepos(m)
 output(vec(m,(.90,.94,.88)),u.MaterialProperty.MP_BASE_COLOR);output(vec(m,(.12,.14,.11)),u.MaterialProperty.MP_EMISSIVE_COLOR)
 output(scalar(m,.85),u.MaterialProperty.MP_ROUGHNESS)
 foamcode='''float coast=-2700+300*sin(P.x*.00085)+180*sin(P.x*.0019+.8);
float motion=26*sin(T*.70+P.x*.001);
float w0=45*(.75+.25*sin(P.x*.0031));float w1=28*(.75+.25*sin(P.x*.0031+1));float w2=20*(.75+.25*sin(P.x*.0031+2));
float f0=1-smoothstep(w0*.08,w0*.52,abs(P.y-coast-440-20*sin(P.x*.006)-w0*.5-motion));
float f1=1-smoothstep(w1*.08,w1*.52,abs(P.y-coast-110-20*sin(P.x*.006+1)-w1*.5-motion));
float f2=1-smoothstep(w2*.08,w2*.52,abs(P.y-coast+270-20*sin(P.x*.006+2)-w2*.5-motion));
float broken=.07+.84*smoothstep(-.25,.55,sin(P.x*.022+sin(P.x*.006)*2-T*.8));
float fleck=.66+.34*sin(P.x*.26+sin(P.y*.17));
return max(f0,max(f1,f2))*broken*fleck;'''
 output(custom(m,foamcode,{'P':p,'T':t},u.CustomMaterialOutputType.CMOT_FLOAT1),u.MaterialProperty.MP_OPACITY)
 output(custom(m,'return float3(0,26*sin(T*.70+P.x*.001),9+2.5*sin(P.x*.006+P.y*.009-T*1.25));',{'P':p,'T':t}),u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
 finish(m);return m

try:
 assert UV['passed'],'UV validation failed'
 u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 textures={}
 for name in ['bark','foliage','stone','wood','caustics']:
  task=u.AssetImportTask();prop(task,'filename',PHASE+'/Imagegen/'+name+'.png');prop(task,'destination_path',DEST+'/Textures');prop(task,'destination_name','T_IG_'+name)
  prop(task,'automated',True);prop(task,'replace_existing',True);prop(task,'save',True);AT.import_asset_tasks([task])
  tex=u.load_asset(DEST+'/Textures/T_IG_'+name);assert tex
  prop(tex,'srgb',name!='caustics');prop(tex,'address_x',u.TextureAddress.TA_WRAP);prop(tex,'address_y',u.TextureAddress.TA_WRAP)
  # Keep the generated 1254-square originals unchanged; UE uses no mipmaps for NPOT images.
  prop(tex,'mip_gen_settings',u.TextureMipGenSettings.TMGS_NO_MIPMAPS)
  u.EditorAssetLibrary.save_loaded_asset(tex);textures[name]=tex
 materials={name:surface_material(name,textures[image]) for name,image in SURFACES.items()}
 materials['Terrain']=ground_material(textures)
 materials['WaterSea']=water_material('WaterSea');materials['WaterLake']=water_material('WaterLake');materials['Foam']=foam_material()
 for name in DATA['meshes']:
  task=u.AssetImportTask();prop(task,'filename',PHASE+'/SourceArt/'+name+'.fbx');prop(task,'destination_path',DEST+'/Meshes');prop(task,'destination_name',name)
  prop(task,'automated',True);prop(task,'replace_existing',True);prop(task,'save',True)
  opts=u.FbxImportUI();prop(opts,'import_mesh',True);prop(opts,'import_materials',False);prop(opts,'import_textures',False);prop(opts,'import_as_skeletal',False)
  prop(opts,'mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH);prop(opts,'automated_import_should_detect_type',False)
  sd=opts.static_mesh_import_data;prop(sd,'combine_meshes',True);prop(sd,'generate_lightmap_u_vs',False);prop(sd,'auto_generate_collision',False)
  prop(sd,'vertex_color_import_option',u.VertexColorImportOption.REPLACE);prop(sd,'normal_import_method',u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
  prop(task,'factory',u.FbxFactory());prop(task,'options',opts);AT.import_asset_tasks([task])
  mesh=u.load_asset(DEST+'/Meshes/'+name);assert mesh
  for i,slot in enumerate(mesh.get_editor_property('static_materials')):mesh.set_material(i,materials[str(slot.material_slot_name)])
  prop(mesh.get_editor_property('body_setup'),'collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
  if name in ['SM_Pine_0','SM_Pine_1']:
   ss=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);bs=ss.get_lod_build_settings(mesh,0);prop(bs,'use_full_precision_u_vs',True);ss.set_lod_build_settings(mesh,0,bs)
  u.EditorAssetLibrary.save_loaded_asset(mesh);u.log('XHIGH_TEXTURE_IMPORTED '+name)
 assert LES.load_level('/Game/Maps/xhigh')
 actors=[]
 for a in EAS.get_all_level_actors():
  if not isinstance(a,u.StaticMeshActor):continue
  c=a.static_mesh_component;n=c.static_mesh.get_name();s=a.get_actor_scale3d();assert max(s.x,s.y,s.z)-min(s.x,s.y,s.z)<.0001
  value=UV['meshes'][n]['mesh_sampling_factor']*s.x
  c.set_default_custom_primitive_data_float(0,value)
  actors.append({'actor':a.get_actor_label(),'mesh':n,'world_scale':[s.x,s.y,s.z],'custom_primitive_data_0':value})
 LES.save_current_level();u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
 report={'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'materials':list(materials),'textures':[t.get_path_name() for t in textures.values()],'actors':actors,'surface_mapping':SURFACES,'water_model':'Translucent animated analytic waves; moving image-generated caustic emission on actual underwater terrain, artistic approximation; no ray-traced optical refraction.'}
 json.dump(report,open(PHASE+'/build_summary.json','w'),indent=2)
 u.log('XHIGH_TEXTURE_BUILD_COMPLETE')
except Exception:
 open(PHASE+'/build_error.txt','w').write(traceback.format_exc());u.log_error(traceback.format_exc())
finally:u.SystemLibrary.quit_editor()
