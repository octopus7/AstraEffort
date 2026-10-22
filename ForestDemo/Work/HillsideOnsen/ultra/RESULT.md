# 산솔 온천 — HillsideOnsen / ultra

100×100m 산비탈에 숙소·목욕 건물 네 동과 자연석 노천탕 두 곳을 배치했다. 세 높이의 테라스를 완만한 지그재그 길, 두 계단, 난간, 작은 다리로 연결하고 목재·회반죽·석재·슬레이트와 청록 수면을 구분했다. 별도 private 프로젝트에서 저장 맵 재로드, 실제 PIE 보행, 렌더 검사를 완료한 뒤 자기 소유 패키지 48개를 게시했다. 상태는 감독 검토 대기다. 완료본은 사용자 요청에 따라 커밋하며, 아래 제출 시각과 검증 기록은 그대로 보존한다.

## 결과와 재현

- 맵: `/Game/Maps/HillsideOnsen_ultra` — [HillsideOnsen_ultra.umap](D:/github/AstraEffort/ForestDemo/Content/Maps/HillsideOnsen_ultra.umap).
- 자산: `ForestDemo/Content/HillsideOnsen/ultra/` — 메시 18개, 머티리얼 19개, 텍스처 10개.
- 원본: [SourceArt/SansolSprings.blend](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/SourceArt/SansolSprings.blend), [author_scene.py](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/author_scene.py), [generate_textures.py](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/generate_textures.py), [build_unreal.py](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/build_unreal.py).
- 게시 전후 SHA-256 일치 및 private UE 종료: [publication_manifest.json](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/publication_manifest.json).

UE 5.7.4에서 맵을 직접 열어 확인한다. 기본 시작 맵은 변경하지 않았다. 검증을 재현하려면 자기 scratch `Saved/Workers/HillsideOnsen/ultra/Project/ForestDemo.uproject`에 대해 공용 `Work/Tools/Run-UnrealIsolated.ps1`로 `verify_and_capture.py`를 실행한다. 이 스크립트는 저장 패키지를 바꾸지 않고 임시 Character를 만들어 실제 PIE에서 이동 입력을 가한다. 원본 재생성은 별도 Blender 4.5 background의 `author_scene.py`, 이후 같은 private UE의 `build_unreal.py` 순서다. shared 프로젝트에서 생성/저장 세션을 실행하지 않는다.

## 실제 렌더

아래 네 장은 실제 UE SceneCapture2D의 1920×1080 FinalColorLDR 출력이다. 수동 노출 bias0, 물리 카메라 노출과 모션 블러 비활성, 동적 조명을 사용했다. 각 시점·카메라·게임 시간·파일 해시는 [Screenshots/capture_manifest.json](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Screenshots/capture_manifest.json)에 기록했다. 최종 육안 확인은 [Validation/visual_review.json](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Validation/visual_review.json)에 남겼다.

### overview

![overview](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Screenshots/overview.png)

### top_down

![top_down](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Screenshots/top_down.png)

### hot_spring

![hot_spring](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Screenshots/hot_spring.png)

### village_path

![village_path](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Screenshots/village_path.png)

고정 온천 카메라의 후속 프레임: [약 4초 후](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Screenshots/hot_spring_timed_04s.png), [약 8초 후](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Screenshots/hot_spring_timed_08s.png). 정확한 간격은 manifest의 실제 게임 시간 차이를 사용한다.

최종 PNG 여섯 장의 디코딩·CRC·해상도·비어 있지 않음·manifest 해시 검사가 모두 통과했다. 실제 +4.20초/+8.40초의 수증기 영역 최대 RGB 차이는18/30, 고정 잔디 대조 영역은2/2였다. 물 영역 평균 차이는1.31/2.22, 수증기는0.76/1.04, 대조 영역은0.47/0.47로 측정되었다. 이는 육안 관찰과 그래프 연결 확인을 보조하는 수치이며, 렌더링 노이즈도 포함된다. [Validation/image_quality.json](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Validation/image_quality.json)

## 검증 결과

저장 맵 재로드 검사 599개 통과, 실패와 API 예외 없음. 18개 메시의 실제 UE LOD0 버퍼를 추출해 총 67,010 삼각형, 월드 경계, 유한 좌표/UV, UV 밀도, 머티리얼/텍스처와 충돌 설정을 확인했다. 모든 `/Game` 의존성을 재귀 조회해 자기 자산과 지정 맵만 참조함을 확인했다. non-World-Partition, external actor/component package 없음, 동적 조명, BuiltData 없음, PlayerStart를 검사했다. 원본과 엔진 검증의 세부 결과는 [Validation/source_geometry.json](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Validation/source_geometry.json)와 [Validation/engine_validation.json](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Validation/engine_validation.json)이다.

