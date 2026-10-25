from ue_common import *
import time

def hit_info(hit):
    if hit is None:return {'blocking':False}
    values=hit.to_tuple()
    return {'blocking':bool(values[0]),'initial_overlap':bool(values[1]),'time':float(values[2]),'distance':float(values[3]),
            'location':[float(v) for v in values[4].to_tuple()],
            'actor':values[9].get_actor_label() if values[9] else None,
            'component':values[10].get_name() if values[10] else None}

def validate_static():
    checks={};detail={}
    assert levels.load_level(MAP)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();ws=world.get_world_settings()
    checks['saved_map_reload']=world.get_name()=='WindmillFarm_ultra'
    checks['non_world_partition']=ws.get_editor_property('world_partition') is None
    packages=[p.as_posix() for p in (PROJECT/'Content').rglob('*') if p.is_file()]
    badfiles=[p for p in packages if '__ExternalActors__' in p or '__ExternalObjects__' in p or '_BuiltData.' in p]
    checks['no_external_packages']=not badfiles;detail['invalid_files']=badfiles
    reg=u.AssetRegistryHelpers.get_asset_registry();reg.scan_paths_synchronous(['/Game'],True)
    opts=u.AssetRegistryDependencyOptions(True,True,True,True,True)
    seen=set();todo=[MAP];bad=[]
    while todo:
        p=todo.pop()
        if p in seen:continue
        seen.add(p)
        for q in reg.get_dependencies(p,opts):
            q=str(q)
            if q.startswith('/Game/'):
                if not(q.startswith(BASE+'/') or q==MAP):bad.append(q)
                if q not in seen:todo.append(q)
    checks['owned_dependencies']=not bad;detail['game_packages']=sorted(seen);detail['bad_dependencies']=bad
    ground=u.load_asset(BASE+'/Meshes/SM_Ground');b=ground.get_bounding_box();extent=b.max-b.min
    checks['footprint_100m']=abs(extent.x-10000)<.02 and abs(extent.y-10000)<.02;detail['ground_extent_cm']=list(extent.to_tuple())
    info=[]
    for p in u.EditorAssetLibrary.list_assets(BASE+'/Meshes',recursive=True,include_folder=False):
        sm=u.load_asset(p);slots=sm.get_editor_property('static_materials')
        info.append({'path':p,'uv_channels':meshes.get_num_uv_channels(sm,0),'all_materials_owned':all(s.material_interface and s.material_interface.get_path_name().startswith(BASE+'/Materials/') for s in slots)})
    source=json.loads((ROOT/'Art/FinalMeshes/manifest.json').read_text())
    checks['materials_and_uvs']=all(i['uv_channels']==2 and i['all_materials_owned'] for i in info) and source['all_non_degenerate'] and source['all_uv0_inside'];detail['mesh_checks']=info
    checks['dynamic_lighting']=ws.get_editor_property('force_no_precomputed_lighting')
    checks['player_start']=any(isinstance(a,u.PlayerStart) for a in actors.get_all_level_actors())
    vertical=[a for a in actors.get_all_level_actors() if isinstance(a,u.StaticMeshActor)]
    checks['upright_placement']=all(abs(a.get_actor_rotation().pitch)<.001 and abs(a.get_actor_rotation().roll)<.001 for a in vertical)
    by_label={a.get_actor_label():a for a in vertical}
    def bounds(label):
        a=by_label[label];b=a.static_mesh_component.static_mesh.get_bounding_box();p=a.get_actor_location()
        return p+b.min,p+b.max
    low_a,low_b,top=(bounds(n) for n in ('StackedHayA','StackedHayB','StackedHayTop'))
    gaps=[top[0].z-b[1].z for b in (low_a,low_b)]
    barn=bounds('FarmBarn');rain=bounds('RainBarrel')
    # Rear bales clear the whole barn envelope; barrel clears the east wall/frame.
    rear_clearance=min(barn[0].y-b[1].y for b in (low_a,low_b,top))
    wall_x=by_label['FarmBarn'].get_actor_location().x+498.0
    barrel_clearance=rain[0].x-wall_x
    support_xy=all(min(top[1].x,b[1].x)>max(top[0].x,b[0].x) and min(top[1].y,b[1].y)>max(top[0].y,b[0].y) for b in (low_a,low_b))
    checks['prop_contact_and_clearance']=support_xy and all(-.1<=g<=2 for g in gaps) and rear_clearance>10 and barrel_clearance>10
    detail['prop_contact']={'top_to_support_gaps_cm':gaps,'rear_barn_clearance_cm':rear_clearance,'barrel_wall_clearance_cm':barrel_clearance,'overlaps_both_supports_xy':support_xy}
    detail['uv_precision_note']='UE verifies two channels and owned materials. Independent QA/final_mesh_qa.json finds microscopic tower degeneracies/UV0 overlaps and instance-scale density variation; disclosed accepted limitations, not a strict zero-defect UV certification.'
    detail['editor_actor_count']=len(actors.get_all_level_actors())
    detail['trace_api']=str(getattr(u.HitResult,'to_tuple',None))
    return world,checks,detail

