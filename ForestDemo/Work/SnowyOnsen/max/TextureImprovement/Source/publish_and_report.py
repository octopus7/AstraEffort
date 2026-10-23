"""Publish only owned, closed, verified bytes and append the single Korean report."""
import sys,json,hashlib,shutil
from pathlib import Path
from datetime import datetime,timezone,timedelta
sys.dont_write_bytecode=True
import check_preservation
R=Path(r'D:/github/AstraEffort');B=R/'ForestDemo/Work/SnowyOnsen/max';W=B/'TextureImprovement';V=W/'Validation';P=R/'ForestDemo/Saved/Workers/SnowyOnsen/max/PrivateOnsen'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
assert read(V/'private_editor_closed.json')['no_matching_processes']
timings=[read(p) for p in sorted(V.glob('ue_timing_*.json'))];assert len(timings)==4 and timings[-1]['exit_code']==0
assert read(V/'render_validation_chain.json')['same_asset_bytes_through_attempts_02_03_04']
ue=read(V/'unreal_validation.json');assert ue['status']=='passed' and ue['world_partition_is_none'] and ue['force_no_precomputed_lighting']
assert len(ue['mesh_checks'])==16 and not ue['used_package_coverage']['missing']
uv=read(V/'uv_geometry_validation.json');assert uv['status']=='passed' and uv['final_triangles']==165742 and all(r['geometry_and_normals_unchanged'] for r in uv['meshes'])
review=read(V/'worker_visual_review.json');assert review['worker_viewed_all_eight']
parent=read(W/'Evidence/parent_final_visual_review.json');assert parent['approved_for_publication']
cap=read(W/'Screenshots/capture_manifest.json');assert len(cap['captures'])==8
for row in cap['captures']:assert sha(W/'Screenshots'/row['file'])==row['sha256']==review['captures'][row['name']]
motion=read(V/'capture_validation.json');assert motion['same_camera_timed_pair']
assert read(V/'texture_runtime_mips.json')['mip_levels']==12
source=read(V/'texture_import_validation.json');assert len(source['textures'])==15
for row in source['textures']:
 for f in row['source_files']:assert sha(Path(f['path']))==f['sha256']
snapshot=read(V/'captured_asset_snapshot.json')
for row in snapshot['files']:assert sha(Path(row['private']))==row['sha256']
preserved=check_preservation.run()
root=P/'Content/SnowyOnsen/max';target=R/'ForestDemo/Content/SnowyOnsen/max';pmap=P/'Content/Maps/SnowyOnsen_max.umap';tmap=R/'ForestDemo/Content/Maps/SnowyOnsen_max.umap'
files=sorted(p for p in root.rglob('*') if p.is_file());assert len(files)==45 and all(p.suffix=='.uasset' for p in files)
owned={p.resolve() for p in files}|{pmap.resolve()}
assert {p.resolve() for p in (P/'Content').rglob('*') if p.is_file() and p.suffix in ['.uasset','.umap']}==owned
assert not [p for p in (P/'Content').rglob('*') if any(x in p.name for x in ['__ExternalActors__','__ExternalObjects__','BuiltData'])]
pairs=[(p,target/p.relative_to(root)) for p in files]+[(pmap,tmap)];published=[];baseline=read(B/'FirstDelivery/archive_manifest.json');old={r['relative_path']:r['sha256'].lower() for r in baseline['asset_files']}
for src,dst in pairs:
 assert dst.resolve().is_relative_to(target.resolve()) or dst.resolve()==tmap.resolve()
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);a=sha(src);assert a==sha(dst)
 rel=src.relative_to(P/'Content').as_posix();change='new' if rel not in old else 'unchanged' if old[rel]==a else 'changed'
 published.append({'private':str(src),'published':str(dst),'relative_content_path':rel,'bytes':dst.stat().st_size,'private_sha256':a,'published_sha256':a,'match':True,'baseline_difference':change})
