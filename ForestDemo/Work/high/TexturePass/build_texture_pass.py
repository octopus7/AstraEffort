import unreal as u,json,datetime
from pathlib import Path
R=Path('D:/github/AstraEffort/ForestDemo/Work/high/TexturePass');BASE='/Game/Forest/high/TexturePass'
E=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools();ME=u.MaterialEditingLibrary
ls=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem);ms=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
audit=json.loads((R/'uv_audit.json').read_text());scene=json.loads((R.parent/'scene.json').read_text())
def prop(o,k,v):o.set_editor_property(k,v)
def node(mat,cls):return ME.create_material_expression(mat,cls)
def connect(a,b,name='',output=''):
 assert ME.connect_material_expressions(a,output,b,name),(b.get_class().get_name(),name,ME.get_material_expression_input_names(b))
def out(a,channel,output=''):assert ME.connect_material_property(a,output,channel)
def scalar(mat,value):n=node(mat,u.MaterialExpressionConstant);prop(n,'r',value);return n
def color(mat,value):n=node(mat,u.MaterialExpressionConstant3Vector);prop(n,'constant',u.LinearColor(*value,1));return n
def vector2(mat,x,y):n=node(mat,u.MaterialExpressionConstant2Vector);prop(n,'r',x);prop(n,'g',y);return n
def matnew(name):
 m=E.load_asset(BASE+'/Materials/'+name) if E.does_asset_exist(BASE+'/Materials/'+name) else None
 if not m:m=AT.create_asset(name,BASE+'/Materials',u.Material,u.MaterialFactoryNew())
 ME.delete_all_material_expressions(m);prop(m,'two_sided',True);return m
def custom(mat,code,output_type,inputs):
 n=node(mat,u.MaterialExpressionCustom);prop(n,'code',code);prop(n,'output_type',output_type)
 pins=[]
 for k in inputs:
  pin=u.CustomInput();prop(pin,'input_name',k);pins.append(pin)
 prop(n,'inputs',pins)
 for k,v in inputs.items():connect(v,n,k)
 return n
