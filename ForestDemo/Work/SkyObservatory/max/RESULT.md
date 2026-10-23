# 하늘섬 천문대 — SkyObservatory / max

## 설계와 구현 계획

사용자가 승인한 100×100m의 차분하고 둥근 게임 아트 천문대 디오라마를 제작한다. 중앙 섬의 청록색 돔, 황동 대형 망원경, 바위 밑면의 수직 실루엣, 따뜻한 창빛이 주제다. 전경 도착 섬, 동쪽 별자리 정원, 서쪽 학자 주택, 작은 등대 섬을 난간과 지지 아치가 있는 교량으로 연결한다. 부유하는 바위와 구름 사이에 충분한 빈 공간을 둔다.

접근 방식은 Blender의 독립 절차적 원본 메시·표면 이미지를 생성하고, 전용 빈 UE 5.7 프로젝트에 가져와 동적 조명과 실제 렌더를 검증하는 방식이다. 기본 도형만 UE에서 배열하는 방식보다 돔 개구부·망원경 기계 부품·암석 밑면을 정교하게 제어할 수 있다. 외부 창작 자산과 다른 작업의 자산은 사용하지 않는다. 실행 방식은 직접 구현이며 부모 감독자가 최종 검토한다.

- [x] 시작 시각·전용 작업 경로·독립 프로젝트 경계 기록
- [x] `Source/build_scene.py`: 원본 지형·건축·교량·소품·표면 이미지 생성, 단위·UV·법선 검사
- [x] `Source/build_unreal.py`: 소유 자산 가져오기·재질·배치·동적 조명·카메라·비 World Partition 맵 저장
- [x] 저장 맵 재로드 후 `/Game` 전체 의존성과 실제 배치 메시/재질/텍스처 대조
- [x] 지정한 1920×1080 UE 실제 렌더 4장과 카메라·UTC·해시 매니페스트 기록
- [x] 이미지 검토 및 필요한 수정, 감독자 검토 후 private UE 종료 상태에서 소유 결과만 게시·파일별 SHA256 대조
- [x] 실제 작업/큐 대기/UE 실행/원본 제작 시간, 제약, 결과를 이 문서와 `STATUS.json`에 기록

검토 중점: 메시 cm 스케일과 100m XY 경계, 열린 돔과 망원경 렌즈의 앞면 방향, 다리의 양끝 연결, 비어 있지 않은 재귀 의존성 그래프, 모든 시점의 Lit/GameView 실제 렌더. UV는 표면별 평면 삼각형 섬에 64px/m를 적용하고 반복 절차적 재질의 타일 반복은 의도적 예외로 명시한다. 구름과 별빛은 정적 예술적 표현이며 대기 시뮬레이션이나 게임플레이를 주장하지 않는다.

## 작업 기록과 실제 결과

- 독립 검토와 감독 확인을 완료했다. [최종 검토 증명](Evidence/supervisor_acceptance.json), [감독 파일·링크 대조](Evidence/parent_publication_check.json), [기존 비교 자료 최종 보존 확인](Evidence/parent_comparison_preservation_final.json). 상태 값은 `ready_for_review`로 보존하며 Git 변경·커밋·푸시는 하지 않았다.
- 시작 UTC: `2026-10-23T12:04:38.840000+00:00` / KST: `2026-10-23T21:04:38.840000+09:00`. 감독자가 확인한 실제 최초 turn 시각이다.
- 최초 수동 상태 기록: `2026-10-23T12:05:03.8566664+00:00`; 최초 시작으로 소급 대체하지 않고 별도 보존한다.
- 완료 UTC: `2026-10-23T12:36:48.647992+00:00` / KST: `2026-10-23T21:36:48.647992+09:00`.
- 총 벽시계: **1929.808초**, 모든 UE 큐 대기 **143.140초**, 모든 UE 실행 **323.274초**. 큐 분류는 변경하지 않은 공용 runner의 `Unknown`, 우선순위 2/FIFO이며 기존 우선순위 작업을 선점하지 않았다.
- 원본 생성·검사 명령의 실제 관측 벽시계 합계 **41.336초**. 셸/프로세스 시작을 포함하며 설계·스크립트 작성·검토 시간은 총 벽시계에 포함된다. 최종 전체 원본 생성 내부 계측 7.480초; 타깃 수정과 재검사는 별도 명령으로 기록했다. ImageGen 사용 및 시간 **0초**.
- 스레드: `01a168a6-1456-7803-8dc6-c6409596987c`. 실제 turn의 `gpt-6-astra` / `max` 확인. 로컬 `fast` 설정과 도구의 `priority` 지원은 확인되지만 turn 기록에는 요청별 실제 serving tier가 노출되지 않는다. [모델·effort 검증 근거](Evidence/runtime_effort_verified.json).

