import sys,time,shutil,json
sys.path.insert(0,'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass')
import capture_vegetation as cv
from ue_common import *

class LateOverview(cv.base.Pipeline):
    def __init__(self):
        super().__init__('VegetationPass/OverviewRecapture',False)
        self.names=['corn','meadow','overview'];self.set_camera('corn');self.deadline=time.monotonic()+15
    def finish(self):
        u.unregister_slate_post_tick_callback(self.handle)
        save_json(self.output+'/capture_manifest.json',self.manifest)
        source=ROOT/self.output/'overview.png';target=ROOT/'VegetationPass/Screenshots/overview.png'
        assert source.is_file();shutil.copy2(source,target)
        p=ROOT/'VegetationPass/Screenshots/capture_manifest.json';manifest=json.loads(p.read_text())
        entry=next(r for r in self.manifest['captures'] if r['name']=='overview');entry['file']=str(target)
        manifest['captures']=[entry if r['name']=='overview' else r for r in manifest['captures']]
        manifest['overview_recapture']='Same overview camera, captured after close corn and meadow views to settle visible material resources.'
        p.write_text(json.dumps(manifest,indent=2))
        save_json('VegetationPass/overview_recapture_validation.json',{'utc':utc(),'checks':self.checks,'detail':self.detail})
        u.SystemLibrary.quit_editor()

try:PIPELINE=LateOverview()
except Exception as e:fail(e,'VegetationPass/overview');u.SystemLibrary.quit_editor()
