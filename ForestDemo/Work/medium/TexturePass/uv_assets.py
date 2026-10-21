import bpy, math, json, os
from mathutils import Vector
ROOT='D:/github/AstraEffort/ForestDemo/Work/medium'
OUT=ROOT+'/TexturePass/Source'; DENSITY=16.; SIZE=1254; HALF=627; PAD=2
layout=json.load(open(ROOT+'/layout.json'))['layout']
groups={}
for p in layout:groups.setdefault(p['mesh'],set()).add(round(p['scale']*10)/10)
report={'target_pixels_per_world_meter':DENSITY,'atlas_size':[SIZE,SIZE],'island_gap_pixels':PAD*2,'quadrant_edge_padding_pixels':4,'method':'Every triangle is an independent rigid planar island with exact metric area; disjoint shelf rectangles conservatively prove no within-quadrant overlap. Scale variants bake nearest 0.1 world scale. Actor scales become 1. Shared atlases intentionally reused between mesh assets and instances.','meshes':[],'scale_max_absolute_change':max(abs(p['scale']-round(p['scale']*10)/10) for p in layout)}
def surface(slot):
 if slot in ['Bark','Wood']:return 0
 if slot.startswith('Leaf'):return 1
 if slot.startswith('Rock'):return 2
 return 3
for name,scales in sorted(groups.items()):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.fbx(filepath=ROOT+'/Source/'+name+'.fbx')
 o=next(o for o in bpy.context.scene.objects if o.type=='MESH');bpy.context.view_layer.objects.active=o;o.select_set(True)
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 mod=o.modifiers.new('UV triangle islands','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
 base=o.data.copy()
 for scale in sorted(scales):
  o.data=base.copy();me=o.data
  for v in me.vertices:v.co*=scale
  me.update();uv=me.uv_layers.active or me.uv_layers.new(name='UVMap')
  regions={i:[] for i in range(4)}
  for p in me.polygons:
   a,b,c=[me.vertices[i].co for i in p.vertices];e=b-a;length=e.length
   if length<1e-9:raise RuntimeError('degenerate edge')
   x=(c-a).dot(e)/length;y=(c-a).cross(e).length/length
   coords=[(0.,0.),(length*DENSITY,0.),(x*DENSITY,y*DENSITY)]
   lo=min(v[0] for v in coords);coords=[(v[0]-lo,v[1]) for v in coords]
   w=max(v[0] for v in coords);h=max(v[1] for v in coords)
   slot=me.materials[p.material_index].name.split('.')[0]
   regions[surface(slot)].append((p,coords,w,h))
  measurements=[];occupied=[]
  for region,items in regions.items():
   x=y=4.;rowh=0.;rects=[]
   for p,coords,w,h in sorted(items,key=lambda t:-t[3]):
    if x+w+PAD*2>HALF-4:x=4.;y+=rowh;rowh=0.
    assert y+h+PAD*2<HALF-4,(name,scale,region,y+h)
    rect=(x,y,x+w+PAD*2,y+h+PAD*2)
    assert all(rect[2]<=r[0]+1e-5 or r[2]<=rect[0]+1e-5 or rect[3]<=r[1]+1e-5 or r[3]<=rect[1]+1e-5 for r in rects)
    rects.append(rect)
    ox=HALF if region in [1,3] else 0;oy=HALF if region in [0,1] else 0
    for li,co in zip(p.loop_indices,coords):uv.data[li].uv=((ox+x+PAD+co[0])/SIZE,(oy+y+PAD+co[1])/SIZE)
    area=p.area;uva=abs((coords[1][0]-coords[0][0])*(coords[2][1]-coords[0][1])-(coords[2][0]-coords[0][0])*(coords[1][1]-coords[0][1]))/2/SIZE**2
    if area>1e-10:measurements.append((area,uva,math.sqrt(uva*SIZE**2/area)))
    x+=w+PAD*2;rowh=max(rowh,h+PAD*2)
   occupied.append({'region':region,'islands':len(items),'used_height_pixels':y+rowh,'conservative_rectangle_overlap_pairs':0})
  variant=name+'_S'+str(round(scale*100));o.name=variant
  bpy.ops.export_scene.fbx(filepath=OUT+'/'+variant+'.fbx',use_selection=True,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_anim=False)
  report['meshes'].append({'name':variant,'source':name,'baked_world_scale':scale,'actor_scale':1,'world_surface_area_m2':sum(v[0] for v in measurements),'uv_area':sum(v[1] for v in measurements),'measured_density_min':min(v[2] for v in measurements),'measured_density_max':max(v[2] for v in measurements),'islands':len(measurements),'regions':occupied})
json.dump(report,open(ROOT+'/TexturePass/uv_validation.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/uv_last_variant.blend')
