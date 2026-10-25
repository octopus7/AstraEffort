"""Validate persisted native files and actual PNGs, independently of rendering."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, struct, sys, time
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1] / '_tools'))
from voxelkit import read_vox, reduce_half, grid_stats

EXPECTED = {
    'stand_mixer': ((96, 128, 128), .40 / 128),
    'espresso_machine': ((128, 104, 128), .40 / 128),
    'toaster': ((128, 84, 88), .31 / 128),
    'blender': ((96, 96, 128), .42 / 128),
    'stock_pot': ((128, 96, 92), .38 / 128),
    'frying_pan': ((128, 96, 32), .48 / 128),
    'cutting_board_knife': ((128, 96, 24), .42 / 128),
}

# Coordinates are large-grid positions; floor-divided for half-size probes.
# Each void is intentionally in functional space, not outside the object.
FEATURES = {
    'stand_mixer': [
        ('bowl_inner_cavity', (48, 44, 42), False),
        ('working_clearance_beside_whisk', (25, 44, 76), False),
        ('bowl_floor', (48, 44, 23), True),
        ('overhead_motor', (48, 44, 104), True),
        ('bowl_handle_hole', (86, 44, 48), False),
    ],
    'espresso_machine': [
        ('cup_bay_clearance', (34, 40, 54), False),
        ('cup_inner_cavity', (58, 42, 43), False),
        ('cup_handle_loop', (74, 42, 40), False),
        ('group_head', (64, 35, 79), True),
        ('steam_wand', (103, 19, 52), True),
        ('rear_chassis', (64, 83, 60), True),
    ],
    'toaster': [
        ('front_slot_open', (64, 29, 58), False),
        ('rear_slot_end_open', (30, 55, 58), False),
        ('toast_slice', (64, 55, 76), True),
        ('side_lever', (123, 42, 44), True),
    ],
    'blender': [
        ('jug_inner_cavity', (45, 45, 78), False),
        ('handle_loop', (79, 45, 80), False),
        ('lid', (45, 45, 114), True),
        ('base_motor', (48, 45, 25), True),
    ],
    'stock_pot': [
        ('pot_inner_cavity', (64, 48, 45), False),
        ('left_handle_loop', (21, 48, 58), False),
        ('right_handle_loop', (107, 48, 58), False),
        ('pot_floor', (64, 48, 17), True),
        ('left_wall_closed_below_handle', (29, 48, 60), True),
        ('right_wall_closed_below_handle', (98, 48, 60), True),
    ],
    'frying_pan': [
        ('pan_inner_cavity', (48, 48, 22), False),
        ('handle_hanging_hole', (119, 48, 20), False),
        ('pan_floor', (48, 48, 10), True),
        ('handle_neck', (88, 48, 17), True),
    ],
    'cutting_board_knife': [
        ('board_handle_hole', (118, 48, 4), False),
        ('board_surface', (50, 60, 4), True),
        ('knife_blade', (56, 36, 10), True),
        ('knife_handle', (98, 44, 14), True),
    ],
}

def utc():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def check(condition, message):
    if not condition:
        raise AssertionError(message)

def validate(require_renders=True):
    started, timer = utc(), time.perf_counter()
    missing = [s for s in EXPECTED if not (ROOT/'assets'/s/'large'/f'{s}.vox').is_file()]
    check(not missing, 'Required native deliverables absent: ' + ', '.join(missing))
    from build import make_assets, PALETTE
    authored = {a.slug: a for a in make_assets()}
    check(set(authored) == set(EXPECTED), 'Unexpected asset roster')
    captures = {}
    if require_renders:
        cm = json.loads((ROOT/'capture_manifest.json').read_text(encoding='utf-8'))
        check(cm['actual_blender_renders'] is True, 'Capture manifest lacks actual-render declaration')
        captures = {(c['asset'], c['variant']): c for c in cm['captures']}
        check(len(captures) == 14, 'Capture count is not 14')
    checks = []
    for slug, (dimensions, scale) in EXPECTED.items():
        asset = authored[slug]
        expected_half = reduce_half(asset.grid)
        if asset.half_postprocess:
            asset.half_postprocess(expected_half)
        pair = []
        for variant, expected, divisor in [('large', asset.grid, 1), ('half', expected_half, 2)]:
            dst = ROOT/'assets'/slug/variant
            vox = dst/f'{slug}.vox'
            raw = vox.read_bytes()
            check(raw[:8] == b'VOX '+struct.pack('<I', 150), f'{slug}/{variant}: version is not VOX150')
            g = read_vox(vox)  # validates duplicate/out-of-grid/zero-color records and chunk lengths
            check(g.shape == tuple(n//divisor for n in dimensions), f'{slug}/{variant}: dimensions')
            check(np.array_equal(g.data, expected.data), f'{slug}/{variant}: authored roundtrip')
            check(g.palette[:len(PALETTE)] == PALETTE, f'{slug}/{variant}: palette roundtrip')
            check(0 < int(g.data.max()) < len(PALETTE), f'{slug}/{variant}: palette bounds')
            check(np.count_nonzero(g.data) > 0, f'{slug}/{variant}: empty')
            meta = json.loads((dst/'metadata.json').read_text(encoding='utf-8'))
            check(abs(meta['voxel_size_m']-scale*divisor) < 1e-12, f'{slug}/{variant}: voxel scale')
            check(meta['native_sha256'] == sha(vox), f'{slug}/{variant}: native hash')
            feature_checks = []
            for label, point, occupied in FEATURES[slug]:
                sample = tuple(p//divisor for p in point)
                value = int(g.data[sample])
                check((value > 0) == occupied, f'{slug}/{variant}: feature {label} at {sample} was {value}')
                feature_checks.append({'feature': label, 'sample': list(sample), 'expected_occupied': occupied, 'palette_index': value, 'passed': True})
            # Functional void probes are small volumes as well as single anchor cells.
            void_centers = [p for name, p, occ in FEATURES[slug] if not occ]
            for p in void_centers:
                c = tuple(v//divisor for v in p)
                block = g.data[tuple(slice(max(0,v-1), v+1) for v in c)]
                check(np.count_nonzero(block) == 0, f'{slug}/{variant}: functional void lost around {p}')
            entry = {'asset': slug, 'variant': variant, 'passed': True, **grid_stats(g, scale*divisor), 'features': feature_checks, 'native_sha256': sha(vox)}
            if require_renders:
                png = dst/'preview.png'
                image = png.read_bytes()
                check(image[:8] == b'\x89PNG\r\n\x1a\n', f'{slug}/{variant}: invalid PNG signature')
                check(struct.unpack('>II', image[16:24]) == (768,768), f'{slug}/{variant}: incorrect PNG dimensions')
                capture = captures[(slug, variant)]
                check(capture['image_sha256'] == sha(png) == meta['preview_sha256'], f'{slug}/{variant}: preview hash')
                check(capture['source_vox_sha256'] == sha(vox), f'{slug}/{variant}: rendered source hash')
                settings = capture['settings']
                check(settings['engine'] == 'CYCLES' and settings['device'] == 'CPU' and settings['threads'] == 4, f'{slug}/{variant}: renderer')
                check(settings['samples'] == 24 and settings['resolution'] == [768,768] and settings['denoising'] and settings['view_transform'] == 'AgX', f'{slug}/{variant}: capture settings')
                check(capture['render_input'] == 'reparsed native VOX', f'{slug}/{variant}: render input')
                entry['preview_sha256'] = sha(png)
            pair.append(entry)
            checks.append(entry)
        check(pair[1]['occupied_voxels'] < pair[0]['occupied_voxels'], slug+': half occupancy did not reduce')
        check(np.allclose(pair[0]['grid_extents_m'], pair[1]['grid_extents_m']), slug+': physical grid extents mismatch')
        if require_renders:
            a,b = captures[(slug,'large')],captures[(slug,'half')]
            check(a['settings'] == b['settings'], slug+': cameras/render settings differ')
    forbidden = [str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.suffix.lower() in {'.blend','.glb','.fbx','.obj','.umap'}]
    check(not forbidden, 'Forbidden outputs: '+str(forbidden))
    check(len(list((ROOT/'assets').rglob('*.vox'))) == 14, 'Native file count')
    if require_renders:
        check(len(list((ROOT/'assets').rglob('preview.png'))) == 14, 'Preview count')
    result = {'passed': True, 'started_at_utc': started, 'finished_at_utc': utc(), 'elapsed_seconds': time.perf_counter()-timer, 'render_checks_included': require_renders, 'native_count':14, 'preview_count':14 if require_renders else 0, 'checks': checks, 'forbidden_outputs': forbidden, 'limitations': ['Single standardized camera per variant', 'Glass is intentionally opaque palette material', 'Thin metal parts are exaggerated for half-scale readability']}
    (ROOT/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'native_count':14,'preview_count':result['preview_count'],'feature_probes':sum(len(c['features']) for c in checks),'elapsed_seconds':result['elapsed_seconds']}))
    return result

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--native-only',action='store_true')
    args=parser.parse_args()
    validate(not args.native_only)
