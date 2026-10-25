import unreal,sys,json,traceback
from pathlib import Path
P=Path('D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra');sys.path.insert(0,str(P));import assemble
try:
    assert assemble.LEV.load_level(assemble.MAP)
    o=unreal.FbxImportUI();o.set_editor_property('import_mesh',True);o.set_editor_property('import_materials',False);o.set_editor_property('import_textures',False);o.set_editor_property('import_as_skeletal',False);o.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_STATIC_MESH)
    d=o.static_mesh_import_data;d.set_editor_property('combine_meshes',True);d.set_editor_property('generate_lightmap_u_vs',False);d.set_editor_property('auto_generate_collision',False);d.set_editor_property('transform_vertex_to_absolute',True)
    mesh=assemble.task(P/'Art/Landscape/FBX/SM_QuayWall.fbx',assemble.ASSET+'/Meshes',o);mesh.set_material(0,unreal.load_asset(assemble.ASSET+'/Materials/M_Stone'));mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    assemble.LEV.save_current_level()
    (P/'Execution/wallfix_saved.json').write_text(json.dumps({'saved':True,'wall_notch_top_cm':-12,'timber_deck_top_cm':0}))
except Exception:
    (P/'Execution/wallfix_error.txt').write_text(traceback.format_exc());raise
