import sys
sys.path.insert(0,'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra')
from ue_common import *
from ue_import import import_file
try:
    m=import_file(ROOT/'Art/Landscape/SM_Ground.fbx',BASE+'/Meshes',True)
    data={'utc':utc(),'ground_bounds':str(m.get_bounding_box()),'uvs':meshes.get_num_uv_channels(m,0),'scene_capture_methods':[x for x in dir(u.SceneCaptureComponent2D) if 'capture' in x or 'post_process' in x],
          'play_methods':[x for x in dir(levels) if 'play' in x], 'editorlibrary_play':[x for x in dir(u.EditorLevelLibrary) if 'play' in x or 'game_world' in x],
          'trace_doc':str(u.SystemLibrary.line_trace_single.__doc__),'request_play_doc':str(getattr(levels,'editor_play_simulate',None)),
          'actor_sweep_doc':str(u.Actor.set_actor_location.__doc__), 'get_game_world_doc':str(u.EditorLevelLibrary.get_game_world.__doc__),
          'rt_formats':str(dir(u.TextureRenderTargetFormat)),'capturesource':str(dir(u.SceneCaptureSource))}
    save_json('api_probe.json',data)
except Exception as e:fail(e,'probe');raise
