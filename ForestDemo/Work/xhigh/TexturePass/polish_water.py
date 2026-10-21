import unreal as u,ast,json,datetime,traceback
try:
 tree=ast.parse(open('D:/github/AstraEffort/ForestDemo/Work/xhigh/TexturePass/apply_textures.py').read())
 tree.body=[n for n in tree.body if not isinstance(n,ast.Try)]
 exec(compile(tree,'texture_material_functions','exec'),globals())
 textures={n:u.load_asset(DEST+'/Textures/T_IG_'+n) for n in ['bark','foliage','stone','wood','caustics']}
 LES.load_level('/Game/Maps/xhigh')
 ground_material(textures);water_material('WaterSea');water_material('WaterLake');foam_material()
 LES.save_current_level();u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
 report=json.load(open(PHASE+'/build_summary.json'));report['water_polish_finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['water_polish']='Reduced and depth-attenuated caustic intensity; stronger translucent water tint; feathered broken foam opacity.'
 json.dump(report,open(PHASE+'/build_summary.json','w'),indent=2);u.log('XHIGH_WATER_POLISH_COMPLETE')
except Exception:
 open('D:/github/AstraEffort/ForestDemo/Work/xhigh/TexturePass/polish_error.txt','w').write(traceback.format_exc());u.log_error(traceback.format_exc())
finally:u.SystemLibrary.quit_editor()
