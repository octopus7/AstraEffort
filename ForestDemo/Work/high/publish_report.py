from pathlib import Path
import json, datetime, hashlib, shutil, struct
ROOT=Path('D:/github/AstraEffort/ForestDemo')
W=ROOT/'Work/high';S=ROOT/'Saved/Workers/high';C=S/'ForestDemo/Content'
start=datetime.datetime.fromisoformat('2026-10-21T12:11:54+00:00')
v=json.loads((W/'validation.json').read_text());cap=json.loads((W/'Screenshots/capture_manifest.json').read_text());mig=json.loads((W/'migration.json').read_text())
timings=[json.loads(p.read_text()) for p in S.glob('*_timing.json')]
last=json.loads((S/'ambient_capture_timing.json').read_text());assert last['exit_code']==0
assert v['map_reloaded'] and not v['forbidden_dependencies'] and not v['external_packages']
assert v['native_hello_logger_count']==1 and all(x['blocking_hit'] for x in v['ground_traces'].values())
assert all(not d.startswith('/Game/') or d.startswith('/Game/Forest/high/') or d=='/Game/Maps/high' for dd in v['dependencies'].values() for d in dd)
assert len(cap['shots'])==4
image_hashes=[]
for shot in cap['shots']:
 p=W/'Screenshots'/(shot['name']+'.png');raw=p.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n';assert struct.unpack('>II',raw[16:24])==(1920,1080)
 image_hashes.append(hashlib.sha256(raw).hexdigest())
 assert shot['captured_at_utc']>mig['migration_finished_at_utc']
assert len(set(image_hashes))==4,'Each capture must show a distinct viewpoint'
top=next(s for s in cap['shots'] if s['name']=='top_down');assert abs(top['rotation_pitch_yaw_roll'][0]+90)<.01
src=C/'Forest/high';dest=ROOT/'Content/Forest/high'
assert src.is_dir() and (C/'Maps/high.umap').is_file()
assert not list(src.rglob('*BuiltData*'))
shutil.copytree(src,dest,dirs_exist_ok=True)
shutil.copy2(C/'Maps/high.umap',ROOT/'Content/Maps/high.umap')
files=[p for p in src.rglob('*') if p.is_file()]+[C/'Maps/high.umap'];delivery=[]
for p in files:
 relative=p.relative_to(C);target=ROOT/'Content'/relative
 digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest==hashlib.sha256(target.read_bytes()).hexdigest()
 delivery.append({'path':'ForestDemo/Content/'+relative.as_posix(),'sha256':digest,'bytes':target.stat().st_size})
