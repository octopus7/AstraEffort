"""Read-only FBX inspection in isolated Blender. Writes only this QA directory."""
import bpy
import hashlib
import json
import math
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / 'Art' / 'FinalMeshes'
RESOLUTION = 1024
TARGET_DENSITY = 128.0
CLIP_EPSILON = 1e-12
POSITIVE_OVERLAP = 1e-10
START = datetime.now(timezone.utc)


def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def triangle_area(tri):
    return abs(cross(*tri)) * .5


def intersection_area(subject, clip):
    if cross(*clip) < 0:
        clip = tuple(reversed(clip))
    output = list(subject)
    for i in range(3):
        a, b = clip[i], clip[(i+1) % 3]
        inp, output = output, []
        if not inp:
            return 0.0
        previous = inp[-1]
        prev_side = cross(a, b, previous)
        for current in inp:
            side = cross(a, b, current)
            inside, was_inside = side >= -CLIP_EPSILON, prev_side >= -CLIP_EPSILON
            if inside != was_inside:
                den = prev_side - side
                if abs(den) > 1e-30:
                    t = prev_side / den
                    output.append((previous[0]+t*(current[0]-previous[0]), previous[1]+t*(current[1]-previous[1])))
            if inside:
                output.append(current)
            previous, prev_side = current, side
    if len(output) < 3:
        return 0.0
    # Shift to the first vertex to limit cancellation for tiny polygons.
    o = output[0]
    return abs(sum(cross(o, output[i], output[(i+1) % len(output)]) for i in range(1, len(output)))) * .5


def overlap_check(records):
    grid, bounds = defaultdict(list), []
    tested, positive_count, largest = 0, 0, 0.0
    examples = []
    cells_per_unit = 128
    for i, record in enumerate(records):
        tri = record['uv0']
        xs, ys = [p[0] for p in tri], [p[1] for p in tri]
        xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
        bounds.append((xmin, xmax, ymin, ymax))
        cells = [(x, y) for x in range(math.floor(xmin*cells_per_unit), math.floor(xmax*cells_per_unit)+1)
                 for y in range(math.floor(ymin*cells_per_unit), math.floor(ymax*cells_per_unit)+1)]
        candidates = set(j for cell in cells for j in grid[cell])
        for j in candidates:
            x0, x1, y0, y1 = bounds[j]
            if x1 <= xmin+1e-13 or x0 >= xmax-1e-13 or y1 <= ymin+1e-13 or y0 >= ymax-1e-13:
                continue
            tested += 1
            area = intersection_area(tri, records[j]['uv0'])
            largest = max(largest, area)
            if area > POSITIVE_OVERLAP:
                positive_count += 1
                if len(examples) < 50:
                    examples.append({'triangle_a': record['id'], 'triangle_b': records[j]['id'],
                        'material_a': record['material'], 'material_b': records[j]['material'],
                        'overlap_area_uv2': area, 'overlap_area_px2_at_1024': area*RESOLUTION**2})
        for cell in cells:
            grid[cell].append(i)
    return {'method': 'Sutherland-Hodgman exact triangle clipping after 128x128 spatial-hash broadphase; shared zero-area edges allowed',
            'positive_threshold_uv2': POSITIVE_OVERLAP, 'candidate_pairs_clipped': tested,
            'positive_overlap_pair_count': positive_count, 'maximum_intersection_uv2': largest,
            'maximum_intersection_px2_at_1024': largest*RESOLUTION**2,
            'examples': examples, 'passed': positive_count == 0}


def percentile(values, p):
    if not values:
        return None
    vals = sorted(values)
    index = (len(vals)-1) * p
    lo = math.floor(index)
    return vals[lo] + (vals[min(lo+1, len(vals)-1)]-vals[lo])*(index-lo)


def density_stats(records):
    valid = [r for r in records if r['world_area_m2'] > 1e-12 and r.get('uv1_area', 0) > 1e-14]
    values = [r['density_px_per_m'] for r in valid]
    area = sum(r['world_area_m2'] for r in valid)
    outliers = [r for r in valid if r['density_px_per_m'] < TARGET_DENSITY*.85 or r['density_px_per_m'] > TARGET_DENSITY*1.15]
    outlier_area = sum(r['world_area_m2'] for r in outliers)
    examples = sorted(outliers, key=lambda r: abs(math.log(r['density_px_per_m']/TARGET_DENSITY)), reverse=True)[:30]
    return {'valid_triangle_count': len(valid), 'area_m2': area,
        'arithmetic_mean_px_per_m': sum(values)/len(values) if values else None,
        'area_weighted_mean_px_per_m': sum(r['density_px_per_m']*r['world_area_m2'] for r in valid)/area if area else None,
        'minimum_px_per_m': min(values) if values else None, 'maximum_px_per_m': max(values) if values else None,
        'p01_px_per_m': percentile(values, .01), 'p05_px_per_m': percentile(values, .05),
        'median_px_per_m': percentile(values, .5), 'p95_px_per_m': percentile(values, .95), 'p99_px_per_m': percentile(values, .99),
        'outside_15percent_target_triangle_count': len(outliers), 'outside_15percent_target_area_m2': outlier_area,
        'outside_15percent_target_area_fraction': outlier_area/area if area else None,
        'outlier_examples': [{k: r[k] for k in ('id','material','world_area_m2','uv1_area','density_px_per_m','world_centroid_m')} for r in examples]}


