"""Owned scaled mesh variants with disjoint, metric triangle UV islands.
Every triangle is flattened isometrically: density 32 px/metre, zero stretch.
Shelf rectangles enclose each island and are separated by >=3 source pixels.
"""
import bpy, json, math, time, datetime, struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/ultra')
OUT=ROOT/'TexturePass'; ART=OUT/'SourceArt'; ART.mkdir(exist_ok=True)
DATA=json.loads((ROOT/'scene_manifest.json').read_text())
N=struct.unpack('>I',(OUT/'Generated/Bark.png').read_bytes()[16:20])[0]
DENSITY=32.0; PAD=1.5
started=time.time()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'SourceArt/Quietwater_Source.blend'))
prototypes={n:bpy.data.objects[n] for n in DATA['assets']}
report={'method':'Isometric per-triangle islands, longest edge horizontal, sorted shelf packing. Actor scale baked into geometry, actor reset to 1. No shared islands even between material slots. UV0 sampled unchanged by material.','texture_resolution':[N,N],'target_pixels_per_metre':DENSITY,'minimum_island_gap_pixels':2*PAD,'atlas_border_pixels':PAD,'exceptions':['Terrain, sea, lake and surf use continuous world-space procedural shading; no prop density target. Tiny plant faces can be subpixel at 32px/m. Triangle seams are deliberately numerous; no claim of hand-painted seam continuity. Non-power-of-two originals are kept unchanged, using no mips.'],'meshes':[]}
for index,item in enumerate(DATA['placements']):
 name=item['asset']
 if name in ['SM_Ground','SM_Sea','SM_Lake','SM_Surf']:continue
 source=prototypes[name].data; source.calc_loop_triangles();scale=item['scale']
 verts=[Vector((v.co.x*scale[0],v.co.y*scale[1],v.co.z*scale[2])) for v in source.vertices]
 triangles=list(source.loop_triangles); faces=[tuple(t.vertices) for t in triangles]
 islands=[]; total_world=0.0; degenerate=0
 for ti,t in enumerate(triangles):
  coords=[verts[v] for v in t.vertices]
  edges=[(coords[(j+1)%3]-coords[j]).length for j in range(3)]
  j=max(range(3),key=lambda k:edges[k]); k=(j+1)%3;l=(j+2)%3
  e=coords[k]-coords[j];length=e.length
  if length<1e-10:degenerate+=1;uvs=[(0,0)]*3;w=h=0;area=0
  else:
   x=(coords[l]-coords[j]).dot(e)/length
   height=(coords[l]-coords[j]).cross(e).length/length
   uvs=[None]*3;uvs[j]=(0.,0.);uvs[k]=(length*DENSITY,0.);uvs[l]=(x*DENSITY,height*DENSITY)
   minx=min(q[0] for q in uvs);maxx=max(q[0] for q in uvs)
   uvs=[(q[0]-minx,q[1]) for q in uvs];w=maxx-minx;h=height*DENSITY;area=length*height*.5
   if area<1e-12:degenerate+=1
  total_world+=area
  islands.append({'triangle':ti,'uv':uvs,'w':w,'h':h,'area':area})
 ordered=sorted(islands,key=lambda x:x['h'],reverse=True)
 px=py=0.;rowh=0.;rects=[]
 for island in ordered:
  rw=island['w']+2*PAD;rh=island['h']+2*PAD
  if px+rw>N:px=0;py+=rowh;rowh=0
  if py+rh>N:raise RuntimeError('Atlas overflow '+name+' '+str(index)+' at '+str(py+rh))
  island['packed']=[((x+px+PAD)/N,(y+py+PAD)/N) for x,y in island['uv']]
  island['rect']=[px,py,px+rw,py+rh];rects.append(island['rect'])
  px+=rw;rowh=max(rowh,rh)
 variant=name+'_UV_%04d'%index
 mesh=bpy.data.meshes.new(variant);mesh.from_pydata(verts,[],faces);mesh.update()
 for m in source.materials:mesh.materials.append(m)
 uv=mesh.uv_layers.new(name='UV_UniqueMetric')
 actual_areas=[];densities=[];minimum=1.;maximum=0.
 for poly,t,island in zip(mesh.polygons,triangles,islands):
  poly.material_index=t.material_index;poly.use_smooth=True
  p=island['packed']
  for li,xy in zip(poly.loop_indices,p):uv.data[li].uv=xy;minimum=min(minimum,*xy);maximum=max(maximum,*xy)
  a,b,c=p;area=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))*.5
  actual_areas.append(area)
  if island['area']>1e-12:densities.append(N*math.sqrt(area/island['area']))
 ob=bpy.data.objects.new(variant,mesh);bpy.context.collection.objects.link(ob)
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.fbx(filepath=str(ART/(variant+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',axis_forward='-Y',axis_up='Z',bake_anim=False,add_leaf_bones=False,use_mesh_modifiers=True)
 # Shelf proof: disjoint rectangles within rows; nonoverlapping row intervals.
 overlap=0
 for a,b in zip(ordered,ordered[1:]):
  ra,rb=a['rect'],b['rect']
  if ra[1]==rb[1] and rb[0]<ra[2]-1e-6:overlap+=1
  elif ra[1]!=rb[1] and rb[1]<ra[3]-1e-6:overlap+=1
 record={'placement_index':index,'source':name,'variant':variant,'baked_world_scale':scale,'final_actor_scale':[1,1,1],'world_surface_area_m2':total_world,'uv_area':sum(actual_areas),'density_area_weighted_px_m':N*math.sqrt(sum(actual_areas)/total_world),'density_triangle_min_px_m':min(densities),'density_triangle_max_px_m':max(densities),'triangles':len(triangles),'islands':len(triangles),'degenerate_triangles':degenerate,'uv_min':minimum,'uv_max':maximum,'overlapping_island_rectangles':overlap,'minimum_gap_px':2*PAD,'packed_height_px':py+rowh,'materials':DATA['assets'][name]['materials'],'collision':DATA['assets'][name]['collision']}
 report['meshes'].append(record)
 bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(mesh)
 if index%50==0:print('ULTRA_UV',index,flush=True);(OUT/'uv_report.json').write_text(json.dumps(report,indent=2))
report['elapsed_seconds']=time.time()-started
report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
report['success']=all(m['overlapping_island_rectangles']==0 and m['uv_min']>=0 and m['uv_max']<=1 and abs(m['density_area_weighted_px_m']-DENSITY)<.01 for m in report['meshes'])
(OUT/'uv_report.json').write_text(json.dumps(report,indent=2))
print('ULTRA_UV_SUCCESS',len(report['meshes']),report['success'],flush=True)