건물 기초 모서리 16곳에서 떠 있는 기초와 기초 상부를 넘는 지형은 0건이며, 계단 바닥과 디딤판 검사를 통과했다. 엔진에서도 건물별 중앙·모서리 5곳 및 길 중앙선을 2m 이하 간격으로 샘플링했다. 하늘 구체는 저장 후 Actor와 Component 양쪽에서 NoCollision인 것을 별도 확인했다.

최종 별도 재로드에서도 조명9개의 Movable 설정, BuiltData 부재, 검증 패키지 해시 불변을 확인했다. [Validation/final_map_checks.json](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Validation/final_map_checks.json)

| 실제 PIE 구간 | 결과 | 실제 수평 이동(m) | 접지 시간 비율 | 관측 게임 시간(s) |
|---|---|---:|---:|---:|
| arrival_flat | passed | 13.82 | 100.0% | 5.59 |
| lower_switchback | passed | 19.08 | 100.0% | 7.69 |
| upper_switchback | passed | 15.25 | 100.0% | 6.16 |
| stream_bridge | passed | 16.27 | 100.0% | 6.56 |
| lower_stairs | passed | 7.17 | 100.0% | 2.92 |
| upper_stairs | passed | 9.23 | 100.0% | 3.75 |
| bathhouse_wall_blocks | passed | 3.55 | 100.0% | 2.66 |

보행은 `/Script/Engine.Character`, 반경28cm·반높이88cm 캡슐, 속도250cm/s, 최대 계단35cm, 경사45°로 수행했다. 구간마다 미리 둔 별도 캐릭터를 활성화했고 보행 중 위치 강제 이동은 사용하지 않았다. 벽 테스트는 지속 입력 중 실제 정지와 해당 벽을 향한 blocking capsule trace를 함께 확인한다. [Validation/runtime_walks.json](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Validation/runtime_walks.json)에 위치·속도·접지·충돌 샘플을 보존했다. 이는 대표 구간 테스트이며 모든 게임플레이·경로 조합이나 패키징 검증을 뜻하지 않는다.

## UV·표면·수면과 수증기

원본의 각 면을 고유 planar chart로 만들고 사각 경계가 겹치지 않도록 배치했다. UV는 full precision으로 가져왔으며, Steam 외 측정 삼각형의 목표 밀도 ±5% 초과는 원본/UE 검사에서 0건이다. 밀도는 가상 atlas 기준으로 산정하고 실제 머티리얼은 자기 제작 512px 이미지를 반복한다. 섬마다 서로 다른 베이크 이미지가 있는 것은 아니다. Steam은 전체 카드 UV를 반복하는 의도적 겹침 예외다. [uv_source_validation.json](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/uv_source_validation.json)

| 메시 | 목표 px/m | 섬 한쪽 padding(가상 atlas px) |
|---|---:|---:|
| SM_Terrain | 32 | 17.0 |
| SM_Earth | 64 | 9.0 |
| SM_Path | 96 | 9.0 |
| SM_DarkWood | 128 | 9.0 |
| SM_Cedar | 128 | 9.0 |
| SM_Stone | 96 | 9.0 |
| SM_BathStone | 96 | 9.0 |
| SM_Water | 128 | 8 |
| SM_Steam | 예외 | — |
| SM_Stream | 128 | 8 |
| SM_Plaster | 128 | 9.0 |
| SM_Glass | 128 | 8 |
| SM_Roof | 128 | 9.0 |
| SM_Fabric | 128 | 8 |
| SM_Metal | 128 | 8 |
| SM_Trunks | 96 | 8 |
| SM_LeavesLight | 64 | 9.0 |
| SM_Leaves | 64 | 8 |

텍스처는 자체 절차 생성 원본 10개이며 외부 이미지/생성형 이미지 호출은 없다. 목재 결, 돌·회반죽·슬레이트·자갈·잔디 바탕, 잔물결 및 수증기 알파를 사용했다. Cedar/Limestone roughness 이미지도 보존했지만 현재 표면 roughness는 재질별 상수이므로 해당 두 이미지는 실제 roughness 입력에 연결되지 않는다. 생성 방식과 사용 표면은 [texture_manifest.json](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/texture_manifest.json) 및 빌드 소스에 기록했다.

