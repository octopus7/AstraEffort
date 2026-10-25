from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import shutil
import sys

P = Path(__file__).resolve().parent
ROOT = P.parent
KST = timezone(timedelta(hours=9))


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def link(label, path):
    return f'[{label}]({path.as_posix()})'


def review():
    analysis = read(P/'render_analysis.json')
    report = (P/'QA/implementation_review.md').read_text(encoding='utf-8')
    assert 'No remaining publication blocker was found' in report
    write(P/'visual_review.json', {
        'utc': datetime.now(timezone.utc).isoformat(), 'accepted': True,
        'reviewers': ['parent', 'delivery_review'],
        'basis': 'Direct inspection of actual UE overview, top-down, architectural views, corn/meadow close-ups, fixed-camera wind pairs and sequence endpoints; independent written review. No claim of continuous MP4 playback.',
        'findings': [
            'Separate green corn field behind barn; four original fields retained.',
            'Varied tall meadow forms and pale seed heads fill irregular edge patches; primary routes remain open.',
            'Visible corn and meadow displacement across fixed-camera captures; anchored WPO graph and retained vertex colors verified.',
            'Late overview after close-view warmup has correct green vegetation colors.',
        ],
        'limitations': ['Artistic material wind, no physical plant simulation or blocking vegetation collision.', 'Clips contain 32 actual frames each at approximately 4.68fps; not a smooth gameplay/performance benchmark.', 'Inherited microscopic MillTower UV exceptions remain documented in Before/RESULT.md.'],
        'independent_review': str(P/'QA/implementation_review.md'),
        'image_sha256': {r['name']: r['sha256'] for r in analysis['images']},
    })
    print('Final visual acceptance recorded for 13 actual UE stills.')


