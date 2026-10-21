from pathlib import Path
import json
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement');OLD=R.parent/'TexturePass'
for name in ['author_uv.py','validate_uv_ue.py','validate_packages.py','runtime_helpers.py','native_and_ramp_checks.py']:
    s=(OLD/name).read_text().replace(str(OLD).replace('\\','/'),str(R).replace('\\','/'))
    if name=='author_uv.py':
        s=s.replace('BASE=R.parent;OUT=', 'BASE=R;OUT=').replace("BASE/'SourceArt/AlderPass.blend'","BASE/'SourceArt/AlderPass_Geometry.blend'")
    if name=='validate_uv_ue.py':
        s=s.replace('assert len(actors)==47','assert len(actors)==48')
        s=s.replace("else:section.update(actual_image_sampler=False,exception='Solid text, clock, glass, emissive surface or tunnel backing; UV geometric density is recorded but image sampling does not apply.')", "else:\n                allowed={s['material'] for mesh in build['meshes'] if mesh['name']==name for s in mesh['slots'] if 'texture_exemption' in s}\n                assert material.get_path_name() in allowed,('Unexpected untextured material',name,material.get_path_name())\n                section.update(actual_image_sampler=False,exception='Explicit original solid/special-material exception')")
        s=s.replace("before=json.loads((R/'scene_before_texture.json').read_text())['actors'];current=[]", "before=json.loads((R/'scene_before_self.json').read_text())['actors'];current=[]")
        s=s.replace("assert sorted(before,key=lambda a:a['label'])==sorted(current,key=lambda a:a['label']),'Actor placement changed'", "allowed_new={'Pedestrian crossing','Tunnel entrance fill','Tunnel inner fill'}\n    preserved=[a for a in current if a['label'] not in allowed_new]\n    assert sorted(before,key=lambda a:a['label'])==sorted(preserved,key=lambda a:a['label']),'Unapproved actor placement changed'\n    assert {a['label'] for a in current}- {a['label'] for a in before}==allowed_new")
        s=s.replace('actor_transforms_unchanged=True','original_actor_transforms_unchanged=True')
    (R/name).write_text(s)
print('Prepared source UV and validation copies under SelfImprovement')
