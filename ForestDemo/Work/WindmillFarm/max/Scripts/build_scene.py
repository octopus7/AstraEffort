import unreal, json, math, traceback
from pathlib import Path
from datetime import datetime, timezone

WORK=Path(r'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/max')
ROOT='/Game/WindmillFarm/max'
MAP='/Game/Maps/WindmillFarm_max'
SOURCE=json.loads((WORK/'Source/scene_manifest.json').read_text(encoding='utf-8'))
ASSETS=unreal.AssetToolsHelpers.get_asset_tools()
EDIT=unreal.MaterialEditingLibrary
EAL=unreal.EditorAssetLibrary
LEVEL=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
WARN=[]

def optional(obj,name,value):
    try:obj.set_editor_property(name,value)
    except Exception as e:WARN.append(str(obj.get_name())+'.'+name+': '+str(e))

def write(name,data):
    (WORK/'Evidence'/name).write_text(json.dumps(data,indent=2),encoding='utf-8')

def srgb(hexcolor):
    vals=[int(hexcolor[i:i+2],16)/255 for i in (1,3,5)]
    return [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals]

def expr(mat,cls,**props):
    e=EDIT.create_material_expression(mat,cls)
    for k,v in props.items():e.set_editor_property(k,v)
    return e

def custom_inputs(*names):
    result=[]
    for name in names:
        value=unreal.CustomInput()
        value.set_editor_property('input_name',name)
        result.append(value)
    return result

def connect(a,out,b,inp):
    if not EDIT.connect_material_expressions(a,out,b,inp):raise RuntimeError('Material connection failed: '+inp)

def output(a,out,mat,prop):
    if not EDIT.connect_material_property(a,out,prop):raise RuntimeError('Material output connection failed')