| UE 시도 | 대기 초 | 실행 초 | 종료 코드 | 실제 결과 |
|---|---:|---:|---:|---|
| 1 | 42.578 | 0.000 | 1 | 프로세스 가드의 sandbox 조회 거부; UE 실행 없음 |
| 2 | 0.182 | 32.480 | 0 | 재질 Multiply 속성 접근 오류; 종료코드 0이어도 제작 성공 아님 |
| 3 | 0.168 | 60.627 | 0 | 맵 저장 후 편집기 카메라 프록시 검사 오탐; 종료코드 0이어도 검증 성공 아님 |
| 4 | 87.361 | 101.300 | 0 | 첫 실제 4장 캡처; 축·조명 보정 필요 |
| 5 | 12.851 | 128.867 | 0 | 축을 FBX에 bake하고 면 방향·조명·구름 보정, 최종 재검증·4장 캡처 성공 |

[전체 계측](Evidence/timing_summary.json), [UE 원본 로그](Evidence/UnrealLogs/phase05.log). 초기 축·조명 상태의 실제 렌더 4장과 매니페스트는 [BeforeCorrection](Evidence/BeforeCorrection/capture_manifest.json)에 보존했다. 최초 원본의 캡 winding 오류는 성분별 인접 면 방향 전파와 양의 체적으로 수정했고, UV를 좁은 선반에 패킹해 float32 밀도 편차를 줄였다.

## 전달 경로와 장면 구성

- 최종 맵: `ForestDemo/Content/Maps/SkyObservatory_max.umap` (`/Game/Maps/SkyObservatory_max`).
- 최종 자산: `ForestDemo/Content/SkyObservatory/max/` 아래 메시 17개, 재질 21개, 텍스처 21개. 맵 포함 **60개 파일**이며 [게시 파일별 SHA256](Evidence/publication_manifest.json)의 private/published 해시가 전부 일치한다.
- 원본: `SourceArt/SkyObservatory_Master.blend`, `SourceArt/Meshes/*.fbx`, `SourceArt/Textures/*.png`; 제작·검사·게시 스크립트는 `Source/`에 보존했다.
- 다섯 부유섬, 중앙 관측 틈이 있는 돔, 황동 망원경의 포크·트러니언·고도 기어·핸드휠·파인더·카운터웨이트·렌즈, 지지 아치와 난간을 가진 네 교량, 별자리 바닥 정원·혼천의·해시계, 학자 주택 두 채, 도착 광장·등대·식생·책/탁자/상자를 제작했다.
- 실제 전체 XY 경계: **93.7985×91.0000m**, X 약 −46.799~47.000m, Y −45.000~46.000m. 높이 **−28.600~25.350m**. 모든 제작 형상과 구름을 100×100m 안에 배치했다.

## 검증 근거

