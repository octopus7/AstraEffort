import json, datetime, collections
from pathlib import Path
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra')
SCRATCH=Path(r'D:/github/AstraEffort/ForestDemo/Saved/Workers/ultra')
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
status=read(ROOT/'STATUS.json');validation=read(ROOT/'validation.json');runtime=read(ROOT/'runtime_validation.json');pub=read(ROOT/'publication.json');visual=read(ROOT/'visual_review.json');capture=read(ROOT/'Screenshots/capture_manifest.json');ready=read(ROOT/'scene_ready_time.json')
assert validation['success'] and runtime['success'] and pub['verified_copy'] and visual['approved']
assert all(n in [v['name'] for v in capture['views']] for n in ['overview','top_down','lake','beach'])
started=datetime.datetime.fromisoformat(status['started_at_utc'].replace('Z','+00:00'));finished=datetime.datetime.now(datetime.timezone.utc);kst=datetime.timezone(datetime.timedelta(hours=9))
timings=[read(p) for p in sorted(SCRATCH.glob('timing-*.json'))]
wait=sum(t['wait_seconds'] for t in timings)
elapsed=(finished-started).total_seconds()
maxerr=max(x['height_error_cm'] for x in runtime['traces'])
capture_start=datetime.datetime.fromisoformat(capture['capture_started_at_utc']);capture_end=datetime.datetime.fromisoformat(capture['capture_finished_at_utc'])
text=f'''# ultra — Quietwater Grove

상태: **ready_for_review**. 에디터를 종료한 뒤 전용 최종 경로로 복사했으며, 원본과 최종 사본 {len(pub['files'])}개 파일의 SHA-256 일치를 확인했습니다. Git 스테이징·커밋·브랜치 변경·푸시는 하지 않았습니다.

## 실제 시간

| 항목 | UTC | KST |
|---|---|---|
| 작업 시작 | {started.isoformat()} | {started.astimezone(kst).isoformat()} |
| 최종 장면 저장 | {ready['scene_saved_at_utc']} | {datetime.datetime.fromisoformat(ready['scene_saved_at_utc']).astimezone(kst).isoformat()} |
| 최종 촬영 시작 | {capture_start.isoformat()} | {capture_start.astimezone(kst).isoformat()} |
| 최종 촬영 완료 | {capture_end.isoformat()} | {capture_end.astimezone(kst).isoformat()} |
| 검증·게시·보고 완료 | {finished.isoformat()} | {finished.astimezone(kst).isoformat()} |

총 실제 경과 시간: **{elapsed:.3f}초 ({elapsed/60:.2f}분)**. 이 시간에는 제작, 엔진 초기화, 오류 수정, 렌더 준비, 자원 대기와 검증이 포함됩니다. 순수 모델 추론 시간으로 해석하면 안 됩니다.

최종 촬영 패스: {(capture_end-capture_start).total_seconds():.3f}초. 첫 카메라는 45초, 다음 카메라는 각각 12초 렌더 준비 시간을 두었습니다. 이전 시각 검토 패스(12:27:12–12:28:46, 12:34:05–12:35:39, 12:42:39–12:44:13, 12:50:13–12:51:47 UTC)에서 회전/머티리얼 문제를 발견하고 재촬영했으므로 최종 스크린샷은 이전 결과를 대체합니다. 추가 캡처 요구에 따른 작업과 제작 보정은 시간상 일부 겹칩니다.

경로 변경 처리는 12:20:57 UTC에 시작했고 새 /Game/Forest/ultra 패키지를 사용한 첫 맵은 12:24:37 UTC까지 저장했습니다. 이 220초 구간에는 새 경로 재생성과 정상 렌더 백엔드 재시도가 함께 포함됩니다. 시작 시각은 재설정하지 않았습니다. .uasset을 OS 폴더 이동만으로 마이그레이션하지 않았습니다.

공유 Unreal 실행 슬롯 누적 대기: **{wait:.3f}초**. 개별 실제 기록:

| 실행 | 대기 초 | 실행 초 | 종료 코드 |
|---|---:|---:|---:|
'''
for t in timings:text+=f"| {Path(t['log']).name} | {t['wait_seconds']:.3f} | {t['execution_seconds']:.3f} | {t['exit_code']} |\n"
text+='''
## 전달물

- `ForestDemo/Content/Maps/ultra.umap` → `/Game/Maps/ultra`
- `ForestDemo/Content/Forest/ultra/Meshes/` — 직접 제작한 Static Mesh 27종
- `ForestDemo/Content/Forest/ultra/Materials/` — 머티리얼 25종
- `ForestDemo/Work/ultra/SourceArt/` — 재생성 가능한 Blender 원본 및 개별 FBX
- `generate_art.py`, `scene_manifest.json`, `build_level.py`, `refine_and_review.py`, `review_pipeline.py`, `validate_level.py`, `validate_runtime.py`, `capture_level.py`, `publish.ps1` — 제작·검증·게시 절차
- `validation.json`, `runtime_validation.json`, `mesh_import_report.json`, `visual_review.json`, `publication.json` — 검증 및 해시 증거
- `Screenshots/overview.png`, `top_down.png`, `lake.png`, `beach.png`, 추가 `hero.png` 및 `capture_manifest.json`

## 장면 구성

100×100m의 연속 지형에 중앙 서쪽의 약 24×19m 호수, 별개의 남쪽 해변, 숲과 초지를 잇는 굽은 흙길을 구성했습니다. 호수와 해변 사이에는 건조한 초지와 산책길이 있어 수면이 연결되지 않습니다. 좌표는 원본 Blender 설계에서 UE로 변환할 때 Y축이 반전되므로 UE에서는 해안이 +Y 쪽입니다. 비교 촬영을 위해 장면 자체를 회전시키지는 않았습니다.

수목은 활엽수 5종·침엽수 3종으로 총 104그루입니다. 작은 가지와 뿌리, 비대칭의 둥근 수관, 휘어진 소나무 잎 층을 직접 모델링했습니다. 바위는 5종을 73개 배치하고, 낮은 풀 556개·고사리 102개·꽃 52개·갈대 28개·쓰러진 통나무 5개·작은 호숫가 데크와 벤치를 더했습니다. 총 StaticMeshActor는 926개입니다.

지형은 144×144 쿼드 표면이며 모래·잔디·호수 가장자리·산책길을 버텍스 컬러로 부드럽게 섞었습니다. 세이지/이끼 녹색, 따뜻한 모래, 회녹색 돌, 풍화된 목재, 차분한 청록색 물을 사용했습니다. 바위와 수관은 불규칙한 둥근 면으로 만들고 목재 모서리는 bevel 처리했습니다. 장식 구름, 얼굴, 하트 모티프는 없습니다.

산책길의 PlayerStart에서 호숫가 데크 및 숲 안쪽으로 이동할 수 있습니다. 지형·나무·데크는 정적 복합 충돌, 바위·통나무·벤치는 단순 볼록 충돌을 사용합니다. 작은 식생과 수면은 이동을 방해하지 않습니다. 기본 `/Script/ForestDemo.ScreenDebugLogger` 인스턴스가 있으며 원본의 BeginPlay `Hello` 동작을 유지했습니다. 캡처에는 UI/디버그 문구가 포함되지 않습니다.

## 검증 증거

'''
for key,c in validation['checks'].items():text+=f"- `{key}`: {'PASS' if c['passed'] else 'FAIL'}\n"
text+=f'''
실제 지형 크기는 **10000.0009766 × 10000.0009766cm**입니다. 새 프로세스에서 저장 맵을 재로드했고, Asset Registry로 맵과 전체 전용 자산 {validation['checks']['recursive_game_dependencies']['detail']['packages_checked']}개 패키지를 재귀 탐색하여 허용 루트 밖 `/Game` 참조 **0건**을 확인했습니다. World Partition은 None이고 외부 액터·외부 오브젝트·BuiltData 패키지가 없습니다. Engine 내장 참조와 기본 native 클래스 참조만 공유합니다.

실제 Play In Editor에서 지면 6지점을 수직 트레이스했고 최대 원본 높이 차이는 **{maxerr:.4f}cm**였습니다. PlayerStart 아래의 지면, 활엽수·침엽수 줄기와 바위의 실제 차단 충돌, native logger 1개도 확인했습니다. 에디터 월드의 초기 트레이스는 물리 장면이 실행되지 않아 None이었고, 이를 성공으로 바꾸어 기록하지 않고 별도의 실제 PIE 결과로 검증했습니다.

감독 보완 시작은 {runtime.get('supervisor_supplement_started_at_utc')}, 완료는 {runtime.get('supervisor_supplement_finished_at_utc')}입니다. 첫 ready_for_review 제출 전에 요청되어 이미 대기 중이던 최종 렌더 세션에 통합했으며, 보완만을 위한 별도 에디터 프로세스나 추가 아트 변경은 없었습니다. 해당 슬롯의 대기·실행 시간은 위 `final-review.log` 행에 포함됩니다. 실제 `{runtime.get('player_test',{}).get('controller')}`가 `{runtime.get('player_test',{}).get('pawn')}`를 빙의했고, 수평 sweep 이동 {runtime.get('player_test',{}).get('horizontal_move_cm',0):.3f}cm 및 지형으로의 하강 sweep 차단을 확인했습니다. PIE 정상 종료 확인: **{runtime.get('normal_play_exit')}**. 원본 native logger는 실행 중 PIE에 존재하며 baseline BeginPlay의 Hello 호출 코드는 변경하지 않았습니다. 깨끗한 캡처에서 Hello 글자를 직접 관찰했다고 주장하지는 않습니다.

실행은 전용 scratch의 `ForestDemo.uproject`를 사용합니다. 감독자 도입 이후 UE 실행에는 `ForestDemo/Work/Tools/Run-UnrealIsolated.ps1 -Project <private> -LogPath <owned> -TimingPath <owned> -EditorArguments ...`를 사용했습니다. 재현 시 `generate_art.py` → `build_level.py` → `refine_and_review.py` 순서입니다. 상세 명령 인수와 상태는 스크립트·개별 UE 로그·timing JSON에 남아 있습니다. private 로그 경로는 `ForestDemo/Saved/Workers/ultra/logs/`입니다.

## 캡처

모두 최종 맵의 실제 UE5.7 D3D12 SM5 SceneCapture2D 렌더입니다. 1920×1080, High scalability(sg=2), ScreenPercentage 100, map 후처리를 사용했습니다. 이미지 생성이나 사후 색 보정은 하지 않았습니다. 저자는 5장을 직접 열어 검정/빈 화면, 수목 회전, 물, 프레이밍 및 UI 부재를 확인했습니다. PNG 크기·픽셀 범위·서로 다른 해시는 `publication.json`에 있습니다.

사이트 중심 `(0,0)`, 기준 높이 `Z0=0cm`입니다. overview는 위치 `(12000,-12000,16000)`, 타깃 `(0,0,0)`, 직교 폭 `20000cm`입니다. top_down은 `(0,0,20000)`, pitch `-90`, yaw/roll `0`, 직교 폭 `20000cm`입니다. lake/beach는 지면 +170cm와 수평 FOV 70도를 사용했습니다. 두 근접 시점의 위치와 프레이밍은 장면별로 달라 직접적인 구도 동등 비교에는 한계가 있습니다. 모든 실제 회전과 촬영 시각은 `Screenshots/capture_manifest.json`에 있습니다.

'''
for name in ['overview','top_down','lake','beach']:
 text+=f"### {name}\n\n![{name}](D:/github/AstraEffort/ForestDemo/Work/ultra/Screenshots/{name}.png)\n\n"
