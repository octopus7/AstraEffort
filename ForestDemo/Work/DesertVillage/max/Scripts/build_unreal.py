import unreal as u, json, math, time, traceback, os
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/DesertVillage/max')
ASSET='/Game/DesertVillage/max'; MAP='/Game/Maps/DesertVillage_max'
MAN=json.loads((ROOT/'SourceArt/source_manifest.json').read_text(encoding='utf-8'))
EA=u.EditorAssetLibrary; ML=u.MaterialEditingLibrary
actors=u.get_editor_subsystem(u.EditorActorSubsystem); levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
tools=u.AssetToolsHelpers.get_asset_tools(); notes=[]
def utc():return datetime.now(timezone.utc).isoformat()
def record(name,data):(ROOT/'Validation'/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
def prop(obj,key,val):obj.set_editor_property(key,val)
def scalar(mat,val,x=0,y=0):
    n=ML.create_material_expression(mat,u.MaterialExpressionConstant,x,y);prop(n,'r',val);return n
def color(mat,value,x=0,y=0):
    n=ML.create_material_expression(mat,u.MaterialExpressionConstant3Vector,x,y);prop(n,'constant',u.LinearColor(*value,1));return n
def connect(a,b,pin='',out=''):ML.connect_material_expressions(a,out,b,pin)
def output(node,mat,mp):ML.connect_material_property(node,'',mp)
def create_material(name,spec,textures):
    dest=ASSET+'/Materials';mat=EA.load_asset(dest+'/M_'+name)
    if not mat:mat=tools.create_asset('M_'+name,dest,u.Material,u.MaterialFactoryNew())
    ML.delete_all_material_expressions(mat);prop(mat,'two_sided',spec.get('two_sided',False))
    tint=color(mat,spec['color'],-550,0)
    base=tint
    if spec.get('texture'):
        sample=ML.create_material_expression(mat,u.MaterialExpressionTextureSample,-700,180);prop(sample,'texture',textures[spec['texture']])
        mul=ML.create_material_expression(mat,u.MaterialExpressionMultiply,-240,0);connect(tint,mul,'A');connect(sample,mul,'B');base=mul
    output(base,mat,u.MaterialProperty.MP_BASE_COLOR)
    output(scalar(mat,spec['roughness'],-180,350),mat,u.MaterialProperty.MP_ROUGHNESS)
    output(scalar(mat,spec['metallic'],-180,440),mat,u.MaterialProperty.MP_METALLIC)
    if name=='Water':
        contrast=ML.create_material_expression(mat,u.MaterialExpressionMultiply,-500,260);connect(sample,contrast,'A');connect(scalar(mat,.12,-730,330),contrast,'B')
        offset=ML.create_material_expression(mat,u.MaterialExpressionAdd,-330,230);connect(contrast,offset,'A');connect(scalar(mat,.88,-540,430),offset,'B');connect(offset,mul,'B')
        panner=ML.create_material_expression(mat,u.MaterialExpressionPanner,-1100,160);prop(panner,'speed_x',.013);prop(panner,'speed_y',.009)
        connect(panner,sample,'Coordinates')
        # Moving authored normal map: shader approximation, not fluid simulation.
        normal=ML.create_material_expression(mat,u.MaterialExpressionTextureSample,-550,600);prop(normal,'texture',textures['T_WaterNormal']);prop(normal,'sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL);connect(panner,normal,'Coordinates')
        flatten=ML.create_material_expression(mat,u.MaterialExpressionLinearInterpolate,-250,650);connect(color(mat,(0,0,1),-500,850),flatten,'A');connect(normal,flatten,'B');connect(scalar(mat,.16,-500,950),flatten,'Alpha');output(flatten,mat,u.MaterialProperty.MP_NORMAL)
        output(scalar(mat,.35,-180,520),mat,u.MaterialProperty.MP_SPECULAR)
    if name.startswith('PalmLeaf'):
        foliage_enum=next(getattr(u.MaterialShadingModel,x) for x in dir(u.MaterialShadingModel) if 'FOLIAGE' in x)
        prop(mat,'shading_model',foliage_enum);output(color(mat,tuple(v*.42 for v in spec['color']),-300,600),mat,u.MaterialProperty.MP_SUBSURFACE_COLOR)
    if name=='LanternGlass':
        mul=ML.create_material_expression(mat,u.MaterialExpressionMultiply,-200,-180);connect(tint,mul,'A');connect(scalar(mat,.5,-400,-250),mul,'B');output(mul,mat,u.MaterialProperty.MP_EMISSIVE_COLOR)
    ML.layout_material_expressions(mat);ML.recompile_material(mat);EA.save_loaded_asset(mat);return mat

def import_one(path,dest,name,fbx=False):
    task=u.AssetImportTask();task.filename=str(path);task.destination_path=dest;task.destination_name=name;task.automated=True;task.replace_existing=True;task.save=True
    if fbx:
        opt=u.FbxImportUI();opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False
        data=opt.static_mesh_import_data;data.combine_meshes=True;data.generate_lightmap_u_vs=False;data.auto_generate_collision=False;data.transform_vertex_to_absolute=True;data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS;data.import_uniform_scale=1.0
        task.options=opt
    tools.import_asset_tasks([task]);paths=list(task.imported_object_paths)
    if not paths:raise RuntimeError('Import returned no assets: '+str(path))
    return EA.load_asset(paths[0])

def spawn_mesh(label,mesh,material=None,location=(0,0,0)):
    a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*location));a.set_actor_label(label)
    comp=a.static_mesh_component;comp.set_static_mesh(mesh)
    if material:comp.set_material(0,material)
    return a

