"""Preserve narrow pine-tip UV triangles in UE's built vertex buffer."""
import unreal as u,json,datetime,os
PP='D:/github/AstraEffort/ForestDemo/Work/xhigh/TexturePass'
ss=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);changes=[]
for name in ['SM_Pine_0','SM_Pine_1']:
 mesh=u.load_asset('/Game/Forest/xhigh/Meshes/'+name)
 settings=ss.get_lod_build_settings(mesh,0)
 before=settings.get_editor_property('use_full_precision_u_vs')
 if not before:
  settings.set_editor_property('use_full_precision_u_vs',True);ss.set_lod_build_settings(mesh,0,settings);u.EditorAssetLibrary.save_loaded_asset(mesh)
  changes.append(name)
if changes:
 u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
 json.dump({'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'changed_meshes':changes,'reason':'UE half-precision built UV buffer collapsed three narrow SM_Pine_0 tip triangles; their world geometry area is positive. Retain full precision UVs on both pine variants. A fresh reload and roundtrip is required after this repair.','requires_fresh_reload':True},open(PP+'/precision_repair.json','w'),indent=2)
u.log('XHIGH_UV_PRECISION_REPAIR '+str(changes))
