"""Main-owned bookkeeping. This inventories outputs; it does not review models."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / 'Blender/SET_BATCH_STATE.json'
SCRATCH = ROOT / 'Blender/BatchTools/scratch'

def now():
    return datetime.now(timezone.utc).isoformat()

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def eligible(path):
    rel = path.relative_to(ROOT)
    return (path.is_file() and not any(p in ('scratch', '__pycache__') for p in rel.parts)
            and path.suffix.lower() not in ('.pyc', '.zip')
            and not re.search(r'\.blend\d+$', path.name))

def process_records(value):
    if isinstance(value,dict):
        if 'returncode' in value:
            yield value
        for child in value.values():
            yield from process_records(child)
    elif isinstance(value,list):
        for child in value:
            yield from process_records(child)

def catalog(state):
    lines = ['# Rounded model sets 03–11', '',
             'Production inventory for 36 ordinary mesh assets. Model review is deferred by user instruction.', '',
             'Each set includes its own REF directory. Original references remain under ../REF/SetNN.', '',
             '| Set | Theme | Production status | Outputs |', '|---|---|---|---|']
    for name, spec in state['sets'].items():
        link = f'[{name}/README]({name}/README.md)' if (ROOT/'Blender'/name/'README.md').exists() else 'Pending'
        lines.append(f'| {name} | {spec["theme"]} | {spec["status"]} | {link} |')
    for name, spec in state['sets'].items():
        if spec['status'] != 'produced_unreviewed':
            continue
        lines += ['', f'## {name} — {spec["theme"]}', '',
                  '| Model | Reference | Native / exports | Preview files (unreviewed) |', '|---|---|---|---|']
        for asset in spec['assets']:
            slug=asset['slug']; base=f'{name}/{slug}'
            lines.append(f'| {asset["label"]} | [REF]({name}/REF/{slug}.png) | [BLEND]({base}/{slug}.blend) · [GLB]({base}/{slug}.glb) · [FBX]({base}/{slug}.fbx) | [Hero]({base}/renders/hero.png) · [Rear]({base}/renders/rear.png) |')
    (ROOT/'Blender/SET_CATALOG.md').write_text('\n'.join(lines)+'\n', encoding='utf-8', newline='\n')

action = sys.argv[1]
state = json.loads(STATE.read_text(encoding='utf-8'))
if action == 'dispatch':
    name, worker = sys.argv[2:4]
    spec = state['sets'][name]
    assert spec['reference_count'] == 4
    spec.update(status='modeling', worker=worker, modeling_dispatched_at_utc=now())
    batch=next(b for b in state['batches'] if name in b['sets'])
    batch['status']='modeling'
    state['current_batch']=batch['number']
    write_json(STATE,state)
    print(name+' dispatched to '+worker)
elif action == 'begin':
    number=int(sys.argv[2]); batch=state['batches'][number-1]
    for previous in state['batches'][:number-1]:
        receipt=json.loads((SCRATCH/f'batch{previous["number"]}_commit.json').read_text(encoding='utf-8'))
        previous.update(status='committed', commit=receipt['commit'])
    batch['status']='generating_references'; batch['started_at_utc']=now()
    state['current_batch']=number
    write_json(STATE,state)
    print('Began batch',number)
elif action == 'collect':
    number=int(sys.argv[2]); batch=state['batches'][number-1]
    inventory=[]; summaries=[]
    for name in batch['sets']:
        folder=ROOT/'Blender'/name; spec=state['sets'][name]
        status=json.loads((folder/'STATUS.json').read_text(encoding='utf-8'))
        assert status['status']=='produced_unreviewed', (name,status['status'])
        assert status['review_status']=='deferred_by_user'
        manifest=json.loads((folder/'delivery_manifest.json').read_text(encoding='utf-8'))
        processes=list(process_records(manifest)) or list(process_records(status))
        assert sum(p['returncode']==0 for p in processes)>=4, (name,'Four successful process records required')
        required=[folder/f for f in ('STATUS.json','RESULT.md','README.md','delivery_manifest.json')]
        for a in spec['assets']:
            slug=a['slug']; base=folder/slug
            required += [base/(slug+ext) for ext in ('.blend','.glb','.fbx')]
            required += [base/'metadata.json',base/'renders/hero.png',base/'renders/rear.png']
            required += [folder/'REF'/(slug+'.png'),folder/'REF'/(slug+'.prompt.txt')]
            required += [ROOT/'REF'/name/(slug+'.png'), ROOT/'REF'/name/(slug+'.prompt.txt')]
        required += [folder/'REF/generation_manifest.json',ROOT/'REF'/name/'generation_manifest.json']
        for path in required:
            assert path.is_file() and path.stat().st_size>0, str(path)
            inventory.append({'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,
                              'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        summaries.append({'set':name,'worker_status_file':f'Blender/{name}/STATUS.json',
                          'started_at_utc':status.get('started_at_utc'),
                          'finished_at_utc':status.get('finished_at_utc'),
                          'elapsed_seconds':status.get('elapsed_seconds'),
                          'recorded_process_returncodes':[p['returncode'] for p in processes]})
        spec.update(status='produced_unreviewed',finished_at_utc=status.get('finished_at_utc'))
    batch.update(status='produced_unreviewed',commit='containing_commit',produced_at_utc=now())
    if all(s['status']=='produced_unreviewed' for s in state['sets'].values()):
        state.update(status='produced_unreviewed',finished_at_utc=now(),produced_models=36)
    write_json(STATE,state)
    write_json(ROOT/f'Blender/BatchTools/batch{number}_inventory.json',{
        'batch':number,'sets':batch['sets'],'models':12,'status':'produced_unreviewed',
        'review_status':'deferred_by_user','recorded_at_utc':now(),
        'checks':'Expected nonempty files and worker completion records only. No visual or model validation.',
        'worker_summaries':summaries,'files':inventory})
    catalog(state)
    plan=ROOT/'Blender/SET_BATCH_PLAN.md'
    content=plan.read_text(encoding='utf-8').replace(f'- [ ] Group {number}:',f'- [x] Group {number}:')
    if number==3:
        content=content.replace('- [ ] Record all three commits','- [x] Record all three commits')
    plan.write_text(content,encoding='utf-8',newline='\n')
    print(json.dumps({'batch':number,'models':12,'required_files':len(inventory),'review':'deferred_by_user'}))
elif action == 'stage-list':
    number=int(sys.argv[2]); batch=state['batches'][number-1]
    assert batch['status']=='produced_unreviewed'
    assert not git('diff','--cached','--name-only','-z'), 'Index contains other work; do not alter it.'
    roots=[ROOT/'Blender'/n for n in batch['sets']]+[ROOT/'REF'/n for n in batch['sets']]
    roots += [ROOT/'Blender/BatchTools']
    if number==1:
        roots += [ROOT/'Blender/Set01/REF', ROOT/'Blender/Set02/REF']
    paths={p.relative_to(ROOT).as_posix() for root in roots for p in root.rglob('*') if eligible(p)}
    paths.update('Blender/'+f for f in ('SET_BATCH_PLAN.md','SET_BATCH_STATE.json','SET_WORKER_BRIEF.md','SET_CATALOG.md'))
    SCRATCH.mkdir(parents=True,exist_ok=True)
    out=SCRATCH/f'batch{number}_paths.bin'
    out.write_bytes(b'\0'.join(p.encode('utf-8') for p in sorted(paths))+b'\0')
    print(json.dumps({'batch':number,'files':len(paths),'pathspec':str(out)}))
elif action == 'commit':
    number=int(sys.argv[2]); batch=state['batches'][number-1]
    pathsfile=SCRATCH/f'batch{number}_paths.bin'
    assert not git('diff','--cached','--name-only','-z'), 'Index contains other work; do not alter it.'
    expected={s.decode('utf-8') for s in pathsfile.read_bytes().split(b'\0') if s}
    subprocess.check_call(['git','add','-f','--pathspec-from-file='+str(pathsfile),'--pathspec-file-nul'],cwd=ROOT)
    actual={s.decode('utf-8') for s in git('diff','--cached','--name-only','-z').split(b'\0') if s}
    assert actual and actual <= expected, 'Staged paths outside task inventory.'
    message=f'feat: add rounded model sets {batch["sets"][0]}-{batch["sets"][-1]} with references'
    subprocess.check_call(['git','commit','-m',message],cwd=ROOT)
    sha=git('rev-parse','HEAD').decode().strip()
    write_json(SCRATCH/f'batch{number}_commit.json',{'batch':number,'commit':sha,'committed_at_utc':now(),'subject':message})
    print(json.dumps({'batch':number,'commit':sha,'staged_files':len(actual)}))
else:
    raise SystemExit('Unknown action: '+action)