def validate():
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();ws=world.get_world_settings();wp=ws.get_editor_property('world_partition')
    ar=u.AssetRegistryHelpers.get_asset_registry();ar.scan_paths_synchronous([ASSET,'/Game/Maps'],True)
    opt=u.AssetRegistryDependencyOptions();opt.include_hard_package_references=True;opt.include_soft_package_references=True;opt.include_searchable_names=True;opt.include_hard_management_references=True;opt.include_soft_management_references=True;opt.include_editor_only_package_references=True;opt.include_game_package_references=True
    visited=set();pending=[MAP];graph={};bad=[]
    while pending:
        package=pending.pop()
        if package in visited:continue
        visited.add(package);deps=[str(x) for x in ar.get_dependencies(package,opt)];graph[package]=deps
        for dep in deps:
            if dep.startswith('/Game/'):
                if not(dep.startswith(ASSET+'/') or dep==MAP):bad.append(dep)
                if dep not in visited:pending.append(dep)
    actor_records=[];missing=[];mesh_bounds=[];nonowned_materials=[];light_records=[]
    for a in actors.get_all_level_actors():
        if isinstance(a,u.DirectionalLight):
            comp=a.get_component_by_class(u.DirectionalLightComponent);light_records.append({'label':a.get_actor_label(),'type':'DirectionalLight','mobility':str(comp.mobility),'movable':comp.mobility==u.ComponentMobility.MOVABLE,'intensity':comp.intensity})
        if isinstance(a,u.SkyLight):
            comp=a.light_component;light_records.append({'label':a.get_actor_label(),'type':'SkyLight','mobility':str(comp.mobility),'movable':comp.mobility==u.ComponentMobility.MOVABLE,'intensity':comp.intensity,'real_time_capture':comp.get_editor_property('real_time_capture')})
        if not isinstance(a,u.StaticMeshActor):continue
        comp=a.static_mesh_component;mesh=comp.static_mesh
        mats=[comp.get_material(i).get_path_name() if comp.get_material(i) else None for i in range(comp.get_num_materials())]
        if any(x is None for x in mats):missing.append(a.get_actor_label())
        nonowned_materials.extend(x for x in mats if x and not x.startswith(ASSET+'/Materials/'))
        loc=a.get_actor_location();rotation=a.get_actor_rotation();bounds=mesh.get_bounding_box() if mesh else None
        actor_records.append({'label':a.get_actor_label(),'mesh':mesh.get_path_name() if mesh else None,'materials':mats,'location':[loc.x,loc.y,loc.z],'scale':[a.get_actor_scale3d().x,a.get_actor_scale3d().y,a.get_actor_scale3d().z]})
        if a.get_actor_label().startswith('SM_'):
            expected=next((x for x in MAN['meshes'] if x['name']==a.get_actor_label()),None)
            got=[[bounds.min.x,bounds.max.x],[bounds.min.y,bounds.max.y],[bounds.min.z,bounds.max.z]]
            error=max(abs(got[k][j]-expected['bounds_m'][k][j]*100) for k in range(3) for j in range(2))
            mesh_bounds.append({'mesh':a.get_actor_label(),'bounds_cm':got,'max_error_cm':error})
    labels={a.get_actor_label() for a in actors.get_all_level_actors()}
    required=['SM_SculptedSandTerrain','SM_TurquoiseOasisWater','SM_PalmFronds','SM_CaravanseraiArcades','SM_AdobeHomes','SM_ExteriorStairsAndRoutes','SM_TradingPlazaPaving','SM_ShadeClothCanopies','SM_HandPatternedRugs','SM_HandThrownPottery','SM_WovenBaskets','SM_CommunityWell','SM_OasisIrrigationChannel','SM_WoodenTradingCarts','SM_CratesAndCaravanCargo']
    result={'validated_at_utc':utc(),'reloaded_saved_map':True,'map':MAP,'world_partition_is_null':wp is None,'world_partition':str(wp),'bad_game_dependencies':sorted(set(bad)),'visited_game_packages':sorted(visited),'dependency_graph':graph,'placed_static_mesh_actors':actor_records,'missing_materials':missing,'required_semantics_present':{x:x in labels for x in required},'mesh_bounds':mesh_bounds,'mesh_bounds_pass':all(x['max_error_cm']<.2 for x in mesh_bounds),'all_29_meshes_present':len(mesh_bounds)==len(MAN['meshes']),'dynamic_lighting':True,'map_saved':True}
    result['light_components']=light_records;result['force_no_precomputed_lighting']=ws.get_editor_property('force_no_precomputed_lighting');result['nonowned_placed_materials']=nonowned_materials
    result['dynamic_lighting']=bool(light_records) and all(x['movable'] for x in light_records) and result['force_no_precomputed_lighting']
    result['passed']=wp is None and not bad and not missing and not nonowned_materials and result['dynamic_lighting'] and all(result['required_semantics_present'].values()) and result['mesh_bounds_pass'] and result['all_29_meshes_present']
    record('saved_map_validation.json',result)
    if not result['passed']:raise RuntimeError('Saved map validation failed: inspect saved_map_validation.json')
    return result

