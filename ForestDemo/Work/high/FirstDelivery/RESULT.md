# high — Quietwater Grove

검토 준비 완료. 최종 맵 `/Game/Maps/high`, 에셋 `/Game/Forest/high/`.

## 실제 시간

| 단계 | UTC | KST |
|---|---|---|
| 시작 | 2026-10-21T12:11:54+00:00 | 2026-10-21T21:11:54+09:00 |
| 최초 제작 맵 저장 완료 | 2026-10-21T12:19:43.558903+00:00 | 2026-10-21T21:19:43.558903+09:00 |
| 최종 캡처 시작 | 2026-10-21T12:38:34.878953+00:00 | 2026-10-21T21:38:34.878953+09:00 |
| 최종 캡처 종료 | 2026-10-21T12:39:36.823356+00:00 | 2026-10-21T21:39:36.823356+09:00 |
| 최종 검증·게시 완료 | 2026-10-21T12:40:14.899003+00:00 | 2026-10-21T21:40:14.899003+09:00 |

전체 실제 경과 **1700.899초**. 최초 맵 저장까지 469.559초, 이후 추가 검증·렌더·아트 보정·경로 이전·게시 1231.340초입니다. 후반 단계는 서로 섞여 진행되어 순수 아트 시간과 순수 캡처 시간을 임의로 나누지 않았습니다. 최종 캡처 실행 시간 76.424초, 공유 UE 실행 슬롯 누적 대기 271.650초입니다.

사용자 경로 변경은 시작 시각을 재설정하지 않고 처리했습니다. `/Game/high` → `/Game/Forest/high`를 UE `rename_directory`로 이전하여 직접 참조를 저장하고 redirector만 남은 옛 경로를 제거했습니다. 새 아트 재생성 없음. 기록된 실제 migration API 작업은 2.210초이며, 요청 기록 시각 2026-10-21T12:21:03+00:00, 실제 실행 시작 2026-10-21T12:23:21.903174+00:00, 완료 2026-10-21T12:23:24.112996+00:00입니다. 기존 렌더가 끝난 후 이 작업을 시작했으므로 요청부터 완료까지의 벽시계 간격은 순수 이전 작업 시간과 다릅니다.

## 장면 구성과 제작

100×100m의 연속 지형 위에 127그루의 활엽수·전나무를 배치했습니다. 북쪽은 침엽수가 섞인 높은 숲, 중앙은 굽은 산책길과 작은 빈터, 서쪽은 독립된 내륙 호수, 남쪽은 넓은 모래 해변과 해수면입니다. 호수 중심은 약 (-1700,700), 수면 Z=162cm이며 바다는 남쪽 해안 너머 Z=78cm에 있습니다. 두 물은 연결되지 않고 숲과 길로 접근합니다.

직접 제작한 재사용 메시 **22종**, 재질 **23종**, 저장된 액터 **761개**입니다. 가지가 갈라지는 둥근 활엽수 3종, 부드러운 층을 가진 전나무 2종, 이끼 바위 4종, 풀 2종, 고사리·갈대·야생화, 쓰러진 통나무, 난간이 있는 나무다리, 길 표식, 수면 잔물결을 포함합니다. 팔레트는 탁한 초록·회녹색·모래색·청록으로 제한했습니다. 얼굴·하트·장식 구름 모티프는 없습니다.

원본 `Source/QuietwaterGrove.blend`, FBX 22개, `make_art.py`, `scene.json`, `build_level.py`로 형상과 배치를 재현할 수 있습니다. 가져오기 과정의 좌표계 반전은 액터의 local Y scale로 보정했고 회전은 이름 있는 pitch/yaw/roll 인수를 사용합니다. 최종 동적 skylight는 공유 허용된 `/Engine/MapTemplates/Sky/DaylightAmbientCubemap`을 읽기 전용 사용합니다. 외부 다운로드나 다른 effort 에셋·코드 참조는 없습니다.

## 플레이와 검증

