"""Write the finite cross-review after image inspection and read-only checks."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib
ROOT=Path(__file__).resolve().parent
TARGET=ROOT.parents[1]/'countertop'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
check=json.loads((ROOT/'countertop_checks.json').read_text(encoding='utf-8'))
assert check['passed']
started=datetime.fromisoformat('2026-10-25T05:38:02+00:00')
finished=datetime.now(timezone.utc)
notes={
 'stand_mixer':{
   'large':'Mixer head, post, deep open bowl, right loop handle and working space around the beater are distinct and unclipped.',
   'half':'Bowl cavity, handle hole and clearance beside the beater remain visible. Larger voxel steps do not obscure the mixer silhouette.'},
 'espresso_machine':{
   'large':'Open cup bay, mug, right steam wand, drip slats and control face read as an espresso machine. Portafilter grip overlaps the cup in projection, consistent with the common camera.',
   'half':'Cup bay, cup loop and slats remain distinct; chunky controls preserve readability. Native checks confirm the cup cavity and handle remain empty.'},
 'toaster':{
   'large':'Two top slots, rear toast slice, side lever and front controls are clearly readable with complete framing.',
   'half':'Both slots remain open around the toast/end gap. Lever and cream body preserve the toaster identity; reduced corner stepping is expected.'},
 'blender':{
   'large':'Blue-gray jug, cream lid, capacity marks and large handle loop are readable. Opaque glass intentionally hides the interior.',
   'half':'Handle opening remains visible; lid, jug and motor base remain separate silhouette features. Hidden jug cavity is confirmed from native occupancy.'},
 'stock_pot':{
   'large':'Deep bowl, complete visible rim and two cream handle loops are clear. Dark interior rectangles are occupied dark-metal mounts, independently checked at saved coordinates.',
   'half':'The bowl and both handle loops remain open. The visible wall is continuous and the previously documented handle-cutter puncture is not present in these final files.'},
 'frying_pan':{
   'large':'Open nonstick bowl, metal rim, connected neck and oak-inset handle are readable. Hanging hole is open; framing includes the full handle.',
   'half':'Bowl remains hollow, hanging hole survives and neck remains visibly connected. Stout handle and stepped interior are intentional low-resolution geometry.'},
 'cutting_board_knife':{
   'large':'Oak board, juice groove, hanging tab and resting chef knife are distinct. Knife edge and rivets remain legible without clipping.',
   'half':'Board hole and groove persist; blade, guard and handle remain identifiable. Fine grain and edge details simplify as documented.'},
}
images=[]
for c in check['checks']:
    assert sha(TARGET/c['image'])==c['image_sha256']
    images.append({'asset':c['asset'],'variant':c['variant'],'image':c['image'],
        'sha256':c['image_sha256'],'inspected_with':'tools.view_image','passed':True,
        'observations':notes[c['asset']][c['variant']]})
evidence=['RESULT.md','STATUS.json','validation.json','capture_manifest.json','frozen_file_hashes.json','visual_inspection.json','preview_pipeline.py']
limits=[
 'One standardized three-quarter view per variant; no new views, target renders, rebuilds or full development-suite runs were performed.',
 'Opaque blue-gray glass intentionally conceals the blender interior; saved native samples confirm the empty cavity.',
 'Fine wires, knife edges and handles are stout to survive reduction; stair stepping and detail simplification are expected native voxel characteristics.',
 'Owner full authored-grid roundtrip and original 66 feature probes were assessed through frozen evidence. This independent audit reparsed natives, verified exact saved-large to saved-half reduction and rechecked 32 critical empty volumes without importing target authoring code.',
]
result={'reviewer_batch':'furnishings','target_batch':'countertop','review_mode':'explicitly assigned read-only same-kitchen cross-review',
    'started_at_utc':started.isoformat(),'started_at_kst':started.astimezone(timezone(timedelta(hours=9))).isoformat(),
    'finished_at_utc':finished.isoformat(),'finished_at_kst':finished.astimezone(timezone(timedelta(hours=9))).isoformat(),
    'elapsed_seconds':(finished-started).total_seconds(),
    'spec_compliance_verdict':'pass','visual_technical_quality_verdict':'pass',
    'blocking_findings':[],'nonblocking_findings':[],
    'summary':'Seven required models, fourteen native/render pairs and the labeled contact sheet meet the reviewed brief. No change is required.',
    'audit':{'frozen_files_verified':check['frozen_files_verified'],'native_files':14,'primary_previews_inspected':14,
        'critical_empty_volume_checks':len(check['critical_open_volume_checks']),'exact_native_half_reductions':7,
        'matched_camera_light_pairs':7,'png_crc_and_decompression_checks':14,'forbidden_outputs':0,
        'target_modified':False,'target_code_executed':False,'own_frozen_production_unchanged':True},
    'evidence':[{'path':p,'sha256':sha(TARGET/p)} for p in evidence],
    'independent_check_file':'countertop_checks.json','independent_check_sha256':sha(ROOT/'countertop_checks.json'),
    'images':images,'contact_sheet':{'image':'overview_half.png','sha256':sha(TARGET/'overview_half.png'),'inspected':True,
        'observations':'All seven actual half previews are labeled, captions are legible, and the title/footer are unclipped.'},
    'known_limits':limits,
    'resolved_visual_question':'Dark stock-pot interior patches are palette index 8 at large-grid [35,48,64] and [92,48,64], not empty wall punctures.'}
(ROOT/'countertop_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
rows=[]
for slug,variants in notes.items():rows.append('| '+slug+' | '+variants['large']+' | '+variants['half']+' |')
md=f'''# Independent countertop review

**Spec compliance: PASS. Visual and technical quality: PASS.** No blocking or nonblocking defect requiring a change was found in the final files.

Reviewer: furnishings worker. Target: `voxel/kitchen/countertop`, explicitly authorized for read-only same-kitchen review. Target files and the reviewer's frozen production files were left unchanged.

Review start: {result['started_at_utc']} UTC / {result['started_at_kst']} KST.  
Review finish: {result['finished_at_utc']} UTC / {result['finished_at_kst']} KST.  
Elapsed tracked wall: {result['elapsed_seconds']:.3f} seconds; lightweight native/hash audit: {check['elapsed_seconds']:.3f} seconds. The first timestamp was recorded just after the initial brief/evidence read.

## Spec compliance

- Exact seven slugs and all 14 VOX/PNG pairs are present; no forbidden scene or mesh format is present.
- All 73 frozen target file hashes and byte lengths match. Fourteen natives parse as VOX150 with legal palette/coordinates and nonzero occupancy.
- Large grids have even axes and longest axis 128; half dimensions are exactly divided by two, their cell size doubles and physical grid extents match. Saved half occupancy exactly equals the prescribed reduction of saved large occupancy and is smaller.
- All 14 PNGs pass 768 × 768 RGB8 dimensions, complete PNG CRC/decompression and metadata/capture hashes.
- All seven capture pairs have identical camera, lighting and render settings: Cycles CPU, four threads, 24 samples, denoising and AgX. The inspected pipeline passes reopened native grids to the shared surface builder and does not save meshes/scenes.
- Independently rechecked 32 empty native volumes covering mixer bowl/working gap/handle, espresso bay/cup/handle, toaster slots, blender jug/handle, pot bowl/handles, pan bowl/hanging hole and board hanging hole, including half variants.
- The owner's frozen validation reports 66 feature probes and authored-grid roundtrips; that development suite was not rerun. The common palette, household dimensions, production timings and visual-inspection evidence are coherent with the brief.

## Visual and technical quality

All fourteen final primary PNGs were opened individually with image tools, followed by the contact sheet. Exact inspected image hashes are recorded in `countertop_review.json`.

| Asset | Large preview observation | Half preview observation |
|---|---|---|
'''+ '\n'.join(rows)+'''

The dark rectangular patches visible inside the stock pot were investigated rather than assumed to be holes. Saved occupancy at `[35,48,64]` and `[92,48,64]` is palette 8, consistent with the dark metal mounts. The final wall repair evidence and current images are consistent; no additional correction is requested.

## Limits

'''+ '\n'.join('- '+s for s in limits)+'''

Independent audit source and full checks are in `check_countertop.py` and `countertop_checks.json`. No geometry was copied or reused, no target code was executed, no target render was created, and no target file or frozen furnishings production file was modified.
'''
(ROOT/'countertop_review.md').write_text(md,encoding='utf-8')
print(json.dumps({'spec_compliance':'pass','visual_technical_quality':'pass','inspected_previews':14,
    'elapsed_seconds':result['elapsed_seconds'],'findings':0}))
