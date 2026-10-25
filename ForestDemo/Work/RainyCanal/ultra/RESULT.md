# 비 오는 운하 마을 — RainyCanal / ultra

상태: **ready_for_review**. 독립 제작한 100×100m 운하 마을을 소유 경로에 게시했다. 새 UE 프로세스에서 저장 맵을 재로드해 **23/23 검증을 통과**했고, 실제 UE 렌더 13장과 짧은 영상 2개를 제공한다. private UE 종료 확인 후 71개 패키지를 복사했으며 모든 원본/게시본 SHA-256이 일치한다. 감독자의 최종 통합 검토 대상이며 이 작업은 Git 커밋을 만들지 않았다.

## 장면과 전달 파일

운하 양쪽에 크림·세이지·로즈색 건물 8채, 아치형 돌다리와 평평한 나무다리, 부두와 작은 배, 가로등 10개, 벤치·화분·난간을 배치했다. 12m 폭 운하와 두 교차 동선, 건물 현관으로 이어지는 돌길을 두었고 나무 16그루, 관목 37개, 길 가장자리 풀 69개로 경계를 정리했다. 건물은 외관용이며 내부는 없다. 얼굴·하트·장식 구름은 없다.

- 맵: `/Game/Maps/RainyCanal_ultra` — `D:/github/AstraEffort/ForestDemo/Content/Maps/RainyCanal_ultra.umap`.
- 자산: `/Game/RainyCanal/ultra/` — Static Mesh 24개, Texture 30개, Material 16개.
- [게시 파일 목록과 해시](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/publication_manifest.json), [최종 검증](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/validation.json), [독립 검토](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/QA/implementation_review.md), [검토한 파일 해시](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/QA/final_review.json).
- 별도 private 프로젝트: `D:/github/AstraEffort/ForestDemo/Saved/Workers/RainyCanal/ultra/Project/RainyCanal.uproject`.

이전 테마의 창작 자산·제작 스크립트·텍스처를 읽거나 재사용하지 않았다. 새 Blender 원본과 절차적 텍스처를 독립 제작했다. `/Engine/BasicShapes/Sphere`는 하늘에 사용한 엔진 내장 자원이다. 공유 Source/Config/Plugins/시작 맵은 변경하지 않았다. 외부 창작 이미지·에셋 출처는 없으며 이미지 생성 호출도 0회다.

## 실제 UE 최종 렌더

아래는 모두 `delivery` 실행에서 얻은 원본 UE5.7 SceneCapture2D 결과다. 1920×1080, D3D12 SM5, High(sg2), 화면 비율 100%, FinalColorLDR/RGBA8/gamma2.2. 카메라별 위치·회전·FOV/직교 폭·UTC·월드 시간·워밍업 프레임은 [capture_manifest.json](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Screenshots/capture_manifest.json)에 기록했다. 생성 이미지나 보정 합성이 아니다.

![전체 조망](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Screenshots/overview.png)

![위에서 본 동선](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Screenshots/top_down.png)

![운하와 돌다리](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Screenshots/canal.png)

![비 오는 돌길](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Screenshots/rainy_street.png)

![부두와 경사 진입부](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Screenshots/dock.png)

전체 풋프린트와 다리 양끝, 부두 경사로, 현관 접근로를 확인했다. 도로·외벽·목재·금속의 차이가 읽히며, 반사는 물과 젖은 돌길에 집중된다. 흐린 조명과 안개는 게임 아트용으로 조정한 결과이며 물리적으로 정확한 흐린 하늘 모델은 아니다.

## 비·수면·웅덩이

비는 교차 면 3,868개로 구성된 1,934개 빗줄기의 버텍스 색상 위상을 이용하여 WPO로 낙하시킨다. 양의 Z 바운드를 14.5m 확장했고, 건물 평면 범위에 여유 폭을 더해 빗줄기 생성에서 제외했다. 재질은 반투명이며 충돌 이벤트나 튀는 물방울 시뮬레이션은 없다. 다리·수목·개별 처마를 정밀하게 충돌 판정하지 않으며 일부 관통 가능성이 남는다.

