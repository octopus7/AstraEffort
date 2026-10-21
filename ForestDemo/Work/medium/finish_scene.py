import unreal as u,traceback,os
error_file='D:/github/AstraEffort/ForestDemo/Work/medium/capture_error.txt'
if os.path.exists(error_file):os.remove(error_file)
try:
 ss=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
 for name in ['Tree0','Tree1','Tree2','Rock0','Rock1','Rock2','Shrub0','Shrub1','Log']:
  mesh=u.load_asset('/Game/Forest/medium/Meshes/'+name)
  if (ss.get_simple_collision_count(mesh)+ss.get_convex_collision_count(mesh))==0:
   ss.add_simple_collisions(mesh,u.ScriptCollisionShapeType.NDOP26)
  assert (ss.get_simple_collision_count(mesh)+ss.get_convex_collision_count(mesh))>0,name
  u.EditorAssetLibrary.save_loaded_asset(mesh)
 exec(open('D:/github/AstraEffort/ForestDemo/Work/medium/validate_capture.py').read())
except Exception:
 open('D:/github/AstraEffort/ForestDemo/Work/medium/capture_error.txt','w').write(traceback.format_exc())
 u.SystemLibrary.quit_editor()


