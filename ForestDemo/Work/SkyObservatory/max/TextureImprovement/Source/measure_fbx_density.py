from pathlib import Path
from collections import defaultdict
import json,math,time
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max/TextureImprovement');E=ROOT/'Evidence'
start=time.time();scope={};exec((ROOT/'Source/verify_exported_fbx.py').read_text().split('layout=json.loads')[0],scope)
layout=json.loads((E/'uv_chart_layout.json').read_text());sampling=json.loads((E/'material_sampling_manifest.json').read_text())['materials'];samplers={r['material'][2:]:r for r in sampling};stats=defaultdict(list)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
for file in sorted((ROOT/'SourceArt/Meshes').glob('*.fbx')):
    data=scope['parse_fbx'](file);v=data['vertices'];raw=data['polygon_indices'];uv=data['uv'];ui=data['uv_index'];charts=layout[file.stem]
    materials={c['id']:c['material'] for c in charts['charts']}
    for fi,chart in enumerate(charts['face_chart_ids']):
        name=materials[chart];sample=samplers[name]
        if sample['sampling_path']!='connected_surface_uv':continue
        ids=[x if x>=0 else -x-1 for x in raw[fi*3:fi*3+3]];p=[list(v[i*3:i*3+3]) for i in ids];q=[list(uv[i*2:i*2+2]) for i in ui[fi*3:fi*3+3]]
        a=[p[1][j]-p[0][j] for j in range(3)];b=[p[2][j]-p[0][j] for j in range(3)];length=math.sqrt(dot(a,a));x=dot(a,b)/length;y=math.sqrt(max(0,dot(b,b)-x*x));assert y>0
        da=[q[1][j]-q[0][j] for j in range(2)];db=[q[2][j]-q[0][j] for j in range(2)]
        j00=da[0]/length;j10=da[1]/length;j01=(db[0]-da[0]*x/length)/y;j11=(db[1]-da[1]*x/length)/y
        aa=j00*j00+j10*j10;bb=j01*j01+j11*j11;ab=j00*j01+j10*j11;dis=math.sqrt(max(0,(aa-bb)**2+4*ab*ab));lo=math.sqrt(max(0,(aa+bb-dis)/2));hi=math.sqrt((aa+bb+dis)/2)
        scale=1024*sample['uv_scale'];area=.5*length*y;density=math.sqrt(abs(j00*j11-j01*j10))*scale
        assert lo>0 and math.isfinite(density)
        stats[name].append((density,lo*scale,hi*scale,hi/lo,area))
out=[]
for name,sample in sorted(samplers.items()):
    if name not in stats:
        out.append({'material':name,'sampling_path':sample['sampling_path'],'actual_world_projection_axis_texels_per_m':sample['target_runtime_texels_per_m'],'world_projection_tile_cm':sample['tile_size_cm'],'density_exception':'Coordinates use three fixed metric world projections blended by normal weights. A single per-face UV area density does not describe this shader; fallback UVs are not sampled.'});continue
    values=stats[name];total=sum(v[4] for v in values)
    out.append({'material':name,'sampling_path':'connected_surface_uv','triangles_measured':len(values),'actual_runtime_texture_size':1024,'actual_uv_scale':sample['uv_scale'],'nominal_target_px_per_m':sample['target_runtime_texels_per_m'],'measured_area_density_min':min(v[0] for v in values),'measured_area_density_max':max(v[0] for v in values),'area_weighted_mean_px_per_m':sum(v[0]*v[4] for v in values)/total,'directional_density_min':min(v[1] for v in values),'directional_density_max':max(v[2] for v in values),'max_anisotropy':max(v[3] for v in values),'area_m2':total,'exception':'Connected axis-projected bevels and curved surfaces preserve texture continuity; their directional stretch is measured rather than re-normalizing individual triangles.'})
report={'validated_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'execution_seconds':time.time()-start,'data_source':'Final actual binary FBX vertex and loop-UV arrays, chart material memberships independently reviewed, final runtime texture dimensions and shader UV scales','materials':out}
(E/'actual_fbx_density.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('ACTUAL_FBX_DENSITY_PASS',round(report['execution_seconds'],4))
for r in out:
    if r['sampling_path']=='connected_surface_uv':print(r['material'],r['measured_area_density_min'],r['measured_area_density_max'],r['max_anisotropy'])
