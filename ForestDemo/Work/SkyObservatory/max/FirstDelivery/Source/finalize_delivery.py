from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,shutil
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max');E=ROOT/'Evidence';S=ROOT/'Screenshots'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
pub=read(E/'publication_manifest.json');valid=read(E/'ue_validation.json');audit=read(E/'persisted_source_audit.json');source=read(E/'source_validation.json');caps=read(S/'capture_manifest.json')
assert pub['own_private_editor_closed'] and pub['file_count']==60 and pub['all_sha256_match']
for item in pub['files']:
 assert hashlib.sha256(Path(item['published_file']).read_bytes()).hexdigest()==item['private_sha256']==item['published_sha256']
assert set(c['name'] for c in caps['captures'])=={'overview','top_down','observatory','bridge'}
for cap in caps['captures']:
 data=(S/cap['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==cap['sha256'];assert int.from_bytes(data[16:20],'big')==1920 and int.from_bytes(data[20:24],'big')==1080
 assert cap['actual_view_mode']=='VMI_LIT' and cap['actual_game_view']
assert valid['graph_packages']==60 and len(valid['placed_required_packages'])==59 and not valid['required_missing_from_graph']
assert all(g['uv_rectangle_overlap_pairs']==0 and g['inconsistent_or_open_edges']==0 and g['uv_finite'] for g in audit['groups'])
assert all(m['scale']==[1.0,1.0,1.0] and m['max_axis_bounds_error_cm']<.1 and m['full_precision_uvs'] for m in valid['placed_meshes'])
assert all(g['nonmanifold_or_inconsistent_edges']==0 for g in source['groups'])
timings=[read(p) for p in sorted(E.glob('ue_timing_*.json'))];assert len(timings)==5
source_commands=[{'command':'Blender initial build (normal-validation failure)','observed_command_wall_seconds':4.4740841},{'command':'Blender winding correction build','observed_command_wall_seconds':7.3439584},{'command':'Blender UV shelf-packing build','observed_command_wall_seconds':8.6950788},{'command':'Persisted source audit before correction','observed_command_wall_seconds':8.418116},{'command':'Targeted cloud geometry and export-axis correction','observed_command_wall_seconds':4.1104765},{'command':'Persisted source audit final','observed_command_wall_seconds':8.2939954}]
logs=E/'UnrealLogs';logs.mkdir(exist_ok=True)
for t in timings:
 p=Path(t['log'])
 if p.exists():shutil.copy2(p,logs/p.name)
for name in ['build_error.json','validation_error.json']:
 p=E/name
 if p.exists():p.unlink() # timestamped attempt evidence is preserved separately.
backup=ROOT/'SourceArt/SkyObservatory_Master.blend1'
if backup.exists():shutil.move(str(backup),str(E/'BeforeCorrection/SkyObservatory_Master_before_cloud_correction.blend'))
started=datetime.fromisoformat('2026-10-23T12:04:38.840+00:00');finished=datetime.now(timezone.utc);kst=timezone(timedelta(hours=9));elapsed=(finished-started).total_seconds()
wait=sum(t['wait_seconds'] for t in timings);run=sum(t['execution_seconds'] for t in timings);source_wall=sum(t['observed_command_wall_seconds'] for t in source_commands)
summary={'started_at_utc':started.isoformat(),'finished_at_utc':finished.isoformat(),'elapsed_wall_seconds':elapsed,'ue_wait_seconds_all_attempts':wait,'ue_execution_seconds_all_attempts':run,'source_commands':source_commands,'source_observed_command_wall_seconds':source_wall,'source_last_full_build_internal_seconds':source['source_generation_seconds'],'imagegen_seconds':0,'imagegen_used':False,'timing_note':'Source command durations are actual tool-observed wall time, including process/shell overhead; source authoring and review are included in total wall time, not inferred as CPU work. UE timing includes all five attempts including guard failure and Python failures.'}
(E/'timing_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
notes=['프로세스 가드의 sandbox 조회 거부; UE 실행 없음','재질 Multiply 속성 접근 오류; 종료코드 0이어도 제작 성공 아님','맵 저장 후 편집기 카메라 프록시 검사 오탐; 종료코드 0이어도 검증 성공 아님','첫 실제 4장 캡처; 축·조명 보정 필요','축을 FBX에 bake하고 면 방향·조명·구름 보정, 최종 재검증·4장 캡처 성공']
rows='\n'.join(f"| {i+1} | {t['wait_seconds']:.3f} | {t['execution_seconds']:.3f} | {t['exit_code']} | {notes[i]} |" for i,t in enumerate(timings))
mins=min(g['density_min_px_per_m'] for g in audit['groups']);maxs=max(g['density_max_px_per_m'] for g in audit['groups']);axis=max(m['max_axis_bounds_error_cm'] for m in valid['placed_meshes']);tri=sum(g['triangles'] for g in source['groups']);components=sum(g['closed_components'] for g in source['groups'])
prefix=(ROOT/'RESULT.md').read_text(encoding='utf-8').split('## 작업 기록')[0].replace('- [ ]','- [x]')
prefix=prefix.replace('그림','그림')
body=f'''## 작업 기록과 실제 결과

- 상태: `ready_for_review` — 감독자 최종 검토 및 통합 대기. 작업자는 Git 변경·커밋·푸시를 하지 않았다.
- 시작 UTC: `{started.isoformat()}` / KST: `{started.astimezone(kst).isoformat()}`. 감독자가 확인한 실제 최초 turn 시각이다.
- 최초 수동 상태 기록: `2026-10-23T12:05:03.8566664+00:00`; 최초 시작으로 소급 대체하지 않고 별도 보존한다.
- 완료 UTC: `{finished.isoformat()}` / KST: `{finished.astimezone(kst).isoformat()}`.
- 총 벽시계: **{elapsed:.3f}초**, 모든 UE 큐 대기 **{wait:.3f}초**, 모든 UE 실행 **{run:.3f}초**. 큐 분류는 변경하지 않은 공용 runner의 `Unknown`, 우선순위 2/FIFO이며 기존 우선순위 작업을 선점하지 않았다.
- 원본 생성·검사 명령의 실제 관측 벽시계 합계 **{source_wall:.3f}초**. 셸/프로세스 시작을 포함하며 설계·스크립트 작성·검토 시간은 총 벽시계에 포함된다. 최종 전체 원본 생성 내부 계측 {source['source_generation_seconds']:.3f}초; 타깃 수정과 재검사는 별도 명령으로 기록했다. ImageGen 사용 및 시간 **0초**.
- 스레드: `01a168a6-1456-7803-8dc6-c6409596987c`. 실제 turn의 `gpt-6-astra` / `max` 확인. 로컬 `fast` 설정과 도구의 `priority` 지원은 확인되지만 turn 기록에는 요청별 실제 serving tier가 노출되지 않는다. [모델·effort 검증 근거](Evidence/runtime_effort_verified.json).

| UE 시도 | 대기 초 | 실행 초 | 종료 코드 | 실제 결과 |
|---|---:|---:|---:|---|
{rows}

[전체 계측](Evidence/timing_summary.json), [UE 원본 로그](Evidence/UnrealLogs/phase05.log). 초기 축·조명 상태의 실제 렌더 4장과 매니페스트는 [BeforeCorrection](Evidence/BeforeCorrection/capture_manifest.json)에 보존했다. 최초 원본의 캡 winding 오류는 성분별 인접 면 방향 전파와 양의 체적으로 수정했고, UV를 좁은 선반에 패킹해 float32 밀도 편차를 줄였다.

## 전달 경로와 장면 구성

- 최종 맵: `ForestDemo/Content/Maps/SkyObservatory_max.umap` (`/Game/Maps/SkyObservatory_max`).
- 최종 자산: `ForestDemo/Content/SkyObservatory/max/` 아래 메시 17개, 재질 21개, 텍스처 21개. 맵 포함 **60개 파일**이며 [게시 파일별 SHA256](Evidence/publication_manifest.json)의 private/published 해시가 전부 일치한다.
- 원본: `SourceArt/SkyObservatory_Master.blend`, `SourceArt/Meshes/*.fbx`, `SourceArt/Textures/*.png`; 제작·검사·게시 스크립트는 `Source/`에 보존했다.
- 다섯 부유섬, 중앙 관측 틈이 있는 돔, 황동 망원경의 포크·트러니언·고도 기어·핸드휠·파인더·카운터웨이트·렌즈, 지지 아치와 난간을 가진 네 교량, 별자리 바닥 정원·혼천의·해시계, 학자 주택 두 채, 도착 광장·등대·식생·책/탁자/상자를 제작했다.
- 실제 전체 XY 경계: **{valid['xy_footprint_m'][0]:.4f}×{valid['xy_footprint_m'][1]:.4f}m**, X 약 −46.799~47.000m, Y −45.000~46.000m. 높이 **−28.600~25.350m**. 모든 제작 형상과 구름을 100×100m 안에 배치했다.

## 검증 근거

- [저장 맵 재로드와 UE 자산 검사](Evidence/ue_validation.json): `world_partition=None`, `force_no_precomputed_lighting=True`, 실제 조명 9개 전부 Movable. 외부 액터/오브젝트 패키지와 BuiltData 없음.
- `/Game` 재귀 의존성 **60개 패키지**: 자신의 맵 1개와 자신의 자산 59개. 실제 배치 메시·모든 슬롯의 재질·재질이 사용하는 텍스처 59개가 그래프에 모두 포함됨. 범위 밖 의존성·누락 재질·누락 텍스처 0개. `/Engine` 편집기 카메라 프록시는 Game View에 렌더되지 않는 시각화 컴포넌트로 분리했다.
- 전체 **{tri:,}삼각형 / {components:,}닫힌 연결 성분**. [저장된 .blend 재검사](Evidence/persisted_source_audit.json)에서 열린/방향 불일치 edge 0, UV NaN/Inf 0, 저장 UV의 사각형 영역 교차 0. [FBX 축 보정 검사](Evidence/export_axis_validation.json)에서 반사 변환 뒤 면 winding을 반전하고 성분별 체적 양수를 확인했다. 열린 면 예외 없음; 돔 개구부 가장자리는 두께 캡을 갖고 렌즈 원판은 닫힌 앞면이다.
- 축은 export 메시 안에 Y 반사와 winding 보정으로 굽고 UE importer의 Y 반사를 상쇄했다. UE의 모든 메시 액터 스케일은 **(+1,+1,+1)**. 각 메시의 실제 cm bounds와 설계 원본 bounds 최대 차이 **{axis:.6f}cm**로 단위와 축을 확인했다.
- UV 목표 **64px/m**, 저장된 실제 UV 실측 **{mins:.6f}~{maxs:.6f}px/m**. 1024² 텍스처 기준 각 삼각형을 독립 평면 섬으로 만들고 각 면에 4px padding을 확보했다. 모든 UE 메시 UV는 full precision. 의도된 예외는 0..1 바깥의 절차적 타일 반복이며, 고유 atlas 베이킹이나 lightmap UV를 주장하지 않는다.
- 표면 이미지는 이 작업에서 새로 만든 결정적 절차적 PNG 21장이다. 외부 이미지/다른 테마·effort 자산을 복사하거나 재사용하지 않았다. 실제 UE 렌더만 장면 증거로 사용했다.
- 감독자가 네 최종 시점을 모두 확인하고 게시를 지시했다. 게시 전에 자신의 private Unreal 프로세스 종료를 조회했고 60개 파일을 복사한 뒤 모든 파일 해시를 다시 확인했다.
- 기존 비교 기록의 보존은 감독자가 독립 검사한 [보존 증명](Evidence/parent_comparison_preservation.json)을 참조한다. 작업자는 기존 보고서 내용을 읽거나 쓰지 않았다.

## 실제 UE 렌더

모두 **1920×1080 PNG**, `High`(모든 sg 그룹 2), `r.ScreenPercentage=100`, 실제 활성 `VMI_LIT`, Game View, 그리드·선택 표시 없음. [카메라 좌표·실제 회전·렌더 UTC·SHA256 매니페스트](Screenshots/capture_manifest.json).

- Overview: 위치 `(12000,-12000,16000)`cm → 원점, orthographic width `20000`cm.
- Top down: 위치 `(0,0,20000)`cm, pitch `−90` / yaw `0` / roll `0`, orthographic width `20000`cm.
- Observatory와 Bridge: 매니페스트에 기록한 perspective 48° 상세 카메라. 정적 환경으로 시간별 움직임을 주장하지 않아 timed pair는 만들지 않았다.

![전체 부유섬 천문대](Screenshots/overview.png)

![평면 구성과 교량 연결](Screenshots/top_down.png)

![천문대와 황동 망원경 상세](Screenshots/observatory.png)

![교량 접속과 바위 밑면 상세](Screenshots/bridge.png)

## 한계와 외부 참조

삼각형별 UV 섬의 타일 위상이 달라 가까운 거리에서 재질 이음과 삼각형 패턴이 보인다. 구름은 밝게 채운 겹친 타원체의 정적 예술적 표현이며 볼륨 기상 시뮬레이션이 아니다. 별자리·별 장식과 해질녘 조명은 예술적 배치다. 건축 내부의 실제 관측 설비 작동이나 내부 생활 공간, 망원경 추적·물리·게임플레이를 구현했다고 주장하지 않는다. 교량은 환경 모델이며 플레이어 충돌/경로 탐색을 제작 범위에 넣지 않았다. 렌더는 에디터 Game View에서 확인했고 패키지 빌드·PIE 게임플레이·FPS 보장은 수행하지 않았다.

외부 창작 이미지·메시·폰트 참조는 없다. API 동작은 설치된 Blender 5.0 및 Unreal Engine 5.7 헤더/실제 실행으로 확인했다. 모델/서비스 계층에 관한 외부 공식 링크는 감독자 제공 runtime 증거에 포함되어 있으며 이 보고서는 요청별 serving tier를 추정하지 않는다. 공유 Source/Config/Plugins/Binaries/uproject, 다른 맵과 작업 디렉터리는 변경하지 않았다. 새 단계나 범위 확장 없이 이 유한 제작과 보정 작업을 종료한다.
'''
(ROOT/'RESULT.md').write_text(prefix+body,encoding='utf-8')
status=read(ROOT/'STATUS.json');status.update({'status':'ready_for_review','finished_at_utc':finished.isoformat(),'finished_at_kst':finished.astimezone(kst).isoformat(),'elapsed_seconds':elapsed,'map':'/Game/Maps/SkyObservatory_max','ue_wait_seconds_all_attempts':wait,'ue_execution_seconds_all_attempts':run,'image_generation_seconds':0,'validation_summary':{'saved_map_reloaded':True,'world_partition':None,'recursive_game_packages':60,'placed_required_assets':59,'missing_or_forbidden_dependencies':0,'published_files':60,'all_private_published_sha256_match':True,'actual_ue_screenshots':4,'uv_overlap_pairs':0,'closed_source_components':components,'actor_scale':[1,1,1],'max_bounds_axis_error_cm':axis},'blockers':[]})
(ROOT/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
proof={'verified_at_utc':finished.isoformat(),'publication_rehashed_files':60,'screenshots_rehashed':4,'source_uv_normals_pass':True,'saved_map_graph_pass':True,'single_human_report':'RESULT.md','ready_for_review':True}
(E/'final_delivery_check.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(json.dumps({'result':'FINAL_DELIVERY_CHECK_PASS','elapsed_seconds':elapsed,'ue_wait_seconds':wait,'ue_run_seconds':run,'published_files':60,'screenshots':4},indent=2))
