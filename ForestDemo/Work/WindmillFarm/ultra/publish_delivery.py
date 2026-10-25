"""Publish only the validated, closed WindmillFarm private project's owned packages."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, shutil
from PIL import Image

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
PROJECT=REPO/'ForestDemo/Saved/Workers/WindmillFarm/ultra/Project'
CONTENT=PROJECT/'Content'
SOURCE=CONTENT/'WindmillFarm/ultra'
DEST=REPO/'ForestDemo/Content/WindmillFarm/ultra'
MAP=Path('Maps/WindmillFarm_ultra.umap')
REQUIRED=('saved_map_reload','non_world_partition','no_external_packages','owned_dependencies',
          'footprint_100m','materials_and_uvs','dynamic_lighting','player_start','upright_placement',
          'prop_contact_and_clearance','pie_possession','ground_collision','building_collision',
          'pawn_sweep_blocks','pawn_can_move','pie_ended')

def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,obj):(ROOT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def date(value):return datetime.fromisoformat(value.replace('Z','+00:00'))

def main():
    assert REPO==Path('D:/github/AstraEffort'),str(REPO)
    valid=read('validation.json');timing=read('Execution/verified_timing.json');shutdown=read('shutdown_check.json')
    assert valid['all_passed'] and all(valid['checks'].get(k) is True for k in REQUIRED)
    assert timing['exit_code']==0 and date(timing['run_started_at_utc'])<=date(valid['utc'])<=date(timing['finished_at_utc'])
    assert shutdown['query_succeeded'] is True and shutdown['own_unreal_process_count']==0 and date(shutdown['utc'])>=date(timing['finished_at_utc'])
    assert valid['detail']['bad_dependencies']==[]
    rendered=read('render_analysis.json');manifest=read('Screenshots/capture_manifest.json')
    assert rendered['all_1920x1080'] and rendered['all_nonblank']
    assert len(rendered['images'])==7 and len(manifest['captures'])==7
    assert 'Actual Unreal Engine' in manifest['source']
    map_modified=datetime.fromtimestamp((CONTENT/MAP).stat().st_mtime,timezone.utc)
    for row in rendered['images']:
        p=ROOT/'Screenshots'/(row['name']+'.png')
        assert Image.open(p).size==(1920,1080) and digest(p)==row['sha256']
    assert all(date(c['utc'])>=map_modified for c in manifest['captures'])
    review=read('visual_review.json')
    assert review['accepted'] and all(review['image_sha256'][r['name']]==r['sha256'] for r in rendered['images'])
    packages=sorted(p for p in CONTENT.rglob('*') if p.is_file())
    assert all(p==CONTENT/MAP or (p.is_relative_to(SOURCE) and p.suffix=='.uasset') for p in packages)
    assert all(not any(s in p.as_posix() for s in ('__ExternalActors__','__ExternalObjects__','_BuiltData')) for p in packages)
    expected={p.relative_to(CONTENT).as_posix():digest(p) for p in packages}
    target_map=REPO/'ForestDemo/Content'/MAP
    if DEST.exists():
        existing={p.relative_to(REPO/'ForestDemo/Content').as_posix():digest(p) for p in DEST.rglob('*') if p.is_file()}
        assert all(expected.get(k)==v for k,v in existing.items()),'Refuse to overwrite divergent owned destination files'
    if target_map.exists():assert digest(target_map)==expected[MAP.as_posix()],'Refuse to overwrite divergent map'
    published=[]
    for source in packages:
        relative=source.relative_to(CONTENT);target=REPO/'ForestDemo/Content'/relative
        assert target==target_map or target.is_relative_to(DEST)
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():shutil.copy2(source,target)
        assert digest(target)==expected[relative.as_posix()]
        published.append({'relative_path':relative.as_posix(),'source':str(source),'destination':str(target),'bytes':target.stat().st_size,'sha256':digest(target)})
    pub={'utc':datetime.now(timezone.utc).isoformat(),'private_editor_closed':True,'validation_utc':valid['utc'],
         'validation_sha256':digest(ROOT/'validation.json'),'all_hashes_match':True,'file_count':len(published),
         'total_bytes':sum(r['bytes'] for r in published),'files':published}
    write('publication.json',pub)
    print(json.dumps({k:v for k,v in pub.items() if k!='files'},indent=2))

if __name__=='__main__':main()
