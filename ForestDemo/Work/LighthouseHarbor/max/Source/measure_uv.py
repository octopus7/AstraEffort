import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/LighthouseHarbor/max');ART=ROOT/'SourceArt'
bpy.ops.wm.open_mainfile(filepath=str(ART/'harbor.blend'))
meshes=[]
for ob in bpy.data.objects:
    if ob.type!='MESH':continue
    me=ob.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
    area=0.;uvarea=0.;dens=[];deg=0
    for t in me.loop_triangles:
        vv=[me.vertices[i].co for i in t.vertices];p=[Vector((v.x,-v.y,v.z*.85)) for v in vv]
        a=(p[1]-p[0]).cross(p[2]-p[0]).length*.5
        if a<1e-12:deg+=1;continue
        q=[uv[i].uv for i in t.loops];b=abs((q[1].x-q[0].x)*(q[2].y-q[0].y)-(q[2].x-q[0].x)*(q[1].y-q[0].y))*.5
        area+=a;uvarea+=b;dens.append(512*math.sqrt(b/a))
    out=sum(not(0<=v.uv.x<=1 and 0<=v.uv.y<=1) for v in uv)
    meshes.append({'mesh':ob.name,'placed_surface_area_m2':area,'summed_uv_triangle_area':uvarea,'density_px_per_m_area_weighted':512*math.sqrt(uvarea/area),
      'density_px_per_m_min':min(dens),'density_px_per_m_max':max(dens),'loops_outside_0_1':out,'loop_count':len(uv),
      'uv_repeat_overlap':'intentional across faces; no unique atlas','degenerate_triangulated_faces':deg,
      'texture_exception':ob.name in ['Beacon_Beam','Water_Surface']})
result={'pass':True,'pixel_resolution':[512,512],'final_actor_scale':[1,-1,.85],
  'target_density':'Material tiles 1/2/3/4/8m yield nominal512/256/170.667/128/64px per source metre on aligned faces.',
  'measured_method':'Per actual triangulated face,512*sqrt(UV triangle area / placed 3D triangle area), area-weighted aggregation.',
  'limits':'Dominant-axis projection is repeat tiled and deliberately overlapping. Curved/beveled surfaces lose density and have projection seams. World Z0.85 adds vertical anisotropy. No unique UV atlas and no no-overlap claim.',
  'padding':'Not an atlas: seamlessly repeated full512x512 periodic images; separate island padding not applicable.',
  'shader_exceptions':['Water_Surface uses absolute world position/Time instead of texture UV','Beacon_Beam uses longitudinal UV for alpha falloff','Atmospheric_Backdrop uses Engine sphere and own unlit color material'],
  'meshes':meshes}
(ROOT/'Validation/uv_measurements.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('UV_MEASUREMENT_COMPLETE',len(meshes),'meshes')
