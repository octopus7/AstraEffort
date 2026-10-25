"""Run four separate Blender producers and record real subprocess return codes.

File sizes and SHA256 values are an inventory. No model/image data is inspected.
"""
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BLENDER = Path('C:/Program Files/Blender Foundation/Blender 4.5/blender.exe')
SLUGS = ['articulated_welding_mech', 'cylindrical_mixer', 'rounded_foundry_workshop', 'vertical_material_tower']
START = datetime.fromisoformat('2026-10-25T06:06:25+00:00')
KST = timezone(timedelta(hours=9))
LOGS = ROOT / 'logs'
LOGS.mkdir(exist_ok=True)


def utc():
    return datetime.now(timezone.utc)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')


def file_record(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def run(slug):
    command = [str(BLENDER), '--background', '--factory-startup', '--threads', '4',
               '--python-exit-code', '1', '--python', str(ROOT / 'build.py'), '--', slug]
    start = utc()
    t = time.perf_counter()
    log = LOGS / (slug + '.log')
    print('START ' + slug + ' ' + start.isoformat(), flush=True)
    with log.open('w', encoding='utf-8') as stream:
        proc = subprocess.run(command, cwd=str(ROOT), stdout=stream, stderr=subprocess.STDOUT,
                              creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    end = utc()
    result = {'slug': slug, 'command': command, 'returncode': proc.returncode,
              'started_at_utc': start.isoformat(), 'finished_at_utc': end.isoformat(),
              'started_at_kst': start.astimezone(KST).isoformat(), 'finished_at_kst': end.astimezone(KST).isoformat(),
              'elapsed_seconds': round(time.perf_counter() - t, 3),
              'log': log.relative_to(ROOT).as_posix()}
    print('FINISH ' + slug + ' returncode=' + str(proc.returncode) + ' seconds=' + str(result['elapsed_seconds']), flush=True)
    write_json(LOGS / (slug + '.process.json'), result)
    return result


def finalize(processes):
    inventory = []
    missing = []
    for slug in SLUGS:
        out = ROOT / slug
        expected = [out / (slug + ext) for ext in ('.blend', '.glb', '.fbx')]
        expected += [out / 'metadata.json', out / 'renders' / 'hero.png', out / 'renders' / 'rear.png']
        files = []
        for path in expected:
            if not path.is_file() or path.stat().st_size <= 0:
                missing.append(path.relative_to(ROOT).as_posix())
            else:
                files.append(file_record(path))
        inventory.append({'slug': slug, 'files': files})
    finish = utc()
    failures = [p['slug'] for p in processes if p['returncode'] != 0]
    status = 'produced_unreviewed' if not failures and not missing and len(processes) == 4 else 'needs_attention'
    result = {
        'set': 'Set08', 'theme': 'Materials processing', 'status': status, 'review_status': 'deferred_by_user',
        'started_at_utc': START.isoformat(), 'finished_at_utc': finish.isoformat(),
        'started_at_kst': START.astimezone(KST).isoformat(), 'finished_at_kst': finish.astimezone(KST).isoformat(),
        'elapsed_seconds': round((finish - START).total_seconds(), 3),
        'timing_note': 'Production clock starts at the first explicit clock capture after initial brief/skill reads. Process times use perf_counter around subprocess.run.',
        'blender_process_seconds': round(sum(p['elapsed_seconds'] for p in processes), 3),
        'subprocess_returncodes': {p['slug']: p['returncode'] for p in processes},
        'processes': processes,
        'completion_checks': {'expected_file_count': 24, 'nonempty_file_count': sum(len(a['files']) for a in inventory),
                              'missing_or_empty_files': missing, 'failed_processes': failures,
                              'scope': 'Only process return codes and expected nonempty file presence.'},
        'review_deferred': ['generated preview inspection', 'fresh BLEND reopen', 'GLB/FBX reimport', 'geometry validation', 'UV validation', 'independent reviewer'],
        'blockers': failures + missing,
    }
    write_json(ROOT / 'STATUS.json', result)
    manifest = dict(result)
    manifest['assets'] = inventory
    manifest['inventory_note'] = 'Paths, bytes and SHA256 are inventory only, not content or visual validation.'
    manifest['source_and_logs'] = [file_record(ROOT / 'build.py'), file_record(ROOT / 'run_builds.py')]
    manifest['source_and_logs'] += [file_record(LOGS / (s + '.log')) for s in SLUGS if (LOGS / (s + '.log')).is_file()]
    manifest['source_and_logs'] += [file_record(LOGS / (s + '.process.json')) for s in SLUGS if (LOGS / (s + '.process.json')).is_file()]
    write_json(ROOT / 'delivery_manifest.json', manifest)
    lines = [
        '# Set08 production result', '',
        'Status: `' + status + '`. Review: `deferred_by_user`.', '',
        'Four original materials-processing assets were authored as named ordinary mesh components with bevels, a solid PBR palette and per-component UV layouts. ASSET and STUDIO are separate. The GLB/FBX export commands select only ASSET meshes.', '',
        '- Start UTC: ' + START.isoformat(), '- Start KST: ' + START.astimezone(KST).isoformat(),
        '- Finish UTC: ' + finish.isoformat(), '- Finish KST: ' + finish.astimezone(KST).isoformat(),
        '- Elapsed wall seconds: ' + str(result['elapsed_seconds']),
        '- Sum of Blender process seconds: ' + str(result['blender_process_seconds']),
        '- Timing starts at the first explicit clock capture, following initial brief and skill reads.', '',
        '| Asset | Process seconds | Actual return code |', '|---|---:|---:|',
    ]
    lines += ['| ' + p['slug'] + ' | ' + str(p['elapsed_seconds']) + ' | ' + str(p['returncode']) + ' |' for p in processes]
    lines += ['', 'Delivery paths are linked in [README.md](README.md); exact file bytes and SHA256 inventory are in [delivery_manifest.json](delivery_manifest.json). Source: [build.py](build.py), [run_builds.py](run_builds.py). Logs are under [logs/](logs/).', '',
              'Completion evidence: actual subprocess return codes and ' + str(result['completion_checks']['nonempty_file_count']) + '/24 expected nonempty files. Renders are actual Cycles studio renders at 960x960. They were generated but not opened or visually inspected.', '',
              'Per-component UVs were authored using angle-based projection with a 2.5% island margin. No UV, geometry, image, reopen or export roundtrip validation was run. No reviewer agents were used. The set remains unreviewed as explicitly requested.', '',
              'Known limitations: static meshes only; no rigging, animation, collision or LODs. Solid palette materials only; no surface textures. Reference fidelity, shading, UV quality, framing and export interchange remain deferred review items.', '',
              'External references: only the four main-supplied reference images and prompts in [REF/](REF/) were used as creative inputs. No online references or other sets were inspected or reused. No worker Git actions, installations or image generation were performed.', '',
              'Set frozen after production; waiting for the parent to commit the group and explicitly dispatch further work.', '']
    (ROOT / 'RESULT.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'status': status, 'nonempty_file_count': result['completion_checks']['nonempty_file_count'],
                      'subprocess_returncodes': result['subprocess_returncodes'], 'elapsed_seconds': result['elapsed_seconds'],
                      'blender_process_seconds': result['blender_process_seconds']}, indent=2), flush=True)
    return 0 if status == 'produced_unreviewed' else 1


if __name__ == '__main__':
    requested = sys.argv[1:]
    if requested and requested[0] == '--finalize':
        results = [json.loads((LOGS / (s + '.process.json')).read_text(encoding='utf-8')) for s in SLUGS]
        raise SystemExit(finalize(results))
    slugs = requested or SLUGS
    results = []
    for s in slugs:
        p = run(s)
        results.append(p)
        if p['returncode'] != 0:
            raise SystemExit(p['returncode'])
    if slugs == SLUGS:
        raise SystemExit(finalize(results))