assert {p.resolve() for p in target.rglob('*') if p.is_file()}=={dst.resolve() for src,dst in pairs if dst!=tmap}
assert sha(pmap)==sha(P.parent/'FirstDeliveryContent/Maps/SnowyOnsen_max.umap')
counts={k:sum(r['baseline_difference']==k for r in published) for k in ['new','changed','unchanged']}
write(V/'publication_sha256.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'private_editor_closed':True,'file_count':46,'all_sha256_match':True,'baseline_difference_counts':counts,'map_binary_unchanged':True,'files':published})
start=datetime.fromisoformat('2026-10-23T14:00:03.073+00:00');finish=datetime.now(timezone.utc);kst=timezone(timedelta(hours=9));elapsed=(finish-start).total_seconds();wait=sum(t['wait_seconds'] for t in timings);run=sum(t['execution_seconds'] for t in timings)
source_seconds=read(V/'uv_geometry_validation_01.json')['seconds']+uv['seconds'];gen=read(W/'ImageGen/generation_manifest.json')
timing={'started_at_utc':start.isoformat(),'finished_at_utc':finish.isoformat(),'elapsed_wall_seconds':elapsed,'ue_wait_seconds_all_attempts':wait,'ue_execution_seconds_all_attempts':run,'uv_source_script_seconds_all_attempts':source_seconds,'image_generation_parallel_wall_seconds':gen['parallel_wall_seconds'],'image_generation_sum_request_seconds':gen['sum_request_duration_seconds'],'attempts':timings,'notes':['Canonical pass start supplied by parent actual turn metadata; first-delivery timestamps remain untouched.','UV source seconds measure script execution only, excluding Blender startup and code authoring; those are included in total wall.','Image requests ran concurrently; their sum must not be added to wall.','Attempts01/03 have native nonzero exits after normal shutdown logs;02 render and04 exact-asset validation exited0. No crash root-cause fix claimed.','Analysis initially ran before03 finished replacing captures; the incomplete-frame hash failure was preserved and final complete8-frame analysis passed.']}
write(V/'timing_summary.json',timing)
status={'theme':'SnowyOnsen','effort':'max','status':'ready_for_review','pass':'TextureImprovement','baseline_commit':baseline['baseline_commit'],'started_at_utc':start.isoformat(),'started_at_kst':start.astimezone(kst).isoformat(),'initial_manual_clock_at_utc':'2026-10-23T14:01:02Z','finished_at_utc':finish.isoformat(),'finished_at_kst':finish.astimezone(kst).isoformat(),'elapsed_seconds':elapsed,'map':'/Game/Maps/SnowyOnsen_max','validation_summary':{'meshes':16,'triangles':165742,'materials':14,'owned_textures':15,'actually_used_textures':9,'recursive_game_packages':len(ue['used_package_coverage']['recursive_game_packages']),'captures':8,'baseline_detail_captures':2,'published_files':46,'sha256_match':True,'map_binary_unchanged':True,'clean_render_attempt':2,'clean_exact_asset_validator_attempt':4,'parent_visual_review':True,'first_delivery_hashes_preserved':True},'blockers':[],'known_limitations':review['limitations']}
write(W/'STATUS.json',status);rootstatus=read(B/'STATUS.json');rootstatus['status']='ready_for_review';rootstatus['texture_improvement']=status;write(B/'STATUS.json',rootstatus)
notes={1:'기준 상세 2장 촬영 후 로그 종료 뒤 native access violation',2:'새 UV·재질 적용, 실제 8장 촬영, 정상 종료',3:'새 프로세스 재열기·최종 8장 촬영, 로그 종료 뒤 native access violation',4:'동일 46개 자산을 NullRHI로 재열기·검증, 정상 종료'}
table='\n'.join(f"| {i} | {t['wait_seconds']:.3f} | {t['execution_seconds']:.3f} | {t['exit_code']} | {notes[i]} |" for i,t in enumerate(timings,1))
wm=uv['wood_area_weighted_density']['Wood'];dm=uv['wood_area_weighted_density']['DarkWood'];mo=motion['motion'];overlaps=sum(r['exact_reused_uv_triangles'] for r in uv['meshes'])
existing=(B/'RESULT.md').read_text(encoding='utf8');marker='## 두 번째 작업 — 텍스처 품질 개선';head,oldpass=existing.split(marker,1)
plan=oldpass.split('현재 상태:',1)[0].replace('- [ ]','- [x]')
tail=f'''### 실제 개선 결과

첫 납품의 형상·배치·조명·노출을 유지하면서 **머티리얼 9개와 목재를 포함한 메시 10개의 UV**를 개선했다. 맵 파일은 기준 커밋과 **바이트 단위로 동일**하다. 새로 만든 원본 알베도 3개가 실제 UE 재질에 연결되어 있고, 모든 메시의 위치·면 인덱스·법선은 원본과 동일하다. 최종 **16개 메시 / 165,742개 삼각형 / 14개 머티리얼 / 15개 소유 텍스처 / 맵 1개**다.

목재 결은 긴 보·판자·기둥을 따르고, 휜 난간과 지붕 보에는 중심선 길이를 따라 UV를 배치했다. 돌과 눈에는 월드 좌표의 연속적인 3방향 투영을 적용했다. 벽은 6cm 크기의 약한 얼룩과 0.35mm 높이 근사를, 천은 화면상 크기에 따라 감쇠하는 2mm 직조와 0.18mm 높이 근사를 추가했다. 수면의 넓은 줄무늬는 65cm 스케일의 이동하는 부드러운 noise로 바꾸고, 기존 5.7초 주기·1.3cm 높이 변화와 증기는 유지했다. [재질 매핑](TextureImprovement/Validation/material_mapping.json), [실제 제작 코드](TextureImprovement/Source/build_materials.py)

### 생성 원본과 표면 크기

built-in ImageGen으로 독립 생성한 원본은 모두 **1254×1254 PNG**이며 선택한 파일은 도구 원본과 SHA256이 같다. 픽셀 편집·명암 굽기·장면 이미지 생성은 하지 않았다. 전체 프롬프트·실제 요청 시각·원본 경로·해시·표면 배정은 [생성 기록](TextureImprovement/ImageGen/generation_manifest.json)에 있다.

| 표면 | 원본 | 한 타일의 실제 크기 | 원본 정보 밀도 | UE 빌드 샘플 밀도 | 기본 roughness / 높이 근사 |
|---|---|---:|---:|---:|---|
| 목재·어두운 목재 | T_IMG_Timber | 2.5m | 501.6px/m | 819.2px/m | 0.72·0.77 / 0.65mm |
| 돌·돌길 | T_IMG_Stone | 2.5m | 501.6px/m | 819.2px/m | 0.82 / 1.4mm |
| 눈 | T_IMG_Snow | 5m | 250.8px/m | 409.6px/m | 0.91 / 1.6mm |

UE 고유 `StretchToPowerOfTwo` 빌드는 2048²·PF_DXT1·12단계 mip을 생성했다. 알베도는 sRGB이며 자산은 streaming 가능 상태를 유지한다. 촬영에서는 첫 납품과 동일하게 streaming을 끄고, overview와 두 근접 촬영 시점의 **실제 resident 2048² / 12 mips**를 기록했다. 확대 빌드는 원본에 새로운 세부 정보를 추가하지 않는다. [임포트 원본·색 공간](TextureImprovement/Validation/texture_import_validation.json), [런타임 mip 증거](TextureImprovement/Validation/texture_runtime_mips.json)

원본 가장자리에는 측정 가능한 작은 불일치가 있어 무조건 seamless라고 주장하지 않는다. Mirror addressing으로 경계값을 이어 붙였으며 전체 무늬는 타일 길이의 2배마다 반복되고 경계에서 방향이 뒤집힌다. 실제 목재·돌·눈 근접 화면에서 두드러진 접힘은 확인되지 않았으나, 모든 시점에서 이음새가 없다는 뜻은 아니다. [원본 경계 측정](TextureImprovement/Validation/image_source_analysis.json)

### UV·형상 검증과 예외

목재 **656개 연결 부품**의 장축을 기본으로 삼되, 축이 모호한 62개는 결정적인 축 선택을 사용했고, 휜 부품 16개는 중심선 근사를 사용했다. 측면은 둘레가 이어지는 U / 길이 방향 V, 끝면은 별도 평면 차트다. 곡선 근사는 기하를 변경하지 않는다.

| 면적 가중 밀도 | Wood | DarkWood |
|---|---:|---:|
| 대상 면적 m² | {wm['surface_area_m2']:.3f} | {dm['surface_area_m2']:.3f} |
| 5백분위 px/m | {wm['percentiles_source_px_per_m']['0.05']:.3f} | {dm['percentiles_source_px_per_m']['0.05']:.3f} |
| 중앙값 px/m | {wm['percentiles_source_px_per_m']['0.5']:.3f} | {dm['percentiles_source_px_per_m']['0.5']:.3f} |
| 95백분위 px/m | {wm['percentiles_source_px_per_m']['0.95']:.3f} | {dm['percentiles_source_px_per_m']['0.95']:.3f} |
| 목표 70–150% 밖 면적 | 0% | 0% |

밀도가 일정해도 모든 방향의 왜곡이 같지는 않다. 독립 검토에서 Wood 비등방성의 95·99백분위는 **1.689·2.114**, 비율 2 초과 면적은 **2.016%**, 4 초과는 **0.0448%**였다. Wood의 끝면·베벨·곡선에 대한 평면 차트 예외는 **64.373m², 전체 Wood 면적의 4.31%**이며 이 경계에는 UV 위상 이음새가 생긴다. 이를 작은 베벨만의 예외로 축소하지 않는다. DarkWood 같은 예외 면적은 0.138m²다.

반복 타일 방식으로 서로 다른 부품 사이의 UV 겹침은 의도적이다. 정확히 재사용된 UV 삼각형은 {overlaps:,}개이며 고유 아틀라스·무겹침 패킹을 주장하지 않는다. 아틀라스 패딩은 적용 대상이 아니며 끝면·둘레 랩·평면 예외 차트를 분리했다. 독립 재구성은 목재 폴리곤 70,822개의 선언된 매핑과 일치했고 설명되지 않은 UV 경계는 0개였다. 유한하지 않은 UV·면적 0 UV·퇴화 기하·와인딩 충돌·비정상 연결은 모두 0개다. [최종 UV·기하 검사](TextureImprovement/Validation/uv_geometry_validation.json), [독립 FBX·UV 검토](TextureImprovement/Evidence/independent_uv_review.json), [제작 원본](TextureImprovement/Source/SnowyOnsen_TextureImproved.blend)

Stone·Snow·Path의 이전 메시 UV 수치는 활성 재질 밀도를 뜻하지 않는다. 이 표면의 실제 스케일은 위 월드 투영 값이며, 격자 방향 경사면은 3방향 가중 혼합을 사용한다.

### 저장 맵·실제 움직임·발행

저장 맵의 직접 `world_partition=None`, 동적 Movable 조명과 `force_no_precomputed_lighting=True`를 다시 확인했다. 지형의 실제 UE 크기는 **10000.000977×10000.000977cm**, 배치 메시 16개의 actor 위치는 원점·회전 0·스케일 1이다. 외부 액터·외부 오브젝트·BuiltData가 없다.

새 프로세스의 재귀 그래프는 **45개 소유 /Game 패키지**이며 실제 배치 메시 16개·재질 14개·사용 텍스처 9개가 모두 포함된다. 텍스처 총 15개 중 기존 텍스처 6개는 활성 재질에서 사용하지 않지만 소유 디렉터리에 보존했다. 그중 5개는 직렬화된 의존성에 남아 있어 활성 사용 목록과 그래프 개수가 다르다. 그래프 누락·타 테마 참조는 0개다. [저장 맵 검사](TextureImprovement/Validation/unreal_validation.json)

동일 카메라의 **{motion['time_separation_seconds']:.3f}초** 차이에서 평균 PNG RGB 변화량(0–255)은 **물만 있는 영역 {mo['clear_water']['mean_abs_png_rgb_0_255']:.4f} / 정적인 건물 {mo['static_house_control']['mean_abs_png_rgb_0_255']:.4f} / 증기 {mo['steam_against_ridge']['mean_abs_png_rgb_0_255']:.4f}**였다. 수면은 의도적으로 약한 변화이며, 증기와 분리해서 검증했다. 이는 예술적인 셰이더 변화이고 물리 유체·굴절 시뮬레이션 측정은 아니다. [픽셀 영역과 측정](TextureImprovement/Validation/capture_validation.json)

최종 8장은 실제 D3D UE03 렌더다. UE02도 같은 자산으로 정상 종료한 8장을 보존했다. UE03은 로그를 닫은 뒤 access violation으로 종료했으므로 정상 실행으로 바꾸어 기록하지 않았다. 후속 UE04는 **촬영 없는 full-editor NullRHI**에서 동일 46개 자산 해시·저장 맵·의존성을 재검증하고 정상 종료했다. NullRHI를 시각 증거로 사용하지 않았다. 종료 오류의 정확한 원인은 확인되지 않았고 수정했다고 주장하지 않는다. [렌더→재열기 검증 연결](TextureImprovement/Validation/render_validation_chain.json)

에디터가 닫힌 것을 확인한 뒤 소유 자산과 지정 맵 **46개 전부**를 발행했고 private/published SHA256이 일치한다. 기준 대비 새 파일 {counts['new']}개, 변경 {counts['changed']}개, 동일 {counts['unchanged']}개다. 맵 바이트는 동일하며 새 텍스처·UV·재질만 갱신했다. [발행 SHA256](TextureImprovement/Validation/publication_sha256.json), [프로세스 종료](TextureImprovement/Validation/private_editor_closed.json)

첫 납품 아카이브 125개, 변경 금지 활성 Work 파일 123개, 별도 Content 보존본 43개 모두 원래 해시와 일치한다. 첫 납품 커밋은 `{baseline['baseline_commit']}`이며 Git 변경 작업은 감독이 담당한다. [동결 보존 증거](TextureImprovement/Validation/baseline_preservation.json)

### 실제 시간

| 항목 | 기록 |
|---|---|
| 시작 UTC / KST | `{start.isoformat()}` / `{start.astimezone(kst).isoformat()}` |
| 완료 UTC / KST | `{finish.isoformat()}` / `{finish.astimezone(kst).isoformat()}` |
| 전체 경과 | **{elapsed:.3f}초** |
| 모든 UE 대기 / 실행 합계 | **{wait:.3f}초 / {run:.3f}초** |
| UV 원본 스크립트 실행 합계 | **{source_seconds:.3f}초** |
| ImageGen 동시 요청 경과 / 개별 요청 합계 | **{gen['parallel_wall_seconds']:.3f}초 / {gen['sum_request_duration_seconds']:.3f}초** |

UV 시간은 두 Blender 스크립트 내부 실행 시간으로 시작 비용·코드 작성 시간과 다르다. 전체 경과는 계획·코드·검토·대기를 포함한다. 첫 납품 시간과 합치거나 시작을 재설정하지 않았다. 실제 설정은 계속 **gpt-6-astra / max**, 로컬 fast이며 개별 요청의 실제 serving tier는 노출되지 않는다. [시간 원장](TextureImprovement/Validation/timing_summary.json), [실행 설정 검증](TextureImprovement/Evidence/parent_runtime_effort_verified.json)

| UE 시도 | 대기 초 | 실행 초 | 종료 코드 | 결과 |
|---|---:|---:|---:|---|
{table}

UE02의 재질 그래프 조립 중 Missing Sine input 경고는 최종 저장 후 UE03에 남아 있지 않았다. 캡처 파일이 교체되는 중 시작한 첫 분석의 해시 실패도 보존했으며, 전체 촬영 완료 후 8장 검사를 다시 통과했다. 추가 외형 수정·무한 반복은 진행하지 않았다.

### 같은 카메라의 전후 화면

모든 렌더는 **1920×1080, High 2, ScreenPercentage 100, Lit, Game View**다. 공통 overview는 `(12000,-12000,16000)cm`에서 원점을 향하며 Ortho Width 20000cm, top_down은 `(0,0,20000)cm`, Pitch -90/Yaw 0/Roll 0, Ortho Width 20000cm다. 기본 6개 카메라와 추가 상세 2개의 전후 위치·회전·화각 일치를 검증했다. 조명·노출은 동일 맵 바이트로 보존했다. [촬영 명세·시각·해시](TextureImprovement/Screenshots/capture_manifest.json)

목재 개선 전:

![목재 개선 전](TextureImprovement/Screenshots/BeforeDetails/detail_timber.png)

목재 개선 후:

![목재 개선 후](TextureImprovement/Screenshots/detail_timber.png)

돌·눈 개선 전:

![돌과 눈 개선 전](TextureImprovement/Screenshots/BeforeDetails/detail_stone_snow.png)

돌·눈 개선 후:

![돌과 눈 개선 후](TextureImprovement/Screenshots/detail_stone_snow.png)

전체 구성 개선 전:

![전체 구성 개선 전](FirstDelivery/Screenshots/overview.png)

전체 구성 개선 후:

![전체 구성 개선 후](TextureImprovement/Screenshots/overview.png)

![개선 후 탑다운](TextureImprovement/Screenshots/top_down.png)

![개선 후 온천](TextureImprovement/Screenshots/onsen.png)

![개선 후 마을](TextureImprovement/Screenshots/village.png)

![개선 후 수면 t0](TextureImprovement/Screenshots/water_t0.png)

![개선 후 수면 t1](TextureImprovement/Screenshots/water_t1.png)

원래의 강한 창 조명·어두운 절벽 전면과 교차 카드 증기 표현을 유지했다. 큰 수면은 불투명한 재질 근사이며 실제 굴절·유체 계산은 없다. 충돌·게임플레이·FPS 목표를 추가하지 않았다. 목재 차트 이음새와 Mirror 방향 반전은 위에 기록한 한계다. 감독이 최종 이미지를 확인했으며 [작업자 시각 검토](TextureImprovement/Validation/worker_visual_review.json)와 [감독 검토](TextureImprovement/Evidence/parent_final_visual_review.json)를 남겼다.
'''
(B/'RESULT.md').write_text(head+marker+plan+tail,encoding='utf8')
print(json.dumps({'status':'ready_for_review','finished_at_utc':finish.isoformat(),'elapsed_seconds':elapsed,'published_files':46,'baseline_difference_counts':counts,'ue_wait_seconds':wait,'ue_execution_seconds':run},indent=2),flush=True)
