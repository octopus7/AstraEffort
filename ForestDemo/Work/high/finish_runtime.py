from pathlib import Path
import json,datetime,hashlib,shutil
R=Path('D:/github/AstraEffort/ForestDemo/Work/high');S=Path('D:/github/AstraEffort/ForestDemo/Saved/Workers/high');repo=Path('D:/github/AstraEffort')
v=json.loads((R/'runtime_validation.json').read_text());assert v['status']=='runtime_checks_passed_pending_native_log_review'
log=(S/'runtime.log').read_text(encoding='utf-8-sig',errors='replace')
passed=[line for line in log.splitlines() if 'Test Completed. Result={Success}' in line and 'ForestDemo.ScreenDebugLogger.HelloOnBeginPlay' in line]
assert len(passed)==1
assert v['checks']['pawn_possessed_by_player_0'] and v['checks']['spawn_distance_cm']==0
assert v['checks']['runtime_ground_collision']['sweep_blocking_hit'] and v['checks']['movement']['distance_cm']>30
attempt1=json.loads((R/'Logs/runtime_attempt1_timing.json').read_text());attempt2=json.loads((S/'runtime_timing.json').read_text());assert attempt2['exit_code']==0
manifest=json.loads((R/'delivery_manifest.json').read_text());checked=[]
for f in manifest:
 p=repo/f['path'];scratch=S/'ForestDemo/Content'/Path(f['path']).relative_to('ForestDemo/Content')
 assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']
 assert hashlib.sha256(scratch.read_bytes()).hexdigest()==f['sha256']
 checked.append(f['path'])
