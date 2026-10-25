"""Reimport delivered FBX and measure geometry and both UV channels. No UE claims."""
import bpy, os, json, math, datetime, collections
from mathutils import Vector
ROOT=r'D:/github/AstraEffort/ForestDemo/Work/RainyCanal/ultra/Art/Props'
START=datetime.datetime.now(datetime.timezone.utc)
manifest=json.load(open(ROOT+'/manifest.json',encoding='utf8'))

def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def uvarea(t): return abs(cross(*t))*.5
def tris_overlap(a,b):
    for tri in [a,b]:
        for i in range(3):
            p,q=tri[i],tri[(i+1)%3]; ax,ay=q[1]-p[1],p[0]-q[0]
            norm=math.hypot(ax,ay)
            if norm<1e-12: continue
            pa=[(p[0]*ax+p[1]*ay)/norm for p in a]
            pb=[(p[0]*ax+p[1]*ay)/norm for p in b]
            if min(max(pa),max(pb))-max(min(pa),min(pb))<=1e-7: return False
    return True

def pseg(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]; denom=dx*dx+dy*dy
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/denom)) if denom else 0
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
def sdist(a,b,c,d):
    if cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0: return 0
    return min(pseg(a,c,d),pseg(b,c,d),pseg(c,a,b),pseg(d,a,b))

def cellrange(points,expand=0,size=64):
    minx=min(v[0] for v in points)-expand; maxx=max(v[0] for v in points)+expand
    miny=min(v[1] for v in points)-expand; maxy=max(v[1] for v in points)+expand
    for x in range(math.floor(minx*size),math.floor(maxx*size)+1):
        for y in range(math.floor(miny*size),math.floor(maxy*size)+1): yield (x,y)