- 지형 범위: 10000.0010 × 10000.0010cm.
- terrain/bridge는 complex-as-simple 충돌, 나무·바위·통나무·표식은 convex 충돌. 작은 식생과 물은 비차단. BlockAll 메시 액터 245개.
- PlayerStart (650,-1900,407.739)cm. 실제 지면 Z=297.803cm으로 약 110cm 간격. 호수 바닥·해변·호수 촬영점까지 총 4개 ray trace가 지형에 맞았습니다.
- 기본 `/Script/ForestDemo.ScreenDebugLogger` 액터 1개를 보존했습니다. 기준 소스의 BeginPlay Hello 기능을 그대로 사용하며 shared Source/Binaries는 수정하지 않았습니다.
- 저장 후 별도 UE 실행에서 맵을 재로드했습니다. Asset Registry로 맵과 전체 소유 에셋 46개 패키지의 hard/soft 프로젝트 의존성을 재귀 검사했습니다. 허용 범위 밖 `/Game` 참조 0개, 옛 `/Game/high` 참조 0개입니다.
- `new_level`로 만든 non-World-Partition 레벨이며 external actor/object 패키지가 없습니다. 동적 조명과 force_no_precomputed_lighting 사용. Maps에는 high.umap만 전달합니다.
- 최종 UE 프로세스 종료 후 소유 에셋과 맵만 복사했으며, 파일 46개의 SHA-256이 scratch 원본과 같습니다. `delivery_manifest.json` 참조.

검증 실행: `Run-UnrealIsolated.ps1 -Project <high scratch>/ForestDemo.uproject -LogPath <high scratch>/ambient_capture.log -TimingPath <high scratch>/ambient_capture_timing.json -EditorArguments @('/Game/Maps/high','-ExecutePythonScript=<Work/high>/run_final.py','-NoSound','-RenderOffscreen')`. 실제 exit code 0. 최종 로그는 `Logs/final_validation_capture.log`, 세부 결과는 `validation.json`, `geometry_checks.json`, `migration.json`입니다.

## 실제 UE 스크린샷

각 PNG를 직접 열어 검정·빈 이미지가 아니며 장면이 보이는 것을 확인했습니다. 이미지 생성/보정은 하지 않았습니다. 1920×1080, High scalability, screen percentage 100, SceneCapture2D 최종 LDR이며 에디터 UI·기즈모·선택선·Hello 문구가 포함되지 않습니다. 위치·회전·투영·촬영 UTC는 `Screenshots/capture_manifest.json`에 있습니다.

공통 중심 (0,0), 지면 기준 Z0=300cm. overview=(12000,-12000,16300), target=(0,0,300), ortho width=20000cm. top_down=(0,0,20300), pitch=-90/yaw=0/roll=0, ortho width=20000cm. lake/beach는 실제 지형 hit 높이+170cm, horizontal FOV=70°입니다. 두 근접 이미지는 장소별 위치가 달라 직접적인 프레이밍 동등 비교에 한계가 있습니다.

![Overview](D:/github/AstraEffort/ForestDemo/Work/high/Screenshots/overview.png)
![Top down](D:/github/AstraEffort/ForestDemo/Work/high/Screenshots/top_down.png)
![Lake](D:/github/AstraEffort/ForestDemo/Work/high/Screenshots/lake.png)
![Beach](D:/github/AstraEffort/ForestDemo/Work/high/Screenshots/beach.png)

## 전달 파일과 한계

- `ForestDemo/Content/Forest/high/Materials/*.uasset`, `Meshes/*.uasset`
- `ForestDemo/Content/Maps/high.umap`
- `ForestDemo/Work/high/`의 소스·스크립트·검증 JSON·PNG·보고서

물은 스타일화된 불투명 정적 표면으로 수영·부력·파도 시뮬레이션은 구현하지 않았습니다. 섬 형태의 100m 사이트 밖에는 확장된 플레이 지형이 없습니다. 지면 재질 경계는 약 83cm 샘플 그리드이므로 탑뷰에서 계단 형태가 보일 수 있습니다. 최초 제출에서는 충돌을 설정 검사와 지형 trace로 확인했습니다. 아래 감독 보완에서 실제 PIE 기본 pawn 이동·충돌 검증을 추가했습니다. 별도 Character의 도보/점프 전체 동선 테스트와 FPS 벤치마크는 수행하지 않았습니다. 네이티브 Hello는 아래 감독 보완에서 기존 BeginPlay 자동화 테스트의 Success 로그로 검증했습니다. 화면에 보이는 Hello 문구 자체의 캡처 증거는 없습니다. 독립 검토는 감독자가 수행하며 이 작업은 직접 제작·자체 시각 검증했습니다. Git staging/commit/push는 실행하지 않았습니다.



