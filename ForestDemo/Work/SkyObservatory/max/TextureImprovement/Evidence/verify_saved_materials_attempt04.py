import unreal as u
import json,time,traceback,hashlib
from pathlib import Path

ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max/TextureImprovement')
E=ROOT/'Evidence'
CONTENT=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/SkyObservatory/max/Project/Content')
ASSET='/Game/SkyObservatory/max'
MAP='/Game/Maps/SkyObservatory_max'
u.EditorPythonScripting.set_keep_python_script_alive(True)
started=time.time()
def stamp():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def files():
    return [{'relative_path':p.relative_to(CONTENT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'modified_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(p.stat().st_mtime))} for p in sorted(CONTENT.rglob('*')) if p.is_file()]
try:
    before=files();assert len(before)==60
    # Reuse the established saved-map validator, excluding its capture state machine.
    prefix=(ROOT/'Source/validate_capture.py').read_text(encoding='utf-8').split('\ntry:\n assert levels.load_level(MAP)')[0]
    scope={};exec(compile(prefix,'validate_capture.py [validation definitions only]','exec'),scope)
    assert scope['levels'].load_level(MAP)
    graph=scope['validate']()
    materials=[]
    for path in sorted(u.EditorAssetLibrary.list_assets(ASSET+'/Materials',recursive=True,include_folder=False)):
        mat=u.load_asset(path);assert mat
        # Installed UE5.7 implementation submits incomplete compile jobs and calls
        # FinishCompilation before collecting the actual material resource stats.
        stats=u.MaterialEditingLibrary.get_statistics(mat)
        values={k:stats.get_editor_property(k) for k in ['num_vertex_shader_instructions','num_pixel_shader_instructions','num_samplers','num_vertex_texture_samples','num_pixel_texture_samples','num_virtual_texture_samples','num_uv_scalars','num_interpolator_scalars']}
        assert values['num_pixel_shader_instructions']>0,(path,values)
        assert values['num_samplers']>0 and values['num_pixel_texture_samples']>0,(path,values)
        textures=sorted(t.get_path_name() for t in u.MaterialEditingLibrary.get_used_textures(mat))
        assert textures and all(t.startswith(ASSET+'/Textures/') for t in textures)
        materials.append({'material':path,'statistics':values,'used_textures':textures})
    assert len(materials)==21
    after=files();assert before==after,'Read-only validation must preserve captured asset bytes'
    captures=json.loads((ROOT/'Screenshots/capture_manifest.json').read_text())
    for c in captures['captures']:
        assert hashlib.sha256((ROOT/'Screenshots'/c['file']).read_bytes()).hexdigest()==c['sha256']
    report={'validated_at_utc':stamp(),'validation_seconds':time.time()-started,'fresh_saved_map_loaded':True,'recursive_graph_packages':graph['graph_packages'],'all_21_materials_have_compiled_shader_statistics':True,'materials':materials,'read_only_no_asset_save_or_mutation':True,'private_package_hashes_before_after_equal':True,'package_count':len(after),'packages':after,'captured_images_sha256_verified':True,'capture_manifest_sha256':hashlib.sha256((ROOT/'Screenshots/capture_manifest.json').read_bytes()).hexdigest(),'compilation_method':'UE5.7 MaterialEditingLibrary.GetStatistics: submit missing shader jobs, FinishCompilation, inspect actual active RHI material resource; no graph editing or asset saving'}
    (E/'saved_material_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.log('FINAL_SAVED_MATERIAL_VALIDATION_PASS 21 compiled materials; 60 unchanged packages; 6 captured image hashes')
except Exception:
    (E/'saved_material_validation_error.json').write_text(json.dumps({'utc':stamp(),'traceback':traceback.format_exc()},indent=2),encoding='utf-8')
    u.log_error(traceback.format_exc())
finally:
    u.SystemLibrary.quit_editor()
