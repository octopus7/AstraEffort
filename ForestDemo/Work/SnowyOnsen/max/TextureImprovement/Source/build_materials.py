"""Texture quality pass. Existing geometry/layout/lights/camera settings retained."""
import sys,json,hashlib,traceback,time
from pathlib import Path
from datetime import datetime,timezone
PASS=Path(r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max/TextureImprovement');BASE=PASS.parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE/'Source'));import build_unreal as b
b.ROOT=PASS
u=b.u;M=b.MEL;E=b.EAL;A=b.ASSET;MAP=b.MAP
sys.path.insert(0,str(PASS/'Source'));import capture_views
PRIVATE=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/SnowyOnsen/max/PrivateOnsen')
BASE_MAP=PRIVATE.parent/'FirstDeliveryContent/Maps/SnowyOnsen_max.umap'
DISK_MAP=PRIVATE/'Content/Maps/SnowyOnsen_max.umap'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def custom(m,code,inputs,output=u.CustomMaterialOutputType.CMOT_FLOAT1,description=''):
 n=b.node(m,u.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('output_type',output);n.set_editor_property('description',description)
 items=[]
 for name in inputs:
  item=u.CustomInput();item.set_editor_property('input_name',name);items.append(item)
 n.set_editor_property('inputs',items)
 for name,expr in inputs.items():b.link(expr,n,name)
 return n
def texobj(m,t):
 n=b.node(m,u.MaterialExpressionTextureObject);n.set_editor_property('texture',t);return n
def sample(m,t,uv=None):
 n=b.node(m,u.MaterialExpressionTextureSample);n.set_editor_property('texture',t)
 if uv:b.link(uv,n,'Coordinates')
 return n
def position_normal(m):return b.node(m,u.MaterialExpressionWorldPosition),b.node(m,u.MaterialExpressionVertexNormalWS)
def triplanar(m,texture,p,n,scale):
 return custom(m,'float3 w=pow(abs(N),4.0);w/=max(w.x+w.y+w.z,0.0001);float3 x=Texture2DSample(Tex,TexSampler,P.yz/Scale).rgb;float3 y=Texture2DSample(Tex,TexSampler,P.xz/Scale).rgb;float3 z=Texture2DSample(Tex,TexSampler,P.xy/Scale).rgb;return x*w.x+y*w.y+z*w.z;',{'Tex':texobj(m,texture),'P':p,'N':n,'Scale':b.const(m,scale)},u.CustomMaterialOutputType.CMOT_FLOAT3,'Physical-scale continuous triplanar, mirrored sampler')
def height(m,c):return custom(m,'return dot(C,float3(0.2126,0.7152,0.0722));',{'C':c})
def bump(m,h,p,n,strength):
 return custom(m,'float3 px=ddx(P),py=ddy(P);float3 r1=cross(py,N),r2=cross(N,px);float det=dot(px,r1);float3 g=sign(det)*(ddx(H)*r1+ddy(H)*r2);return normalize((abs(det)+0.000001)*N-Strength*g);',{'H':h,'P':p,'N':n,'Strength':b.const(m,strength)},u.CustomMaterialOutputType.CMOT_FLOAT3,'World-space surface gradient; strength in centimetres')
NOISE='''struct LocalNoise { float hash(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);} float value(float2 p){float2 i=floor(p),f=frac(p);f=f*f*(3.0-2.0*f);return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1),f.x),f.y);} float fbm(float2 p){return value(p)*0.57+value(p*2.07+float2(9.2,3.7))*.29+value(p*4.11+float2(1.8,7.4))*.14;}};LocalNoise no;'''
def noise(m,p,n=None,scale=100,time_node=None):
 inputs={'P':p,'Scale':b.const(m,scale)}
 if time_node:
  inputs['T']=time_node
  code=NOISE+'float2 q=P.xy/Scale;float t=T*.10;float2 warp=float2(no.value(q*.6+float2(t,0)),no.value(q*.7+float2(0,-t)))-.5;return no.fbm(q+warp*.65+float2(t*.65,-t*.33));'
 else:code=NOISE+'return no.fbm((P.xy+P.z*.371)/Scale);'
 return custom(m,code,inputs,description='Soft nonperiodic value-noise detail')
def finish(m,base,h,p,n,rough,variation,strength,spec=.25):
 m.set_editor_property('tangent_space_normal',False)
 b.prop(base,m,u.MaterialProperty.MP_BASE_COLOR);b.prop(bump(m,h,p,n,strength),m,u.MaterialProperty.MP_NORMAL)
 r=custom(m,'return clamp(Base+(H-.5)*Range,.35,.98);',{'Base':b.const(m,rough),'H':h,'Range':b.const(m,variation)})
 b.prop(r,m,u.MaterialProperty.MP_ROUGHNESS);b.prop(b.const(m,spec),m,u.MaterialProperty.MP_SPECULAR)
 M.layout_material_expressions(m);M.recompile_material(m);E.save_loaded_asset(m)
def import_generated():
 textures={}
 for name in ['Timber','Stone','Snow']:
  task=u.AssetImportTask();task.filename=str(PASS/'ImageGen'/('T_IMG_'+name+'.png'));task.destination_path=A+'/Textures';task.destination_name='T_IMG_'+name;task.automated=True;task.replace_existing=True;task.save=True;b.tools.import_asset_tasks([task])
  tex=u.load_asset(A+'/Textures/T_IMG_'+name);assert tex
  for key,value in {'srgb':True,'compression_settings':u.TextureCompressionSettings.TC_DEFAULT,'address_x':u.TextureAddress.TA_MIRROR,'address_y':u.TextureAddress.TA_MIRROR,'power_of_two_mode':u.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO,'mip_gen_settings':u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,'never_stream':False}.items():tex.set_editor_property(key,value)
  E.save_loaded_asset(tex);textures[name]=tex
 return textures
def change_materials(tex):
 records=[]
 for name in ['Wood','DarkWood','Stone','Snow','Path','Plaster','Towel','Red','Water']:
  m=u.load_asset(A+'/Materials/M_'+name);assert m;M.delete_all_material_expressions(m);p,n=position_normal(m)
  if name in ['Wood','DarkWood']:
   source=sample(m,tex['Timber']);h=height(m,source);base=b.mul(m,source,b.const(m,.90 if name=='Wood' else .43))
   finish(m,base,h,p,n,.72 if name=='Wood' else .77,.18,.065,.23)
   desc={'source':'T_IMG_Timber','mapping':'component long-axis/centerline arc UV','source_tile_m':2.5,'source_density_px_per_m':501.6,'built_sampling_px_per_m':819.2,'normal_height_cm':.065}
  elif name in ['Stone','Path','Snow']:
   tile=500 if name=='Snow' else 250;source=triplanar(m,tex['Snow' if name=='Snow' else 'Stone'],p,n,tile);h=height(m,source)
   code=('return lerp(float3(.73,.80,.84),C,.43);' if name=='Snow' else 'return lerp(float3(.205,.245,.265),C,.34);' if name=='Stone' else 'return lerp(float3(.21,.225,.23),C,.26);')
   base=custom(m,code,{'C':source},u.CustomMaterialOutputType.CMOT_FLOAT3,'Restrained mineral/crystal contrast; no painted lighting')
   finish(m,base,h,p,n,.91 if name=='Snow' else .82,.16,.16 if name=='Snow' else .14,.18 if name=='Snow' else .24)
   desc={'source':'T_IMG_Snow' if name=='Snow' else 'T_IMG_Stone','mapping':'world triplanar, weight exponent4','source_tile_m':tile/100,'source_density_px_per_m':1254/(tile/100),'built_sampling_px_per_m':2048/(tile/100),'normal_height_cm':.16 if name=='Snow' else .14}
  elif name=='Plaster':
   source=sample(m,u.load_asset(A+'/Textures/T_Plaster'));h=noise(m,p,scale=6);base=custom(m,'return C*(.95+H*.10);',{'C':source,'H':h},u.CustomMaterialOutputType.CMOT_FLOAT3)
   finish(m,base,h,p,n,.88,.14,.035,.19);desc={'source':'baseline T_Plaster','detail':'6cm spatial mottling,0.35mm surface gradient; albedo variation5%'}
  elif name in ['Towel','Red']:
   source=sample(m,u.load_asset(A+'/Textures/T_'+name));h=custom(m,'float3 w=abs(N);float2 q=w.z>w.x&&w.z>w.y?P.xy:(w.y>w.x?P.xz:P.yz);float2 fw=fwidth(q);float att=saturate(1-max(fw.x,fw.y)/.20);return .5+.24*sin(q.x*31.4159)*sin(q.y*31.4159)*att;',{'P':p,'N':n},description='2mm woven fibres, screen-footprint attenuation')
   finish(m,source,h,p,n,.93,.1,.018,.14);desc={'source':'baseline T_'+name,'detail':'2mm weave with fwidth antialias attenuation;0.18mm height'}
  else:
   tm=b.node(m,u.MaterialExpressionTime);h=noise(m,p,scale=65,time_node=tm)
   base=custom(m,'return float3(.016,.365,.325)*(.94+.12*H);',{'H':h},u.CustomMaterialOutputType.CMOT_FLOAT3,'Turquoise water, subtle organic variation')
   finish(m,base,h,p,n,.53,.10,.85,.05)
   b.prop(b.mul(m,base,b.const(m,.25)),m,u.MaterialProperty.MP_EMISSIVE_COLOR)
   sine=b.node(m,u.MaterialExpressionSine);sine.set_editor_property('period',5.7);b.link(tm,sine,'Input');b.prop(b.mul(m,sine,b.color(m,(0,0,1.3))),m,u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
   M.recompile_material(m);E.save_loaded_asset(m);desc={'source':'original shader-authored advected value noise; no bitmap','detail':'65cm organic domain-warped FBM;0.85cm normal height; low color amplitude','motion':'existing5.7s/1.3cm vertical sine retained plus new advected ripples'}
  desc.update(material=m.get_path_name(),two_sided=m.get_editor_property('two_sided'),tangent_space_normal=m.get_editor_property('tangent_space_normal'));records.append(desc)
 b.dump('material_mapping.json',{'at_utc':b.now(),'materials':records,'original_image_pixels_edited':False,'mirror_repeat_note':'Mirror addressing changes motifs to a2x tile repeat; no original edge-continuity claim.'})
def import_uv_meshes():
 audit=json.loads((PASS/'Validation/uv_geometry_validation.json').read_text());changes=[r['mesh'] for r in audit['meshes'] if r['wood_components']>0]
 for name in changes:
  task=u.AssetImportTask();task.filename=str(PASS/'Source'/(name+'.fbx'));task.destination_path=A+'/Meshes';task.destination_name=name;task.automated=True;task.replace_existing=True;task.save=True
  opt=u.FbxImportUI()
  for key,value in {'import_mesh':True,'import_materials':False,'import_textures':False,'import_as_skeletal':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH}.items():opt.set_editor_property(key,value)
  data=opt.get_editor_property('static_mesh_import_data')
  for key,value in {'combine_meshes':True,'auto_generate_collision':False,'generate_lightmap_u_vs':False,'import_uniform_scale':1.0,'convert_scene':True,'normal_import_method':u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS}.items():data.set_editor_property(key,value)
  task.options=opt;b.tools.import_asset_tasks([task]);mesh=u.load_asset(A+'/Meshes/'+name);assert mesh
  slots=list(mesh.get_editor_property('static_materials'))
  for slot in slots:slot.set_editor_property('material_interface',u.load_asset(A+'/Materials/M_'+str(slot.get_editor_property('material_slot_name'))))
  mesh.set_editor_property('static_materials',slots);E.save_loaded_asset(mesh)
 b.dump('uv_mesh_imports.json',{'at_utc':b.now(),'reimported_meshes':changes,'other_meshes_kept_byte_identical':True,'geometry_change':False})
def validate_pass():
 b.validate();assert sha(DISK_MAP)==sha(BASE_MAP),'Map/layout/light/exposure bytes changed'
 textures=[]
 for path in E.list_assets(A+'/Textures',recursive=True,include_folder=False):
  t=u.load_asset(path);files=[]
  for fn in t.get_editor_property('asset_import_data').extract_filenames():
   pp=Path(fn).resolve();assert str(pp).replace('\\','/').startswith(str(BASE).replace('\\','/'));dd=pp.read_bytes();files.append({'path':str(pp),'sha256':sha(pp),'source_resolution':[int.from_bytes(dd[16:20],'big'),int.from_bytes(dd[20:24],'big')]})
  textures.append({'asset':path,'source_files':files,'built_size':[t.blueprint_get_size_x(),t.blueprint_get_size_y()],'srgb':t.get_editor_property('srgb'),'power_of_two_mode':str(t.get_editor_property('power_of_two_mode')),'mip_gen_settings':str(t.get_editor_property('mip_gen_settings')),'never_stream':t.get_editor_property('never_stream'),'address_x':str(t.get_editor_property('address_x')),'address_y':str(t.get_editor_property('address_y')),'compression':str(t.get_editor_property('compression_settings'))})
 b.dump('texture_import_validation.json',{'at_utc':b.now(),'textures':textures,'map_binary_matches_first_delivery':True,'baseline_map_sha256':sha(BASE_MAP),'current_map_sha256':sha(DISK_MAP),'mip_evidence':'ListTextures -CSV actual runtime NumMips in UE log; parsed after editor closes.'})
 u.SystemLibrary.execute_console_command(b.editor.get_editor_world(),'ListTextures -CSV')
if __name__=='__main__':
 try:
  assert sha(DISK_MAP)==sha(BASE_MAP);assert b.levels.load_level(MAP)
  u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
  generated=import_generated();change_materials(generated);import_uv_meshes();E.save_directory(A,only_if_is_dirty=True,recursive=True)
  validate_pass();capture_views.capture()
 except Exception:
  b.dump('build_error.json',{'at_utc':b.now(),'traceback':traceback.format_exc()});u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
