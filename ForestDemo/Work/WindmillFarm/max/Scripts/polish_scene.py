"""Reuses this assignment's material helpers without repeating geometry import."""
from pathlib import Path
import ast
source_path=Path(r'D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/max/Scripts/build_scene.py')
tree=ast.parse(source_path.read_text(encoding='utf-8'))
definitions=[node for node in tree.body if isinstance(node,(ast.Import,ast.ImportFrom,ast.Assign,ast.FunctionDef))]
exec(compile(ast.Module(body=definitions,type_ignores=[]),str(source_path),'exec'),globals())
assert LEVEL.load_level(MAP)
textures={n:EAL.load_asset(ROOT+'/Textures/T_'+Path(n).stem) for n in SOURCE['textures']}
pivot=[q*100 for q in SOURCE['rotor_pivot_m']]
for name,palette in SOURCE['palette'].items():make_material(name,palette,textures,pivot)
configure_presentation()
assert LEVEL.save_current_level()
EAL.save_directory(ROOT,only_if_is_dirty=False,recursive=True)
write('presentation_polish.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'texture_contrast_weight':.28,'sun_pitch_yaw':[-48,135],
    'sky_fill':'Engine built-in DaylightAmbientCubemap at intensity1','background':'Own unlit sky material on Engine sphere; presentation environment outside the 100x100m farm footprint',
    'windmill_camera_cm':[-650,-1750,1250],'warnings':WARN})
unreal.log('WINDMILL_PRESENTATION_POLISHED')
