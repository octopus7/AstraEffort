import unreal as u,json,datetime,traceback
from pathlib import Path
W=Path(r'D:/github/AstraEffort/ForestDemo/Work/NightMarket/max');ROOT='/Game/NightMarket/max';MAP='/Game/Maps/NightMarket_max'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
try:
 levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels.load_level(MAP)
 u.SystemLibrary.execute_console_command(u.EditorLevelLibrary.get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
 source=json.loads((W/'Source'/'source_manifest.json').read_text(encoding='utf-8'));fix=json.loads((W/'Evidence'/'font_winding_correction.json').read_text(encoding='utf-8'));changed={c['mesh'] for c in fix['changed'] if c['flipped_inward_open_glyph_faces']}
 assets=u.AssetToolsHelpers.get_asset_tools();records=[]
 for ent in source['meshes']:
  if ent['name'] not in changed:continue
  t=u.AssetImportTask();t.filename=str(W/'Source'/'Exports'/ent['file']);t.destination_path=ROOT+'/Meshes';t.destination_name=ent['name'];t.automated=True;t.replace_existing=True;t.save=True
  opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.automated_import_should_detect_type=False
  d=opt.static_mesh_import_data;d.combine_meshes=True;d.generate_lightmap_u_vs=False;d.auto_generate_collision=False;d.convert_scene=True;d.convert_scene_unit=True;d.force_front_x_axis=False;d.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
  t.options=opt;t.factory=u.FbxFactory();assets.import_asset_tasks([t]);me=u.load_asset(ROOT+'/Meshes/'+ent['name']);slots=me.get_editor_property('static_materials')
  for i,slot in enumerate(slots):
   key=str(slot.get_editor_property('material_slot_name'));slot.set_editor_property('material_interface',u.load_asset(ROOT+'/Materials/M_NM_'+key));slots[i]=slot
  me.set_editor_property('static_materials',slots);u.EditorAssetLibrary.save_loaded_asset(me)
  records.append({'mesh':me.get_path_name(),'slots':len(slots),'uv_channels':u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_num_uv_channels(me,0)})
 # Bounded camera correction: keep the foreground lantern pole out of alley center.
 cam=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='Capture_alley')
 loc=u.Vector(2550,-2700,480);target=u.Vector(1400,900,340);rot=u.MathLibrary.find_look_at_rotation(loc,target)
 cam.set_actor_location_and_rotation(loc,rot,False,False);cam.get_component_by_class(u.CameraComponent).set_editor_property('field_of_view',65)
 defs=json.loads((W/'Source'/'camera_definitions.json').read_text(encoding='utf-8'))
 for cd in defs:
  if cd['name']=='alley':cd.update({'location':[2550,-2700,480],'target':[1400,900,340],'fov':65,'actual_rotation':[rot.pitch,rot.yaw,rot.roll]})
 (W/'Source'/'camera_definitions.json').write_text(json.dumps(defs,indent=2),encoding='utf-8')
 u.EditorAssetLibrary.save_directory(ROOT,False,True);levels.save_current_level()
 (W/'Evidence'/'targeted_fix_validation.json').write_text(json.dumps({'at_utc':now(),'reimported':records,'alley_camera':{'location_cm':[2550,-2700,480],'target_cm':[1400,900,340],'rotation_deg':[rot.pitch,rot.yaw,rot.roll],'fov':65},'scene_scope_changed':False},indent=2),encoding='utf-8')
 u.SystemLibrary.quit_editor()
except Exception:
 (W/'Evidence'/'targeted_fix_error.json').write_text(json.dumps({'at_utc':now(),'traceback':traceback.format_exc()},indent=2),encoding='utf-8');u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
