from pathlib import Path
import json
from datetime import datetime, timezone

WORK = Path(__file__).resolve().parents[1]
FOREST = WORK.parents[2]
PROJECT = FOREST / 'Saved/Workers/WindmillFarm/max/Project'
for p in (PROJECT/'Config', PROJECT/'Content', WORK/'Evidence', WORK/'Screenshots', WORK/'Source/Models', WORK/'Source/Textures'):
    p.mkdir(parents=True, exist_ok=True)
uproject = {'FileVersion':3,'EngineAssociation':'5.7','Category':'','Description':'Isolated original WindmillFarm/max authoring',
            'Plugins':[{'Name':'PythonScriptPlugin','Enabled':True},{'Name':'EditorScriptingUtilities','Enabled':True},{'Name':'SequencerScripting','Enabled':True}]}
(PROJECT/'WindmillFarmMax.uproject').write_text(json.dumps(uproject,indent=2),encoding='utf-8')
(PROJECT/'Config/DefaultEngine.ini').write_text('''[/Script/EngineSettings.GameMapsSettings]
EditorStartupMap=/Engine/Maps/Entry
GameDefaultMap=/Game/Maps/WindmillFarm_max

[/Script/Engine.RendererSettings]
r.AllowStaticLighting=False
r.DynamicGlobalIlluminationMethod=1
r.ReflectionMethod=1
r.Shadow.Virtual.Enable=1
r.GenerateMeshDistanceFields=True
r.DefaultFeature.AutoExposure=False
r.DefaultFeature.MotionBlur=False
r.AntiAliasingMethod=4

[/Script/WindowsTargetPlatform.WindowsTargetSettings]
DefaultGraphicsRHI=DefaultGraphicsRHI_DX12
+D3D12TargetedShaderFormats=PCD3D_SM6

[SystemSettings]
r.Streaming.PoolSize=2048
r.ScreenPercentage=100

[/Script/Engine.Engine]
bSmoothFrameRate=False
''',encoding='utf-8')
(PROJECT/'Config/DefaultEditor.ini').write_text('''[/Script/UnrealEd.EditorPerformanceSettings]
bThrottleCPUWhenNotForeground=False
''',encoding='utf-8')
p=WORK/'STATUS.json'
s=json.loads(p.read_text(encoding='utf-8'))
s.update(status='working',phase='authoring_original_source',implementation_started=True,blockers=[])
s['implementation_started_at_utc']=datetime.now(timezone.utc).isoformat()
s['private_project']=str(PROJECT/'WindmillFarmMax.uproject')
s['validation_summary']['private_project_created']=True
p.write_text(json.dumps(s,indent=2),encoding='utf-8')
print(PROJECT/'WindmillFarmMax.uproject')
