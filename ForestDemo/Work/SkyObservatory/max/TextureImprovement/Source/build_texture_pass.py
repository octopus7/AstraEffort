import unreal as u,json,time,traceback,hashlib,struct,shutil
from pathlib import Path
BASE=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max');ROOT=BASE/'TextureImprovement';ART=ROOT/'SourceArt';E=ROOT/'Evidence';ASSET='/Game/SkyObservatory/max';MAP='/Game/Maps/SkyObservatory_max'
u.EditorPythonScripting.set_keep_python_script_alive(True)
tools=u.AssetToolsHelpers.get_asset_tools();actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem);smss=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
def prop(o,n,v):o.set_editor_property(n,v)
def write(name,v):(E/name).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
WORLD={'Limestone','StoneDark','RockBlue','RockPale','Grass','Moss','Path','Leaf','LeafLight','Lavender','Cloud','Window','Star'}
IMAGE_MAP={'RoofTeal':'teal','RoofLight':'teal','Limestone':'limestone','StoneDark':'limestone','Path':'limestone','RockBlue':'rock','RockPale':'rock','WoodLight':'timber','Timber':'timber','Grass':'moss','Moss':'moss','Leaf':'moss','LeafLight':'moss'}
PIXELS_PER_M={'RoofTeal':128,'RoofLight':128,'Limestone':128,'StoneDark':128,'Path':128,'WoodLight':128,'Timber':128,'Brass':256,'BrassLight':256,'Iron':128,'Lens':64}
TINT={'RoofTeal':(.90,1.0,1.0),'RoofLight':(1.0,1.08,1.08),'Limestone':(.80,.86,.92),'StoneDark':(.18,.25,.34),'Path':(.68,.63,.50),'RockBlue':(.70,.80,1.0),'RockPale':(.90,1.0,1.05),'Timber':(.58,.45,.32),'WoodLight':(.88,.75,.54),'Grass':(.5,.75,2.0),'Moss':(.85,.95,2.0),'Leaf':(.3,.5,1.4),'LeafLight':(.6,.9,2.0)}

def snapshot():
 data=[]
 for a in actors.get_all_level_actors():
  label=a.get_actor_label();lc=a.get_component_by_class(u.LightComponentBase)
  if lc:
   c=lc.get_editor_property('light_color');loc=a.get_actor_location();rot=a.get_actor_rotation();data.append({'label':label,'intensity':lc.get_editor_property('intensity'),'color':[c.r,c.g,c.b,c.a],'mobility':str(lc.mobility),'location':[loc.x,loc.y,loc.z],'rotation':[rot.pitch,rot.yaw,rot.roll]})
  if label=='Calm_Dusk_Grade':
   s=a.get_editor_property('settings');data.append({'label':label,'bias':s.get_editor_property('auto_exposure_bias'),'method':str(s.get_editor_property('auto_exposure_method')),'physical_camera':s.get_editor_property('auto_exposure_apply_physical_camera_exposure'),'bloom':s.get_editor_property('bloom_intensity'),'vignette':s.get_editor_property('vignette_intensity')})
  if label in ['Capture_overview','Capture_top_down','Capture_observatory','Capture_bridge']:
   c=a.get_component_by_class(u.CameraComponent);loc=a.get_actor_location();rot=a.get_actor_rotation();data.append({'label':label,'location':[loc.x,loc.y,loc.z],'rotation':[rot.pitch,rot.yaw,rot.roll],'projection':str(c.projection_mode),'ortho_width':c.ortho_width,'fov':c.field_of_view})
 return sorted(data,key=lambda d:d['label'])

