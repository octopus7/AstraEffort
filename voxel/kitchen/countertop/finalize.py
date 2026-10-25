"""Freeze final native/render evidence after all actual images have been inspected."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse, hashlib, json, sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from validate import validate, EXPECTED

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')

def verify_frozen():
    frozen=read(ROOT/'frozen_file_hashes.json')
    for record in frozen['files']:
        p=ROOT/record['path']
        assert p.is_file(),record['path']
        assert p.stat().st_size==record['bytes'] and sha(p)==record['sha256'],record['path']
    print(json.dumps({'frozen_integrity_passed':True,'checked_files':len(frozen['files'])}))

def finish():
    validation=validate(True)
    inspection=read(ROOT/'visual_inspection.json')
    assert inspection['complete'] and len(inspection['images'])==14
    assert {(r['asset'],r['variant']) for r in inspection['images']}=={(s,v) for s in EXPECTED for v in ('large','half')}
    for record in inspection['images']:
        assert record['inspected'] and not record['unresolved_defects']
        assert sha(ROOT/record['path'])==record['sha256']
    overview=read(ROOT/'overview_half.json')
    assert overview['source_count']==7 and sha(ROOT/'overview_half.png')==overview['sha256']
    for record in overview['sources']:
        assert sha(ROOT/record['path'])==record['source_sha256']
    assert inspection['contact_sheet_inspected'] is True
    status=read(ROOT/'STATUS.json')
    started=datetime.fromisoformat(status['started_at_utc'])
    finished=datetime.now(timezone.utc)
    kst=timezone(timedelta(hours=9))
    native_passes=[read(p) for p in (ROOT/'logs').glob('native_*.json')]
    render_passes=[read(p) for p in (ROOT/'logs').glob('render_*.json')]
    builds=[read(p) for p in (ROOT/'logs').glob('pipeline_*.json') if '--native-only' in read(p)['arguments']]
    timing={
        'started_at_utc':started.isoformat(),'started_at_kst':started.astimezone(kst).isoformat(),
        'finished_at_utc':finished.isoformat(),'finished_at_kst':finished.astimezone(kst).isoformat(),
        'wall_seconds':(finished-started).total_seconds(),
        'prebuild_wall_seconds':(min(datetime.fromisoformat(n['started_at_utc']) for n in native_passes)-started).total_seconds(),
        'native_build_seconds':sum(n['elapsed_seconds'] for n in native_passes),
        'grid_generation_seconds':sum(b['grid_generation_seconds'] for b in builds),
        'native_build_pipeline_seconds':sum(b['elapsed_seconds'] for b in builds),
        'render_pipeline_seconds':sum(r['elapsed_seconds'] for r in render_passes),
        'temporary_surface_and_studio_seconds':sum(r['surface_build_seconds'] for r in render_passes),
        'actual_render_seconds':sum(r['render_seconds'] for r in render_passes),
        'render_calls_including_superseded_previews':sum(r['captures_completed'] for r in render_passes),
        'native_passes':native_passes,
        'render_passes':render_passes,
        'final_validation_seconds':validation['elapsed_seconds'],
        'contact_sheet_seconds':overview['elapsed_seconds'],
        'notes':['Start is the first sampled production timestamp after reading the binding brief.',
                 'Prebuild wall includes planning, source authoring and initial contract verification.',
                 'Image inspection and source/evidence preparation overlapped the render pipeline.',
                 'Final validation timing is the fresh complete validation, not a claim that earlier diagnostics were separately timed.'],
    }
    write(ROOT/'timing.json',timing)
    status.update({
        'status':'ready_for_review','stage':'native files, rendered previews, visual inspection and frozen evidence complete',
        'finished_at_utc':timing['finished_at_utc'],'finished_at_kst':timing['finished_at_kst'],'elapsed_seconds':timing['wall_seconds'],
        'validation':{'passed':True,'native_count':14,'actual_preview_count':14,'contact_sheet_count':1,'native_feature_probes':sum(len(c['features']) for c in validation['checks']),'all_14_previews_inspected':True,'forbidden_outputs':0},
        'blockers':[], 'pending':'Coordinator-assigned read-only same-kitchen cross-review',
    })
    write(ROOT/'STATUS.json',status)
    lines=[
        '# Countertop kitchen voxel result','',
        'Seven original models are ready for review: **14 native VOX150 files, 14 actual 768x768 PNG previews, and one labeled half-size contact sheet**. No mesh or Blender scene files were produced.','',
        f"Production start: {timing['started_at_utc']} UTC / {timing['started_at_kst']} KST.  ",
        f"Production finish: {timing['finished_at_utc']} UTC / {timing['finished_at_kst']} KST.  ",
        f"Elapsed wall time: **{timing['wall_seconds']:.3f} seconds**.",'',
        '| Phase | Actual seconds |','|---|---:|',
        f"| Prebuild wall, including authoring | {timing['prebuild_wall_seconds']:.3f} |",
        f"| Grid generation and native build pipeline | {timing['native_build_pipeline_seconds']:.3f} |",
        f"| Render pipeline | {timing['render_pipeline_seconds']:.3f} |",
        f"| Temporary surface/studio construction within render pipeline | {timing['temporary_surface_and_studio_seconds']:.3f} |",
        f"| Actual Cycles render calls within render pipeline | {timing['actual_render_seconds']:.3f} |",
        f"| Final full validation | {timing['final_validation_seconds']:.3f} |",
        f"| Contact-sheet assembly | {timing['contact_sheet_seconds']:.3f} |",'',
        'Inspection and evidence preparation overlapped rendering; phase durations are not additive wall time. Earlier untimed diagnostic overhead remains included in wall time.','',
        f"The recorded render time includes {timing['render_calls_including_superseded_previews']} actual calls: 14 delivered previews plus two superseded pot previews from the visual defect correction.",'',
        '## Delivered native models','',
        '| Model | Large grid | Half grid | Large / half occupied cells | Grid extents (m) |','|---|---|---|---:|---|',
    ]
    by={(c['asset'],c['variant']):c for c in validation['checks']}
    for slug in EXPECTED:
        a,b=by[(slug,'large')],by[(slug,'half')]
        dims=lambda v:' x '.join(str(n) for n in v)
        lines.append(f"| {slug} | {dims(a['grid_size'])} | {dims(b['grid_size'])} | {a['occupied_voxels']:,} / {b['occupied_voxels']:,} | {' x '.join(f'{n:.4f}' for n in a['grid_extents_m'])} |")
    lines += [
        '', 'Paths: `assets/<slug>/{large,half}/<slug>.vox`, `preview.png`, and `metadata.json`.',
        '', '![Actual half-resolution countertop contact sheet](overview_half.png)', '',
        '## Validation and visual evidence','',
        f"Fresh `validate.py` passes all 14 native roundtrips and {status['validation']['native_feature_probes']} feature probes from reopened files. It checks VOX150/chunk validity, unique in-grid coordinates, common palette, nonzero occupancy, exact half dimensions, reduced native occupancy, doubled cell size, identical physical extents, 768px PNG headers, native/PNG hashes, camera parity and render settings.",
        '', 'Functional void probes cover mixer bowl/handle/working clearance, espresso cup bay/cup/cup handle, both toaster slots, blender jug/handle, stock-pot bowl/handles, pan bowl/hanging hole and cutting-board hanging hole. No half postprocess was required.',
        '', 'Every render uses the reopened VOX as surface input. Rendering used Blender 4.5, Cycles CPU, 24 samples, denoising, AgX, four fixed threads, and the same large-native camera bounds for each pair. The studio floor is temporary render geometry and is absent from native deliverables.',
        '', 'All 14 PNG previews were individually inspected using the image-viewing tool. Full-object framing, intended silhouette, retained half-size features and native open spaces were reviewed; the contact sheet was inspected separately. Findings are recorded in `visual_inspection.json`; timestamps, camera/lights and SHA256 evidence are in `capture_manifest.json`.',
        '', '## Limitations and provenance','',
        '- Glass is deliberately opaque blue-gray. No transparency, texture, animation, rigging or collision is implied.',
        '- Fine wire, knife edge and control thicknesses are exaggerated for half-size voxel readability. A single common three-quarter camera is supplied for each variant.',
        '- Blender ran headlessly; no GUI review is claimed. Hidden interiors were checked in native data, not by extra camera renders.',
        '- The toaster slot probe was moved from the rounded wall boundary to the actual gap center after a saved-data diagnostic; no geometry was changed for that probe.',
        '- Visual inspection exposed two small stock-pot wall punctures caused by the handle cutter. Saved-data regression probes failed before the fix; preserving the vessel shell corrected both sizes. Both pot previews were then rendered again and re-inspected.',
        '- The kitchen brief and read-only generic voxel utilities are the only references. No external images, other batch geometry or generated scene imagery were used.',
        '', 'Source: `build.py` (`make_assets()` is pure), `preview_pipeline.py`, `validate.py`, `make_overview.ps1`. Evidence: `validation.json`, `capture_manifest.json`, `visual_inspection.json`, `timing.json`, `frozen_file_hashes.json`, `logs/`. Read-only frozen-integrity recheck: `finalize.py --verify-frozen`.',
    ]
    (ROOT/'RESULT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    plan=(ROOT/'PLAN.md').read_text(encoding='utf-8').replace('- [ ]','- [x]')
    (ROOT/'PLAN.md').write_text(plan,encoding='utf-8')
    files=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or p.name=='frozen_file_hashes.json':continue
        if p.suffix.lower() in {'.vox','.png','.json','.md','.py','.ps1','.log'}:
            files.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    write(ROOT/'frozen_file_hashes.json',{'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'All current batch deliverables, source and evidence; later assigned cross-review records are separate. No self-hash or interpreter cache.','files':files})
    verify_frozen()
    print(json.dumps({'status':'ready_for_review','wall_seconds':timing['wall_seconds'],'actual_renders':14,'feature_probes':status['validation']['native_feature_probes']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify-frozen',action='store_true');args=parser.parse_args()
    verify_frozen() if args.verify_frozen else finish()