(W/'delivery_manifest.json').write_text(json.dumps(delivery,indent=2))
(W/'Logs').mkdir(exist_ok=True);shutil.copy2(S/'ambient_capture.log',W/'Logs/final_validation_capture.log')
shutil.copy2(S/'ambient_capture_timing.json',W/'Logs/final_capture_timing.json')
finish=datetime.datetime.now(datetime.timezone.utc);elapsed=(finish-start).total_seconds()
kst=datetime.timezone(datetime.timedelta(hours=9))
initial=datetime.datetime.fromtimestamp((W/'build_summary.json').stat().st_mtime,datetime.timezone.utc)
migtime=(datetime.datetime.fromisoformat(mig['migration_finished_at_utc'])-datetime.datetime.fromisoformat(mig['migration_started_at_utc'])).total_seconds()
wait=sum(t['wait_seconds'] for t in timings)
art=json.loads((W/'scene.json').read_text());treecount=sum('Broadleaf' in a['mesh'] or 'Fir_' in a['mesh'] for a in art['actors'])
status={'effort':'high','status':'ready_for_review','started_at_utc':start.isoformat(),'finished_at_utc':finish.isoformat(),'elapsed_seconds':elapsed,'map':'/Game/Maps/high','asset_root':'/Game/Forest/high','validation':{'map_reload':True,'recursive_owned_packages':v['owned_packages_checked'],'forbidden_dependencies':0,'terrain_extent_cm':v['terrain_extent_cm'],'blocking_mesh_actor_count':v['blocking_mesh_actor_count'],'ground_collision_traces':4,'native_hello_logger_count':1,'actual_ue_pngs':4,'capture_resolution':[1920,1080],'published_hash_verified_files':len(delivery),'editor_closed_before_publish':True},'blockers':[],'path_change':mig,'shared_ue_wait_seconds':wait,'capture_started_at_utc':cap['capture_started_at_utc'],'capture_finished_at_utc':cap['capture_finished_at_utc']}
(W/'STATUS.json').write_text(json.dumps(status,indent=2))
report=f'''# high — Quietwater Grove

검토 준비 완료. 최종 맵 `/Game/Maps/high`, 에셋 `/Game/Forest/high/`.

## 실제 시간

| 단계 | UTC | KST |
|---|---|---|
| 시작 | {start.isoformat()} | {start.astimezone(kst).isoformat()} |
| 최초 제작 맵 저장 완료 | {initial.isoformat()} | {initial.astimezone(kst).isoformat()} |
| 최종 캡처 시작 | {cap['capture_started_at_utc']} | {datetime.datetime.fromisoformat(cap['capture_started_at_utc']).astimezone(kst).isoformat()} |
| 최종 캡처 종료 | {cap['capture_finished_at_utc']} | {datetime.datetime.fromisoformat(cap['capture_finished_at_utc']).astimezone(kst).isoformat()} |
| 최종 검증·게시 완료 | {finish.isoformat()} | {finish.astimezone(kst).isoformat()} |

전체 실제 경과 **{elapsed:.3f}초**. 최초 맵 저장까지 {(initial-start).total_seconds():.3f}초, 이후 추가 검증·렌더·아트 보정·경로 이전·게시 {(finish-initial).total_seconds():.3f}초입니다. 후반 단계는 서로 섞여 진행되어 순수 아트 시간과 순수 캡처 시간을 임의로 나누지 않았습니다. 최종 캡처 실행 시간 {last['execution_seconds']:.3f}초, 공유 UE 실행 슬롯 누적 대기 {wait:.3f}초입니다.

사용자 경로 변경은 시작 시각을 재설정하지 않고 처리했습니다. `/Game/high` → `/Game/Forest/high`를 UE `rename_directory`로 이전하여 직접 참조를 저장하고 redirector만 남은 옛 경로를 제거했습니다. 새 아트 재생성 없음. 기록된 실제 migration API 작업은 {migtime:.3f}초이며, 요청 기록 시각 {mig['requested_path_change_recorded_at_utc']}, 실제 실행 시작 {mig['migration_started_at_utc']}, 완료 {mig['migration_finished_at_utc']}입니다. 기존 렌더가 끝난 후 이 작업을 시작했으므로 요청부터 완료까지의 벽시계 간격은 순수 이전 작업 시간과 다릅니다.

## 장면 구성과 제작

100×100m의 연속 지형 위에 {treecount}그루의 활엽수·전나무를 배치했습니다. 북쪽은 침엽수가 섞인 높은 숲, 중앙은 굽은 산책길과 작은 빈터, 서쪽은 독립된 내륙 호수, 남쪽은 넓은 모래 해변과 해수면입니다. 호수 중심은 약 (-1700,700), 수면 Z=162cm이며 바다는 남쪽 해안 너머 Z=78cm에 있습니다. 두 물은 연결되지 않고 숲과 길로 접근합니다.

직접 제작한 재사용 메시 **22종**, 재질 **23종**, 저장된 액터 **{v['actor_count']}개**입니다. 가지가 갈라지는 둥근 활엽수 3종, 부드러운 층을 가진 전나무 2종, 이끼 바위 4종, 풀 2종, 고사리·갈대·야생화, 쓰러진 통나무, 난간이 있는 나무다리, 길 표식, 수면 잔물결을 포함합니다. 팔레트는 탁한 초록·회녹색·모래색·청록으로 제한했습니다. 얼굴·하트·장식 구름 모티프는 없습니다.

원본 `Source/QuietwaterGrove.blend`, FBX 22개, `make_art.py`, `scene.json`, `build_level.py`로 형상과 배치를 재현할 수 있습니다. 가져오기 과정의 좌표계 반전은 액터의 local Y scale로 보정했고 회전은 이름 있는 pitch/yaw/roll 인수를 사용합니다. 최종 동적 skylight는 공유 허용된 `/Engine/MapTemplates/Sky/DaylightAmbientCubemap`을 읽기 전용 사용합니다. 외부 다운로드나 다른 effort 에셋·코드 참조는 없습니다.

## 플레이와 검증

- 지형 범위: {v['terrain_extent_cm'][0]:.4f} × {v['terrain_extent_cm'][1]:.4f}cm.
- terrain/bridge는 complex-as-simple 충돌, 나무·바위·통나무·표식은 convex 충돌. 작은 식생과 물은 비차단. BlockAll 메시 액터 {v['blocking_mesh_actor_count']}개.
- PlayerStart (650,-1900,407.739)cm. 실제 지면 Z={v['ground_traces']['PlayerStart']['location'][2]:.3f}cm으로 약 110cm 간격. 호수 바닥·해변·호수 촬영점까지 총 4개 ray trace가 지형에 맞았습니다.
- 기본 `/Script/ForestDemo.ScreenDebugLogger` 액터 1개를 보존했습니다. 기준 소스의 BeginPlay Hello 기능을 그대로 사용하며 shared Source/Binaries는 수정하지 않았습니다.
- 저장 후 별도 UE 실행에서 맵을 재로드했습니다. Asset Registry로 맵과 전체 소유 에셋 {v['owned_packages_checked']}개 패키지의 hard/soft 프로젝트 의존성을 재귀 검사했습니다. 허용 범위 밖 `/Game` 참조 0개, 옛 `/Game/high` 참조 0개입니다.
- `new_level`로 만든 non-World-Partition 레벨이며 external actor/object 패키지가 없습니다. 동적 조명과 force_no_precomputed_lighting 사용. Maps에는 high.umap만 전달합니다.
- 최종 UE 프로세스 종료 후 소유 에셋과 맵만 복사했으며, 파일 {len(delivery)}개의 SHA-256이 scratch 원본과 같습니다. `delivery_manifest.json` 참조.

검증 실행: `Run-UnrealIsolated.ps1 -Project <high scratch>/ForestDemo.uproject -LogPath <high scratch>/ambient_capture.log -TimingPath <high scratch>/ambient_capture_timing.json -EditorArguments @('/Game/Maps/high','-ExecutePythonScript=<Work/high>/run_final.py','-NoSound','-RenderOffscreen')`. 실제 exit code 0. 최종 로그는 `Logs/final_validation_capture.log`, 세부 결과는 `validation.json`, `geometry_checks.json`, `migration.json`입니다.

## 실제 UE 스크린샷

각 PNG를 직접 열어 검정·빈 이미지가 아니며 장면이 보이는 것을 확인했습니다. 이미지 생성/보정은 하지 않았습니다. 1920×1080, High scalability, screen percentage 100, SceneCapture2D 최종 LDR이며 에디터 UI·기즈모·선택선·Hello 문구가 포함되지 않습니다. 위치·회전·투영·촬영 UTC는 `Screenshots/capture_manifest.json`에 있습니다.

공통 중심 (0,0), 지면 기준 Z0=300cm. overview=(12000,-12000,16300), target=(0,0,300), ortho width=20000cm. top_down=(0,0,20300), pitch=-90/yaw=0/roll=0, ortho width=20000cm. lake/beach는 실제 지형 hit 높이+170cm, horizontal FOV=70°입니다. 두 근접 이미지는 장소별 위치가 달라 직접적인 프레이밍 동등 비교에 한계가 있습니다.

![Overview](Screenshots/overview.png)
![Top down](Screenshots/top_down.png)
![Lake](Screenshots/lake.png)
![Beach](Screenshots/beach.png)

## 전달 파일과 한계

- `ForestDemo/Content/Forest/high/Materials/*.uasset`, `Meshes/*.uasset`
- `ForestDemo/Content/Maps/high.umap`
- `ForestDemo/Work/high/`의 소스·스크립트·검증 JSON·PNG·보고서

물은 스타일화된 불투명 정적 표면으로 수영·부력·파도 시뮬레이션은 구현하지 않았습니다. 섬 형태의 100m 사이트 밖에는 확장된 플레이 지형이 없습니다. 지면 재질 경계는 약 83cm 샘플 그리드이므로 탑뷰에서 계단 형태가 보일 수 있습니다. 충돌은 설정 검사와 지형 trace로 검증했고 완전한 캐릭터 도보/점프 플레이 테스트나 FPS 벤치마크는 수행하지 않았습니다. 네이티브 Hello는 액터와 기준 구현을 확인했으며 캡처를 위해 실행 중 디버그 글자를 찍은 증거는 없습니다. 독립 검토는 감독자가 수행하며 이 작업은 직접 제작·자체 시각 검증했습니다. Git staging/commit/push는 실행하지 않았습니다.
'''
(W/'RESULT.md').write_text(report,encoding='utf-8')
print(json.dumps({'status':'ready_for_review','finished_at_utc':finish.isoformat(),'elapsed_seconds':elapsed,'files':len(delivery),'wait_seconds':wait}))
