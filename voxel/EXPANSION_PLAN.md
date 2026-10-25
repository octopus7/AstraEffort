# Voxel expansion implementation plan

**Goal:** Add six useful models to six existing themes, finish and validate those, then create the approved nine additional themes (36 models). Final catalog: 18 themes, 81 models, 162 large/half variants.

**Architecture:** Preserve all 39 accepted original models and their original archive. Additions have isolated roots `voxel/THEME/additions`, so original capture/validation records remain intact. New themes use `voxel/THEME`. Main alone generates and saves reference sheets sequentially in REF/voxel. Three existing gpt-6-astra/max workers author isolated theme geometry; main authors desert/water_purifier and the final bakery theme. Fast remains unavailable as a separate agent API setting.

**Tech stack / spec:** Existing BRIEF.md and _tools/API.md, voxelkit.py, blender_pipeline.py and verify_theme.py. Native VOX 150, BLEND/GLB/FBX exports, actual same-camera 768px renders. Large longest axis128, every large axis even; half every axis divided by2 with doubled cell size and unchanged physical grid extents. Opaque palette colors, no rig/animation/collision/engine integration.

## Selection

Six additions add distinct gameplay functions and silhouettes: farm/combine_harvester (harvesting), factory/robot_workcell (articulated assembly), antarctic/ice_core_drill (sample extraction), harbor/repair_dock (boat maintenance structure), mine/haul_truck (large bulk transport), desert/water_purifier (treatment rather than storage). Mountain railway, spaceport and underwater already have five complementary models; no forced additions there. These are builder selections under the user's explicit discretion.

## Authorized sequence

- [x] Main generates six additional model references, sequentially, preserving prompts/original outputs.
- [x] Worker1: farm addition, then harbor addition. Worker2: factory addition, then mine addition. Worker3: antarctic addition. Main: desert addition after all six reference images are ready.
- [x] Main independently reparses/reimports all 12 added variants, inspects all primary previews, freezes hashes and accepts phase A. Existing 39 models remain unchanged.
- [x] Only after phase A acceptance, main generates nine new theme reference sheets sequentially. Dispatch each ready first theme immediately; later assigned themes wait for their references and predecessor acceptance.
- [ ] Worker1: forestry -> airfield -> canal. Worker2: construction -> recycling -> camping. Worker3: fire_rescue -> geothermal. Main: bakery after all nine references are ready.
- [ ] Main independently validates and visually reviews every new large/half pair. Workers inspect actual previews before submission and fix demonstrated defects only.
- [ ] Assemble the expanded 18-theme comparison gallery, README, manifest and a new verified ZIP; preserve original nine-theme ZIP and model hashes.

## New themes and exact assets

| Theme | Assets |
|---|---|
| forestry / 산림·제재소 | logging_harvester, timber_forwarder, sawmill, log_rack |
| construction / 건설 현장 | concrete_mixer, wheel_loader, tower_crane, site_office |
| fire_rescue / 소방·구조 기지 | fire_engine, rescue_robot, fire_station, rescue_helicopter |
| airfield / 소형 비행장 | propeller_plane, airport_tug, maintenance_hangar, control_tower |
| recycling / 재활용 센터 | collection_truck, sorting_machine, compactor, recycling_center |
| geothermal / 화산·지열 기지 | thermal_rover, geothermal_drill, cooling_tower, volcano_observatory |
| canal / 운하·수문 마을 | canal_boat, lock_gate, drawbridge, lockkeepers_house |
| camping / 캠핑·휴양지 | camper_van, log_cabin, generator_trailer, shower_block |
| bakery / 제과·제빵 마을 | bakery_shop, dough_mixer, bread_oven, delivery_van |

## Ownership and review

Workers may write only their currently assigned root; own-theme old palette/reference can be consulted for continuity, but existing accepted assets may not be modified. No cross-theme creative reads, ForestDemo access, Git operations, installations or shared live Blender scene. Isolated Blender background processes only, four CPU threads maximum each. Record actual UTC/KST and process timing; generated references are never render evidence. Final reviewer verifies native occupancy, real grid reduction, palette indices, outward exposed surfaces, all three fresh mesh imports, file hashes, visible functional openings/mechanisms and completeness. No repeated speculative polish cycles.

## Progress checkpoint

User requested a commit of current progress. 61 models are parent-accepted; airfield/recycling (8) await parent review; geothermal (4) is exported but unverified WIP; canal/camping (8) are unstarted. All nine reference sheets are ready. Workers are frozen. See RESUME.md and CHECKPOINT.json; final assembly remains pending.
