from pathlib import Path
import subprocess, shutil, json
ROOT=Path('D:/github/AstraEffort')
WORK=ROOT/'ForestDemo/Work/MountainStation/xhigh'
SCRATCH=ROOT/'ForestDemo/Saved/Workers/MountainStation/xhigh'
PROJECT=SCRATCH/'Project'
PROJECT.mkdir(parents=True,exist_ok=True)
paths=subprocess.check_output(['git','ls-tree','-r','--name-only','7558c8f','--','ForestDemo/Source','ForestDemo/Config','ForestDemo/ForestDemo.uproject'],cwd=ROOT,text=True).splitlines()
for path in paths:
    dst=PROJECT/Path(path).relative_to('ForestDemo')
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_bytes(subprocess.check_output(['git','show',f'7558c8f:{path}'],cwd=ROOT))
shutil.copytree(ROOT/'ForestDemo/Binaries',PROJECT/'Binaries',dirs_exist_ok=True)
p=PROJECT/'Config/DefaultEngine.ini'
s=p.read_text().replace('/Game/Maps/main','/Game/Maps/MountainStation_xhigh')
s+='\n[/Script/Engine.RendererSettings]\nr.AllowStaticLighting=False\nr.DynamicGlobalIlluminationMethod=0\nr.ReflectionMethod=0\nr.DefaultFeature.AutoExposure=False\nr.DefaultFeature.MotionBlur=False\nr.Shadow.Virtual.Enable=0\n'
p.write_text(s)
for name in ['SourceArt','Screenshots','Evidence']:(WORK/name).mkdir(exist_ok=True)
for name in ['Logs','Timings']:(SCRATCH/name).mkdir(exist_ok=True)
print(PROJECT)