- [저장 맵 재로드와 UE 자산 검사](Evidence/ue_validation.json): `world_partition=None`, `force_no_precomputed_lighting=True`, 실제 조명 9개 전부 Movable. 외부 액터/오브젝트 패키지와 BuiltData 없음.
- `/Game` 재귀 의존성 **60개 패키지**: 자신의 맵 1개와 자신의 자산 59개. 실제 배치 메시·모든 슬롯의 재질·재질이 사용하는 텍스처 59개가 그래프에 모두 포함됨. 범위 밖 의존성·누락 재질·누락 텍스처 0개. `/Engine` 편집기 카메라 프록시는 Game View에 렌더되지 않는 시각화 컴포넌트로 분리했다.
- 전체 **158,816삼각형 / 2,446닫힌 연결 성분**. [저장된 .blend 재검사](Evidence/persisted_source_audit.json)에서 열린/방향 불일치 edge 0, UV NaN/Inf 0, 저장 UV의 사각형 영역 교차 0. [FBX 축 보정 검사](Evidence/export_axis_validation.json)에서 반사 변환 뒤 면 winding을 반전하고 성분별 체적 양수를 확인했다. 열린 면 예외 없음; 돔 개구부 가장자리는 두께 캡을 갖고 렌즈 원판은 닫힌 앞면이다.
- 축은 export 메시 안에 Y 반사와 winding 보정으로 굽고 UE importer의 Y 반사를 상쇄했다. UE의 모든 메시 액터 스케일은 **(+1,+1,+1)**. 각 메시의 실제 cm bounds와 설계 원본 bounds 최대 차이 **0.000472cm**로 단위와 축을 확인했다.
- UV 목표 **64px/m**, 저장된 실제 UV 실측 **63.980373~64.025250px/m**. 1024² 텍스처 기준 각 삼각형을 독립 평면 섬으로 만들고 각 면에 4px padding을 확보했다. 모든 UE 메시 UV는 full precision. 의도된 예외는 0..1 바깥의 절차적 타일 반복이며, 고유 atlas 베이킹이나 lightmap UV를 주장하지 않는다.
- 표면 이미지는 이 작업에서 새로 만든 결정적 절차적 PNG 21장이다. 외부 이미지/다른 테마·effort 자산을 복사하거나 재사용하지 않았다. 실제 UE 렌더만 장면 증거로 사용했다.
- 감독자가 네 최종 시점을 모두 확인하고 게시를 지시했다. 게시 전에 자신의 private Unreal 프로세스 종료를 조회했고 60개 파일을 복사한 뒤 모든 파일 해시를 다시 확인했다.
- 기존 비교 기록의 보존은 감독자가 독립 검사한 [보존 증명](Evidence/parent_comparison_preservation.json)을 참조한다. 작업자는 기존 보고서 내용을 읽거나 쓰지 않았다.

## 실제 UE 렌더

모두 **1920×1080 PNG**, `High`(모든 sg 그룹 2), `r.ScreenPercentage=100`, 실제 활성 `VMI_LIT`, Game View, 그리드·선택 표시 없음. [카메라 좌표·실제 회전·렌더 UTC·SHA256 매니페스트](Screenshots/capture_manifest.json).

- Overview: 위치 `(12000,-12000,16000)`cm → 원점, orthographic width `20000`cm.
- Top down: 위치 `(0,0,20000)`cm, pitch `−90` / yaw `0` / roll `0`, orthographic width `20000`cm.
- Observatory와 Bridge: 매니페스트에 기록한 perspective 48° 상세 카메라. 정적 환경으로 시간별 움직임을 주장하지 않아 timed pair는 만들지 않았다.

![전체 부유섬 천문대](Screenshots/overview.png)

![평면 구성과 교량 연결](Screenshots/top_down.png)

![천문대와 황동 망원경 상세](Screenshots/observatory.png)

![교량 접속과 바위 밑면 상세](Screenshots/bridge.png)

## 한계와 외부 참조

삼각형별 UV 섬의 타일 위상이 달라 가까운 거리에서 재질 이음과 삼각형 패턴이 보인다. 구름은 밝게 채운 겹친 타원체의 정적 예술적 표현이며 볼륨 기상 시뮬레이션이 아니다. 별자리·별 장식과 해질녘 조명은 예술적 배치다. 건축 내부의 실제 관측 설비 작동이나 내부 생활 공간, 망원경 추적·물리·게임플레이를 구현했다고 주장하지 않는다. 교량은 환경 모델이며 플레이어 충돌/경로 탐색을 제작 범위에 넣지 않았다. 렌더는 에디터 Game View에서 확인했고 패키지 빌드·PIE 게임플레이·FPS 보장은 수행하지 않았다.

외부 창작 이미지·메시·폰트 참조는 없다. API 동작은 설치된 Blender 5.0 및 Unreal Engine 5.7 헤더/실제 실행으로 확인했다. 모델/서비스 계층에 관한 외부 공식 링크는 감독자 제공 runtime 증거에 포함되어 있으며 이 보고서는 요청별 serving tier를 추정하지 않는다. 공유 Source/Config/Plugins/Binaries/uproject, 다른 맵과 작업 디렉터리는 변경하지 않았다. 새 단계나 범위 확장 없이 이 유한 제작과 보정 작업을 종료한다.
