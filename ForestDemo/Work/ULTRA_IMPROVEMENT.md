# Ultra 자가 개선 결과 보고서

Forest ultra의 나무 교체와 색상 조정을 검증·커밋했습니다. MountainStation ultra는 사용자가 중단과 현재 상태 커밋을 요청하여 **미검증 체크포인트**로 보존했습니다. 기차역 개선을 완료로 처리하거나 새 지시 없이 재개하지 않습니다.

이 보고서는 추론 강도 비교 실험과 분리된 후속 작업만 다룹니다. 기존 SUPERVISION.md·token_usage.json 및 연결 증거 2,300개는 2026-10-21 16:26:37.829146 UTC / 2026-10-22 01:26:37.829146 KST에 동결했으며 이후 수정하지 않았습니다. 비교 보고서 커밋은 `54304c0`, 동결 기록 커밋은 `9041599`입니다. 모든 최초/두 번째 납품 기록은 보존했습니다. 이번 이식 지시는 전역 AGENTS.md에 남기지 않고 이 대화의 개별 승인으로만 관리했습니다.

| 테마 | 결과 | 실제 제작 시작 UTC / KST(+09:00) | 제작 종료 UTC / KST(+09:00) | wall 초 | 결과 커밋 |
|---|---|---|---|---:|---|
| Forest ultra | 최종 게시·감독 검증 통과 | 10-21 15:30:53 / 10-22 00:30:53 | 10-21 16:24:27.478715 / 10-22 01:24:27.478715 | 3,214.478715 | `31f7b64b12da02a443d747d5d693fbd4674cef09` |
| MountainStation ultra | 사용자 요청 중단, 후보 미게시 | 10-21 15:38:54 / 10-22 00:38:54 | 10-21 16:05:23.649339 / 10-22 01:05:23.649339 | 1,589.649339 | `f7f46b7` |

Forest의 재개 턴은 15:30:23 UTC에 시작했으며 표는 작업자가 기록한 제작 시작을 사용합니다. Forest 결과 커밋은 16:31:28 UTC / 01:31:28 KST, 기차역 체크포인트 커밋은 16:05:50 UTC / 01:05:50 KST입니다. 별도 감독 검토·빌드 시간과 제작 wall을 중복 합산하지 않습니다.

## Forest ultra — 선택한 변경과 결과

사용자가 지정한 읽기 전용 `D:/github/extraction_shooter/TunaSweeper`의 `BP_AnimeFoliageTree`와 필요한 의존성을 이식했습니다. 원래 둥근 덩어리 형태의 활엽수 63개를 잎 윤곽·가지·줄기와 바람/수관 음영을 가진 나무로 교체했습니다. 활엽수 위치와 yaw는 유지했고 원래 크기 범위에 맞춰 균등 스케일을 적용했습니다. 나머지 871개 액터의 위치·메시·재질과 기존 978개 자산은 유지했습니다.

원본 BP는 네이티브 부모와 CanopyRim 렌더러가 필요했습니다. 감독자가 `ForestUltraTrees` 플러그인 10개 소스/셰이더/descriptor를 통합하고 공유 프로젝트를 실제 빌드했습니다. 여섯 핵심 소스는 선언한 클래스·모듈·CVar·셰이더 경로 변경만 적용했고 셰이더는 원본과 동일합니다. 바람, transform 기반 그라디언트, 나무마다 10개 leaf clump와 10개 숨은 그림자 프록시를 보존했습니다. 원본은 수정·빌드하지 않았습니다.

최종 새 자산 10개는 `/Game/Forest/ultra/AnimeTree` 안에만 있습니다. BP 1개, 메시 4개, 재질 2개, 텍스처 3개이며 변경 맵을 포함한 납품 파일 11개의 해시를 확인했습니다. 임시 CoreRedirect는 공유 프로젝트에 설치하지 않았고 원래 `/Script/TunaSweeper`, `/Game/Environment` 참조는 제거했습니다. 원본 메시의 UV·바람용 vertex color를 유지했으며 이번 단계에서 새 UV 또는 이미지 생성 텍스처를 만들었다고 주장하지 않습니다.

초기 이식 렌더는 밝은 라임색과 강한 수관 명암이 기존 장면에서 두드러졌습니다. 감독자가 실제 overview/tree_detail을 보고 색상만 보완하도록 지시했습니다. 작업자는 두 노출 파라미터 후보를 실제 렌더해 moss를 선택했고 최종 63개 인스턴스와 630개 leaf MID를 새 프로세스에서 확인했습니다. 원본 네이티브 기본값·셰이더·메시·텍스처는 이 색상 보정에서 바꾸지 않았습니다. 기존 Before와 초기 After 증거도 보존했습니다.