text+='''## 알려진 한계와 재사용

- 물은 장식용 불투명 절차 머티리얼입니다. 수영·부력·상호작용 물리와 실제 파도 시뮬레이션은 구현하지 않았습니다.
- 지정 overview 직교 각도에서는 수면 반사가 밝게 보입니다. 이를 숨기기 위해 카메라나 이미지를 변경하지 않았으며, top_down·lake·beach·hero에서는 청록색 수면이 읽힙니다. 사이트 밖 배경 월드는 제작하지 않아 100m 경계가 보입니다.
- 자체 플레이어 캐릭터/게임 모드, NavMesh나 경계 제한 시스템은 추가하지 않았습니다. 제공된 baseline과 PlayerStart를 사용합니다.
- 수목의 복합 충돌과 개별 StaticMeshActor 배치는 이 작은 환경의 검증에 맞춘 선택입니다. 대규모 확장 시 HISM/LOD/충돌 단순화가 필요합니다.
- 조명은 동적입니다. SM5에서는 Lumen 대신 지정 cubemap 환경광과 map 후처리의 ambient fill을 사용하며, SM6/Lumen 성능 검증은 하지 않았습니다.
- 절차 생성기는 deterministic seed와 명시적인 asset/placement manifest를 사용합니다. 원본 메시·색 팔레트·배치 구조를 따로 수정해 다시 생성할 수 있습니다.
- 모든 작업과 최종 검토를 이 채팅에서 직접 수행했습니다. 다른 effort나 MountainStation의 에셋/스크립트/이미지를 열거나 복사하지 않았습니다. 별도 reviewer 모델이나 서브에이전트 평가를 사용하지 않았습니다.

외부 아트 참조/다운로드는 없습니다. 허용된 `/Engine/MapTemplates/Sky/DaylightAmbientCubemap`을 환경광에 사용했습니다. API 확인 참고: [Epic Rotator 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/Rotator?application_version=5.7), [Epic HitResult 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/HitResult?application_version=5.7). 공유 Source/Config/Plugins/uproject/main.umap/Binaries는 수정하지 않았으며, baseline 7558c8f의 파일과 기존 native binaries를 private 프로젝트에만 복사했습니다.
'''
(ROOT/'RESULT.md').write_text(text,encoding='utf-8')
status.update(status='ready_for_review',finished_at_utc=finished.isoformat(),finished_at_kst=finished.astimezone(kst).isoformat(),first_submission_at_utc=status.get('first_submission_at_utc',finished.isoformat()),elapsed_seconds=round(elapsed,3),map='/Game/Maps/ultra',asset_root='/Game/Forest/ultra',supervisor_supplement={'started_at_utc':runtime.get('supervisor_supplement_started_at_utc'),'finished_at_utc':runtime.get('supervisor_supplement_finished_at_utc'),'merged_into_existing_queued_session':True,'timing_record':'Saved/Workers/ultra/timing-final-review.json'},validation={'success':True,'checks':{k:v['passed'] for k,v in validation['checks'].items()},'recursive_packages':validation['checks']['recursive_game_dependencies']['detail']['packages_checked'],'dependency_violations':0,'runtime_max_ground_error_cm':maxerr,'screenshots':5,'resolution':[1920,1080],'published_files':len(pub['files']),'hash_verified':True,'resource_wait_seconds':wait,'path_change_started_at_utc':'2026-10-21T12:20:57Z','path_regeneration_first_saved_at_utc':'2026-10-21T12:24:37Z','path_change_processing_interval_seconds':220},blockers=[])
(ROOT/'STATUS.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
print(json.dumps({'status':status['status'],'finished_at_utc':status['finished_at_utc'],'finished_at_kst':status['finished_at_kst'],'elapsed_seconds':status['elapsed_seconds'],'wait_seconds':wait},indent=2))
