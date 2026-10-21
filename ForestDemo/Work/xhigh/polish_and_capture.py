import unreal,ast,traceback,json,datetime
try:
 unreal.EditorPythonScripting.set_keep_python_script_alive(True)
 src=ast.parse(open('D:/github/AstraEffort/ForestDemo/Work/xhigh/build_scene.py').read())
 src.body=[n for n in src.body if not isinstance(n,ast.Try)]
 exec(compile(src,'build_scene_functions.py','exec'),globals())
 LES.load_level('/Game/Maps/xhigh')
 for name in ['Terrain','WaterLake','WaterSea']:material(name,DATA['palette'][name])
 sky=next(a for a in EAS.get_all_level_actors() if a.get_actor_label()=='QuietCove_SkyLight')
 prop(sky.light_component,'real_time_capture',False)
 prop(sky.light_component,'source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
 prop(sky.light_component,'cubemap',u.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'))
 prop(sky.light_component,'intensity',.9)
 LES.save_current_level();u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
 summary=json.load(open(ROOT+'/build_summary.json'));summary['previous_environment_saved_at_utc']=summary['utc'];summary['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();summary['visual_fix']='Connected unnamed vertex-color and sine pins; daylight ambient cubemap fill'
 json.dump(summary,open(ROOT+'/build_summary.json','w'),indent=2)
 u.log('XHIGH_VISUAL_FIX_SAVED')
 exec(compile(open(ROOT+'/capture_entry.py').read(),'capture_entry.py','exec'),globals())
except Exception:
 open('D:/github/AstraEffort/ForestDemo/Work/xhigh/polish_error.txt','w').write(traceback.format_exc())
 unreal.log_error(traceback.format_exc());unreal.SystemLibrary.quit_editor()