def make_material(name,palette,textures,pivot):
    path=ROOT+'/Materials/M_'+name
    mat=EAL.load_asset(path) if EAL.does_asset_exist(path) else ASSETS.create_asset('M_'+name,ROOT+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
    EDIT.delete_all_material_expressions(mat)
    mat.set_editor_property('two_sided',True)
    rgb=srgb(palette['srgb_hex'])
    color=expr(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(*rgb,1))
    if palette['texture']:
        sample=expr(mat,unreal.MaterialExpressionTextureSample,texture=textures[palette['texture']])
        subtle=expr(mat,unreal.MaterialExpressionLinearInterpolate,const_a=1.0,const_alpha=.28)
        connect(sample,'RGB',subtle,'B')
        mul=expr(mat,unreal.MaterialExpressionMultiply)
        connect(color,'',mul,'A');connect(subtle,'',mul,'B');color=mul
    output(color,'',mat,unreal.MaterialProperty.MP_BASE_COLOR)
    rough=expr(mat,unreal.MaterialExpressionConstant,r=palette['roughness'])
    output(rough,'',mat,unreal.MaterialProperty.MP_ROUGHNESS)
    if name in ['Iron','RotorIron']:
        metal=expr(mat,unreal.MaterialExpressionConstant,r=.65);output(metal,'',mat,unreal.MaterialProperty.MP_METALLIC)
    if name=='WarmGlass':
        glow=expr(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.15,.07,.018,1));output(glow,'',mat,unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    if name in ['RotorWood','RotorIron','RotorCanvas']:
        mat.set_editor_property('tangent_space_normal',False)
        pos=expr(mat,unreal.MaterialExpressionWorldPosition)
        time=expr(mat,unreal.MaterialExpressionTime)
        pivot_expr=expr(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(*pivot,1))
        offset=expr(mat,unreal.MaterialExpressionCustom,description='Continuous windmill rotation, 0.12 radians per second',
          code='float s,c; sincos(T*0.12,s,c); float3 q=P-Pivot; return float3(q.x*c+q.z*s,q.y,-q.x*s+q.z*c)-q;',
          output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,
          inputs=custom_inputs('P','T','Pivot'))
        connect(pos,'',offset,'P');connect(time,'',offset,'T');connect(pivot_expr,'',offset,'Pivot')
        output(offset,'',mat,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
        normal=expr(mat,unreal.MaterialExpressionVertexNormalWS)
        norm_rot=expr(mat,unreal.MaterialExpressionCustom,description='Rotate world-space lighting normals with the sails',
          code='float s,c; sincos(T*0.12,s,c); return normalize(float3(N.x*c+N.z*s,N.y,-N.x*s+N.z*c));',
          output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,
          inputs=custom_inputs('N','T'))
        connect(normal,'',norm_rot,'N');connect(time,'',norm_rot,'T');output(norm_rot,'',mat,unreal.MaterialProperty.MP_NORMAL)
    elif name in ['Wheat','WheatLight']:
        pos=expr(mat,unreal.MaterialExpressionWorldPosition);time=expr(mat,unreal.MaterialExpressionTime)
        sway=expr(mat,unreal.MaterialExpressionCustom,description='Small wind ripple in wheat tips',
          code='float k=saturate((P.z-25.0)/100.0); return float3(sin(T*1.4+P.x*0.008+P.y*0.004)*4.0*k,cos(T*1.1+P.x*0.006)*2.0*k,0);',
          output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,
          inputs=custom_inputs('P','T'))
        connect(pos,'',sway,'P');connect(time,'',sway,'T');output(sway,'',mat,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    EDIT.layout_material_expressions(mat);EDIT.recompile_material(mat);EAL.save_loaded_asset(mat)
    return mat

def import_texture(filename):
    t=unreal.AssetImportTask();t.filename=str(WORK/'Source/Textures'/filename);t.destination_path=ROOT+'/Textures'
    t.destination_name='T_'+Path(filename).stem;t.automated=True;t.replace_existing=True;t.save=True
    ASSETS.import_asset_tasks([t])
    obj=EAL.load_asset(ROOT+'/Textures/'+t.destination_name)
    if not obj:raise RuntimeError('Missing imported texture '+filename)
    obj.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_DEFAULT)
    obj.set_editor_property('srgb',True);EAL.save_loaded_asset(obj);return obj

def import_mesh(item,materials):
    t=unreal.AssetImportTask();t.filename=str(WORK/'Source/Models'/(item['name']+'.fbx'));t.destination_path=ROOT+'/Meshes'
    t.destination_name=item['name'];t.automated=True;t.replace_existing=True;t.save=True;t.factory=unreal.FbxFactory()
    options=unreal.FbxImportUI();options.set_editor_property('import_mesh',True)
    options.set_editor_property('import_materials',False);options.set_editor_property('import_textures',False)
    options.set_editor_property('import_as_skeletal',False);options.set_editor_property('automated_import_should_detect_type',False)
    options.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_STATIC_MESH)
    d=options.static_mesh_import_data
    for k,v in {'combine_meshes':True,'auto_generate_collision':False,'generate_lightmap_u_vs':False,'convert_scene':False,'convert_scene_unit':False,'force_front_x_axis':False,'import_uniform_scale':1.0}.items():d.set_editor_property(k,v)
    d.set_editor_property('normal_import_method',unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
    t.options=options;ASSETS.import_asset_tasks([t])
    obj=EAL.load_asset(ROOT+'/Meshes/'+item['name'])
    if not isinstance(obj,unreal.StaticMesh):raise RuntimeError('Mesh import failed '+item['name'])
    slots=obj.get_editor_property('static_materials')
    for i,slot in enumerate(slots):
        slotname=str(slot.get_editor_property('imported_material_slot_name'))
        if slotname not in materials:slotname=str(slot.get_editor_property('material_slot_name'))
        if slotname not in materials:raise RuntimeError('Unknown mesh material slot '+slotname)
        obj.set_material(i,materials[slotname])
    setup=obj.get_editor_property('body_setup')
    if setup and item['category'] not in ['Wheat'] and item['name'] not in ['SM_Wildflowers','SM_WindmillRotor']:
        setup.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    EAL.save_loaded_asset(obj)
    return obj

def spawn(cls,label,location=(0,0,0),rotation=None):
    actor=ACTORS.spawn_actor_from_class(cls,unreal.Vector(*location),rotation or unreal.Rotator())
    if not actor:raise RuntimeError('Could not spawn '+label)
    actor.set_actor_label(label);return actor

def camera(name,location,target,ortho=None):
    actor=spawn(unreal.CameraActor,'Capture_'+name,location)
    rot=unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*location),unreal.Vector(*target))
    if name=='top_down':rot=unreal.Rotator(pitch=-90,yaw=0,roll=0)
    actor.set_actor_rotation(rot,False)
    comp=actor.get_component_by_class(unreal.CameraComponent)
    comp.set_editor_property('aspect_ratio',16/9);comp.set_editor_property('constrain_aspect_ratio',True)
    comp.set_editor_property('field_of_view',70.0)
    if ortho:
        comp.set_editor_property('projection_mode',unreal.CameraProjectionMode.ORTHOGRAPHIC)
        comp.set_editor_property('ortho_width',ortho)
        optional(comp,'auto_calculate_ortho_planes',False)
        comp.set_editor_property('ortho_near_clip_plane',1.0);comp.set_editor_property('ortho_far_clip_plane',100000.0)
    return actor

