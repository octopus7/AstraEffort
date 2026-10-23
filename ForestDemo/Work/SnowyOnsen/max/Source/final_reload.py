import sys,traceback,hashlib
sys.path.insert(0,r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max/Source')
import build_unreal as b
try:
 assert b.levels.load_level(b.MAP)
 task=b.u.AssetImportTask();task.filename=str(b.SRC/'T_Steam.png');task.destination_path=b.ASSET+'/Textures';task.destination_name='T_Steam';task.automated=True;task.replace_existing=True;task.save=True;b.tools.import_asset_tasks([task])
 b.EAL.save_directory(b.ASSET,only_if_is_dirty=True,recursive=True);b.levels.save_current_level()
 b.validate()
 sources=[]
 for p in b.EAL.list_assets(b.ASSET+'/Textures',recursive=True,include_folder=False):
  tex=b.u.load_asset(p);imp=tex.get_editor_property('asset_import_data');files=[str(x) for x in imp.extract_filenames()];checks=[]
  for file in files:
   fp=b.Path(file).resolve();assert str(fp).replace('\\','/').startswith(str(b.SRC).replace('\\','/'));checks.append({'file':str(fp),'sha256':hashlib.sha256(fp.read_bytes()).hexdigest()})
  sources.append({'asset':p,'source_files':checks,'size':[tex.blueprint_get_size_x(),tex.blueprint_get_size_y()]})
 assert len(sources)==12;b.dump('texture_import_sources.json',{'at_utc':b.now(),'textures':sources,'status':'passed'})
 b.capture()
except Exception:
 b.dump('build_error.json',{'at_utc':b.now(),'traceback':traceback.format_exc()});b.u.log_error(traceback.format_exc());b.u.SystemLibrary.quit_editor()
