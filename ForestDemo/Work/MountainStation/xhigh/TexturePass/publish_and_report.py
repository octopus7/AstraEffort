from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,shutil,struct
ROOT=Path('D:/github/AstraEffort/ForestDemo');W=ROOT/'Work/MountainStation/xhigh/TexturePass';S=ROOT/'Saved/Workers/MountainStation/xhigh';P=S/'Project';T=S/'TexturePass'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
status=read(W/'STATUS.json');uv=read(W/'Evidence/saved_ue_validation.json');static=read(W/'Evidence/validation.json');runtime=read(W/'Evidence/runtime_validation.json');visual=read(W/'Evidence/visual_review.json');manifest=read(W/'Screenshots/capture_manifest.json');gen=read(W/'Evidence/imagegen_calls.json');src=read(W/'Evidence/source_uv_validation.json');exceptions=read(W/'Evidence/source_exception_audit.json')
partition=read(W/'Evidence/world_partition_validation.json')
assert uv['success'] and static['success'] and runtime['success'] and partition['success'] and partition['direct_check_available']
assert runtime['checks']['exact_expected_ground_meshes'] and len(runtime['blocking_pawn_sweeps'])==4
assert visual['four_scene_images_inspected'] and visual['native_hello_visible'] and manifest['first_delivery_exact_camera_match']
timings=[]
for path in sorted((T/'Timings').glob('*.json')):
 d=read(path);d['name']=path.stem;timings.append(d)
timings.sort(key=lambda d:d['wait_started_at_utc']);assert timings[-1]['name']=='partition' and timings[-1]['exit_code']==0
assert next(t for t in timings if t['name']=='runtime')['exit_code']==0
assert next(t for t in timings if t['name']=='capture')['exit_code']==0
# The final read-only partition process is closed; packages must still match the validation fingerprint.
hashes=[]
for relative,digest in uv['private_package_hashes'].items():
 relative=relative.replace('\\','/');assert relative.startswith('MountainStation/xhigh/') or relative=='Maps/MountainStation_xhigh.umap'
 private=P/'Content'/relative;assert sha(private)==digest,relative
 published=ROOT/'Content'/relative;published.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(private,published);assert sha(published)==digest
 hashes.append({'path':'Content/'+relative,'private_path':str(private),'published_path':str(published),'validated_sha256':digest,'private_sha256':sha(private),'published_sha256':sha(published),'bytes':published.stat().st_size})
for c in manifest['captures']:
 p=W/'Screenshots'/(c['name']+'.png');assert sha(p)==c['sha256'] and struct.unpack('>II',p.read_bytes()[16:24])==(1920,1080)