def finish():
    pub = read(P/'publication.json')
    valid = read(P/'validation.json')
    assert pub['all_hashes_match'] and pub['private_editor_closed']
    assert valid['all_passed'] and len(valid['checks']) == 23
    for row in pub['files']:
        assert sha(Path(row['destination'])) == row['sha256'] == sha(Path(row['source']))
    before = read(P/'Before/STATUS.json')
    status = read(P/'STATUS.json')
    runs = []
    for f in (P/'Execution').glob('*_timing.json'):
        row = read(f)
        runs.append({'phase': f.name.removesuffix('_timing.json'), **row})
    runs.sort(key=lambda x: x['run_started_at_utc'])
    now = datetime.now(timezone.utc)
    start = datetime.fromisoformat(status['started_at_utc'])
    wait = sum(r['wait_seconds'] for r in runs)
    execution = sum(r['execution_seconds'] for r in runs)
    elapsed = (now-start).total_seconds()
    timings = {'started_at_utc': start.isoformat(), 'started_at_kst': start.astimezone(KST).isoformat(), 'finished_at_utc': now.isoformat(), 'finished_at_kst': now.astimezone(KST).isoformat(), 'elapsed_seconds': elapsed, 'timing_note': status['timing_note'], 'ue_wait_seconds': wait, 'ue_execution_seconds': execution, 'image_generation_seconds': 0, 'attempts': runs}
    write(P/'timings.json', timings)
    status.update({'status': 'ready_for_review', **{k: v for k, v in timings.items() if k != 'attempts'}, 'phase': 'Published tall meadow and separate corn field, both with anchored wind', 'validation_summary': '23 saved-load/runtime checks passed; 13 actual UE stills and two 32-frame clips; independent review has no blocker; every published package SHA-256 matches private source.', 'validation': valid['checks'], 'publication': 'publication.json', 'result': 'RESULT.md', 'blockers': []})
    write(P/'STATUS.json', status)
    for f in (P/'Screenshots').iterdir():
        if f.is_file():
            shutil.copy2(f, ROOT/'Screenshots'/f.name)
    for name in ('publication.json', 'render_analysis.json', 'visual_review.json', 'validation.json'):
        shutil.copy2(P/name, ROOT/name)
    root_status = read(ROOT/'STATUS.json')
    root_status.update({'status': 'ready_for_review', 'finished_at_utc': now.isoformat(), 'finished_at_kst': now.astimezone(KST).isoformat(), 'elapsed_seconds': (now-datetime.fromisoformat(before['started_at_utc'])).total_seconds(), 'elapsed_note': 'Calendar span from first-delivery start through this follow-up; includes the interval between deliveries. Separate measured follow-up duration is in VegetationPass/timings.json.', 'ue_wait_seconds': before['ue_wait_seconds']+wait, 'ue_execution_seconds': before['ue_execution_seconds']+execution, 'phase': status['phase'], 'validation_summary': status['validation_summary'], 'validation': valid['checks'], 'first_delivery': {'record': 'VegetationPass/Before/STATUS.json', 'started_at_utc': before['started_at_utc'], 'finished_at_utc': before['finished_at_utc'], 'elapsed_seconds': before['elapsed_seconds']}, 'follow_up': 'VegetationPass/STATUS.json', 'blockers': []})
    write(ROOT/'STATUS.json', root_status)
    image = lambda label, name: f'![{label}]({(P/"Screenshots"/name).as_posix()})'
    run_table = '\n'.join(f"| {r['phase']} | {r['wait_seconds']:.3f} | {r['execution_seconds']:.3f} | {r['exit_code']} |" for r in runs)
    report = f'''# WindmillFarm / ultra — 키 큰 들풀과 옥수수밭

요청한 별도 옥수수 재배구역과 키 큰 들풀을 추가하고, 둘 다 뿌리를 고정한 채 바람에 흔들리도록 적용했다. private UE 저장·재로드·실행 검증 후 소유한 자산과 맵만 전달 경로에 반영했다. 상태는 **ready_for_review**이며 Git 커밋은 수행하지 않았다.

## 장면 변경

- 헛간 뒤 15×12m의 독립 옥수수밭: 14줄, 210포기(3개 원형 각70), 가운데 관리 통로, 헛간 뒤 연결길과 울타리17구간.
- 키 큰 들풀 1,457개 인스턴스: 긴 풀591, 밝은 이삭769, 갈대 형태97. 16개 후보 영역 안에서 불규칙하게 분포시키고 가장자리는 성기게 배치했다.
- 기존 밭4개, 건물, 풍차, 나무20그루와 주요 길을 유지했다. 밭과 겹치던 나무1그루를 이동하고 새 밭/입구 안의 기존 짧은 풀만 제거했다.
- 옥수수와 들풀은 UE foliage 인스턴싱을 사용한다. 정점색 R의 높이 가중치로 뿌리 변위를0으로 고정하고, 공통 월드 위치/시간 위상으로 줄기 휘어짐과 잎·이삭의 잔떨림을 만들었다.

## 실제 UE 렌더와 바람 증거

{image('농장 전체 — 헛간 뒤 별도 옥수수밭과 들풀', 'overview.png')}

{image('옥수수 재배구역', 'corn.png')}

{image('키 큰 들풀', 'meadow.png')}

{link('옥수수 바람 영상', P/'Motion/corn_wind.mp4')} · {link('들풀 바람 영상', P/'Motion/meadow_wind.mp4')}

13장 정지 렌더는 실제 UE5.7 SceneCapture2D, 1920×1080, D3D12 SM5, High/sg2, 동적 조명, FinalColorLDR/RGBA8/gamma2.2다. {link('카메라·개별 촬영 시각', P/'Screenshots/capture_manifest.json')}와 {link('렌더 해시·분석', P/'render_analysis.json')}에 원본 설정을 기록했다. 전체 조망은 근접 시점으로 머티리얼 표시를 안정시킨 뒤 같은 원래 카메라로 다시 촬영했다.

옥수수/들풀 고정 카메라 쌍의 실제 월드 시간 간격은 각각1.905240/1.912218초다. RGB 차이12 초과 픽셀은871,938/658,481개이며 그림자·시간적 렌더 차이도 포함한다. 식물의 위치 변화는 이미지 직접 검토와 연결된 WPO/정점색 검증을 함께 근거로 삼았다.

각 영상은 실제 UE 1280×720 PNG32장으로 만들었다. 원본 촬영 구간은 옥수수6.626404초, 들풀6.609987초이며 평균 촬영 간격으로 약4.68fps MP4를 인코딩했다. 프레임 보간·생성 이미지는 없고, 작은 프레임 간 시간 차이는 평균으로 정규화했다. 연속 재생 성능 측정이나30/60fps 게임 녹화는 아니다. {link('영상 출처·해시', P/'Motion/video_manifest.json')}와 프레임별 월드 시간/UTC 원본 manifest를 함께 보관했다. FFmpeg 디코드 검사도 통과했다.

## 저장·실행·게시 검증

{link('최종 검증 JSON', P/'validation.json')}의 **23개 검사 모두 통과**했다. 저장 후 맵 재로드,100×100m 범위, 비월드파티션, 외부 actor/object 패키지 없음, 자기 자산 재귀 의존성, 동적 조명, UV/머티리얼, 인스턴스 수, 바람 입력 그래프, 정점색, 바람 bounds와 경로 간격을 확인했다. PIE에서 DefaultPawn 소유, 지면/풍차 벽 trace, 지면에 막히는 sweep, 수평200cm 이동과 PIE 종료를 확인했다. 이는 스크립트 실행 검증이며 사람이 직접 보행한 테스트는 아니다.

최종 polish 검증 UTC는 {valid['utc']}이며 polish/overview UE 프로세스는 모두 정상 종료했다. 최종 로그에는 초기 바람 머티리얼 compile/fallback 오류가 없다. {link('독립 구현·시각 검토', P/'QA/implementation_review.md')}에 초기 문제와 수정 후 승인 근거를 보존했다.

전달 맵: {link('WindmillFarm_ultra.umap', ROOT.parents[3]/'ForestDemo/Content/Maps/WindmillFarm_ultra.umap')} (`/Game/Maps/WindmillFarm_ultra`). 자산 루트는 `/Game/WindmillFarm/ultra/`다. 게시 패키지는 **{pub['file_count']}개**, 새 패키지{pub['new_files']}개, baseline 대비 변경{pub['changed_files']}개다. 모든 게시 파일의 SHA-256이 private 원본과 일치한다. {link('파일별 게시 검증', P/'publication.json')}와 {link('private UE 종료 확인', P/'shutdown_check.json')}을 제공한다. 다른 작업의 자산, 공유 소스/설정, Git/index는 변경하지 않았다.

## 원본과 UV

이번에 옥수수3종/들풀3종을 독립 제작하고 FBX를 재임포트해 검사했다. 원본 Blender, 제작 코드, mesh/UV/정점색 manifest는 {link('Corn', P/'Art/Corn/manifest.json')}과 {link('Meadow', P/'Art/Meadow/manifest.json')}에 있다. 옥수수는 각2,168tri, 들풀은1,396/1,400/2,284tri다. UV0은 삼각형별 고유 셀, UV1은 무스케일128px/m 목표다. 새 메시의 붕괴 UV/중복 UV0 셀은 없으며 정점색 뿌리 R=0과 높이 오차3e-8 미만을 재임포트에서 확인했다. UV0 여백은1024기준 옥수수2px, 들풀2.13–2.69px다.

배치 스케일에 따라 유효 평균 밀도는 옥수수 약121.9–137.5px/m, 들풀 약112.3–218.6px/m로 달라진다. 새 독립 절차 BaseColor7장과 기존 자기 지면 atlas에 새 밭/입구만 추가한 texture1장을 실제 머티리얼에 연결했다. {link('텍스처 원본·해시', P/'Art/Textures/manifest.json')}를 제공한다. 외부 창작 자산이나 이미지 생성 서비스는 사용하지 않았다.

바람은 물리 시뮬레이션이 아닌 시각적 머티리얼 변형이다. 식물 충돌·수확 상호작용은 없고, 경로 검사는 배치 중심 기준이므로 일부 움직이는 잎이 길 가장자리까지 뻗을 수 있다. 주요 길은 렌더로도 확인했다. 기본 free-fly pawn을 유지했으며 이번에 LOD/플랫폼별 성능 최적화를 수행하지 않았다. 기존 MillTower의 미세 UV 예외 등 최초 장면의 한계는 {link('보존한 최초 결과', P/'Before/RESULT.md')} 및 기존 QA에 그대로 남아 있으며, 전체 자산에 대한 엄격한 zero-overlap 주장은 하지 않는다.

## 실제 시간과 보존

| 항목 | 기록 |
|---|---|
| 이번 시작 UTC / KST | {start.isoformat()} / {start.astimezone(KST).isoformat()} |
| 이번 완료 UTC / KST | {now.isoformat()} / {now.astimezone(KST).isoformat()} |
| 측정 wall seconds | {elapsed:.3f} |
| UE 대기 합계 | {wait:.3f}s |
| UE 실행 합계, 실패 포함 | {execution:.3f}s |
| 이미지 생성 서비스 | 0s, 미사용 |

시작은 이번 후속 작업의 첫 명시적 시계 측정값이며 초기 확인 작업이 그보다 앞섰다. 따라서 위 wall은 전체 요청의 정확한 최초 시점부터 측정한 값으로 주장하지 않는다. 원래 최초 제작의 시작/완료/3323.076879초 기록은 Before에 보존했고 이번 측정과 분리했다. 소스 제작 병렬 시간은 wall에 포함하며 별도 합산하지 않는다. {link('시도별 실제 시각과 대기/실행', P/'timings.json')}:

| 시도 | 대기초 | 실행초 | 종료코드 |
|---|---:|---:|---:|
{run_table}

초기 VertexColor 출력 이름 때문에 바람 shader 입력이 누락된 문제를 기본 출력 연결·반환값 assertion으로 수정했다. 옥수수 카메라의 수관 가림을 이동으로 해결하고, 작은 들풀 스케일의 바람 bounds를40cm로 확대했다. 최초 capture의 비정상 종료(-1073741819)는 기록을 보존했으며 이후 최종 capture/polish/overview에서 재현되지 않았다. 그 종료 원인은 확정하지 않았다. 최종 성공 근거는 이전 실패 로그가 아닌 위 최종 검증/렌더/게시 해시다.

변경 전 보고서/스크린샷/검증/시각 기록은 `VegetationPass/Before/`, 변경 전 Content/map은 자기 scratch의 `VegetationBefore/Content/`에 보존했다. 재촬영은 자기 private 프로젝트에서 공용 runner를 통해 `Run-Vegetation.ps1 -Phase polish`, 종료 후 `-Phase overview` 순서로 수행한다. shared 프로젝트에서 생성·저장 세션을 실행하지 않는다.
'''
    (P/'RESULT.md').write_text(report, encoding='utf-8')
    root_report = f'''# 오래된 풍차 농장 — WindmillFarm / ultra

최신 전달본에는 **15×12m 별도 옥수수밭210포기와 키 큰 들풀1,457개**가 추가됐으며 둘 다 뿌리를 고정한 바람 움직임을 갖는다. 기존 밭4개와 주요 통로를 유지했다. 저장·실행 검증23개를 통과하고 private UE 종료 후 {pub['file_count']}개 소유 패키지를 해시 일치 확인하여 게시했다. 상태는 **ready_for_review**다. Git 커밋은 감독자 담당이다.

{image('최신 농장 전체', 'overview.png')}

{link('최신 상세 결과·시각·검증·한계', P/'RESULT.md')} · {link('현재 상태', ROOT/'STATUS.json')} · {link('게시 파일 SHA-256', ROOT/'publication.json')}

{link('옥수수 바람 영상', P/'Motion/corn_wind.mp4')} · {link('들풀 바람 영상', P/'Motion/meadow_wind.mp4')}

영상은 실제 UE 프레임으로 만든 약4.68fps 증거다. 바람은 시각적 머티리얼 변형이며 식물 물리/충돌/수확 기능은 없다. 현재 `Screenshots/`는 이번 최종13장과 동일한 원본 복사본이다. 원본 촬영 manifest는 VegetationPass의 파일 경로를 가리킨다.

최초 제작 기록과 알려진 기존 UV 예외는 {link('변경 전 결과', P/'Before/RESULT.md')}와 {link('변경 전 상태', P/'Before/STATUS.json')}에 보존했다. 최초 제작3323.076879초와 이번 측정{elapsed:.3f}초를 분리한다. 이번 측정은 첫 명시적 시계 확인부터이며 초기 확인은 그보다 앞섰다. 루트 `timings.json`은 최초 제작 기록, `VegetationPass/timings.json`은 이번 추가 작업 기록이다. root STATUS의 전체 elapsed는 두 전달 사이 간격을 포함한 달력상 경과다.
'''
    (ROOT/'RESULT.md').write_text(root_report, encoding='utf-8')
    print(json.dumps({'status': 'ready_for_review', 'files': pub['file_count'], 'new_files': pub['new_files'], 'changed_files': pub['changed_files'], 'wall_seconds': elapsed, 'ue_wait_seconds': wait, 'ue_execution_seconds': execution, 'finish_utc': now.isoformat()}, indent=2))


if __name__ == '__main__':
    {'review': review, 'finish': finish}[sys.argv[1]]()
