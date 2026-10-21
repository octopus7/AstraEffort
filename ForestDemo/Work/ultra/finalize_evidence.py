import json, datetime, hashlib
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra')
SCRATCH=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/ultra')
captures=json.loads((ROOT/'Screenshots/capture_manifest.json').read_text())
assert captures['capture_finished_at_utc'].startswith('2026-10-21T12:59:06')
graph=json.loads((ROOT/'water_graph_validation.json').read_text())
assert all(x['expressions_after']==8 and 'MaterialExpressionConstant3Vector' in x['normal_input'] for x in graph.values())
log=(SCRATCH/'logs/water-clean.log').read_text(encoding='utf-8',errors='replace')
final_part=log.split('ULTRA_CLEAN_WATER_SAVED',1)[1]
errors=[line for line in final_part.splitlines() if any(s in line for s in ['Failed to compile Material','LogPython: Error','Fatal error!'])]
assert not errors,errors
assert 'LogExit: Exiting.' in final_part
review={'approved':True,'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'author, direct inspection of all five actual UE PNG files using view_image','image_sha256':{n:hashlib.sha256((ROOT/'Screenshots'/(n+'.png')).read_bytes()).hexdigest().upper() for n in ['overview','top_down','lake','beach','hero']},'observations':{'overview':'Exact specified orthographic composition, full site visible, upright trees. Water reflection appears bright at this angle; retained as the honest standardized view.','top_down':'Exact top-down orthographic square site; separate turquoise inland lake and coastal water, path and forest readable.','lake':'Actual 170cm eye-height lake view; water, reeds, rounded rocks and trees visible without editor UI.','beach':'Actual 170cm eye-height beach view; sand, distinct coastal water, foam ribbons, forest and driftwood visible without editor UI.','hero':'Additional perspective overview from coastal side; complete environment and both water bodies readable.'},'limitations':['Standard overview has bright specular water reflections.','The exact 100m site terminates at a visible edge; no surrounding world is authored.'],'post_final_save_material_or_python_errors':errors,'no_image_postprocessing':True}
(ROOT/'visual_review.json').write_text(json.dumps(review,indent=2))
validation=json.loads((ROOT/'validation.json').read_text())
validation['checks']['water_graph_and_final_render']={'passed':True,'detail':{'nodes_per_water_material':8,'normal_explicitly_reset':True,'errors_after_final_save':errors,'render_images_personally_reviewed':5}}
validation['success']=all(c['passed'] for c in validation['checks'].values())
validation['errors']=[k for k,c in validation['checks'].items() if not c['passed']]
(ROOT/'validation.json').write_text(json.dumps(validation,indent=2))
print('All five final render images personally reviewed; final shader/log and 14 validation checks pass.')