운하와 웅덩이는 시간에 따라 확장하는 원형 파문과 완만한 물결을 노멀로 표현한다. 비를 잠시 숨긴 같은 카메라 시차 캡처로 물의 변화를 별도로 확인했다. 이 숨김은 증거 캡처에서만 적용했고 저장 맵은 비가 켜진 상태다. 물은 불투명한 반사 재질이며 굴절·유체·부력 시뮬레이션은 없다. 반사는 SSR/스카이라이트에 의존하므로 화면 밖 물체를 정확히 반사하지 않는다.

| 고정 카메라 쌍 | 월드 시간 간격(초) | 차이 >12인 픽셀 | 비 |
|---|---:|---:|---|
| canal | 2.440 | 40,462 | 표시 |
| rainy_street | 2.416 | 34,477 | 표시 |
| water_only | 2.443 | 23,400 | 숨김 |
| puddle | 2.399 | 56,799 | 숨김 |

픽셀 수는 움직임의 보조 지표이며 셰이딩·시간 누적 렌더링 변화도 포함한다. 원형 파문의 위치·크기 변화와 빗줄기 위치 변화는 실제 이미지도 열어 확인했다. [수면 t0](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Screenshots/water_only_t0.png) / [수면 t1](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Screenshots/water_only_t1.png), [웅덩이 t0](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Screenshots/puddle_t0.png) / [웅덩이 t1](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Screenshots/puddle_t1.png). 전체 분석은 [render_analysis.json](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/render_analysis.json)에 있다.

- [canal 실제 UE 영상](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Motion/canal_rain.mp4): 1280×720, 원본 40프레임, 3.478 fps, 11.501초. 인코딩 후 전체 디코딩 확인.
- [rainy_street 실제 UE 영상](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Motion/rainy_street_rain.mp4): 1280×720, 원본 40프레임, 3.523 fps, 11.355초. 인코딩 후 전체 디코딩 확인.

영상은 각 카메라에서 순서대로 캡처한 실제 UE 픽셀만 사용했다. 원본 시각 간격의 평균으로 재생하며 프레임 간 약간의 편차는 균등화했다. 보간 프레임은 없다. 이 낮은 캡처 빈도는 **게임 성능/FPS 측정값이 아니다**. [원본 프레임 시각](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Motion/capture_manifest.json), [영상 해시와 디코딩 결과](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Motion/video_manifest.json).

## UV·표면 검증

모든 24개 메시를 원본 FBX로 재수입해 검사했다. 건물 3종, 프랍 8종, 지형·날씨·식생 13종은 2개 UV 채널을 유지하며 검사에서 기하/UV 퇴화와 UV0 양의 면적 중첩이 없었다. 건물은 최대 29,596삼각형, 프랍은 각 15,000삼각형 미만이다.

UV0는 고유 아일랜드 좌표다. 1024 기준 건물 최소 아일랜드 간격 약 4.50px, 프랍 3.12px, 지형 일반 메시 셀 경계 여백 2.10px(인접 셀 간 약4.20px), 비 메시 여백 약1.396px다. UV0의 물리 밀도는 삼각형 크기에 따라 다르며 베이크 광원에는 사용하지 않았다.

UV1은 원본 scale1 기준 1024텍스처/8m, 목표128px/m인 반복 좌표다. 건물 측정127.979–128.019, 프랍 약127.01–128.004, 최종 지형 약127.9996–128.0027px/m. UV1의 반복·중첩·0–1 범위 밖 좌표는 의도한 설정이다. 최종 벽 노치와 부두 경사로도 독립 재수입 검사를 통과했다. 최종 노치 벽은44삼각형이고 Y26–30m 구간 상단−0.12m, 나머지+0.1m, 바닥−2m가 측정되었다.

