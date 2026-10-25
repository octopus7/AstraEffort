"""Inspect actual exported binary FBX with Blender's installed standard-library parser."""
from pathlib import Path
from datetime import datetime, timezone
import importlib, json, sys, types, math
from collections import defaultdict
addon=Path('C:/Program Files/Blender Foundation/Blender 5.0/5.0/scripts/addons_core/io_scene_fbx')
package=types.ModuleType('own_fbx_audit');package.__path__=[str(addon)];sys.modules[package.__name__]=package
parser=importlib.import_module(package.__name__+'.parse_fbx')
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/DesertVillage/max')
def walk(n):
    yield n
    for c in n.elems:yield from walk(c)
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def inspect(path):
    tree,version=parser.parse(str(path));result={'file':path.name,'version':version,'closed_components':0,'open_components':0,'negative_closed_components':0,'normal_samples':0,'opposite_normals':0,'properties':{}}
    for node in walk(tree):
        if node.id==b'P' and node.props[0] in [b'UnitScaleFactor',b'Lcl Scaling',b'UpAxis',b'FrontAxis',b'CoordAxis']:
            result['properties'][str(node.props[0])]=[str(x) if isinstance(x,bytes) else x for x in node.props[4:]]
        if node.id!=b'Geometry':continue
        cs={x.id:x for x in node.elems}
        if b'Vertices' not in cs:continue
        raw=cs[b'Vertices'].props[0];vertices=list(zip(raw[::3],raw[1::3],raw[2::3]));faces=[];current=[];indices=[];loop=0
        for value in cs[b'PolygonVertexIndex'].props[0]:
            current.append(value if value>=0 else -value-1)
            if value<0:faces.append(current);indices.append(loop);loop+=len(current);current=[]
        par=list(range(len(vertices)))
        def find(i):
            while par[i]!=i:par[i]=par[par[i]];i=par[i]
            return i
        for f in faces:
            for v in f[1:]:par[find(v)]=find(f[0])
        parts=defaultdict(list)
        for f in faces:parts[find(f[0])].append(f)
        for fs in parts.values():
            edges=defaultdict(int);volume=0.;ref=vertices[fs[0][0]]
            for f in fs:
                for a,b in zip(f,f[1:]+f[:1]):edges[tuple(sorted((a,b)))]+=1
                a=sub(vertices[f[0]],ref)
                for i in range(1,len(f)-1):volume+=dot(a,cross(sub(vertices[f[i]],ref),sub(vertices[f[i+1]],ref)))/6
            closed=all(n==2 for n in edges.values());result['closed_components' if closed else 'open_components']+=1
            if closed and volume< -1e-9:result['negative_closed_components']+=1
        norm=cs.get(b'LayerElementNormal')
        if norm:
            nc={x.id:x for x in norm.elems};raw=nc[b'Normals'].props[0];normals=list(zip(raw[::3],raw[1::3],raw[2::3]));mapping=nc[b'MappingInformationType'].props[0];index=nc.get(b'NormalsIndex')
            for fi,f in enumerate(faces):
                n=(0.,0.,0.)
                for j in range(1,len(f)-1):
                    cr=cross(sub(vertices[f[j]],vertices[f[0]]),sub(vertices[f[j+1]],vertices[f[0]]));n=tuple(a+b for a,b in zip(n,cr))
                if dot(n,n)<1e-16:continue
                for li,vi in enumerate(f):
                    ni=indices[fi]+li if mapping==b'ByPolygonVertex' else (vi if mapping==b'ByVertice' else fi)
                    if index:ni=index.props[0][ni]
                    val=dot(n,normals[ni]);result['normal_samples']+=1
                    if val < -1e-8:
                        result['opposite_normals']+=1
                        result.setdefault('opposite_normal_examples',[])
                        if len(result['opposite_normal_examples'])<16:result['opposite_normal_examples'].append({'face':fi,'corner':li,'face_vertices':[vertices[i] for i in f],'normal':normals[ni],'dot':val,'face_cross_length':math.sqrt(dot(n,n))})
    return result
results=[inspect(p) for p in sorted((ROOT/'SourceArt/FBX').glob('*.fbx'))]
out={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'method':'Actual FBX connected-component signed volume, translated origin and double precision; vertex normal agreement with polygon normal; positive model scaling checked.','results':results,'closed_components':sum(x['closed_components'] for x in results),'negative_closed_components':sum(x['negative_closed_components'] for x in results),'opposite_normals':sum(x['opposite_normals'] for x in results)}
out['passed']=out['negative_closed_components']==0 and out['opposite_normals']==0
(ROOT/'Validation/fbx_geometry_validation.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='results'}))
for r in results:
    if r['negative_closed_components'] or r['opposite_normals']:print(json.dumps(r))
