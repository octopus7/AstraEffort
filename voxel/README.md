# 현재 복셀 제작 체크포인트

이 문서는 초기 일반 메시 모델 2세트·8종과 별도로 제작한 복셀 모델의 기록입니다.

[작은 버전 73종 한 장으로 둘러보기](overview_half_all.png) · [모음 이미지 출처 및 원본 보존 확인](overview_half_all.json)

사용자 요청으로 현재 작업을 고정해 커밋합니다. **최종 승인 13테마·61모델·122버전**, 메인 검수 대기 8모델(비행장·재활용), 출력 후 검증 전인 지열 4모델입니다. 운하·캠핑 8모델은 아직 시작하지 않았습니다. 전체 목표는 18테마·81모델·162버전입니다.

[진행 및 이어서 할 작업](RESUME.md) · [체크포인트 검사 기록](CHECKPOINT.json) · [진행 상태](EXPANSION_STATE.json)

이번에 승인한 테마: [산림·제재소](forestry/RESULT.md), [건설 현장](construction/RESULT.md), [소방·구조](fire_rescue/RESULT.md), [제과·제빵](bakery/RESULT.md). 검수 대기: [비행장](airfield/RESULT.md), [재활용](recycling/RESULT.md). 작업 중: [지열](geothermal/RESULT.md). 신규 9테마 레퍼런스는 모두 REF/voxel에 저장되어 있습니다.

# 복셀 모델 9테마 · 45종 · 90버전

**아래 목록과 비교 갤러리는 이전 커밋 63e475d의 45종 카탈로그입니다. 현재 제작 진행은 위 체크포인트와 RESUME.md를 기준으로 합니다.**

[큰·절반 비교 갤러리](index.html) · [전체 파일 목록](delivery_manifest.json) · [다음 작업 인계](RESUME.md)

큰 버전은 긴 축 128복셀, 절반 버전은 64복셀입니다. 각 축 복셀 수를 절반으로 줄이고 복셀 크기를 두 배로 하여 같은 물리적 격자 크기를 유지합니다. 기존 39종에 유용한 모델 6종을 추가했습니다.

| 테마 | 모델 수 | 기존 제작 기록 | 보강 모델 |
|---|---:|---|---|
| 농장 | 5 | [farm](farm/RESULT.md) | [Farm combine harvester](farm/additions/RESULT.md) |
| 공장 | 5 | [factory](factory/RESULT.md) | [Articulated robot assembly workcell](factory/additions/RESULT.md) |
| 남극 연구기지 | 5 | [antarctic](antarctic/RESULT.md) | [Sled-mounted Antarctic ice core drill](antarctic/additions/RESULT.md) |
| 항구 | 5 | [harbor](harbor/RESULT.md) | [Empty harbor repair dock](harbor/additions/RESULT.md) |
| 광산 | 5 | [mine](mine/RESULT.md) | [Six-wheel open-bed mine haul truck](mine/additions/RESULT.md) |
| 사막 전초기지 | 5 | [desert](desert/RESULT.md) | [사막 정수 장치](desert/additions/RESULT.md) |
| 산악 철도 | 5 | [mountain_railway](mountain_railway/RESULT.md) | — |
| 우주항 | 5 | [spaceport](spaceport/RESULT.md) | — |
| 해저 탐사기지 | 5 | [underwater](underwater/RESULT.md) | — |

모델마다 `.vox`, `.blend`, `.glb`, `.fbx`, `preview.png`, `metadata.json`이 있습니다. 기존 모델은 `테마/assets/모델명/{large,half}`, 보강분은 `테마/additions/assets/모델명/{large,half}`에 있습니다. VOX가 편집 기준 원본이며 BLEND에는 별도 STUDIO 컬렉션, GLB/FBX에는 모델 형상만 포함합니다.

원본 복셀 파싱, 색상·크기·표면 검사, BLEND·GLB·FBX 재가져오기를 통과했고 모든 최종 미리보기를 메인이 직접 확인했습니다. 기존 39종의 모델 파일 해시는 그대로입니다. 생성 레퍼런스와 프롬프트는 [REF/voxel](../REF/voxel)에 있습니다.

정적 팔레트 모델입니다. 리깅·애니메이션·충돌·엔진 통합은 포함하지 않으며 유리는 불투명 색상입니다. 얇은 구조를 보존하는 축소 방식으로 외곽이 큰 격자 한 칸까지 넓어질 수 있습니다. MagicaVoxel GUI에서는 검사하지 않았습니다.

이전 `voxel-nine-themes.zip`은 최초 39종 묶음으로 로컬에 보존하며 Git에는 중복 압축파일을 넣지 않습니다. 현재 45종의 기준은 이 목록과 실제 모델 폴더입니다.
