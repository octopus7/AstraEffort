import unreal as u,json,datetime,traceback
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/TexturePass')
eas=u.get_editor_subsystem(u.EditorAssetSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem);ml=u.MaterialEditingLibrary
try:
 levels.load_level('/Game/Maps/ultra');mat=eas.load_asset('/Game/Forest/ultra/Materials/M_Sea');base=ml.get_material_property_input_node(mat,u.MaterialProperty.MP_BASE_COLOR)
 code=base.get_editor_property('code')
 code=code.replace('return lerp(float3(.045,.28,.32)', 'float cellular=.50+.23*sin(P.x*.071+P.y*.027+T*.55)+.20*sin(P.x*.043-P.y*.058-T*.8)+.07*sin(P.x*.19+P.y*.13);foam*=smoothstep(.35,.68,cellular);return lerp(float3(.045,.28,.32)')
 assert 'cellular' in code;base.set_editor_property('code',code);ml.recompile_material(mat);eas.save_loaded_asset(mat)
 for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  if isinstance(actor,u.StaticMeshActor) and actor.static_mesh_component.static_mesh.get_name()=='SM_Surf':
   actor.static_mesh_component.set_visibility(False);actor.set_actor_hidden_in_game(True);actor.static_mesh_component.set_cast_shadow(False)
 levels.save_current_level()
 (ROOT/'foam_refinement.json').write_text(json.dumps({'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Final beach inspection still showed long parallel bands and thin dashed ribbons. The final sea crest foam uses irregular animated cellular breakup; legacy thin ribbons are hidden in editor rendering and runtime. White foam is part of the actual water material and cannot cast floating shadows.','success':True},indent=2))
except Exception:(ROOT/'foam_refinement_error.txt').write_text(traceback.format_exc());raise
finally:u.SystemLibrary.quit_editor()
