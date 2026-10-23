from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,re

BASE=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max');ROOT=BASE/'TextureImprovement';E=ROOT/'Evidence'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
start=datetime.fromisoformat('2026-10-23T14:00:36.464+00:00');kst=timezone(timedelta(hours=9))
publication=read(E/'publication_manifest.json');materials=read(E/'saved_material_validation.json');validation=read(E/'ue_validation.json')
for row in publication['files']:
    assert sha(Path(row['private_file']))==sha(Path(row['published_file']))==row['private_sha256']==row['published_sha256']
assert publication['all_published_hashes_equal_fresh_final_validation'] and materials['all_21_materials_have_compiled_shader_statistics']
attempts=[]
results={1:'CustomInput 생성자 API 오류로 중단; 종료 코드 0도 성공으로 해석하지 않음',2:'재질·FBX 갱신/첫 6장 캡처 완료, 로그 종료 뒤 비정상 종료',3:'식생 줄무늬 교체, 저장·재로드·최종 6장 캡처와 밉 검사 완료',4:'Custom HLSL 미집계 샘플 통계를 필수 조건으로 둔 검증식 중단; 자산 수정 없음',5:'새 세션 저장 맵·21개 컴파일 재질·60개 해시 검증 완료, 로그 종료 뒤 비정상 종료'}
for i in range(1,6):
    item=read(E/f'ue_timing_{i:02d}.json');item.update({'attempt':i,'result':results[i]});attempts.append(item)
