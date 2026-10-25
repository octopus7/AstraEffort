"""Finalize after human-equivalent tool image inspection has been recorded."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import sys,json,hashlib
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from validate import validate,png_info
from preview_pipeline import dump,sha

def main():
    # Fresh full verification is required; do not rely on a prior summary.
    validation=validate(False)
    inspection=json.loads((ROOT/'visual_inspection.json').read_text(encoding='utf-8'))
    assert inspection['inspected_image_count']==12
    assert all(r['passed'] and sha(ROOT/r['image'])==r['image_sha256'] for r in inspection['images'])
    overview=ROOT/'overview_half.png';overview_info=png_info(overview)
    assert (overview_info['width'],overview_info['height'])==(1560,1200)
    assert inspection['contact_sheet_inspected']
    manifest=json.loads((ROOT/'capture_manifest.json').read_text(encoding='utf-8'))
    manifest['contact_sheet']={'image':'overview_half.png','image_sha256':sha(overview),
        'size_px':[1560,1200],'assembly':'System.Drawing contact sheet of the six actual half previews; no scene imagery generation',
        'assembled_at_utc':datetime.fromtimestamp(overview.stat().st_mtime,timezone.utc).isoformat(),
        'sources':[c['image'] for c in manifest['captures'] if c['variant']=='half']}
    dump(ROOT/'capture_manifest.json',manifest)
    status=json.loads((ROOT/'STATUS.json').read_text(encoding='utf-8'))
    started=datetime.fromisoformat(status['started_at_utc']);finished=datetime.now(timezone.utc)
    elapsed=(finished-started).total_seconds()
    native_runs=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(ROOT.glob('native_build*.json'))]
    render_runs=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT/'logs').glob('render_timing_*.json'))]
    timing={'started_at_utc':started.isoformat(),'started_at_kst':started.astimezone(timezone(timedelta(hours=9))).isoformat(),
            'finished_at_utc':finished.isoformat(),'finished_at_kst':finished.astimezone(timezone(timedelta(hours=9))).isoformat(),
            'wall_seconds':elapsed,
            'successful_native_build_seconds':sum(r['elapsed_seconds'] for r in native_runs),
            'preview_pipeline_seconds':sum(r['elapsed_seconds'] for r in render_runs),
            'actual_render_seconds_including_corrective_renders':sum(r['render_seconds'] for r in render_runs),
            'surface_extraction_seconds_including_corrective_renders':sum(r['surface_seconds'] for r in render_runs),
            'actual_frames_rendered':sum(r['captures_this_run'] for r in render_runs),
            'delivered_frames':12,'final_validation_seconds':validation['elapsed_seconds'],
            'image_generation_seconds':0,'queue_wait_seconds':0,
            'timing_notes':['Tracked start is the first UTC clock reading after brief/helper preflight reads.',
                'Failed exploratory native builds and source-authoring time are included in wall time; their internal CPU time was not retained.',
                'Preview pipeline time overlaps actual render and surface extraction time; do not add these categories.',
                'Two isolated Blender processes ran sequentially in this batch; each used four threads. No queue runner was required.']}
    dump(ROOT/'timing.json',timing)
    status.update({'status':'ready_for_review','stage':'verified_and_visually_inspected',
        'finished_at_utc':timing['finished_at_utc'],'finished_at_kst':timing['finished_at_kst'],
        'elapsed_seconds':elapsed,'native_vox_count':12,'actual_preview_count':12,'contact_sheet_count':1,
        'validation_summary':'VOX150 parsing, source roundtrip, palette, dimensions/scale, reduced occupancy, 48 feature probes, native support connectivity, PNG CRC/zlib, paired camera settings and SHA256 all pass.',
        'visual_inspection':'All 12 delivered previews and contact sheet inspected with image tools.',
        'blockers':[],'fast_mode_claimed':False,'last_updated_at_utc':finished.isoformat()})
    dump(ROOT/'STATUS.json',status)
    rows=[]
    for r in validation['variants']:
        if r['variant']=='large':
            half=next(x for x in validation['variants'] if x['asset']==r['asset'] and x['variant']=='half')
            rows.append('| '+r['asset']+' | '+' × '.join(map(str,r['grid_size']))+' | '+' × '.join(map(str,half['grid_size']))+' | '+str(r['occupied_voxels'])+' / '+str(half['occupied_voxels'])+' | '+str(r['voxel_size_m'])+' / '+str(half['voxel_size_m'])+' |')
    report=f'''# Kitchen furnishings result

Ready for review: six independently authored furnishings, **12 native VOX 150 files and 12 actual 768 × 768 previews**, plus the labeled half-resolution contact sheet.

![Half-resolution furnishing overview](overview_half.png)

## Timing

- Tracked start UTC: {timing['started_at_utc']}; KST: {timing['started_at_kst']}.
- Finish UTC: {timing['finished_at_utc']}; KST: {timing['finished_at_kst']}.
- Elapsed wall: {elapsed:.3f} seconds. Preflight brief/helper reads preceded the first recorded UTC timestamp and are explicitly excluded from this tracked interval.
- Successful native build scripts: {timing['successful_native_build_seconds']:.3f} seconds.
- Preview pipelines: {timing['preview_pipeline_seconds']:.3f} seconds, including {timing['actual_render_seconds_including_corrective_renders']:.3f} seconds of actual Cycles rendering and {timing['surface_extraction_seconds_including_corrective_renders']:.3f} seconds of exact surface extraction. These categories overlap.
- {timing['actual_frames_rendered']} frames were actually rendered: 12 initial, then 8 corrected frames. The 12 final frames are delivered.
- Fresh final validation: {validation['elapsed_seconds']:.3f} seconds. Additional exploratory checks are documented in logs and included in wall time.
- No image generation, queue wait, package installation, Git operation or shared-scene use. Fast is not exposed by the dispatch API and is not claimed.

## Deliverables and native resolution

Each model is under `assets/SLUG/large/` and `assets/SLUG/half/`, containing `SLUG.vox`, `preview.png` and `metadata.json`.

| Model | Large grid | Half grid | Occupied voxels large / half | Cell size m large / half |
|---|---|---|---|---|
'''+ '\n'.join(rows)+f'''

Large longest grid axis is exactly 128, with all axes even. Half dimensions are exactly divided by two, cell size doubles and physical grid extents remain unchanged. Occupancy genuinely decreases. No half postprocessing or added palette shades were used.

## Verification and visual findings

`validation.json` records fresh parsing of all saved native files, exact authored occupancy/palette roundtrip, valid VOX 150, unique in-bounds coordinates, legal palette indices, scale relationships, 48 functional feature probes and physically connected supports. Each image passes 768 px dimensions, PNG CRC/decompression and capture/metadata SHA256 checks. Both variants use identical camera/light settings based on the saved large grid bounds.

All twelve final images were individually inspected with image tools; findings and their exact image hashes are in `visual_inspection.json`. Sink basin, shelf bays, handles, drying slots and unused knife slot remain empty and readable. All six silhouettes remain distinct at half resolution. The contact sheet is assembled only from actual half previews.

The finite correction pass fixed observed contact defects: island rail hooks meet their posts, the display bowl rests on its shelf, plates rest on a rack crossbar, and inserted knife ends reach slot floors. Initial failing support evidence and the original capture manifest remain in `logs/`. The sink and cart previews were retained unchanged. Connectivity is evidence for these intended assemblies; no unrelated parts were fused.

## Capture and provenance

`capture_manifest.json` records source VOX and PNG SHA256, reparse/render UTC timestamps, camera bounds/transform, orthographic scale, all lights, world settings and actual frame duration. Every render surface was created from the reopened VOX in memory using the read-only generic `build_surface` and `add_studio` helpers. No Blender scene or exchange mesh was saved. Rendering used Blender 4.5.12 LTS, Cycles CPU, four threads, 24 samples, denoising, AgX and RGB 8-bit PNG.

Source: `build.py` (pure `make_assets()`), `features.py`, `preview_pipeline.py`, `validate.py`, `support_check.py`, `repair_support.py`, `contact_sheet.ps1`, `finalize.py`; palette in `palette.json`. Audit files include `timing.json`, `STATUS.json`, `native_validation.json`, `validation.json`, `visual_inspection.json`, `frozen_file_hashes.json` and logs.

## Known limitations

- Static colored occupancy only; no animation, collision, rigging, UV textures or scene/exchange formats, as requested.
- Decorative one-voxel oak seams disappear at half resolution. Functional openings are preserved; this simplification is documented rather than patched.
- The common single studio view partly occludes the hutch mug and rear details. Saved-data probes cover hidden clearances; no claim of additional camera views is made.
- Opaque blue-gray color is used for the hutch back; no transparent glass simulation.
- A render-only studio plane provides shadows and is absent from every VOX asset.

## References

Binding local `../BRIEF.md`; read-only generic `../../_tools/API.md`, `voxelkit.py` and `blender_pipeline.py`. No external creative references or another batch's geometry were read or reused during production.
'''
    (ROOT/'RESULT.md').write_text(report,encoding='utf-8')
    plan=ROOT/'PLAN.md';plan.write_text(plan.read_text(encoding='utf-8').replace('- [ ]','- [x]'),encoding='utf-8')
    excluded={'frozen_file_hashes.json','hash_verification.json'}
    files=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded]
    frozen={'created_at_utc':datetime.now(timezone.utc).isoformat(),'algorithm':'SHA256',
            'excluded':['frozen_file_hashes.json (self)','hash_verification.json (post-freeze audit)','__pycache__'],
            'files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]}
    dump(ROOT/'frozen_file_hashes.json',frozen)
    checks=[{'path':f['path'],'passed':sha(ROOT/f['path'])==f['sha256']} for f in frozen['files']]
    assert all(c['passed'] for c in checks)
    dump(ROOT/'hash_verification.json',{'verified_at_utc':datetime.now(timezone.utc).isoformat(),
         'passed':True,'files_checked':len(checks),'manifest_sha256':sha(ROOT/'frozen_file_hashes.json'),'checks':checks})
    print(json.dumps({'status':'ready_for_review','elapsed_seconds':elapsed,'files_hashed':len(checks),
                      'vox':12,'previews':12,'actual_frames_rendered':timing['actual_frames_rendered']}),flush=True)

if __name__=='__main__':main()