def camera(label,loc,target=None,ortho=None,rotation=None,fov=55):
    rot=u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]) if rotation else u.MathLibrary.find_look_at_rotation(u.Vector(*loc),u.Vector(*target))
    a=actors.spawn_actor_from_class(u.CameraActor,u.Vector(*loc),rot);a.set_actor_label('Camera_'+label);c=a.camera_component
    c.aspect_ratio=1920/1080;c.constrain_aspect_ratio=False;c.field_of_view=fov
    if ortho:
        c.projection_mode=u.CameraProjectionMode.ORTHOGRAPHIC;c.ortho_width=ortho;c.auto_calculate_ortho_planes=False;c.ortho_near_clip_plane=1;c.ortho_far_clip_plane=100000
    return a

def begin_capture(cameras):
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    for cmd in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','sg.ShadingQuality 2','r.ScreenPercentage 100','r.DynamicRes.OperationMode 0','r.MotionBlurQuality 0','r.Streaming.PoolSize 2000','r.TextureStreaming 0','r.Tonemapper.Sharpen 0.5','viewmode lit','ShowFlag.Grid 0','ShowFlag.Selection 0']:
        u.SystemLibrary.execute_console_command(world,cmd)
    actors.clear_actor_selection_set();levels.editor_set_game_view(True);levels.editor_set_viewport_realtime(True)
    u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
    u.AutomationLibrary.set_editor_active_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
    captures=[('overview',cameras['overview']),('top_down',cameras['top_down']),('plaza',cameras['plaza']),('oasis',cameras['oasis']),('water_t0',cameras['oasis']),('water_later',cameras['oasis']),('hero',cameras['hero'])]
    manifest={'created_at_utc':utc(),'engine':'Unreal Engine 5.7','source':'Actual saved-map UE editor rendering','resolution':[1920,1080],'scalability_level':2,'screen_percentage':100,'view_mode':'Lit','game_view':True,'ui_grid_debug_selection':False,'camera_piloted':True,'perspective_and_orthographic_view_modes':'Both configured to Lit in private project settings; viewmode lit issued after every pilot','water_motion':'Panner driven original normal and color textures, no fluid simulation/refraction; cloth is static authored sag','captures':[]}
    state={'index':0,'phase':'setup','last':time.monotonic(),'task':None,'handle':None,'start':time.monotonic(),'in_tick':False}
    def tick(dt):
        if state['in_tick']:return
        state['in_tick']=True
        try:
            if time.monotonic()-state['start']>420:raise RuntimeError('Capture timeout')
            if state['index']>=len(captures):
                manifest['completed_at_utc']=utc();(ROOT/'Screenshots/capture_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
                levels.save_current_level();u.unregister_slate_post_tick_callback(state['handle']);u.SystemLibrary.quit_editor();return
            name,cam=captures[state['index']]
            if state['phase']=='setup':
                levels.pilot_level_actor(cam);levels.set_exact_camera_view(True);levels.editor_set_game_view(True);levels.editor_set_viewport_realtime(True)
                u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
                u.AutomationLibrary.set_editor_active_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
                if u.AutomationLibrary.get_editor_active_viewport_view_mode()!=u.ViewModeIndex.VMI_LIT:raise RuntimeError('Active viewport not Lit')
                u.SystemLibrary.execute_console_command(world,'viewmode lit');u.SystemLibrary.execute_console_command(world,'ShowFlag.Grid 0');levels.editor_invalidate_viewports();state['last']=time.monotonic();state['phase']='warmup';return
            wait=16 if state['index']==0 else (4 if name=='water_later' else 7)
            if state['phase']=='warmup' and time.monotonic()-state['last']>=wait:
                path=ROOT/'Screenshots'/(name+'.png');loc=cam.get_actor_location();rot=cam.get_actor_rotation();c=cam.camera_component
                state['last']=time.monotonic();state['phase']='save'
                manifest['captures'].append({'file':name+'.png','requested_at_utc':utc(),'elapsed_capture_session_seconds':time.monotonic()-state['start'],'location_cm':[loc.x,loc.y,loc.z],'rotation_degrees':{'pitch':rot.pitch,'yaw':rot.yaw,'roll':rot.roll},'projection':str(c.projection_mode),'ortho_width_cm':c.ortho_width if c.projection_mode==u.CameraProjectionMode.ORTHOGRAPHIC else None,'fov_degrees':c.field_of_view,'game_view_confirmed':levels.editor_get_game_view(),'piloted_actor':levels.get_pilot_level_actor().get_actor_label(),'viewport_keys':[str(k) for k in levels.get_viewport_config_keys()]})
                manifest['captures'][-1]['actual_view_mode']=str(u.AutomationLibrary.get_editor_active_viewport_view_mode())
                state['task']=u.AutomationLibrary.take_high_res_screenshot(1920,1080,str(path),camera=None,delay=0,force_game_view=True)
                return
            if state['phase']=='save' and time.monotonic()-state['last']>3:
                path=ROOT/'Screenshots'/(name+'.png')
                if path.exists() and path.stat().st_size>10000:
                    manifest['captures'][-1]['file_seen_at_utc']=utc();manifest['captures'][-1]['bytes']=path.stat().st_size;state['index']+=1;state['phase']='setup'
        except Exception:
            record('capture_error.json',{'time':utc(),'error':traceback.format_exc()});u.log_error(traceback.format_exc());u.unregister_slate_post_tick_callback(state['handle']);u.SystemLibrary.quit_editor()
        finally:state['in_tick']=False
    state['handle']=u.register_slate_post_tick_callback(tick)

def main():
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    textures={}
    for p in sorted((ROOT/'SourceArt/Textures').glob('*.png')):
        tex=import_one(p,ASSET+'/Textures',p.stem)
        if p.stem=='T_WaterNormal':tex.set_editor_property('srgb',False);tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP)
        textures[p.stem]=tex;EA.save_loaded_asset(tex)
    materials={name:create_material(name,spec,textures) for name,spec in MAN['materials'].items()}
    meshes={};bounds_check=[]
    for desc in MAN['meshes']:
        name=desc['name'];mesh=import_one(ROOT/'SourceArt/FBX'/(name+'.fbx'),ASSET+'/Meshes',name,True)
        for i,slot in enumerate(mesh.static_materials):
            slotname=str(slot.material_slot_name)
            if slotname not in materials:raise RuntimeError('Unexpected material slot '+name+' '+slotname)
            mesh.set_material(i,materials[slotname])
        EA.save_loaded_asset(mesh);meshes[name]=mesh
    # Confirm axis and units through a second actual UE import of corrected asymmetric probe.
    probe=import_one(ROOT/'SourceArt/FBX/SM_AxisProbe.fbx',ASSET+'/Probe','SM_AxisProbe',True);b=probe.get_bounding_box()
    probe_result={'expected_min_cm':[200,500,0],'expected_max_cm':[400,900,200],'actual_min_cm':[b.min.x,b.min.y,b.min.z],'actual_max_cm':[b.max.x,b.max.y,b.max.z],'passed':max(abs(b.min.x-200),abs(b.min.y-500),abs(b.min.z),abs(b.max.x-400),abs(b.max.y-900),abs(b.max.z-200))<.1};record('import_axis_units.json',probe_result)
    if not probe_result['passed']:raise RuntimeError('FBX axis probe failed')
    EA.delete_asset(probe.get_path_name());EA.delete_directory(ASSET+'/Probe')
    if not levels.new_level(MAP,False):raise RuntimeError('Could not create level')
    for name,mesh in meshes.items():spawn_mesh(name,mesh)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();ws=world.get_world_settings();prop(ws,'force_no_precomputed_lighting',True)
    sun=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,15000),u.Rotator(pitch=-48,yaw=135,roll=0));sun.set_actor_label('Sun_WarmLateAfternoon');lc=sun.get_component_by_class(u.DirectionalLightComponent);lc.set_mobility(u.ComponentMobility.MOVABLE);lc.set_intensity(3.8);lc.set_light_color(u.LinearColor(1,.90,.77,1));lc.set_editor_property('light_source_angle',2.0)
    sky=actors.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,6000));sky.set_actor_label('Sky_DynamicAmbient');sky.light_component.set_mobility(u.ComponentMobility.MOVABLE);sky.light_component.set_intensity(1.05);sky.light_component.set_editor_property('real_time_capture',True)
    sky_mat=tools.create_asset('M_DistantSky',ASSET+'/Materials',u.Material,u.MaterialFactoryNew());prop(sky_mat,'shading_model',u.MaterialShadingModel.MSM_UNLIT);prop(sky_mat,'two_sided',True);prop(sky_mat,'is_sky',True);output(color(sky_mat,(.38,.57,.63)),sky_mat,u.MaterialProperty.MP_EMISSIVE_COLOR);ML.recompile_material(sky_mat);EA.save_loaded_asset(sky_mat)
    sky_actor=spawn_mesh('Backdrop_SkyDome',EA.load_asset('/Engine/BasicShapes/Sphere'),sky_mat);sky_actor.set_actor_scale3d(u.Vector(2000,2000,2000));sky_actor.static_mesh_component.set_editor_property('cast_shadow',False);sky_actor.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    pp=actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector(0,0,0));pp.set_actor_label('PostProcess_FixedExposure');pp.set_editor_property('unbound',True)
    settings=pp.get_editor_property('settings')
    for key,val in [('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('auto_exposure_apply_physical_camera_exposure',False),('auto_exposure_bias',0.0),('bloom_intensity',.12),('motion_blur_amount',0.0),('ambient_occlusion_intensity',.8),('ambient_occlusion_radius',90.0)]:prop(settings,'override_'+key,True);prop(settings,key,val)
    pp.set_editor_property('settings',settings)
    cams={
      'overview':camera('overview',(12000,-12000,16000),(0,0,0),20000),
      'top_down':camera('top_down',(0,0,20000),ortho=20000,rotation=(-90,0,0)),
      'plaza':camera('plaza',(1900,-2500,900),(200,-300,240),fov=58),
      'oasis':camera('oasis',(-4200,-4100,1550),(-1250,-1250,250),fov=55),
      'hero':camera('hero',(10000,-14000,11500),(0,0,300),14500)
    }
    actors.clear_actor_selection_set();levels.save_current_level();EA.save_directory(ASSET,False,True)
    if not levels.load_level(MAP):raise RuntimeError('Reload saved map failed')
    validate()
    cams={a.get_actor_label()[7:]:a for a in actors.get_all_level_actors() if isinstance(a,u.CameraActor)}
    record('build_complete.json',{'at_utc':utc(),'materials':len(materials)+1,'meshes':len(meshes),'textures':len(textures),'notes':notes})
    begin_capture(cams)

if __name__=='__main__':
    try:main()
    except Exception:
        record('build_error.json',{'at_utc':utc(),'error':traceback.format_exc()});u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
