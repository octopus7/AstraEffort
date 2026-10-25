"""Package reviewed original and expanded voxel assets without changing models."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from html.parser import HTMLParser
import json,hashlib,html,zipfile

ROOT=Path(__file__).resolve().parent;PROJECT=ROOT.parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
state=read(ROOT/'EXPANSION_STATE.json');assert set(state['accepted'])==set(state['units'])
base=read(ROOT/'delivery_manifest_first39.json');assert base['models']==39
records=[]
for old in base['assets']:
    row=dict(old);row['root']=row['theme'];row['delivery']='original';records.append(row)
for theme,u in state['units'].items():
    v=read(ROOT/'validation'/f'expansion_{theme}.json');review=read(ROOT/'validation'/f'expansion_{theme}_visual_review.json')
    assert v['passed'] and review['accepted'] and review['all_primary_images_personally_inspected']
    assert set(r['asset'] for r in v['records'])==set(u['assets'])
    for im in review['images']:assert sha(ROOT/im['path'])==im['sha256']
    for asset in u['assets']:
        variants={}
        for size in ('large','half'):
            m=read(ROOT/u['root']/'assets'/asset/size/'metadata.json')
            verified=next(r for r in v['records'] if r['asset']==asset and r['variant']==size)
            assert m['sha256']==verified['sha256'];variants[size]=m
        records.append({'theme':theme,'theme_label':u['label'],'root':u['root'],'delivery':u['phase'],'asset':asset,'label':variants['large']['label'],'variants':variants})
assert len(records)==81 and len({r['theme'] for r in records})==18
assert len({(r['theme'],r['asset']) for r in records})==81
for r in records:
    for size,m in r['variants'].items():
        folder=ROOT/r['root']/'assets'/r['asset']/size
        for f,h in m['sha256'].items():assert sha(folder/f)==h,f'changed after inspection: {folder/f}'
        assert max(m['grid_size'])==(128 if size=='large' else 64)
    assert all(a==b*2 for a,b in zip(r['variants']['large']['grid_size'],r['variants']['half']['grid_size']))
    assert abs(r['variants']['half']['voxel_size_m']-2*r['variants']['large']['voxel_size_m'])<1e-9
    assert all(abs(a-b)<1e-9 for a,b in zip(r['variants']['large']['grid_extents_m'],r['variants']['half']['grid_extents_m']))
overview=read(ROOT/'overview_half_all.json')
assert overview['source_count']==overview['unique_source_count']==81 and overview['theme_count']==18
assert overview['status_counts']=={'accepted':81} and overview['all_labels_fit']
expected_half={f'voxel/{r["root"]}/assets/{r["asset"]}/half/preview.png':r['variants']['half']['sha256']['preview.png'] for r in records}
assert {s['source_path'] for s in overview['sources']}==set(expected_half)
for item in overview['sources']:
    assert item['sha256_before']==item['sha256_after']==expected_half[item['source_path']]
    assert sha(PROJECT/item['metadata_path'])==item['metadata_sha256_before']==item['metadata_sha256_after']
assert sha(PROJECT/overview['output']['path'])==overview['output']['sha256']
refs=[]
for theme,u in state['units'].items():
    folder=PROJECT/'REF'/'voxel'/theme
    if u['phase']=='additions':folder=folder/'additions'
    meta=read(folder/'generation.json');assert meta['inspected'];assert (folder/'reference.png').is_file();refs.append(meta)
(PROJECT/'REF'/'voxel'/'generation_manifest_expansion.json').write_text(json.dumps({'method':'built-in image_gen, main only, strictly sequential','references':refs},ensure_ascii=False,indent=2),encoding='utf-8')
now=datetime.now(timezone.utc)
manifest={'status':'complete','packaged_at_utc':now.isoformat(),'themes':18,'models':81,'variants':162,'original_models_preserved':39,'existing_theme_additions':6,'new_theme_models':36,'native_format':'MagicaVoxel VOX 150','large_longest_axis':128,'half_longest_axis':64,'same_physical_grid_extents':True,'all_primary_previews_are_actual_blender_renders':True,'assets':records,'limitations':base['limitations']}
(ROOT/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
theme_order=list(dict.fromkeys(r['theme'] for r in records));labels={r['theme']:r['theme_label'] for r in records}
text=['# 복셀 모델 18테마 · 81종 · 162버전','','기존 39종에 유용한 모델 6종을 보강한 뒤 신규 9테마 36종을 제작했습니다. 기존 모델 파일과 9테마 ZIP은 보존했습니다. 큰 버전은 긴 축 128복셀, 절반 버전은 64복셀입니다. 각 축 해상도를 절반으로 줄이고 복셀 크기를 두 배로 하여 물리적 격자 크기를 유지합니다.','','이 목록은 복셀 모델만 포함합니다. 앞서 제작한 일반 메시 모델 2세트·8종은 별도입니다. 작은 버전 모음은 전체 81종으로 갱신했으며 개별 프리뷰 파일은 모두 유지했습니다.','','[작은 버전 81종 모음](overview_half_all.png) · [큰·절반 비교 갤러리](index.html) · [전체 ZIP](voxel-eighteen-themes.zip) · [전체 제작·검증 목록](delivery_manifest.json) · [확장 계획](EXPANSION_PLAN.md)','','| 테마 | 모델 수 | 제작·검증 기록 |','|---|---:|---|']
for t in theme_order:
    roots=list(dict.fromkeys(r['root'] for r in records if r['theme']==t))
    links=' · '.join(f'[제작 {i+1}]({p}/RESULT.md)' for i,p in enumerate(roots))
    text.append(f'| {labels[t]} | {sum(r["theme"]==t for r in records)} | {links} |')
text+=['','각 모델은 `assets/모델명/{large,half}`에 VOX 원본, BLEND·GLB·FBX, 실제 렌더 PNG와 metadata.json이 있습니다. 기존 테마 보강분은 해당 테마의 `additions/` 아래에 있습니다. 각 제작 폴더의 build.py로 복셀 원본과 출력을 재생성할 수 있습니다.','','전체 원본을 다시 읽고 BLEND·GLB·FBX를 새 장면으로 가져와 복셀 표면, 방향, 색상, 크기와 파일 해시를 검사했습니다. 모든 최종 기본 렌더를 메인에서 직접 확인했습니다. 원본 39종은 이전 검증 기록과 현재 해시를 대조해 그대로 보존된 것을 확인했습니다.','','정적 모델이며 리깅·애니메이션·충돌·자동 LOD·엔진 통합은 포함하지 않습니다. 유리는 불투명 팔레트 색상입니다. 얇은 부품을 보존하는 축소 방식으로 외곽이 큰 격자 한 칸까지 넓어질 수 있습니다. MagicaVoxel GUI 검사는 수행하지 않았으며 native VOX 파일은 독립 파서로 검사했습니다.','','레퍼런스 이미지와 프롬프트는 [REF/voxel](../REF/voxel)에 저장했습니다. 모든 이미지 생성은 메인이 기본 image_gen으로 순차 진행했으며 실제 모델 증거는 Blender 렌더입니다.','','| 테마 / 모델 | 큰 VOX | 절반 VOX | 큰 GLB | 절반 GLB |','|---|---|---|---|---|']
for r in records:
    b=f'{r["root"]}/assets/{r["asset"]}';n=r['asset']
    text.append(f'| {r["theme_label"]} / {r["label"]} | [VOX]({b}/large/{n}.vox) | [VOX]({b}/half/{n}.vox) | [GLB]({b}/large/{n}.glb) | [GLB]({b}/half/{n}.glb) |')
(ROOT/'README.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
cards=[]
for r in records:
    parts=[];label=html.escape(r['label']);n=r['asset']
    for size,title in [('large','큰 버전 · 128'),('half','절반 버전 · 64')]:
        b=f'{r["root"]}/assets/{n}/{size}';m=r['variants'][size]
        links=' · '.join(f'<a href="{b}/{n}.{e}">{e.upper()}</a>' for e in ('vox','blend','glb','fbx'))
        parts.append(f'<figure><a href="{b}/preview.png"><img loading="lazy" src="{b}/preview.png" alt="{label} {title}"></a><figcaption><b>{title}</b> / {"×".join(map(str,m["grid_size"]))}<br>{m["occupied_voxels"]:,} voxels · {m["surface"]["triangles"]:,} triangles<br>{links}</figcaption></figure>')
    badge={'original':'기존 모델','additions':'기존 테마 보강','new':'신규 테마'}[r['delivery']]
    cards.append(f'<article data-theme="{r["theme"]}"><h2>{html.escape(r["theme_label"])} · {label}</h2><small>{badge}</small><div class="pair">{"".join(parts)}</div></article>')
options='<option value="">전체 18테마</option>'+''.join(f'<option value="{t}">{html.escape(labels[t])}</option>' for t in theme_order)
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>복셀 모델 18테마 비교</title><style>body{font:16px/1.6 system-ui,sans-serif;background:#f3f1ec;color:#263438;margin:0;padding:24px;max-width:1200px;margin:auto}h1{font-size:28px;margin:0}header{position:sticky;top:0;background:#f3f1eced;padding:14px 0;z-index:1}select{font:inherit;padding:8px 14px;border:1px solid #9da7a5;border-radius:8px}article{background:white;border-radius:14px;padding:18px;margin:24px 0}h2{font-size:20px;margin:0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}figure{margin:0}img{width:100%;display:block;border-radius:8px}figcaption{padding:12px 4px}a{color:#246b71}p{margin:8px 0}small{display:block;margin-bottom:12px;color:#657472}@media(max-width:600px){body{padding:12px}.pair{gap:8px}figcaption{font-size:12px}}</style><header><h1>복셀 모델 · 큰 버전 / 절반 버전</h1><p>18테마 · 81종 · 162버전. 모든 미리보기는 실제 모델 렌더입니다.</p><p>물리적 격자 크기를 유지한 128 / 64 복셀 해상도를 같은 카메라로 비교합니다.</p><select id="theme">'''+options+'''</select> <a href="README.md">파일 안내</a></header>'''+''.join(cards)+'''<script>document.getElementById('theme').addEventListener('change',function(){document.querySelectorAll('article').forEach(a=>a.hidden=this.value&&a.dataset.theme!==this.value)});</script></html>'''
(ROOT/'index.html').write_text(page,encoding='utf-8')
class CheckHTML(HTMLParser):
    def __init__(self):super().__init__();self.counts=Counter();self.links=[]
    def handle_starttag(self,tag,attrs):
        self.counts[tag]+=1
        self.links.extend(v for k,v in attrs if k in ('src','href'))
check=CheckHTML();check.feed(page);assert check.counts['article']==81 and check.counts['img']==162
assert all((ROOT/p).exists() for p in check.links)
state.update(status='complete',finished_at_utc=now.isoformat(),phase_b_completed_at_utc=now.isoformat(),models=81,variants=162,completed_models=81,completed_variants=162,exported_models=81,exported_variants=162,awaiting_primary_review=[],work_in_progress=[],not_started=[],original_hashes_preserved=True,checkpoint_45_models_preserved=True,checkpoint_73_commit='b3992e3')
if state.get('phase_b_started_at_utc'):
    state['phase_b_elapsed_seconds']=(now-datetime.fromisoformat(state['phase_b_started_at_utc'].replace('Z','+00:00'))).total_seconds()
    state['phase_b_recorded_pause_seconds']=sum((datetime.fromisoformat(h['resumed_at_utc'].replace('Z','+00:00'))-datetime.fromisoformat(h['paused_modeling_since_utc'].replace('Z','+00:00'))).total_seconds() for h in state.get('resume_history',[]) if h.get('paused_modeling_since_utc'))
    state['phase_b_elapsed_excluding_recorded_pauses_seconds']=state['phase_b_elapsed_seconds']-state['phase_b_recorded_pause_seconds']
if state.get('paused_at_utc'):
    state.setdefault('pause_history',[]).append({'paused_at_utc':state.pop('paused_at_utc'),'reason':state.pop('pause_reason','User pause')})
(ROOT/'EXPANSION_STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'RESUME.md').write_text('# Voxel production completed\n\nAll 18 themes, 81 models and 162 large/half variants are complete and parent-accepted. No model task remains queued. The 45-model checkpoint is preserved in commit 63e475d and the 73-exported-model checkpoint/overview in commit b3992e3. CHECKPOINT.json is a historical record of that intermediate state. The later nine themes add 36 models to the 45-model baseline.\n\nUse README.md, index.html, overview_half_all.png and delivery_manifest.json for the current delivery. Every individual preview remains present. EXPANSION_STATE.json retains actual acceptance, pause/resume and completion records, separating recorded pauses from elapsed phase time. Per-theme RESULT/STATUS and validation evidence retain timings and limitations. References and prompts live in REF/voxel.\n\nThe old prepare_delivery.py and prepare_checkpoint.py target historical snapshots; do not run them over the final catalog. prepare_expanded_delivery.py verifies and reconstructs the final catalog/archive from frozen results after the 81-model half overview is ready.\n',encoding='utf-8')
p=ROOT/'EXPANSION_PLAN.md';plan=p.read_text(encoding='utf-8').replace('- [ ]','- [x]').replace('## Progress checkpoint','## Historical checkpoint (b3992e3)').split('\n## Final completion')[0];p.write_text(plan+'\n## Final completion\n\nAll 18 themes / 81 models / 162 variants are parent-accepted. The 81-model half overview, comparison gallery, manifest and archive are prepared from frozen outputs. Completed at '+now.isoformat()+'.\n',encoding='utf-8')
allowed={'.vox','.blend','.glb','.fbx','.png','.json','.md','.py','.ps1','.txt','.log','.html'}
files=[p for p in ROOT.iterdir() if p.is_file() and p.suffix in allowed and p.name!='delivery_package_validation.json']
for t in theme_order:files.extend(p for p in (ROOT/t).rglob('*') if p.is_file() and p.suffix in allowed and '__pycache__' not in p.parts)
files.extend(p for p in (ROOT/'_tools').iterdir() if p.is_file() and p.suffix in {'.py','.md'})
files.extend(p for p in (ROOT/'validation').iterdir() if p.is_file() and p.suffix in {'.json','.log'})
files.extend(p for p in (PROJECT/'REF'/'voxel').rglob('*') if p.is_file())
archive=ROOT/'voxel-eighteen-themes.zip';files=list(dict.fromkeys(files))
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:z.write(p,p.relative_to(PROJECT).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    counts=Counter(Path(n).suffix for n in z.namelist());assert all(counts[e]==162 for e in ('.vox','.blend','.glb','.fbx'))
digest=sha(archive);(ROOT/'voxel-eighteen-themes.sha256').write_text(digest+'  '+archive.name+'\n',encoding='ascii')
package_check={'started_at_utc':now.isoformat(),'finished_at_utc':datetime.now(timezone.utc).isoformat(),'archive':archive.name,'bytes':archive.stat().st_size,'files':len(files),'themes':18,'models':81,'variants':162,'format_counts':{e:counts[e] for e in ('.vox','.blend','.glb','.fbx')},'zip_crc_passed':True,'original_model_hashes_unchanged':True,'gallery_cards':check.counts['article'],'gallery_images':check.counts['img'],'gallery_links_checked':len(check.links),'half_overview_models':81,'half_overview_sha256':overview['output']['sha256'],'sha256':digest}
(ROOT/'delivery_package_validation.json').write_text(json.dumps(package_check,indent=2)+'\n',encoding='utf-8')
print(json.dumps(package_check,indent=2))
