import unreal as u,importlib.util,json,time,traceback
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max/TextureImprovement');E=ROOT/'Evidence'
u.EditorPythonScripting.set_keep_python_script_alive(True)
try:
 started=time.time();spec=importlib.util.spec_from_file_location('sky_texture_pipeline',str(ROOT/'Source/build_texture_pass.py'));pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
 levels=pipeline.levels;assert levels.load_level(pipeline.MAP);before=pipeline.snapshot();baseline=json.loads((E/'baseline_lighting_cameras.json').read_text());assert before==baseline
 originals=json.loads((E/'texture_source_manifest.json').read_text())['records'];materials=json.loads((E/'material_sampling_manifest.json').read_text())
 vegetation={'Grass','Moss','Leaf','LeafLight'};all_images=pipeline.IMAGE_MAP;pipeline.IMAGE_MAP={n:'moss' for n in vegetation};pipeline.import_images();pipeline.IMAGE_MAP=all_images
 new=json.loads((E/'texture_source_manifest.json').read_text());new['records']=[r for r in originals if r['texture'][2:] not in vegetation]+new['records'];pipeline.write('texture_source_manifest.json',new)
 pipeline.materials(only=vegetation);mnew=json.loads((E/'material_sampling_manifest.json').read_text());mnew['materials']=[r for r in materials['materials'] if r['material'][2:] not in vegetation]+mnew['materials'];pipeline.write('material_sampling_manifest.json',mnew)
 assert before==pipeline.snapshot();assert levels.save_current_level();u.EditorAssetLibrary.save_directory(pipeline.ASSET,only_if_is_dirty=False,recursive=True)
 u.EditorLoadingAndSavingUtils.new_blank_map(False);assert levels.load_level(pipeline.MAP)
 pipeline.write('auxiliary_correction.json',{'started_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(started)),'finished_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'execution_seconds':time.time()-started,'reason':'Replace legacy sine-wave Grass/Leaf stripe source exposed by continuous mapping','new_original':'ImageGen/moss_albedo_original.png','changed_texture_and_materials':sorted(vegetation),'geometry_and_uv_unchanged':True,'lighting_exposure_existing_cameras_unchanged':True})
 exec(compile((ROOT/'Source/validate_capture.py').read_text(encoding='utf-8'),str(ROOT/'Source/validate_capture.py'),'exec'),globals())
except Exception:
 (E/'auxiliary_error.json').write_text(traceback.format_exc());u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
