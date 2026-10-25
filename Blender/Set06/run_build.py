"""Run four isolated Blender authoring processes and record inventory only."""
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
BLENDER = Path(r'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe')
SLUGS = ['tree_transplanter', 'nursery_carrier_robot', 'arched_nursery_greenhouse', 'forest_watchtower']
KST = timezone(timedelta(hours=9))


def iso():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def expected(slug):
    return [ROOT / slug / (slug + ext) for ext in ('.blend', '.glb', '.fbx')] + [
        ROOT / slug / 'metadata.json', ROOT / slug / 'renders' / 'hero.png', ROOT / slug / 'renders' / 'rear.png']


def file_record(path):
    return {'path': path.relative_to(REPO).as_posix(), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    status = json.loads((ROOT / 'STATUS.json').read_text(encoding='utf-8-sig'))
    recorded_start = datetime.fromisoformat(status['started_at_utc'])
    (ROOT / 'logs').mkdir(exist_ok=True)
    records = []
    for slug in SLUGS:
        log = ROOT / 'logs' / (slug + '.log')
        command = [str(BLENDER), '--background', '--factory-startup', '--threads', '4', '--python-exit-code', '1',
                   '--python', str(ROOT / 'build.py'), '--', slug]
        began = iso()
        monotonic_start = time.perf_counter()
        print(json.dumps({'event': 'process_start', 'asset': slug, 'at_utc': began}), flush=True)
        with log.open('w', encoding='utf-8') as output:
            result = subprocess.run(command, cwd=str(ROOT), stdout=output, stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        elapsed = time.perf_counter() - monotonic_start
        ended = iso()
        presence = [{'path': p.relative_to(REPO).as_posix(), 'exists': p.exists(),
                     'bytes': p.stat().st_size if p.exists() else 0} for p in expected(slug)]
        record = {'asset': slug, 'command': command, 'started_at_utc': began, 'finished_at_utc': ended,
                  'process_elapsed_seconds': elapsed, 'returncode': result.returncode,
                  'log': log.relative_to(REPO).as_posix(), 'expected_file_presence': presence}
        records.append(record)
        write_json(ROOT / 'process_records.json', records)
        print(json.dumps({'event': 'process_end', 'asset': slug, 'returncode': result.returncode,
                          'seconds': elapsed, 'expected_nonempty': all(p['bytes'] > 0 for p in presence)}), flush=True)
        if result.returncode != 0 or not all(p['bytes'] > 0 for p in presence):
            status.update({'status': 'needs_attention', 'blockers': [f'{slug}: process or expected-file production failure'],
                           'process_records': records})
            write_json(ROOT / 'STATUS.json', status)
            raise SystemExit(1)
    ended = datetime.now(timezone.utc)
    elapsed = (ended - recorded_start).total_seconds()
    total_process = sum(r['process_elapsed_seconds'] for r in records)
    status.update({'status': 'produced_unreviewed', 'review_status': 'deferred_by_user',
                   'finished_at_utc': ended.isoformat(), 'finished_at_kst': ended.astimezone(KST).isoformat(),
                   'elapsed_seconds': elapsed, 'blender_process_seconds_total': total_process,
                   'subprocess_returncodes': {r['asset']: r['returncode'] for r in records},
                   'presence_summary': 'All 24 required per-asset files exist and are nonempty.',
                   'review_summary': 'Only actual subprocess return codes and expected nonempty file presence checked. No generated render opened; no reopen/reimport or geometry/UV validator run.',
                   'blockers': [], 'frozen': True})
    write_json(ROOT / 'STATUS.json', status)
    rows = '\n'.join(f"| `{r['asset']}` | {r['returncode']} | {r['process_elapsed_seconds']:.3f} |" for r in records)
    result_text = f'''# Set06 — Forestry care

Status: **produced_unreviewed**. Review: **deferred_by_user**.

Four original ordinary rounded mesh assets were produced in separate Blender 4.5.12 background processes. Each asset has an editable named-parts BLEND, selected-geometry GLB and FBX, metadata and actual 960 × 960 neutral-studio hero/rear renders. ASSET and STUDIO are separate collections. All authoring and delivered outputs stay in `Blender/Set06`; supplied `REF/` remains read-only.

Recorded production start after brief/reference intake: {status['started_at_utc']} UTC / {status['started_at_kst']} KST. Intake duration was not recorded or invented.

Finish: {status['finished_at_utc']} UTC / {status['finished_at_kst']} KST.

Elapsed recorded wall time: **{elapsed:.3f} seconds**. Sum of four measured Blender subprocess durations: **{total_process:.3f} seconds**.

| Asset | Actual return code | Blender seconds |
|---|---:|---:|
{rows}

Delivery paths are linked in [README.md](README.md); exact bytes and SHA256 inventory are in [delivery_manifest.json](delivery_manifest.json). Commands, actual UTC process intervals and expected-file presence are in [process_records.json](process_records.json). Build source: [build.py](build.py), runner: [run_build.py](run_build.py).

Only actual subprocess completion and 24 expected nonempty file paths were checked. SHA256 recording is inventory, not validation. Generated previews were not opened. No fresh BLEND reopen, GLB/FBX reimport, geometry/UV validator or reviewer agent was used.

Production choices: original geometry inspired only by the four assigned references; pine/cream/terracotta solid PBR palette; per-component UV unwrap; softened functional forms. The greenhouse has architectural floor/foundation and the lookout has individual structural footings; no shared display slab is included in exports.

Known limitations: visual quality, framing, topology, UV quality, material/export fidelity and roundtrips remain unreviewed. Static meshes have no rig, animation, collision or LODs. Transmissive glazing may require engine-specific material adjustment; FBX transmission fidelity is unreviewed. Authored measurements in metadata are production measurements, not independent validation evidence.

References: main-supplied original concept PNGs and prompts in [local REF](REF/), retained at `REF/Set06` as well. No external creative resources or other set assets were read or reused. No image generation, installs, shared live Blender mutations, Git operations or extra agents were used by this worker.

Workflow ruling: the explicit user instruction to defer review overrides generic review/test/reviewer/commit steps in process skills. The supplied set plan and worker brief govern this production. Outputs are now frozen awaiting parent integration and the next explicit dispatch.
'''
    (ROOT / 'RESULT.md').write_text(result_text, encoding='utf-8')
    assets = [{'slug': slug, 'files': [file_record(p) for p in expected(slug)]} for slug in SLUGS]
    supporting = [ROOT / 'build.py', ROOT / 'run_build.py', ROOT / 'README.md', ROOT / 'RESULT.md', ROOT / 'STATUS.json',
                  ROOT / 'process_records.json'] + [ROOT / 'logs' / (slug + '.log') for slug in SLUGS]
    manifest = {'set': 'Set06', 'theme': 'Forestry care', 'status': 'produced_unreviewed', 'review_status': 'deferred_by_user',
                'started_at_utc': status['started_at_utc'], 'started_at_kst': status['started_at_kst'],
                'finished_at_utc': status['finished_at_utc'], 'finished_at_kst': status['finished_at_kst'],
                'elapsed_seconds': elapsed, 'blender_process_seconds_total': total_process,
                'checks_performed': ['Actual subprocess return code', 'Expected file exists and is nonempty'],
                'inventory_note': 'Bytes and SHA256 are inventory only. Manifest excludes its own hash and main-owned REF files.',
                'deferred_checks': ['Visual inspection', 'BLEND reopen', 'GLB/FBX reimport', 'Geometry validation', 'UV validation', 'Reviewer agents'],
                'processes': records, 'assets': assets, 'supporting_files': [file_record(p) for p in supporting]}
    write_json(ROOT / 'delivery_manifest.json', manifest)
    print(json.dumps({'event': 'set_produced', 'set': 'Set06', 'status': 'produced_unreviewed',
                      'elapsed_seconds': elapsed, 'process_seconds': total_process, 'asset_count': 4, 'expected_files': 24}), flush=True)


if __name__ == '__main__':
    main()
