import unreal as u,json,time,traceback,struct
from pathlib import Path
from datetime import datetime,timezone
u.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/LighthouseHarbor/max');OUT=ROOT/'Screenshots';OUT.mkdir(exist_ok=True)
V=ROOT/'Validation';BASE='/Game/LighthouseHarbor/max';MAP='/Game/Maps/LighthouseHarbor_max'
LES=u.get_editor_subsystem(u.LevelEditorSubsystem);AES=u.get_editor_subsystem(u.EditorActorSubsystem)
def now():return datetime.now(timezone.utc).isoformat()
def write(path,d):path.write_text(json.dumps(d,indent=2,default=str),encoding='utf-8')
def validate():
    assert LES.load_level(MAP),'Saved map reload failed'
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();ws=world.get_world_settings()
    wp=ws.get_editor_property('world_partition');assert wp is None,'World Partition must be null'
    reg=u.AssetRegistryHelpers.get_asset_registry();reg.search_all_assets(True)
    opt=u.AssetRegistryDependencyOptions()
    for k in ['include_hard_package_references','include_soft_package_references','include_searchable_names','include_soft_management_references','include_hard_management_references']:opt.set_editor_property(k,True)
    seen=set();todo=[MAP];edges={};bad=[]
    while todo:
        package=todo.pop()
        if package in seen:continue
        seen.add(package);deps=[str(x) for x in reg.get_dependencies(package,opt)];edges[package]=deps
        for dep in deps:
            if dep.startswith('/Game/'):
                if dep!=MAP and not dep.startswith(BASE+'/'):bad.append(dep)
                elif dep not in seen:todo.append(dep)
    assert not bad,'Out-of-scope dependencies '+str(bad)
    actors=AES.get_all_level_actors();coverage=[];missing=[];actual_cameras=[];geometry_bounds=[]
    for a in actors:
        if a.get_actor_label().startswith('CAPTURE_'):
            loc=a.get_actor_location();rot=a.get_actor_rotation();cc=a.get_component_by_class(u.CameraComponent)
            actual_cameras.append({'name':a.get_actor_label(),'location_cm':[loc.x,loc.y,loc.z],'rotation_deg':[rot.pitch,rot.yaw,rot.roll],'ortho_width_cm':cc.get_editor_property('ortho_width')})
            if a.get_actor_label()=='CAPTURE_top_down':
                assert abs(rot.pitch+90)<.001 and abs(rot.yaw)<.001 and abs(rot.roll)<.001, 'Top down rotation is not true -90 pitch'
                assert abs(loc.z-20000)<.01 and abs(loc.x)<.01 and abs(loc.y)<.01
            if a.get_actor_label()=='CAPTURE_overview':
                assert abs(loc.x-12000)<.01 and abs(loc.y+12000)<.01 and abs(loc.z-16000)<.01
    for a in actors:
        if isinstance(a,u.StaticMeshActor):
            c=a.static_mesh_component;sm=c.static_mesh
            if not sm:missing.append(a.get_actor_label()+': mesh');continue
            mats=[c.get_material(i) for i in range(c.get_num_materials())]
            if not mats or any(m is None for m in mats):missing.append(a.get_actor_label()+': material')
            for m in mats:
                if m and not m.get_path_name().startswith(BASE+'/'):missing.append(a.get_actor_label()+': external material '+m.get_path_name())
            coverage.append({'actor':a.get_actor_label(),'mesh':sm.get_path_name(),'materials':[m.get_path_name() if m else None for m in mats],
              'scale':str(a.get_actor_scale3d()),'cast_shadow':c.get_editor_property('cast_shadow')})
            if a.get_actor_label() not in ['Atmospheric_Backdrop','Beacon_Beam']:
                origin,extent=a.get_actor_bounds(False)
                geometry_bounds.append({'actor':a.get_actor_label(),'min_cm':[origin.x-extent.x,origin.y-extent.y,origin.z-extent.z],
                  'max_cm':[origin.x+extent.x,origin.y+extent.y,origin.z+extent.z]})
    assert not missing,missing
    content=Path('D:/github/AstraEffort/ForestDemo/Saved/Workers/LighthouseHarbor/max/HarborPrivate/Content')
    forbidden=[str(p) for p in content.rglob('*') if '__ExternalActors__' in str(p) or '__ExternalObjects__' in str(p) or 'BuiltData' in p.name]
    assert not forbidden,forbidden
    # Water/foam bounds have conservative shader bounds_scale, so source footprint is checked on the rigid water base.
    base=next(b for b in geometry_bounds if b['actor']=='Water_Base')
    assert abs(base['min_cm'][0]+5000)<1 and abs(base['min_cm'][1]+5000)<1 and abs(base['max_cm'][0]-5000)<1 and abs(base['max_cm'][1]-5000)<1
    result={'pass':True,'utc':now(),'map':MAP,'saved_map_reloaded':True,'world_partition':None,'force_no_precomputed_lighting':ws.get_editor_property('force_no_precomputed_lighting'),
      'recursive_game_packages':sorted(seen),'dependency_edges':edges,'out_of_scope_game_dependencies':bad,'actor_count':len(actors),
      'placed_static_mesh_count':len(coverage),'placed_resource_coverage':coverage,'missing_materials':missing,'external_or_builtdata_packages':forbidden,'actual_saved_cameras':actual_cameras,
      'actual_rigid_base_footprint_cm':[base['max_cm'][0]-base['min_cm'][0],base['max_cm'][1]-base['min_cm'][1]],'placed_actor_bounds':geometry_bounds,
      'bounds_exceptions':'Sky backdrop is presentation environment; rotating beam/water/foam have enlarged culling bounds for shader movement.'}
    write(V/'saved_map_validation.json',result)
    return world,actors
