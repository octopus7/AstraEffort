from pathlib import Path
root=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement')
s=(root/'capture_after.py').read_text().replace("OUT=ROOT/'Screenshots/After'","OUT=ROOT/'Screenshots/Final'")
begin=s.index('views=[');end=s.index("manifest={'map'",begin)
s=s[:begin]+'''before=json.loads((ROOT/'Screenshots/Before/capture_manifest.json').read_text())
views=[dict(next(v for v in before['views'] if v['name']==name)) for name in ['overview','top_down','lake','beach','tree_detail']]
''' +s[end:]
begin=s.index(" name=view['name'];cmd(");end=s.index(' loc=u.Vector',begin)
s=s[:begin]+" cmd('r.ForestUltra.CanopyRim 1');cmd('r.ForestUltra.CanopyRim.Debug 0')\n"+s[end:]
s=s.replace("warmup=45 if index==0 else (3 if views[index]['name'] in ['water_t1','tree_wind_t1'] else 8)","warmup=25 if index==0 else 8")
(root/'capture_final.py').write_text(s)
(root/'final_pipeline.py').write_text('''import runpy,json,unreal as u
from pathlib import Path
p=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement')
runpy.run_path(str(p/'validate_level.py'),init_globals={'KEEP_EDITOR_OPEN':True})
runpy.run_path(str(p/'validate_final_palette.py'))
if json.loads((p/'validation.json').read_text())['success']:runpy.run_path(str(p/'capture_final.py'))
else:u.SystemLibrary.quit_editor()
''')
print('Final saved-palette validation and five unmodified-camera renders prepared.')
