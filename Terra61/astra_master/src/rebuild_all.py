"""Rebuild shipped static module assets from the included textures/references."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
steps=[['build_architecture.py'],['build_shed.py','--config','modules/shed/texture_config.json'],['build_infrastructure.py'],['build_locomotive.py'],['build_carriage.py'],['build_props.py'],['build_freight_props.py'],['add_tangents.py','modules/**/*.glb'],['assemble_station.py']]
for name,*args in steps:
    subprocess.run([sys.executable,str(root/'src'/name),*args],cwd=root,check=True)