### 실제 전후 이미지와 관찰

아래는 같은 카메라의 실제 UE 5.7 PNG입니다. 1920×1080, High scalability, screen percentage 100, D3D12 SM5, SceneCapture2D Final Color LDR이며 보정·이미지 생성으로 장면 증거를 대체하지 않았습니다. 동일 카메라지만 시간에 따라 변하는 기존 물 효과의 프레임 시각은 같지 않습니다. 다른 테마의 근접 구도와 위치를 직접 대응시키지 않습니다.

#### overview

| 교체 전 | 최종 moss |
|---|---|
| ![Before overview](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/Screenshots/Before/overview.png) | ![Final overview](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/Screenshots/Final/overview.png) |

#### top_down

| 교체 전 | 최종 moss |
|---|---|
| ![Before top_down](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/Screenshots/Before/top_down.png) | ![Final top_down](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/Screenshots/Final/top_down.png) |

#### lake

| 교체 전 | 최종 moss |
|---|---|
| ![Before lake](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/Screenshots/Before/lake.png) | ![Final lake](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/Screenshots/Final/lake.png) |

#### beach

| 교체 전 | 최종 moss |
|---|---|
| ![Before beach](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/Screenshots/Before/beach.png) | ![Final beach](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/Screenshots/Final/beach.png) |

#### tree_detail

| 교체 전 | 최종 moss |
|---|---|
| ![Before tree_detail](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/Screenshots/Before/tree_detail.png) | ![Final tree_detail](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/Screenshots/Final/tree_detail.png) |

감독자가 최종 5장 원본과 대응되는 전 이미지를 직접 확인했습니다. overview/top_down에서는 호수·해변·산책길의 배치가 유지되고 활엽수의 수관 외곽이 불규칙한 잎 윤곽으로 바뀌었습니다. tree_detail에서는 굽은 줄기와 가지 분기, 작은 잎 실루엣, 잘게 나뉜 그림자가 이전의 큰 덩어리 표현보다 명확합니다. 초기 이식본보다 노란 상단과 림 대비를 낮췄지만, 잎의 디테일·녹색 대비는 기존 단순한 침엽수보다 강합니다.

lake의 좌측 전경 줄기는 원래 카메라에도 있었으며 교체 뒤 휘어진 줄기가 좌상단을 더 많이 가립니다. 동일 시점 비교를 위해 카메라·나무 위치는 옮기지 않았습니다. beach는 수목 실루엣이 낮아지고 가지가 드러났지만 해변 자체의 매끈한 모래 경계, 반복되는 거품 줄무늬와 예술적 caustics는 이번 범위에서 유지했습니다. 전체 장면의 스타일 통일, 길 가장자리의 자연스러운 전이와 호수 카메라 가림 조정은 향후 선택할 개선점이며 이번 패스를 무기한 늘리지 않았습니다.

### 검증·통합 범위

| 근거 | 확인 결과 | 한계 |
|---|---|---|
| 최종 private 재로드 | 24/24 검사, 100×100m, 비WP·외부 패키지/BuiltData 없음, 소유 경로 의존성, 최종 색상 저장 확인 | 전체 플랫폼/패키징 검증은 아님 |
| 실제 private PIE | 빙의된 Pawn 이동·지면 sweep 차단·초기 겹침 없음, 63개 Trunk line trace가 각 자기 컴포넌트에 명중 | 63개 나무 검사는 line trace이며 모든 보행 경로 완주 검사는 아님 |
| 수관 기능 | 63개 나무 × leaf/shadow 각 10개, stencil 16–78 고유, 파라미터 refresh, rim/gradient/wind 시각 변화 기록 | CPD 직접 getter는 없음. 렌더 변화는 성능 측정이 아님 |
| 게시물 | 새 자산 10개+맵 SHA 동일, 원본 자산/네이티브 출처 해시·기존 증거 보존 | 쓰이지 않는 이전 활엽수 자산은 복구를 위해 남김 |
| 공유 네이티브 빌드 | ForestDemoEditor Win64 Development 실제 Result:Succeeded / exit 0 | 패키징·다른 RHI 미시험 |
| 공유 빌드 ultra smoke | 새 private 프로세스에서 실제 로드 DLL 경로·SHA, native class, 989 package 소유 의존성, 빙의 PIE·63개 나무 구성 등 16개 검사, exit 0 | 전체 렌더·이동 검사를 반복하지 않음 |
| 공유 빌드 medium smoke | 별도 새 private 프로세스 18개 검사, native 나무 0개, 빙의 PIE, exit 0 | style 배열/GPU pass는 공개 getter 없음. 0개 나무와 동일 소스의 등록 guard에 근거한 비활성 추론 |

