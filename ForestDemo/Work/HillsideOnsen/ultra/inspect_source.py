"""Independent read-only saved-geometry audit. Run in background Blender 4.5."""
import bpy, math, json, hashlib, time
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector
from mathutils.bvhtree import BVHTree

W = Path('D:/github/AstraEffort/ForestDemo/Work/HillsideOnsen/ultra')
BLEND = W / 'SourceArt/SansolSprings.blend'
MANIFEST = W / 'scene_manifest.json'
OUT = W / 'Validation/source_geometry.json'
started = datetime.now(timezone.utc).isoformat()
t0 = time.monotonic()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
hashes = {str(p.relative_to(W)): sha(p) for p in [BLEND, MANIFEST, W/'author_scene.py']}
manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
meshes = {o.name:o for o in bpy.data.objects if o.type == 'MESH'}
metadata = {m['name']:m for m in manifest['meshes']}

def vec(v): return [float(c) for c in v]
def quantile(vals, q):
    a = sorted(vals)
    if not a: return None
    pos=(len(a)-1)*q; low=int(pos); high=min(low+1,len(a)-1)
    return a[low]+(a[high]-a[low])*(pos-low)
def stats(vals):
    return {'count':len(vals),'min':min(vals) if vals else None,'p01':quantile(vals,.01),
            'p05':quantile(vals,.05),'median':quantile(vals,.5),'p95':quantile(vals,.95),
            'p99':quantile(vals,.99),'max':max(vals) if vals else None,
            'mean':sum(vals)/len(vals) if vals else None}
def triangle_points(o, p): return [o.matrix_world @ o.data.vertices[i].co for i in p.vertices]
def bvh(o): return BVHTree.FromPolygons([o.matrix_world @ v.co for v in o.data.vertices], [list(p.vertices) for p in o.data.polygons], all_triangles=True)
def cast(tree, x, y):
    loc,norm,face,dist=tree.ray_cast(Vector((x,y,100)),Vector((0,0,-1)),200)
    if loc is None:return None
    return {'z':float(loc.z),'normal':vec(norm),'triangle':face}
def bounds(points): return [[min(v[i] for v in points),max(v[i] for v in points)] for i in range(3)]
def components(o):
    parent=list(range(len(o.data.vertices)))
    def root(i):
        while parent[i]!=i: parent[i]=parent[parent[i]];i=parent[i]
        return i
    for e in o.data.edges:
        a,b=map(root,e.vertices);parent[b]=a
    out={}
    for i in range(len(parent)):out.setdefault(root(i),[]).append(i)
    return list(out.values())

result={'started_at_utc':started,'source_hashes':hashes,'blender_version':bpy.app.version_string,
        'policy':'Read-only saved Blender mesh inspection; geometry and world coordinates in meters. No author code executed.',
        'tolerances':{'geometry_degenerate_area_m2':1e-10,'terrain_above_significant_m':.005,'raycast_comparison_m':.001},
        'meshes':{}}
