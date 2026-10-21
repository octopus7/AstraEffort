# ForestDemo 작업 결과 비교 · 수행 시간 · 스크린샷

최종 결과를 모으는 단일 보고서입니다. 현재 네 작업은 제작 중이며, 아래 비교와
실제 UE 스크린샷은 결과 검증 후 채웁니다. 제작 중에는 순위나 우열을 판정하지 않습니다.

Supervisor setup started: 2026-10-21 21:09:14 KST (12:09:14 UTC).
Baseline: `7558c8f`. Four user-owned local chats, same configured default model,
with reasoning efforts medium, high, xhigh, ultra.

## Shared assignment

Independently build a 100 x 100 metre playable forest scene for UE 5.7, containing
a small lake, a distinct beach and suitable original props. Use softly rounded
forms and a restrained, calm game palette. Avoid cloud-shaped ornamentation,
faces, hearts, or similar decorative motifs. Natural atmospheric clouds are not
required. Scene design and prop construction are each worker's responsibility;
do not reuse another effort's work. Deliver a composed scene, not just a script.
Use UE centimetres (10,000 x 10,000 cm site), usable lighting, a player start,
appropriate ground collisions, and an intentional overview camera/viewpoint.
Preserve the baseline ScreenDebugLogger behavior in each map where practical.

## Isolation and integration

- Assets: `ForestDemo/Content/Forest/<effort>/**`.
- Map: `ForestDemo/Content/Maps/<effort>.umap`.
- Scripts, source artwork, evidence, result: `ForestDemo/Work/<effort>/**`.
- Private authoring project: `ForestDemo/Saved/Workers/<effort>/**` (ignored).
- Workers do not commit. Supervisor validates and commits each delivery separately.
- Keep baseline main during work. Once all four maps pass integration checks,
  supervisor retires main and selects medium as startup/default map in a separate
  integration commit, leaving exactly four scene maps.
- Do not change the selected effort or use subagents to create the scene; the
  comparison concerns each chat's own reasoning effort. No arbitrary time cap.

## Timing definitions

Dispatch time is when the supervisor requests chat creation. Worker active wall
time is actual worker start through its ready-for-review timestamp; it includes
tool waiting but excludes later supervisor review and commit time. Supervisor
also records dispatch-to-ready duration and commit time separately where available.
Missing timestamps remain unknown rather than estimated from a polling interval.

## Progress

| Effort | Chat | Dispatch (KST) | Worker start | Ready | Wall time | Status | Commit |
|---|---|---|---|---|---|---|---|
| medium | 01a15e5f-d4b8-7e53-b162-d84c019c5478 | 2026-10-21 21:11:37 | 2026-10-21 21:11:50 | pending | pending | working | pending |
| high | 01a15e5f-e4c8-7bc1-b8da-c01f6d6d175c | 2026-10-21 21:11:42 | 2026-10-21 21:11:54 | pending | pending | working | pending |
| xhigh | 01a15e5f-f174-72d3-bc4b-f9f812ebf7db | 2026-10-21 21:11:46 | 2026-10-21 21:11:57 | pending | pending | working | pending |
| ultra | 01a15e5f-fef9-7323-8733-3c0553c29d7e | 2026-10-21 21:11:49 | 2026-10-21 21:12:01 | pending | pending | working | pending |

## Supervisor log

- Prepared isolated ownership rules, per-worker delivery boundaries, and central
  commit control. Automatic follow-up will inspect progress and stay quiet unless
  completion, failure, a meaningful change, or a user decision needs attention.

- All four chats confirmed active. Supervisor heartbeat: forestdemo, every 5 minutes.
- 2026-10-21 21:19:35 KST: 사용자 요청으로 에셋 경로를
  `Content/Forest/<effort>/` (`/Game/Forest/<effort>/`)로 변경했습니다.
  레벨은 `Content/Maps/<effort>.umap`에 유지합니다. 제작 대화가 자기 scratch에서
  패키지 경로와 참조를 갱신하고 재검증하며, 이 변경에 든 시간은 별도 기록합니다.

## 공통 캡처 기준

