"""Persist this worker's completed independent review without writing the target."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json
HERE=Path(__file__).resolve().parent
TARGET=HERE.parents[1]/'appliances'
OWN=HERE.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

checks=read(HERE/'appliances_check.json')
assert checks['passed']
frozen=read(TARGET/'frozen_file_hashes.json')
for p,d in frozen['sha256'].items():assert sha(TARGET/p)==d,p
own_frozen=read(OWN/'frozen_file_hashes.json')
for r in own_frozen['files']:assert sha(OWN/r['path'])==r['sha256'],r['path']

observations={
    'double_door_fridge':{
        'large':'Cream double-door silhouette is clear. Door seam and the two sage pulls remain visibly separate, with clean stepped corner rounding, plinth and feet. Whole model is framed.',
        'half':'Door separation, projecting pulls and base survive reduction. The outer form is intentionally more angular; no clipping or filled grip clearance is apparent.',
    },
    'range_oven':{
        'large':'Four burner rests, four front knobs, oven pull and opaque blue-gray oven window read clearly. Cream/sage body and charcoal grates suit the brief.',
        'half':'All four burners and knobs remain distinct. Oven-pull clearance is visible and the closed door remains readable. Same-camera framing is preserved.',
    },
    'microwave':{
        'large':'Wide microwave shape, opaque framed window, sage handle, dial/button and right-side ventilation slots are recognizable. Vents are actual visible recesses.',
        'half':'Handle remains separate from the front and all four side slots survive. Control shapes and the window border remain legible despite coarser steps.',
    },
    'dishwasher':{
        'large':'Lowered static door, open wash chamber, two rack fronts, visible plate spacing and door dispenser are readable. Interior is dark but the important rack structure is distinct.',
        'half':'Open chamber and rack gaps survive native reduction; plates remain individually separated. Some upper items are naturally hidden behind the top rack/roof in this one camera.',
    },
    'range_hood':{
        'large':'FINAL repaired preview: both visible sloped canopy surfaces are continuous with no unintended slit. Top duct opening, cream chimney, sage trim and front controls are clear.',
        'half':'FINAL repaired preview: continuous stepped canopy, open top duct and three control buttons remain readable. Underside filter is outside this camera view and is assessed via saved-native probes.',
    },
    'rice_cooker':{
        'large':'Rounded cream cooker, separated sage lid band, open carry-handle loop, lid fittings, front control panel and feet form a clear appliance silhouette.',
        'half':'Carry-handle opening remains visible and control blocks stay distinct. Coarser circular steps are expected; no broken connection or unintended closure is visible.',
    },
    'electric_kettle':{
        'large':'Kettle has a visible open spout mouth, generous open handle, lid, electric base, switch and opaque level panel. Its full silhouette fits the image.',
        'half':'Handle loop and spout mouth remain open and readable. Lid, base and switch remain distinct. The chunky spout and handle match the restrained voxel style.',
    },
}
started=datetime(2026,10,25,5,38,0,tzinfo=timezone.utc)
finished=datetime.now(timezone.utc)
kst=timezone(timedelta(hours=9))
inspected=[]
for row in checks['records']:
    assert sha(TARGET/row['preview_path'])==row['preview_sha256']
    inspected.append({'asset':row['asset'],'variant':row['variant'],'path':row['preview_path'],'sha256':row['preview_sha256'],'inspected':True,'tool':'view_image','observations':observations[row['asset']][row['variant']],'findings':[]})
report={
    'reviewer':'countertop worker','target_batch':'appliances','target_path':str(TARGET),
    'started_at_utc':started.isoformat(),'finished_at_utc':finished.isoformat(),
    'started_at_kst':started.astimezone(kst).isoformat(),'finished_at_kst':finished.astimezone(kst).isoformat(),
    'elapsed_seconds':(finished-started).total_seconds(),
    'review_mode':'Independent read-only same-kitchen review authorized by coordinator. No target authoring or renderer execution.',
    'spec_compliance':{'verdict':'pass','blocking_findings':[],
        'evidence':['Exact seven required appliance slugs with fourteen VOX150 files and fourteen 768px PNGs.',
                    'All saved native dimensions, common palette, coordinates and metadata checked independently.',
                    'All seven saved half grids exactly match 2x reduction of their saved large grids, with doubled meter scale and identical physical extents.',
                    'All 64 declared functional probes independently resampled from saved native data.',
                    'All 67 frozen files match SHA256; native/PNG hashes agree across metadata, capture and validation evidence.',
                    'All seven camera/light/render pairs match, with Cycles CPU, four threads, 24 samples, denoising and AgX.',
                    'Read-only pipeline inspection confirms surface construction consumes reparsed VOX, using the shared build_surface and add_studio helpers.',
                    'No forbidden scene, exchange mesh or engine artifacts found.']},
    'visual_technical_quality':{'verdict':'pass','blocking_findings':[],'minor_findings':[],
        'summary':'All fourteen primary previews were directly inspected. The seven models are distinct, fully framed and consistent with the cream/sage/charcoal kitchen style; important openings remain readable at half size. No demonstrated defect requiring owner correction was found.',
        'repaired_hood':'Visible canopy slit is absent in both final previews. Independent saved-native checks pass intact shell, continuous airway, open duct, filter gap, chimney wall and filter bar at both resolutions.'},
    'findings':[],
    'known_limits':['Single prescribed three-quarter camera does not expose every rear/underside surface; those functional regions were checked in saved native data where probes are supplied.',
                    'Glass is intentionally opaque. Dishwasher uses one static lowered-door pose; no operation, animation or mechanics are implied.',
                    'This review parsed saved files and recomputed reduction/features, but did not rerun target authoring, rendering or the target development suite. Authored-to-saved roundtrip is supported by hash-matched producer evidence and pipeline inspection.',
                    'Production timings are reported by the producer; this review records its own real timestamps separately.'],
    'independent_checks':{'evidence':'appliances_check.json','elapsed_seconds':checks['elapsed_seconds'],'frozen_files_checked':67,'native_files_checked':14,'png_files_checked':14,'functional_probes':64,'same_camera_pairs':7,'target_modified':False,'own_frozen_production_unchanged':True,'own_frozen_files_checked':len(own_frozen['files'])},
    'inspected_previews':inspected,
    'contact_sheet':{'path':'overview_half.png','sha256':sha(TARGET/'overview_half.png'),'inspected':True,'observations':'Seven labeled half previews match the inspected final models. Labels, dimensions/cell sizes and footer are clear and unclipped.'},
    'target_evidence_hashes':{p:sha(TARGET/p) for p in ['RESULT.md','STATUS.json','validation.json','capture_manifest.json','frozen_file_hashes.json','image_inspection.json','visual_fix.json','timing.json']},
}
(HERE/'appliances_review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
lines=[
    '# Independent appliances review','',
    '**Spec compliance: PASS. Visual/technical quality: PASS.** No blocking or minor defect requiring correction was found.','',
    f"Reviewer: countertop worker. Read-only target: `voxel/kitchen/appliances`.",
    f"Actual start: {started.isoformat()} UTC / {started.astimezone(kst).isoformat()} KST.  ",
    f"Actual finish: {finished.isoformat()} UTC / {finished.astimezone(kst).isoformat()} KST.  ",
    f"Review wall time: **{report['elapsed_seconds']:.3f} seconds**; independent native/hash check: **{checks['elapsed_seconds']:.3f} seconds**.",'',
    '## Spec-compliance evidence','',
]
lines += ['- '+s for s in report['spec_compliance']['evidence']]
lines += ['', 'The refrigerator occupies about 1.984m vertically within its 2.048m grid; the kettle grid is 0.3392m high. These are consistent with the requested household scale guidance.',
          '', '## Visual and technical observations','',
          'All fourteen final primary PNGs were individually opened with `view_image`, followed by the labeled contact sheet. The final repaired hood images, rather than superseded captures, were reviewed.','',
          '| Asset | Large preview | Half preview |','|---|---|---|']
for slug,notes in observations.items():lines.append(f"| {slug} | {notes['large']} | {notes['half']} |")
lines += ['', '**Repaired hood:** no unintended side slit remains in the final views. Six saved-native checks per resolution confirm canopy shell, central airway, top duct, filter gap, chimney wall and filter bar.',
          '', '## Findings and limits','', 'Findings requiring owner action: **none**. No target files or frozen countertop production files were modified. All 73 countertop frozen production hashes also remain unchanged.','']
lines += ['- '+s for s in report['known_limits']]
lines += ['', 'Detailed per-image SHA256 values and inspection notes: `appliances_review.json`. Independent parsing, scale, reduction, probe and frozen-file results: `appliances_check.json`; reproducible read-only checker: `check_appliances.py`.']
(HERE/'appliances_review.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'spec_compliance':'pass','visual_technical_quality':'pass','inspected_primary_previews':14,'frozen_target_files_verified':67,'own_frozen_files_unchanged':len(own_frozen['files']),'review_seconds':report['elapsed_seconds'],'findings':0}))
