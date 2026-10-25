# 오래된 풍차 농장 — ultra

사용자가 2026-10-22 KST에 기존 Forest ultra 대화에서 새 테마 제작을 즉시 시작하도록 승인했다. 기존 숲은 보존하고 새 경로를 사용하며, 이 작업은 기존 추론 강도 비교 실험 및 측정 대상에서 제외한다. 새 대화를 만들지 않는다.

## 새 작업의 소유 경로

- 대화: `01a15e5f-fef9-7323-8733-3c0553c29d7e` / local. 기존 모델을 유지하고 effort는 ultra.
- 자산: `ForestDemo/Content/WindmillFarm/ultra/**` (`/Game/WindmillFarm/ultra`).
- 레벨: `ForestDemo/Content/Maps/WindmillFarm_ultra.umap` 하나.
- 제작 코드, 원본, 상태, 검증, 캡처 및 별도 결과 보고서: `ForestDemo/Work/WindmillFarm/ultra/**`.
- 새 private scratch: `ForestDemo/Saved/Workers/WindmillFarm/ultra/**`.
- 최종 결과 보고서: `ForestDemo/Work/WindmillFarm/ultra/RESULT.md`.

이 명시적 새 배정은 기존 AGENTS.md의 Forest 작업 경로 표를 이번 작업에 한해 대체한다. 기존 Forest 자산/맵/Work/SelfImprovement/scratch는 이번 작업 소유 경로가 아니다. 전역 AGENTS.md에 개별 제작 지시를 추가하지 않는다.

## 제작 방향

이전 대화의 차분한 색감과 둥근 모서리의 게임 아트를 이어간다. 설계 기본값은 약 100×100m의 독립적인 농장 장면이다. 오래된 풍차를 중심으로 풍화된 목재와 석재, 작은 농장 건물, 밭과 초지, 울타리·수레·도구 등 어울리는 프랍, 접근 가능한 산책 동선을 구성한다. 정확한 배치와 프랍 선택은 작업자가 자율 결정한다. 낡았지만 관리되는 시골 농장 분위기로 만들고 얼굴·하트·장식 구름은 넣지 않는다.

길과 풀의 경계는 불규칙한 전이, 흙/풀 재질 혼합 및 절제된 식생 배치로 자연스럽게 구성한다. 건축/풍차 비례와 지면 접지, 길 가독성을 확인한다. 고유 표면 UV와 적절한 텍셀 밀도, 표면별 목재·돌·금속 묘사를 준비한다. 이미지 생성이 필요한 텍스처는 자기 경로에 독립 생성하고 원본/프롬프트/매핑을 기록한다. 기존 다른 테마의 창작 자원이나 외부 Tuna 나무를 이번 작업에 복사·참조하지 않는다.

## 보존과 실행 규칙

기존 Forest 네 장면과 MountainStation 네 장면, 공용 기본 맵 설정을 보존한다. 기존 Content/Forest 및 Content/MountainStation, 기존 8개 .umap, 기존 작업 자료와 보고서를 수정하거나 덮어쓰지 않는다. `SUPERVISION.md`, `token_usage.json`, `ComparisonFreeze`, `ULTRA_IMPROVEMENT.md`, 기존 회계 파일은 수정하지 않는다. 비교 토큰 수집 도구나 비교 측정을 이번 작업 때문에 실행하지 않는다. 새 결과를 비교 표/순위/시간·토큰 비교에 추가하지 않는다.

새 scratch를 만들고 거기서 제작·검증한다. 공용 Source/Plugins/Config/uproject/Binaries와 UE 실행 도구는 읽기 전용이다. 필요한 공용 지원 변경은 자기 Work 안에 제안만 남기고 감독자에게 알린다. 모든 새 /Game 의존성은 자기 WindmillFarm/ultra 및 자기 맵에 한정한다. Engine 기본 자원과 baseline ForestDemo 클래스는 읽기 전용으로 사용 가능하다. 공유 제작 자원 또는 다른 테마 자산을 scratch에 복사하지 않는다.

private UE는 `Work/Tools/Run-UnrealIsolated.ps1`을 사용한다. 새 WindmillFarm 경로는 현재 실행기의 기타 우선순위(2)로 처리되며 Forest 우선권을 얻으려고 경로를 위장하지 않는다. 실행 중인 다른 UE나 launcher를 종료하지 않는다. 단독 Blender 프로세스는 자기 소유 파일에만 작업한다. worker는 Git index/commit/branch를 조작하지 않는다. 검증 후 커밋은 감독자 담당이다.

## 완료와 보고

자기 `STATUS.json`에 theme=WindmillFarm, effort=ultra, working/needs_attention/ready_for_review, 실제 시작/완료 시각, 경로, 검증 및 blockers를 남긴다. 비교용 토큰/성능 벤치마크는 작성하지 않는다.

새 프로세스에서 저장 맵 재로드, 지형 범위, PlayerStart/PIE 시작과 충돌, 재귀 의존성, 머티리얼/UV/텍스처, non-World-Partition, external packages/BuiltData 부재를 확인한다. 실제 검증하지 않은 사항을 성공으로 쓰지 않는다. private UE를 닫은 후 검증된 자기 자산 폴더와 지정 .umap만 게시한다.

실제 UE 렌더 1920×1080으로 `Screenshots/overview.png`, `top_down.png`, `windmill.png`, `farm_detail.png`를 제공한다. capture_manifest.json에는 실제 카메라·렌더 설정과 시각을 기록한다. 생성 이미지는 재질용이며 장면 증거를 대신할 수 없다.

별도 `RESULT.md`에 장면 의도, 구현 결과, 자산/맵 경로, 실제 렌더 이미지, 검증 결과·한계와 재현 방법을 작성한다. 이 작업 결과만 다루고 이전 비교나 자가 개선 보고서에 합치지 않는다. 사용자는 이미 작업 시작을 승인했으므로 통상적인 디자인 선택은 자율적으로 진행하고 실제 blocker만 보고한다.
