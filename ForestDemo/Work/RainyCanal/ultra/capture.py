import unreal,json,time,traceback
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
MAP='/Game/Maps/RainyCanal_ultra'
LEV=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACT=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ED=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
CAMS={
 'overview':{'location':[11500,14375,9900],'target':[0,0,50],'fov':48},
 'top_down':{'location':[0,0,16000],'target':[0,0,0],'ortho_width':19600},
 'canal':{'location':[350,4300,450],'target':[0,1000,20],'fov':62},
 'rainy_street':{'location':[-1000,3600,230],'target':[-1400,1000,100],'fov':64},
 'puddle':{'location':[-1400,3100,190],'target':[-1100,2700,0],'fov':55},
 'dock':{'location':[1500,-800,350],'target':[350,-100,0],'fov':60},
}
class Capture:
    def __init__(self,phase='draft',validate=False,movie=False):
        self.phase=phase;self.validate=validate;self.movie=movie;self.begin=time.monotonic();self.last=self.begin;self.stage='warm';self.frames=0;self.done=False;self.rows=[];self.movie_rows=[];self.counter=0
        assert LEV.load_level(MAP)
        self.world=ED.get_editor_world()
        unreal.SystemLibrary.execute_console_command(self.world,'sg.ViewDistanceQuality 2')
        for group in ['AntiAliasing','Shadow','GlobalIllumination','Reflection','PostProcess','Texture','Effects','Foliage','Shading']:
            unreal.SystemLibrary.execute_console_command(self.world,f'sg.{group}Quality 2')
        unreal.SystemLibrary.execute_console_command(self.world,'r.Streaming.PoolSize 3000')
        unreal.SystemLibrary.execute_console_command(self.world,'r.ScreenPercentage 100')
        self.camera=ACT.spawn_actor_from_class(unreal.SceneCapture2D,unreal.Vector(0,0,1000));self.camera.set_actor_label('TransientEvidenceCamera')
        self.comp=self.camera.get_component_by_class(unreal.SceneCaptureComponent2D)
        self.rt=unreal.RenderingLibrary.create_render_target2d(self.world,1920,1080,unreal.TextureRenderTargetFormat.RTF_RGBA8)
        self.rt.set_editor_property('target_gamma',2.2)
        self.comp.set_editor_property('texture_target',self.rt);self.comp.set_editor_property('capture_source',unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR);self.comp.set_editor_property('capture_every_frame',True);self.comp.set_editor_property('always_persist_rendering_state',True)
        self.rain=next(a for a in ACT.get_all_level_actors() if a.get_actor_label()=='RainVolume')
        self.views=[('rainy_street','rainy_street'),('canal','canal'),('dock','dock'),('top_down','top_down'),('overview','overview'),('canal_motion_t0','canal'),('canal_motion_t1','canal'),('rainy_street_motion_t0','rainy_street'),('rainy_street_motion_t1','rainy_street'),('water_only_t0','canal'),('water_only_t1','canal'),('puddle_t0','puddle'),('puddle_t1','puddle')]
        self.set_view('rainy_street')
        self.out=ROOT/('Screenshots' if validate else 'Draft');self.out.mkdir(exist_ok=True)
        unreal.EditorPythonScripting.set_keep_python_script_alive(True)
        self.handle=unreal.register_slate_post_tick_callback(self.tick)
    def set_view(self,key):
        d=CAMS[key];loc=unreal.Vector(*d['location']);target=unreal.Vector(*d['target']);rot=unreal.MathLibrary.find_look_at_rotation(loc,target)
        self.camera.set_actor_location(loc,False,False);self.camera.set_actor_rotation(rot,False)
        self.comp.set_editor_property('projection_type',unreal.CameraProjectionMode.ORTHOGRAPHIC if 'ortho_width'in d else unreal.CameraProjectionMode.PERSPECTIVE)
        if 'ortho_width'in d:self.comp.set_editor_property('ortho_width',d['ortho_width'])
        else:self.comp.set_editor_property('fov_angle',d['fov'])
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc,rot)
        self.current=key;self.last=time.monotonic();self.frames=0
    def export(self,name,directory):
        self.comp.capture_scene();unreal.RenderingLibrary.export_render_target(self.world,self.rt,str(directory),name+'.png')
        rot=self.camera.get_actor_rotation()
        return {'name':name,'file':str(directory/(name+'.png')),'utc':datetime.now(timezone.utc).isoformat(),'world_time_seconds':unreal.GameplayStatics.get_time_seconds(self.world),'camera':CAMS[self.current],'rotation_degrees':{'pitch':rot.pitch,'yaw':rot.yaw,'roll':rot.roll},'warmup_frames':self.frames,'rain_hidden_for_isolation':name.startswith(('water_only','puddle'))}
    def next_still(self):
        name,key=self.views[self.counter];hide=name.startswith(('water_only','puddle'))
        self.rain.set_is_temporarily_hidden_in_editor(hide);self.rain.set_actor_hidden_in_game(hide);self.set_view(key)
    def begin_validation(self):
        self.rain.set_is_temporarily_hidden_in_editor(False);self.rain.set_actor_hidden_in_game(False)
        import validate
        self.result=validate.saved(self.world);ACT.destroy_actor(self.camera)
        LEV.editor_request_begin_play();self.stage='pie';self.last=time.monotonic()
    def save_manifest(self):
        (self.out/'capture_manifest.json').write_text(json.dumps({'source':'Actual UE5.7 SceneCapture2D, no image edits','resolution':[1920,1080],'rhi':'D3D12 SM5','quality':'High / sg2','capture_source':'FinalColorLDR RGBA8 gamma2.2','phase':self.phase,'captures':self.rows},indent=2))
    def tick(self,dt):
        if self.done:return
        try:
            self.frames+=1;elapsed=time.monotonic()-self.last
            assert time.monotonic()-self.begin<240,'Pipeline timeout'
            if self.stage=='warm':
                if elapsed<12 or self.frames<60:return
                self.stage='stills';self.next_still();return
            if self.stage=='stills':
                if elapsed<2.2 or self.frames<12:return
                name,key=self.views[self.counter];self.rows.append(self.export(name,self.out));self.counter+=1;self.save_manifest()
                if self.counter<len(self.views):self.next_still();return
                if not self.validate:self.finish();return
                if self.movie:
                    self.rain.set_is_temporarily_hidden_in_editor(False);self.rain.set_actor_hidden_in_game(False)
                    unreal.RenderingLibrary.resize_render_target2d(self.rt,1280,720)
                    self.movie_group=0;self.movie_frame=0;self.stage='movie_warm';self.set_view('canal');return
                self.begin_validation();return
            if self.stage=='movie_warm':
                if elapsed<2:return
                self.stage='movie';self.last=time.monotonic();return
            if self.stage=='movie':
                if elapsed<.18:return
                group=['canal','rainy_street'][self.movie_group];directory=ROOT/'Motion'/group;directory.mkdir(exist_ok=True)
                row=self.export(f'frame_{self.movie_frame:03d}',directory);row['group']=group;self.movie_rows.append(row);self.movie_frame+=1;self.last=time.monotonic()
                if self.movie_frame<40:return
                if self.movie_group==0:
                    self.movie_group=1;self.movie_frame=0;self.stage='movie_warm';self.set_view('rainy_street');return
                (ROOT/'Motion/capture_manifest.json').write_text(json.dumps({'source':'Actual UE5.7 sequential frame renders','resolution':[1280,720],'frames':self.movie_rows},indent=2))
                self.begin_validation();return
            if self.stage=='pie':
                if elapsed<4:return
                import validate
                game=ED.get_game_world();self.result=validate.runtime(game,self.result)
                LEV.editor_request_end_play();self.stage='ended';self.last=time.monotonic();return
            if self.stage=='ended':
                if elapsed<2:return
                self.result['checks']['pie_ended']=not LEV.is_in_play_in_editor();self.result['utc']=datetime.now(timezone.utc).isoformat();self.result['all_passed']=all(self.result['checks'].values())
                (ROOT/'validation.json').write_text(json.dumps(self.result,indent=2));assert self.result['all_passed'],self.result['checks']
                self.finish();return
        except Exception:
            (ROOT/'Execution'/(self.phase+'_capture_error.txt')).write_text(traceback.format_exc());self.finish(error=True)
    def finish(self,error=False):
        self.done=True
        (ROOT/'Execution'/(self.phase+'_completion.json')).write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'success':not error,'stills':len(self.rows),'movie_frames':len(self.movie_rows),'validated':bool(getattr(self,'result',{}).get('all_passed',False))},indent=2))
        if hasattr(self,'handle'):unreal.unregister_slate_post_tick_callback(self.handle)
        if LEV.is_in_play_in_editor():LEV.editor_request_end_play()
        unreal.EditorPythonScripting.set_keep_python_script_alive(False)
        unreal.SystemLibrary.quit_editor()

def start(phase='draft',validate=False,movie=False):
    global ACTIVE
    ACTIVE=Capture(phase,validate,movie)
