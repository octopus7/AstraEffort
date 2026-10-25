# Set 01 — 둥근 산업형 게임 에셋 4종

레퍼런스 이미지 4장을 메인에서 순차 생성한 후, 메인과 max 추론 서브에이전트 3개가 각각 모델 하나씩 병렬 제작했습니다. 아래 미리보기는 실제 Blender 렌더입니다.

| 모델 | BLEND | GLB | FBX | 삼각형 수 | 크기 X × Y × Z (m) |
|---|---|---|---|---:|---|
| 4륜 화물 운반차 | [편집 파일](cargo_rover/cargo_rover.blend) | [GLB](cargo_rover/cargo_rover.glb) | [FBX](cargo_rover/cargo_rover.fbx) | 156,628 | 2.33 × 4.05 × 2.41 |
| 2족 정비 메카 | [편집 파일](service_mech/service_mech.blend) | [GLB](service_mech/service_mech.glb) | [FBX](service_mech/service_mech.fbx) | 151,052 | 2.58 × 1.29 × 2.80 |
| 아치 지붕 정비소 | [편집 파일](arched_workshop/arched_workshop.blend) | [GLB](arched_workshop/arched_workshop.glb) | [FBX](arched_workshop/arched_workshop.fbx) | 184,984 | 7.49 × 6.40 × 4.50 |
| 물탱크 급수소 | [편집 파일](water_station/water_station.blend) | [GLB](water_station/water_station.glb) | [FBX](water_station/water_station.fbx) | 245,200 | 6.50 × 4.88 × 5.43 |

각 모델은 편집 가능한 개별 부품과 이름이 지정된 PBR 재질을 포함합니다. `ASSET` 컬렉션은 모델, `STUDIO`는 미리보기용 조명·카메라·바닥입니다. 내보낸 GLB/FBX에는 모델 형상만 포함됩니다.

## 실제 모델 미리보기

### 4륜 화물 운반차

![4륜 화물 운반차 실제 Blender 렌더](cargo_rover/renders/hero.png)

[후면 렌더](cargo_rover/renders/rear.png) · [생성 레퍼런스](../../REF/Set01/cargo_rover.png) · [제작 기록](cargo_rover/RESULT.md) · [재검증](validation/cargo_rover.json)

### 2족 정비 메카

![2족 정비 메카 실제 Blender 렌더](service_mech/renders/hero.png)

[후면 렌더](service_mech/renders/rear.png) · [생성 레퍼런스](../../REF/Set01/service_mech.png) · [제작 기록](service_mech/RESULT.md) · [재검증](validation/service_mech.json)

### 아치 지붕 정비소

![아치 지붕 정비소 실제 Blender 렌더](arched_workshop/renders/hero.png)

[후면 렌더](arched_workshop/renders/rear.png) · [생성 레퍼런스](../../REF/Set01/arched_workshop.png) · [제작 기록](arched_workshop/RESULT.md) · [재검증](validation/arched_workshop.json)

### 물탱크 급수소

![물탱크 급수소 실제 Blender 렌더](water_station/renders/hero.png)

[후면 렌더](water_station/renders/rear.png) · [생성 레퍼런스](../../REF/Set01/water_station.png) · [제작 기록](water_station/RESULT.md) · [재검증](validation/water_station.json)

## 확인한 사항

모든 저장 BLEND와 재수입 GLB·FBX에서 크기와 삼각형 수가 일치했습니다. 누락된 UV·재질·외부 이미지, 비정상 좌표, 면적이 0인 삼각형은 공통 검증에서 발견되지 않았습니다. 앞·뒤 실제 렌더는 메인에서 직접 확인했습니다.

## 범위와 한계

정적 모델이며 리깅·애니메이션·LOD·충돌 메시와 엔진 통합은 포함하지 않습니다. UV는 부품별로 제공하며 통합 아틀라스와 공통 텍셀 밀도를 맞추는 작업은 수행하지 않았습니다. 재질은 단색 PBR 중심으로, 레퍼런스의 미세한 오염 표현을 텍스처로 굽지는 않았습니다. FBX 재질은 사용하는 엔진에서 조정이 필요할 수 있습니다.

레퍼런스 원본과 최종 프롬프트는 [REF/Set01](../../REF/Set01)에, 생성 시각은 [generation_manifest.json](../../REF/Set01/generation_manifest.json)에 있습니다.
