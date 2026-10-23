"""Record the user's requested pause after six additions, before new themes."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from html.parser import HTMLParser
import json,hashlib,html,re
R=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=read(R/'EXPANSION_STATE.json');base=read(R/'delivery_manifest_first39.json')
added={t:u for t,u in s['units'].items() if u['phase']=='additions'}
assert len(added)==6 and set(added)<=set(s['accepted'])
rows=[]
for old in base['assets']:
    row=dict(old);row.update(root=row['theme'],delivery='original');rows.append(row)
    assert read(R/'validation'/(row['theme']+'.json'))['passed']
    assert read(R/'validation'/(row['theme']+'_visual_review.json'))['all_primary_images_personally_inspected']
for t,u in added.items():
    v=read(R/'validation'/f'expansion_{t}.json');review=read(R/'validation'/f'expansion_{t}_visual_review.json')
    assert v['passed'] and review['accepted'] and review['all_primary_images_personally_inspected']
    for name in u['assets']:
        pair={size:read(R/u['root']/'assets'/name/size/'metadata.json') for size in ('large','half')}
        for size,m in pair.items():assert m['sha256']==next(x for x in v['records'] if x['asset']==name and x['variant']==size)['sha256']
        rows.append({'theme':t,'theme_label':u['label'],'root':u['root'],'delivery':'additions','asset':name,'label':pair['large']['label'],'variants':pair})
for row in rows:
    for size,m in row['variants'].items():
        d=R/row['root']/'assets'/row['asset']/size
        for f,h in m['sha256'].items():assert sha(d/f)==h,str(d/f)
assert len(rows)==45 and len({r['theme'] for r in rows})==9
for t,u in s['units'].items():
    if u['phase']=='new':
        assert not (R/u['root']/'assets').exists(),f'Unexpected new theme assets: {t}'
        assert not (R.parent/'REF'/'voxel'/t/'reference.png').exists(),f'Unexpected new reference: {t}'
now=datetime.now(timezone.utc).isoformat();s.update(status='paused',paused_at_utc=now,pause_reason='User explicitly requested commit validated outputs and stop; resume later.',phase_a_complete=True,new_themes_started=False,completed_models=45,completed_variants=90)
(R/'EXPANSION_STATE.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
manifest=dict(base);manifest.update(status='validated_checkpoint_paused',recorded_at_utc=now,models=45,variants=90,original_models_preserved=39,existing_theme_additions=6,new_theme_models=0,assets=rows)
manifest.pop('packaged_at_utc',None)
(R/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
cards=[]
for row in rows[39:]:
    parts=[];n=row['asset'];label=html.escape(row['label'])
    for size,title in [('large','큰 버전 · 128'),('half','절반 버전 · 64')]:
        b=f'{row["root"]}/assets/{n}/{size}';m=row['variants'][size]
        links=' · '.join(f'<a href="{b}/{n}.{e}">{e.upper()}</a>' for e in ('vox','blend','glb','fbx'))
        parts.append(f'<figure><a href="{b}/preview.png"><img loading="lazy" src="{b}/preview.png" alt="{label} {title}"></a><figcaption><b>{title}</b> / {"×".join(map(str,m["grid_size"]))}<br>{m["occupied_voxels"]:,} voxels · {m["surface"]["triangles"]:,} triangles<br>{links}</figcaption></figure>')
    cards.append(f'<article data-theme="{row["theme"]}"><h2>{html.escape(row["theme_label"])} · {label} · 추가 모델</h2><div class="pair">{"".join(parts)}</div></article>')
page=(R/'index.html').read_text(encoding='utf-8');page=re.sub(r'<!-- additions:start -->.*?<!-- additions:end -->','',page,flags=re.S)
page=page.replace('39종 · 78버전','45종 · 90버전').replace('<script>','<!-- additions:start -->'+''.join(cards)+'<!-- additions:end --><script>',1)
(R/'index.html').write_text(page,encoding='utf-8')
class Check(HTMLParser):
    def __init__(self):super().__init__();self.counts=Counter();self.links=[]
    def handle_starttag(self,t,a):self.counts[t]+=1;self.links.extend(v for k,v in a if k in ('src','href'))
c=Check();c.feed(page);assert c.counts['article']==45 and c.counts['img']==90;assert all((R/p).exists() for p in c.links)
lines=['# 복셀 모델 9테마 · 45종 · 90버전','','**출력 검사와 렌더 검토를 마친 상태에서 사용자 요청으로 중단했습니다. 신규 9테마는 아직 시작하지 않았습니다.**','','[큰·절반 비교 갤러리](index.html) · [전체 파일 목록](delivery_manifest.json) · [다음 작업 인계](RESUME.md)','','큰 버전은 긴 축 128복셀, 절반 버전은 64복셀입니다. 각 축 복셀 수를 절반으로 줄이고 복셀 크기를 두 배로 하여 같은 물리적 격자 크기를 유지합니다. 기존 39종에 유용한 모델 6종을 추가했습니다.','','| 테마 | 모델 수 | 기존 제작 기록 | 보강 모델 |','|---|---:|---|---|']
for t in dict.fromkeys(r['theme'] for r in rows):
    label=next(r['theme_label'] for r in rows if r['theme']==t);extra=next((r for r in rows if r['theme']==t and r['delivery']=='additions'),None)
    link=f'[{extra["label"]}]({extra["root"]}/RESULT.md)' if extra else '—'
    lines.append(f'| {label} | 5 | [{t}]({t}/RESULT.md) | {link} |')
lines+=['','모델마다 `.vox`, `.blend`, `.glb`, `.fbx`, `preview.png`, `metadata.json`이 있습니다. 기존 모델은 `테마/assets/모델명/{large,half}`, 보강분은 `테마/additions/assets/모델명/{large,half}`에 있습니다. VOX가 편집 기준 원본이며 BLEND에는 별도 STUDIO 컬렉션, GLB/FBX에는 모델 형상만 포함합니다.','','원본 복셀 파싱, 색상·크기·표면 검사, BLEND·GLB·FBX 재가져오기를 통과했고 모든 최종 미리보기를 메인이 직접 확인했습니다. 기존 39종의 모델 파일 해시는 그대로입니다. 생성 레퍼런스와 프롬프트는 [REF/voxel](../REF/voxel)에 있습니다.','','정적 팔레트 모델입니다. 리깅·애니메이션·충돌·엔진 통합은 포함하지 않으며 유리는 불투명 색상입니다. 얇은 구조를 보존하는 축소 방식으로 외곽이 큰 격자 한 칸까지 넓어질 수 있습니다. MagicaVoxel GUI에서는 검사하지 않았습니다.','','이전 `voxel-nine-themes.zip`은 최초 39종 묶음으로 로컬에 보존하며 Git에는 중복 압축파일을 넣지 않습니다. 현재 45종의 기준은 이 목록과 실제 모델 폴더입니다.']
(R/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
plan=R/'EXPANSION_PLAN.md';lines=plan.read_text(encoding='utf-8').splitlines();n=0
for i,line in enumerate(lines):
    if line.startswith('- [ ]'):
        n+=1
        if n<=3:lines[i]=line.replace('- [ ]','- [x]',1)
plan.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'models':45,'variants':90,'themes':9,'original_hashes_unchanged':True,'gallery_images':c.counts['img'],'checked_links':len(c.links),'new_themes_started':False,'status':'paused'},indent=2))