def fail():
    write(V/'capture_error.json',{'utc':now(),'error':traceback.format_exc()})
    try:u.unregister_slate_post_tick_callback(handle)
    except:pass
    u.SystemLibrary.quit_editor()
try:
    world,actors=validate()
    for c in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2',
      'sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','sg.ShadingQuality 2','sg.LandscapeQuality 2',
      'r.ScreenPercentage 100','r.DynamicRes.OperationMode 0','r.MotionBlurQuality 0','r.HighResScreenshotDelay 8']:
        u.SystemLibrary.execute_console_command(world,c)
    cams={a.get_actor_label()[8:]:a for a in actors if a.get_actor_label().startswith('CAPTURE_')}
    queue=[('overview','overview'),('top_down','top_down'),('lighthouse','lighthouse'),('harbor','harbor'),('motion_t0','motion'),('motion_t1','motion')]
    state={'index':0,'phase':'warmup','until':time.monotonic()+18,'records':[],'task':None}
    manifest={'engine':'Unreal Engine 5.7','map':MAP,'capture_source':'Actual saved map reloaded in private Unreal editor, HighResScreenshot',
      'resolution':[1920,1080],'quality':'High (2)','screen_percentage':100,'view_mode':'Lit','game_view':True,
      'effects':'M_Beacon Time*0.20943951 rad/s rotates WPO cone. M_Water and M_Foam use Time-driven WPO; shader approximations.',
      'physical_simulation':False,'PIE_executed':False,'captures':state['records']}
    def tick(dt):
        try:
            t=time.monotonic()
            if t<state['until']:return
            i=state['index']
            if i>=len(queue):
                manifest['completed_at_utc']=now();write(OUT/'capture_manifest.json',manifest)
                u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
            filename,key=queue[i];cam=cams[key];cc=cam.get_component_by_class(u.CameraComponent)
            if state['phase'] in ['warmup','next']:
                # Deliberately update both cached perspective and orthographic viewport modes to Lit.
                cc.set_editor_property('projection_mode',u.CameraProjectionMode.PERSPECTIVE)
                LES.pilot_level_actor(cam);LES.set_exact_camera_view(True)
                # UE5.7 true removes a named override; add it first to avoid a handled ensure on an absent override.
                LES.editor_set_viewport_realtime(False);LES.editor_set_viewport_realtime(True);LES.editor_set_game_view(True)
                u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
                u.AutomationLibrary.set_editor_active_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
                AES.set_selected_level_actors([]);state['phase']='orthographic';state['until']=t+.5
            elif state['phase']=='orthographic':
                cc.set_editor_property('projection_mode',u.CameraProjectionMode.ORTHOGRAPHIC);LES.pilot_level_actor(cam)
                u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
                u.AutomationLibrary.set_editor_active_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
                LES.editor_set_game_view(True);LES.editor_invalidate_viewports()
                state['phase']='capture';state['until']=t+(5 if filename!='motion_t1' else 3)
            elif state['phase']=='capture':
                assert u.AutomationLibrary.get_editor_active_viewport_view_mode()==u.ViewModeIndex.VMI_LIT
                assert LES.editor_get_game_view()
                loc=cam.get_actor_location();rot=cam.get_actor_rotation()
                rec={'file':filename+'.png','requested_at_utc':now(),'location_cm':[loc.x,loc.y,loc.z],'rotation_deg':[rot.pitch,rot.yaw,rot.roll],
                  'projection':str(cc.get_editor_property('projection_mode')),'ortho_width_cm':cc.get_editor_property('ortho_width'),
                  'aspect_ratio':cc.get_editor_property('aspect_ratio'),'active_view_mode':str(u.AutomationLibrary.get_editor_active_viewport_view_mode()),
                  'game_view':LES.editor_get_game_view(),'realtime_subsystem_request':True,'screen_percentage':u.SystemLibrary.get_console_variable_float_value('r.ScreenPercentage'),
                  'quality':{k:u.SystemLibrary.get_console_variable_int_value('sg.'+k+'Quality') for k in ['ViewDistance','AntiAliasing','Shadow','GlobalIllumination','Reflection','PostProcess','Texture','Effects','Foliage','Shading']}}
                state['pending']=rec;state['requested_monotonic']=t;state['requested_epoch']=time.time()
                state['task']=u.AutomationLibrary.take_high_res_screenshot(1920,1080,str(OUT/(filename+'.png')),camera=None,delay=.25,force_game_view=True)
                state['phase']='await';state['until']=t+1
            elif state['phase']=='await':
                path=OUT/(filename+'.png')
                if path.exists() and path.stat().st_size>10000 and path.stat().st_mtime>=state['requested_epoch']-.1:
                    data=path.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n'
                    size=list(struct.unpack('>II',data[16:24]));assert size==[1920,1080]
                    state['pending'].update({'completed_at_utc':now(),'png_dimensions':size,'bytes':len(data),'capture_elapsed_seconds':t-state['requested_monotonic']})
                    state['records'].append(state['pending']);write(OUT/'capture_manifest.json',manifest)
                    state['index']+=1;state['phase']='next';state['until']=t+1
                    u.log('HARBOR_CAPTURE '+filename)
                elif t-state['requested_monotonic']>90:raise RuntimeError('Screenshot timeout '+filename)
        except:fail()
    handle=u.register_slate_post_tick_callback(tick)
except:fail()
