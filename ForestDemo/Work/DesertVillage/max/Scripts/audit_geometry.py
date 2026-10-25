import bpy, json, sys, math
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/DesertVillage/max')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'SourceArt/DesertVillage_Original.blend'))
report={'meshes':{},'negative_closed_components':0,'closed_components':0,'open_components':0}
for obj in bpy.context.scene.objects:
    if obj.type!='MESH':continue
    m=obj.data;par=list(range(len(m.vertices)))
    def find(i):
        while par[i]!=i:par[i]=par[par[i]];i=par[i]
        return i
    def union(a,b):
        a=find(a);b=find(b)
        if a!=b:par[b]=a
    for e in m.edges:union(*e.vertices)
    parts=defaultdict(list)
    for p in m.polygons:parts[find(p.vertices[0])].append(p)
    components=[]
    for ps in parts.values():
        edges=defaultdict(int);volume=0.0
        ref=m.vertices[ps[0].vertices[0]].co.copy()
        for p in ps:
            vs=list(p.vertices)
            for a,b in zip(vs,vs[1:]+vs[:1]):edges[tuple(sorted((a,b)))]+=1
            p0=m.vertices[vs[0]].co-ref
            for i in range(1,len(vs)-1):volume+=p0.dot((m.vertices[vs[i]].co-ref).cross(m.vertices[vs[i+1]].co-ref))/6
        closed=all(v==2 for v in edges.values())
        if closed:report['closed_components']+=1
        else:report['open_components']+=1
        if closed and volume<-.000001:report['negative_closed_components']+=1
        components.append({'closed':closed,'signed_volume_m3':round(volume,8),'polygons':len(ps)})
    report['meshes'][obj.name]={'components':len(components),'closed':sum(x['closed'] for x in components),'negative_closed':sum(x['closed'] and x['signed_volume_m3']<-.000001 for x in components),'minimum_closed_volume':min([x['signed_volume_m3'] for x in components if x['closed']] or [0]),'component_details':components}
label=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'final'
out=ROOT/('Validation/geometry_normals_'+label+'.json');out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='meshes'}))
for k,v in report['meshes'].items():
    if v['negative_closed']:print(k,v['negative_closed'],v['minimum_closed_volume'])