def import_images():
 dst=ART/'Textures';dst.mkdir(exist_ok=True);tasks=[];records=[]
 for name,kind in IMAGE_MAP.items():
  original=ROOT/'ImageGen'/(kind+'_albedo_original.png');copy=dst/('T_'+name+'.png');shutil.copy2(original,copy);data=copy.read_bytes()
  w,h=struct.unpack('>II',data[16:24]);assert(w,h)==(1254,1254)
  task=u.AssetImportTask();task.filename=str(copy);task.destination_path=ASSET+'/Textures';task.destination_name='T_'+name;task.automated=True;task.replace_existing=True;task.save=True;tasks.append(task)
  records.append({'texture':'T_'+name,'imagegen_original':str(original),'source_size':[w,h],'source_sha256':hashlib.sha256(data).hexdigest(),'native_build_resize':'ResizeToSpecificResolution 1024x1024, no padding','intended_runtime_size':[1024,1024],'color_space':'sRGB albedo','target_runtime_texels_per_m':PIXELS_PER_M.get(name,64)})
 tools.import_asset_tasks(tasks)
 for name in IMAGE_MAP:
  tex=u.load_asset(ASSET+'/Textures/T_'+name);assert tex
  prop(tex,'srgb',True);prop(tex,'power_of_two_mode',u.TexturePowerOfTwoSetting.RESIZE_TO_SPECIFIC_RESOLUTION);prop(tex,'resize_during_build_x',1024);prop(tex,'resize_during_build_y',1024)
  prop(tex,'mip_gen_settings',u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP);prop(tex,'address_x',u.TextureAddress.TA_WRAP);prop(tex,'address_y',u.TextureAddress.TA_WRAP)
  prop(tex,'compression_settings',u.TextureCompressionSettings.TC_DEFAULT);u.EditorAssetLibrary.save_loaded_asset(tex)
 write('texture_source_manifest.json',{'records':records,'originals_unedited':True,'ue_native_resize_only':True})

def expr(mat,cls,x,y):return u.MaterialEditingLibrary.create_material_expression(mat,cls,x,y)
def connect(a,out,b,slot):assert u.MaterialEditingLibrary.connect_material_expressions(a,out,b,slot)
def custom(mat,code,names,x,y,kind=u.CustomMaterialOutputType.CMOT_FLOAT3):
 n=expr(mat,u.MaterialExpressionCustom,x,y);prop(n,'code',code);prop(n,'output_type',kind);inputs=[]
 for name in names:
  item=u.CustomInput();prop(item,'input_name',name);inputs.append(item)
 prop(n,'inputs',inputs);return n
def constant(mat,v,x,y):
 n=expr(mat,u.MaterialExpressionConstant,x,y);n.r=v;return n