for name,o in meshes.items():
    me=o.data;uv=me.uv_layers.active;meta=metadata[name];atlas=meta['uv']['atlas_pixels']
    vertices=[o.matrix_world@v.co for v in me.vertices]
    area=[];dens=[];uv_area=[];bad=[];bad_uv=[];nonfinite_uv=0;outside_uv=0;uvpoints=[];down=0;normz=[]
    uvtris=[]
    for p in me.polygons:
        vv=triangle_points(o,p)
        ar=(vv[1]-vv[0]).cross(vv[2]-vv[0]).length*.5
        area.append(ar)
        if ar<=1e-10:bad.append(p.index)
        n=(vv[1]-vv[0]).cross(vv[2]-vv[0]).normalized();normz.append(float(n.z))
        if n.z < -.5:down+=1
        if uv:
            pts=[tuple(uv.data[i].uv) for i in p.loop_indices];uvpoints.extend(pts)
            nonfinite_uv+=sum(not all(math.isfinite(c) for c in pt) for pt in pts)
            outside_uv+=sum(any(c < -1e-6 or c > 1+1e-6 for c in pt) for pt in pts)
            a,b,c=pts;ua=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))*.5
            uv_area.append(ua)
            if ua<=1e-16:bad_uv.append(p.index)
            if ar>1e-10:dens.append((math.sqrt(ua/ar)*atlas,p.index,ar))
            uvtris.append(pts)
    target=meta['uv'].get('target_px_per_m')
    dvals=[d[0] for d in dens]
    outliers=sorted([{'triangle':i,'density':d,'area_m2':ar,'relative_error':d/target-1} for d,i,ar in dens if target and abs(d/target-1)>.05],key=lambda r:abs(r['relative_error']),reverse=True)
    # Recover UV islands from geometry edges whose endpoint UVs match. Packed pretriangulation
    # face charts form islands; distinct charts have separate UV coordinates even on shared edges.
    island_info={}
    if uv and name!='SM_Steam':
        parent=list(range(len(me.polygons)));edges={}
        def root(i):
            while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
            return i
        for p in me.polygons:
            for j in range(3):
                ia=p.vertices[j];ib=p.vertices[(j+1)%3];ua=uvtris[p.index][j];ub=uvtris[p.index][(j+1)%3]
                if ia>ib:ia,ib,ua,ub=ib,ia,ub,ua
                key=(ia,ib,tuple(round(v,7) for v in ua),tuple(round(v,7) for v in ub))
                if key in edges:parent[root(p.index)]=root(edges[key])
                else:edges[key]=p.index
        groups={}
        for p in me.polygons:groups.setdefault(root(p.index),[]).extend(uvtris[p.index])
        rects=[]
        for k,pts in groups.items():rects.append((min(p[0] for p in pts),max(p[0] for p in pts),min(p[1] for p in pts),max(p[1] for p in pts),k))
        active=[];overlaps=[]
        for r in sorted(rects):
            active=[a for a in active if a[1]>r[0]+1e-7]
            for a in active:
                if min(a[3],r[3])-max(a[2],r[2])>1e-7 and min(a[1],r[1])-max(a[0],r[0])>1e-7:
                    if len(overlaps)<100:overlaps.append([a[4],r[4]])
            active.append(r)
        island_info={'recovered_islands':len(rects),'manifest_pretriangulation_charts':meta['uv']['charts'],
                     'positive_bbox_overlap_pairs_capped_100':overlaps,'bbox_overlap_test':'Independent recovered island bounding rectangle test; positive area overlaps >1e-7 UV'}
    result['meshes'][name]={'vertices':len(me.vertices),'triangles':len(me.polygons),'bounds_m':bounds(vertices),
        'nonfinite_vertices':sum(not all(math.isfinite(c) for c in v) for v in vertices),
        'area_m2':sum(area),'degenerate_triangle_count':len(bad),'degenerate_triangle_ids':bad[:40],
        'uv_layer':uv.name if uv else None,'nonfinite_uv_corners':nonfinite_uv,'outside_0_1_uv_corners':outside_uv,
        'degenerate_uv_triangle_count':len(bad_uv),'degenerate_uv_triangle_ids':bad_uv[:40],
        'uv_bounds':[[min(p[i] for p in uvpoints),max(p[i] for p in uvpoints)] for i in range(2)] if uvpoints else None,
        'atlas_pixels':atlas,'target_px_per_m':target,'measured_triangle_px_per_m':stats(dvals),
        'density_outliers_over_5_percent_count':len(outliers),'density_worst_outliers':outliers[:10],
        'negative_z_normals_count':down,'normal_z_distribution':stats(normz),'uv_islands':island_info,
        'uv_exception':'Full-card steam UV reuse intentional; density not targeted.' if name=='SM_Steam' else None}

terrain=bvh(meshes['SM_Terrain']);path=bvh(meshes['SM_Path']);stone=bvh(meshes['SM_Stone'])
def summarize_samples(samples):
    valid=[s for s in samples if s.get('clearance_m') is not None]
    ordered=sorted(valid,key=lambda s:s['clearance_m'])
    return {'sample_count':len(samples),'missing_terrain_count':len(samples)-len(valid),
        'clearance_m':stats([s['clearance_m'] for s in valid]),
        'terrain_above_by_more_than_0_0001m_count':sum(s['clearance_m']<-.0001 for s in valid),
        'terrain_above_by_more_than_0_005m_count':sum(s['clearance_m']<-.005 for s in valid),
        'clearance_above_0_25m_count':sum(s['clearance_m']>.25 for s in valid),
        'worst_buried_samples':ordered[:12],'highest_clearance_samples':list(reversed(ordered[-6:]))}