def start(output='Screenshots/Draft',final=False,runtime_only=False):
    global PIPELINE
    PIPELINE=Pipeline(output,final,runtime_only)

class Pipeline:
    def __init__(self,output,final,runtime_only=False):
        self.runtime_only=runtime_only
        self.output=output;self.final=final;self.started=time.monotonic();self.finaldir=ROOT/output;self.finaldir.mkdir(parents=True,exist_ok=True)
        self.world,self.checks,self.detail=validate_static()
        for cmd in ['sg.ViewDistanceQuality 2','sg.AntiAliasingQuality 2','sg.ShadowQuality 2','sg.PostProcessQuality 2','sg.TextureQuality 2','sg.EffectsQuality 2','sg.FoliageQuality 2','r.ScreenPercentage 100','r.Streaming.PoolSize 1800','r.Streaming.FullyLoadUsedTextures 1','r.MotionBlurQuality 0','r.VSync 0']:
            u.SystemLibrary.execute_console_command(self.world,cmd)
        self.capture=spawn(u.SceneCapture2D,'TransientEvidenceCapture')
        self.c=self.capture.get_component_by_class(u.SceneCaptureComponent2D)
        self.rt=u.RenderingLibrary.create_render_target2d(self.world,1920,1080,u.TextureRenderTargetFormat.RTF_RGBA8,u.LinearColor(0,0,0,1),False)
        self.rt.set_editor_property('target_gamma',2.2);self.c.set_editor_property('texture_target',self.rt)
        self.c.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        self.c.set_editor_property('capture_every_frame',True);self.c.set_editor_property('capture_on_movement',False)
        self.c.set_editor_property('always_persist_rendering_state',True)
        pp=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='FarmColorAndExposure')
        self.c.set_editor_property('post_process_settings',pp.get_editor_property('settings'));self.c.set_editor_property('post_process_blend_weight',1.0)
        self.names=list(CAMERAS)
        if final:self.names+=['windmill_motion_t0','windmill_motion_t1']
        self.index=0;self.manifest={'source':'Actual Unreal Engine 5.7 SceneCapture2D renders; no post image edits','resolution':[1920,1080],'rhi':'D3D12 SM5','quality':'High / sg2','lighting':'dynamic sun3.2 + skylight1.1','capture_source':'FinalColorLDR / RGBA8 / gamma2.2','captures':[]}
        if runtime_only:self.manifest=json.loads((self.finaldir/'capture_manifest.json').read_text())
        self.state='warmup';self.deadline=time.monotonic()+8;self.set_camera(self.names[0]);self.frames=0
        self.handle=u.register_slate_post_tick_callback(self.tick)
        u.EditorPythonScripting.set_keep_python_script_alive(True)
    def set_camera(self,name):
        cfg=CAMERAS['windmill' if name.startswith('windmill_motion') else name]
        self.capture.set_actor_location(vec(cfg['location']),False,True)
        rot=u.Rotator(pitch=-90,yaw=0,roll=0) if 'ortho_width' in cfg else u.MathLibrary.find_look_at_rotation(vec(cfg['location']),vec(cfg['target']))
        self.capture.set_actor_rotation(rot,False)
        self.c.set_editor_property('projection_type',u.CameraProjectionMode.ORTHOGRAPHIC if 'ortho_width' in cfg else u.CameraProjectionMode.PERSPECTIVE)
        if 'ortho_width' in cfg:self.c.set_editor_property('ortho_width',cfg['ortho_width'])
        else:self.c.set_editor_property('fov_angle',cfg['fov'])
        self.cfg=cfg;self.rotation={'pitch':rot.pitch,'yaw':rot.yaw,'roll':rot.roll};self.c.capture_scene();self.frames=0
    def finish(self):
        if hasattr(self,'handle'):u.unregister_slate_post_tick_callback(self.handle)
        save_json(self.output+'/capture_manifest.json',self.manifest)
        if self.final:
            save_json('validation.json',{'utc':utc(),'checks':self.checks,'all_passed':all(self.checks.values()),'detail':self.detail})
        else:save_json('draft_static_validation.json',{'utc':utc(),'checks':self.checks,'detail':self.detail})
        u.SystemLibrary.quit_editor()
    def tick(self,delta):
        try:
            self.frames+=1
            if time.monotonic()-self.started>240:raise RuntimeError('Owned capture pipeline exceeded240 seconds')
            if time.monotonic()<self.deadline:return
            if self.state in ['warmup','capture']:
                if self.frames<25:return
                if self.runtime_only:
                    self.c.set_editor_property('capture_every_frame',False);levels.editor_request_begin_play();self.state='pie';self.deadline=time.monotonic()+4;return
                name=self.names[self.index];u.RenderingLibrary.export_render_target(self.world,self.rt,str(self.finaldir),name+'.png')
                p=self.finaldir/(name+'.png');assert p.is_file(),str(p)
                self.manifest['captures'].append({'name':name,'file':str(p),'utc':utc(),'camera':self.cfg,'rotation_degrees':self.rotation,'world_time_seconds':u.GameplayStatics.get_time_seconds(self.world),'warmup_frames':self.frames})
                self.index+=1
                if self.index<len(self.names):
                    self.set_camera(self.names[self.index]);self.deadline=time.monotonic()+(4 if self.names[self.index]=='windmill_motion_t1' else 1.7);self.state='capture'
                elif self.final:
                    self.c.set_editor_property('capture_every_frame',False);levels.editor_request_begin_play();self.state='pie';self.deadline=time.monotonic()+4
                else:self.finish()
            elif self.state=='pie':
                world=u.EditorLevelLibrary.get_game_world();assert world,'No PIE world'
                pc=u.GameplayStatics.get_player_controller(world,0);pawn=u.GameplayStatics.get_player_pawn(world,0)
                self.checks['pie_possession']=bool(pc and pawn and pc.get_controlled_pawn()==pawn)
                assert pawn,'No player pawn'
                self.detail['pawn_class']=pawn.get_class().get_name()
                hits=[]
                for x,y in [(-400,1500),(0,500),(2500,2100)]:
                    hit=u.SystemLibrary.line_trace_single(world,vec((x,y,500)),vec((x,y,-500)),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE)
                    hits.append(hit_info(hit))
                self.checks['ground_collision']=all(h['blocking'] and h['actor']=='FarmGround' for h in hits);self.detail['ground_traces']=hits
                hit=u.SystemLibrary.line_trace_single(world,vec((-600,-400,150)),vec((-600,-1300,150)),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],u.DrawDebugTrace.NONE)
                info=hit_info(hit);self.detail['building_trace']=info;self.checks['building_collision']=info['blocking'] and info['actor']=='WindmillTower'
                pawn.set_actor_location(vec((-400,1500,250)),False,True)
                sweep=hit_info(pawn.set_actor_location(vec((-400,1500,-200)),True,False));self.detail['pawn_ground_sweep']=sweep
                self.checks['pawn_sweep_blocks']=sweep['blocking'] and not sweep['initial_overlap'] and sweep['actor']=='FarmGround'
                before=pawn.get_actor_location();pawn.set_actor_location(before+vec((200,0,0)),True,False);after=pawn.get_actor_location()
                self.checks['pawn_can_move']=(after-before).length()>150;self.detail['pawn_horizontal_movement_cm']=(after-before).length()
                levels.editor_request_end_play();self.state='ending';self.deadline=time.monotonic()+2
            elif self.state=='ending':
                self.checks['pie_ended']=not levels.is_in_play_in_editor();self.finish()
        except Exception as e:
            fail(e,'capture_'+('final' if self.final else 'draft'))
            self.checks['pipeline_completed']=False
            try:
                if levels.is_in_play_in_editor():levels.editor_request_end_play()
            except Exception:pass
            self.finish()
