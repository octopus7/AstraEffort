import runpy,traceback
ns=runpy.run_path(r'D:/github/AstraEffort/ForestDemo/Work/DesertVillage/max/Scripts/build_unreal.py',run_name='desert_helpers');globals().update(ns)
try:
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    for name in ['SM_CaravanseraiArchitecture','SM_DoorsWindowsAndBeams','SM_MarketTimberAndStalls','SM_CratesAndCaravanCargo','SM_CommunityWell','SM_LanternsBenchesAndSigns']:
        mesh=import_one(ROOT/'SourceArt/FBX'/(name+'.fbx'),ASSET+'/Meshes',name,True)
        for i,slot in enumerate(mesh.static_materials):mesh.set_material(i,EA.load_asset(ASSET+'/Materials/M_'+str(slot.material_slot_name)))
        EA.save_loaded_asset(mesh)
    levels.load_level(MAP)
    for a in actors.get_all_level_actors():
        if isinstance(a,u.DirectionalLight):
            a.set_actor_rotation(u.Rotator(pitch=-48,yaw=135,roll=0),False);lc=a.get_component_by_class(u.DirectionalLightComponent);lc.set_intensity(3.8);lc.set_light_color(u.LinearColor(1,.90,.77,1))
        if a.get_actor_label()=='Camera_top_down':a.set_actor_rotation(u.Rotator(pitch=-90,yaw=0,roll=0),False)
        if a.get_actor_label()=='Camera_plaza':
            a.set_actor_location(u.Vector(1900,-2500,900),False,False);a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(a.get_actor_location(),u.Vector(200,-300,240)),False);a.camera_component.field_of_view=58
    levels.save_current_level();levels.load_level(MAP);validate()
    cams={a.get_actor_label()[7:]:a for a in actors.get_all_level_actors() if isinstance(a,u.CameraActor)};begin_capture(cams)
except Exception:
    record('polish_error.json',{'at_utc':utc(),'error':traceback.format_exc()});u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
