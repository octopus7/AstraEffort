import unreal as u, traceback,json
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'
try:
    # Extend movable shadows to cover the common overview camera distance.
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);levels.load_level('/Game/Maps/MountainStation_ultra')
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if isinstance(a,u.StaticMeshActor) and a.get_actor_label() in {'Alpine sky backdrop','RailFasteners','RoofSeams','Lettering','StationCladding','StationGlass','Clock','MeadowDetails','Shrubs','Conifers','OutcropMoss','TunnelRibs'}:
            a.static_mesh_component.set_collision_profile_name('NoCollision')
            a.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        if isinstance(a,u.DirectionalLight):
            a.light_component.set_editor_property('dynamic_shadow_distance_movable_light',50000)
            a.light_component.set_editor_property('dynamic_shadow_cascades',4)
    levels.save_current_level()
    exec(compile(open(ROOT+'/run_review.py').read(),ROOT+'/run_review.py','exec'),globals())
except Exception:
    with open(ROOT+'/final_review_error.json','w') as f:json.dump({'traceback':traceback.format_exc()},f,indent=2)
    u.SystemLibrary.quit_editor()