def materials(only=None):
 old=json.loads((BASE/'SourceArt/materials.json').read_text());records=[]
 for name,p in old.items():
  if only and name not in only:continue
  mat=u.load_asset(ASSET+'/Materials/M_'+name);tex=u.load_asset(ASSET+'/Textures/T_'+name);assert mat and tex
  u.MaterialEditingLibrary.delete_all_material_expressions(mat);prop(mat,'two_sided',False);prop(mat,'tangent_space_normal',True)
  obj=expr(mat,u.MaterialExpressionTextureObject,-1000,0);obj.texture=tex;ppm=PIXELS_PER_M.get(name,64);tile_cm=1024/ppm*100
  uv=expr(mat,u.MaterialExpressionTextureCoordinate,-1000,300);uv.u_tiling=ppm/64;uv.v_tiling=ppm/64
  if name in WORLD:
   pos=expr(mat,u.MaterialExpressionWorldPosition,-1000,500);normal=expr(mat,u.MaterialExpressionVertexNormalWS,-1000,700)
   code=f'float3 p=W/{tile_cm:.9f}; float3 w=pow(abs(normalize(N)),4.0); w/=max(w.x+w.y+w.z,0.00001); return Texture2DSample(T,TSampler,p.yz).rgb*w.x+Texture2DSample(T,TSampler,p.xz).rgb*w.y+Texture2DSample(T,TSampler,p.xy).rgb*w.z;'
   sample=custom(mat,code,['T','W','N'],-600,0);connect(obj,'',sample,'T');connect(pos,'',sample,'W');connect(normal,'',sample,'N');path='smooth_world_triplanar'
  else:
   sample=custom(mat,'return Texture2DSample(T,TSampler,UV).rgb;',['T','UV'],-600,0);connect(obj,'',sample,'T');connect(uv,'',sample,'UV');path='connected_surface_uv'
  if name in ['Brass','BrassLight','Iron']:
   rgb={'Brass':(.52,.28,.07),'BrassLight':(.72,.46,.15),'Iron':(.035,.065,.09)}[name];base=expr(mat,u.MaterialExpressionConstant3Vector,-300,-150);base.constant=u.LinearColor(*rgb,1)
  else:
   tint=TINT.get(name,(1,1,1));base=custom(mat,f'return C*float3({tint[0]},{tint[1]},{tint[2]});',['C'],-300,-150);connect(sample,'',base,'C')
  u.MaterialEditingLibrary.connect_material_property(base,'',u.MaterialProperty.MP_BASE_COLOR)
  rough=p['roughness'];metal=p['metallic']
  if name in ['Brass','BrassLight']:rough=.34 if name=='Brass' else .31;metal=.78
  if name in ['RoofTeal','RoofLight']:rough=.48;metal=.24
  amount=.10 if name in ['Brass','BrassLight','RoofTeal','RoofLight','WoodLight','Timber','Limestone'] else .035
  roughnode=custom(mat,f'return clamp({rough}+ (dot(C,float3(.2126,.7152,.0722))-.25)*{amount},0.08,0.98);',['C'],-250,170,u.CustomMaterialOutputType.CMOT_FLOAT1);connect(sample,'',roughnode,'C');u.MaterialEditingLibrary.connect_material_property(roughnode,'',u.MaterialProperty.MP_ROUGHNESS)
  mn=constant(mat,metal,-250,300);u.MaterialEditingLibrary.connect_material_property(mn,'',u.MaterialProperty.MP_METALLIC)
  if name in ['RoofTeal','RoofLight','WoodLight','Timber','Brass','BrassLight','Iron']:
   strength=3.0 if name in ['WoodLight','Timber'] else (1.2 if name in ['RoofTeal','RoofLight'] else .35)
   code=f'float e=1.0/1024.0; float3 l=float3(.2126,.7152,.0722); float dx=dot(Texture2DSample(T,TSampler,UV+float2(e,0)).rgb-Texture2DSample(T,TSampler,UV-float2(e,0)).rgb,l); float dy=dot(Texture2DSample(T,TSampler,UV+float2(0,e)).rgb-Texture2DSample(T,TSampler,UV-float2(0,e)).rgb,l); return normalize(float3(-dx*{strength},-dy*{strength},1.0));'
   bump=custom(mat,code,['T','UV'],-300,500);connect(obj,'',bump,'T');connect(uv,'',bump,'UV');u.MaterialEditingLibrary.connect_material_property(bump,'',u.MaterialProperty.MP_NORMAL)
  if name in ['Window','Star','Lens','Cloud']:
   amp={'Window':2.2,'Star':1.2,'Lens':.28,'Cloud':1.0}[name];em=custom(mat,f'return C*{amp};',['C'],-150,-400);connect(sample,'',em,'C');u.MaterialEditingLibrary.connect_material_property(em,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
  u.MaterialEditingLibrary.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat)
  records.append({'material':'M_'+name,'texture':'T_'+name,'sampling_path':path,'runtime_texture_size':1024,'target_runtime_texels_per_m':ppm,'tile_size_cm':tile_cm,'uv_scale':ppm/64 if name not in WORLD else None,'triplanar_normal_blend_exponent':4 if name in WORLD else None,'base_tint':TINT.get(name),'roughness_base':rough,'metallic':metal,'normal_detail':'albedo finite differences, artistic microdetail' if name in ['RoofTeal','RoofLight','WoodLight','Timber','Brass','BrassLight','Iron'] else 'geometry normal','no_per_face_phase_or_rotation':True})
 write('material_sampling_manifest.json',{'materials':records,'world_continuity':'World position is continuous on every shared mesh edge; the three projection coordinates use fixed physical axes. Blended geometric vertex-normal weights replace hard per-face dominant-axis sampling. Declared hard geometric normals remain shading boundaries, not random texture phases.','uv_policy':'Lambert dome shells, separate crown/base/slit thickness caps, stable component-axis timber charts; no triangle-local UV normalization.'})

