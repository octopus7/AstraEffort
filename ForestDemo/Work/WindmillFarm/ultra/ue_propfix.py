import sys
sys.path.insert(0,'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra')
from ue_common import *
try:
    assert levels.load_level(MAP)
    by_label={a.get_actor_label():a for a in actors.get_all_level_actors()}
    for label,x,y in [('RainBarrel',28.7,13.4),('StackedHayA',18.0,22.0),('StackedHayB',19.25,22.0)]:
        by_label[label].set_actor_location(vec((x*100,-y*100,height(x,y)*100)),False,True)
    b=u.load_asset(BASE+'/Meshes/SM_HayBale').get_bounding_box()
    support=max(by_label[n].get_actor_location().z+b.max.z for n in ('StackedHayA','StackedHayB'))
    by_label['StackedHayTop'].set_actor_location(vec((1862.5,-2200,support-b.min.z)),False,True)
    assert levels.save_current_level()
    save_json('QA/prop_fix.json',{'utc':utc(),'changes':{n:list(by_label[n].get_actor_location().to_tuple()) for n in ('RainBarrel','StackedHayA','StackedHayB','StackedHayTop')}})
    import ue_capture_pipeline
    ue_capture_pipeline.start('Screenshots',True)
except Exception as e:fail(e,'propfix');raise
