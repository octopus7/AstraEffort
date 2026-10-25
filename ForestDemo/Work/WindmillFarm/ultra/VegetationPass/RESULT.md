# WindmillFarm / ultra — 키 큰 들풀과 옥수수밭

요청한 별도 옥수수 재배구역과 키 큰 들풀을 추가하고, 둘 다 뿌리를 고정한 채 바람에 흔들리도록 적용했다. private UE 저장·재로드·실행 검증 후 소유한 자산과 맵만 전달 경로에 반영했다. 상태는 **ready_for_review**이며 Git 커밋은 수행하지 않았다.

## 장면 변경

- 헛간 뒤 15×12m의 독립 옥수수밭: 14줄, 210포기(3개 원형 각70), 가운데 관리 통로, 헛간 뒤 연결길과 울타리17구간.
- 키 큰 들풀 1,457개 인스턴스: 긴 풀591, 밝은 이삭769, 갈대 형태97. 16개 후보 영역 안에서 불규칙하게 분포시키고 가장자리는 성기게 배치했다.
- 기존 밭4개, 건물, 풍차, 나무20그루와 주요 길을 유지했다. 밭과 겹치던 나무1그루를 이동하고 새 밭/입구 안의 기존 짧은 풀만 제거했다.
- 옥수수와 들풀은 UE foliage 인스턴싱을 사용한다. 정점색 R의 높이 가중치로 뿌리 변위를0으로 고정하고, 공통 월드 위치/시간 위상으로 줄기 휘어짐과 잎·이삭의 잔떨림을 만들었다.

## 실제 UE 렌더와 바람 증거

![농장 전체 — 헛간 뒤 별도 옥수수밭과 들풀](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/Screenshots/overview.png)

![옥수수 재배구역](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/Screenshots/corn.png)

![키 큰 들풀](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/Screenshots/meadow.png)

[옥수수 바람 영상](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/Motion/corn_wind.mp4) · [들풀 바람 영상](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/Motion/meadow_wind.mp4)

13장 정지 렌더는 실제 UE5.7 SceneCapture2D, 1920×1080, D3D12 SM5, High/sg2, 동적 조명, FinalColorLDR/RGBA8/gamma2.2다. [카메라·개별 촬영 시각](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/Screenshots/capture_manifest.json)와 [렌더 해시·분석](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/render_analysis.json)에 원본 설정을 기록했다. 전체 조망은 근접 시점으로 머티리얼 표시를 안정시킨 뒤 같은 원래 카메라로 다시 촬영했다.

옥수수/들풀 고정 카메라 쌍의 실제 월드 시간 간격은 각각1.905240/1.912218초다. RGB 차이12 초과 픽셀은871,938/658,481개이며 그림자·시간적 렌더 차이도 포함한다. 식물의 위치 변화는 이미지 직접 검토와 연결된 WPO/정점색 검증을 함께 근거로 삼았다.

각 영상은 실제 UE 1280×720 PNG32장으로 만들었다. 원본 촬영 구간은 옥수수6.626404초, 들풀6.609987초이며 평균 촬영 간격으로 약4.68fps MP4를 인코딩했다. 프레임 보간·생성 이미지는 없고, 작은 프레임 간 시간 차이는 평균으로 정규화했다. 연속 재생 성능 측정이나30/60fps 게임 녹화는 아니다. [영상 출처·해시](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/Motion/video_manifest.json)와 프레임별 월드 시간/UTC 원본 manifest를 함께 보관했다. FFmpeg 디코드 검사도 통과했다.

## 저장·실행·게시 검증

[최종 검증 JSON](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/validation.json)의 **23개 검사 모두 통과**했다. 저장 후 맵 재로드,100×100m 범위, 비월드파티션, 외부 actor/object 패키지 없음, 자기 자산 재귀 의존성, 동적 조명, UV/머티리얼, 인스턴스 수, 바람 입력 그래프, 정점색, 바람 bounds와 경로 간격을 확인했다. PIE에서 DefaultPawn 소유, 지면/풍차 벽 trace, 지면에 막히는 sweep, 수평200cm 이동과 PIE 종료를 확인했다. 이는 스크립트 실행 검증이며 사람이 직접 보행한 테스트는 아니다.

최종 polish 검증 UTC는 2026-10-22T14:17:31.368406+00:00이며 polish/overview UE 프로세스는 모두 정상 종료했다. 최종 로그에는 초기 바람 머티리얼 compile/fallback 오류가 없다. [독립 구현·시각 검토](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/QA/implementation_review.md)에 초기 문제와 수정 후 승인 근거를 보존했다.

전달 맵: [WindmillFarm_ultra.umap](D:/github/AstraEffort/ForestDemo/Content/Maps/WindmillFarm_ultra.umap) (`/Game/Maps/WindmillFarm_ultra`). 자산 루트는 `/Game/WindmillFarm/ultra/`다. 게시 패키지는 **99개**, 새 패키지26개, baseline 대비 변경28개다. 모든 게시 파일의 SHA-256이 private 원본과 일치한다. [파일별 게시 검증](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/publication.json)와 [private UE 종료 확인](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/shutdown_check.json)을 제공한다. 다른 작업의 자산, 공유 소스/설정, Git/index는 변경하지 않았다.

