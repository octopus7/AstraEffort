"""Finite read-only review check; never imports or runs target authoring code."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import struct
import sys
import time
import zlib
sys.dont_write_bytecode = True
import numpy as np

OUT = Path(__file__).resolve().parent
TARGET = OUT.parent.parent / 'furnishings'
sys.path.insert(0, str(OUT.parents[2] / '_tools'))
from voxelkit import read_vox, reduce_half

SLUGS = ('sink_cabinet', 'kitchen_island', 'dish_cabinet', 'kitchen_cart',
         'dish_drying_rack', 'knife_block')
PALETTE = [(0,0,0,0),(232,225,205,255),(121,151,133,255),(75,105,91,255),
           (181,130,78,255),(217,176,113,255),(48,56,57,255),(156,170,170,255),
           (91,108,112,255),(92,133,145,255),(244,239,225,255),(191,105,70,255),
           (35,42,44,255),(217,164,85,255),(151,94,48,255),(203,183,106,255)]


def read(rel):
    return json.loads((TARGET / rel).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(data):
    """Independent 6-neighbor connectivity by union of Z-column intervals."""
    parent, weights, columns = [], [], {}
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def merge(a, b):
        a, b = root(a), root(b)
        if a == b:
            return
        if weights[a] < weights[b]:
            a, b = b, a
        parent[b] = a
        weights[a] += weights[b]
    for x in range(data.shape[0]):
        for y in range(data.shape[1]):
            edges = np.flatnonzero(np.diff(np.r_[False, data[x,y] > 0, False]))
            intervals = []
            for lo, hi in zip(edges[::2], edges[1::2]):
                i = len(parent)
                parent.append(i)
                weights.append(int(hi-lo))
                intervals.append((int(lo), int(hi), i))
            columns[x,y] = intervals
            for neighbor in ((x-1,y), (x,y-1)):
                previous = columns.get(neighbor, ())
                i = j = 0
                while i < len(intervals) and j < len(previous):
                    a, b = intervals[i], previous[j]
                    if max(a[0], b[0]) < min(a[1], b[1]):
                        merge(a[2], b[2])
                    if a[1] <= b[1]:
                        i += 1
                    else:
                        j += 1
    roots = {root(i) for i in range(len(parent))}
    sizes = sorted((weights[i] for i in roots), reverse=True)
    assert sum(sizes) == int(np.count_nonzero(data))
    return sizes


def png_check(path):
    raw = path.read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    pos, packed, dims = 8, [], None
    while pos < len(raw):
        n = struct.unpack_from('>I', raw, pos)[0]
        kind, body = raw[pos+4:pos+8], raw[pos+8:pos+8+n]
        crc = struct.unpack_from('>I', raw, pos+8+n)[0]
        assert zlib.crc32(kind+body) & 0xffffffff == crc
        if kind == b'IHDR':
            dims = struct.unpack('>IIBBBBB', body)
        elif kind == b'IDAT':
            packed.append(body)
        pos += n + 12
        if kind == b'IEND':
            break
    assert pos == len(raw) and dims[:4] == (768,768,8,2)
    decoded = zlib.decompress(b''.join(packed))
    assert len(decoded) == (768*3+1)*768
    return {'width': 768, 'height': 768, 'crc_and_decompression': True}


def main():
    start = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    frozen_path = TARGET / 'frozen_file_hashes.json'
    frozen_sha = sha(frozen_path)
    frozen, capture, validation = read('frozen_file_hashes.json'), read('capture_manifest.json'), read('validation.json')
    assert read('STATUS.json')['status'] == 'ready_for_review'
    assert validation['passed'] and not validation['errors']
    for entry in frozen['files']:
        path = (TARGET / entry['path']).resolve()
        assert path.is_relative_to(TARGET.resolve())
        assert path.stat().st_size == entry['bytes'] and sha(path) == entry['sha256'], entry['path']
    records = []
    for slug in SLUGS:
        pair = []
        grids = []
        settings = []
        for variant in ('large', 'half'):
            rel = f'assets/{slug}/{variant}'
            vox, png = TARGET / rel / (slug+'.vox'), TARGET / rel / 'preview.png'
            assert struct.unpack_from('<I', vox.read_bytes(), 4)[0] == 150
            grid = read_vox(vox)
            meta = read(rel+'/metadata.json')
            assert list(grid.shape) == meta['grid_size']
            assert grid.palette[:16] == PALETTE and 0 < int(grid.data.max()) <= 15
            count = int(np.count_nonzero(grid.data))
            assert count == meta['occupied_voxels'] > 0
            assert sha(vox) == meta['sha256'][slug+'.vox']
            assert sha(png) == meta['sha256']['preview.png']
            assert hashlib.sha256(grid.data.tobytes()).hexdigest() == meta['occupancy_sha256']
            assert np.allclose(np.array(grid.shape)*meta['voxel_size_m'], meta['grid_extents_m'], rtol=0, atol=1e-12)
            cap = [c for c in capture['captures'] if c['asset'] == slug and c['variant'] == variant]
            assert len(cap) == 1
            cap = cap[0]
            assert cap['source_native_sha256'] == sha(vox) and cap['image_sha256'] == sha(png)
            assert cap['render_from_reopened_vox']
            s = cap['settings']
            assert (s['engine'],s['device'],s['threads'],s['samples'],s['denoising'],s['view_transform']) == ('CYCLES','CPU',4,24,True,'AgX')
            assert s['resolution'] == [768,768] and s['studio_floor_is_render_only']
            declared = next(r for r in validation['variants'] if r['asset'] == slug and r['variant'] == variant)
            probes = []
            for p in declared['feature_probes']:
                lo, hi = p['bounds_voxels']
                region = grid.data[tuple(slice(l,h) for l,h in zip(lo,hi))]
                assert region.size > 0 and np.all(region == p['expected_palette_index']), (slug,variant,p['feature'])
                probes.append(p['feature'])
            sizes = components(grid.data)
            assert len(sizes) == 1, (slug,variant,sizes)
            record = {'asset':slug,'variant':variant,'native_sha256':sha(vox),'image_sha256':sha(png),
                      'image':rel+'/preview.png','grid_size':list(grid.shape),'occupied_voxels':count,
                      'voxel_size_m':meta['voxel_size_m'],'grid_extents_m':meta['grid_extents_m'],
                      'six_neighbor_components':len(sizes),'component_sizes':sizes,
                      'replayed_native_feature_probes':probes,'png':png_check(png)}
            records.append(record)
            pair.append(meta)
            grids.append(grid)
            settings.append(s)
        assert max(grids[0].shape) == 128 and all(n % 2 == 0 for n in grids[0].shape)
        assert grids[1].shape == tuple(n//2 for n in grids[0].shape) and max(grids[1].shape) == 64
        assert pair[1]['voxel_size_m'] == pair[0]['voxel_size_m']*2
        assert pair[1]['grid_extents_m'] == pair[0]['grid_extents_m']
        assert pair[1]['occupied_voxels'] < pair[0]['occupied_voxels']
        assert np.array_equal(grids[1].data, reduce_half(grids[0]).data)
        assert settings[0] == settings[1]
    assert len(list((TARGET/'assets').rglob('*.vox'))) == 12
    assert len(list((TARGET/'assets').rglob('preview.png'))) == 12
    forbidden = [p.relative_to(TARGET).as_posix() for p in TARGET.rglob('*')
                 if p.suffix.lower() in {'.blend','.blend1','.glb','.gltf','.fbx','.obj','.umap'}]
    assert not forbidden
    assert sha(frozen_path) == frozen_sha
    report = {'passed':True,'target':'voxel/kitchen/furnishings','started_at_utc':start,
              'finished_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.perf_counter()-t0,
              'target_frozen_manifest_sha256':frozen_sha,'frozen_files_verified':len(frozen['files']),
              'native_vox_count':12,'final_preview_count':12,'same_camera_pairs':6,
              'native_probe_replays':sum(len(r['replayed_native_feature_probes']) for r in records),
              'all_variants_single_connected_assembly':True,'exact_saved_large_to_half_reduction':True,
              'target_files_modified':False,'target_code_executed':False,'target_rerendered_or_rebuilt':False,
              'limits':'Checks saved native data; source-to-authored roundtrip is additionally documented by target validation, not rerun here. Connectivity proves voxel face contact, not mechanical strength.',
              'records':records}
    (OUT/'furnishings_native_check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('passed','frozen_files_verified','native_vox_count','final_preview_count','native_probe_replays','all_variants_single_connected_assembly','elapsed_seconds')}))


if __name__ == '__main__':
    main()
