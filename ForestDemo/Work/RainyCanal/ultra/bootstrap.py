from pathlib import Path
from datetime import datetime, timezone
import json

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
SCRATCH=REPO/'ForestDemo/Saved/Workers/RainyCanal/ultra'
PROJECT=SCRATCH/'Project'
assert ROOT.as_posix().endswith('/Work/RainyCanal/ultra')
assert not (PROJECT/'RainyCanal.uproject').exists(), 'Fresh bootstrap must not overwrite an existing project'
for sub in ('Content','Config','Saved'):
    (PROJECT/sub).mkdir(parents=True,exist_ok=True)
for sub in ('Execution','QA','Screenshots','Motion','Art/Landscape'):
    (ROOT/sub).mkdir(parents=True,exist_ok=True)
(PROJECT/'RainyCanal.uproject').write_text(json.dumps({'FileVersion':3,'EngineAssociation':'5.7','Category':'','Description':'Independent RainyCanal ultra scratch','Plugins':[{'Name':'PythonScriptPlugin','Enabled':True},{'Name':'EditorScriptingUtilities','Enabled':True}]},indent=2))
(PROJECT/'Config/DefaultEngine.ini').write_text('''[/Script/Engine.RendererSettings]
r.DefaultFeature.AutoExposure=False
r.DefaultFeature.MotionBlur=False
r.GenerateMeshDistanceFields=False
r.DynamicGlobalIlluminationMethod=0
r.ReflectionMethod=2
r.Shadow.Virtual.Enable=0
r.AllowStaticLighting=False
r.AntiAliasingMethod=2

[/Script/WindowsTargetPlatform.WindowsTargetSettings]
DefaultGraphicsRHI=DefaultGraphicsRHI_DX12
+D3D12TargetedShaderFormats=PCD3D_SM5
''')
status={'theme':'RainyCanal','effort':'ultra','status':'working','started_at_utc':'2026-10-22T14:53:36+00:00','started_at_kst':'2026-10-22T23:53:36+09:00','timing_note':'First explicit clock reading after assignment inspection; initial reading preceded this timestamp. Operational record, excluded from comparisons.','finished_at_utc':None,'map':'/Game/Maps/RainyCanal_ultra','phase':'Original source production and fresh private project','comparison_excluded':True,'validation_summary':'Not yet validated','blockers':[]}
(ROOT/'STATUS.json').write_text(json.dumps(status,indent=2))
print(PROJECT/'RainyCanal.uproject')
