import bpy,json,math
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/DesertVillage/max')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'SourceArt/DesertVillage_Original.blend'))
spec=json.loads((ROOT/'SourceArt/source_manifest.json').read_text())['materials'];values=defaultdict(list);bad=[];triangles=0
for o in bpy.context.scene.objects:
    if o.type!='MESH':continue
    m=o.data;m.calc_loop_triangles();uv=m.uv_layers.active
    for tr in m.loop_triangles:
        p=[m.vertices[i].co for i in tr.vertices];area=(p[1]-p[0]).cross(p[2]-p[0]).length*.5
        if area<1e-10:continue
        coords=[uv.data[i].uv for i in tr.loops];a,b,c=coords;uvarea=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
        mat=m.materials[tr.material_index].name;density=512*math.sqrt(uvarea/area);triangles+=1
        values[mat].append((density,area,uvarea))
        if uvarea<1e-12:bad.append({'mesh':o.name,'triangle':tr.index,'material':mat,'surface_area_m2':area})
materials={}
for name,vals in values.items():
    textured=bool(spec[name]['texture']);scale=spec[name]['uv_meters_per_repeat'];dens=sorted(d for d,a,u in vals)
    materials[name]={'texture':spec[name]['texture'],'texture_size':[512,512] if textured else None,'target_pixels_per_m':512/scale if textured and scale else None,'uv_repeat_m':scale,'surface_area_m2':sum(a for d,a,u in vals),'uv_area_with_repeats':sum(u for d,a,u in vals),'measured_area_weighted_density_px_per_m':sum(d*a for d,a,u in vals)/sum(a for d,a,u in vals),'density_p05':dens[int(len(dens)*.05)],'density_p95':dens[min(len(dens)-1,int(len(dens)*.95))],'density_min':min(dens),'density_max':max(dens)}
result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'triangle_count_nonzero_area':triangles,'degenerate_uv_triangles':len(bad),'degenerate_uv_details':bad,'materials':materials,'mapping':'World-meter dominant-normal box projection AFTER bevel. Deliberate overlapping/repeating UVs; not a unique atlas or baked lightmap. Rugs preserve full0-1 artwork UVs and variable aspect ratio.','padding':'Repeating textures are full tile images with no UV-island packing or unique-atlas padding requirement; rug border artwork provides4% inset.','density_exception':'Curved/slope faces project onto dominant axis and have density reduced by square-root of normal projection. Small cloth weave uses0.5m repeats; rug dimensions produce different directional density. Untextured solids do not have meaningful texel-density targets.','passed':len(bad)==0}
(ROOT/'Validation/uv_density_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('UV audit',result['passed'],'nonzero-area triangles',triangles,'degenerateUV',len(bad))
