# Rounded model set production plan

> **For agentic workers:** Use the established subagent-driven execution, with one Astra/max worker per set. The user's explicit instruction defers visual inspection and independent validation; do not add reviewer agents or review gates.

**Goal:** Produce Set03 through Set11: nine ordinary mesh sets, four original assets each, in three consecutive groups of three sets. Commit after each group.

**Latest user extension (2026-10-25 KST):** After the original nine sets, main selects further sets and continues until the user says to stop. Preserve the same workflow: three Astra/max set workers per group, four models per set, main-only sequential image generation, local REF mirrors, deferred review, and one commit after each completed group. The original nine-set milestone is not a stopping condition. Append subsequent groups before starting their references. Do not push.

**Architecture:** Main generates one reference image per asset sequentially and saves it under REF/SetNN. A worker begins modeling its four assets after its four references are ready. Three set workers run independently in parallel; main owns coordination and Git. All output remains separate from the completed voxel library and Set01/Set02.

Latest user addition: also copy every reference image, prompt and generation record into `Blender/SetNN/REF/`, keeping the original `REF/SetNN/`. Apply this to Set01/02 as well. Main owns the mirrors; workers read them but do not overwrite them.

**Tech Stack:** Built-in image_gen for references; isolated Blender 4.5.12 background processes, Python/bpy, four CPU threads per worker. Editable BLEND, geometry-only GLB/FBX, actual hero/rear PNG renders.

**Spec:** The user's instructions in this conversation: rounded functional game art, three Astra/max workers, main-only sequential image generation, defer review, continue three groups (nine sets), commit after each completed group. Model and effort are configurable; a separate Fast flag is unavailable in the agent API.

## Global constraints

- Ordinary rounded mesh assets, not voxels. No large/half variants are requested for these sets.
- Friendly softened silhouettes and edges; retain recognizable functional structure. No heart, smiley, cloud, face or childish ornamental motifs.
- Each set contains two machines/vehicles and two buildings/facilities. No people, logos or lettering are required.
- One worker owns only Blender/SetNN. Its creative references are only REF/SetNN. No other set/voxel/ForestDemo creative source reads or reuse.
- No shared live Blender scene, package installations, worker Git operations or extra subagents.
- Named PBR palette materials and sensible per-component UVs; no generated surface texture task, rigging, animation, collision or LOD task.
- Produce actual renders for later review, but do not inspect them or run fresh reopen/import, geometry, UV or visual validation. Record review_status=deferred_by_user. Only process completion and expected nonempty file presence are checked before committing.
- Keep all existing individual outputs. Exclude caches, Blender backups and duplicate ZIP files from Git. Never stage unrelated work.

## Group 1: approved proposals

| Set | Theme | Assets (slug — label) |
|---|---|---|
| Set03 | Urban maintenance | street_sweeper — 소형 노면청소차; pipe_inspection_robot — 다관절 배관점검 로봇; road_maintenance_depot — 도로 관리 차고; compact_pump_station — 소형 펌프장 |
| Set04 | Aerial logistics | twin_rotor_cargo_drone — 쌍로터 화물 드론; airport_cargo_tug — 공항 화물 견인차; circular_drone_hangar — 원형 드론 격납고; low_control_building — 저층 관제동 |
| Set05 | Marine work | catamaran_workboat — 쌍동형 작업선; underwater_service_robot — 수중 정비 로봇; docking_lift_platform — 접안용 승강 도크; marine_equipment_workshop — 해양장비 정비소 |

## Groups 2 and 3: main-selected continuation

The following selections are the main's decisions under the user's explicit permission to select the subsequent sets. Start each group only after the previous group's commit.

| Set | Theme | Assets (slug — label) |
|---|---|---|
| Set06 | Forestry care | tree_transplanter — 관절식 수목 이식차; nursery_carrier_robot — 종묘 운반 로봇; arched_nursery_greenhouse — 아치형 육묘 온실; forest_watchtower — 원형 산불 감시탑 |
| Set07 | Rail freight | rail_inspection_trolley — 레일 점검 소형차; side_loading_freight_shuttle — 측면 적재 화물 셔틀; barrel_roof_freight_station — 배럴 지붕 화물역; mechanical_signal_house — 기계식 신호소 |
| Set08 | Materials processing | articulated_welding_mech — 소형 관절형 용접 메카; cylindrical_mixer — 원통형 혼합기; rounded_foundry_workshop — 곡면 지붕 주조 작업장; vertical_material_tower — 수직 자재 저장탑 |
| Set09 | Alpine transport | tracked_snowplow — 궤도형 제설차; freight_cable_car — 소형 화물 케이블카; cable_drive_station — 케이블카 구동실; modular_mountain_shelter — 모듈형 산악 대피소 |
| Set10 | Coastal energy | turbine_service_crawler — 터빈 정비 크롤러; generator_transport_trailer — 발전기 운반 트레일러; tidal_power_module — 소형 조력 발전 모듈; circular_power_control_house — 원형 전력 제어동 |
| Set11 | Food production and delivery | mobile_grain_mill — 이동식 곡물 분쇄차; refrigerated_delivery_robot — 저상 냉장 배송 로봇; curved_roof_flour_mill — 곡면 지붕 제분소; modular_cold_store — 모듈형 저온 저장고 |

## Deliverable interface

For each asset: `Blender/SetNN/SLUG/SLUG.blend`, `.glb`, `.fbx`, `renders/hero.png`, `renders/rear.png`, `metadata.json`. A set-level `build.py` or per-asset source scripts must reproduce the authored geometry and output. Native BLEND keeps ASSET and STUDIO collections separate; GLB/FBX contain asset geometry only.

Each worker supplies `STATUS.json`, concise `RESULT.md`, `delivery_manifest.json` with exact output paths/sizes/hashes and review deferred, plus source, build logs, actual UTC/KST start/end and measured process durations. Use status `produced_unreviewed`, not `validated` or `ready_for_review` with implied success. Main produces the group catalog and commit.

## Execution

- [x] Group 1: generate 12 references in sequence; dispatch Set03/04/05 as each complete set of four references becomes ready; collect the four assets per worker; record deferred review; commit the group.
- [x] Group 2: announce selected Set06/07/08 themes; repeat the sequential-reference and three-worker workflow; commit the group.
- [ ] Group 3: announce selected Set09/10/11 themes; repeat the workflow; commit the group.
- [ ] Record all three commits and the 36-asset output inventory, with review still deferred.

## Deferred review focus

Future review should inspect reference fidelity, silhouette/functional clarity, mesh/material/UV quality, export roundtrips and complete render framing. Those checks are deliberately deferred by the user's latest instruction. Generation failures and missing deliverable files still require correction so the requested assets actually exist.