def configure_presentation():
    existing={a.get_actor_label():a for a in ACTORS.get_all_level_actors()}
    for label in ['Lighting_Atmosphere','Lighting_AerialPerspective']:
        if label in existing:ACTORS.destroy_actor(existing[label])
    sun=existing['Lighting_Sun']
    sun.set_actor_rotation(unreal.Rotator(pitch=-48,yaw=135,roll=0),False)
    sun.light_component.set_intensity(7.0)
    sun.light_component.set_editor_property('light_source_angle',6.0)
    sky=existing['Lighting_Sky'].light_component
    sky.set_editor_property('real_time_capture',False)
    sky.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sky.set_editor_property('cubemap',EAL.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'))
    sky.set_intensity(1.0)
    optional(sky,'lower_hemisphere_is_black',False)
    mat=EAL.load_asset(ROOT+'/Materials/M_SkyBackdrop')
    if not mat:mat=ASSETS.create_asset('M_SkyBackdrop',ROOT+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
    EDIT.delete_all_material_expressions(mat)
    mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('two_sided',True)
    optional(mat,'is_sky',True)
    color=expr(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.34,.43,.42,1))
    output(color,'',mat,unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    EDIT.recompile_material(mat);EAL.save_loaded_asset(mat)
    backdrop=existing.get('Presentation_SkyBackdrop') or spawn(unreal.StaticMeshActor,'Presentation_SkyBackdrop')
    backdrop.static_mesh_component.set_static_mesh(EAL.load_asset('/Engine/BasicShapes/Sphere'))
    backdrop.static_mesh_component.set_material(0,mat)
    backdrop.static_mesh_component.set_editor_property('cast_shadow',False)
    backdrop.static_mesh_component.set_editor_property('affect_distance_field_lighting',False)
    backdrop.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    backdrop.set_actor_scale3d(unreal.Vector(1000,1000,1000))
    backdrop.tags=[unreal.Name('PresentationEnvironment')]
    cam=existing['Capture_windmill']
    cam.set_actor_location(unreal.Vector(-650,-1750,1250),False,False)
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam.get_actor_location(),unreal.Vector(-2300,1700,850)),False)