all_samples=[];exposed=[];topward_exposed=0;downward_exposed=0
for p in meshes['SM_Path'].data.polygons:
    v=triangle_points(meshes['SM_Path'],p)
    n=(v[1]-v[0]).cross(v[2]-v[0]).normalized()
    points=[('vertex_'+str(i),p) for i,p in enumerate(v)] + [('centroid',sum(v,Vector())/3)] + [('edge_midpoint_'+str(i),(v[i]+v[(i+1)%3])/2) for i in range(3)]
    for kind,pt in points:
        t=cast(terrain,pt.x,pt.y);h=cast(path,pt.x,pt.y)
        item={'triangle':p.index,'sample_kind':kind,'position_m':vec(pt),'terrain_z_m':t['z'] if t else None,
              'clearance_m':pt.z-t['z'] if t else None,'normal_z':float(n.z)}
        all_samples.append(item)
        # Sheet normals can be reversed: use highest same-XY path intersection, not winding,
        # to isolate exposed walking surfaces. Side and underside faces are intentionally embedded.
        if abs(n.z)>.5 and h and abs(h['z']-pt.z)<.001:
            exposed.append(item)
            if n.z<0:downward_exposed+=1
            else:topward_exposed+=1
result['path_clearance']={'sampling':'Every saved Path triangle: all 3 vertices, centroid, all 3 edge midpoints. Duplicate samples retained.',
    'all_triangles_including_apron_sides_and_undersides':summarize_samples(all_samples),
    'exposed_walking_surfaces':summarize_samples(exposed),'exposed_sample_winding':{'upward':topward_exposed,'downward':downward_exposed}}
route_samples=[]
for si,(pa,pb) in enumerate(zip(manifest['route'],manifest['route'][1:])):
    a,b=Vector(pa),Vector(pb);count=max(1,math.ceil((b-a).length/.25))
    for i in range(count+1):
        pt=a+(b-a)*i/count;t=cast(terrain,pt.x,pt.y);h=cast(path,pt.x,pt.y)
        route_samples.append({'segment':si,'t':i/count,'position_m':vec(pt),'terrain_z_m':t['z'] if t else None,
            'path_z_m':h['z'] if h else None,'clearance_m':h['z']-t['z'] if t and h else None,
            'path_minus_design_z_m':h['z']-pt.z if h else None})
result['route_centerline']={'spacing_max_m':.25,'summary':summarize_samples(route_samples),'samples':route_samples}

stone_comps=[]
for indices in components(meshes['SM_Stone']):
    pts=[meshes['SM_Stone'].matrix_world@meshes['SM_Stone'].data.vertices[i].co for i in indices]
    stone_comps.append({'indices':indices,'points':pts,'bounds':bounds(pts)})
foundations=[]
for b in [b for b in manifest['semantic_objects'] if b['type']=='building']:
    x,y,z=b['center'];w,d=b['footprint']
    match=[c for c in stone_comps if abs(sum(c['bounds'][0])/2-x)<.01 and abs(sum(c['bounds'][1])/2-y)<.01 and abs(c['bounds'][2][0]-b['foundation_bottom'])<.01 and abs(c['bounds'][0][1]-c['bounds'][0][0]-(w+.45))<.01]
    item={'name':b['name'],'center':b['center'],'matched_saved_mesh_components':len(match),'samples':[]}
    if len(match)==1:
        c=match[0];item['actual_bounds_m']=c['bounds'];bottom=c['bounds'][2][0];top=c['bounds'][2][1]
        pts=[p for p in c['points'] if p.z<bottom+.0001]
        for sx,sy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            corner=max(pts,key=lambda p:sx*(p.x-x)+sy*(p.y-y));t=cast(terrain,corner.x,corner.y)
            item['samples'].append({'corner_sign':[sx,sy],'actual_bottom_vertex_m':vec(corner),
                'terrain_z_m':t['z'] if t else None,'bottom_clearance_m':corner.z-t['z'] if t else None,
                'terrain_above_foundation_top_m':t['z']-top if t else None})
        item['unsupported_corner_count']=sum(s['bottom_clearance_m'] is None or s['bottom_clearance_m']>.005 for s in item['samples'])
        item['terrain_above_foundation_top_corner_count']=sum(s['terrain_above_foundation_top_m'] is not None and s['terrain_above_foundation_top_m']>.005 for s in item['samples'])
    foundations.append(item)
result['foundations']=foundations