공유 `r.CustomDepth=3`은 프로젝트 전체 렌더 설정입니다. 비교 기준 8개 맵의 기존 CustomDepth 사용 census는 enabled/unknown 모두 0이었고 medium의 새 프로세스에서 나무 기능이 등록될 조건이 없음을 확인했습니다. 이는 다른 장면의 GPU 비용이 정확히 0이라는 측정이 아닙니다. medium의 기존 지형 충돌 320,000 triangles navigation export 경고는 별도 성능 개선 항목이며 이번 나무 이식의 새 실패로 분류하지 않았습니다.

색상 탐색 프로세스 한 번은 모든 캡처와 로그 종료 뒤 접근 위반 종료 코드를 반환했습니다. 네이티브 스택은 얻지 못했고 이 일회성 종료 이상은 해결됐다고 주장하지 않습니다. 이후 최종 저장·재로드·캡처/PIE 및 감독의 두 smoke 프로세스는 모두 exit 0입니다. 잘못 인용된 ExecCmds의 기존 대기 프로세스는 사용자가 해당 PID 종료를 직접 승인했던 별도 사건으로 기록되어 있습니다.

- [최종 작업자 결과](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/RESULT.md)
- [최종 private 검증](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/validation.json), [최종 색상](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/final_palette_validation.json)
- [실제 runtime](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/runtime_validation.json), [원본/게시 해시](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/file_audit.json)
- [최종 카메라](D:/github/AstraEffort/ForestDemo/Work/ultra/SelfImprovement/Screenshots/Final/capture_manifest.json)
- [공유 ultra smoke](D:/github/AstraEffort/ForestDemo/Work/UltraImprovementIntegration/Evidence/ultra-smoke.json), [공유 medium smoke](D:/github/AstraEffort/ForestDemo/Work/UltraImprovementIntegration/Evidence/medium-smoke.json)

### 실제 시간과 커밋

| 구분 | 대기 초 | 실행 초 | 비고 |
|---|---:|---:|---|
| Forest 작업자 UE 합계 | 126.290873 | 908.826240 | 시행착오와 최종 색상 캡처 포함; wall의 일부 |
| 작업자 private native build | — | 58.153906 | 15:38:31.012111–15:39:29.164566 UTC |
| 감독 공유 native build | — | 8.742474 | 16:19:57.362666–16:20:06.105139 UTC |
| 감독 ultra smoke | 0.201253 | 20.783594 | 16:28:11.914819–16:28:32.698413 UTC |
| 감독 medium smoke | 0.176382 | 15.767350 | 16:28:33.491688–16:28:49.259038 UTC |
| 이미지 생성 | — | 0 | 원본의 승인된 텍스처 사용; 새 생성 없음 |

모든 KST는 표의 UTC에 명시적으로 +09:00을 적용합니다. 감독 smoke 총 대기는 0.377635초, 실행은 36.550944초입니다. 작업자 ready부터 감독 결과 커밋까지는 420.521285초이며 이 사이의 모든 시간이 UE 실행은 아닙니다. 공유 native 지원 커밋은 `3d1f790641615153688c976aad660113325c6038`(16:23:15 UTC / 01:23:15 KST), 소유 자산·맵·전후 증거 커밋은 `31f7b64b12da02a443d747d5d693fbd4674cef09`(16:31:28 UTC / 01:31:28 KST)입니다.

## MountainStation ultra — 사용자 요청 중단

자기 장면 검토에서 길이 지형에 파묻히는 부분, 침목·자갈층·횡단 구간 연결을 우선 문제로 선택했습니다. 아래는 문제를 살핀 실제 before_fixed 이미지이며 완료된 개선 후 렌더가 아닙니다.

| 작업 전 전체 | 작업 전 길 접점 |
|---|---|
| ![Station before overview](D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement/Screenshots/before_fixed/overview.png) | ![Station before path junction](D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement/Screenshots/before_fixed/path_junction.png) |

감독자가 두 원본을 확인했습니다. 전체 구도에서 역과 철길은 유지되지만 길 일부가 언덕에 끊겨 보이고, 접점 근접샷에는 흙길과 잔디가 각지게 맞물리는 경계가 드러납니다. 작업자는 이를 보완할 137패키지 후보를 만들었으나, 사용자가 2026-10-21 16:03:56 UTC / 2026-10-22 01:03:56 KST에 해당 대화에서 중단과 현재 상태 커밋을 직접 요청했습니다.

