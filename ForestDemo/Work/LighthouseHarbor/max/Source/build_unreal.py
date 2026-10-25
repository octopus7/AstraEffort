"""Private UE5.7 build. No shared project is opened by this script."""
import unreal as u, json, math, time, traceback
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/LighthouseHarbor/max')
ART=ROOT/'SourceArt'; VALID=ROOT/'Validation';VALID.mkdir(exist_ok=True)
BASE='/Game/LighthouseHarbor/max'; MAP='/Game/Maps/LighthouseHarbor_max'
AT=u.AssetToolsHelpers.get_asset_tools(); EL=u.EditorAssetLibrary; ML=u.MaterialEditingLibrary
LES=u.get_editor_subsystem(u.LevelEditorSubsystem); AES=u.get_editor_subsystem(u.EditorActorSubsystem)
started=datetime.now(timezone.utc).isoformat()
def log(s):u.log('HARBOR: '+str(s))
def save_json(n,d):(VALID/n).write_text(json.dumps(d,indent=2,default=str),encoding='utf-8')
def expr(m,cls,x=0,y=0):return ML.create_material_expression(m,cls,x,y)
def scalar(m,val,x=-300,y=0):
    n=expr(m,u.MaterialExpressionConstant,x,y);n.set_editor_property('r',val);return n
def vec(m,vals,x=-300,y=0):
    n=expr(m,u.MaterialExpressionConstant3Vector,x,y);n.set_editor_property('constant',u.LinearColor(*vals,1));return n
def conn(a,out,b,p):assert ML.connect_material_expressions(a,out,b,p)
def prop(n,out,m,p):assert ML.connect_material_property(n,out,p)
def custom(m,code,inputs,typ=u.CustomMaterialOutputType.CMOT_FLOAT3):
    n=expr(m,u.MaterialExpressionCustom,0,0);n.set_editor_property('code',code);n.set_editor_property('output_type',typ)
    custom_inputs=[]
    for k in inputs:
        ci=u.CustomInput();ci.set_editor_property('input_name',k);custom_inputs.append(ci)
    n.set_editor_property('inputs',custom_inputs)
    for k,node in inputs.items():conn(node,'',n,k)
    return n
def newmat(name):
    path=BASE+'/Materials/'+name
    if EL.does_asset_exist(path):return u.load_asset(path)
    return AT.create_asset(name,BASE+'/Materials',u.Material,u.MaterialFactoryNew())
