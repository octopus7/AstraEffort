"""Create only the new content-only WindmillFarm private project."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]/'Saved/Workers/WindmillFarm/ultra/Project'
assert ROOT.as_posix().endswith('/Work/WindmillFarm/ultra')
assert PROJECT.as_posix().endswith('/Saved/Workers/WindmillFarm/ultra/Project')
for p in (PROJECT/'Config',PROJECT/'Content/Maps',PROJECT/'Content/WindmillFarm/ultra',ROOT/'Execution',ROOT/'Screenshots',ROOT/'Art/Landscape',ROOT/'Art/Textures'):
    p.mkdir(parents=True,exist_ok=True)
p=PROJECT/'WindmillFarm.uproject'
assert not p.exists(), 'Do not overwrite an existing private project'
p.write_text(json.dumps({'FileVersion':3,'EngineAssociation':'5.7','Category':'','Description':'Independent WindmillFarm ultra private authoring project','Plugins':[{'Name':'PythonScriptPlugin','Enabled':True},{'Name':'EditorScriptingUtilities','Enabled':True}]},indent=2))
(PROJECT/'Config/DefaultEngine.ini').write_text('''[/Script/EngineSettings.GameMapsSettings]
EditorStartupMap=/Game/Maps/WindmillFarm_ultra
GameDefaultMap=/Game/Maps/WindmillFarm_ultra

[/Script/Engine.RendererSettings]
r.AllowStaticLighting=False
r.DynamicGlobalIlluminationMethod=0
r.ReflectionMethod=0
r.AntiAliasingMethod=2
r.DefaultFeature.AutoExposure=False
r.Shadow.Virtual.Enable=0

[/Script/WindowsTargetPlatform.WindowsTargetSettings]
DefaultGraphicsRHI=DefaultGraphicsRHI_DX12
+D3D12TargetedShaderFormats=PCD3D_SM5
''')
print(PROJECT)