try:
    for folder in ['Materials','Textures','Meshes']:EAL.make_directory(ROOT+'/'+folder)
    EAL.make_directory('/Game/Maps')
    unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    textures={name:import_texture(name) for name in SOURCE['textures']}
    pivot=[x*100 for x in SOURCE['rotor_pivot_m']]
    materials={name:make_material(name,p,textures,pivot) for name,p in SOURCE['palette'].items()}
    meshes={item['name']:import_mesh(item,materials) for item in SOURCE['meshes']}
    if not LEVEL.new_level(MAP):raise RuntimeError('Could not create private level')
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    world.get_world_settings().set_editor_property('force_no_precomputed_lighting',True)
    actors=[];bounds=[]
    for item in SOURCE['meshes']:
        loc=pivot if item['category']=='WindmillRotor' else (0,0,0)
        a=spawn(unreal.StaticMeshActor,item['name'].replace('SM_','Farm_'),loc)
        a.tags=[unreal.Name('WindmillFarm_max'),unreal.Name(item['category'])]
        comp=a.static_mesh_component;comp.set_static_mesh(meshes[item['name']])
        # FBX importer changes Blender right-handed Y to UE left-handed -Y even with scene conversion disabled.
        # Mirror the actor back so the authored farm front and common camera convention stay consistent.
        a.set_actor_scale3d(unreal.Vector(1,-1,1))
        comp.set_mobility(unreal.ComponentMobility.MOVABLE if item['category']=='WindmillRotor' else unreal.ComponentMobility.STATIC)
        if item['category']=='WindmillRotor':
            comp.set_editor_property('bounds_scale',1.8);comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        if item['category']=='Wheat' or item['name']=='SM_Wildflowers':comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        center,extent=a.get_actor_bounds(False)
        bounds.append({'name':item['name'],'center_cm':[center.x,center.y,center.z],'extent_cm':[extent.x,extent.y,extent.z]})
        actors.append(a)
    # Dynamic daylight with a fixed exposure. The sky is genuine UE atmosphere.
    sun=spawn(unreal.DirectionalLight,'Lighting_Sun',(0,0,10000),unreal.Rotator(pitch=-42,yaw=-42,roll=0))
    sun.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sun.light_component.set_intensity(7.0)
    sun.light_component.set_light_color(unreal.LinearColor(1.0,.89,.72,1))
    optional(sun.light_component,'atmosphere_sun_light',True);optional(sun.light_component,'light_source_angle',3.0)
    spawn(unreal.SkyAtmosphere,'Lighting_Atmosphere')
    sky=spawn(unreal.SkyLight,'Lighting_Sky',(0,0,300))
    sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);sky.light_component.set_intensity(1.1)
    optional(sky.light_component,'real_time_capture',True)
    optional(sky.light_component,'lower_hemisphere_is_solid_color',False)
    fog=spawn(unreal.ExponentialHeightFog,'Lighting_AerialPerspective',(0,0,-1000))
    fogcomp=fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    optional(fogcomp,'fog_density',.002);optional(fogcomp,'fog_height_falloff',.2)
    pp=spawn(unreal.PostProcessVolume,'Lighting_FixedExposure')
    pp.set_editor_property('unbound',True)
    settings=pp.get_editor_property('settings')
    for k,v in {'override_auto_exposure_method':True,'auto_exposure_method':unreal.AutoExposureMethod.AEM_HISTOGRAM,
        'override_auto_exposure_min_brightness':True,'auto_exposure_min_brightness':1.0,
        'override_auto_exposure_max_brightness':True,'auto_exposure_max_brightness':1.0,
        'override_auto_exposure_bias':True,'auto_exposure_bias':0.0,
        'override_motion_blur_amount':True,'motion_blur_amount':0.0,
        'override_bloom_intensity':True,'bloom_intensity':.15,
        'override_vignette_intensity':True,'vignette_intensity':.12}.items():settings.set_editor_property(k,v)
    pp.set_editor_property('settings',settings)
    camera('overview',(12000,-12000,16000),(0,0,0),20000)
    camera('top_down',(0,0,20000),(0,0,0),20000)
    camera('windmill',(-650,-1750,420),(-2300,1700,850))
    camera('farm',(650,-1500,500),(2550,1100,230))
    configure_presentation()
    start=spawn(unreal.PlayerStart,'Farm_Entry',(0,-4400,220),unreal.Rotator(pitch=0,yaw=90,roll=0))
    ACTORS.set_selected_level_actors([])
    if not LEVEL.save_current_level():raise RuntimeError('Level save failed')
    EAL.save_directory(ROOT,only_if_is_dirty=False,recursive=True)
    write('build_scene.json',{'passed':True,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'map':MAP,'actors':len(ACTORS.get_all_level_actors()),'bounds':bounds,'warnings':WARN,
          'rotor':{'pivot_cm':pivot,'axis':[0,1,0],'radians_per_second':.12,'implementation':'Time-driven world position offset plus rotated world-space normals; non-colliding rotor'},'material_count':len(materials),'mesh_count':len(meshes),'texture_count':len(textures)})
    unreal.log('WINDMILL_BUILD_COMPLETE')
except Exception:
    write('build_scene_error.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'traceback':traceback.format_exc(),'warnings':WARN})
    unreal.log_error(traceback.format_exc())
    raise
