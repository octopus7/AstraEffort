"""Append one main-selected three-set group after the prior delivery commit."""
from pathlib import Path
from datetime import datetime, timezone
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
state_path=ROOT/'Blender/SET_BATCH_STATE.json'
state=json.loads(state_path.read_text(encoding='utf-8'))
spec_path=Path(sys.argv[1]).resolve()
assert spec_path.is_relative_to(ROOT/'Blender/BatchTools')
spec=json.loads(spec_path.read_text(encoding='utf-8'))
number=spec['batch']
assert state.get('continuation_mode')=='until_user_stop'
assert number==len(state['batches'])+1 and number>=4
assert (ROOT/f'Blender/BatchTools/scratch/batch{number-1}_commit.json').is_file()
assert len(spec['sets'])==3
expected_first=max(int(n[3:]) for n in state['sets'])+1
assert [s['name'] for s in spec['sets']]==[f'Set{i:02}' for i in range(expected_first,expected_first+3)]
slugs={a['slug'] for s in state['sets'].values() for a in s['assets']}
for item in spec['sets']:
    name=item['name']
    assert len(item['assets'])==4 and name not in state['sets']
    assert not (ROOT/'Blender'/name).exists() and not (ROOT/'REF'/name).exists()
    for asset in item['assets']:
        slug=asset['slug']
        assert re.fullmatch(r'[a-z][a-z0-9_]+',slug) and slug not in slugs
        slugs.add(slug)
        assert asset['label'] and asset['description']

common=('Use case: stylized-concept.\n'
 'Asset type: one original design reference image for one editable rounded 3D game asset (ordinary smooth/beveled mesh, NOT voxels).\n'
 'Style: calm mature-friendly game art with broad simplified shapes and rounded corners. Preserve recognizable functional structure. Express friendliness through softened form and proportion, without childish ornamentation.\n'
 'Composition: a single fully visible isolated object in orthographic front three-quarter view, generous margins, neutral pale studio background, soft lighting. No people, text, labels, logos, watermark, faces, hearts, clouds, smileys, sharp decorative spikes or shared diorama slab. Functional mechanical details should be thick, legible and geometrically plausible.\n')
plan=['',f'## Continuation group {number}', '',
      'Selected by main under the user’s continue-until-stop authorization. Review remains deferred.', '',
      '| Set | Theme | Assets |','|---|---|---|']
for item in spec['sets']:
    name=item['name']; model_dir=ROOT/'Blender'/name; ref_dir=ROOT/'REF'/name
    model_dir.mkdir(parents=True); ref_dir.mkdir(parents=True)
    for folder in (model_dir,ref_dir):
        (folder/'.gitattributes').write_text('** -text\n',encoding='utf-8',newline='\n')
    (model_dir/'.gitignore').write_text('__pycache__/\n*.pyc\n*.blend[0-9]\n*.zip\n',encoding='utf-8',newline='\n')
    task=f'# {name}: {item["theme"]}\n\nRead ../SET_WORKER_BRIEF.md and ../SET_BATCH_PLAN.md. Own only this set. Main supplies four image references under local REF/. Review is deferred. Stop after your four models; parent alone dispatches continuation.\n\n'
    for asset in item['assets']:
        slug=asset['slug']
        prompt=common+'Subject: '+asset['description']+'\nColor palette: '+item['palette']+'.\nMaterials: simple clean PBR painted metal, rubber, muted glazing and appropriate masonry or roof surfaces, restrained seams and surface variation.\n'
        (ref_dir/(slug+'.prompt.txt')).write_text(prompt,encoding='utf-8',newline='\n')
        task+=f'- `{slug}`: {asset["label"]}\n'
    (model_dir/'TASK.md').write_text(task,encoding='utf-8',newline='\n')
    state['sets'][name]={'theme':item['theme'],'assets':[{'slug':a['slug'],'label':a['label']} for a in item['assets']],
                        'status':'awaiting_references','reference_count':0,'worker':None,'review_status':'deferred_by_user'}
    names='; '.join(a['slug']+' — '+a['label'] for a in item['assets'])
    plan.append(f'| {name} | {item["theme"]} | {names} |')
state['batches'].append({'number':number,'sets':[s['name'] for s in spec['sets']],
                         'status':'pending','commit':None,'selected_at_utc':datetime.now(timezone.utc).isoformat()})
state['planned_sets']=len(state['sets']); state['planned_models']=len(state['sets'])*4
state['next_action']='Generate this group references sequentially and dispatch one worker per completed set of four references'
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
plan+=['',f'- [ ] Group {number}: produce references, dispatch three workers, collect files with review deferred, commit.','']
plan_path=ROOT/'Blender/SET_BATCH_PLAN.md'
plan_path.write_text(plan_path.read_text(encoding='utf-8')+'\n'.join(plan),encoding='utf-8',newline='\n')
print(json.dumps({'batch':number,'sets':[s['name'] for s in spec['sets']],'prepared_prompts':12}))
