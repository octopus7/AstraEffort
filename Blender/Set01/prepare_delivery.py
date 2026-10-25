"""Package only validated Set01 deliverables; never collect unrelated workspace assets."""
import json, hashlib, zipfile
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
ASSETS=[('cargo_rover','4륜 화물 운반차'),('service_mech','2족 정비 메카'),('arched_workshop','아치 지붕 정비소'),('water_station','물탱크 급수소')]
records=[]
for slug,label in ASSETS:
    v=json.loads((ROOT/'validation'/f'{slug}.json').read_text(encoding='utf-8-sig'))
    assert v['passed'],f'{slug} validation did not pass: {v["errors"]}'
    assert (ROOT/slug/'RESULT.md').is_file(),f'{slug} has no delivery report'
    for filename,expected in v['sha256'].items():
        actual=hashlib.sha256((ROOT/slug/filename).read_bytes()).hexdigest()
        assert actual==expected,f'{slug}/{filename} changed after validation'
    records.append({'slug':slug,'name_ko':label,'triangles':v['source']['triangles'],'dimensions_m':v['source']['dimensions_m'],'mesh_objects':v['source']['mesh_objects'],'validation':f'validation/{slug}.json','sha256':v['sha256'],'renders':{name:hashlib.sha256((ROOT/slug/'renders'/name).read_bytes()).hexdigest() for name in ['hero.png','rear.png']}})

now=datetime.now(timezone.utc)
manifest={'set':'Set01','status':'ready_for_review','packaged_at_utc':now.isoformat(),'references':'../../REF/Set01','imagegen':'built-in tool; four sequential main-agent generations before modeling','modeling':'main cargo_rover plus three gpt-6-astra workers explicitly set to reasoning_effort=max','assets':records,'limitations':['Static geometry; no rigging, animation, LOD chain or collision assets.','Per-component UVs; no cross-object atlas or uniform measured texel density.','Solid named PBR materials; FBX target-engine shader adjustment may be required.','Validated in Blender, not imported into Unreal or another game engine.']}
(ROOT/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

lines=['# Set 01 — 둥근 산업형 게임 에셋 4종','', '레퍼런스 이미지 4장을 메인에서 순차 생성한 후, 메인과 max 추론 서브에이전트 3개가 각각 모델 하나씩 병렬 제작했습니다. 아래 미리보기는 실제 Blender 렌더입니다.','', '| 모델 | BLEND | GLB | FBX | 삼각형 수 | 크기 X × Y × Z (m) |','|---|---|---|---|---:|---|']
for r in records:
    s=r['slug'];d=' × '.join(f'{x:.2f}' for x in r['dimensions_m'])
    lines.append(f'| {r["name_ko"]} | [편집 파일]({s}/{s}.blend) | [GLB]({s}/{s}.glb) | [FBX]({s}/{s}.fbx) | {r["triangles"]:,} | {d} |')
lines+=['','각 모델은 편집 가능한 개별 부품과 이름이 지정된 PBR 재질을 포함합니다. `ASSET` 컬렉션은 모델, `STUDIO`는 미리보기용 조명·카메라·바닥입니다. 내보낸 GLB/FBX에는 모델 형상만 포함됩니다.','', '## 실제 모델 미리보기','']
for r in records:
    s=r['slug'];lines +=[f'### {r["name_ko"]}','',f'![{r["name_ko"]} 실제 Blender 렌더]({s}/renders/hero.png)','',f'[후면 렌더]({s}/renders/rear.png) · [생성 레퍼런스](../../REF/Set01/{s}.png) · [제작 기록]({s}/RESULT.md) · [재검증]({r["validation"]})','']
lines+=['## 확인한 사항','','모든 저장 BLEND와 재수입 GLB·FBX에서 크기와 삼각형 수가 일치했습니다. 누락된 UV·재질·외부 이미지, 비정상 좌표, 면적이 0인 삼각형은 공통 검증에서 발견되지 않았습니다. 앞·뒤 실제 렌더는 메인에서 직접 확인했습니다.','','## 범위와 한계','','정적 모델이며 리깅·애니메이션·LOD·충돌 메시와 엔진 통합은 포함하지 않습니다. UV는 부품별로 제공하며 통합 아틀라스와 공통 텍셀 밀도를 맞추는 작업은 수행하지 않았습니다. 재질은 단색 PBR 중심으로, 레퍼런스의 미세한 오염 표현을 텍스처로 굽지는 않았습니다. FBX 재질은 사용하는 엔진에서 조정이 필요할 수 있습니다.','','레퍼런스 원본과 최종 프롬프트는 [REF/Set01](../../REF/Set01)에, 생성 시각은 [generation_manifest.json](../../REF/Set01/generation_manifest.json)에 있습니다.','']
(ROOT/'README.md').write_text('\n'.join(lines),encoding='utf-8')

plan_path=ROOT/'PLAN.md'
plan_path.write_text(plan_path.read_text(encoding='utf-8').replace('- [ ] Reopen final files','- [x] Reopen final files'),encoding='utf-8')
progress_path=ROOT/'PROGRESS.md'
progress=progress_path.read_text(encoding='utf-8')
progress+='\n- Final review index and delivery manifest prepared at '+now.isoformat()+'. All four model files match their independently checked SHA-256 records.\n'
progress_path.write_text(progress,encoding='utf-8')

files=[ROOT/p for p in ['README.md','BRIEF.md','PLAN.md','PROGRESS.md','delivery_manifest.json','validate_asset.py','prepare_delivery.py']]
for slug,_ in ASSETS:
    d=ROOT/slug
    # Include source and referenced evidence logs, but omit redundant Blender backups.
    allowed={'.blend','.glb','.fbx','.png','.py','.md','.json','.log','.txt'}
    files += sorted(p for p in d.rglob('*') if p.is_file() and p.suffix.lower() in allowed and '__pycache__' not in p.parts)
    files.append(ROOT/'validation'/f'{slug}.json')
files+=sorted((PROJECT/'REF'/'Set01').glob('*'))
files=list(dict.fromkeys(p.resolve() for p in files if p.is_file()))
archive=ROOT/'Set01-delivery.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:z.write(p,p.relative_to(PROJECT).as_posix())
with zipfile.ZipFile(archive,'r') as z:
    assert z.testzip() is None,'Archive CRC verification failed'
archive_hash=hashlib.sha256(archive.read_bytes()).hexdigest()
(ROOT/'Set01-delivery.sha256').write_text(archive_hash+'  Set01-delivery.zip\n',encoding='ascii')
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'file_count':len(files),'sha256':archive_hash,'assets':records},ensure_ascii=False,indent=2))
