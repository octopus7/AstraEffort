import unreal as u,json,time,traceback,importlib.util
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max');ASSET='/Game/SkyObservatory/max';MAP='/Game/Maps/SkyObservatory_max'
u.EditorPythonScripting.set_keep_python_script_alive(True)
try:
 spec=importlib.util.spec_from_file_location('sky_pipeline',str(ROOT/'Source/build_unreal.py'));pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
 mats={p.stem[2:]:u.load_asset(ASSET+'/Materials/M_'+p.stem[2:]) for p in (ROOT/'SourceArt/Textures').glob('T_*.png')}
 pipeline.import_meshes(mats)
 levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem);assert levels.load_level(MAP)
 changes=[]
 for a in actors.get_all_level_actors():
  name=a.get_actor_label()
  if name=='Dusk_Warm_Key':a.get_component_by_class(u.DirectionalLightComponent).set_intensity(18.0);changes.append([name,18])
  if name=='Moon_Cool_Fill':a.get_component_by_class(u.DirectionalLightComponent).set_intensity(3.0);changes.append([name,3])
  if name=='Dusk_Ambient':a.get_component_by_class(u.SkyLightComponent).set_intensity(1.3);changes.append([name,1.3])
  if name.startswith('Warm_Lantern_Pool_'):a.get_component_by_class(u.PointLightComponent).set_intensity(250);changes.append([name,250])
  if name=='Calm_Dusk_Grade':
   settings=a.get_editor_property('settings');settings.set_editor_property('auto_exposure_bias',1.0);a.set_editor_property('settings',settings)
  if name=='Capture_overview':
   r=a.get_actor_rotation();a.set_actor_rotation(u.Rotator(pitch=r.pitch,yaw=r.yaw,roll=0),False)
 cloud=mats['Cloud'];tex=u.load_asset(ASSET+'/Textures/T_Cloud')
 node=u.MaterialEditingLibrary.create_material_expression(cloud,u.MaterialExpressionTextureSample,-500,-250);node.texture=tex
 mult=u.MaterialEditingLibrary.create_material_expression(cloud,u.MaterialExpressionMultiply,-200,-250);mult.set_editor_property('const_b',1.0)
 u.MaterialEditingLibrary.connect_material_expressions(node,'RGB',mult,'A');u.MaterialEditingLibrary.connect_material_property(mult,'',u.MaterialProperty.MP_EMISSIVE_COLOR);u.MaterialEditingLibrary.recompile_material(cloud);u.EditorAssetLibrary.save_loaded_asset(cloud)
 assert levels.save_current_level();u.EditorAssetLibrary.save_directory(ASSET,only_if_is_dirty=False,recursive=True)
 (ROOT/'Evidence/correction_changes.json').write_text(json.dumps({'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'lighting_changes':changes,'exposure_bias':1.0,'cloud_emissive_texture_multiplier':1.0,'mesh_transform':'Y mirrored and winding reversed in exported FBX; actor scale remains +1,+1,+1'},indent=2))
 u.EditorLoadingAndSavingUtils.new_blank_map(False);assert levels.load_level(MAP)
 exec(compile((ROOT/'Source/validate_capture.py').read_text(encoding='utf-8'),str(ROOT/'Source/validate_capture.py'),'exec'),globals())
except Exception:
 (ROOT/'Evidence/correction_error.json').write_text(traceback.format_exc());u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
