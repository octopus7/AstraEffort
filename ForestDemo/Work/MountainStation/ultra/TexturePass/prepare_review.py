"""Build standalone review helpers from this assignment's already verified scripts."""
from pathlib import Path
import ast
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass');B=R.parent
src=(B/'validate_unreal.py').read_text();src=src.replace("ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra'","ROOT=r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass'")
(R/'validate_packages.py').write_text(src)
tree=ast.parse((B/'BlockingSupplement/check_blocking.py').read_text());wanted={'utc','v3','distance','path','hit_record','save','inspect_terrain','test_move','play_checks'}
body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in wanted]
(R/'runtime_helpers.py').write_text('import unreal as u,json,datetime,math,traceback\n'+ast.unparse(ast.Module(body=body,type_ignores=[])))
(R/'native_and_ramp_checks.py').write_text((B/'runtime_checks.py').read_text())