작업 종료 기록은 16:05:23.649339 UTC / 01:05:23.649339 KST, wall 1,589.649339초, UE 대기 312.060초·실행 293.038초이며 새 imagegen은 0회입니다. 사용자 승인 커밋 `f7f46b7`은 16:05:50 UTC / 01:05:50 KST에 만들어졌습니다. 이 직접 승인이 워커 Git 금지의 명시적 예외였습니다.

후보 137패키지는 ZIP으로만 보존됐고 공유 프로젝트에 게시하지 않았습니다. 기존 배포 130패키지와 비교 증거 201개는 그대로입니다. imported vertex-color API 사용 오류, 캡처 초기화 cleanup, soft-path 재질 검사와 최종 런타임·의존성·UV·해시 검증이 남아 있습니다. 완료된 전후 쌍이 없으므로 개선 효과·최종 통과를 주장하지 않습니다. 새 사용자 지시 전에는 재개하지 않습니다.

[중단 시점 RESULT](D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement/RESULT.md)와 [STATUS](D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/SelfImprovement/STATUS.json)에 후보와 미완료 사항을 보존했습니다.

## 별도 토큰 증분

같은 ID의 마지막 누적값에서 기준 누적값을 한 번 빼고, 기준 이후 생성이 확인된 후손을 한 번씩 포함했습니다. 감소·기준 불명·계수 범위 미확인은 0으로 대체하지 않습니다. 캐시 입력은 입력의 일부, 추론은 출력의 일부이며 중복 가산하지 않았습니다. 다음 수치는 로컬 토큰 계수이고 이미지 생성/외부 모델 호출 또는 청구 금액이 아닙니다.

| 테마 | 기준 UTC / KST | 기준 부모+후손 | 관측 마감 UTC / KST | 부모 증분 | 검증 후손 증분 | 합계 증분 |
|---|---|---:|---|---:|---:|---:|
| Forest ultra | 15:28:19.915029 / 00:28:19.915029 | 25,073,209 | 16:29:16.404937 / 01:29:16.404937 | 11,934,544 | 1,047,181 | 12,981,725 |
| Station ultra | 15:37:23.463169 / 00:37:23.463169 | 32,669,468 | 16:10:20.985090 / 01:10:20.985090 | 4,567,048 | 2,255,354 | 6,822,402 |

UTC 날짜는 2026-10-21, KST 날짜는 2026-10-22입니다. 두 작업의 확인된 합계 증분은 19,804,127입니다. Forest 최종 부모 토큰 이벤트는 16:26:35 UTC로 ready 시각 뒤에 있으므로 표는 보고·정리를 포함한 후속 대화 누적이며 정확한 ready 순간 사용량이 아닙니다. 작업자 모델/effort는 두 부모 모두 기존 gpt-6-astra/ultra로 관측됐습니다. 각 ID의 입력·캐시·비캐시·출력·추론 구성은 별도 JSON에 있습니다.

감독 대화는 위 두 제작 합계에서 제외했습니다. 16:29:16 UTC 관측 시 감독 부모는 73,964,938, 비교 경계 부모는 51,794,424여서 경계 뒤 부모 증가분은 22,170,514입니다. 이 기간에는 남은 비교 검토·통합도 섞여 있으므로 순수 자가 개선 감독 비용으로 귀속하지 않습니다. 감독 후손의 일부 계수가 미확인이라 감독 부모+후손 총합은 unknown입니다. 이후 보고서 정리 토큰도 이 관측 시각에는 포함되지 않습니다.

- [Forest 기준](D:/github/AstraEffort/ForestDemo/Work/UltraImprovementAccounting/forest_baseline.json), [최종 부모·후손 증분](D:/github/AstraEffort/ForestDemo/Work/UltraImprovementAccounting/forest_final_delta.json)
- [Station 기준](D:/github/AstraEffort/ForestDemo/Work/UltraImprovementAccounting/station_baseline.json), [중단 시점 증분](D:/github/AstraEffort/ForestDemo/Work/UltraImprovementAccounting/station_stopped_delta.json)
- [최종 원본 스냅샷](D:/github/AstraEffort/ForestDemo/Work/UltraImprovementAccounting/final_snapshot.json)

## 감독 종료 범위

Forest 개선은 검증·개별 커밋했고, Station 개선은 사용자의 중단 요청과 체크포인트를 존중해 종료했습니다. 비교 실험의 최종 8맵 통합·보고서·토큰 동결은 별도로 끝났습니다. 기존 여덟 맵은 모두 보존했고 기본 시작 맵은 medium입니다. 이 보고서와 별도 회계·감독 smoke 증거를 커밋한 뒤 자동 감독을 정지하며 새 작업을 임의로 시작하지 않습니다.

보고서 정리 시각: 2026-10-21 16:34:02.0022984 UTC / 2026-10-22 01:34:02.0022984 KST(+09:00).