def import_task(path,dest,name,mesh=False):
 t=u.AssetImportTask();prop(t,'filename',str(path));prop(t,'destination_path',dest);prop(t,'destination_name',name);prop(t,'automated',True);prop(t,'replace_existing',True);prop(t,'save',False)
 if mesh:
  opts=u.FbxImportUI();prop(opts,'import_mesh',True);prop(opts,'import_materials',False);prop(opts,'import_textures',False);prop(opts,'import_as_skeletal',False);prop(opts,'mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH)
  si=opts.get_editor_property('static_mesh_import_data');prop(si,'combine_meshes',True);prop(si,'auto_generate_collision',False);prop(si,'generate_lightmap_u_vs',False);prop(t,'options',opts);prop(t,'factory',u.FbxFactory())
 return t
AT.import_asset_tasks([import_task(R/'Source/GeneratedSurfaceAtlas.png',BASE+'/Textures','T_GeneratedSurfaceAtlas')])
tex=E.load_asset(BASE+'/Textures/T_GeneratedSurfaceAtlas');assert tex
prop(tex,'srgb',True);prop(tex,'address_x',u.TextureAddress.TA_CLAMP);prop(tex,'address_y',u.TextureAddress.TA_CLAMP)
# Native 1254px generated atlas. No upscaling is counted as extra detail.
regions={'bark':(0,0),'leaves':(.5,0),'stone':(0,.5),'wood':(.5,.5)}
def category(n):
 if n in ['Bark','BarkLight']:return 'bark'
 if n in ['Rock','RockLight','Moss','Cliff']:return 'stone'
 if n in ['Wood','WoodEnd','Reed','Metal']:return 'wood'
 return 'leaves'
mats={};mapping=[]
for name,palette in scene['palette'].items():
 m=matnew('M_TP_'+name);uv=node(m,u.MaterialExpressionTextureCoordinate);mul=node(m,u.MaterialExpressionMultiply);connect(uv,mul,'A');connect(vector2(m,.5,.5),mul,'B')
 add=node(m,u.MaterialExpressionAdd);connect(mul,add,'A');reg=regions[category(name)];connect(vector2(m,*reg),add,'B')
 sample=node(m,u.MaterialExpressionTextureSample);prop(sample,'texture',tex);connect(add,sample)
 lerp=node(m,u.MaterialExpressionLinearInterpolate);connect(color(m,palette),lerp,'A');connect(sample,lerp,'B','RGB');connect(scalar(m,.42),lerp,'Alpha');out(lerp,u.MaterialProperty.MP_BASE_COLOR);out(scalar(m,.85),u.MaterialProperty.MP_ROUGHNESS)
 ME.recompile_material(m);mats[name]=m;mapping.append({'material':m.get_path_name(),'source_region':category(name),'uv_scale':[.5,.5],'uv_offset':list(reg),'generated_texture':tex.get_path_name(),'texture_color_blend':.42})
tasks=[]
for f in sorted((R/'Source/FBX').glob('*.fbx')):
 if not E.does_asset_exist(BASE+'/Meshes/'+f.stem):tasks.append(import_task(f,BASE+'/Meshes',f.stem,True))
tasks.append(import_task(R/'Source/SM_CausticsBed.fbx',BASE+'/Meshes','SM_CausticsBed',True))
AT.import_asset_tasks(tasks)
meshassets={}
for name,info in audit['meshes'].items():
 for vn,metrics in info['variants'].items():
  sm=E.load_asset(BASE+'/Meshes/'+vn);assert sm and ms.get_num_uv_channels(sm,0)>=1,vn
  for i,slot in enumerate(sm.get_editor_property('static_materials')):
   key=str(slot.get_editor_property('material_slot_name')).removeprefix('M_');assert key in mats,key;sm.set_material(i,mats[key])
  settings=ms.get_lod_build_settings(sm,0);settings.use_full_precision_u_vs=True;settings.remove_degenerates=False;ms.set_lod_build_settings(sm,0,settings)
  ms.remove_collisions(sm)
  if 'Bridge' in name:prop(sm.get_editor_property('body_setup'),'collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
  elif any(k in name for k in ['Broadleaf','Fir','Rock','FallenLog','TrailPost']):ms.add_simple_collisions(sm,u.ScriptingCollisionShapeType.NDOP26)
  meshassets[vn]=sm
E.save_directory(BASE,only_if_is_dirty=True,recursive=True)
assert ls.load_level('/Game/Maps/high')
lookup={(scene['actors'][p['manifest_index']]['mesh'],tuple(round(x,2) for x in p['location_cm'])):p for p in audit['instances']}
replaced=0
for actor in actors.get_all_level_actors():
 if isinstance(actor,u.StaticMeshActor):
  c=actor.static_mesh_component;name=c.static_mesh.get_name().split('_UV')[0];p=actor.get_actor_location();key=(name,tuple(round(x,2) for x in [p.x,p.y,p.z]))
  if key in lookup:c.set_static_mesh(meshassets[lookup[key]['uv_variant']]);replaced+=1
 if isinstance(actor,u.DirectionalLight):prop(actor.light_component,'forward_shading_priority',2 if actor.get_actor_label()=='Late afternoon sun' else 0)
assert replaced==742,replaced
# Animated, shallow translucent ocean. Optical effects are artistic approximations.
water=matnew('M_TP_SeaAnimated');prop(water,'blend_mode',u.BlendMode.BLEND_TRANSLUCENT);prop(water,'translucency_lighting_mode',u.TranslucencyLightingMode.TLM_SURFACE);prop(water,'tangent_space_normal',False)
P=node(water,u.MaterialExpressionWorldPosition);T=node(water,u.MaterialExpressionTime)
water_code='''float coast=-2900+270*sin(P.x/1350)+120*sin(P.x/540)-100;
float d=max(0,coast-P.y);
float shore=exp(-pow((d-(35+22*sin(T*.85+P.x*.005)))/32,2));
float phase=d*.018-T*1.35+.6*sin(P.x*.004+T*.3);
float crest=pow(saturate((sin(phase)-.58)*2.38),3)*exp(-d/1100);
float lace=.6+.4*sin(P.x*.07+sin(P.y*.025+T)*2);
float foam=saturate(shore*.95+crest*.75*lace);
float ripple=sin(P.x*.006+P.y*.011-T)*.025;
float3 c=lerp(float3(.12,.34,.37)+ripple,float3(.90,.94,.88),foam);
return float4(c,lerp(.48,.94,foam));'''
rgba=custom(water,water_code,u.CustomMaterialOutputType.CMOT_FLOAT4,{'P':P,'T':T});rgb=node(water,u.MaterialExpressionComponentMask);prop(rgb,'r',True);prop(rgb,'g',True);prop(rgb,'b',True);prop(rgb,'a',False);connect(rgba,rgb);out(rgb,u.MaterialProperty.MP_BASE_COLOR)
alpha=node(water,u.MaterialExpressionComponentMask);prop(alpha,'r',False);prop(alpha,'g',False);prop(alpha,'b',False);prop(alpha,'a',True);connect(rgba,alpha);out(alpha,u.MaterialProperty.MP_OPACITY)
out(scalar(water,.22),u.MaterialProperty.MP_ROUGHNESS);out(scalar(water,1.015),u.MaterialProperty.MP_REFRACTION)
wpo=custom(water,'return float3(0,0,5*sin(P.x*.005+P.y*.009-T*1.2)+2*sin(P.x*.011-P.y*.006+T*.7));',u.CustomMaterialOutputType.CMOT_FLOAT3,{'P':P,'T':T});out(wpo,u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
normal=custom(water,'return normalize(float3(-.025*cos(P.x*.005+P.y*.009-T*1.2)-.022*cos(P.x*.011-P.y*.006+T*.7),-.045*cos(P.x*.005+P.y*.009-T*1.2)+.012*cos(P.x*.011-P.y*.006+T*.7),1));',u.CustomMaterialOutputType.CMOT_FLOAT3,{'P':P,'T':T});out(normal,u.MaterialProperty.MP_NORMAL);ME.recompile_material(water)
bed=matnew('M_TP_AnimatedCaustics');P2=node(bed,u.MaterialExpressionWorldPosition);T2=node(bed,u.MaterialExpressionTime)
caustic_code='''float2 q=P.xy*.018+float2(sin(T*.45),cos(T*.37))*.8;
float cell=abs(sin(q.x+sin(q.y*.8+T*.4)) + cos(q.y+sin(q.x*.7-T*.3)));
float light=pow(saturate(1-cell*.85),7);
float second=pow(saturate(1-abs(sin(q.x*.83-q.y*.6+T*.55)+cos(q.y*.93+q.x*.4-T*.37))*.9),9);
return lerp(float3(.30,.42,.34),float3(.86,.92,.65),saturate(light*.7+second*.5));'''
cb=custom(bed,caustic_code,u.CustomMaterialOutputType.CMOT_FLOAT3,{'P':P2,'T':T2});out(cb,u.MaterialProperty.MP_BASE_COLOR);out(scalar(bed,.85),u.MaterialProperty.MP_ROUGHNESS);ME.recompile_material(bed)
bedmesh=E.load_asset(BASE+'/Meshes/SM_CausticsBed');bedmesh.set_material(0,bed)
for actor in actors.get_all_level_actors():
 if actor.get_actor_label()=='Sea':actor.static_mesh_component.set_material(0,water);prop(actor.static_mesh_component,'bounds_scale',1.05)
 if actor.get_actor_label()=='Animated underwater caustics':actors.destroy_actor(actor)
ca=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));ca.set_actor_label('Animated underwater caustics');ca.static_mesh_component.set_static_mesh(bedmesh);ca.set_actor_scale3d(u.Vector(1,-1,1));ca.static_mesh_component.set_collision_profile_name('NoCollision');prop(ca.static_mesh_component,'cast_shadow',False)
E.save_directory(BASE,only_if_is_dirty=False,recursive=True);assert ls.save_current_level()
(R/'material_mapping.json').write_text(json.dumps(mapping,indent=2))
(R/'build_summary.json').write_text(json.dumps({'saved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'replaced_prop_actors':replaced,'uv_mesh_variants':len(meshassets),'generated_texture':tex.get_path_name(),'uv_channels_checked':True,'water_material':water.get_path_name(),'caustics_material':bed.get_path_name(),'water_technique':'Two analytic sine-wave WPO terms (5+2cm); animated crest/shore foam; translucent surface with mild screen-space IOR=1.015. Underwater caustics are animated artistic interference patterns on a separate seabed sheet, not physically simulated refracted light.'},indent=2))
u.log('HIGH_TEXTURE_BUILD_COMPLETE')
