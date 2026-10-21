from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,shutil
ROOT=Path('D:/github/AstraEffort/ForestDemo');WORK=ROOT/'Work/MountainStation/xhigh';SCRATCH=ROOT/'Saved/Workers/MountainStation/xhigh'
status=json.loads((WORK/'STATUS.json').read_text(encoding='utf-8-sig'))
validation=json.loads((WORK/'Evidence/validation.json').read_text());runtime=json.loads((WORK/'Evidence/runtime_validation.json').read_text());visual=json.loads((WORK/'Evidence/visual_review.json').read_text())
published=json.loads((WORK/'Evidence/published_hashes.json').read_text());timings=json.loads((WORK/'Evidence/process_timings.json').read_text());manifest=json.loads((WORK/'Screenshots/capture_manifest.json').read_text())
assert validation['success'] and runtime['success'] and visual['four_scene_images_inspected'] and visual['native_hello_visible']
shutil.copy2(SCRATCH/'Logs/capture_delivery.log',WORK/'Evidence/runtime_ue.log')
now=datetime.now(timezone.utc);started=datetime.fromisoformat(status['started_at_utc'].replace('Z','+00:00'));kst=timezone(timedelta(hours=9));elapsed=(now-started).total_seconds()
wait=sum(t['wait_seconds'] for t in timings);execution=sum(t['execution_seconds'] for t in timings)
supplement_start=datetime.fromisoformat('2026-10-21T12:46:44+00:00')
supplement={'started_at_utc':supplement_start.isoformat(),'finished_at_utc':now.isoformat(),'elapsed_seconds':(now-supplement_start).total_seconds(),'first_pie_evidence':'Evidence/runtime_validation_first.json','final_pie_execution_seconds':runtime['pie_execution_seconds'],'shared_session_accounting':'PIE checks were combined with map repairs and capture passes. Per-process wait/execution values are in process_timings.json; they are not claimed to be exclusively runtime validation overhead.','combined_sessions':[t for t in timings if t['name'] in ['capture2','capture3','capture4','capture_final','capture_verified','capture_delivery']]}
(WORK/'Evidence/supervisor_supplement_timing.json').write_text(json.dumps(supplement,indent=2))
rows='\n'.join(f"| {t['name']} | {t['wait_seconds']:.3f} | {t['execution_seconds']:.3f} | {t['exit_code']} |" for t in timings)
scene_files='\n'.join(f"- `{c['name']}.png`: {c['captured_at_utc']}" for c in manifest['captures'])
report=f'''# MountainStation / xhigh — Alder Pass

Status: **ready_for_review**. 독립 제작한 100×100m 산악 역 장면입니다. 최종 에디터 종료 후 소유 에셋과 맵만 게시했고, {len(published['files'])}개 게시 파일의 SHA-256이 private 프로젝트 원본과 일치합니다. Git index, branch, commit, push 작업은 하지 않았습니다.

## 실제 시간

- 시작 UTC: {started.isoformat()}
- 시작 KST: {started.astimezone(kst).isoformat()}
- 완료 UTC: {now.isoformat()}
- 완료 KST: {now.astimezone(kst).isoformat()}
- 총 벽시계 경과: **{elapsed:.3f}초** ({elapsed/60:.2f}분). 시작 시각을 재설정하지 않았습니다.
- UE mutex 대기 합계: **{wait:.3f}초**.
- UE 프로세스 실행 합계: **{execution:.3f}초**. 실패·재시도와 최종 캡처를 모두 포함합니다.
- 최종 editor-world 검증: {validation['elapsed_seconds']:.3f}초. 최종 캡처/검증 스크립트: {manifest['elapsed_seconds']:.3f}초. 최종 PIE 생명주기: {runtime['pie_execution_seconds']:.3f}초. 이 값들은 UE 프로세스 실행 시간에 포함되며 별도로 더하지 않습니다.
- 감독 보완 시작: 2026-10-21 12:46:44 UTC / 21:46:44 KST. 종료: {now.isoformat()}. 수정·캡처와 같은 프로세스에 통합되어 배타적인 추가 비용으로 해석하지 않습니다. 자세한 기록: `Evidence/supervisor_supplement_timing.json`.
- 첫 제출은 이 ready-for-review 기록입니다. 이전 중간 작업은 제출 완료로 기록하지 않았습니다.

| 실행 | mutex 대기 초 | UE 실행 초 | 종료 코드 |
|---|---:|---:|---:|
{rows}

`build`는 최초 조립입니다. `capture`는 배경 충돌, `capture2`는 진입로 높이와 등 받침과 겹친 표본을 발견했습니다. `capture3`에서 모든 정적 검증이 통과했으나 비동기 Python 자동 종료로 렌더가 실행되지 않았습니다. `capture4`에서 실제 렌더와 첫 PIE 검증을 수행했습니다. `capture_final`은 조명·터널 보강 및 바닥 표본 정밀화, `capture_verified`는 native sRGB 출력 점검입니다. 이때 직접 이미지와 실제 회전값을 대조해 평면샷의 Rotator 위치 인수 축 오류를 발견했습니다. `capture_delivery`가 명시적 pitch/yaw/roll, 정리된 터널 통과 공간, native sRGB를 사용한 최종 캡처입니다. 종료 코드 0만을 검증 성공으로 취급하지 않았습니다.

## 산출물

- 맵: `Content/Maps/MountainStation_xhigh.umap` — `/Game/Maps/MountainStation_xhigh`.
- 소유 에셋: `Content/MountainStation/xhigh/` — 9개 의미별 StaticMesh와 27개 머티리얼.
- 원본: `Work/MountainStation/xhigh/SourceArt/AlderPass.blend`, 9개 FBX, 팔레트와 geometry manifest.
- 생성·보완·검증·캡처·게시 Python/PowerShell 스크립트: 이 Work 폴더.
- 실제 UE 비교 이미지: `Screenshots/overview.png`, `top_down.png`, `platform.png`, `tracks.png` 및 `capture_manifest.json`.
- 증거: `Evidence/validation.json`, `runtime_validation.json`, `runtime_ue.log`, `runtime_hello.png`, `visual_review.json`, `baseline_native.json`, `published_hashes.json`, `process_timings.json`.

## 장면 및 검증

크림색 목조 역과 청록색 지붕, 곡선 플랫폼·연속 레일·침목·자갈층, 접선 방향의 석조 아치와 실제 빈 터널 내부, 화물 캐노피, 언덕 산책길, 97그루의 전나무를 구성했습니다. 벤치, 역명판, 시계, 시간표, 조명, 여행 가방, 나무 상자, 통, 울타리, 이정표와 화분을 직접 제작했습니다. 서쪽 진입로에서 완만한 램프로 승강장까지 연결됩니다.

- 저장 맵 재로드와 UE MapCheck가 통과했습니다. 사이트 지형은 XY 각각 10,000.00098cm이며 부동소수점 오차 범위입니다.
- Asset Registry로 맵과 소유 에셋의 hard/soft/editor/game/management 의존성을 재귀 검사했습니다. 다른 `/Game` 루트 참조는 **0개**입니다.
- World Partition 외부 액터/오브젝트 패키지와 map-adjacent BuiltData는 없습니다. 동적 조명과 `force_no_precomputed_lighting`을 사용합니다.
- 시작 지점, 램프 하단·중간·상단, 플랫폼 3점, 선로 바닥, 산책길의 차단 충돌과 실제 높이를 확인했습니다.
- 실제 `/Game/Maps/UEDPIE_0_MountainStation_xhigh`에서 PlayerController와 DefaultPawn 생성·빙의, PlayerStart (-3800,-300,135)cm, 100cm sweep 이동, 접근로·램프·플랫폼 바닥 actor에 대한 하향 Pawn sweep 및 정상 PIE 종료를 확인했습니다.
- 네이티브 ScreenDebugLogger 소스는 베이스 `7558c8f`와 byte-for-byte 동일합니다. 실제 PIE 화면의 녹색 **Hello**를 직접 확인했습니다. 해당 추가 증거에는 의도적으로 에디터 UI가 포함되며 네 비교 캡처와 분리됩니다.
- Blender/FBX의 좌표계 변환을 보정하는 Y scale -1을 모든 authored assembly에 사용했습니다. 이 변환을 validation actor 목록에 기록했고, 비교 카메라를 위해 장면을 회전시키지는 않았습니다.

## 실제 캡처와 직접 검토

모두 UE 5.7 SceneCapture2D의 1920×1080 native PNG입니다. High 품질(sg 그룹 2), screen percentage 100, FinalColorLDR + RTF_RGBA8_SRGB를 사용했습니다. 편집기 선택선·그리드·기즈모·UI·Hello는 네 비교 이미지에 없습니다. 이미지 생성 도구와 외부 색 보정은 사용하지 않았습니다. 초기 선형 렌더 타깃의 어두운 PNG는 최종 sRGB 캡처로 대체했습니다.

중심 (0,0), 지면 Z0=22cm. Overview 위치 (12000,-12000,16022), 지면 중심 주시, 직교 폭 20000cm. Top-down 위치 (0,0,20022), 회전 (-90,0,0), 직교 폭 20000cm. 상세 두 장은 보행면 위 170cm, 수평 FOV 70도입니다. 정확한 회전, 시각, 설정은 manifest에 있습니다.

{scene_files}

네 이미지를 직접 열어 전체 사이트, 선로와 플랫폼의 연결, 아치 입구, 역과 소품의 가독성 및 빈/검정 화면이 아님을 확인했습니다. 관찰 내용은 `Evidence/visual_review.json`에 기록했습니다.

## 한계

- 실제 PIE 화면에 두 방향광의 동일 우선순위 경고가 표시됩니다. 엔진이 밝기를 기준으로 주 방향광을 선택하는 fallback을 사용합니다. 네 비교 캡처에는 UI가 없으며, 이 경고를 해결했다고 주장하지 않습니다.
- 공통 overview 카메라에서 가장 먼 높은 지형 모서리가 화면 상단에 조금 잘립니다. top-down은 전체 사이트 범위를 보여줍니다. 파스텔 조명으로 원경의 작은 디테일 대비가 낮습니다.
- 정적 외부 환경입니다. 역 실내, 열차 운행, 철도 시뮬레이션은 구현하지 않았고 터널 뒤는 닫힌 배경입니다.
- 엔진 기본 DefaultPawn의 비행 이동을 사용합니다. 전용 보행 캐릭터나 내비게이션 시스템을 새로 구현하지 않았습니다. 런타임 충돌은 실제 Pawn sweep으로 확인했습니다.
- 9개 의미별 결합 메시 구조입니다. 인스턴싱/LOD 최적화나 FPS 성능 벤치마크를 수행한 결과로 주장하지 않습니다.

## 외부 참조

외부 창작 에셋·다른 작업의 원본은 사용하지 않았습니다. 공유 read-only 참조는 베이스 `/Script/ForestDemo`, `/Engine/BasicShapes/Sphere`, `/Engine/MapTemplates/Sky/DaylightAmbientCubemap`입니다. 엔진 Python API와 로컬 UE 5.7 C++ 헤더/구현을 확인했습니다: [SceneCaptureComponent2D](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SceneCaptureComponent2D?application_version=5.7), [RenderingLibrary](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/RenderingLibrary?application_version=5.7), [LevelEditorSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/LevelEditorSubsystem?application_version=5.7).
'''
(WORK/'RESULT.md').write_text(report,encoding='utf-8')
status.update(status='ready_for_review',finished_at_utc=now.isoformat(),finished_at_kst=now.astimezone(kst).isoformat(),elapsed_seconds=elapsed,first_ready_at_utc=status.get('first_ready_at_utc') or now.isoformat(),updated_at_utc=now.isoformat(),validation={'editor':validation['checks'],'runtime':runtime['checks'],'native_hello_visible':True,'screenshots':'4 actual UE 1920x1080 native sRGB PNGs visually inspected','published_files':len(published['files']),'hash_match':True},blockers=[],known_limitations=['PIE displays equal-priority directional light warning; engine selects brighter light as fallback.','DefaultPawn flying movement; no bespoke walking controller.','Static exterior; tunnel rear closed; no performance benchmark.'],mutex_wait_seconds=wait,ue_execution_seconds=execution,supervisor_supplement_finished_at_utc=now.isoformat())
(WORK/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
p=WORK/'PLAN.md';p.write_text(p.read_text().replace('- [ ]','- [x]'))
print(json.dumps({'status':status['status'],'elapsed_seconds':elapsed,'mutex_wait_seconds':wait,'ue_execution_seconds':execution,'finished_at_utc':now.isoformat()},indent=2))
