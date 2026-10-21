# Ultra 자가 개선 결과 보고서

현재 상태: **Forest·MountainStation 기존 ultra 두 대화에 자가 개선 지시 완료**.

이 문서는 두 ultra 대화의 유한한 후속 개선만 기록합니다. 최신 사용자 지시에 따라
두 작업 모두 다른 강도의 완료나 전체 통합을 기다리지 않습니다. 각자의 개선 전 비교
결과를 보존한 뒤 진행하며, 개선 계획·진행·결과·시간·토큰은 SUPERVISION.md에 넣지 않습니다.
아직 최종 개선 결과가 제출되었다는 뜻은 아닙니다.

## 비교 기록과의 경계

- Forest 네 최초 납품과 TexturePass는 검증·개별 커밋을 완료했습니다.
- Forest ultra 개선 전 납품 커밋은 `8a686096a17e6560bd8b08241746eef7606fa8e1`이며,
  변경 직전 전체 저장소 기준은 `65f16249f1aacb3dee28b3c3f12b1c70b6207d63`입니다.
- Forest 네 작업의 FirstDelivery/TexturePass 1,621개 파일은
  `UltraImprovementAccounting/forest_comparison_evidence_freeze.json`의 SHA256으로 고정했습니다.
  원본 증거의 줄바꿈까지 보존하는 보정 커밋은 `9eb27078afedfc1e236d81d7b3d0760d958ace42`입니다.
- Forest 네 대화와 감독 비교 토큰 경계는 **2026-10-21 15:28:19.9150287 UTC /
  2026-10-22 00:28:19.9150287 KST(+09:00)**입니다. 감독 행은 이 경계 뒤의 기차역 감독분도
  포함하지 않는 보수적인 부분 집계입니다. 비교 보고서의 나머지 기차역 제작 수치는 계속 집계합니다.
- 기차역 ultra도 자기 TexturePass를 검증·커밋하고 별도 기준 시각을 고정한 뒤 시작합니다.
  medium/high/xhigh에는 자가 개선을 지시하지 않습니다.
- 이후 비교용 8맵 통합 검증은 각자의 **개선 전 커밋**을 감독자 scratch에 구성해 수행합니다.
  작업 중인 ultra 자산을 되돌리거나 비교 자료를 새 결과로 덮어쓰지 않습니다.

## Forest / ultra

- 기존 대화: `01a15e5f-fef9-7323-8733-3c0553c29d7e`, 기존 `gpt-6-astra` / ultra 유지.
- 실제 재개 턴 시작: **2026-10-21 15:30:23 UTC / 2026-10-22 00:30:23 KST(+09:00)**.
  작업자 제작 시작은 2026-10-21 15:30:53 UTC / 2026-10-22 00:30:53 KST이며 완료·wall·UE 시간은 진행 중입니다.
- 필수 변경: 읽기 전용 원본 `D:/github/extraction_shooter/TunaSweeper`의
  `Content/Environment/AnimeTree/BP_AnimeFoliageTree.uasset`를 가져와 기존 활엽수를 대체합니다.
- 원본 BP는 UE 5.7의 `TunaSweeperAnimeTreeActor` 네이티브 부모를 참조합니다.
  바람·그라디언트·고정 그림자 프록시와 `CanopyRim` 렌더링 의존성을 보존하는 이식을 진행합니다.
  단순 파일 복사를 성공으로 취급하지 않습니다. 원본 프로젝트는 수정하지 않습니다.
- 필요한 외부 의존성 사용은 이번 Forest ultra에 대한 명시적 예외입니다.
  최종 자산은 `/Game/Forest/ultra` 안에 두고, 다른 강도/테마와 공유하지 않습니다.
  공용 네이티브 지원이 필요하면 워커는 IntegrationProposal만 작성하고 감독자가 통합합니다.
- 새 코드·검증·출처·STATUS/RESULT·실제 PNG: `Work/ultra/SelfImprovement/`.
- 시작 전 토큰: 부모 **23,634,637**, 확인된 후손 **1,438,572**, 합계 **25,073,209**.
  원본 스냅샷은 `UltraImprovementAccounting/forest_baseline.json`입니다.
- 결과·검증·완료 시각·증분·개선 커밋: 아직 없음.

## MountainStation / ultra

- 기존 대화: `01a15e6e-1907-7ff1-b13c-5a4a31875490`, 기존 모델 / ultra 유지.
- 다른 강도의 완료를 기다리지 않고 시작하도록 추가 승인되었습니다.
- 자기 TexturePass는 2026-10-21 15:30:03.551119 UTC에 제출되었으며 감독 검증 후 커밋했습니다. 기준 커밋은 `3e13e569b0e8725f4a9faaeee8e3d13ddf7b5737`(15:36:44 UTC)입니다.
  이 납품의 완료 시간과 후속 개선 시작 시간을 합치지 않습니다.
- 새 코드·검증·STATUS/RESULT·실제 PNG: `Work/MountainStation/ultra/SelfImprovement/`.
- 자기 장면을 검토해 개선 우선순위를 선택합니다. Forest 나무 이식 요구를 이 작업에 추가하지 않습니다.
- 같은 대화에 자가 개선을 한 번 명시적으로 지시했습니다. 실제 제작 시작은 2026-10-21 15:38:54 UTC / 2026-10-22 00:38:54 KST입니다. 자기 검토로 길이 지형에 파묻히는 부분과 침목·자갈층·횡단구간의 연결을 우선 선정했습니다. 최종 검증 전입니다.
- 비교 증거 201개 파일을 `station_comparison_evidence_freeze.json`에 고정했습니다.
- 시작 전 토큰 경계는 2026-10-21 15:37:23.4631689 UTC / 2026-10-22 00:37:23.4631689 KST(+09:00)입니다. 부모 31,201,862, 후손 1,467,606, 합계 32,669,468이며 `station_baseline.json`에 보존했습니다.
- 개선 결과·완료·증분·커밋은 아직 없습니다.

## 검증과 집계 원칙

두 장면의 필수 구성·100×100m·차분하고 둥근 아트는 유지합니다. 실제 저장 맵 재로드,
자기 경로만의 재귀 의존성, non-World-Partition, 플레이·충돌을 검증하고 감독자가 이미지를
직접 확인합니다. 전후 장면 증거는 실제 UE 렌더이며 같은 카메라의 1920×1080 PNG를
SelfImprovement/Screenshots에 보존합니다. FirstDelivery/TexturePass 파일은 수정하지 않습니다.

새 토큰은 `Update-TokenUsage.ps1 -NoWrite -IgnoreComparisonCutoffs`로 조회하여
`Work/UltraImprovementAccounting/`에만 저장합니다. 같은 ID의 마지막 누적값 차이와 새 후손을
중복 없이 합산하며, parent/검증된 child와 unknown을 구분합니다. 비교용 기본 집계는
coordination.comparison_token_cutoffs를 지켜 해당 후속 사용량을 제외합니다. 전체 비교 동결 후에는
비교 파일 쓰기를 금지합니다. 청구 금액으로 환산하지 않습니다.

워커의 Git 조작은 계속 금지합니다. 감독자가 각 결과 검증 후 개별 커밋하고 이 보고서를
완성·커밋합니다. 공유 UE의 최신 우선순위는 MountainStation medium → Forest → 나머지 MountainStation입니다. 실행 중인 작업은 중단하지 않습니다.

