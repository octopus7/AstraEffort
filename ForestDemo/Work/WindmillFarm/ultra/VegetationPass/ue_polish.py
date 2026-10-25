import sys,time
sys.path.insert(0,'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass')
sys.path.insert(0,'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra')
from ue_common import *
import capture_vegetation as cv

class WithMovies(cv.VegetationPipeline):
    def __init__(self):
        self.movies_started=False;self.movie_manifest={'source':'Actual UE5.7 SceneCapture2D sequential frames; no generated imagery','resolution':[1280,720],'groups':{},'utc_started':utc()}
        super().__init__()
    def finish(self):
        if self.movies_started:
            save_json('VegetationPass/Motion/capture_manifest.json',self.movie_manifest)
            super().finish();return
        self.movies_started=True;self.movie_group=0;self.movie_index=0
        self.movie_rt=u.RenderingLibrary.create_render_target2d(self.world,1280,720,u.TextureRenderTargetFormat.RTF_RGBA8,u.LinearColor(0,0,0,1),False)
        self.movie_rt.set_editor_property('target_gamma',2.2);self.c.set_editor_property('texture_target',self.movie_rt);self.c.set_editor_property('capture_every_frame',True)
        self.begin_movie()
    def begin_movie(self):
        self.group=('corn','meadow')[self.movie_group];self.set_camera(self.group)
        self.movie_dir=ROOT/'VegetationPass/Motion'/self.group;self.movie_dir.mkdir(parents=True,exist_ok=True)
        self.movie_manifest['groups'][self.group]={'camera':self.cfg,'rotation_degrees':self.rotation,'frames':[]}
        self.state='movie';self.deadline=time.monotonic()+1.5
    def tick(self,delta):
        if self.state!='movie':return super().tick(delta)
        try:
            if time.monotonic()<self.deadline:return
            name='frame_%03d.png'%self.movie_index
            u.RenderingLibrary.export_render_target(self.world,self.movie_rt,str(self.movie_dir),name)
            self.movie_manifest['groups'][self.group]['frames'].append({'file':name,'utc':utc(),'world_time_seconds':u.GameplayStatics.get_time_seconds(self.world)})
            self.movie_index+=1
            if self.movie_index==32:
                self.movie_group+=1;self.movie_index=0
                if self.movie_group==2:self.finish()
                else:self.begin_movie()
            else:self.deadline=time.monotonic()+.12
        except Exception as e:
            fail(e,'VegetationPass/movie');self.checks['motion_clip_capture']=False;self.finish()

try:
    for name in ('SM_MeadowTall','SM_MeadowPlume','SM_MeadowReed'):
        sm=u.load_asset(BASE+'/Meshes/'+name)
        for prop in ('positive_bounds_extension','negative_bounds_extension'):sm.set_editor_property(prop,vec((40,40,5)))
        u.EditorAssetLibrary.save_loaded_asset(sm)
    PIPELINE=WithMovies()
except Exception as e:
    fail(e,'VegetationPass/polish');u.SystemLibrary.quit_editor()