def meshes():
 tasks=[]
 for path in sorted((ART/'Meshes').glob('*.fbx')):
  options=u.FbxImportUI();options.import_mesh=True;options.import_materials=False;options.import_textures=False;options.import_as_skeletal=False;options.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;options.automated_import_should_detect_type=False
  d=options.static_mesh_import_data
  for key,value in {'combine_meshes':True,'generate_lightmap_u_vs':False,'auto_generate_collision':False,'normal_import_method':u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS,'convert_scene':True,'convert_scene_unit':True,'import_uniform_scale':1.0}.items():prop(d,key,value)
  task=u.AssetImportTask();task.filename=str(path);task.destination_path=ASSET+'/Meshes';task.destination_name=path.stem;task.automated=True;task.save=True;task.replace_existing=True;task.options=options;tasks.append(task)
 tools.import_asset_tasks(tasks)
 for path in sorted((ART/'Meshes').glob('*.fbx')):
  mesh=u.load_asset(ASSET+'/Meshes/'+path.stem);slots=list(mesh.static_materials)
  for slot in slots:
   name=str(slot.material_slot_name);slot.material_interface=u.load_asset(ASSET+'/Materials/M_'+name);assert slot.material_interface
  prop(mesh,'static_materials',slots);settings=smss.get_lod_build_settings(mesh,0);prop(settings,'use_full_precision_u_vs',True);prop(settings,'generate_lightmap_u_vs',False);prop(settings,'recompute_normals',False);prop(settings,'recompute_tangents',True);prop(settings,'use_mikk_t_space',True);smss.set_lod_build_settings(mesh,0,settings);u.EditorAssetLibrary.save_loaded_asset(mesh)

def run_build():
 try:
  started=time.time();assert levels.load_level(MAP);before=snapshot();write('baseline_lighting_cameras.json',before)
  if not (E/'texture_source_manifest.json').exists():import_images()
  materials();meshes();assert levels.load_level(MAP)
  # Detail cameras add evidence only. Existing four cameras and all lighting stay byte-for-value identical.
  cameras=json.loads((BASE/'Screenshots/capture_manifest.json').read_text())['captures'];specs=[{k:v for k,v in c.items() if k in ['name','location_cm','rotation_degrees','target_cm','projection','ortho_width_cm','fov_degrees']} for c in cameras]
  existing={a.get_actor_label():a for a in actors.get_all_level_actors()}
  for name,pos,target,fov in [('material_dome',(1800,-1800,2500),(-400,500,1600),40),('material_bridge',(2100,-2400,1000),(1050,-1500,450),42)]:
   rot=u.MathLibrary.find_look_at_rotation(u.Vector(*pos),u.Vector(*target));cam=existing.get('Capture_'+name) or actors.spawn_actor_from_class(u.CameraActor,u.Vector(*pos),rot);cam.set_actor_label('Capture_'+name);cc=cam.get_component_by_class(u.CameraComponent);prop(cc,'aspect_ratio',16/9);prop(cc,'constrain_aspect_ratio',False);prop(cc,'field_of_view',fov)
   specs.append({'name':name,'location_cm':pos,'rotation_degrees':{'pitch':rot.pitch,'yaw':rot.yaw,'roll':rot.roll},'target_cm':target,'projection':'perspective','ortho_width_cm':None,'fov_degrees':fov})
  write('camera_specs.json',specs);after=snapshot();assert before==after,'Baseline light/exposure/camera changed';write('lighting_camera_preservation.json',{'unchanged':True,'before':before,'after':after})
  assert levels.save_current_level();u.EditorAssetLibrary.save_directory(ASSET,only_if_is_dirty=False,recursive=True);u.EditorLoadingAndSavingUtils.new_blank_map(False);assert levels.load_level(MAP)
  write('build_summary.json',{'started_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(started)),'finished_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'build_seconds':time.time()-started,'changed_image_texture_assets':len(IMAGE_MAP),'materials':21,'meshes':17,'lighting_unchanged':True})
  exec(compile((ROOT/'Source/validate_capture.py').read_text(encoding='utf-8'),str(ROOT/'Source/validate_capture.py'),'exec'),globals())
 except Exception:
  write('build_error.json',{'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'traceback':traceback.format_exc()});u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()

if __name__=='__main__':run_build()