Stone/Timber는 넓은 면에서 삼각형별 무늬 단절을 줄이기 위해 최종 재질에 연속 월드 투영을 사용했다. Ground도 월드 XY 투영이다. 수평·수직 면은 명목128px/m이며 사선·베벨 면에서는 투영 밀도와 방향이 달라진다. 다른 표면은 UV1을 사용한다. 버텍스별 표면 방향과 접선 공간 노멀 조합은 스타일화한 근사다. 30개 원본 PNG는1024×1024, 맞은편 경계가 정확히 일치한다. 경계 복제 픽셀 때문에 실제 샘플 간격은127.875px/m다. Roughness는 선형 Grayscale, Normal은 DirectX이며 실제 UE의 선형 Grayscale 샘플러11개를 검사했다.

식생 크기 변화에 따른 UV1 밀도 예외는 저장 맵에서 실제 스케일을 읽어 계산했다. 별도의 다시 언랩한 값은 아니다.

| 배치 종류 | 수 | 스케일 범위 | 명목 UV1 px/m 범위 |
|---|---:|---:|---:|
| Tree_ | 16 | 0.9674–1.3145 | 97.37–132.32 |
| Shrub_ | 37 | 0.8037–1.2956 | 98.80–159.27 |
| GrassFringe_ | 69 | 0.6553–1.1805 | 108.43–195.32 |

세부 출처: [건축 QA](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Art/Architecture/REVIEW.md), [프랍 QA](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Art/Props/REVIEW.md), [최종 지형 QA](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/QA/Landscape/REVIEW.md), [텍스처 QA](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Art/Textures/REVIEW.md). 원본 지형 manifest의 DockStep/QuayWall 항목은 각각 `dock_ramp.json`/`wall_notch.json`과 최신 `QA/Landscape/landscape_qa.json`으로 대체된다.

## 저장·실행 검증과 제한

새 프로세스 `ue_delivery.py`는 저장 자산을 수정하지 않고 맵을 다시 열었다. [전체 실행 로그](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Execution/delivery.log)에 Python 오류, 재질 컴파일 실패 또는 기본 재질 대체 진단이 없으며, [명시적 완료 기록](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Execution/delivery_completion.json)은 success/validated=true다. 프로세스 종료 코드만으로 성공을 판정하지 않았다.

23개 체크에는 저장 재로드, 100×100m 양안 지형, 건물 8채 바닥 접지, 두 다리의 표면과 진입부, 메시 24개의 UV와 재질, 날씨 그래프 연결과 비 색상·바운드, 이동식 조명, PlayerStart, PIE 소유·이동·충돌·종료가 포함된다. 돌다리 양끝 안쪽의 높이는 약 2.68cm, 중앙은 110cm이고 나무다리 5개 표본은 0cm다. 나무다리 입구를 가로막던 10cm 벽은 노치로 제거했다.

대표 이동은 **DefaultPawn의 스윕 이동**으로 부두 및 두 다리 경로를 따라 확인했다. 보행 Character의 경사/계단 처리, NavMesh/AI, 모든 지점의 길찾기 또는 패키징된 게임은 검증하지 않았다. 나무다리12mm 판자 틈을 피한 표면 표본과 몸체 스윕을 사용했다. 건물은 닫힌 외관용이며 입장 기능은 없다.

recursive hard/soft `/Game` 의존성은 자기 자산과 자기 맵만 참조했다. non-World-Partition이며 external actor/object 패키지와 BuiltData가 없다. private UE 종료 후 [프로세스 조회 기록](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Execution/shutdown_check.json)을 확인하고 게시했다. 공유 프로젝트에서의 재렌더는 하지 않았으므로 그 프로젝트의 렌더 설정에 따라 시각 차이가 날 수 있다.