def build():
    assert (ART/'harbor.blend').exists()
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    if EL.does_asset_exist(MAP):
        assert LES.load_level(MAP)
        for previous in AES.get_all_level_actors():
            if previous.get_class().get_name() not in ['WorldSettings','Brush','DefaultPhysicsVolume']:
                AES.destroy_actor(previous)
    else:assert LES.new_level(MAP,False)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    ws=world.get_world_settings();ws.set_editor_property('force_no_precomputed_lighting',True)
    palette=json.loads((ART/'palette.json').read_text()); manifests=json.loads((ART/'mesh_manifest.json').read_text())
    mats={};textures={};imports=[]
    # Explicit factories keep texture creation in a full Slate editor session.
    for name,rec in palette.items():
        task=u.AssetImportTask();task.filename=rec['image'];task.destination_path=BASE+'/Textures';task.destination_name='T_'+name
        task.automated=True;task.save=True;task.replace_existing=True;task.factory=u.TextureFactory()
        existing=BASE+'/Textures/T_'+name
        if EL.does_asset_exist(existing):paths=[existing]
        else:AT.import_asset_tasks([task]);paths=list(task.imported_object_paths)
        assert paths, 'Texture failed '+name
        tex=u.load_asset(paths[0]);textures[name]=tex
        mat=newmat('M_'+name);ML.delete_all_material_expressions(mat)
        sample=expr(mat,u.MaterialExpressionTextureSample,-500,0);sample.texture=tex
        prop(sample,'RGB',mat,u.MaterialProperty.MP_BASE_COLOR)
        prop(scalar(mat,rec['roughness']), '',mat,u.MaterialProperty.MP_ROUGHNESS)
        prop(scalar(mat,.15 if name in ['Iron','Copper'] else 0), '',mat,u.MaterialProperty.MP_METALLIC)
        if name=='Lamp':
            mult=expr(mat,u.MaterialExpressionMultiply);conn(sample,'RGB',mult,'A');conn(scalar(mat,2.6),'',mult,'B');prop(mult,'',mat,u.MaterialProperty.MP_EMISSIVE_COLOR)
        if name in ['RoofClay','RoofLight']:mat.set_editor_property('two_sided',True)
        ML.recompile_material(mat);EL.save_loaded_asset(mat);mats[name]=mat
    # Animated opaque stylized seawater: two analytic swell fields and matching normal disturbance.
    water=mats['Water'];ML.delete_all_material_expressions(water)
    P=expr(water,u.MaterialExpressionWorldPosition,-700,0);T=expr(water,u.MaterialExpressionTime,-700,200)
    wpo=custom(water,'float a=P.x*0.003+P.y*0.0018+T*0.8; float b=P.y*0.004-P.x*0.001-T*0.55; return float3(0,0,3.2*sin(a)+1.5*sin(b));',{'P':P,'T':T})
    prop(wpo,'',water,u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    color=custom(water,'float s=0.5+0.5*sin(P.x*0.0024+P.y*0.004+T*0.55); float f=pow(saturate(s),18)*0.16; return lerp(float3(0.025,0.19,0.22),float3(0.075,0.34,0.35),s*.35)+float3(f*.4,f*.7,f*.65);',{'P':P,'T':T})
    prop(color,'',water,u.MaterialProperty.MP_BASE_COLOR)
    norm=custom(water,'float a=P.x*0.009+P.y*0.004+T*0.8; float b=P.y*0.012-P.x*0.003-T*.55;return normalize(float3(-.13*cos(a),-.12*cos(b),1));',{'P':P,'T':T})
    prop(norm,'',water,u.MaterialProperty.MP_NORMAL);prop(scalar(water,.28),'',water,u.MaterialProperty.MP_ROUGHNESS)
    prop(scalar(water,.45),'',water,u.MaterialProperty.MP_SPECULAR);ML.recompile_material(water);EL.save_loaded_asset(water)
    for name in ['Foam']:
        fm=mats[name];fp=expr(fm,u.MaterialExpressionWorldPosition);ft=expr(fm,u.MaterialExpressionTime)
        move=custom(fm,'return float3(2*sin(T*.6+P.y*.004),1.2*cos(T*.5+P.x*.003),2*sin(T*.8+P.x*.003+P.y*.0018));',{'P':fp,'T':ft})
        prop(move,'',fm,u.MaterialProperty.MP_WORLD_POSITION_OFFSET);ML.recompile_material(fm);EL.save_loaded_asset(fm)
    # FBX export coordinate/unit contract checked against actual UE imported bounds.
    meshes={};bounds=[]
    for rec in manifests['meshes']:
        name=rec['name'];task=u.AssetImportTask();task.filename=str(ART/'FBX'/(name+'.fbx'));task.destination_path=BASE+'/Meshes';task.destination_name='SM_'+name
        task.automated=True;task.save=True;task.replace_existing=True
        opt=u.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False
        opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
        opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.generate_lightmap_u_vs=False
        opt.static_mesh_import_data.auto_generate_collision=False
        opt.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
        opt.static_mesh_import_data.convert_scene=True;opt.static_mesh_import_data.convert_scene_unit=True
        task.options=opt
        existing=BASE+'/Meshes/SM_'+name
        if EL.does_asset_exist(existing) and name not in manifests.get('polish_changes',[]):paths=[existing]
        else:AT.import_asset_tasks([task]);paths=list(task.imported_object_paths)
        assert paths,'Mesh failed '+name
        sm=u.load_asset(paths[0]);meshes[name]=sm
        box=sm.get_bounding_box(); mn=[box.min.x,box.min.y,box.min.z];mx=[box.max.x,box.max.y,box.max.z]
        bounds.append({'name':name,'source_bounds_m':rec['bounds_m'],'imported_bounds_cm':[mn,mx]})
        for i,slot in enumerate(sm.get_editor_property('static_materials')):
            slotname=str(slot.material_slot_name)
            match=slotname if slotname in mats else next((k for k in mats if slotname.startswith(k)),None)
            if name=='Beacon_Beam':continue
            assert match, f'Unmapped material {name}:{slotname}'
            sm.set_material(i,mats[match])
        EL.save_loaded_asset(sm)
        log('Imported '+name)
    # Read exact geometric centers to identify the importer handedness, without assumptions.
    lookup={b['name']:b for b in bounds}
    waterb=lookup['Water_Surface'];ext=[waterb['imported_bounds_cm'][1][i]-waterb['imported_bounds_cm'][0][i] for i in range(3)]
    assert abs(ext[0]-10000)<2 and abs(ext[1]-10000)<2, 'FBX unit conversion not centimetres'
    def center(b,k):return [(b[k][0][i]+b[k][1][i])/2 for i in range(3)]
    src=center(lookup['Lighthouse_Optic'],'source_bounds_m');got=center(lookup['Lighthouse_Optic'],'imported_bounds_cm')
    # Standard Blender -Y/+Z exports are imported with Y reflected; preserve coherent source coordinates by actor reflection.
    sx=round(got[0]/(src[0]*100));sy=round(got[1]/(src[1]*100));assert sx in [-1,1] and sy in [-1,1],f'Unexpected FBX axes {src}/{got}'
    for b in bounds:
        sc=center(b,'source_bounds_m');ic=center(b,'imported_bounds_cm')
        assert max(abs(ic[i]-sc[i]*100*[sx,sy,1][i]) for i in range(3))<2, 'FBX axis mismatch '+b['name']
        b['actor_scale_correction']=[sx,sy,.85]
    save_json('import_bounds.json',{'pass':True,'x_sign':sx,'y_sign':sy,'scale_cm_per_m':100,'meshes':bounds})
    # Shader rotates source beam around the actual placed lighthouse center. This persists in the material asset.
    bm=newmat('M_Beacon');ML.delete_all_material_expressions(bm)
    bm.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT);bm.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);bm.set_editor_property('two_sided',True)
    bp=expr(bm,u.MaterialExpressionWorldPosition,-700,0);bt=expr(bm,u.MaterialExpressionTime,-700,180);uv=expr(bm,u.MaterialExpressionTextureCoordinate,-700,360)
    pivot=(-2200,1900,4550)
    bw=custom(bm,'float2 p=P.xy-float2(-2200,1900); float a=T*0.20943951; float2 q=float2(p.x*cos(a)-p.y*sin(a),p.x*sin(a)+p.y*cos(a));return float3(q-p,0);',{'P':bp,'T':bt})
    prop(bw,'',bm,u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    prop(vec(bm,(1.0,.66,.22)),'',bm,u.MaterialProperty.MP_EMISSIVE_COLOR)
    alpha=custom(bm,'return pow(saturate(1-UV.x),1.5)*0.22;',{'UV':uv},u.CustomMaterialOutputType.CMOT_FLOAT1)
    prop(alpha,'',bm,u.MaterialProperty.MP_OPACITY);ML.recompile_material(bm);EL.save_loaded_asset(bm)
    meshes['Beacon_Beam'].set_material(0,bm);EL.save_loaded_asset(meshes['Beacon_Beam']);mats['Beacon']=bm
    actors=[]
    for name,sm in meshes.items():
        a=AES.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));a.set_actor_label(name);a.set_actor_scale3d(u.Vector(sx,sy,.85))
        comp=a.static_mesh_component;comp.set_static_mesh(sm);comp.set_mobility(u.ComponentMobility.STATIC)
        comp.set_editor_property('cast_shadow',name not in ['Beacon_Beam','Water_Surface','Sea_Ripples','Shore_Foam','Boat_Wake'])
        if name=='Beacon_Beam':comp.set_editor_property('bounds_scale',5.0)
        if name in ['Water_Surface','Sea_Ripples','Shore_Foam','Boat_Wake']:comp.set_editor_property('bounds_scale',1.15)
        actors.append(a)
    # Entirely movable sky/sun; no baked lighting or map-adjacent BuiltData.
    sun=AES.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,10000),u.Rotator(pitch=-48,yaw=135,roll=0));sun.set_actor_label('Warm afternoon sun')
    sc=sun.light_component;sc.set_mobility(u.ComponentMobility.MOVABLE);sc.set_editor_property('intensity',5.0)
    sc.set_editor_property('light_color',u.Color(255,230,193));sc.set_editor_property('light_source_angle',3.2)
    sc.set_editor_property('atmosphere_sun_light',True)
    sky=AES.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,7000));sky.set_actor_label('Open coastal skylight')
    sk=sky.light_component;sk.set_mobility(u.ComponentMobility.MOVABLE);sk.set_editor_property('real_time_capture',True);sk.set_editor_property('intensity',1.8)
    AES.spawn_actor_from_class(u.SkyAtmosphere,u.Vector(0,0,0))
    # Restrained ambient fill preserves form under the cliff in close views.
    fill=AES.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,8000),u.Rotator(pitch=-60,yaw=-45,roll=0));fill.set_actor_label('Soft sky fill')
    fc=fill.light_component;fc.set_mobility(u.ComponentMobility.MOVABLE);fc.set_editor_property('intensity',1.8);fc.set_editor_property('light_color',u.Color(181,219,235));fc.set_editor_property('cast_shadows',False)
    backdrop=newmat('M_SkyBackdrop');ML.delete_all_material_expressions(backdrop)
    backdrop.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);backdrop.set_editor_property('two_sided',True)
    backdrop.set_editor_property('is_sky',True);prop(vec(backdrop,(.13,.22,.27)),'',backdrop,u.MaterialProperty.MP_EMISSIVE_COLOR)
    ML.recompile_material(backdrop);EL.save_loaded_asset(backdrop)
    sky_shell=AES.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));sky_shell.set_actor_label('Atmospheric_Backdrop')
    sky_shell.set_actor_scale3d(u.Vector(10000,10000,10000));sky_shell.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Sphere.Sphere'))
    sky_shell.static_mesh_component.set_material(0,backdrop);sky_shell.static_mesh_component.set_editor_property('cast_shadow',False)
    pp=AES.spawn_actor_from_class(u.PostProcessVolume,u.Vector());pp.set_actor_label('Coastal color grade');pp.set_editor_property('unbound',True)
    settings=pp.get_editor_property('settings')
    for k,v in {'override_auto_exposure_method':True,'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,
      'override_auto_exposure_bias':True,'auto_exposure_bias':0.0,'override_motion_blur_amount':True,'motion_blur_amount':0.0,
      'override_bloom_intensity':True,'bloom_intensity':.18,'override_vignette_intensity':True,'vignette_intensity':.12}.items():settings.set_editor_property(k,v)
    settings.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True)
    settings.set_editor_property('auto_exposure_apply_physical_camera_exposure',False)
    pp.set_editor_property('settings',settings)
    cameras={}
    specs=[('overview',(12000,-12000,16000),(0,0,0),20000),('top_down',(0,0,20000),(0,0,0),20000),
      ('lighthouse',(2800,-5400,6000),(-2100,1700,2550),9000),('harbor',(6800,-7800,4000),(1400,-1500,380),8500),
      ('motion',(4800,-6200,6400),(-500,300,1870),13500)]
    for name,loc,target,width in specs:
        rot=u.Rotator(pitch=-90,yaw=0,roll=0) if name=='top_down' else u.MathLibrary.find_look_at_rotation(u.Vector(*loc),u.Vector(*target))
        a=AES.spawn_actor_from_class(u.CameraActor,u.Vector(*loc),rot);a.set_actor_label('CAPTURE_'+name)
        cc=a.get_component_by_class(u.CameraComponent);cc.set_editor_property('projection_mode',u.CameraProjectionMode.ORTHOGRAPHIC);cc.set_editor_property('ortho_width',width)
        cc.set_editor_property('aspect_ratio',1920/1080);cc.set_editor_property('constrain_aspect_ratio',True)
        cc.set_editor_property('auto_calculate_ortho_planes',True)
        cameras[name]=a
    player=AES.spawn_actor_from_class(u.PlayerStart,u.Vector(1500,-1200,380),u.Rotator(pitch=0,yaw=90,roll=0));player.set_actor_label('Harbor viewpoint start')
    AES.set_selected_level_actors([])
    assert LES.save_current_level();EL.save_directory(BASE,False,True)
    save_json('build_summary.json',{'started_at_utc':started,'saved_at_utc':datetime.now(timezone.utc).isoformat(),
      'map':MAP,'meshes':len(meshes),'textures':len(textures),'materials':len(mats)+1,'actor_count':len(AES.get_all_level_actors()),'source_axes_correction':[sx,sy,.85],
      'placed_beacon_pivot_cm':[-2200,1900,3867.5],'site_footprint_cm':[10000,10000],
      'sun_rotation_actual':str(sun.get_actor_rotation()),'fill_rotation_actual':str(fill.get_actor_rotation()),
      'effects':{'water':'opaque analytic WPO/normal/color shader, no physical refraction','beacon':'12 degrees/sec WPO translucent emissive cone; no dynamic spotlight','foam':'authored rounded lines with sine WPO'}})
    log('BUILD_SAVED')
    u.SystemLibrary.quit_editor()
try:build()
except Exception:
    error=traceback.format_exc();log(error);save_json('build_error.json',{'utc':datetime.now(timezone.utc).isoformat(),'error':error});u.SystemLibrary.quit_editor()