작업별 실제 UE 화면을 1920×1080 PNG로 캡처합니다. 에디터 선택선, 그리드,
기즈모, 콘솔, UI, 디버그 문구를 숨깁니다. 가능한 공통 설정은 High 품질과
screen percentage 100이며, 실제 사용 설정과 차이는 capture_manifest.json에 기록합니다.
이미지 생성 도구의 대체 이미지나 시각적 보정은 비교 증거로 사용하지 않습니다.

자기 100×100m 사이트의 중심을 (Cx,Cy), 지면 기준 높이를 Z0로 정의합니다.

| 파일 | 카메라 기준 | 비교 목적 |
|---|---|---|
| overview.png | 위치 (Cx+12000,Cy-12000,Z0+16000), 중심 지면 주시, 직교 폭 20000cm | 같은 규모·시점에서 전체 아트와 공간 구성 비교 |
| top_down.png | 위치 (Cx,Cy,Z0+20000), 회전 pitch -90/yaw 0/roll 0, 직교 폭 20000cm | 100×100m 영역과 숲·호수·해변 배치 비교 |
| lake.png | 지면에서 약 170cm, 수평 FOV 70°, 호수별 적절한 지점 | 호수 물가·식생·프랍의 실제 디테일 |
| beach.png | 지면에서 약 170cm, 수평 FOV 70°, 해변별 적절한 지점 | 해변 모래·물·바위와 동선의 실제 디테일 |

조명과 재질은 각 작업이 완성한 아트를 유지합니다. 근접 캡처 두 장의 위치는
작업별로 다르므로 구도까지 동일한 비교는 아닙니다. 카메라/렌더 설정 차이와
캡처 실패가 있으면 명시하며, 검정 화면이나 미완성 셰이더 화면은 완료로 처리하지 않습니다.
원본 위치: `Work/<effort>/Screenshots/`. 완료 후 이 문서에 실제 이미지들을 직접
삽입하여 같은 시점의 네 작업을 나란히 볼 수 있도록 구성합니다.

## 결과 비교

관찰 가능한 차이를 근거로 작성하며, 아직 측정하지 않은 FPS·메모리·폴리곤 수나
검증하지 않은 기능은 추정하지 않습니다. 작업당 한 번의 제작 결과이므로 결과 차이를
추론 강도만의 인과 효과로 단정하지 않습니다. 감독 수정·도구 오류·추가 캡처 시간도
함께 보고하여 제작 시간과 최종 품질을 해석할 수 있게 합니다.

| 비교 항목 | medium | high | xhigh | ultra |
|---|---|---|---|---|
| 100×100m 범위 및 요구 충족 | 제작 중 | 제작 중 | 제작 중 | 제작 중 |
| 숲의 공간감·지형·동선 | 미평가 | 미평가 | 미평가 | 미평가 |
| 호수와 해변의 구분·연결 | 미평가 | 미평가 | 미평가 | 미평가 |
| 프랍의 완성도·다양성·배치 | 미평가 | 미평가 | 미평가 | 미평가 |
| 둥근 형태·차분한 색감의 일관성 | 미평가 | 미평가 | 미평가 | 미평가 |
| 플레이 시작·충돌·이동 가능성 | 미검증 | 미검증 | 미검증 | 미검증 |
| 에셋 의존성·경로 격리 | 미검증 | 미검증 | 미검증 | 미검증 |
| 제작 구조·재현성·후속 수정 용이성 | 미평가 | 미평가 | 미평가 | 미평가 |
| 실제 수행 시간·검증·제약 | 집계 중 | 집계 중 | 집계 중 | 집계 중 |

## 스크린샷 비교

전체 사선 조감, 수직 조감, 호수, 해변 순서로 네 작업을 비교합니다.
실제 완료한 캡처만 여기에 삽입합니다. 현재 캡처 대기 중입니다.

## 작업별 분석과 최종 판단

각 작업의 강점, 미흡한 점, 구체적인 화면 근거, 적합한 활용과 개선 우선순위를
감독자가 원본 이미지를 직접 확인한 뒤 작성합니다. 마지막에 시간 대비 완성도와
공통 개선점을 정리합니다. 현재 결과 분석 대기 중입니다.
