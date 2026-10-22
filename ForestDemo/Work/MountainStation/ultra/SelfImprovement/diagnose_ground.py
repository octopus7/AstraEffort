import unreal as u,json,runpy,traceback
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement')
try:
    assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Maps/MountainStation_ultra')
    checks=runpy.run_path(str(R/'improvement_checks.py'));g,actors,colors=checks['mesh_grids']()
    (R/'terrain_imported_triangles.json').write_text(json.dumps(g['SM_Terrain'][0],separators=(',',':')))
    samples=[]
    for tri in g['SM_Footpath'][0]:
        for w in [(1/3,1/3,1/3),(.5,.5,0),(.5,0,.5),(0,.5,.5)]:
            p=[sum(t[k]*ww for t,ww in zip(tri,w)) for k in range(3)];margin=p[2]-checks['height'](g['SM_Terrain'],p[0],p[1]);samples.append({'point_cm':p,'clearance_cm':margin})
    (R/'ground_discrepancy.json').write_text(json.dumps({'worst_samples':sorted(samples,key=lambda x:x['clearance_cm'])[:20],'samples':len(samples),'below':sum(x['clearance_cm']<0 for x in samples),'colors':colors},indent=2))
except Exception:(R/'ground_probe_error.json').write_text(traceback.format_exc())
u.SystemLibrary.quit_editor()