의미 있는 증거 수용 테스트 `test_evidence.py`의2개 테스트는 성공했다. 초기 증거가 없을 때 실패시킨 뒤 최종 저장/실행 결과와 비·운하·웅덩이 시차 증거를 검사했다. 독립 검토에서 재질 샘플러 오류, 어두운 조명/차가운 램프색, 부두 캡 충돌, 현관 진입로, 전체 조망 잘림, 나무다리 벽 걸림을 찾아 수정했다. 중간 실패 로그는 Execution에 남아 있으며 최종 성공과 혼동하지 않는다.

## 운영 시각

- 시작 UTC: **2026-10-22T14:53:36+00:00**, KST: **2026-10-22T23:53:36+09:00**.
- 완료 UTC: **2026-10-22T15:55:51.932422+00:00**, KST: **2026-10-23T00:55:51.932422+09:00**.
- 경과: **3735.932초**. 시작은 배정 문서를 확인한 뒤 처음 명시적으로 읽은 시계값이며 그 이전 최초 문서 읽기는 포함되지 않는다.
- UE 대기 합계 **67.746초**, 실행 합계 **544.919초**,12개 프로세스. 모든 실행은 공용 runner의 Unknown/priority2로 직렬화했고 다른 프로세스를 중단하지 않았다.
- 이미지 생성시간0초. 텍스처는 절차적 원본으로 제작했다. 아래는 이 작업의 재현·운영 기록이며 비교 실험 시간/토큰 집계가 아니다.

| 실행 | 대기(초) | UE 실행(초) | 종료 코드 |
|---|---:|---:|---:|
| probe | 0.306 | 25.194 | 0 |
| build | 0.453 | 25.088 | 0 |
| build2 | 0.294 | 44.373 | 0 |
| build3 | 0.377 | 33.488 | 0 |
| build4 | 0.349 | 33.955 | 0 |
| build5 | 0.256 | 64.416 | 0 |
| polish | 0.313 | 63.651 | 0 |
| verify | 0.348 | 19.583 | 0 |
| verify2 | 0.294 | 19.755 | 0 |
| final | 0.295 | 95.471 | 0 |
| wallfix | 64.135 | 27.852 | 0 |
| delivery | 0.326 | 92.093 | 0 |

[원시 시각과 실행별 기록](D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/operational_timing.json). 초기 Python/API/재질 오류가 있는 실행도 정상 프로세스 종료0을 반환하므로 위 표는 검증 성공표가 아니다.

## 다시 열기와 원본 재현

검토자는 UE5.7 Content Browser에서 `/Game/Maps/RainyCanal_ultra`를 연다. 재현 렌더는 제공된 private 프로젝트와 `Run-Canal.ps1 -Phase delivery`를 사용하며 공용 runner를 우회하지 않는다. 이 명령은 현재 증거를 다시 기록하므로 제출 증거를 보존한 뒤 실행한다. private설정은 D3D12/SM5, SSR, TAA, 자동노출/모션블러/정적광원 비활성이다.

원본 재구성 순서: Architecture/build_architecture.py → Props/build_props.py → Textures/build_textures.py → Landscape/build_landscape.py → Landscape/build_dock_ramp.py → Landscape/build_wall_notch.py. Blender 스크립트는 별도 background/factory-startup으로 실행한다. 두 마지막 보정 스크립트가 최종 형상을 만든다. 그 뒤 최신 assemble.py/materials.py를 사용하는 `Run-Canal.ps1 -Phase build5`로 재구성하고, 별도의 `-Phase delivery`로 다시 검증한다. bootstrap.py는 최초 생성 전용이며 기존 프로젝트 덮어쓰기를 거부한다. 과거 진단용 polish/final 스크립트를 현재 맵에 다시 적용할 필요는 없다.

게시 스크립트는 승인된 소유 루트/맵만 허용하고, 기존 게시 경로가 있으면 덮어쓰기를 거부한다. 다음 수정은 새 버전 증거와 감독자 검토를 거쳐야 한다.