source=[{'name':'UV 최초 구성/검사','evidence':'uv_rebuild_attempt01.json','seconds':read(E/'uv_rebuild_attempt01.json')['execution_seconds']},{'name':'돔 두께 cap 보정 후 최종 UV 구성/검사','evidence':'uv_rebuild.json','seconds':read(E/'uv_rebuild.json')['execution_seconds']},{'name':'실제 binary FBX 형상/방향/UV 재검증','evidence':'actual_fbx_validation.json','seconds':read(E/'actual_fbx_validation.json')['execution_seconds']},{'name':'실제 binary FBX 재질별 밀도/방향 신장 계측','evidence':'actual_fbx_density.json','seconds':read(E/'actual_fbx_density.json')['execution_seconds']}]
generation=read(ROOT/'ImageGen/generation_manifest.json')['assets']+[read(ROOT/'ImageGen/auxiliary_generation_manifest.json')]
call_sum=sum(x['elapsed_seconds'] for x in generation);active_wall=101.528+32.527
wait=sum(a['wait_seconds'] for a in attempts);run=sum(a['execution_seconds'] for a in attempts)
finished=datetime.now(timezone.utc);elapsed=(finished-start).total_seconds()
timing={'canonical_started_at_utc':start.isoformat(),'manual_started_at_utc':'2026-10-23T14:00:53.6105607+00:00','finished_at_utc':finished.isoformat(),'started_at_kst':start.astimezone(kst).isoformat(),'finished_at_kst':finished.astimezone(kst).isoformat(),'elapsed_wall_seconds':elapsed,'ue_wait_seconds_all_attempts':wait,'ue_execution_seconds_all_attempts':run,'ue_attempts':attempts,'imagegen_call_count':5,'imagegen_sum_of_call_seconds_overlapping':call_sum,'imagegen_active_wall_interval_seconds':active_wall,'imagegen_timing_note':'First four calls ran concurrently from14:02:44.078 to14:04:25.606 UTC (101.528s); auxiliary moss ran14:25:46.404 to14:26:18.931 UTC (32.527s). Sum of call durations is not elapsed wall time.','measured_source_commands':source,'measured_source_command_seconds':sum(s['seconds'] for s in source),'source_timing_note':'Measured script wall durations only. Design, script writing, image inspection, metadata authoring and review are included in total pass wall time, not fabricated as CPU execution duration. UE wait/run includes every attempted launch, including failures and shutdown anomalies.','ue_subtasks_not_additional_to_ue_total':{'primary_build_seconds':read(E/'build_summary.json')['build_seconds'],'auxiliary_build_seconds':read(E/'auxiliary_correction.json')['execution_seconds'],'fresh_material_validation_seconds':materials['validation_seconds']},'first_delivery_timings_preserved':True}
write(E/'timing_summary.json',timing)
rows='\n'.join(f"| {a['attempt']:02d} | {a['wait_seconds']:.3f} | {a['execution_seconds']:.3f} | {a['exit_code']} | {a['result']} |" for a in attempts)
density=read(E/'actual_fbx_density.json')['materials'];densityrows='\n'.join(f"| {d['material']} | {d['nominal_target_px_per_m']} | {d['measured_area_density_min']:.3f}–{d['measured_area_density_max']:.3f} | {d['max_anisotropy']:.3f} |" for d in density if d['sampling_path']=='connected_surface_uv')
imagerows='\n'.join(f"| {g['name']} | {g['elapsed_seconds']:.3f} | [원본](TextureImprovement/ImageGen/{g['name']}_albedo_original.png) |" for g in generation)
body=f'''

## 두 번째 텍스처 품질 패스 — 실제 결과와 전후 비교

삼각형마다 달라지던 텍스처 위상·방향을 연결 UV와 연속 월드 투영으로 교체했다. 청록 돔·석벽·암석·목재의 표면이 이어지고, 첫 개선 렌더에서 남았던 풀·잎의 규칙적인 줄무늬도 새 이끼 알베도로 교체했다. 감독자가 최종 실제 UE 이미지 6장을 확인했고, 소유 자산 게시까지 완료했다. 현재 상태는 독립 최종 검토를 위한 `ready_for_review`다. **형상·배치·조명·노출·기존 카메라는 유지했다.**

- 별도 패스 시작 UTC **`{start.isoformat()}`**, KST **`{start.astimezone(kst).isoformat()}`**: 감독자가 확인한 최초 turn_context 시각이다. 수동 첫 기록 `2026-10-23T14:00:53.6105607+00:00`은 별도 보존했다.
- 작성·게시 완료 UTC **`{finished.isoformat()}`**, KST **`{finished.astimezone(kst).isoformat()}`**. 이 패스 벽시계 **{elapsed:.3f}초**. 첫 전달의 시작·종료·소요 시간은 위 기록 및 불변 보관본에 그대로 남아 있다.
- 모든 UE 시도의 대기 **{wait:.7f}초**, 실행 **{run:.7f}초**. ImageGen 5회 개별 호출 시간 합계 **{call_sum:.3f}초**, 겹침을 제거한 실제 생성 구간 **{active_wall:.3f}초**. 계측된 원본/FBX 검사 명령 4개의 시간 합계 **{sum(s['seconds'] for s in source):.3f}초**. 이 수치를 전체 저작 CPU 시간으로 해석하지 않는다.
- 모델 `gpt-6-astra` / effort `max`, 로컬 `fast` 설정 유지. 요청별 실제 serving tier는 turn_context에 노출되지 않으므로 추정하지 않는다. [시작·실행 설정 검증](TextureImprovement/Evidence/parent_runtime_effort_verified.json), [전체 실제 시간](TextureImprovement/Evidence/timing_summary.json).

| UE 시도 | 대기 초 | 실행 초 | 종료 코드 | 실제 결과 |
|---|---:|---:|---:|---|
{rows}

두 번의 종료 코드 `-1073741819`는 정상 종료로 바꾸어 기록하지 않았다. 해당 세션은 검증/캡처 완료와 `Log file closed` 뒤에 비정상 종료했고 원인은 해결됐다고 주장하지 않는다. 최종 저장·캡처 세션 03은 코드 0이다. 세션 05에서 새로 로드한 최종 21개 재질은 실제 셰이더 명령 수와 샘플러를 가지며 재질 컴파일 경고가 0개였다. 03의 그래프 교체 중 `missing input N` 경고는 최종 저장 전의 중간 상태였고, 최종 저장 재질 검사에서 재현되지 않았다. Custom HLSL의 `Texture2DSample` 호출은 UE 추정 샘플 카운터에 집계되지 않아 세션 04의 검사식을 바로잡았다. [새 저장 재질 검증](TextureImprovement/Evidence/saved_material_validation.json), [종료 진단](TextureImprovement/Evidence/shutdown_diagnostics.json), [세션 03 원본 로그](TextureImprovement/Evidence/ue_phase03.log), [세션 05 원본 로그](TextureImprovement/Evidence/ue_phase05.log). 이 패스에서 전용 `Saved/Crashes`에 새 dump/context 파일은 생성되지 않았으며 원본 로그와 runner 종료 기록을 보존했다.

### UV와 실제 샘플 좌표 검증

실제 최종 FBX 17개의 vertex 배열과 polygon index 배열은 첫 전달본과 **완전히 같다**. 158,816삼각형, 2,446닫힌 양의 체적 성분, 기존 Y 반사 bake와 winding 보정, UE actor scale `(1,1,1)`을 유지했다. 맵 경계는 93.7985×91.0000m이며 높이도 기존 범위다. [실제 binary FBX 검증](TextureImprovement/Evidence/actual_fbx_validation.json), [독립 UV 검토](TextureImprovement/Evidence/independent_uv_review.json).

연결된 chart 15,917개에서 공유 edge **168,465개가 정확히 연속**, 의도된 chart 경계 **69,759개**, 예상하지 않은 불연속 **0개**다. 첫 전달본에서는 공유 edge 238,224개 모두 위상이 끊겼다. UV NaN/Inf·축퇴 삼각형·chart 내부 foldover는 0개다. chart별 nominal 8px padding을 둔 확장 경계가 서로 겹치지 않으며, 반복 텍스처를 사용하는 서로 떨어진 부품의 타일 재사용은 의도된 예외다. 고유 lightmap atlas를 주장하지 않는다.

돔은 외피·내피를 분리한 Lambert 등면적 반구 chart, 슬릿·바닥·꼭대기 두께는 별도 chart를 쓴다. 경도 특이점 없이 주 돔 면적 밀도는 실제 1024²/UV×2에서 **126.081–129.967px/m**, 최대 방향 신장비 **1.941**이다. 나무 부재는 부품 PCA 길이축을 V로 고정하고 옆면·단면을 분리했다. 독립 검사한 명확한 옆면 2,998개의 축 정렬 오차는 최대 `5.446619e-7` UV다. 다리 판재의 길이축은 통행 방향에 직각인 가로 방향이며 실제 렌더의 나뭇결이 이를 따른다.

아래는 **최종 FBX의 실제 좌표와 UV**, 실제 런타임 1024 해상도, 최종 재질 UV 배율로 계산한 재질별 면적 밀도다. 연결성을 보존하는 bevel·곡면 투영에서는 표면 방향에 따라 목표보다 낮은 밀도가 남는다. 이를 삼각형마다 재정규화하지 않고 방향별 신장과 함께 기록했다. [재질별 실제 밀도·방향 신장](TextureImprovement/Evidence/actual_fbx_density.json).

| UV 재질 | 목표 px/m | 실제 면적 밀도 px/m | 최대 방향 신장비 |
|---|---:|---:|---:|
{densityrows}

석재·암석·풀·잎 등 13종 재질은 UV 대신 월드 위치의 고정 XYZ 투영을 기하 노멀 가중치로 부드럽게 합성한다. 석벽/길은 축 기준 **128px/m·8m 반복**, 암석/식생은 **64px/m·16m 반복**이다. 경사 표면에서는 세 투영을 혼합하므로 한 장의 UV 면적 밀도와 동일하지 않다. 사용하지 않는 fallback UV에 RockBlue 겹침 **13쌍**(Beacon 8, Cottages 3, Garden 2)이 남아 있으며 실제 셰이더는 이를 샘플링하지 않는다. **UV로 샘플링하는 재질의 내부 겹침은 0쌍**이다. [실제 재질 샘플 경로·물리 스케일](TextureImprovement/Evidence/material_sampling_manifest.json), [13쌍 예외와 chart 검사 근거](TextureImprovement/Evidence/independent_uv_review.json).

### 생성 텍스처와 재질

독립 ImageGen 원본 5장은 요청한 1024가 아니라 실제 **1254×1254**로 반환됐다. 모든 선택 원본과 13개 import 소스는 생성 결과와 SHA256이 같으며 외부 이미지 편집·리사이즈를 하지 않았다. UE의 `ResizeToSpecificResolution` 빌드에서 1024×1024로 변환했다. 실제 사용 텍스처 21개 모두 **1024², 11단계 mip, sRGB 알베도, wrap 주소 방식**을 검증했다. [원본·용도·시간·전체 프롬프트 4종](TextureImprovement/ImageGen/generation_manifest.json), [추가 이끼의 전체 프롬프트](TextureImprovement/ImageGen/auxiliary_generation_manifest.json), [원본 해시·밉 실측](TextureImprovement/Evidence/texture_final_validation.json), [13개 표면 배정](TextureImprovement/Evidence/texture_source_manifest.json).

| 독립 생성 원본 | 실제 호출 초 | 원본 |
|---|---:|---|
{imagerows}

Teal은 RoofTeal/RoofLight, limestone은 Limestone/StoneDark/Path, rock은 RockBlue/RockPale, timber는 WoodLight/Timber, moss는 Grass/Moss/Leaf/LeafLight에 적용했다. 황동은 색 노이즈를 줄인 일정한 금속 색과 metallic 0.78, 거칠기 0.31–0.34를 사용한다. 금속·목재의 미세 노멀과 거칠기 차이는 알베도에서 유도한 예술적 보조 디테일이며 별도 실측 PBR 스캔 맵이 아니다. MikkTSpace tangent를 재계산하고 full precision UV를 유지했다. 타일 가능한 표면을 요청하고 실제 UE 반복 표면을 시각 검토했으나 맞은편 픽셀 경계가 수학적으로 완전히 같다고 주장하지 않는다.

### 동일 카메라 전후 증거

모두 실제 UE 5.7의 1920×1080 PNG, High(모든 sg 2), ScreenPercentage 100, Lit/Game View다. 원래 네 카메라의 위치·회전·투영·화각/ortho width가 첫 전달 manifest와 정확히 같고, 조명 9개·노출도 그대로다. Overview `(12000,-12000,16000)`cm→원점/ortho 20000cm, top down `(0,0,20000)`cm/pitch −90/yaw 0/roll 0/ortho 20000cm를 유지했다. 추가 상세 카메라 2개만 증거 수집용으로 넣었으며 렌더 형상을 추가하지 않았다. [캡처 manifest·UTC·해시](TextureImprovement/Screenshots/capture_manifest.json), [카메라/조명 동일성·캡처 자산 해시 연결](TextureImprovement/Evidence/capture_asset_identity.json).

| 시점 | 첫 전달본 보존 이미지 | 텍스처 개선 최종 이미지 |
|---|---|---|
| 전체 | ![첫 전체](FirstDelivery/Screenshots/overview.png) | ![개선 전체](TextureImprovement/Screenshots/overview.png) |
| 평면 | ![첫 평면](FirstDelivery/Screenshots/top_down.png) | ![개선 평면](TextureImprovement/Screenshots/top_down.png) |
| 천문대 | ![첫 천문대](FirstDelivery/Screenshots/observatory.png) | ![개선 천문대](TextureImprovement/Screenshots/observatory.png) |
| 다리 | ![첫 다리](FirstDelivery/Screenshots/bridge.png) | ![개선 다리](TextureImprovement/Screenshots/bridge.png) |

![청록 돔·황동·석재 실제 상세](TextureImprovement/Screenshots/material_dome.png)

![목재 방향·연결·식생 실제 상세](TextureImprovement/Screenshots/material_bridge.png)

식생 보정 전의 첫 개선 렌더 6장도 [InitialTextureRender manifest](TextureImprovement/Evidence/InitialTextureRender/capture_manifest.json)에 별도 보존했다. 모든 장면 증거는 실제 UE 출력이며 생성 이미지나 후처리 이미지로 교체하지 않았다.

### 저장·게시·보존과 남는 한계

최종 구성은 메시 **17**, 재질 **21**, 텍스처 **21**, 맵 포함 **60패키지**로 동일하다. 13개 텍스처를 교체하고 8개 기존 텍스처는 그대로 유지했다. 게시된 파일 중 첫 전달과 bytes가 바뀐 것은 **52개**(17메시+21재질+13텍스처+맵)다. 새 UE 세션의 저장 맵 재로드에서 재귀 `/Game` 그래프 60패키지와 배치 메시/재질/텍스처 59개 전체를 대조했다. 범위 밖 의존성·누락 재질 0, World Partition 없음, 동적 Movable 조명 9개, 외부 actor/object/BuiltData 없음. [저장 맵 검증](TextureImprovement/Evidence/ue_validation.json).

전용 UE가 종료된 상태에서 `Content/SkyObservatory/max/**`와 `Content/Maps/SkyObservatory_max.umap`만 게시했다. 모든 private/published SHA256은 새 저장 재질 검사 시점과 같고, 모든 자산 저장 시각은 최종 캡처보다 앞선다. 게시 전 공유 경로의 60개 파일은 첫 전달 커밋과 같았다. [파일별 게시·캡처 자산 해시](TextureImprovement/Evidence/publication_manifest.json). 원본은 `TextureImprovement/SourceArt/SkyObservatory_TextureImprovement.blend`, `SourceArt/Meshes/*.fbx`, `SourceArt/Textures/*.png`에 있다.

첫 전달의 Work 보관 102개, Content 보관 60개 및 원래 활성 Source/SourceArt/Evidence/Screenshots 100개 파일은 모두 불변 해시를 확인했다. 변경을 허용한 활성 문서는 이 `RESULT.md`와 `STATUS.json`뿐이다. [첫 전달 보존 대조](TextureImprovement/Evidence/first_delivery_preservation.json), [기존 비교 기록의 감독자 보존 증거](TextureImprovement/Evidence/parent_comparison_preservation_before.json). 다른 theme/effort의 창작 자료·보고서·scratch는 읽거나 재사용하지 않았으며 Git 작업은 하지 않았다.

월드 투영은 이 정적 환경에 맞춰 세계 좌표에 고정되어 있다. 향후 물체를 움직이면 텍스처가 표면에 붙어 이동하는 방식은 아니다. 곡면/부품 경계의 의미 있는 seam, 원래 모델의 암석 면 분할, 앞서 기록한 사용하지 않는 fallback UV 겹침 예외는 남는다. 구름·별은 정적 예술적 표현이고 기상/천문/내부 생활/게임플레이/물리 시뮬레이션이 아니다. 에디터 실제 렌더와 저장 자산을 검증했으며 패키지 빌드·PIE·FPS 보장은 주장하지 않는다. 종료 뒤 비정상 코드 원인도 해결을 주장하지 않고 근거를 보존했다. 이 유한 텍스처 품질 패스의 저작을 종료하고 최종 독립 검토를 기다린다.
'''
report=BASE/'RESULT.md';text=report.read_text(encoding='utf-8');marker='## 두 번째 텍스처 품질 패스 — 설계와 구현 계획';head,plan=text.split(marker,1)
plan=plan.split('## 두 번째 텍스처 품질 패스 — 실제 결과와 전후 비교')[0]
plan=plan.replace('- [ ]','- [x]').replace('별도 시작 UTC는 `2026-10-23T14:00:53.6105607+00:00`이다.','검증된 별도 시작 UTC는 `2026-10-23T14:00:36.464Z`이며 첫 수동 상태 기록 `2026-10-23T14:00:53.6105607+00:00`은 별도 보존한다.')
lead='# SkyObservatory/max — 두 번째 텍스처 품질 패스 전달\n\n현재 전달본은 텍스처 개선과 실제 UE 재검증·게시를 완료한 버전이다. 이 문서 앞부분의 첫 전달 이력은 보존했으며, 아래 「두 번째 텍스처 품질 패스 — 실제 결과와 전후 비교」에 현재 결과·시간·이미지를 기록했다. 독립 최종 검토 대기 상태다.\n\n---\n\n'
if not head.startswith('# SkyObservatory/max — 두 번째 텍스처 품질 패스 전달'):head=lead+head
report.write_text(head+marker+plan+body,encoding='utf-8')
summary={'saved_map_reloaded':True,'world_partition':None,'recursive_game_packages':60,'placed_required_assets':59,'missing_or_forbidden_dependencies':0,'published_files':60,'changed_package_bytes':52,'all_private_published_captured_asset_sha256_match':True,'actual_ue_screenshots':6,'imagegen_originals':5,'imagegen_changed_texture_assets':13,'runtime_textures_1024_with_11_mips':21,'compiled_final_material_resources':21,'mesh_geometry_and_winding_exactly_equal_baseline':True,'triangles':158816,'closed_components':2446,'connected_uv_charts':15917,'exactly_continuous_shared_edges':168465,'declared_chart_boundary_edges':69759,'unexpected_shared_edge_discontinuities':0,'uv_driven_overlap_pairs':0,'unused_world_projected_rockblue_fallback_overlap_pairs':13,'original_cameras_lights_exposure_unchanged':True,'final_capture_ue_exit_code':0,'fresh_final_validator_proof_completed':True,'post_log_shutdown_nonzero_attempts':[2,5],'actor_scale':[1,1,1]}
status=read(ROOT/'STATUS.json');status.update({'status':'ready_for_review','started_at_utc':start.isoformat(),'started_at_kst':start.astimezone(kst).isoformat(),'finished_at_utc':finished.isoformat(),'finished_at_kst':finished.astimezone(kst).isoformat(),'elapsed_seconds':elapsed,'ue_wait_seconds_all_attempts':wait,'ue_execution_seconds_all_attempts':run,'imagegen_sum_of_call_seconds_overlapping':call_sum,'imagegen_active_wall_interval_seconds':active_wall,'validation_summary':summary,'blockers':[],'known_limitations':['Two UE sessions returned access-violation exit code after Log file closed; cause unresolved. Final capture session exited0 and fresh saved-asset validation completed with unchanged hashes.','13 unused RockBlue fallback UV overlap pairs; actual material samples continuous world projection.','Static artistic clouds/environment; no gameplay/PIE/FPS claims.'],'evidence':'Evidence/publication_manifest.json'})
write(ROOT/'STATUS.json',status)
root=read(BASE/'STATUS.json');root.setdefault('first_delivery_validation_summary',root['validation_summary']);root['status']='ready_for_review';root['active_phase']='texture_improvement';root['texture_improvement']=status;root['validation_summary']=summary;root['blockers']=[];write(BASE/'STATUS.json',root)
# Validate the final active report links and publication after the record is written.
links=re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8'))
for link in links:
    if link.startswith(('http:','https:','#')):continue
    path=(BASE/link).resolve();assert str(path).startswith(str(BASE.resolve())) and path.exists(),link
for row in publication['files']:assert sha(Path(row['published_file']))==row['published_sha256']
assert read(ROOT/'STATUS.json')['finished_at_utc']==read(BASE/'STATUS.json')['texture_improvement']['finished_at_utc']
print('FINAL_RECORD_PASS',finished.isoformat(),'wall',elapsed,'wait',wait,'run',run,'report_links',len(links),'published',len(publication['files']))
