"""Offline delivery gate. Run only after the private editor has exited."""
import os,json,hashlib,shutil,datetime,struct
from pathlib import Path
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/xhigh')
PROJECT=Path('D:/github/AstraEffort/ForestDemo/Saved/Workers/xhigh/Project/ForestDemo')
SCRATCH=PROJECT.parents[1]
FINAL=Path('D:/github/AstraEffort/ForestDemo')
UTC=datetime.timezone.utc;KST=datetime.timezone(datetime.timedelta(hours=9))
def dt(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
state=json.loads((ROOT/'STATUS.json').read_text(encoding='utf-8-sig'))
val=json.loads((ROOT/'validation.json').read_text())
cap=json.loads((ROOT/'Screenshots/capture_manifest.json').read_text())
build=json.loads((ROOT/'build_summary.json').read_text())
runtime_report=json.loads((ROOT/'runtime_validation.json').read_text())
assert val['passed'],val['errors']
assert runtime_report['passed'],runtime_report['errors']
assert len(cap['views'])==4 and cap.get('finished_at_utc')
assert (ROOT/'Screenshots/visual_review.json').exists(),'Direct visual review must be recorded first'
review=json.loads((ROOT/'Screenshots/visual_review.json').read_text())
assert review['all_four_directly_inspected'] and review['accepted']
assert runtime_report['checks'].get('baseline_native_hello_beginplay_test'), 'Baseline native BeginPlay test must pass'
assert not val['forbidden_game_dependencies']
assert val['world_partition']=='None'
assert not list((PROJECT/'Content/Maps').glob('*BuiltData*'))
assert not (PROJECT/'Content/__ExternalActors__').exists()
assert not (PROJECT/'Content/__ExternalObjects__').exists()
imgs={}
for name in ['overview','top_down','lake','beach']:
 p=ROOT/'Screenshots'/(name+'.png');raw=p.read_bytes()
 assert raw[:8]==b'\x89PNG\r\n\x1a\n'
 w,h=struct.unpack('>II',raw[16:24]);assert (w,h)==(1920,1080)
 imgs[name]={'bytes':len(raw),'resolution':[w,h],'sha256':sha(p)}
timings=[]
for p in SCRATCH.glob('*_timing.json'):
 t=json.loads(p.read_text(encoding='utf-8-sig'));t['file']=str(p);timings.append(t)
assert timings
assert dt(cap['finished_at_utc'])<=max(dt(t['finished_at_utc']) for t in timings),'Editor completion not recorded'
assert max(timings,key=lambda t:dt(t['finished_at_utc']))['exit_code']==0,'Last private editor did not exit normally'
source=PROJECT/'Content/Forest/xhigh';target=FINAL/'Content/Forest/xhigh'
assert source.is_dir()
shutil.copytree(source,target,dirs_exist_ok=True)
shutil.copy2(PROJECT/'Content/Maps/xhigh.umap',FINAL/'Content/Maps/xhigh.umap')
published=[]
for p in sorted(source.rglob('*')):
 if p.is_file():
  q=target/p.relative_to(source);assert sha(p)==sha(q)
  published.append({'file':str(q),'bytes':q.stat().st_size,'sha256':sha(q)})
p=PROJECT/'Content/Maps/xhigh.umap';q=FINAL/'Content/Maps/xhigh.umap';assert sha(p)==sha(q)
published.append({'file':str(q),'bytes':q.stat().st_size,'sha256':sha(q)})
now=datetime.datetime.now(UTC);start=dt(state['started_at_utc']);elapsed=(now-start).total_seconds()
wait=sum(t['wait_seconds'] for t in timings);runtime=sum(t['execution_seconds'] for t in timings)
evidence={'finished_at_utc':now.isoformat(),'published_files':published,'images':imgs,'timings':timings,
 'total_recorded_mutex_wait_seconds':wait,'total_recorded_mutex_execution_seconds':runtime,
 'publication_verified_sha256':True,'editor_closed_before_publication':True}
(ROOT/'delivery_evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
state.update(status='ready_for_review',started_at_utc=start.astimezone(UTC).isoformat(),finished_at_utc=now.isoformat(),elapsed_seconds=elapsed,
 validation={'passed':True,'checks':val['checks'],'packages_checked':val['checked_package_count'],'forbidden_game_dependencies':0,
 'actual_ue_render_png_count':4,'screenshots_directly_reviewed':True,'published_sha256_verified':True,'actual_pie_passed':runtime_report['passed'],'native_hello_beginplay_test_passed':True,'runtime_hello_visually_confirmed':review.get('runtime_hello_visible',False)},blockers=[],
 final_asset_root='/Game/Forest/xhigh',resource_queue_wait_seconds=wait,production_finished_at_utc=build['utc'],
 capture_started_at_utc=cap['started_at_utc'],capture_finished_at_utc=cap['finished_at_utc'],runtime_supplement_finished_at_utc=runtime_report['finished_at_utc'],current_phase='Published and verified; ready for supervisor review')
state.setdefault('first_submitted_at_utc',now.isoformat())
for k,v in list(state.items()):
 if k.endswith('_at_utc') and isinstance(v,str):state[k]=dt(v).astimezone(UTC).isoformat()
(ROOT/'STATUS.json').write_text(json.dumps(state,indent=2,ensure_ascii=False),encoding='utf-8')
path_start=dt(state['path_change_started_at_utc']);path_end=dt(state['path_change_regeneration_finished_at_utc'])
source_s=(dt(build['utc'])-start).total_seconds();capture_s=(dt(cap['finished_at_utc'])-dt(cap['started_at_utc'])).total_seconds()
maxerr=max(t['height_error_cm'] for t in val['terrain_traces'])
last_timing_name=Path(max(timings,key=lambda t:dt(t['finished_at_utc']))['file']).name
text=f'''# xhigh 결과 — Quiet Cove

상태: ready_for_review. Git 스테이징·커밋·브랜치 변경은 수행하지 않았습니다.

## 실제 시간

| 구간 | UTC | KST |
|---|---|---|
| 작업 시작 | {start.astimezone(UTC).isoformat()} | {start.astimezone(KST).isoformat()} |
| 최종 환경 저장 | {dt(build['utc']).astimezone(UTC).isoformat()} | {dt(build['utc']).astimezone(KST).isoformat()} |
| 최종 캡처 시작 | {dt(cap['started_at_utc']).astimezone(UTC).isoformat()} | {dt(cap['started_at_utc']).astimezone(KST).isoformat()} |
| 최종 캡처 종료 | {dt(cap['finished_at_utc']).astimezone(UTC).isoformat()} | {dt(cap['finished_at_utc']).astimezone(KST).isoformat()} |
| 게시·검증 완료 | {now.isoformat()} | {now.astimezone(KST).isoformat()} |

- 전체 실제 경과: **{elapsed:.3f}초**.
- 시작부터 최종 환경 저장까지: {source_s:.3f}초. 디버깅과 해당 구간의 자원 대기를 포함합니다.
- 최종 실제 렌더 캡처 구간: {capture_s:.3f}초. 이후 직접 이미지 확인과 게시 검증 시간을 전체 경과에 포함했습니다.
- 공유 named mutex에 기록된 대기 합계: **{wait:.3f}초**, 해당 유틸리티의 실행 합계: {runtime:.3f}초. 유틸리티 도입 이전 실행은 이 합계에 포함되지 않습니다. 대기시간은 전체 경과에 이미 포함됩니다.
- 사용자 Forest 경로 변경 적용 구간: {path_start.astimezone(UTC).isoformat()} → {path_end.astimezone(UTC).isoformat()}, {(path_end-path_start).total_seconds():.3f}초. /Game/Forest/xhigh 아래 UE 에셋을 재생성하고 맵을 재조립했습니다. 이 구간에는 병행한 API/실행 모드 수정도 포함되므로 순수 경로 변경만의 추가 비용으로 해석하지 않습니다. 시작 시각을 재설정하지 않았습니다.
- 감독 런타임 보완 착수: {state['runtime_supplement_started_at_utc']}. 실제 PIE 구간: {runtime_report['started_at_utc']} → {runtime_report['finished_at_utc']} ({runtime_report['elapsed_seconds']:.3f}초). 대기 중이던 캡처 세션에 합쳤으며 별도 맵 재설계는 없었습니다. 해당 세션의 mutex 대기·실행 값은 delivery_evidence.json의 {last_timing_name} 항목에 있습니다.

## 산출물과 구성

- 최종 맵: `ForestDemo/Content/Maps/xhigh.umap` → `/Game/Maps/xhigh`.
- 최종 에셋: `ForestDemo/Content/Forest/xhigh/` → `/Game/Forest/xhigh/`. 정적 메시 28종, 재질 22종. 게시 파일 {len(published)}개의 SHA-256이 private scratch 원본과 일치합니다.
- 원본: `SourceArt/QuietCove_Source.blend`, 개별 FBX 28개, `make_art.py`, `scene_manifest.json`.
- 재현·검증: `build_scene.py`, `validate_scene.py`, `capture_scene.py`, `capture_entry.py`, `finalize_delivery.py`, `AUTHORING.md`.
- 증거: `validation.json`, `delivery_evidence.json`, `Screenshots/capture_manifest.json`, `Screenshots/visual_review.json`.

100m 정사각형 지형 위에 남쪽 해변과 바다, 서북쪽 내륙 호수, 동·북쪽 완만한 숲 능선을 구성했습니다. 호수와 해변은 별도의 수면이며 육지와 숲으로 분리됩니다. 남쪽 열린 도착 지점에서 굽은 흙길을 따라 중앙 숲으로 들어가고 호수 동쪽의 작은 나무 데크와 벤치로 접근할 수 있습니다.

나무 {val['roles'].get('tree',0)}그루는 굽은 줄기·뿌리·분지와 겹치는 둥근 활엽수 수관 3종, 부드러운 층을 가진 침엽수 2종으로 구성했습니다. 바위 군집, 자갈, 양치식물, 풀, 갈대, 작은 꽃, 관목, 고사목, 그루터기, 벤치와 데크를 직접 제작했습니다. 지면 식생 {val['roles'].get('understory',0)}군집과 해변 자갈 {val['roles'].get('beach_stones',0)}군집, 해변 풀 {val['roles'].get('beach_grass',0)}군집, 호수 갈대 {val['roles'].get('lake_reeds',0)}군집을 배치했습니다. 색은 이끼·세이지·청록·모래·나무갈색을 사용하고 표면은 거칠고 둥글게 처리했습니다. 장식 구름이나 얼굴·하트 모티프는 없습니다.

## 검증 결과

- 새 UE 에디터 세션에서 맵을 실제 재로드했습니다. terrain XY bounds는 10000 × 10000cm(부동소수점 오차 0.001cm 수준)입니다.
- Asset Registry로 맵과 모든 소유 에셋의 의존성 {val['checked_package_count']}개 패키지를 재귀 검사했습니다. `/Game/Forest/xhigh/`와 자기 맵 이외 `/Game` 참조는 **0개**입니다. 이전 `/Game/xhigh/` 경로도 없습니다.
- WorldSettings의 WorldPartition은 None, 외부 액터 패키지는 0개입니다. 최종 Maps에 BuiltData를 생성하지 않았습니다.
- terrain의 complex collision을 실제 component line trace로 7지점 검사했습니다. 원본 높이와 최대 오차 {maxerr:.3f}cm, PlayerStart 지면 검사를 통과했습니다.
- 충돌 사용 정적 메시 액터 {val['collision_enabled_actor_count']}개. 물·지면 장식 식생에는 저장 후 재로드해도 NoCollision이 유지됩니다.
- PlayerStart, 개요 CameraActor, `/Script/ForestDemo.ScreenDebugLogger`가 있습니다. 기준 소스의 BeginPlay Hello 동작을 그대로 사용하는 네이티브 인스턴스입니다.
- 실제 PIE 월드에서 PlayerController/Pawn 생성과 빙의, PlayerStart 일치, 런타임 지형 trace, Pawn을 지면 아래로 이동시키는 sweep의 차단, 100cm 짧은 이동, 정상 PIE 종료를 검증했습니다. `runtime_validation.json`에 실제 위치와 체크 결과가 있습니다. 기준 바이너리에 포함된 `ForestDemo.ScreenDebugLogger.HelloOnBeginPlay` 자동화 테스트가 성공해 기존 BeginPlay의 화면 메시지 등록 동작을 실제 확인했습니다. Hello의 별도 화면 증거 직접 확인 여부는 {review.get('runtime_hello_visible',False)}이며, 네이티브 테스트의 실제 로그를 함께 보존합니다.
- 동적 DirectionalLight/SkyLight와 ForceNoPrecomputedLighting을 확인했습니다.
- 캡처는 최종 경로의 저장 맵을 실제 UE SceneCapture2D로 렌더링한 1920×1080 PNG 4장입니다. High(sg.*=2), screen percentage 100. 선택선·그리드·기즈모·콘솔·UI·Hello 오버레이 없이 촬영했습니다. 이미지 생성·보정은 하지 않았습니다.
- private 에디터 종료가 wrapper timing에 기록된 뒤 소유 경로만 복사하고 바이트 해시를 비교했습니다.

검증 실행은 `Run-UnrealIsolated.ps1 -Project <xhigh private ForestDemo.uproject> -LogPath <xhigh log> -TimingPath <xhigh timing.json> -EditorArguments @('-ExecutePythonScript=.../capture_entry.py','-RenderOffscreen','-windowed','-ResX=1920','-ResY=1080',...)`입니다. 전체 실제 명령·출력 경로는 이 대화와 자체 scratch 로그에 남아 있습니다. 원본 아트는 독립 Blender 4.5 `--background --factory-startup --python make_art.py`로 생성했습니다.

## 캡처

공통 사이트 중심 (Cx,Cy)=(0,0)cm, 기준 Z0={cap['ground_reference_z0_cm']:.3f}cm(사이트 중심의 지면 높이). 개요는 (12000,-12000,Z0+16000)→(0,0,Z0), 직교폭 20000cm. 탑뷰는 (0,0,Z0+20000), pitch -90/yaw 0/roll 0, 직교폭 20000cm입니다. 호수·해변은 실제 지면 +170cm, 수평 FOV 70도입니다. 각 위치·회전·시각은 capture_manifest.json에 기록했습니다. 장소별 눈높이 시점은 위치가 달라 직접 프레이밍 동등 비교에 한계가 있습니다.

![개요](Screenshots/overview.png)

![탑뷰](Screenshots/top_down.png)

![호수](Screenshots/lake.png)

![해변](Screenshots/beach.png)

## 한계와 참고

환경 레벨이며 별도 보행 캐릭터·수영·부력·AI 내비게이션이나 패키징 성능 인증은 구현하지 않았습니다. 수면은 스타일화한 불투명 재질입니다. 표면 충돌은 정적 complex collision로 검증했고 동적 물리 오브젝트 운용을 위한 convex 최적화는 하지 않았습니다. 기본 Pawn으로 실제 PIE/sweep 검증을 수행했습니다. Hello는 네이티브 자동화 테스트의 실제 메시지 등록 검사로 확인했으며 unattended PIE 화면 캡처에서는 문구가 보이지 않았습니다. 공통 비교용 네 장은 UI 없는 장면 캡처입니다.

초기 UE Interchange/NullRHI와 Python 바인딩 문제, FBX Y축 좌표 변환 및 저장되는 충돌 프로필 문제를 로그와 재로드 검사로 확인해 수정했습니다. 실제 렌더 검토 후 지면 VertexColor 출력·수면 unary 입력의 핀 연결과 환경광도 수정했습니다. 수정 내역은 PLAN.md에 기록했습니다. 외부 아트 다운로드·다른 effort의 에셋 사용은 없습니다. 허용된 엔진 내장 `/Engine/MapTemplates/Sky/DaylightAmbientCubemap`을 환경광용으로 읽기 전용 참조합니다. API 확인은 설치된 UE 5.7.4 헤더와 Python 런타임을 사용했습니다. 나머지 재료·배치·원본은 xhigh가 직접 작성했습니다. 평가는 자기 완료 조건에 한정하며 다른 결과와 비교 점수는 부여하지 않았습니다.
'''
(ROOT/'RESULT.md').write_text(text,encoding='utf-8')
print(json.dumps({'status':'ready_for_review','elapsed_seconds':elapsed,'finished_at_utc':now.isoformat(),'files':len(published),'mutex_wait_seconds':wait},ensure_ascii=False))