수면은 불투명 머티리얼의 panned detail/노멀과 ±1.5cm 주기적 WPO로 표현했다. 수증기는 교차한 반투명 카드, soft alpha, 18초 pulse/WPO와 60cm DepthFade로 표현했다. 마스크 최대 알파116/255에 최종 계수0.45를 적용해 밝은 배경에서도 은은한 기둥이 보이도록 조정했다. 저장된 그래프의 실제 Time/Sine/Panner/DepthFade 연결은 [Validation/effect_graphs.json](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Validation/effect_graphs.json)로 확인했다. 유체·열역학·굴절 시뮬레이션은 구현하지 않았다.

## 알려진 한계와 수정 기록

- 길 모서리 한 위치에서 지형이 최대7.16mm 침범하며 중복 샘플3개가 이를 검출한다. 원본 중앙선은 침범0건이다. 다리 아래는 의도적으로 지형과 간격이 있고 큰 간격 지점의 목재 지지가 검사되어 있다. 얇은 길 단면과 일부 날카로운 경계가 근접 시점에서 보인다.
- 물길은 교량 아래와 가장자리 지형 연결부에서 가려진다. 주 경로 2.2m 밴드 바깥의 삼각형 중심4개도 지형 아래에 있으며, 최대 약0.90m다. 전 구간에 연속해서 보이는 흐름이나 물리적 유동을 주장하지 않는다.
- 건물은 외관 중심의 닫힌 메시이며 내부 생활 공간, 수영·목욕 상호작용, NPC·오디오·패키징은 포함하지 않았다. 물은 불투명하고 수증기는 각도에 따라 카드 구조가 드러날 수 있다.
- 첫 검증에서 목욕 건물 모서리의 지형34.5cm 침범을 확인해 좁은 기초 영역을 다시 깎았다. 실제 Character 검사에서 하늘 구체가 BlockAll로 다시 로드되는 문제를 확인해 저장된 NoCollision 프로필과 actor 충돌 비활성으로 수정했다. [Validation/sky_collision_repair.json](D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra/Validation/sky_collision_repair.json)
- 초기 검증은 지원되지 않는 Python API 및 transient actor의 PIE 복제 제외로 실패했다. 실패 기록은 Validation/Attempt01–03과 각 실행 로그에 남겼다. build_05와 verify_02는 결과 파일을 남긴 뒤 종료 중 Windows 접근 위반(-1073741819)이 발생했다. 종료 코드0만으로 성공을 판정하지 않으며 최종 체크·렌더·해시 근거를 사용한다.

## 실제 운영 시각

| 항목 | 값 |
|---|---|
| 최초 시작 UTC / KST | 2026-10-22T15:11:37+00:00 / 2026-10-23T00:11:37+09:00 |
| 사용자 중단 UTC / KST | 2026-10-22T15:53:18+00:00 / 2026-10-23T00:53:18+09:00 |
| 중단 체크포인트 | `62eda36`; Work/HillsideOnsen/ultra/Checkpoint/20261023T005318KST |
| 재개 UTC / KST | 2026-10-22T16:03:15+00:00 / 2026-10-23T01:03:15+09:00 |
| 완료 UTC / KST | 2026-10-22T16:26:50.932359+00:00 / 2026-10-23T01:26:50.932359+09:00 |
| 전체 wall seconds | 4513.932 |
| 중단 구간 seconds | 597 |
| 중단 제외 wall seconds | 3916.932 |
| UE mutex 대기 합계 seconds | 19.357 |
| UE 실행 합계 seconds | 880.450 |

| UE 실행 | mutex 대기(s) | 실행(s) | 프로세스 exit code |
|---|---:|---:|---:|
| build_01 | 13.927 | 35.721 | 0 |
| build_02 | 0.409 | 13.226 | 0 |
| build_03 | 1.466 | 50.322 | 0 |
| build_04 | 0.351 | 66.307 | 0 |
| build_05 | 0.322 | 65.680 | -1073741819 |
| build_06 | 0.222 | 61.868 | 0 |
| build_07 | 0.293 | 64.574 | 0 |
| final_saved_checks_01 | 0.315 | 14.670 | 0 |
| sky_repair_01 | 0.358 | 15.304 | 0 |
| verify_01 | 0.227 | 17.208 | 0 |
| verify_02 | 0.592 | 142.086 | -1073741819 |
| verify_03 | 0.457 | 192.107 | 0 |
| verify_04 | 0.418 | 141.374 | 0 |

이 기록은 해당 장면의 재현·운영 기록이다. 이전 비교 보고서와 토큰 측정에서 제외했으며 다른 테마 자료는 수정하지 않았다. 외부 창작 참고 자료는 사용하지 않았다. API 확인에는 설치된 UE 5.7 소스/헤더를 사용했고 정확한 근거 경로는 engine_validation의 api_evidence에 남겼다.