## 원본과 UV

이번에 옥수수3종/들풀3종을 독립 제작하고 FBX를 재임포트해 검사했다. 원본 Blender, 제작 코드, mesh/UV/정점색 manifest는 [Corn](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/Art/Corn/manifest.json)과 [Meadow](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/Art/Meadow/manifest.json)에 있다. 옥수수는 각2,168tri, 들풀은1,396/1,400/2,284tri다. UV0은 삼각형별 고유 셀, UV1은 무스케일128px/m 목표다. 새 메시의 붕괴 UV/중복 UV0 셀은 없으며 정점색 뿌리 R=0과 높이 오차3e-8 미만을 재임포트에서 확인했다. UV0 여백은1024기준 옥수수2px, 들풀2.13–2.69px다.

배치 스케일에 따라 유효 평균 밀도는 옥수수 약121.9–137.5px/m, 들풀 약112.3–218.6px/m로 달라진다. 새 독립 절차 BaseColor7장과 기존 자기 지면 atlas에 새 밭/입구만 추가한 texture1장을 실제 머티리얼에 연결했다. [텍스처 원본·해시](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/Art/Textures/manifest.json)를 제공한다. 외부 창작 자산이나 이미지 생성 서비스는 사용하지 않았다.

바람은 물리 시뮬레이션이 아닌 시각적 머티리얼 변형이다. 식물 충돌·수확 상호작용은 없고, 경로 검사는 배치 중심 기준이므로 일부 움직이는 잎이 길 가장자리까지 뻗을 수 있다. 주요 길은 렌더로도 확인했다. 기본 free-fly pawn을 유지했으며 이번에 LOD/플랫폼별 성능 최적화를 수행하지 않았다. 기존 MillTower의 미세 UV 예외 등 최초 장면의 한계는 [보존한 최초 결과](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/Before/RESULT.md) 및 기존 QA에 그대로 남아 있으며, 전체 자산에 대한 엄격한 zero-overlap 주장은 하지 않는다.

## 실제 시간과 보존

| 항목 | 기록 |
|---|---|
| 이번 시작 UTC / KST | 2026-10-22T13:57:19+00:00 / 2026-10-22T22:57:19+09:00 |
| 이번 완료 UTC / KST | 2026-10-22T14:32:39.554991+00:00 / 2026-10-22T23:32:39.554991+09:00 |
| 측정 wall seconds | 2120.555 |
| UE 대기 합계 | 2.380s |
| UE 실행 합계, 실패 포함 | 309.767s |
| 이미지 생성 서비스 | 0s, 미사용 |

시작은 이번 후속 작업의 첫 명시적 시계 측정값이며 초기 확인 작업이 그보다 앞섰다. 따라서 위 wall은 전체 요청의 정확한 최초 시점부터 측정한 값으로 주장하지 않는다. 원래 최초 제작의 시작/완료/3323.076879초 기록은 Before에 보존했고 이번 측정과 분리했다. 소스 제작 병렬 시간은 wall에 포함하며 별도 합산하지 않는다. [시도별 실제 시각과 대기/실행](D:/github/AstraEffort/ForestDemo/Work/WindmillFarm/ultra/VegetationPass/timings.json):

| 시도 | 대기초 | 실행초 | 종료코드 |
|---|---:|---:|---:|
| build | 0.546 | 29.649 | 0 |
| capture | 0.430 | 69.409 | -1073741819 |
| verify | 0.334 | 29.056 | 0 |
| materialfix | 0.259 | 22.806 | 0 |
| capture2 | 0.299 | 55.426 | 0 |
| polish | 0.284 | 70.577 | 0 |
| overview | 0.228 | 32.845 | 0 |

초기 VertexColor 출력 이름 때문에 바람 shader 입력이 누락된 문제를 기본 출력 연결·반환값 assertion으로 수정했다. 옥수수 카메라의 수관 가림을 이동으로 해결하고, 작은 들풀 스케일의 바람 bounds를40cm로 확대했다. 최초 capture의 비정상 종료(-1073741819)는 기록을 보존했으며 이후 최종 capture/polish/overview에서 재현되지 않았다. 그 종료 원인은 확정하지 않았다. 최종 성공 근거는 이전 실패 로그가 아닌 위 최종 검증/렌더/게시 해시다.

변경 전 보고서/스크린샷/검증/시각 기록은 `VegetationPass/Before/`, 변경 전 Content/map은 자기 scratch의 `VegetationBefore/Content/`에 보존했다. 재촬영은 자기 private 프로젝트에서 공용 runner를 통해 `Run-Vegetation.ps1 -Phase polish`, 종료 후 `-Phase overview` 순서로 수행한다. shared 프로젝트에서 생성·저장 세션을 실행하지 않는다.
