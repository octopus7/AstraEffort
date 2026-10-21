from pathlib import Path
import subprocess, shutil, json
repo=Path('D:/github/AstraEffort')
root=repo/'ForestDemo/Saved/Workers/high/ForestDemo'
root.mkdir(parents=True,exist_ok=True)
paths=subprocess.check_output(['git','ls-tree','-r','--name-only','7558c8f','--','ForestDemo/Source','ForestDemo/Config','ForestDemo/ForestDemo.uproject'],cwd=repo,text=True).splitlines()
for p in paths:
    dest=root/Path(p).relative_to('ForestDemo')
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(subprocess.check_output(['git','show',f'7558c8f:{p}'],cwd=repo))
shutil.copytree(repo/'ForestDemo/Binaries',root/'Binaries',dirs_exist_ok=True)
config=root/'Config/DefaultEngine.ini'
s=config.read_text();s=s.replace('/Game/Maps/main','/Game/Maps/high')
s+='\n[/Script/Engine.RendererSettings]\nr.DefaultFeature.AutoExposure=False\nr.DefaultFeature.MotionBlur=False\nr.DynamicGlobalIlluminationMethod=1\nr.ReflectionMethod=1\nr.Shadow.Virtual.Enable=1\n'
config.write_text(s)
(root/'Content/Forest/high').mkdir(parents=True,exist_ok=True)
(root/'Content/Maps').mkdir(parents=True,exist_ok=True)
print(root)
