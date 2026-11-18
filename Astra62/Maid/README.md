# Luna Mk.3

은빛 트윈테일과 검은 메이드복을 입은 게임용 캐릭터입니다. 두 버전은 같은 체형과 A 포즈, 같은 스켈레톤을 사용합니다. 머리 장식을 포함한 키는 약 146.7cm입니다.

원화의 확대 컷에서 윗속눈썹의 윤곽, 남색에서 청록색으로 밝아지는 홍채, 위쪽의 흰 반사광 두 점을 옮겼습니다. 두 버전 모두 턱을 짧고 둥글게 만들고 코 아래와 윗입술 양옆을 앞으로 빚어, 옆에서 고양이형 입매가 드러납니다. [원화·수정 전후 얼굴 비교](Luna_Mk3_FaceComparison.jpg) · [전신과 표정](Luna_Mk3_Preview.jpg)

| 버전 | 원본과 교환 파일 | 표정 제어 |
|---|---|---|
| 입체 얼굴 | `ModeledFace/Luna_Mk3.blend`, `ModeledFace/Luna_Mk3.fbx` | 독립 안구와 눈썹, 눈꺼풀, 입술과 입안 메시. `eye_l`·`eye_r`로 시선을, `Blink_L`·`Blink_R`·`MouthOpen`·`Smile`로 표정을 조절합니다. |
| 텍스처 얼굴 | `TextureFace/Luna_Mk3.blend`, `TextureFace/Luna_Mk3.fbx` | 안구·눈썹·입 지오메트리를 생략한 얼굴입니다. `Expression` 값으로 기본(0), 눈 감기(1), 미소(2)를 전환합니다. |

## Unreal Engine 5.7

`Unreal/Luna_Mk3.uproject`를 열면 콘텐츠 브라우저의 `/Game/Maid/ModeledFace`와 `/Game/Maid/TextureFace`에 각각 `Luna_Mk3` 스켈레탈 메시가 있습니다. 기존 프로젝트로 가져갈 때는 `Maid` 폴더에서 **Asset Actions → Migrate**를 사용하면 스켈레톤·재질·텍스처도 함께 옮겨집니다.

텍스처 얼굴의 표정은 얼굴 슬롯에 연결된 `MI_Luna_Mk3_Expression`에서 바꿉니다. 플레이 중에는 해당 슬롯에 다이내믹 머티리얼 인스턴스를 만들고 `Set Scalar Parameter Value`로 `Expression`을 설정하면 캐릭터마다 다른 표정을 쓸 수 있습니다. Blender에서는 `Face` 메시의 셰이더 에디터에 같은 이름의 Value 노드가 있습니다.

입체 얼굴은 UE5.7 플레이 시뮬레이션에서 좌우 눈을 따로 감고, 입 벌리기와 미소를 각각 재생해 확인했습니다. 텍스처 얼굴은 엔진에서 기본·눈 감기·미소를 같은 카메라로 확인했습니다.

스켈레톤은 UE5 Manny 본 161개의 이름과 부모 관계를 유지합니다. 캐릭터 비율에 맞춰 본 위치를 조정했고, 양쪽 눈에 1개씩, 양쪽 트윈테일에 5개씩 보조 본을 추가했습니다. Manny 애니메이션을 옮길 때는 `IK_Luna_Mk3`를 타깃 IK Rig로 지정합니다. 검증에는 엔진에 포함된 `MM_Walk_InPlace`를 사용했습니다.

## 텍스처와 LOD

두 버전이 아래 세 PNG를 공유합니다. Blender 원본에도 같은 이미지를 패킹했습니다.

| 파일 | 해상도 | 대응하는 표면 |
|---|---:|---|
| `Textures/T_Luna_Mk3_Body.png` | 2048 × 2048 | 몸의 피부, 모든 의상, 머리 장식, 신발 |
| `Textures/T_Luna_Mk3_Face.png` | 2048 × 2048 | 왼쪽 위 기본, 오른쪽 위 눈 감기, 왼쪽 아래 미소, 오른쪽 아래 입체 얼굴용 피부·홍채·입술 |
| `Textures/T_Luna_Mk3_Hair.png` | 1024 × 1024 | 앞머리, 옆머리, 뒷머리, 트윈테일 |

| 엔진 메시 | LOD 0 삼각형 | LOD 1 삼각형 | LOD 2 삼각형 |
|---|---:|---:|---:|
| 입체 얼굴 | 60,162 | 22,860 | 11,430 |
| 텍스처 얼굴 | 54,596 | 20,745 | 10,372 |

UE의 모든 LOD는 몸·얼굴·헤어 3개 재질 슬롯을 사용합니다. Blender와 FBX에는 편집용 최고 해상도 모델이 들어 있습니다. FBX를 단독 임포트할 때 입체 얼굴의 **Import Morph Targets**를 켜세요. 텍스처 얼굴의 표정 전환 머티리얼은 위 UE 프로젝트에 포함되어 있습니다.

토폴로지는 `extraction_shooter/Blender/SKM_LunaMk2.blend`에서 얼굴의 눈꺼풀·입 주변 루프, 얼굴 파츠 분리, 트윈테일 체인을 참고했습니다. 외형과 의상은 제공된 메이드 레퍼런스를 기준으로 모델링했습니다.
