from ue_common import *

def import_file(path,dest,mesh=False):
    task=u.AssetImportTask();task.set_editor_property('filename',str(path));task.set_editor_property('destination_path',dest)
    task.set_editor_property('automated',True);task.set_editor_property('save',True);task.set_editor_property('replace_existing',True)
    if mesh:
        opts=u.FbxImportUI();opts.set_editor_property('import_mesh',True);opts.set_editor_property('import_as_skeletal',False)
        opts.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH);opts.set_editor_property('automated_import_should_detect_type',False)
        opts.set_editor_property('import_materials',False);opts.set_editor_property('import_textures',False)
        data=opts.get_editor_property('static_mesh_import_data');data.set_editor_property('combine_meshes',True);data.set_editor_property('auto_generate_collision',False)
        data.set_editor_property('generate_lightmap_u_vs',False);data.set_editor_property('convert_scene',True);data.set_editor_property('convert_scene_unit',True)
        data.set_editor_property('normal_import_method',u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
        task.set_editor_property('options',opts)
    assets.import_asset_tasks([task])
    out=task.get_editor_property('imported_object_paths');assert out, str(path)
    return u.load_asset(out[0])

def expr(m,cls,x,y):return u.MaterialEditingLibrary.create_material_expression(m,cls,x,y)
def constant(m,val,x=-350,y=250):
    e=expr(m,u.MaterialExpressionConstant,x,y);e.set_editor_property('r',val);return e
def connect(m,e,prop):u.MaterialEditingLibrary.connect_material_property(e,'',prop)
def new_material(name):
    m=u.load_asset(BASE+'/Materials/'+name)
    if m:u.MaterialEditingLibrary.delete_all_material_expressions(m)
    else:m=assets.create_asset(name,BASE+'/Materials',u.Material,u.MaterialFactoryNew())
    return m
def rotor_motion(m):
    custom=expr(m,u.MaterialExpressionCustom,600,450)
    custom.set_editor_property('description','Rigid sail rotation about world Y, 0.08 radians per second')
    custom.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3)
    inputs=[]
    for name in ['P','O','T']:
        ci=u.CustomInput();ci.set_editor_property('input_name',name);inputs.append(ci)
    custom.set_editor_property('inputs',inputs)
    custom.set_editor_property('code','float a=T*0.08; float s=sin(a),c=cos(a); float3 q=P-O; return float3(q.x*c+q.z*s-q.x,0,-q.x*s+q.z*c-q.z);')
    for cls,name,y in [(u.MaterialExpressionWorldPosition,'P',300),(u.MaterialExpressionObjectPositionWS,'O',500),(u.MaterialExpressionTime,'T',700)]:
        e=expr(m,cls,300,y);u.MaterialEditingLibrary.connect_material_expressions(e,'',custom,name)
    connect(m,custom,u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
def texture(m,asset,x=-600,y=0,normal=False):
    e=expr(m,u.MaterialExpressionTextureSample,x,y);e.set_editor_property('texture',asset)
    if not asset.get_name().startswith('T_Ground'):
        uv=expr(m,u.MaterialExpressionTextureCoordinate,x-240,y);uv.set_editor_property('coordinate_index',1)
        u.MaterialEditingLibrary.connect_material_expressions(uv,'',e,'UVs')
    if normal:e.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    elif not asset.get_editor_property('srgb'):e.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE if 'Detail' in asset.get_name() else u.MaterialSamplerType.SAMPLERTYPE_MASKS)
    return e