## 감독 보완 — 실제 PIE 및 BeginPlay 검증

원래 시작 **2026-10-21T12:11:54Z**와 최초 ready **2026-10-21T12:40:14.899003Z**는 보존했습니다. 이번 보완 시작은 2026-10-21T12:41:24+00:00 (2026-10-21T21:41:24+09:00), 완료는 2026-10-21T13:02:06.461440+00:00 (2026-10-21T22:02:06.461440+09:00)입니다. 추가 경과 1242.461초, 공유 UE 대기 합계 904.313초, 실제 UE 실행 합계 58.086초입니다. 첫 실행은 PIE 시작 후 Python의 pawn 조회 별칭 오류로 검사가 중단되었고, 엔진 헤더에 명시된 `get_controlled_pawn()`으로 수정해 두 번째 실행에서 통과했습니다. 두 실행의 실제 timing과 오류 로그를 보존했습니다.

- 실제 플레이 월드: `/Game/Maps/UEDPIE_0_high.high`. GameModeBase / DefaultPawn / PlayerController 사용.
- pawn은 PlayerStart (650,-1900,407.739423)cm에 정확히 생성됐으며 시작점 차이 **0cm**, player 0에게 빙의된 상태를 확인했습니다.
- 게임 월드에서 pawn을 지면 아래로 sweep한 결과 실제 blocking hit가 발생했습니다. 지면 Z=297.802923cm, 차단 후 pawn 중심 Z=335.255655cm, 간격 37.452732cm입니다.
- 기존 기본 pawn에 +Y 이동 입력을 약 2초 적용하여 **2324.760cm** 이동한 것을 확인했습니다. DefaultPawn의 floating 이동을 검증한 것이며, 새 걷기 Character를 추가하지 않았습니다. 검사 후 원위치로 돌리고 PIE를 종료했습니다.
- PIE 맵 안의 `/Script/ForestDemo.ScreenDebugLogger` 인스턴스 1개를 확인했습니다. 별도로 기존 네이티브 `ForestDemo.ScreenDebugLogger.HelloOnBeginPlay` 테스트가 **Success**로 완료됐습니다. 이 테스트는 실제 Game world에서 해당 클래스의 BeginPlay를 dispatch하고 `GEngine->OnScreenDebugMessageExists`를 assert합니다. 로그의 실제 성공 시각은 2026-10-21 13:00:16.094 UTC입니다.
- `runtime_viewport.png`는 에디터 뷰포트를 캡처했으므로 Hello 글자 관찰 증거로 사용하지 않았습니다. BeginPlay의 메시지 등록 증거는 네이티브 테스트 로그입니다.
- 추가 런타임 경고: 보조광을 포함한 여러 DirectionalLight의 forward-shading 우선순위가 같다는 경고가 표시됩니다. 엔진은 가장 밝은 주광을 fallback으로 선택합니다. 이번 보완에서는 조명이나 맵을 변경하지 않았습니다.

세부 수치: [runtime_validation.json](D:/github/AstraEffort/ForestDemo/Work/high/runtime_validation.json). 실제 로그: [runtime_validation.log](D:/github/AstraEffort/ForestDemo/Work/high/Logs/runtime_validation.log). 최초 실패와 두 실행 시간도 `Logs/runtime_attempt1.*`, `Logs/runtime_attempt1_timing.json`, `Logs/runtime_attempt2_timing.json`에 남았습니다.

에디터 종료 후 기존 전달 **46개 파일 모두**의 SHA-256을 scratch와 게시본에서 다시 대조했고 최초 delivery_manifest와 동일했습니다. 맵 수정·에셋 재게시·기존 네 장 재촬영·shared Source/Config 변경·Git 작업은 없었습니다.

### 감독 검토 주석

최종 성공 실행에도 `editor_set_viewport_realtime(True)` 호출에서
`No realtime override was found with Level Editor Subsystem Realtime Override`
handled ensure가 발생했습니다 (`Logs/runtime_validation.log`). 이는 검증 도구의
비치명적 오류이며 이후 PIE·충돌·이동·HelloOnBeginPlay 테스트와 정상 종료가
확인됐습니다. 오류 없는 실행으로 해석하지 않습니다. 실제 시작부터 보완 완료까지는
두 단계 사이 간격을 포함하여 3012.461초입니다.
