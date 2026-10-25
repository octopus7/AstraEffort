import ast
from pathlib import Path
source_path=Path(r'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/max/Scripts/build_scene.py')
tree=ast.parse(source_path.read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.Assign,ast.FunctionDef))],type_ignores=[]),str(source_path),'exec'),globals())
assert LEVEL.load_level(MAP)
materials={n:EAL.load_asset(ROOT+'/Materials/M_'+n) for n in SOURCE['palette']}
for item in SOURCE['meshes']:
    if item['name'] in ['SM_Terrain','SM_Paths']:import_mesh(item,materials)
configure_presentation()
assert LEVEL.save_current_level()
EAL.save_directory(ROOT,only_if_is_dirty=True,recursive=True)
write('terrain_refinement.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'reason':'Preview showed paths clipping into coarse terrain interpolation. Subdivided rounded-rectangle perimeter at <=1.5m before radial surface generation; paths retain4cm offset.','meshes':['SM_Terrain','SM_Paths']})
unreal.log('WINDMILL_TERRAIN_REFINED')
