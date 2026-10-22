"""Fresh-process read-only saved-map validation, actual PIE and final UE captures."""
import unreal as u, sys, json, hashlib, traceback, time, struct
from pathlib import Path
from datetime import datetime,timezone
W=Path('D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra')
P=Path('D:/github/AstraEffort/ForestDemo/Saved/Workers/HillsideOnsen/ultra/Project')
sys.path.insert(0,str(W))
from validate_engine import run_static_validation
from runtime_probe import start_runtime_probe
M_BYTES=(W/'scene_manifest.json').read_bytes()
M=json.loads(M_BYTES)
M_SHA=hashlib.sha256(M_BYTES).hexdigest()
S={}
def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,data):path.write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inventory():
    paths=sorted((P/'Content/HillsideOnsen/ultra').rglob('*.uasset'))+[P/'Content/Maps/HillsideOnsen_ultra.umap']
    return [{'path':p.relative_to(P).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths]
def check_effect_graphs():
    checks=[]
    specs=[('M_Water',u.MaterialProperty.MP_WORLD_POSITION_OFFSET,['MaterialExpressionTime','MaterialExpressionSine']),('M_Water',u.MaterialProperty.MP_NORMAL,['MaterialExpressionPanner','MaterialExpressionTextureSample']),('M_Stream',u.MaterialProperty.MP_BASE_COLOR,['MaterialExpressionPanner','MaterialExpressionTextureSample']),('M_Steam',u.MaterialProperty.MP_OPACITY,['MaterialExpressionTime','MaterialExpressionSine','MaterialExpressionDepthFade','MaterialExpressionTextureSample']),('M_Steam',u.MaterialProperty.MP_WORLD_POSITION_OFFSET,['MaterialExpressionTime','MaterialExpressionSine'])]
    for name,prop,expected in specs:
        mat=u.load_asset('/Game/HillsideOnsen/ultra/Materials/'+name)
        root=u.MaterialEditingLibrary.get_material_property_input_node(mat,prop)
        pending=[root];seen=set();classes=[]
        while pending:
            expr=pending.pop()
            if expr is None or expr.get_path_name() in seen:continue
            seen.add(expr.get_path_name());classes.append(expr.get_class().get_name())
            pending.extend(u.MaterialEditingLibrary.get_inputs_for_material_expression(mat,expr))
        checks.append({'material':name,'property':str(prop),'classes':sorted(set(classes)),'expected':expected,'passed':all(x in classes for x in expected)})
    report={'utc':utc(),'passed':all(c['passed'] for c in checks),'checks':checks,'technique':'Artistic animated opaque water and translucent steam cards; no fluid, refraction or thermodynamics simulation'}
    dump(W/'Validation/effect_graphs.json',report)
    return report
def quit_with_error(where):
    dump(W/'Validation/verification_error.json',{'utc':utc(),'where':where,'traceback':traceback.format_exc()})
    if S.get('handle'):u.unregister_slate_post_tick_callback(S['handle']);S['handle']=None
    u.SystemLibrary.quit_editor()

def start_capture(runtime_report):
    try:
        S['runtime_report']=runtime_report
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        assert world is not None,'PIE world absent after runtime probe'
        cap=next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.SceneCapture2D) if a.actor_has_tag('OnsenEvidenceCapture'))
        comp=cap.get_component_by_class(u.SceneCaptureComponent2D)
        rt=u.RenderingLibrary.create_render_target2d(world,1920,1080,u.TextureRenderTargetFormat.RTF_RGBA8)
        comp.set_editor_property('texture_target',rt)
        comp.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        comp.set_editor_property('capture_every_frame',True)
        comp.set_editor_property('always_persist_rendering_state',True)
        settings=u.PostProcessSettings()
        for key,value in {'override_auto_exposure_method':True,'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,'override_auto_exposure_bias':True,'auto_exposure_bias':0.0,'override_auto_exposure_apply_physical_camera_exposure':True,'auto_exposure_apply_physical_camera_exposure':False,'override_motion_blur_amount':True,'motion_blur_amount':0.0}.items():settings.set_editor_property(key,value)
        comp.set_editor_property('post_process_settings',settings);comp.set_editor_property('post_process_blend_weight',1.0)
        views=[(name,M['camera_views'][name],35.0 if name=='overview' else 12.0) for name in ['overview','top_down','village_path','hot_spring']]
        views += [('hot_spring_timed_04s',M['camera_views']['hot_spring'],4.0),('hot_spring_timed_08s',M['camera_views']['hot_spring'],4.0)]
        S.update(world=world,cap=cap,comp=comp,rt=rt,views=views,index=-1,view_started=0)
        assert sha(W/'scene_manifest.json')==M_SHA,'Scene source changed since validation began'
        S['manifest']={'theme':'HillsideOnsen','effort':'ultra','started_at_utc':utc(),'source':'Actual Unreal Engine SceneCapture2D in PlayInEditor world','world':world.get_path_name(),'resolution':[1920,1080],'render_target_format':'RGBA8','capture_source':'FinalColorLDR','exposure':'Manual, bias0, physical camera exposure disabled','motion_blur':0,'dynamic_lighting':True,'packages_sha256':S['package_digest'],'scene_manifest_sha256':M_SHA,'views':[]}
        def advance():
            S['index']+=1
            if S['index']>=len(S['views']):
                after=inventory();unchanged=after==S['packages']
                assert sha(W/'scene_manifest.json')==M_SHA,'Scene source changed during capture'
                S['manifest'].update(finished_at_utc=utc(),packages_unchanged=unchanged,static_validation_passed=bool(S['static'].get('passed',S['static'].get('status')=='passed')),runtime_status=runtime_report.get('status'))
                dump(W/'Screenshots/capture_manifest.json',S['manifest'])
                dump(W/'Validation/after_capture_packages.json',{'unchanged':unchanged,'files':after})
                u.unregister_slate_post_tick_callback(S['handle']);S['handle']=None
                # End PIE first and let its world finish teardown before editor shutdown.
                u.get_editor_subsystem(u.LevelEditorSubsystem).editor_request_end_play()
                S['shutdown_started']=time.monotonic()
                def shutdown_tick(dt):
                    if time.monotonic()-S['shutdown_started']<5:return
                    u.unregister_slate_post_tick_callback(S['shutdown_handle'])
                    u.SystemLibrary.quit_editor()
                S['shutdown_handle']=u.register_slate_post_tick_callback(shutdown_tick)
                return
            name,cam,delay=S['views'][S['index']]
            pos=u.Vector(*(v*100 for v in cam['location']));target=u.Vector(*(v*100 for v in cam['target']))
            cap.set_actor_location(pos,False,False);cap.set_actor_rotation(u.MathLibrary.find_look_at_rotation(pos,target),False)
            assert max(abs(a-b) for a,b in zip(cap.get_actor_location().to_tuple(),pos.to_tuple()))<.01
            comp.set_editor_property('fov_angle',cam['fov']);comp.capture_scene()
            S['view_started']=time.monotonic();S['game_started']=u.GameplayStatics.get_time_seconds(world)
        def tick(dt):
            try:
                name,cam,delay=S['views'][S['index']]
                if time.monotonic()-S['view_started']<delay:return
                comp.capture_scene()
                file=W/'Screenshots'/(name+'.png')
                if file.exists():file.unlink()
                u.RenderingLibrary.export_render_target(world,rt,str(W/'Screenshots'),name+'.png')
                assert file.exists() and file.stat().st_size>100000
                head=file.read_bytes()[:24];assert head[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',head[16:24])==(1920,1080)
                S['manifest']['views'].append({'name':name,'file':file.name,'utc':utc(),'game_seconds':u.GameplayStatics.get_time_seconds(world),'camera':cam,'actual_location_cm':cap.get_actor_location().to_tuple(),'actual_rotation_degrees':cap.get_actor_rotation().to_tuple(),'actual_fov':comp.get_editor_property('fov_angle'),'fresh_export':True,'warmup_wall_seconds':time.monotonic()-S['view_started'],'sha256':sha(file),'bytes':file.stat().st_size})
                dump(W/'Screenshots/capture_manifest.json',S['manifest']);advance()
            except Exception:quit_with_error('capture tick')
        S['handle']=u.register_slate_post_tick_callback(tick);advance()
    except Exception:quit_with_error('start capture')

def main():
    assert '/Saved/Workers/HillsideOnsen/ultra/' in u.Paths.get_project_file_path().replace('\\','/')
    assert u.EditorLevelLibrary.load_level('/Game/Maps/HillsideOnsen_ultra')
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    S['packages']=inventory();S['package_digest']=hashlib.sha256(json.dumps(S['packages'],sort_keys=True).encode()).hexdigest()
    dump(W/'Validation/validated_packages.json',{'utc':utc(),'digest':S['package_digest'],'files':S['packages']})
    S['static']=run_static_validation(world,M,W/'Validation/engine_validation.json')
    S['effects']=check_effect_graphs()
    # Unsaved ordinary editor actors duplicate into PIE; RF_Transient actors do not.
    S['editor_capture']=u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(u.SceneCapture2D,u.Vector(0,0,1000))
    S['editor_capture'].set_editor_property('tags',[u.Name('OnsenEvidenceCapture')])
    S['editor_capture'].set_actor_label('Transient onsen evidence capture')
    dump(W/'Validation/python_api_inventory.json',{cls.__name__:[n for n in dir(cls) if not n.startswith('_')] for cls in [u.Character,u.CharacterMovementComponent,u.GameplayStatics,u.EditorActorSubsystem,u.SceneCaptureComponent2D,u.HitResult]})
    routes=[{'name':r['name'],'points':[[v*100 for v in p] for p in r['points']]} for r in M['runtime_routes']]
    routes += [
      {'name':'stream_bridge','points':[[800,962.5,766.25],[-800,1391.0714,877.6786]]},
      {'name':'lower_stairs','points':[[-2400,-1970,377.3333],[-2400,-1225,620]]},
      {'name':'upper_stairs','points':[[2500,1125,637.7273],[2500,2075,1010]]},
      {'name':'bathhouse_wall_blocks','points':[[1300,-800,620],[1300,-200,620]],'obstacle_point':[1300,-411,620],'obstacle_actor_label':'Onsen_DarkWood'}]
    S['probe']=start_runtime_probe(world,routes,W/'Validation/runtime_walks.json',start_capture)
    u.EditorPythonScripting.set_keep_python_script_alive(True)

try:main()
except Exception:quit_with_error('bootstrap')
