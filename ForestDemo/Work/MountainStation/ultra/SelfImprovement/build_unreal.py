import unreal as u,json,datetime,traceback
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement');A='/Game/MountainStation/ultra';MAP='/Game/Maps/MountainStation_ultra'
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(name,x):(R/name).write_text(json.dumps(x,indent=2))
def rgb(h):
    vals=[int(h[i:i+2],16)/255 for i in [1,3,5]];return [v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in vals]
try:
    level=u.get_editor_subsystem(u.LevelEditorSubsystem);assert level.load_level(MAP)
    editor=u.get_editor_subsystem(u.EditorActorSubsystem);ss=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);ml=u.MaterialEditingLibrary;tools=u.AssetToolsHelpers.get_asset_tools()
    art=json.loads((R/'art_manifest.json').read_text());layouts=json.loads((R/'uv_layouts.json').read_text());old=json.loads((R.parent/'TexturePass/build_evidence.json').read_text());images=json.loads((R.parent/'TexturePass/images_manifest.json').read_text())
    actors=[{'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'location':list(a.get_actor_location().to_tuple()),'rotation':list(a.get_actor_rotation().to_tuple()),'scale':list(a.get_actor_scale3d().to_tuple())} for a in editor.get_all_level_actors()]
    if not (R/'scene_before_self.json').exists():write('scene_before_self.json',{'actors':actors})
    result={**old,'started_at_utc':stamp(),'pass':'SelfImprovement','saved':False};materials={x['material']:x for x in old['materials']};records={x['name']:x for x in old['meshes']}
    # A separate path master blends the existing gravel and meadow tints using
    # exported corner colors. It retains the actual owned stone image sampler.
    folder=A+'/Materials/SelfImprovement';u.EditorAssetLibrary.make_directory(folder);masterpath=folder+'/M_SoftPath'
    master=u.load_asset(masterpath) if u.EditorAssetLibrary.does_asset_exist(masterpath) else tools.create_asset('M_SoftPath',folder,u.Material,u.MaterialFactoryNew())
    ml.delete_all_material_expressions(master);master.set_editor_property('two_sided',True)
    def node(cls,x,y,**values):
        n=ml.create_material_expression(master,cls,x,y)
        for k,v in values.items():n.set_editor_property(k,v)
        return n
    def link(a,out,b,inp):assert ml.connect_material_expressions(a,out,b,inp)
    coord=node(u.MaterialExpressionTextureCoordinate,-900,0,coordinate_index=0)
    scale=node(u.MaterialExpressionVectorParameter,-900,180,parameter_name='UVScale',default_value=u.LinearColor(1,1,0,0));mask=node(u.MaterialExpressionComponentMask,-700,180,r=True,g=True,b=False,a=False);link(scale,'',mask,'')
    scaled=node(u.MaterialExpressionMultiply,-500,0);link(coord,'',scaled,'A');link(mask,'',scaled,'B')
    tex=u.load_asset(A+'/Textures/TexturePass/T_stone');sample=node(u.MaterialExpressionTextureSampleParameter2D,-300,0,parameter_name='DetailTexture',texture=tex,sampler_type=u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR);link(scaled,'',sample,'')
    contrast=node(u.MaterialExpressionMultiply,-100,0,const_b=.4);link(sample,'R',contrast,'A');offset=node(u.MaterialExpressionAdd,100,0,const_b=.8);link(contrast,'',offset,'A')
    tint=node(u.MaterialExpressionVectorParameter,-450,300,parameter_name='Tint',default_value=u.LinearColor(*rgb(art['palette']['Gravel'][0]),1));edge=node(u.MaterialExpressionVectorParameter,-450,480,parameter_name='EdgeTint',default_value=u.LinearColor(*rgb(art['palette']['Meadow'][0]),1));vc=node(u.MaterialExpressionVertexColor,-450,650)
    blend=node(u.MaterialExpressionLinearInterpolate,-100,350);link(edge,'',blend,'A');link(tint,'',blend,'B');link(vc,'R',blend,'Alpha')
    color=node(u.MaterialExpressionMultiply,300,0);link(blend,'',color,'A');link(offset,'',color,'B');assert ml.connect_material_property(color,'',u.MaterialProperty.MP_BASE_COLOR)
    rough=node(u.MaterialExpressionScalarParameter,300,250,parameter_name='Roughness',default_value=.98);assert ml.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
    ml.recompile_material(master);u.EditorAssetLibrary.save_loaded_asset(master)
    changed=['SM_Ballast','SM_Rails','SM_Footpath','SM_PedestrianCrossing']
    for name in changed:
        entry=next(x for x in art['meshes'] if x['name']==name);task=u.AssetImportTask();task.filename=entry['file'];task.destination_path=A+'/Meshes';task.destination_name=name;task.automated=True;task.replace_existing=True;task.save=True
        options=u.FbxImportUI();options.import_materials=False;options.import_textures=False;options.import_as_skeletal=False;options.automated_import_should_detect_type=False;options.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
        imp=options.static_mesh_import_data;imp.combine_meshes=True;imp.auto_generate_collision=False;imp.generate_lightmap_u_vs=False;imp.convert_scene=False;imp.convert_scene_unit=True;imp.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS;imp.vertex_color_import_option=u.VertexColorImportOption.REPLACE
        task.options=options;task.factory=u.FbxFactory();tools.import_asset_tasks([task]);sm=u.load_asset(A+'/Meshes/'+name);assert sm
        build=ss.get_lod_build_settings(sm,0);build.use_full_precision_u_vs=True;build.generate_lightmap_u_vs=False;ss.set_lod_build_settings(sm,0,build)
        sm.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        for si in range(sm.get_num_sections(0)):ss.enable_section_collision(sm,True,0,si)
        side=layouts[name]['side_px'];slots=[]
        for si,slot in enumerate(sm.static_materials):
            palette=str(slot.material_slot_name).split('.')[0];assert palette in art['palette']
            family='wood' if name=='SM_PedestrianCrossing' else ('metal' if name=='SM_Rails' else 'stone')
            image=next(x for x in images['calls'] if x['name']==family);w,h=image['dimensions']
            parent=master if name=='SM_Footpath' else u.load_asset(A+'/Materials/TexturePass/M_SurfaceDetail')
            mi_name=('MI_SoftPath_' if name=='SM_Footpath' else 'MI_'+family+'_'+palette+'_')+str(side);mi_path=folder+'/'+mi_name
            mi=u.load_asset(mi_path) if u.EditorAssetLibrary.does_asset_exist(mi_path) else tools.create_asset(mi_name,folder,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
            ml.set_material_instance_parent(mi,parent);texture=u.load_asset(A+'/Textures/TexturePass/T_'+family)
            ml.set_material_instance_texture_parameter_value(mi,'DetailTexture',texture);ml.set_material_instance_vector_parameter_value(mi,'UVScale',u.LinearColor(side/w,side/h,0,0));ml.set_material_instance_vector_parameter_value(mi,'Tint',u.LinearColor(*rgb(art['palette'][palette][0]),1));ml.set_material_instance_scalar_parameter_value(mi,'Roughness',art['palette'][palette][1]);ml.update_material_instance(mi);u.EditorAssetLibrary.save_loaded_asset(mi);sm.set_material(si,mi)
            materials[mi.get_path_name()]={'material':mi.get_path_name(),'parent':parent.get_path_name(),'image':family,'texture':texture.get_path_name(),'image_sha256':image['sha256'],'source_dimensions':[w,h],'uv_scale':[side/w,side/h],'virtual_atlas_side_px':side,'base_texels_per_meter':128}
            slots.append({'slot':si,'source_palette':palette,'material':mi.get_path_name(),'image':family,'uv_scale':[side/w,side/h]})
        u.EditorAssetLibrary.save_loaded_asset(sm);records[name]={'name':name,'mesh':sm.get_path_name(),'slots':slots,'full_precision_uvs':True,'virtual_atlas_side_px':side,'section_collision_restored':[True]*sm.get_num_sections(0)}
        if name=='SM_PedestrianCrossing':
            existing=[a for a in editor.get_all_level_actors() if a.get_actor_label()=='Pedestrian crossing']
            a=existing[0] if existing else editor.spawn_actor_from_class(u.StaticMeshActor,u.Vector());a.set_actor_label('Pedestrian crossing');a.static_mesh_component.set_static_mesh(sm);a.set_actor_scale3d(u.Vector(1,-1,1));a.static_mesh_component.set_collision_profile_name('BlockAll')
    import math
    tx=31;ty=-9+.012*34**2;tz=.82+.0015*13**2-.25;angle=math.atan(.024*34)
    lightrecords=[]
    for label,depth,intensity in [('Tunnel entrance fill',1.5,900.),('Tunnel inner fill',5.,650.)]:
        existing=[a for a in editor.get_all_level_actors() if a.get_actor_label()==label]
        a=existing[0] if existing else editor.spawn_actor_from_class(u.PointLight,u.Vector((tx+math.cos(angle)*depth)*100,(ty+math.sin(angle)*depth)*100,(tz+4.5)*100));a.set_actor_label(label)
        c=a.light_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',u.LightUnits.LUMENS);c.set_intensity(intensity);c.set_attenuation_radius(650.);c.set_light_color(u.LinearColor(1,.86,.70,1));c.set_editor_property('source_radius',18.);c.set_editor_property('cast_shadows',True)
        lightrecords.append({'label':label,'location_cm':list(a.get_actor_location().to_tuple()),'intensity_lumens':intensity,'mobility':str(c.mobility),'attenuation_radius_cm':c.attenuation_radius})
    assert level.save_current_level();result.update(materials=list(materials.values()),meshes=list(records.values()),material_instance_count=len(materials),saved=True,finished_at_utc=stamp(),changed_meshes=changed,added_lights=lightrecords)
    write('build_evidence.json',result)
except Exception:write('build_error.json',{'utc':stamp(),'error':traceback.format_exc()});u.log_error(traceback.format_exc())
u.SystemLibrary.quit_editor()
