Rabbit Bike — 벌쳐 스타일의 토끼 모티프 삼륜 바이크

파일
  RabbitBike.glb        4K 텍스처가 내장된 단독 사용 가능한 glTF 2.0 파일
  RabbitBike.blend      편집 가능한 Blender 4.5 원본, 이미지 패킹, 프리뷰 스튜디오 포함
  textures/            생성 이미지 원본 3장과 최종 UV 아틀라스
  renders/hero.png     실제 Blender 원본 렌더
  renders/glb_reimport_front.png, rear.png, side.png, front_suspension.png
                      최종 GLB를 새 세션에 다시 불러와 촬영한 실제 렌더
  validation/UV_layout_4096.png  조립체별 색으로 표시한 실제 UV 배치
  validation/validation.json   UV, 토폴로지, GLB, 재가져오기 검사 결과와 파일 해시
  validation/texture_binding_audit.json  외부/패킹/GLB 아틀라스 해시 및 픽셀 동일성
  source/imagegen_provenance.json        내장 image_gen에 전달한 전체 프롬프트
  source/build_bike.py                  형상부터 텍스처/내보내기까지 재생성 스크립트

형상
  REF/rabbit_bike.png를 참조한 정적 외형 모델이다.
  앞바퀴 2개와 큰 뒷바퀴 1개, 노출형 위시본 서스펜션, 주황색 댐퍼,
  토끼 귀 장식, 전면 라이트/센서, 분할 좌석, 측면 패널, 리어 스윙암과 후면 모듈을 포함한다.
  전체 폭 1.600 m, 길이 2.459 m, 귀를 포함한 높이 1.568 m.
  레퍼런스의 약 1m 높이는 차체의 대략적인 높이로 해석했다.
  20개 메시 조립체, 155,216개 삼각형, 12개 PBR 재질.
  Blender 좌표는 Z-up, 전면 -Y, 바닥 접지면 Z=0이다. GLB는 glTF 표준 Y-up으로 변환된다.
  .blend에는 부품별 이름을 가진 버텍스 그룹이 남아 있으며, 형상 수정은 원본/스크립트에서 할 수 있다.
  리깅과 바퀴/조향 애니메이션은 포함하지 않는다.

UV
  전체 모델이 고유한 0–1 UV 공간을 사용하며 좌우 면을 미러링하거나 겹쳐 놓지 않았다.
  타이어는 둘레/단면 길이를 따르는 전개, 얇은 곡면 커버는 분석적 전개를 적용했다.
  중앙 프레임과 일반 부품은 면 방향에 따라 전개한 뒤 전체 아일랜드의 면적 비율을 정리했다.
  목표는 약 512 px/m, 실제 4K 기준 면적 가중 중앙값은 약 501.30 px/m이다.
  표면적의 5–95백분위는 약 439.92–563.62 px/m이다. 곡면 투영과 작은 모서리에는 차이가 있다.
  실제 면 점유율 약 41.77%, 나머지는 패딩과 분리된 면 사이 공간이다.
  패킹 여백 설정 UV 0.002(8.192px), 베이크 확장 8px.
  이는 패커 설정이며 최소 실제 간격의 수학적 측정값은 아니다.
  4096px 내부 픽셀 검사에서 겹침 0, 범위 이탈 0, 면적 0 UV 삼각형 0을 확인했다.
  이 검사로 픽셀보다 작은 교차까지 배제할 수는 없으며 밉 단계별 패딩 검사는 별도로 하지 않았다.

텍스처와 재질
  내장 image_gen으로 새 아이보리 도장, 주황색 도장, 고무 텍스처를 각각 생성했다.
  실제 생성 원본은 각각 1254×1254 PNG이며 그대로 보존되어 있다.
  최종 RabbitBike_BaseColor_4096.png는 이 생성 이미지를 고유 UV에 적용한 4096×4096 베이크 결과다.
  아이보리/주황색 원본은 UV에서 4배, 고무/좌석 원본은 8배 반복 샘플링했다.
  고무/좌석은 과도한 입자 대비를 줄이기 위해 생성 색상 12%를 기본 재질색과 섞었다.
  조명 영향 없이 Emission 베이크하여 색상 아틀라스를 만들었고, 금속도/거칠기는 PBR 재질 값이다.
  타이어 트레드, 모서리, 패널과 기계 부품은 실제 형상이며 별도 노멀맵은 없다.

검증과 편집 참고
  조립체의 경계/비다양체 에지 0, 모든 GLB 프리미티브에 UV가 있다.
  하나의 최종 아틀라스가 GLB에 완전히 내장되어 있으며 외부 텍스처 경로가 필요하지 않다.
  외부 PNG, .blend 패킹 PNG, GLB PNG의 SHA-256과 실제 픽셀 일치 여부를 검사했다.
  20개 조립체와 치수를 유지한 GLB 재가져오기를 확인하고 실제 렌더를 검토했다.
  스튜디오 바닥/카메라/조명은 .blend에만 포함되어 있다.
  디테일 배치와 서스펜션/후면 모듈은 참조 이미지를 해석한 것으로 공학적 설계 도면은 아니다.

재생성 예시
  blender --background --factory-startup --threads 4 --python source/build_bike.py
  blender --background RabbitBike.blend --threads 4 --python source/validate_bike.py
  source/finalize_frame_uv.py는 저장된 파일의 중앙 프레임 UV를 다시 정리하고 베이크하는 보조 스크립트다.
  이미 패킹된 텍스처를 다시 베이크했다면 REMOVE 방식으로 언패킹한 뒤 외부 PNG를 reload/pack해야 한다.
  source/refresh_embedded_atlas.py와 audit_texture_binding.py가 그 갱신 및 바이트/픽셀 검사를 제공한다.

Git
  이전 SSTO 결과와 REF 제외 설정은 c312bb7에 커밋되어 있다.
  이번 바이크 결과는 Blender/RabbitBike 안에 별도로 저장했으며 자동으로 커밋하지 않았다.
