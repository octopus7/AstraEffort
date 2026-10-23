import sys,traceback
sys.path.insert(0,r'D:/github/AstraEffort/ForestDemo/Work/SnowyOnsen/max/Source')
import build_unreal as b
try:
 assert b.levels.load_level(b.MAP)
 task=b.u.AssetImportTask();task.filename=str(b.SRC/'T_Steam.png');task.destination_path=b.ASSET+'/Textures';task.destination_name='T_Steam';task.automated=True;task.replace_existing=True;task.save=True;b.tools.import_asset_tasks([task])
 m=b.u.load_asset(b.ASSET+'/Materials/M_Water')
 rough=b.MEL.get_material_property_input_node(m,b.u.MaterialProperty.MP_ROUGHNESS);spec=b.MEL.get_material_property_input_node(m,b.u.MaterialProperty.MP_SPECULAR)
 before={'roughness':rough.get_editor_property('r'),'specular':spec.get_editor_property('r')}
 rough.set_editor_property('r',.58);spec.set_editor_property('r',.05)
 b.MEL.recompile_material(m);b.EAL.save_loaded_asset(m);b.levels.save_current_level()
 b.dump('water_material_refinement.json',{'at_utc':b.now(),'before':before,'after':{'roughness':.58,'specular':.05},'reason':'Preserve turquoise readability in exact common overview by reducing broad reflected sky highlight.'})
 b.validate();b.capture()
except Exception:
 b.dump('build_error.json',{'at_utc':b.now(),'traceback':traceback.format_exc()});b.u.log_error(traceback.format_exc());b.u.SystemLibrary.quit_editor()
