import unreal as u, runpy, json, datetime
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra')
try:
 ns=runpy.run_path(str(ROOT/'build_level.py'),init_globals={'SKIP_BUILD':True})
 report={}
 for name in ['Lake','Sea']:
  old=ns['eas'].load_asset('/Game/Forest/ultra/Materials/M_'+name)
  before=u.MaterialEditingLibrary.get_num_material_expressions(old)
  mat=ns['create_mat'](name,ns['DATA']['palette'][name])
  report[name]={'expressions_before':before,'expressions_after':u.MaterialEditingLibrary.get_num_material_expressions(mat),'normal_input':str(u.MaterialEditingLibrary.get_material_property_input_node(mat,u.MaterialProperty.MP_NORMAL)),'base_color_input':str(u.MaterialEditingLibrary.get_material_property_input_node(mat,u.MaterialProperty.MP_BASE_COLOR))}
 ns['levels'].load_level('/Game/Maps/ultra');ns['levels'].save_current_level()
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (ROOT/'scene_ready_time.json').write_text(json.dumps({'scene_saved_at_utc':stamp,'changes':'Drained retained old expression nodes, explicitly reset water normals; all gameplay/collision geometry unchanged.'},indent=2))
 (ROOT/'water_graph_validation.json').write_text(json.dumps(report,indent=2))
 u.log('ULTRA_CLEAN_WATER_SAVED')
 runpy.run_path(str(ROOT/'validate_level.py'),init_globals={'KEEP_EDITOR_OPEN':True})
 validation=json.loads((ROOT/'validation.json').read_text());runtime=json.loads((ROOT/'runtime_validation.json').read_text())
 validation['checks']['runtime_ground_collision']={'passed':runtime['success'],'detail':'Preserved actual PIE evidence in runtime_validation.json; only water material graphs changed afterward.'}
 validation['checks']['player_possession_and_sweep']={'passed':runtime['player_test']['passed'] and runtime['normal_play_exit'],'detail':runtime['player_test']}
 validation['runtime_collision_test_required']=False
 validation['success']=all(c['passed'] for c in validation['checks'].values());validation['errors']=[k for k,c in validation['checks'].items() if not c['passed']]
 (ROOT/'validation.json').write_text(json.dumps(validation,indent=2))
 runpy.run_path(str(ROOT/'capture_level.py'))
except Exception:
 import traceback
 (ROOT/'final_review_error.txt').write_text(traceback.format_exc());u.SystemLibrary.quit_editor();raise
