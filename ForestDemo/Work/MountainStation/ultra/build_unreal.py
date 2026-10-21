import unreal as u, json, os, math, traceback, datetime
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
ASSET='/Game/MountainStation/ultra'
MAP='/Game/Maps/MountainStation_ultra'
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(name,data):
    with open(ROOT+'/'+name,'w') as f:json.dump(data,f,indent=2)
def vec(v):return [v.x,v.y,v.z]
def srgb(h):
    a=[int(h[i:i+2],16)/255 for i in (1,3,5)];return [v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in a]
def prop(obj,k,v):obj.set_editor_property(k,v)
def main():
    data=json.load(open(ROOT+'/art_manifest.json'));tools=u.AssetToolsHelpers.get_asset_tools();editor=u.get_editor_subsystem(u.EditorActorSubsystem)
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    u.EditorAssetLibrary.make_directory(ASSET+'/Meshes');u.EditorAssetLibrary.make_directory(ASSET+'/Materials')
    materials={}
    for n,(hexcolor,rough) in data['palette'].items():
        if u.EditorAssetLibrary.does_asset_exist(ASSET+'/Materials/M_'+n):
            materials[n]=u.load_asset(ASSET+'/Materials/M_'+n)
            continue
        m=u.load_asset(ASSET+'/Materials/M_'+n) if u.EditorAssetLibrary.does_asset_exist(ASSET+'/Materials/M_'+n) else tools.create_asset('M_'+n,ASSET+'/Materials',u.Material,u.MaterialFactoryNew())
        u.MaterialEditingLibrary.delete_all_material_expressions(m)
        c=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant3Vector,-300,0)
        prop(c,'constant',u.LinearColor(*srgb(hexcolor),1));u.MaterialEditingLibrary.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
        r=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant,-300,130);prop(r,'r',rough);u.MaterialEditingLibrary.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS)
        prop(m,'two_sided',True)
        if n=='Lamp':u.MaterialEditingLibrary.connect_material_property(c,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
        u.MaterialEditingLibrary.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m);materials[n]=m
    tasks=[]
    for entry in data['meshes']:
        task=u.AssetImportTask();task.filename=entry['file'];task.destination_path=ASSET+'/Meshes';task.destination_name=entry['name'];task.automated=True;task.replace_existing=True;task.save=True
        options=u.FbxImportUI();options.import_mesh=True;options.import_materials=False;options.import_textures=False;options.import_as_skeletal=False;options.automated_import_should_detect_type=False;options.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
        imp=options.static_mesh_import_data;imp.combine_meshes=True;imp.auto_generate_collision=False;imp.generate_lightmap_u_vs=False;imp.convert_scene=False;imp.convert_scene_unit=True;imp.force_front_x_axis=False
        imp.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
        task.options=options;task.factory=u.FbxFactory();tasks.append(task)
    tools.import_asset_tasks([t for t in tasks if t.destination_name in {'SM_Terrain','SM_AccessRamp','SM_Railings'} or not u.EditorAssetLibrary.does_asset_exist(t.destination_path+'/'+t.destination_name)])
    if u.EditorAssetLibrary.does_asset_exist(MAP):
        assert levels.load_level(MAP),'load existing private level failed'
        for old in editor.get_all_level_actors():
            if not isinstance(old,(u.WorldSettings,u.Brush,u.LevelScriptActor)):editor.destroy_actor(old)
    else:assert levels.new_level(MAP,False),'new_level failed'
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    settings=world.get_world_settings();prop(settings,'force_no_precomputed_lighting',True)
    imported=[];actor_map={}
    no_collision={'RailFasteners','RoofSeams','Lettering','StationCladding','StationGlass','Clock','MeadowDetails','Shrubs','Conifers','OutcropMoss','TunnelRibs'}
    for entry,task in zip(data['meshes'],tasks):
        paths=list(task.imported_object_paths);meshes=[u.load_asset(p) for p in paths];meshes=[m for m in meshes if isinstance(m,u.StaticMesh)]
        if not meshes:meshes=[u.load_asset(ASSET+'/Meshes/'+entry['name'])]
        assert meshes and meshes[0],entry['name']+' missing'
        sm=meshes[0];slots=sm.get_editor_property('static_materials');slot_names=[]
        for i,s in enumerate(slots):
            name=str(s.material_slot_name).split('.')[0];slot_names.append(name)
            if name not in materials:raise RuntimeError('Unknown material '+name+' on '+entry['name'])
            sm.set_material(i,materials[name])
        bs=sm.get_editor_property('body_setup');bs.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        actor=editor.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));actor.set_actor_label(entry['name'][3:]);actor.static_mesh_component.set_static_mesh(sm)
        actor.static_mesh_component.set_mobility(u.ComponentMobility.STATIC)
        actor.static_mesh_component.set_collision_profile_name('BlockAll')
        if entry['name'][3:] in no_collision:
            actor.static_mesh_component.set_collision_profile_name('NoCollision')
            actor.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        actor_map[entry['name']]=actor
        origin,extent=actor.get_actor_bounds(False)
        imported.append({'name':entry['name'],'path':sm.get_path_name(),'origin':vec(origin),'extent':vec(extent),'slots':slot_names,'collision':entry['name'][3:] not in no_collision})
        u.EditorAssetLibrary.save_loaded_asset(sm)
    # FBX's handedness conversion flips Y. Detect it from the asymmetric station.
    sy=actor_map['SM_StationWalls'].get_actor_bounds(False)[0].y
    y_sign=-1 if sy<0 else 1
    for actor in actor_map.values():actor.set_actor_scale3d(u.Vector(1,y_sign,1))
    terrain=actor_map['SM_Terrain'];origin,extent=terrain.get_actor_bounds(False)
    assert abs(extent.x-5000)<2 and abs(extent.y-5000)<2,('Invalid centimetre scale',vec(extent))
    # Warm afternoon directional light, broad blue-gray sky fill, no baked data.
    sun=editor.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,6000),u.Rotator(pitch=-50,yaw=135,roll=0));sun.set_actor_label('Afternoon sun')
    light=sun.light_component;light.set_mobility(u.ComponentMobility.MOVABLE);light.set_intensity(4.8);light.set_light_color(u.LinearColor(1,.89,.73,1));prop(light,'light_source_angle',3.0)
    prop(light,'dynamic_shadow_distance_movable_light',50000);prop(light,'dynamic_shadow_cascades',4)
    sky=editor.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,3000));sky.set_actor_label('Soft alpine skylight');sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    prop(sky.light_component,'source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    cube=u.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap')
    if cube:prop(sky.light_component,'cubemap',cube)
    sky.light_component.set_intensity(2.5)
    sky.light_component.set_light_color(u.LinearColor(.78,.87,1,1))
    for label,rot,intensity,color in [('Soft front fill',u.Rotator(pitch=-35,yaw=135,roll=0),1.8,u.LinearColor(.86,.93,1,1)),('Soft ridge fill',u.Rotator(pitch=-45,yaw=-35,roll=0),1.1,u.LinearColor(.88,.94,1,1))]:
        a=editor.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,5000),rot);a.set_actor_label(label);c=a.light_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_intensity(intensity);c.set_light_color(color);prop(c,'cast_shadows',False)
    # Neutral studio-like sky enclosure, authored material; the sphere is Engine-only.
    bg=u.load_asset(ASSET+'/Materials/M_SkyBackdrop') if u.EditorAssetLibrary.does_asset_exist(ASSET+'/Materials/M_SkyBackdrop') else tools.create_asset('M_SkyBackdrop',ASSET+'/Materials',u.Material,u.MaterialFactoryNew())
    prop(bg,'two_sided',True);prop(bg,'shading_model',u.MaterialShadingModel.MSM_UNLIT)
    c=u.MaterialEditingLibrary.create_material_expression(bg,u.MaterialExpressionConstant3Vector);prop(c,'constant',u.LinearColor(.36,.44,.44,1));u.MaterialEditingLibrary.connect_material_property(c,'',u.MaterialProperty.MP_EMISSIVE_COLOR);u.MaterialEditingLibrary.recompile_material(bg);u.EditorAssetLibrary.save_loaded_asset(bg)
    dome=editor.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));dome.set_actor_label('Alpine sky backdrop');dome.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Sphere'));dome.set_actor_scale3d(u.Vector(900,900,900));dome.static_mesh_component.set_material(0,bg);dome.static_mesh_component.set_collision_profile_name('NoCollision');dome.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);prop(dome.static_mesh_component,'cast_shadow',False)
    pp=editor.spawn_actor_from_class(u.PostProcessVolume,u.Vector(0,0,0));pp.set_actor_label('Alder Pass grading');prop(pp,'unbound',True)
    p=pp.get_editor_property('settings')
    for k,v in {'override_auto_exposure_method':True,'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,'override_auto_exposure_bias':True,'auto_exposure_bias':0.0,'override_auto_exposure_apply_physical_camera_exposure':True,'auto_exposure_apply_physical_camera_exposure':False,'override_motion_blur_amount':True,'motion_blur_amount':0.0,'override_vignette_intensity':True,'vignette_intensity':0.15}.items():prop(p,k,v)
    prop(pp,'settings',p)
    player=editor.spawn_actor_from_class(u.PlayerStart,u.Vector(-2950,488.46,155),u.Rotator(pitch=0,yaw=-13,roll=0));player.set_actor_label('PlayerStart_ArrivalRamp')
    logger_class=u.load_class(None,'/Script/ForestDemo.ScreenDebugLogger');assert logger_class
    logger=editor.spawn_actor_from_class(logger_class,u.Vector(-2600,50,80));logger.set_actor_label('ScreenDebugLogger_Hello')
    cam=editor.spawn_actor_from_class(u.CameraActor,u.Vector(12000,-12000,16000),u.MathLibrary.find_look_at_rotation(u.Vector(12000,-12000,16000),u.Vector(0,0,0)));cam.set_actor_label('Camera_Overview');cam.camera_component.projection_mode=u.CameraProjectionMode.ORTHOGRAPHIC;cam.camera_component.ortho_width=20000
    editor.clear_actor_selection_set()
    u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(8000,-10500,7000),u.MathLibrary.find_look_at_rotation(u.Vector(8000,-10500,7000),u.Vector(0,300,180)))
    assert levels.save_current_level(),'save level failed'
    u.EditorAssetLibrary.save_directory(ASSET,only_if_is_dirty=False,recursive=True)
    write('build_evidence.json',{'utc':stamp(),'map':MAP,'mesh_count':len(imported),'materials':len(materials)+1,'fbx_y_correction':y_sign,'terrain_extent_cm':vec(extent),'imports':imported,'sky_cubemap':cube.get_path_name() if cube else None,'saved':True})
    unreal_done=True
    u.log('ALDER_BUILD_COMPLETE')
try:main()
except Exception:
    write('build_error.json',{'utc':stamp(),'traceback':traceback.format_exc()});raise