results=[]
for item in manifest['assets']:
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=ROOT+'/'+item['filename'])
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert len(objects)==1,(item['name'],'not exactly one object')
    obj=objects[0]; data=obj.data; data.calc_loop_triangles()
    tris=list(data.loop_triangles); uvs=data.uv_layers
    pos=[obj.matrix_world@v.co for v in data.vertices]
    bounds=[[min(v[k] for v in pos),max(v[k] for v in pos)] for k in range(3)]
    triangles=[]; ratios=[]; degenerate_uv=[0,0]; degenerate_geo=0
    edge_uses=collections.defaultdict(list)
    for ti,tri in enumerate(tris):
        p=[pos[i] for i in tri.vertices]; area=(p[1]-p[0]).cross(p[2]-p[0]).length*.5
        if area<1e-12: degenerate_geo+=1
        for ui in range(2):
            tc=[tuple(uvs[ui].data[li].uv) for li in tri.loops]
            ar=uvarea(tc)
            if ar<1e-12: degenerate_uv[ui]+=1
            if ui==1 and area>1e-12: ratios.append(math.sqrt(ar/area)*1024)
            if ui==0: triangles.append(tc)
        tc=triangles[-1]
        for k in range(3):
            va,vb=tri.vertices[k],tri.vertices[(k+1)%3]
            a,b=tc[k],tc[(k+1)%3]
            ends=sorted([(va,round(a[0],7),round(a[1],7)),(vb,round(b[0],7),round(b[1],7))])
            edge_uses[tuple(ends)].append((ti,a,b))
    parents=list(range(len(tris)))
    def find(i):
        while parents[i]!=i: parents[i]=parents[parents[i]]; i=parents[i]
        return i
    for uses in edge_uses.values():
        if len(uses)==2: parents[find(uses[1][0])]=find(uses[0][0])
    roots=[find(i) for i in range(len(tris))]
    bins=collections.defaultdict(list); pairs=set(); overlap=[]
    for i,tri in enumerate(triangles):
        for cell in cellrange(tri):
            for j in bins[cell]:
                pair=(j,i)
                if pair in pairs: continue
                pairs.add(pair)
                if tris_overlap(tri,triangles[j]): overlap.append(pair)
            bins[cell].append(i)
    # Measure nearest boundary separation within an 8px search radius.
    segments=[]
    for uses in edge_uses.values():
        if len(uses)==1:
            ti,a,b=uses[0]; segments.append((a,b,roots[ti]))
    bins=collections.defaultdict(list); pairs=set(); mingap=8/1024; gap_violations=[]
    for i,(a,b,root) in enumerate(segments):
        for cell in cellrange([a,b],8/1024):
            for j in bins[cell]:
                c,d,otherroot=segments[j]
                if root==otherroot or (j,i) in pairs: continue
                pairs.add((j,i)); dist=sdist(a,b,c,d)
                mingap=min(mingap,dist)
                if dist<2/1024-1e-6: gap_violations.append((j,i,dist*1024))
            bins[cell].append(i)
    bounds_error=max(abs(bounds[k][v]-item['bounds_m'][k][v]) for k in range(3) for v in range(2))
    uv0bounds=[[min(p[k] for tri in triangles for p in tri),max(p[k] for tri in triangles for p in tri)] for k in range(2)]
    ratios.sort()
    density={'min':min(ratios),'p01':ratios[int(len(ratios)*.01)],'median':ratios[len(ratios)//2],
             'p99':ratios[int(len(ratios)*.99)],'max':max(ratios),
             'target':128,'outside_1pct_count':sum(abs(r-128)>1.28 for r in ratios)}
    bridge_probes={}
    if item['name']=='SM_StoneBridge':
        probes=[]
        for x in [-7.999,-6,-4,-2,0,2,4,6,7.999]:
            hit,point,normal,index=obj.ray_cast(Vector((x,0,5)),Vector((0,0,-1)),distance=10)
            probes.append({'x_m':x,'hit':hit,'deck_z_m':point.z if hit else None})
        open_water=not obj.ray_cast(Vector((0,-10,-.5)),Vector((0,1,0)),distance=20)[0]
        bridge_probes={'centerline_downward_rays':probes,'open_transverse_ray_at_x0_z_minus0_5':open_water,
                       'analytic_max_deck_slope_degrees':math.degrees(math.atan(2.2/8))}
    passed=len(tris)<15000 and len(uvs)==2 and bounds_error<.0001 and not any(degenerate_uv) and not degenerate_geo and not overlap and not gap_violations and density['outside_1pct_count']==0
    res={'name':item['name'],'passed':passed,'triangles':len(tris),'uv_channels':[u.name for u in uvs],
         'materials':[m.name.split('.')[0] for m in data.materials], 'bounds_m':bounds,
         'fbx_roundtrip_max_bounds_error_m':bounds_error,'geometry_degenerate_triangles':degenerate_geo,
         'uv_degenerate_triangles':degenerate_uv,'uv0_bounds':uv0bounds,
         'uv0_island_count':len(set(roots)),'uv0_positive_area_overlap_pairs':len(overlap),
         'uv0_overlap_sample':overlap[:5],'uv0_minimum_island_gap_px_at1024':mingap*1024,
         'uv0_gap_search_limit_px':8,'uv0_gap_at_search_limit_means_at_least':True,
         'uv0_padding_below2px_pairs':len(gap_violations),'uv0_padding_violation_sample':gap_violations[:5],
         'uv1_texel_density_px_per_m_at1024':density,
         'source_geometry_bridge_probes':bridge_probes,
         'uv1_overlap_policy':'Intentional periodic physical-space mapping; UV1 is not a lightmap.'}
    results.append(res); print('VALIDATED',json.dumps(res),flush=True)

report={'started_at_utc':START.isoformat(),'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'method':'Fresh Blender FBX import of each mesh. 2D separating-axis test on all UV0 triangle candidates, adjacency-based island boundaries and segment-distance padding audit.',
        'all_passed':all(r['passed'] for r in results),'assets':results,
        'scope_limitations':['No Unreal runtime or collision test performed by this prop subagent.',
            'UV1 overlap is intentional to maintain physical density. Use channel 1 in tiled surface materials.',
            'Material slots are supplied with source preview colors; parent supplies final UE textures/materials.']}
json.dump(report,open(ROOT+'/validation.json','w',encoding='utf8'),indent=2)
print('VALIDATION_COMPLETE',report['all_passed'],flush=True)
