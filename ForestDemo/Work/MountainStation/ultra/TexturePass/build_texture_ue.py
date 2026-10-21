import unreal as u,json,datetime,traceback
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass');A='/Game/MountainStation/ultra';MAP='/Game/Maps/MountainStation_ultra'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(name,data):(R/name).write_text(json.dumps(data,indent=2))
def prop(o,k,v):o.set_editor_property(k,v)
def srgb(h):
    a=[int(h[i:i+2],16)/255 for i in (1,3,5)];return [v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in a]
def family(mesh,mat):
    if mat in ['Metal','Rail','Ink'] or mesh in ['SM_StationRoof','SM_RoofSeams']:return 'metal'
    if mesh=='SM_Trunks':return 'bark'
    if mat.startswith('Pine') or mesh in ['SM_Conifers','SM_Shrubs','SM_OutcropMoss','SM_MeadowDetails']:return 'foliage'
    if mat in ['Stone','StoneLight','StoneDark','Gravel','Ballast','Meadow','MeadowLight','Earth','Interior'] or mesh in ['SM_Platform','SM_PlatformCoping','SM_AccessRamp','SM_TunnelMasonry']:return 'stone'
    return 'wood'
EXEMPT={'SM_Lettering':'Small text remains solid for legibility','SM_Clock':'Clock face and hands retain clear solid markings','SM_StationGlass':'Stylized glass retains its existing smooth surface','SM_TunnelDarkness':'Dark visual backing is not a physical surface treatment'}
try:
    result={'started_at_utc':utc(),'map':MAP,'materials':[],'meshes':[],'exemptions':EXEMPT,'saved':False}
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);assert levels.load_level(MAP)
    editor=u.get_editor_subsystem(u.EditorActorSubsystem);ss=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);tools=u.AssetToolsHelpers.get_asset_tools();ml=u.MaterialEditingLibrary
    manifest=json.loads((R/'art_manifest.json').read_text());layouts=json.loads((R/'uv_layouts.json').read_text());images=json.loads((R/'images_manifest.json').read_text())
    for folder in ['Textures/TexturePass','Materials/TexturePass']:u.EditorAssetLibrary.make_directory(A+'/'+folder)
    textures={}
    for im in images['calls']:
        task=u.AssetImportTask();task.filename=im['workspace_file'];task.destination_path=A+'/Textures/TexturePass';task.destination_name='T_'+im['name'];task.automated=True;task.save=True;task.replace_existing=True;tools.import_asset_tasks([task])
        tex=u.load_asset(task.destination_path+'/'+task.destination_name);assert tex
        tex.set_editor_property('srgb',False);tex.set_editor_property('never_stream',True);tex.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tex.set_editor_property('address_x',u.TextureAddress.TA_WRAP);tex.set_editor_property('address_y',u.TextureAddress.TA_WRAP)
        u.EditorAssetLibrary.save_loaded_asset(tex);textures[im['name']]=tex
    masterpath=A+'/Materials/TexturePass/M_SurfaceDetail'
    master=u.load_asset(masterpath) if u.EditorAssetLibrary.does_asset_exist(masterpath) else tools.create_asset('M_SurfaceDetail',A+'/Materials/TexturePass',u.Material,u.MaterialFactoryNew())
    ml.delete_all_material_expressions(master);prop(master,'two_sided',True)
    def node(cls,x=0,y=0,**kwargs):
        n=ml.create_material_expression(master,cls,x,y)
        for k,v in kwargs.items():prop(n,k,v)
        return n
    def link(a,out,b,inp):
        # Empty input name explicitly selects the first input in UE's API.
        name='' if inp in ('Input','Coordinates') else inp
        assert ml.connect_material_expressions(a,out,b,name),(b.get_class().get_name(),ml.get_material_expression_input_names(b),inp)
    uv=node(u.MaterialExpressionTextureCoordinate,-900,0,coordinate_index=0)
    scale=node(u.MaterialExpressionVectorParameter,-900,180,parameter_name='UVScale',default_value=u.LinearColor(1,1,0,0))
    mask=node(u.MaterialExpressionComponentMask,-700,180,r=True,g=True,b=False,a=False);link(scale,'',mask,'Input')
    muluv=node(u.MaterialExpressionMultiply,-500,0);link(uv,'',muluv,'A');link(mask,'',muluv,'B')
    texn=node(u.MaterialExpressionTextureSampleParameter2D,-300,0,parameter_name='DetailTexture',texture=textures['wood'],sampler_type=u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR);link(muluv,'',texn,'Coordinates')
    contrast=node(u.MaterialExpressionMultiply,-80,0,const_b=.4);link(texn,'R',contrast,'A')
    offset=node(u.MaterialExpressionAdd,120,0,const_b=.8);link(contrast,'',offset,'A')
    tint=node(u.MaterialExpressionVectorParameter,-100,180,parameter_name='Tint',default_value=u.LinearColor(.3,.3,.3,1))
    color=node(u.MaterialExpressionMultiply,300,0);link(tint,'',color,'A');link(offset,'',color,'B');assert ml.connect_material_property(color,'',u.MaterialProperty.MP_BASE_COLOR)
    bias=node(u.MaterialExpressionAdd,-70,400,const_b=-.5);link(texn,'R',bias,'A')
    delta=node(u.MaterialExpressionMultiply,100,400,const_b=.12);link(bias,'',delta,'A')
    rough=node(u.MaterialExpressionScalarParameter,-100,550,parameter_name='Roughness',default_value=.8)
    add=node(u.MaterialExpressionAdd,300,400);link(rough,'',add,'A');link(delta,'',add,'B')
    clamp=node(u.MaterialExpressionClamp,450,400,min_default=0.,max_default=1.);link(add,'',clamp,'Input');assert ml.connect_material_property(clamp,'',u.MaterialProperty.MP_ROUGHNESS)
    ml.recompile_material(master);u.EditorAssetLibrary.save_loaded_asset(master)
    collision_before={};actors_before=[]
    for a in editor.get_all_level_actors():
        actors_before.append({'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'location':list(a.get_actor_location().to_tuple()),'rotation':list(a.get_actor_rotation().to_tuple()),'scale':list(a.get_actor_scale3d().to_tuple())})
    for entry in manifest['meshes']:
        sm=u.load_asset(A+'/Meshes/'+entry['name']);collision_before[entry['name']]=[ss.is_section_collision_enabled(sm,0,i) for i in range(sm.get_num_sections(0))]
    write('scene_before_texture.json',{'actors':actors_before,'section_collision':collision_before})
    cache={}
    for entry in manifest['meshes']:
        name=entry['name'];task=u.AssetImportTask();task.filename=entry['file'];task.destination_path=A+'/Meshes';task.destination_name=name;task.automated=True;task.replace_existing=True;task.save=True
        options=u.FbxImportUI();options.import_materials=False;options.import_textures=False;options.import_as_skeletal=False;options.automated_import_should_detect_type=False;options.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
        imp=options.static_mesh_import_data;imp.combine_meshes=True;imp.auto_generate_collision=False;imp.generate_lightmap_u_vs=False;imp.convert_scene=False;imp.convert_scene_unit=True;imp.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
        task.options=options;task.factory=u.FbxFactory();tools.import_asset_tasks([task]);sm=u.load_asset(A+'/Meshes/'+name)
        build=ss.get_lod_build_settings(sm,0);build.use_full_precision_u_vs=True;build.generate_lightmap_u_vs=False;ss.set_lod_build_settings(sm,0,build)
        sm.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        assert sm.get_num_sections(0)==len(collision_before[name]),'Section topology changed: '+name
        for i,value in enumerate(collision_before[name]):ss.enable_section_collision(sm,value,0,i)
        slots=[];side=layouts[name]['side_px']
        for i,s in enumerate(sm.static_materials):
            mat=str(s.material_slot_name).split('.')[0];assert mat in manifest['palette'],mat
            exempt=EXEMPT.get(name) or ('Emissive lamp glass retains original emission' if mat=='Lamp' else None)
            if exempt:
                mi=u.load_asset(A+'/Materials/M_'+mat);sm.set_material(i,mi);slots.append({'slot':i,'source_palette':mat,'material':mi.get_path_name(),'texture_exemption':exempt});continue
            kind=family(name,mat);im=next(x for x in images['calls'] if x['name']==kind);w,h=im['dimensions'];key=(kind,mat,side)
            if key not in cache:
                iname='MI_'+kind+'_'+mat+'_'+str(side);ipath=A+'/Materials/TexturePass/'+iname
                mi=u.load_asset(ipath) if u.EditorAssetLibrary.does_asset_exist(ipath) else tools.create_asset(iname,A+'/Materials/TexturePass',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
                ml.set_material_instance_parent(mi,master);ml.set_material_instance_texture_parameter_value(mi,'DetailTexture',textures[kind]);ml.set_material_instance_vector_parameter_value(mi,'UVScale',u.LinearColor(side/w,side/h,0,0))
                color,roughness=manifest['palette'][mat];ml.set_material_instance_vector_parameter_value(mi,'Tint',u.LinearColor(*srgb(color),1));ml.set_material_instance_scalar_parameter_value(mi,'Roughness',roughness)
                ml.update_material_instance(mi);u.EditorAssetLibrary.save_loaded_asset(mi);cache[key]=mi
                result['materials'].append({'material':mi.get_path_name(),'parent':master.get_path_name(),'image':kind,'texture':textures[kind].get_path_name(),'image_sha256':im['sha256'],'source_dimensions':[w,h],'uv_scale':[side/w,side/h],'virtual_atlas_side_px':side,'base_texels_per_meter':128})
            mi=cache[key];sm.set_material(i,mi);slots.append({'slot':i,'source_palette':mat,'material':mi.get_path_name(),'image':kind,'uv_scale':[side/w,side/h]})
        u.EditorAssetLibrary.save_loaded_asset(sm)
        result['meshes'].append({'mesh':sm.get_path_name(),'name':name,'slots':slots,'section_collision_restored':collision_before[name],'full_precision_uvs':True,'virtual_atlas_side_px':side});write('build_evidence.json',result)
    levels.save_current_level();result.update(saved=True,finished_at_utc=utc(),material_instance_count=len(cache));write('build_evidence.json',result)
except Exception:write('build_error.json',{'utc':utc(),'traceback':traceback.format_exc()});u.log_error(traceback.format_exc())
u.SystemLibrary.quit_editor()