for c in gen['calls']:assert sha(Path(c['preserved_path']))==c['sha256']
first=read(W/'Evidence/first_delivery_preservation.json');assert all(sha(W.parent/'FirstDelivery'/rel)==digest for rel,digest in first['sha256'].items())
for t in timings:shutil.copy2(Path(t['log']),W/'Evidence'/('ue_'+t['name']+'.log'))
now=datetime.now(timezone.utc);kst=timezone(timedelta(hours=9));started=datetime.fromisoformat(status['started_at_utc']);elapsed=(now-started).total_seconds();wait=sum(t['wait_seconds'] for t in timings);execution=sum(t['execution_seconds'] for t in timings)
(W/'Evidence/process_timings.json').write_text(json.dumps(timings,indent=2))
evidence_hashes={str(p.relative_to(W)):sha(p) for p in (W/'Evidence').rglob('*') if p.is_file() and p.name not in ['published_hashes.json']}
(W/'Evidence/published_hashes.json').write_text(json.dumps({'published_at_utc':now.isoformat(),'map':'/Game/Maps/MountainStation_xhigh','files':hashes,'evidence_sha256':evidence_hashes,'first_delivery_unchanged':True,'screenshots_sha256':{c['name']:c['sha256'] for c in manifest['captures']},'source_art_hashes':read(W/'Evidence/source_art_hashes.json')},indent=2))
(W/'Evidence/process_timings.json').write_text(json.dumps(timings,indent=2))
table='\n'.join(f"| {t['name']} | {t['wait_seconds']:.3f} | {t['execution_seconds']:.3f} | {t['exit_code']} |" for t in timings)
uvrows='\n'.join(f"| {name} | {s['triangles']:,} | {s['area_m2']:.3f} | {s['area_weighted_density_px_per_m']:.4f} | {uv['meshes'][name]['lods']['render']['all_triangles']:,} | {uv['meshes'][name]['lods']['render']['area_weighted_density_px_per_m']:.4f} | {uv['meshes'][name]['lods']['render']['sampled_triangles']:,} |" for name,s in src['assemblies'].items())
swrows='\n'.join(f"| {x['name']} | {x['positive_distance_cm']:.3f} | {x['actor_label']} | {x['mesh'].split('/')[-1]} | true / false |" for x in runtime['blocking_pawn_sweeps'])
image_links='\n\n'.join(f"### {c['name']}\n\n![{c['name']}](Screenshots/{c['name']}.png)\n\n{c['captured_at_utc']} / {c['captured_at_kst']}" for c in manifest['captures'])
ue_samples=sum(l['sampled_triangles'] for x in uv['meshes'].values() for l in x['lods'].values());render_count=sum(x['lods']['render']['all_triangles'] for x in uv['meshes'].values())
text=f'''# MountainStation / xhigh — TexturePass

Status: **ready_for_review**. 기존 100×100m Alder Pass 구성을 유지하면서 UV와 imagegen 표면 텍스처를 보강했습니다. 최종 private editor 종료 후 {len(hashes)}개 패키지를 소유 경로에 게시했고, 저장 맵을 검증한 프로세스의 해시와 private/published 해시가 모두 일치합니다. FirstDelivery 파일의 해시도 그대로입니다. 첫 납품의 STATUS/RESULT/시각·커밋을 덮어쓰지 않았습니다. Git 조작과 보조 에이전트 사용은 없었습니다.

## 두 번째 패스 실제 시간

- 시작 UTC: {started.isoformat()}
- 시작 KST: {started.astimezone(kst).isoformat()}
- 완료 UTC: {now.isoformat()}
- 완료 KST: {now.astimezone(kst).isoformat()}
- 벽시계: **{elapsed:.3f}초 ({elapsed/60:.2f}분)**.
- UE mutex/우선순위 대기 합계: **{wait:.3f}초**. UE 실행 합계: **{execution:.3f}초**. 실패 종료도 포함합니다.
- Blender UV 작성 실행: {src['elapsed_seconds']:.3f}초. 이 값과 UE/이미지 생성은 벽시계 내 작업이며 총 wall에 다시 더하지 않습니다.
- imagegen: 독립 이미지 4건, 동시 요청 4개, 재시도·중복 호출 0회. 호출 구간 전체 wall **{gen['batch_wall_seconds']:.3f}초**, 중첩을 포함한 요청별 시간 합 **{gen['total_request_seconds_including_overlap']:.3f}초**, 중첩분 **{gen['overlapped_request_seconds']:.3f}초**. 내부 서버의 실제 병렬 실행 여부는 모릅니다.
- 토큰 증분은 감독자의 dispatch/완료 누적값으로 계산합니다. 이 작업자가 토큰 수를 추정하지 않았습니다.

| UE 실행 | 대기 초 | 실행 초 | 종료 코드 |
|---|---:|---:|---:|
{table}

`build`에서 에셋 저장과 스크립트 완료 후 엔진 종료 단계의 비정상 코드 -1073741819가 발생했습니다. 로그는 Exiting까지 도달했지만 정상 종료로 처리하지 않았습니다. `capture`의 별도 새 프로세스에서 저장 에셋 재로드·검증, 실제 렌더와 PIE를 수행해 종료 코드 0을 확인했습니다. `runtime`은 지형 메시 자체에 대한 sweep을 보완한 추가 새 프로세스이며 정상 종료했습니다. 전체 로그와 원본 시간 기록은 `Evidence/ue_*.log`, `process_timings.json`에 있습니다. Forest 우선 runner를 사용했고 다른 실행을 종료하지 않았습니다.

`partition`은 감독 요청에 따른 마지막 읽기 전용 재로드 검사입니다. `WorldSettings.get_editor_property("world_partition")`에서 실제 저장 맵의 값이 None임을 확인했습니다. UE 5.7 헤더의 VisibleAnywhere 프로퍼티와 엔진 getter 구현을 확인한 뒤 사용했으며, 외부 패키지 부재만으로 non-WP를 추정하지 않았습니다. 자세한 값은 `world_partition_validation.json`에 있습니다.

## UV와 표면 밀도

목표 **256px/m**, 실제 이미지 **1254×1254**, UV 배율 **256/1254 per metre**, 반복 폭 **4.8984375m**입니다. 요청 프롬프트의 1024 해상도를 실제 값으로 주장하지 않습니다. 실제 면적 공식은 `density = sqrt(UV 삼각형 면적 × 1254² / 배치 후 m² 면적)`입니다. source 변환을 적용하고 UE cm→m, BuildScale, actor/component scale `(1,-1,1)`을 확인했습니다. 반사 배율의 절대값은 1입니다. 원본과 저장 UE 모두 UV0이며 머티리얼 추가 UV 배율은 1입니다.

공면·동일 재질·인접 삼각형을 고유 표면 아일랜드로 묶고 직교 투영했습니다. 원본 전체 사각 경계의 shelf 간격 검사는 nominal **8px 이상**이며 아일랜드 경계 사각형 간 겹침은 없습니다. UV는 0..1 밖으로 확장되고, wrap 후 같은 타일을 재사용하는 겹침은 의도된 것입니다. 고유 베이크 atlas나 라이트맵이라고 주장하지 않습니다. 곡면은 면 단위 아일랜드여서 베벨/곡면 경계에서 결 방향이 연속적이지 않을 수 있습니다.

| 메시 | 원본 삼각형 | 원본 면적 m² | 원본 면적 가중 px/m | 저장 UE Render 삼각형 | UE 전체 면적 가중 px/m | UE Render 표본 수 |
|---|---:|---:|---:|---:|---:|---:|
{uvrows}

원본은 **{exceptions['all_source_triangles']:,}개 삼각형 전수**, 전체 면적 **{exceptions['all_source_area_m2']:.3f}m²**입니다. 이는 보이는 부지 면적이 아니라 바닥/뒷면/겹쳐진 내부 표면/반복 나무를 포함한 모든 기하 면적입니다. 16 target pixel² 이상인 **{exceptions['regular_at_least_16_target_pixels']:,}면**은 전부 목표 ±1% 안입니다. 1..16 pixel²인 전나무 작은 면 6개는 ±1%를 벗어났고, 그보다 작은 글자·베벨과 퇴화 면의 편차도 원본 CSV에서 숨기지 않았습니다. 재질별 면적과 밀도는 `source_uv_validation.json`, 예외는 `source_exception_audit.json`을 참고하십시오.

저장 UE에서는 새 프로세스에서 SourceModel/RenderData LOD0의 전체 삼각형/재질 목록, 총 기하·UV 면적, 아일랜드 수를 검사했습니다. Render 삼각형은 **{render_count:,}개**이며 수입 과정에서 퇴화/아주 작은 면이 정리되어 원본과 개수가 다릅니다. 총 기하 면적의 상대 차이는 모든 메시에서 0.000001 미만입니다. 개별 밀도는 재질당 최대 256개씩 두 LOD 합 **{ue_samples:,}개 표본**이며, 16 pixel² 이상 표본은 모두 ±2% 안입니다. 정확한 배치 위치/UV/재질/작은 면 예외를 `*_uv_samples.json`에 보존했습니다. **저장 UE의 개별 면 밀도나 패딩·겹침을 전수 검사했다고 주장하지 않습니다.** source의 전수 패킹 검사와 UE 표본 확인 범위는 다릅니다.

## 이미지 생성과 실제 연결

내장 **image_gen.imagegen**을 사용했습니다. 목재, 미네랄, 도장 금속, 전나무 4개 원본은 `Textures/`에 원본 바이트로 보존했습니다. 정확한 전체 프롬프트는 `texture_prompts.json`, 호출 UTC/KST·원본 경로·해시·동시 구간은 `Evidence/imagegen_calls.json`입니다. 외부 창작 에셋, 다른 작업의 텍스처, API/CLI 대체 생성은 사용하지 않았습니다.

21개 머티리얼에 실제 TextureSample을 UV0로 연결하여 기존 색을 곱하고 거칠기도 약하게 변조했습니다. 새 프로세스에서 각 저장 머티리얼의 컴파일된 used-texture 목록과 실제 텍스처 크기를 확인했습니다. 세부 표면 매핑과 연결식은 `Evidence/build_textures.json`, `saved_ue_validation.json`, `README.md`에 있습니다. Glass/Cream/Amber/Dark/Flowers와 Backdrop은 유리·글자·작은 색 요소/배경 예외로 단색을 유지합니다. 모든 authored 파일은 본인 MountainStation/xhigh 루트에 속합니다.

## 장면·런타임 검증

저장 맵 재로드, 100m 범위, 모든 재귀 `/Game` 의존성의 소유 경로, non-WP·외부 패키지/BuiltData 없음, 동적 조명과 정적 바닥 표본이 통과했습니다. 부지·역·곡선 선로/침목·플랫폼·터널 연결과 기존 건축 비례를 유지했습니다. Sun의 forward priority를 1, fill을 0으로 지정하여 첫 납품의 동순위 경고를 정리했습니다. 새 실제 Hello 캡처에서 그 노란 경고가 보이지 않음을 확인했습니다.

실제 PIE world에서 PlayerStart, PlayerController와 DefaultPawn 빙의, 100cm sweep 이동, 아래의 하향 차단과 정상 종료를 검증했습니다. 모든 차단은 `blocking=true`, `initial_overlap=false`, 양의 실제 이동거리이며 정확한 actor/component/mesh를 JSON에 기록했습니다.

| 표본 | 실제 이동 cm | hit actor label | hit mesh | blocking / initial overlap |
|---|---:|---|---|---|
{swrows}

네이티브 소스 해시와 실제 PIE 녹색 **Hello**를 확인했습니다. `Evidence/runtime_hello.png`는 UI 포함 보조 증거이며 네 비교 이미지와 분리됩니다. DefaultPawn의 비행 이동/하향 충돌 검사이며 실제 보행 캐릭터 주행 시험이라고 주장하지 않습니다.

## 실제 UE 비교 캡처

첫 납품과 네 카메라의 위치·회전·투영·FOV·1920×1080·High·100% 설정이 정확히 같습니다. manifest에서 항목별 비교를 통과했고 FirstDelivery manifest 해시를 연결했습니다. 아래는 실제 UE 렌더이며 imagegen으로 만든 장면 이미지가 아닙니다. 원본 PNG를 후처리하지 않았습니다. 직접 열어 목재 기둥/통/침목의 결, 벽과 석재 표면, 선로와 승강장 연결 및 터널 입구를 확인했습니다. 원경은 여전히 차분한 낮은 대비이고, 기존 공통 overview의 높은 원거리 모서리 잘림은 유지됩니다.

{image_links}

## 납품 경로와 한계

- `Content/Maps/MountainStation_xhigh.umap`
- `Content/MountainStation/xhigh/`: 9 meshes, 27 materials, 4 generated-source textures.
- `Work/MountainStation/xhigh/TexturePass/`: 원본 이미지/Blender/FBX, 작성 스크립트, 실제 캡처, 검증 및 이번 별도 기록.
- `Evidence/published_hashes.json`: 검증 시 private 패키지 → 종료 후 private → published 해시 및 증거 해시 연결.

1254 NPOT 원본은 변형하지 않아 mipmap/streaming을 사용하지 않습니다. 이로 인한 원거리 minification/메모리 한계가 있으며 FPS·LOD 최적화 성과를 주장하지 않습니다. 반복 텍스처와 작은 면의 UV 양자화, 곡면 seam 예외가 있습니다. 역 내부·열차 운행은 추가하지 않았고 터널 뒤는 닫힌 배경입니다. 원본 그림은 seamless를 요청했으나 모든 경계의 수학적 무봉합을 보증하지 않습니다. 첫 import 종료 실패도 위에 별도 기록했습니다.
'''
(W/'RESULT.md').write_text(text,encoding='utf-8')
status.update(status='ready_for_review',finished_at_utc=now.isoformat(),finished_at_kst=now.astimezone(kst).isoformat(),elapsed_seconds=elapsed,mutex_wait_seconds=wait,ue_execution_seconds=execution,imagegen_batch_wall_seconds=gen['batch_wall_seconds'],imagegen_summed_request_seconds=gen['total_request_seconds_including_overlap'],validation={'saved_ue':True,'non_world_partition_direct':True,'recursive_dependencies':True,'materials_with_texture':21,'source_all_triangles':exceptions['all_source_triangles'],'ue_individual_density_samples':ue_samples,'four_exact_camera_pngs':True,'pie':runtime['checks'],'native_hello_visually_confirmed':True,'published_package_hashes_match':True,'first_delivery_unchanged':True},blockers=[],known_limitations=['NPOT 1254px originals: no mipmaps/streaming.','UE per-triangle density and overlap/padding checks sampled; source density/packing exhaustive.','Tiny faces, curved facet seams and intentional repeating UV reuse.','Build process saved assets then returned abnormal shutdown code; subsequent validation/capture/runtime processes exited 0.','DefaultPawn flight; static exterior and closed tunnel rear.'])
(W/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':'ready_for_review','files':len(hashes),'elapsed_seconds':elapsed,'wait_seconds':wait,'ue_execution_seconds':execution,'finished_at_utc':now.isoformat(),'finished_at_kst':now.astimezone(kst).isoformat()},indent=2))
