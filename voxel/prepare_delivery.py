"""Assemble only accepted voxel themes, originals, real previews and evidence."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,zipfile,html

ROOT=Path(__file__).resolve().parent;PROJECT=ROOT.parent
THEMES={
 'farm':('농장',['tractor','barn','silo','windmill']),
 'factory':('공장',['production_machine','conveyor','forklift','generator']),
 'antarctic':('남극 연구기지',['research_station','snowcat','radar','weather_instrument']),
 'harbor':('항구',['fishing_boat','lighthouse','warehouse','cargo_crane']),
 'mine':('광산',['excavator','mine_cart','mine_elevator','ore_sorter']),
 'desert':('사막 전초기지',['exploration_rover','water_tower','solar_array','repair_garage']),
 'mountain_railway':('산악 철도',['locomotive','passenger_car','station','railway_bridge','cable_car']),
 'spaceport':('우주항',['transport_rocket','hangar','exploration_rover','fuel_tank','control_tower']),
 'underwater':('해저 탐사기지',['submersible','dome_laboratory','connecting_tunnel','seabed_miner','docking_station'])}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
coord=json.loads((ROOT/'coordination.json').read_text(encoding='utf-8'));assert set(coord['accepted'])==set(THEMES)
records=[]
for theme,(label,names) in THEMES.items():
    validation=json.loads((ROOT/'validation'/f'{theme}.json').read_text(encoding='utf-8'))
    visual=json.loads((ROOT/'validation'/f'{theme}_visual_review.json').read_text(encoding='utf-8'))
    assert validation['passed'] and visual['accepted'] and visual['all_primary_images_personally_inspected']
    assert {r['asset'] for r in validation['records']}==set(names)
    assert validation['variant_count']==2*len(names)
    assert (ROOT/theme/'RESULT.md').is_file()
    for image in visual['images']:assert sha(ROOT/image['path'])==image['sha256']
    for name in names:
        pair={}
        for variant in ('large','half'):
            d=ROOT/theme/'assets'/name/variant;m=json.loads((d/'metadata.json').read_text(encoding='utf-8'))
            verified=next(r for r in validation['records'] if r['asset']==name and r['variant']==variant)
            for filename,digest in verified['sha256'].items():assert sha(d/filename)==digest,f'changed after parent review: {d/filename}'
            assert m['sha256']==verified['sha256']
            pair[variant]=m
        records.append({'theme':theme,'theme_label':label,'asset':name,'label':pair['large']['label'],'variants':pair})
assert len(records)==39
now=datetime.now(timezone.utc)
manifest={'status':'ready_for_review','packaged_at_utc':now.isoformat(),'themes':len(THEMES),'models':len(records),'variants':len(records)*2,'large_longest_axis':128,'half_longest_axis':64,'scale_semantics':'Half grid dimensions, double meters per voxel, same physical grid extents. Conservative boundary rounding may expand occupied bounds by one large cell.','native_format':'MagicaVoxel VOX 150','all_primary_previews_are_actual_blender_renders':True,'references':'../REF/voxel','assets':records,'limitations':['Static colored voxel assets; no rig, animation, collision, automatic LOD chain or engine integration.','Palette materials are solid/opaque; glass is stylized color. No image textures or UV atlas.','MagicaVoxel GUI was not used; native binary structure and occupancy were independently reparsed.','Fast was requested but not separately selectable in the worker creation API. Workers were explicitly gpt-6-astra/max.']}
(ROOT/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 복셀 모델 9테마 · 39종 · 78버전','','큰 버전은 긴 축 기준 128칸, 절반 버전은 64칸입니다. 절반 버전은 각 축의 복셀 수를 절반으로 줄이고 한 칸의 실제 크기를 두 배로 하여 같은 물리적 격자 크기를 유지합니다.','', '[큰 버전·절반 버전 비교 갤러리](index.html) · [전체 제작·검증 목록](delivery_manifest.json) · [생성 레퍼런스와 프롬프트](../REF/voxel)','', '| 테마 | 모델 수 | 실제 모델·제작 기록 | 독립 검증 |','|---|---:|---|---|']
for theme,(label,names) in THEMES.items():lines.append(f'| {label} | {len(names)} | [{theme}]({theme}/RESULT.md) | [검증](validation/{theme}.json) |')
lines+=['','각 모델의 `assets/모델명/large`와 `half` 폴더에 `.vox`, `.blend`, `.glb`, `.fbx`, `preview.png`, `metadata.json`이 있습니다. `.vox`가 수정과 재출력의 기준 원본이며, BLEND에는 별도 STUDIO 컬렉션에 미리보기용 조명·카메라가 들어 있습니다. GLB/FBX에는 모델 형상만 들어 있습니다.','','모든 원본을 독립 파서로 다시 읽고, BLEND·GLB·FBX를 각각 새 장면에서 열어 복셀 표면·색상·크기·삼각형 수를 확인했습니다. 모든 큰 버전·절반 버전 기본 렌더는 메인에서 직접 확인했으며 파일 해시를 고정했습니다.','','정적 모델입니다. 리깅·애니메이션·충돌·자동 LOD·게임 엔진 통합은 포함하지 않습니다. 유리는 불투명 색상으로 표현하며, 단색 팔레트 재질을 사용합니다. MagicaVoxel 앱에서 직접 열어보는 검사는 수행하지 않았습니다. 작은 버전은 얇은 구조를 보존하는 축소 방식이라 일부 외곽이 큰 격자 한 칸까지 넓어질 수 있습니다.','','## 개별 원본과 출력','','| 테마 / 모델 | 큰 VOX | 절반 VOX | 큰 GLB | 절반 GLB |','|---|---|---|---|---|']
for r in records:
    base=f'{r["theme"]}/assets/{r["asset"]}';n=r['asset'];lines.append(f'| {r["theme_label"]} / {r["label"]} | [VOX]({base}/large/{n}.vox) | [VOX]({base}/half/{n}.vox) | [GLB]({base}/large/{n}.glb) | [GLB]({base}/half/{n}.glb) |')
(ROOT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
cards=[]
for r in records:
    t=r['theme'];n=r['asset'];label=html.escape(r['label']);parts=[]
    for variant,text in [('large','큰 버전 · 128'),('half','절반 버전 · 64')]:
        base=f'{t}/assets/{n}/{variant}';meta=r['variants'][variant]
        links=' · '.join(f'<a href="{base}/{n}.{ext}">{ext.upper()}</a>' for ext in ['vox','blend','glb','fbx'])
        parts.append(f'<figure><a href="{base}/preview.png"><img loading="lazy" src="{base}/preview.png" alt="{label} {text}"></a><figcaption><b>{text}</b> / {"×".join(map(str,meta["grid_size"]))}<br>{meta["occupied_voxels"]:,} voxels · {meta["surface"]["triangles"]:,} triangles<br>{links}</figcaption></figure>')
    cards.append(f'<article data-theme="{t}"><h2>{html.escape(r["theme_label"])} · {label}</h2><div class="pair">{"".join(parts)}</div></article>')
options='<option value="">전체 9테마</option>'+''.join(f'<option value="{t}">{html.escape(label)}</option>' for t,(label,_) in THEMES.items())
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>복셀 모델 비교</title><style>body{font:16px/1.6 system-ui,sans-serif;background:#f3f1ec;color:#263438;margin:0;padding:24px;max-width:1200px;margin:auto}h1{font-size:28px;margin:0}header{position:sticky;top:0;background:#f3f1eced;padding:14px 0;z-index:1}select{font:inherit;padding:8px 14px;border:1px solid #9da7a5;border-radius:8px}article{background:white;border-radius:14px;padding:18px;margin:24px 0}h2{font-size:20px;margin:0 0 12px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}figure{margin:0}img{width:100%;display:block;border-radius:8px}figcaption{padding:12px 4px}a{color:#246b71}p{margin:8px 0}@media(max-width:600px){body{padding:12px}.pair{gap:8px}figcaption{font-size:12px}}</style><header><h1>복셀 모델 · 큰 버전 / 절반 버전</h1><p>9테마 · 39종 · 78버전. 아래 이미지는 모두 실제 모델 렌더입니다.</p><p>동일한 물리적 격자 크기에서 해상도를 비교합니다. 그림을 누르면 원본 크기로 볼 수 있습니다.</p><select id="theme">'''+options+'''</select> <a href="README.md">파일 안내</a></header>'''+''.join(cards)+'''<script>document.getElementById('theme').addEventListener('change',function(){document.querySelectorAll('article').forEach(a=>a.hidden=this.value&&a.dataset.theme!==this.value)});</script></html>'''
(ROOT/'index.html').write_text(page,encoding='utf-8')
for line in ['Worker 1: farm; after acceptance harbor; after acceptance mountain_railway.','Worker 2: factory; after acceptance mine; after acceptance spaceport.','Worker 3: antarctic; after acceptance desert; after acceptance underwater.','Main: independent voxel/export validation, actual image inspection, review index and verified archive.']:
    path=ROOT/'PLAN.md';path.write_text(path.read_text(encoding='utf-8').replace('- [ ] '+line,'- [x] '+line),encoding='utf-8')
allowed={'.vox','.blend','.glb','.fbx','.png','.json','.md','.py','.txt','.log','.html'}
files=[ROOT/p for p in ['README.md','index.html','BRIEF.md','PLAN.md','coordination.json','delivery_manifest.json','prepare_delivery.py']]
for theme in THEMES:files+=sorted(p for p in (ROOT/theme).rglob('*') if p.is_file() and p.suffix.lower() in allowed and '__pycache__' not in p.parts)
files+=sorted((ROOT/'validation').glob('*.json'))
files+=sorted(p for p in (ROOT/'_tools').glob('*') if p.is_file() and p.suffix in {'.py','.md'})
files+=sorted(p for p in (PROJECT/'REF'/'voxel').rglob('*') if p.is_file())
files=list(dict.fromkeys(files));archive=ROOT/'voxel-nine-themes.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:z.write(p,p.relative_to(PROJECT).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
digest=sha(archive);(ROOT/'voxel-nine-themes.sha256').write_text(digest+'  '+archive.name+'\n',encoding='ascii')
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'files':len(files),'models':39,'variants':78,'sha256':digest},ensure_ascii=False,indent=2))
