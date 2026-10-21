"""Preserve the current unvalidated private build after the user's stop request."""
import datetime, hashlib, json, shutil, zipfile
from pathlib import Path

R = Path(__file__).resolve().parent
ROOT = R.parents[3]
P = ROOT / 'Saved/Workers/MountainStation/ultra/Project'
C = R / 'Checkpoint'
C.mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name, data): (R / name).write_text(json.dumps(data, indent=2), encoding='utf-8')

baseline = json.loads((R / 'baseline_immutability.json').read_text())
actual = []
for folder in ['FirstDelivery', 'TexturePass']:
    for p in sorted((R.parent / folder).rglob('*')):
        if p.is_file():
            actual.append({'path': str(p).replace('\\', '/'), 'relative_path': str(p.relative_to(R.parent)), 'bytes': p.stat().st_size, 'sha256': sha(p)})
expected = baseline['files']
assert len(actual) == len(expected)
assert [(x['relative_path'], x['bytes'], x['sha256']) for x in actual] == [(x['relative_path'], x['bytes'], x['sha256']) for x in expected], 'Frozen baseline changed'
published = json.loads((R / 'baseline_packages.json').read_text())['packages']
assert all(sha(Path(x['published'])) == x['sha256'] for x in published), 'Published baseline changed'

files = sorted((P / 'Content/MountainStation/ultra').rglob('*.uasset')) + [P / 'Content/Maps/MountainStation_ultra.umap']
manifest = [{'path': p.relative_to(P).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in files]
archive = C / 'private_candidate_unvalidated.zip'
assert not archive.exists(), 'Do not overwrite a checkpoint'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in files: z.write(p, p.relative_to(P).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert set(z.namelist()) == {x['path'] for x in manifest}
    assert all(hashlib.sha256(z.read(x['path'])).hexdigest() == x['sha256'] for x in manifest)

timings = [json.loads(p.read_text()) for p in sorted(R.glob('timing_*.json'))]
for name in ['self_build_01.log', 'self_build_02.log', 'self_before_capture.log', 'self_before_capture_02.log']:
    p = P.parent / name
    if p.is_file(): shutil.copy2(p, C / name)
now = datetime.datetime.now(datetime.timezone.utc)
kst = now.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
status = json.loads((R / 'STATUS.json').read_text())
elapsed = (now - datetime.datetime.fromisoformat(status['started_at_utc'])).total_seconds()
blockers = [
    'Stopped at explicit user request; final UE validation, after screenshots, and publication were not performed.',
    'Known validation-script bug: improvement_checks.py treats static-mesh tangents as vertex colors (data[4]).',
    'Review/capture initialization needs guarded cleanup before enabling Python keep-alive.',
    'Soft-path material graph validation and post-capture package hash confirmation remain incomplete.'
]
status.update(status='needs_attention', stopped_by_user=True, finished_at_utc=now.isoformat(), finished_at_kst=kst.isoformat(), elapsed_seconds=elapsed,
              validation='Checkpoint ZIP CRC and every package SHA-256 verified; 201 frozen evidence files and 130 published baseline packages unchanged. Candidate scene is NOT validated or published.', blockers=blockers)
write('STATUS.json', status)
write('Checkpoint/manifest.json', {'recorded_at_utc': now.isoformat(), 'validated': False, 'published': False,
    'archive': archive.name, 'archive_sha256': sha(archive), 'package_count': len(files), 'files': manifest,
    'immutable_baseline_files_verified': len(expected), 'published_baseline_packages_verified': len(published),
    'timings': timings, 'mutex_wait_seconds': sum(t['wait_seconds'] for t in timings),
    'ue_execution_seconds': sum(t['execution_seconds'] for t in timings), 'elapsed_wall_seconds': elapsed})
result = f'''# MountainStation / ultra — stopped checkpoint

The user explicitly requested stopping and committing the current state. No further scene work or UE validation was started after that request. This is an unfinished checkpoint, not a validated delivery.

- Start: {status['started_at_utc']} UTC / {status['started_at_kst']} KST.
- Stop record: {now.isoformat()} UTC / {kst.isoformat()} KST.
- Total elapsed wall time: {elapsed:.3f} seconds.
- Recorded UE mutex wait: {sum(t['wait_seconds'] for t in timings):.3f} seconds; UE execution: {sum(t['execution_seconds'] for t in timings):.3f} seconds, including the rejected first capture attempt.
- Last private build exited 0. No private UE process remained when checked after the stop request.

## Preserved work

Source artwork and scripts contain the footpath, ballast, rail-profile, crossing and tunnel-light changes described in DESIGN.md. The last saved private candidate (137 packages) is preserved in [Checkpoint/private_candidate_unvalidated.zip](Checkpoint/private_candidate_unvalidated.zip), with per-package SHA-256 and archive hash in [Checkpoint/manifest.json](Checkpoint/manifest.json). Archive CRC and every archived package hash were verified. Extract only into an owned private project when resuming; do not copy directly into the shared project without final validation.

The shared map and 130 published packages remain the TexturePass baseline from commit 3e13e569b0e8725f4a9faaeee8e3d13ddf7b5737. All 201 FirstDelivery/TexturePass evidence files were hash-verified unchanged. This checkpoint does not publish the candidate scene.

## Evidence and limitations

CPU source diagnostics and UV reports are retained. They do not establish actual UE runtime or final imported-mesh correctness. Screenshots/before_fixed contains six actual baseline UE captures. Screenshots/before_current is a rejected sky-only attempt, recorded in capture_retry_record.json; it is not valid scene evidence. No after screenshots exist.

Final imported UV/dependency/world-partition checks, runtime traversal, scene visual review and candidate publication remain outstanding. Technical audit found these unresolved issues; no fixes were made after the stop request:

- improvement_checks.py reads ProceduralMeshLibrary result index 4 as colors, but that field contains tangents and would raise. Use a supported imported-color API on resume.
- Guard review/capture initialization and cleanup to avoid leaving a private editor alive after initialization errors.
- Validate the new soft-path material graph and confirm package hashes after capture and before publication.

No new generated images or external art references were used in this pass. Existing owned TexturePass textures are reused. Token usage is unavailable here. No claim of completed scene validation is made.
'''
(R / 'RESULT.md').write_text(result, encoding='utf-8')
print(json.dumps({'checkpoint_packages': len(files), 'archive_bytes': archive.stat().st_size, 'baseline_files_unchanged': len(expected), 'published_packages_unchanged': len(published), 'stopped_at_utc': now.isoformat()}))