shutil.copy2(S/'runtime.log',R/'Logs/runtime_validation.log');shutil.copy2(S/'runtime_timing.json',R/'Logs/runtime_attempt2_timing.json')
image=R/'Screenshots/runtime_hello.png'
if image.exists():image.rename(R/'Screenshots/runtime_viewport.png')
finish=datetime.datetime.now(datetime.timezone.utc);start=datetime.datetime.fromisoformat(v['supplement_started_at_utc']);kst=datetime.timezone(datetime.timedelta(hours=9))
timing={'started_at_utc':start.isoformat(),'finished_at_utc':finish.isoformat(),'started_at_kst':start.astimezone(kst).isoformat(),'finished_at_kst':finish.astimezone(kst).isoformat(),'elapsed_seconds':(finish-start).total_seconds(),'shared_ue_wait_seconds':attempt1['wait_seconds']+attempt2['wait_seconds'],'ue_execution_seconds':attempt1['execution_seconds']+attempt2['execution_seconds'],'attempts':[attempt1,attempt2]}
v['status']='passed';v['supplement_finished_at_utc']=finish.isoformat();v['timing']=timing
v['checks']['native_hello_beginplay_test']={'status':'Success','name':'ForestDemo.ScreenDebugLogger.HelloOnBeginPlay','evidence_line':passed[0],'scope':'Existing baseline native test creates a Game world, spawns ScreenDebugLogger, dispatches BeginPlay, and asserts OnScreenDebugMessageExists. In the separate actual PIE map, the native logger instance is present.'}
v['checks']['unchanged_deliverables_sha256_count']=len(checked)
v['visual_hello_confirmation']=False
v['capture_note']='runtime_viewport.png captured the editor viewport, not the possessed PIE camera. It is not evidence of visible Hello text; native automation log is the BeginPlay message-registration evidence.'
v['warnings']=['Engine displays a multiple directional-light forward-shading priority warning; the brightest main sun is selected as fallback. No map changes were made in this supplement.','Movement verification used the existing floating DefaultPawn, not a new walking Character; full walking/jumping traversal remains untested.']
(R/'runtime_validation.json').write_text(json.dumps(v,indent=2),encoding='utf-8')
s=json.loads((R/'STATUS.json').read_text(encoding='utf-8-sig'));s['status']='ready_for_review';s['blockers']=[];s['first_ready_at_utc']='2026-10-21T12:40:14.899003+00:00';s['runtime_supplement']={**timing,'status':'passed','evidence':'ForestDemo/Work/high/runtime_validation.json','map_modified':False};s['validation']['runtime_pie_spawn_and_possession']=True;s['validation']['runtime_ground_blocking_sweep']=True;s['validation']['native_hello_beginplay_automation']='Success';s['validation']['deliverables_unchanged_after_runtime_check']=46
(R/'STATUS.json').write_text(json.dumps(s,indent=2),encoding='utf-8')
p=R/'RESULT.md';text=p.read_text(encoding='utf-8-sig')
text=text.replace('충돌은 설정 검사와 지형 trace로 검증했고 완전한 캐릭터 도보/점프 플레이 테스트나 FPS 벤치마크는 수행하지 않았습니다.','최초 제출에서는 충돌을 설정 검사와 지형 trace로 확인했습니다. 아래 감독 보완에서 실제 PIE 기본 pawn 이동·충돌 검증을 추가했습니다. 별도 Character의 도보/점프 전체 동선 테스트와 FPS 벤치마크는 수행하지 않았습니다.')
text=text.replace('네이티브 Hello는 액터와 기준 구현을 확인했으며 캡처를 위해 실행 중 디버그 글자를 찍은 증거는 없습니다.','네이티브 Hello는 아래 감독 보완에서 기존 BeginPlay 자동화 테스트의 Success 로그로 검증했습니다. 화면에 보이는 Hello 문구 자체의 캡처 증거는 없습니다.')
text+=f'''

## 감독 보완 — 실제 PIE 및 BeginPlay 검증

원래 시작 **2026-10-21T12:11:54Z**와 최초 ready **2026-10-21T12:40:14.899003Z**는 보존했습니다. 이번 보완 시작은 {start.isoformat()} ({start.astimezone(kst).isoformat()}), 완료는 {finish.isoformat()} ({finish.astimezone(kst).isoformat()})입니다. 추가 경과 {timing['elapsed_seconds']:.3f}초, 공유 UE 대기 합계 {timing['shared_ue_wait_seconds']:.3f}초, 실제 UE 실행 합계 {timing['ue_execution_seconds']:.3f}초입니다. 첫 실행은 PIE 시작 후 Python의 pawn 조회 별칭 오류로 검사가 중단되었고, 엔진 헤더에 명시된 `get_controlled_pawn()`으로 수정해 두 번째 실행에서 통과했습니다. 두 실행의 실제 timing과 오류 로그를 보존했습니다.

- 실제 플레이 월드: `{v['checks']['actual_pie_world']}`. GameModeBase / DefaultPawn / PlayerController 사용.
- pawn은 PlayerStart (650,-1900,407.739423)cm에 정확히 생성됐으며 시작점 차이 **0cm**, player 0에게 빙의된 상태를 확인했습니다.
- 게임 월드에서 pawn을 지면 아래로 sweep한 결과 실제 blocking hit가 발생했습니다. 지면 Z=297.802923cm, 차단 후 pawn 중심 Z=335.255655cm, 간격 37.452732cm입니다.
- 기존 기본 pawn에 +Y 이동 입력을 약 2초 적용하여 **{v['checks']['movement']['distance_cm']:.3f}cm** 이동한 것을 확인했습니다. DefaultPawn의 floating 이동을 검증한 것이며, 새 걷기 Character를 추가하지 않았습니다. 검사 후 원위치로 돌리고 PIE를 종료했습니다.
- PIE 맵 안의 `/Script/ForestDemo.ScreenDebugLogger` 인스턴스 1개를 확인했습니다. 별도로 기존 네이티브 `ForestDemo.ScreenDebugLogger.HelloOnBeginPlay` 테스트가 **Success**로 완료됐습니다. 이 테스트는 실제 Game world에서 해당 클래스의 BeginPlay를 dispatch하고 `GEngine->OnScreenDebugMessageExists`를 assert합니다. 로그의 실제 성공 시각은 2026-10-21 13:00:16.094 UTC입니다.
- `runtime_viewport.png`는 에디터 뷰포트를 캡처했으므로 Hello 글자 관찰 증거로 사용하지 않았습니다. BeginPlay의 메시지 등록 증거는 네이티브 테스트 로그입니다.
- 추가 런타임 경고: 보조광을 포함한 여러 DirectionalLight의 forward-shading 우선순위가 같다는 경고가 표시됩니다. 엔진은 가장 밝은 주광을 fallback으로 선택합니다. 이번 보완에서는 조명이나 맵을 변경하지 않았습니다.

세부 수치: [runtime_validation.json](D:/github/AstraEffort/ForestDemo/Work/high/runtime_validation.json). 실제 로그: [runtime_validation.log](D:/github/AstraEffort/ForestDemo/Work/high/Logs/runtime_validation.log). 최초 실패와 두 실행 시간도 `Logs/runtime_attempt1.*`, `Logs/runtime_attempt1_timing.json`, `Logs/runtime_attempt2_timing.json`에 남았습니다.

에디터 종료 후 기존 전달 **46개 파일 모두**의 SHA-256을 scratch와 게시본에서 다시 대조했고 최초 delivery_manifest와 동일했습니다. 맵 수정·에셋 재게시·기존 네 장 재촬영·shared Source/Config 변경·Git 작업은 없었습니다.
'''
p.write_text(text,encoding='utf-8');print(json.dumps({'status':'ready_for_review','supplement_timing':timing,'unchanged_files':len(checked)},indent=2))
