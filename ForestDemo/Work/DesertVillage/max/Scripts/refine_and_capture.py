import runpy, traceback
from pathlib import Path
ns=runpy.run_path(r'D:/github/AstraEffort/ForestDemo/Work/DesertVillage/max/Scripts/build_unreal.py',run_name='desert_helpers')
globals().update(ns)
try:
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    for desc in MAN['meshes']:
        name=desc['name'];mesh=import_one(ROOT/'SourceArt/FBX'/(name+'.fbx'),ASSET+'/Meshes',name,True)
        for i,slot in enumerate(mesh.static_materials):
            mesh.set_material(i,EA.load_asset(ASSET+'/Materials/M_'+str(slot.material_slot_name)))
        EA.save_loaded_asset(mesh)
    levels.load_level(MAP);levels.save_current_level();levels.load_level(MAP);validate()
    cams={a.get_actor_label()[7:]:a for a in actors.get_all_level_actors() if isinstance(a,u.CameraActor)}
    begin_capture(cams)
except Exception:
    record('refine_error.json',{'at_utc':utc(),'error':traceback.format_exc()});u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