def run():
    imported=[]
    for folder in ['FinalMeshes']:
        for p in sorted((ROOT/'Art'/folder).glob('SM_*.fbx')):
            sm=import_file(p,BASE+'/Meshes',True)
            body=sm.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            sm.set_editor_property('light_map_resolution',64)
            imported.append({'name':sm.get_name(),'bounds':str(sm.get_bounding_box()),'uv_channels':meshes.get_num_uv_channels(sm,0),'materials':[str(s.material_slot_name) for s in sm.get_editor_property('static_materials')]})
            u.EditorAssetLibrary.save_loaded_asset(sm)
    textures={}
    for folder in ['Textures','Landscape']:
        for p in sorted((ROOT/'Art'/folder).glob('T_*.png')):
            t=import_file(p,BASE+'/Textures');textures[p.stem]=t
            if 'Roughness' in p.stem or 'Detail' in p.stem:
                t.set_editor_property('srgb',False);t.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS)
            if 'Normal' in p.stem:
                t.set_editor_property('srgb',False);t.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP)
            u.EditorAssetLibrary.save_loaded_asset(t)
    mats={}
    for key in ['Wood','WoodLight','Stone','Plaster','Roof','Iron','Canvas','Glass','Hay','Leaf','Soil','Ground']:
        m=new_material('M_'+key);assert m
        if key in ['Leaf','Hay','Canvas']:m.set_editor_property('two_sided',True)
        tex=textures['T_'+key+'_BaseColor'];sample=texture(m,tex)
        if key=='Ground':
            detail=texture(m,textures['T_Ground_Detail'],-650,240);detail.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_MASKS)
            uv=expr(m,u.MaterialExpressionTextureCoordinate,-950,260);uv.set_editor_property('u_tiling',100);uv.set_editor_property('v_tiling',100)
            u.MaterialEditingLibrary.connect_material_expressions(uv,'',detail,'UVs')
            factor=expr(m,u.MaterialExpressionMultiply,-350,220);u.MaterialEditingLibrary.connect_material_expressions(detail,'R',factor,'A');factor.set_editor_property('const_b',.22)
            add=expr(m,u.MaterialExpressionAdd,-160,180);u.MaterialEditingLibrary.connect_material_expressions(factor,'',add,'A');add.set_editor_property('const_b',.90)
            mult=expr(m,u.MaterialExpressionMultiply,50,0);u.MaterialEditingLibrary.connect_material_expressions(sample,'RGB',mult,'A');u.MaterialEditingLibrary.connect_material_expressions(add,'',mult,'B');connect(m,mult,u.MaterialProperty.MP_BASE_COLOR)
        else:connect(m,sample,u.MaterialProperty.MP_BASE_COLOR)
        rough=textures.get('T_'+key+'_Roughness')
        if rough:
            e=texture(m,rough,-500,450);u.MaterialEditingLibrary.connect_material_property(e,'R',u.MaterialProperty.MP_ROUGHNESS)
        else:connect(m,constant(m,.30 if key=='Glass' else .88),u.MaterialProperty.MP_ROUGHNESS)
        normal=textures.get('T_'+key+'_Normal')
        if normal:connect(m,texture(m,normal,-700,650,True),u.MaterialProperty.MP_NORMAL)
        connect(m,constant(m,.6 if key=='Iron' else 0,-400,750),u.MaterialProperty.MP_METALLIC)
        connect(m,constant(m,.22,-400,850),u.MaterialProperty.MP_SPECULAR)
        u.MaterialEditingLibrary.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m);mats[key]=m
    for row in imported:
        sm=u.load_asset(BASE+'/Meshes/'+row['name'])
        for i,s in enumerate(sm.get_editor_property('static_materials')):
            key=str(s.material_slot_name).split('.')[0]
            assert key in mats,(sm.get_name(),key)
            sm.set_material(i,mats[key])
        u.EditorAssetLibrary.save_loaded_asset(sm)
    # Calm neutral unlit sky; no authored clouds or external environment dependencies.
    # Rotor-only duplicates add reversible rigid vertex animation. Tower materials remain stationary.
    rotor=u.load_asset(BASE+'/Meshes/SM_MillRotor')
    for i,s in enumerate(rotor.get_editor_property('static_materials')):
        key=str(s.material_slot_name).split('.')[0];dest=BASE+'/Materials/M_Rotor_'+key
        m=u.load_asset(dest)
        if not m:m=u.EditorAssetLibrary.duplicate_asset(BASE+'/Materials/M_'+key,dest)
        rotor_motion(m);u.MaterialEditingLibrary.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m);rotor.set_material(i,m)
    u.EditorAssetLibrary.save_loaded_asset(rotor)
    sky=new_material('M_Sky');sky.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);sky.set_editor_property('two_sided',True)
    e=expr(sky,u.MaterialExpressionConstant3Vector,0,0);e.set_editor_property('constant',u.LinearColor(.36,.48,.56,1));connect(sky,e,u.MaterialProperty.MP_EMISSIVE_COLOR)
    u.MaterialEditingLibrary.recompile_material(sky);u.EditorAssetLibrary.save_loaded_asset(sky)
    save_json('import_manifest.json',{'utc':utc(),'meshes':imported,'textures':list(textures),'materials':list(mats)})
    u.log('WINDFARM_IMPORT_COMPLETE')

if __name__=='__main__':
    try:run()
    except Exception as e:fail(e,'import');raise
