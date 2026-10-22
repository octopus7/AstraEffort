"""Create only this task's fresh private project from unthemed runtime support."""
from pathlib import Path
import json, shutil

REPO = Path('D:/github/AstraEffort/ForestDemo')
WORK = REPO / 'Work/HillsideOnsen/ultra'
PRIVATE = REPO / 'Saved/Workers/HillsideOnsen/ultra/Project'
assert 'HillsideOnsen/ultra' in PRIVATE.as_posix()
PRIVATE.mkdir(parents=True, exist_ok=True)
for rel in ['Source', 'Binaries/Win64']:
    shutil.copytree(REPO / rel, PRIVATE / rel, dirs_exist_ok=True)
(PRIVATE / 'Config').mkdir(exist_ok=True)
(PRIVATE / 'Content').mkdir(exist_ok=True)
project = json.loads((REPO / 'ForestDemo.uproject').read_text(encoding='utf-8-sig'))
project['Description'] = 'Private HillsideOnsen ultra authoring project'
project['Plugins'] = [
    {'Name': 'PythonScriptPlugin', 'Enabled': True, 'TargetAllowList': ['Editor']},
    {'Name': 'EditorScriptingUtilities', 'Enabled': True},
    {'Name': 'ProceduralMeshComponent', 'Enabled': True}
]
(PRIVATE / 'ForestDemo.uproject').write_text(json.dumps(project, indent=2), encoding='utf-8')
(PRIVATE / 'Config/DefaultEngine.ini').write_text('''[/Script/EngineSettings.GameMapsSettings]
EditorStartupMap=/Engine/Maps/Entry
GameDefaultMap=/Game/Maps/HillsideOnsen_ultra

[/Script/Engine.RendererSettings]
r.AllowStaticLighting=False
r.DefaultFeature.AutoExposure=False
r.DynamicGlobalIlluminationMethod=1
r.ReflectionMethod=1
r.Shadow.Virtual.Enable=1
r.Nanite.ProjectEnabled=True

[/Script/Engine.Engine]
bSmoothFrameRate=False
''', encoding='utf-8')
for folder in ['SourceArt', 'Textures', 'Logs', 'Screenshots', 'Validation']:
    (WORK / folder).mkdir(exist_ok=True)
print(json.dumps({'private_project': str(PRIVATE / 'ForestDemo.uproject'), 'created': True}))
