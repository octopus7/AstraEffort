"""Write the completed independent review in the reviewer's owned directory."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json

OUT = Path(__file__).resolve().parent
TARGET = OUT.parent.parent / 'furnishings'
check = json.loads((OUT/'furnishings_native_check.json').read_text(encoding='utf-8'))
assert check['passed']
start = datetime.fromisoformat('2026-10-25T05:37:38+00:00')
finish = datetime.now(timezone.utc)
kst = timezone(timedelta(hours=9))
notes = {
    'sink_cabinet': {
        'large': 'Deep basin is visibly empty; faucet stands over it and both cabinet pulls project with clear gaps. Sage panels and cream top are distinct, with no cropping.',
        'half': 'Basin, tap clearance and pull openings survive. Chunkier corner steps preserve the cabinet identity and there is no visible detached part.'},
    'kitchen_island': {
        'large': 'Broad oak top, front storage and open right shelf identify the island. Side rail ends visibly meet the supporting posts, with the cloth hanging from the rail.',
        'half': 'Side shelf bays and rail opening remain readable. Decorative plank seams on the top disappear as documented; the work surface and supports remain coherent.'},
    'dish_cabinet': {
        'large': 'Display plates sit on the lower oak stands and the upper bowl rests on its shelf. Open shelf space is clear. The upper-right mug is partly hidden by the cabinet side and camera.',
        'half': 'Tall hutch, lower cupboard and two shelf bays stay distinct. Bowl and plate contours become chunky, while the supported arrangement remains readable; mug occlusion remains.'},
    'kitchen_cart': {
        'large': 'Caster wheels connect to their stems, shelves span the upright posts, and the towel stack sits on the lower shelf. Drawer pull and top transport bar are identifiable.',
        'half': 'Caster, shelf and drawer silhouettes survive. Open shelf bays and pull clearance remain; thin top inlay lines simplify without obscuring the cart.'},
    'dish_drying_rack': {
        'large': 'Three plates are visibly separated, with lower support bars beneath them. Divider loops, draining gaps, hollow utensil cup and tray handle are clear.',
        'half': 'All three plates remain separated; open slots, cup top and tray handle remain visible. Coarser plate stepping is consistent with the true lower resolution.'},
    'knife_block': {
        'large': 'Three differently raised knife handles and exposed blade portions are distinct, and the unused front slot is visibly empty. No detached blade is apparent.',
        'half': 'The three knife silhouettes remain separate, the front slot stays hollow and the sloped oak body retains its stepped form. Native connectivity corroborates hidden blade contact.'},
}
times = {slug:'2026-10-25T05:38:11+00:00' for slug in ('sink_cabinet','kitchen_island')}
times.update({slug:'2026-10-25T05:38:16+00:00' for slug in ('dish_cabinet','kitchen_cart')})
times.update({slug:'2026-10-25T05:38:21+00:00' for slug in ('dish_drying_rack','knife_block')})
images = []
for r in check['records']:
    actual = hashlib.sha256((TARGET/r['image']).read_bytes()).hexdigest()
    assert actual == r['image_sha256']
    images.append({'asset':r['asset'],'variant':r['variant'],'image':r['image'],
                   'sha256':actual,'inspected_at_utc':times[r['asset']],
                   'method':'Direct image-tool inspection of the final primary 768px PNG',
                   'verdict':'pass','observations':notes[r['asset']][r['variant']]})
limitations = [
    {'asset':'dish_cabinet','detail':'The common camera partly occludes the upper-right mug; its cavity is covered by the saved-native probe, not an additional view.'},
    {'asset':'kitchen_island, kitchen_cart','detail':'Thin decorative oak top seams disappear at half size. This documented simplification does not close a functional opening.'},
    {'asset':'all','detail':'Single-view inspection and integer face connectivity do not establish mechanical strength or animation behavior; these static colored voxel models do not claim either.'},
    {'asset':'all','detail':'The target source-to-authored roundtrip claim was read in its validated evidence, not rerun. This review independently checked saved-native reduction, palette, dimensions/scales, supports, probe volumes, images and hashes without executing target code.'},
]
report = {
    'reviewer':'appliances worker','target':'voxel/kitchen/furnishings','review_mode':'independent read-only same-kitchen cross-review',
    'started_at_utc':start.isoformat(),'finished_at_utc':finish.isoformat(),
    'started_at_kst':start.astimezone(kst).isoformat(),'finished_at_kst':finish.astimezone(kst).isoformat(),
    'elapsed_seconds':(finish-start).total_seconds(),
    'start_definition':'First recorded review clock sample after the initial brief/evidence read.',
    'spec_compliance':{'verdict':'pass','blocking_findings':[],
        'summary':'All six exact slugs, twelve native files, twelve 768px final previews and required evidence are present. Large/half dimensions, doubled cell scale, common palette, exact saved-grid reduction and paired render settings meet the brief.'},
    'visual_technical_quality':{'verdict':'pass','blocking_findings':[],
        'summary':'All twelve final previews directly inspected. Models remain distinct at half resolution and functional openings remain readable. All twelve saved native models independently form one six-neighbor connected assembly; 48 feature probes pass.'},
    'findings_requiring_changes':[], 'known_limits':limitations,
    'native_check_file':'furnishings_native_check.json','native_check_sha256':hashlib.sha256((OUT/'furnishings_native_check.json').read_bytes()).hexdigest(),
    'frozen_target_manifest_sha256':check['target_frozen_manifest_sha256'],
    'frozen_target_files_verified':check['frozen_files_verified'],'inspected_previews':images,
    'contact_sheet':{'image':'overview_half.png','inspected_at_utc':'2026-10-25T05:39:19+00:00',
        'sha256':hashlib.sha256((TARGET/'overview_half.png').read_bytes()).hexdigest(),
        'observations':'Six actual half views are correctly labeled in a clear 3x2 layout. No missing image or clipped label observed.'},
    'target_files_modified':False,'target_code_executed':False,'target_rerendered_or_rebuilt':False,
    'writes_confined_to':'voxel/kitchen/appliances/reviews',
}
(OUT/'furnishings_review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
rows = '\n'.join(f"| {slug} | Pass | {notes[slug]['half']} |" for slug in notes)
md = f'''# Independent furnishings review

**Spec compliance: PASS. Visual and technical quality: PASS. No changes requested.**

Reviewer: appliances worker. Target: `voxel/kitchen/furnishings`. Review was read-only; writes were confined to `voxel/kitchen/appliances/reviews`. No target authoring code, development suite, rebuild or rerender was run, and no production file was modified.

Review clock: {start.isoformat()} to {finish.isoformat()} UTC; {start.astimezone(kst).isoformat()} to {finish.astimezone(kst).isoformat()} KST. Recorded interval: {(finish-start).total_seconds():.3f} seconds. Initial brief/evidence reading preceded the first recorded review clock sample.

## Spec compliance

The brief and target RESULT, STATUS, validation, capture, visual-inspection and frozen-hash evidence were read. The six required slugs have 12 native VOX files and 12 final primary PNGs. The independent lightweight check verified **71 frozen files**, VOX 150 parsing, palette, nonzero/unique/in-bounds occupancy, longest axes 128/64, exact half dimensions, doubled cell scale, identical physical extents, exact saved-large-to-half reduction, and true occupancy reduction.

All PNGs pass 768 x 768, CRC and compressed-image checks. Their hashes match both metadata and captures. Each pair has identical camera and lighting settings with Cycles CPU, 24 samples, four threads, denoising and AgX. Capture evidence identifies reopened VOX sources and render-only studio floors. No prohibited scene or mesh export was found.

## Visual and technical quality

All **12 final primary previews** were individually inspected with image tools; their exact hashes and inspection times are recorded in `furnishings_review.json`. The contact sheet was also inspected. Cream, sage, oak and charcoal form a consistent restrained set. Every silhouette is readable at half size; no image clipping or new visible support defect was found.

| Asset | Verdict | Half-size observation |
|---|---|---|
{rows}

An independent column-interval connectivity check found **one six-neighbor connected assembly for each of all twelve native models**. It corroborates the repaired rail hooks, shelf bowl, rack plate supports and inserted knives. All **48 existing functional feature probes** were independently replayed against saved VOX values and passed, including basin, handles, shelf bays, cup and rack openings, and the unused knife slot. Check runtime: {check['elapsed_seconds']:.3f} seconds.

## Known limits

- The hutch's upper-right mug is partly hidden by the common camera. Its native cavity probe passes; no additional view is claimed.
- Thin decorative oak seams disappear on the half island/cart. Functional geometry remains open and recognizable.
- Connectivity proves integer face contact, not mechanical strength. These are static colored voxel models.
- The authored-source roundtrip is supported by the owner's validation evidence. This review independently checked the saved artifacts without rerunning target authoring code.

Full machine evidence: `furnishings_native_check.json` and `furnishings_review.json`. No issue requires routing back to the owner.
'''
(OUT/'furnishings_review.md').write_text(md,encoding='utf-8')
print(json.dumps({'spec_compliance':'pass','visual_technical_quality':'pass','changes_requested':0,
                  'inspected_previews':12,'review_finished_at_utc':finish.isoformat()}))
