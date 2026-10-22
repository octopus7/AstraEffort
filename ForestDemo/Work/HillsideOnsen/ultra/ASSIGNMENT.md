# 산비탈 온천 마을 — ultra

사용자가 기존 MountainStation ultra 대화에서 이 새 테마를 제작하도록 승인했다. 현재 대화를 이어 사용하고 새 대화는 만들지 않는다. 기존 모델을 유지하며 추론 강도는 ultra로 유지한다. 이번 작업은 추론 강도 비교와 측정에서 제외하고 결과 보고서는 독립 작성한다.

## 명시적 소유 범위

- 대화 ID: `01a15e6e-1907-7ff1-b13c-5a4a31875490`, host: local.
- 자산: `ForestDemo/Content/HillsideOnsen/ultra/**` / `/Game/HillsideOnsen/ultra`.
- 레벨: `ForestDemo/Content/Maps/HillsideOnsen_ultra.umap` 하나.
- 제작 코드·원본·상태·검증·캡처·보고서: `ForestDemo/Work/HillsideOnsen/ultra/**`.
- 새로운 private scratch: `ForestDemo/Saved/Workers/HillsideOnsen/ultra/**`.
- 최종 별도 보고서: `ForestDemo/Work/HillsideOnsen/ultra/RESULT.md`.

이 사용자 승인 배정이 이번 작업에 한하여 AGENTS.md의 기존 테마 소유 표를 확장한다. 이전 대화 이름과 effort가 같아도 작업 식별자는 (HillsideOnsen, ultra)이며 이전 작업 경로가 아니다. 전역 AGENTS.md에 테마별 구현 지시를 추가하지 않는다.

## 제작 방향

산비탈의 높낮이에 맞춘 작은 테라스형 마을을 구성한다. 자연석 노천탕과 은은한 수증기, 목재와 석재의 작은 숙소/목욕 건물, 계단·완만한 접근로·난간, 물길과 바위·식생을 어울리게 배치한다. 경사와 건물 기초의 접지, 온천과 보행 동선의 연결, 마을 건축 비례가 읽혀야 한다. 수증기와 수면은 실제 UE에서 표현하고 사용한 근사 기법과 한계를 보고한다.

기존에 합의한 차분한 색조와 둥근 모서리의 게임 아트를 유지한다. 얼굴·하트·장식 구름은 넣지 않는다. 약 100×100m 장면을 기본값으로 두고 정확한 배치·건축 스타일·프랍 선택은 자율 설계한다. 보행 가능한 공간, 자연스러운 길/풀 경계와 절제된 프랍 밀도를 확인한다. 표면에 맞는 UV 아일랜드와 일관된 텍셀 밀도, 목재·돌·금속·물의 차이가 드러나는 재질을 구성한다. 이미지 생성이 필요하면 자기 텍스처를 독립 생성하고 프롬프트·원본·UV 매핑을 자기 Work에 남긴다. 새로운 창작 자원은 모두 자기 테마 안에 둔다.

## 보존과 격리

기존 산악 기차역 및 그 ultra 개선본은 완료 또는 제출된 현재 상태 그대로 보존한다. 이전 작업에 확인되지 않은 성공 표시나 임의 수정·커밋을 추가하지 않는다. 기존 Forest/MountainStation/WindmillFarm 자산, 기존 모든 맵, 이전 Work 및 scratch를 수정하거나 삭제하지 않는다. 이미 생성된 미커밋 결과도 그대로 보존한다. 이전 창작 자산·제작 스크립트·텍스처를 읽기/복사/참조하여 새 테마에 재사용하지 않는다. 다른 새 테마 작업도 같은 격리 원칙을 적용한다. 이전 hardcoded 경로가 들어 있는 생성·게시 스크립트를 실행하지 않는다.

`SUPERVISION.md`, `token_usage.json`, `ComparisonFreeze/**`, `ULTRA_IMPROVEMENT.md`, 기존 회계와 이미지·검증 증거는 수정하지 않는다. 이번 작업을 위해 비교 토큰 수집 도구, 추론 강도 벤치마크, 비교 표·순위·시간/토큰 집계를 실행하거나 추가하지 않는다. 실제 시작/완료 시각 및 UE 실행 로그는 이 작업의 재현·운영 기록으로 자기 Work에만 남긴다.

## 실행과 검증

완전히 새로운 자기 scratch에서 제작한다. baseline Source/Config/uproject 등 최소 실행 기반과 /Engine 내장 자원만 읽기 전용 복사/참조 가능하다. 기존 테마 Content나 ForestUltraTrees 같은 테마 전용 지원을 가져오지 않는다. 공용 Source/Plugins/Config/uproject/Binaries 및 기존 시작 맵 설정은 수정하지 않는다. 공용 지원이 꼭 필요하면 자기 Work에 IntegrationProposal로 제안한다.

private UE는 `Work/Tools/Run-UnrealIsolated.ps1`로 실행한다. 새 테마 경로는 현재 runner에서 Unknown/priority=2로 등록되지만 mutex 직렬화는 적용된다. 기존 테마 우선권을 얻으려고 경로를 바꾸거나 runner를 수정하지 않는다. 이미 실행 중인 UE/launcher를 종료하지 않는다. Blender는 자기 파일만 다루는 독립 프로세스를 사용한다. Git index/커밋/브랜치 변경은 금지하며 감독자가 검증 후 처리한다.

새 프로세스의 저장 맵 재로드, 범위/건물 접지, PlayerStart 및 실제 PIE 시작/대표 보행 구간의 충돌, UV/재질·효과, /Game 재귀 의존성이 자기 테마와 자기 맵뿐인지 검증한다. non-World-Partition과 external actor/object packages 없음, 동적 조명과 map-adjacent BuiltData 없음도 확인한다. 실제 확인하지 않은 사항은 성공으로 쓰지 않는다. private UE 종료 후 검증된 자기 소유 자산 폴더와 지정 맵만 게시한다.

## 결과 제출

`STATUS.json`에 theme=HillsideOnsen, effort=ultra, status=working/needs_attention/ready_for_review, 실제 시작/완료 시각, map, validation, blockers를 새로 기록한다. 사용자는 작업 시작을 승인했으므로 통상적인 디자인과 구현 선택은 자율 진행하고 실질적인 blocker만 보고한다.

실제 UE 1920×1080 캡처 `Screenshots/{overview, top_down, hot_spring, village_path}.png`와 카메라·렌더 설정·실제 촬영 시각을 적은 capture_manifest.json을 제공한다. 시간에 따른 효과는 고정 카메라 시차 이미지 또는 짧은 실제 UE 영상으로 확인한다. 이미지 생성 결과는 자산 제작용이며 실제 장면 증거로 대체할 수 없다.

`RESULT.md`에는 이 장면의 의도, 구현 내용, 자산/레벨 경로, 실제 렌더 이미지, 검증·한계, 다시 열고 재현하는 방법을 작성한다. 기존 비교 보고서나 이전 개선 보고서에 합치지 않는다.

