# 복셀 모델 9테마 · 45종 · 90버전

**출력 검사와 렌더 검토를 마친 상태에서 사용자 요청으로 중단했습니다. 신규 9테마는 아직 시작하지 않았습니다.**

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