stair_results=[]
for stair in manifest['stairs']:
    a,b=Vector(stair['start']),Vector(stair['end']);cx=a.x;ymin,ymax=sorted([a.y,b.y]);count=round((b.z-a.z)/stair['riser_m']);run=stair['tread_m']
    samples=[];matches=[]
    # Separate stair components from other Stone objects using their actual AABBs.
    for c in stone_comps:
        bb=c['bounds'];mx=sum(bb[0])/2;my=sum(bb[1])/2
        if abs(mx-cx)<.01 and ymin-.1<my<ymax+.1 and abs(bb[0][1]-bb[0][0]-2.6)<.01 and abs(bb[1][1]-bb[1][0]-(run+.03))<.01:
            matches.append(c)
    matches.sort(key=lambda c:sum(c['bounds'][1]))
    for step,c in enumerate(matches):
        bb=c['bounds'];top=bb[2][1]
        for xi in [-.95,0,.95]:
            for yi in [.1,.5,.9]:
                x=cx+xi;y=bb[1][0]+(bb[1][1]-bb[1][0])*yi
                t=cast(terrain,x,y);h=cast(stone,x,y)
                # At these inset sample positions, actual tread should be its flat top.
                samples.append({'step':step,'position_m':[x,y,top],'terrain_z_m':t['z'] if t else None,
                    'stone_z_m':h['z'] if h else None,'clearance_m':top-t['z'] if t else None,
                    'actual_tread_bottom_z_m':bb[2][0],'bottom_clearance_m':bb[2][0]-t['z'] if t else None})
    bottom_samples=[dict(s,clearance_m=s['bottom_clearance_m'],position_m=[s['position_m'][0],s['position_m'][1],s['actual_tread_bottom_z_m']]) for s in samples]
    stair_results.append({'start':stair['start'],'end':stair['end'],'expected_treads':count,'matched_saved_components':len(matches),
        'sample_pattern':'3 width positions x 3 longitudinal inset positions per actual saved tread component',
        'summary':summarize_samples(samples),'samples':samples,
        'bottom_grounding_summary':summarize_samples(bottom_samples),
        'unsupported_bottom_samples_over_5mm':sum(s['bottom_clearance_m'] is None or s['bottom_clearance_m']>.005 for s in samples)})
result['stairs']=stair_results

bathstone=bvh(meshes['SM_BathStone']);water=bvh(meshes['SM_Water']);pool_results=[]
for p in manifest['pools']:
    samples=[]
    for r in [0,.25,.5,.7,.85,.95]:
        for angle in ([0] if r==0 else [i*2*math.pi/16 for i in range(16)]):
            x=p['x']+p['rx']*r*math.cos(angle);y=p['y']+p['ry']*r*math.sin(angle)
            t=cast(terrain,x,y);s=cast(bathstone,x,y);w=cast(water,x,y)
            samples.append({'radius_fraction':r,'xy_m':[x,y],'water_z_m':w['z'] if w else None,'terrain_z_m':t['z'] if t else None,
                'stone_z_m':s['z'] if s else None,'water_above_terrain_m':w['z']-t['z'] if w and t else None,
                'water_above_stone_m':w['z']-s['z'] if w and s else None})
    pool_results.append({'name':p['name'],'semantic_water_to_center_bottom_m':next(b['water_z']-b['bottom_z'] for b in manifest['semantic_objects'] if b['type']=='bath' and b['name']==p['name']),
        'saved_center_geometry':samples[0],'samples':samples,'water_above_terrain_m':stats([s['water_above_terrain_m'] for s in samples if s['water_above_terrain_m'] is not None]),
        'water_terrain_intrusion_samples_over_5mm':sum(s['water_above_terrain_m'] is not None and s['water_above_terrain_m']<-.005 for s in samples)})
result['pools']=pool_results
# Visibility of the actual saved stream surface against saved terrain. The author's
# main-route crossing band is explicitly classified as a bridge/culvert exception;
# this geometric classification does not by itself assert a visible bridge render.
stream_samples=[]
def route_distance_xy(x,y):
    best=(float('inf'),None,None)
    for i,(a,b) in enumerate(zip(manifest['route'],manifest['route'][1:])):
        dx=b[0]-a[0];dy=b[1]-a[1]
        t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
        dist=math.hypot(x-a[0]-dx*t,y-a[1]-dy*t)
        if dist<best[0]:best=(dist,i,t)
    return best
for p in meshes['SM_Stream'].data.polygons:
    pts=triangle_points(meshes['SM_Stream'],p)
    normal=(pts[1]-pts[0]).cross(pts[2]-pts[0]).normalized()
    if normal.z<=0:continue
    pt=sum(pts,Vector())/3;t=cast(terrain,pt.x,pt.y);distance,segment,progress=route_distance_xy(pt.x,pt.y)
    stream_samples.append({'triangle':p.index,'position_m':vec(pt),'terrain_z_m':t['z'] if t else None,
        'clearance_m':pt.z-t['z'] if t else None,'normal_z':float(normal.z),
        'main_route_distance_xy_m':distance,'nearest_route_segment':segment,
        'classification':'route_crossing_culvert_exception' if distance<2.2 else 'outside_main_route'})