def hashfile(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(path):
    t = time.perf_counter()
    before = {'sha256': hashfile(path), 'bytes': path.stat().st_size, 'mtime_ns': path.stat().st_mtime_ns}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path), use_anim=False, use_custom_normals=False)
    objects = sorted([o for o in bpy.context.scene.objects if o.type == 'MESH'], key=lambda o: o.name)
    records, object_info, points, missing_uv = [], [], [], []
    materials = defaultdict(list)
    for obj in objects:
        mesh = obj.data
        mesh.calc_loop_triangles()
        matrix = obj.matrix_world
        wp = [matrix @ v.co for v in mesh.vertices]
        points.extend(wp)
        layers = list(mesh.uv_layers)
        object_info.append({'name': obj.name, 'vertices': len(mesh.vertices), 'polygons': len(mesh.polygons),
            'triangles': len(mesh.loop_triangles), 'uv_layer_names': [u.name for u in layers],
            'location_m': list(obj.location), 'rotation_euler_rad': list(obj.rotation_euler), 'scale': list(obj.scale),
            'world_pivot_m': list(matrix.translation), 'local_bbox_min_m': [min(v.co[a] for v in mesh.vertices) for a in range(3)],
            'local_bbox_max_m': [max(v.co[a] for v in mesh.vertices) for a in range(3)],
            'materials': [m.name if m else None for m in mesh.materials]})
        if len(layers) < 2:
            missing_uv.append(obj.name)
        for triangle_index, tri in enumerate(mesh.loop_triangles):
            verts = [wp[v] for v in tri.vertices]
            world_area = (verts[1]-verts[0]).cross(verts[2]-verts[0]).length*.5
            material = mesh.materials[tri.material_index].name if tri.material_index < len(mesh.materials) and mesh.materials[tri.material_index] else '(unassigned)'
            record = {'id': f'{obj.name}:tri{triangle_index}:poly{tri.polygon_index}', 'material': material,
                      'world_area_m2': world_area, 'world_centroid_m': list(sum(verts, verts[0]*0)/3)}
            for i in range(min(2, len(layers))):
                uv = tuple(tuple(layers[i].data[loop].uv) for loop in tri.loops)
                record[f'uv{i}'] = uv
                record[f'uv{i}_area'] = triangle_area(uv)
            if world_area > 1e-12 and record.get('uv1_area', 0) > 1e-14:
                record['density_px_per_m'] = RESOLUTION*math.sqrt(record['uv1_area']/world_area)
            records.append(record)
            materials[material].append(record)
    uvrecords = [r for r in records if 'uv0' in r]
    ranges = {}
    for layer in ('uv0', 'uv1'):
        coords = [p for r in records if layer in r for p in r[layer]]
        ranges[layer] = {'min': [min(p[a] for p in coords) for a in range(2)],
                         'max': [max(p[a] for p in coords) for a in range(2)]} if coords else None
    degenerate = {}
    for label, key, epsilon in [('world','world_area_m2',1e-12),('uv0','uv0_area',1e-14),('uv1','uv1_area',1e-14)]:
        bad = [r for r in records if r.get(key, 0) <= epsilon]
        degenerate[label] = {'count': len(bad), 'threshold': epsilon,
                             'examples': [{k:r.get(k) for k in ('id','material','world_area_m2','uv0_area','uv1_area')} for r in bad[:30]]}
    overlap = overlap_check(uvrecords)
    bounds_min = [min(p[a] for p in points) for a in range(3)]
    bounds_max = [max(p[a] for p in points) for a in range(3)]
    uv0_in_tile = bool(ranges['uv0'] and min(ranges['uv0']['min']) >= -1e-6 and max(ranges['uv0']['max']) <= 1+1e-6)
    after = {'sha256': hashfile(path), 'bytes': path.stat().st_size, 'mtime_ns': path.stat().st_mtime_ns}
    density = density_stats(records)
    result = {'mesh': path.stem, 'file': str(path), 'source_before': before, 'source_after': after,
        'source_unmodified': before == after, 'object_count': len(objects), 'objects': object_info,
        'triangle_count': len(records), 'world_bounds_min_m': bounds_min, 'world_bounds_max_m': bounds_max,
        'world_dimensions_m': [bounds_max[a]-bounds_min[a] for a in range(3)],
        'uv_ranges': ranges, 'uv0_within_unit_tile': uv0_in_tile, 'objects_missing_two_uv_layers': missing_uv,
        'degenerate_triangles': degenerate, 'uv0_overlap': overlap,
        'uv1_density': density, 'uv1_density_by_material': {m:density_stats(v) for m,v in materials.items()},
        'elapsed_seconds': time.perf_counter()-t}
    result['strict_uv_integrity_passed'] = bool(not missing_uv and uv0_in_tile and overlap['passed'] and
        all(d['count']==0 for d in degenerate.values()) and before == after)
    (OUT/f'{path.stem}.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('MESH_QA', path.stem, 'integrity', result['strict_uv_integrity_passed'], 'triangles',len(records),
          'density', round(density['area_weighted_mean_px_per_m'] or 0, 3),
          'outlier_area_fraction',round(density['outside_15percent_target_area_fraction'] or 0,8),
          'seconds',round(result['elapsed_seconds'],2),flush=True)
    return result


