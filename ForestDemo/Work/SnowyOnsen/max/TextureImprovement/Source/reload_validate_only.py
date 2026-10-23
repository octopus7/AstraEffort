"""Read-only exact-asset saved-map validation without screenshot/Slate callbacks."""
import sys,json,traceback
sys.dont_write_bytecode=True
sys.path.insert(0,r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max/TextureImprovement/Source')
import build_materials as m
try:
 proof=json.loads((m.PASS/'Validation/captured_asset_snapshot.json').read_text())
 for row in proof['files']:assert m.sha(m.Path(row['private']))==row['sha256'],row['private']
 m.b.validate()
 assert m.sha(m.DISK_MAP)==m.sha(m.BASE_MAP)
 for row in proof['files']:assert m.sha(m.Path(row['private']))==row['sha256'],row['private']
 m.b.dump('fresh_reload_asset_match.json',{'at_utc':m.b.now(),'all_captured_asset_hashes_match':True,'asset_count':len(proof['files']),'map_binary_identical_to_baseline':True,'rendering':'NullRHI validation only; actual image/mip evidence remains full-D3D UE02/03','capture_callbacks_used':False,'source_capture_manifest_sha256':m.sha(m.PASS/'Screenshots/capture_manifest.json'),'status':'passed'})
except Exception:
 m.b.dump('validation_only_error.json',{'at_utc':m.b.now(),'traceback':traceback.format_exc()});m.u.log_error(traceback.format_exc())
m.u.SystemLibrary.quit_editor()