outside=[s for s in stream_samples if s['classification']=='outside_main_route']
crossing=[s for s in stream_samples if s['classification']=='route_crossing_culvert_exception']
result['stream_visibility']={'sampling':'Centroid of every actual saved SM_Stream triangle with upward normal; terrain BVH downward raycast.',
    'route_exception_policy':'Centroid XY distance < 2.2m from manifest main route is classified as intentional culvert/bridge crossing by parent request.',
    'all_upward_triangles':summarize_samples(stream_samples),'outside_main_route':summarize_samples(outside),
    'route_crossing_culvert_exception':summarize_samples(crossing),'samples':stream_samples,
    'unintended_buried_centroids_over_5mm':[s for s in outside if s['clearance_m'] is not None and s['clearance_m']<-.005]}
# Direct support below the largest Path/terrain gaps; this avoids treating protruding
# rim rocks or solid stair geometry beneath a sheet as an unsupported air space.
support_trees={name:bvh(meshes[name]) for name in ['SM_Stone','SM_BathStone','SM_Cedar','SM_DarkWood']}
support_samples=[]
candidate_samples=result['path_clearance']['exposed_walking_surfaces']['highest_clearance_samples']+result['route_centerline']['summary']['highest_clearance_samples']
for s in candidate_samples:
    pos=s['position_m'][:]
    if 'path_z_m' in s:pos[2]=s['path_z_m']
    supports=[]
    for name,tree in support_trees.items():
        loc,norm,face,dist=tree.ray_cast(Vector((pos[0],pos[1],pos[2]-.001)),Vector((0,0,-1)),100)
        if loc is not None:supports.append({'mesh':name,'z_m':float(loc.z),'gap_below_path_m':pos[2]-loc.z})
    support_samples.append({'path_position_m':pos,'terrain_z_m':s['terrain_z_m'],'terrain_clearance_m':s['clearance_m'],
        'other_geometry_below_path':sorted(supports,key=lambda x:x['gap_below_path_m'])})
result['worst_path_gap_other_support_checks']=support_samples
result['source_unchanged_during_inspection']=all(sha(W/p)==h for p,h in hashes.items())
result['finished_at_utc']=datetime.now(timezone.utc).isoformat();result['elapsed_seconds']=time.monotonic()-t0
result['summary']={'mesh_count':len(meshes),'total_triangles':sum(len(o.data.polygons) for o in meshes.values()),
    'nonfinite_vertex_count':sum(r['nonfinite_vertices'] for r in result['meshes'].values()),
    'degenerate_triangle_count':sum(r['degenerate_triangle_count'] for r in result['meshes'].values()),
    'nonfinite_uv_count':sum(r['nonfinite_uv_corners'] for r in result['meshes'].values()),
    'uv_outside_count':sum(r['outside_0_1_uv_corners'] for r in result['meshes'].values()),
    'degenerate_uv_triangle_count':sum(r['degenerate_uv_triangle_count'] for r in result['meshes'].values()),
    'uv_density_outliers_over_5_percent_count':sum(r['density_outliers_over_5_percent_count'] for r in result['meshes'].values()),
    'path_min_exposed_clearance_m':result['path_clearance']['exposed_walking_surfaces']['clearance_m']['min'],
    'path_exposed_terrain_above_5mm_count':result['path_clearance']['exposed_walking_surfaces']['terrain_above_by_more_than_0_005m_count'],
    'unsupported_foundation_corners':sum(r.get('unsupported_corner_count',4) for r in foundations),
    'terrain_above_foundation_top_corners_over_5mm':sum(r.get('terrain_above_foundation_top_corner_count',4) for r in foundations),
    'unsupported_stair_bottom_samples_over_5mm':sum(r['unsupported_bottom_samples_over_5mm'] for r in stair_results),
    'stream_outside_route_buried_centroids_over_5mm':len(result['stream_visibility']['unintended_buried_centroids_over_5mm']),
    'buried_stair_tread_samples_over_5mm':sum(r['summary']['terrain_above_by_more_than_0_005m_count'] for r in stair_results)}
OUT.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
print('INDEPENDENT_GEOMETRY_AUDIT',json.dumps(result['summary']))
print('SAVED',OUT)