def main():
    files = sorted(SOURCE.glob('*.fbx'))
    results = [inspect(path) for path in files]
    finish = datetime.now(timezone.utc)
    output = {'started_at_utc': START.isoformat(), 'finished_at_utc': finish.isoformat(),
        'elapsed_seconds': (finish-START).total_seconds(), 'blender_version': bpy.app.version_string,
        'expected_mesh_count':20, 'actual_mesh_count':len(results), 'texture_resolution': RESOLUTION,
        'target_uv1_density_px_per_m': TARGET_DENSITY,
        'source_import': 'Blender FBX importer global_scale=1; source FBX unit metadata applied by importer; bounds expressed in Blender metres.',
        'density_definition': '1024 * sqrt(UV1 triangle area / world-space triangle area in square metres). Area-weighted summary; +/-15% marked for review, including isolated bevel triangles.',
        'all_sources_unmodified': all(r['source_unmodified'] for r in results),
        'all_strict_uv_integrity_passed': all(r['strict_uv_integrity_passed'] for r in results),
        'meshes': results}
    (OUT/'final_mesh_qa.json').write_text(json.dumps(output,indent=2)+'\n', encoding='utf-8')
    lines = ['# Independent final FBX review', '', f'Blender {bpy.app.version_string}; {len(results)} FBX files; source hashes and timestamps unchanged: {output["all_sources_unmodified"]}.',
        f'UTC: {START.isoformat()} to {finish.isoformat()}; elapsed {(finish-START).total_seconds():.3f} seconds.', '',
        'UV0 checked by exact triangle clipping after spatial hashing. Positive area threshold 1e-10 UV². UV1 density measured at 1024² using imported world triangle areas. This is source-mesh QA, not Unreal import/runtime validation.', '',
        '| Mesh | Triangles | UV integrity | UV1 mean px/m (area weighted) | UV1 min–max | Area outside ±15% | Bounds m |',
        '|---|---:|---|---:|---|---:|---|']
    for r in results:
        d=r['uv1_density']
        lines.append(f'| {r["mesh"]} | {r["triangle_count"]} | {"PASS" if r["strict_uv_integrity_passed"] else "REVIEW"} | {d["area_weighted_mean_px_per_m"]:.3f} | {d["minimum_px_per_m"]:.3f}–{d["maximum_px_per_m"]:.3f} | {100*d["outside_15percent_target_area_fraction"]:.6f}% | '+ ' × '.join(f'{x:.3f}' for x in r['world_dimensions_m'])+' |')
    lines += ['', 'Per-mesh JSON includes every object pivot/transform, bounds, channel names, overlap examples, material-level density statistics and exact outlier triangle/face IDs and centroids. UV0 is constrained to its own 0–1 tile; UV1 is intentionally tiled.', '',
              'Geometry and UVs were inspected without saving a Blender file or changing source FBX files. No other theme, effort, Unreal session, Git operation, or shared Blender state was accessed.']
    (OUT/'REVIEW.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('FINAL_MESH_QA_COMPLETE',len(results),output['all_strict_uv_integrity_passed'],flush=True)


if __name__ == '__main__':
    main()
