"""Finite polish based on the first actual UE render; preserves original ownership."""
import bpy,bmesh,ast,math,random,json
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/LighthouseHarbor/max');ART=ROOT/'SourceArt'
bpy.ops.wm.open_mainfile(filepath=str(ART/'harbor.blend'))
MAT={m.name:m for m in bpy.data.materials};GROUPS={};R=random.Random(981)
tree=ast.parse((ROOT/'Source/author_scene.py').read_text())
names={'collect','bevel','cube','cyl','sphere','mesh','line','rod','ring','stairs'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'<own_geometry_helpers>','exec'))
changed=[]
for o in list(bpy.data.objects):
    if o.name in ['Stairs','Stair_Rails']:
        bpy.data.objects.remove(o,do_unlink=True)
    elif o.name.endswith('_Grass'):
        for p in o.data.polygons:p.material_index=0
        changed.append(o)
# External switchbacks remain fully visible instead of passing through cliff solids.
flights=[((8,-10,3.2),(-3,-10,3.2)),((-3,-10,3.2),(-16,-10,8.2)),((-16,-10,8.2),(-26,-2,13)),
         ((-26,-2,13),(-36,8,19)),((-36,8,19),(-32,13,25)),((-32,13,25),(-25,16,25))]
for a,b in flights:stairs(a,b)
for a,b in flights[1:5]:
    av,bv=Vector(a),Vector(b);d=bv-av;theta=math.atan2(d.y,d.x);base=3.2 if a[2]<13 else 13
    for t in np.linspace(.12,.91,6):
        p=av+d*t;h=max(.35,p.z-base)
        cube('Stair_Footings',(p.x,p.y,base+h/2-.13),(1.4,2.15,h),'WarmStone',.09,theta)
def path(points,z):
    for a,b in zip(points,points[1:]):
        d=Vector((b[0]-a[0],b[1]-a[1],0));count=max(1,math.ceil(d.length/.7));theta=math.atan2(d.y,d.x)
        for i in range(count):
            t=(i+.5)/count;x=a[0]+d.x*t;y=a[1]+d.y*t
            cube('Coastal_Paths',(x,y,z+.04),(.62,1.35+R.uniform(-.1,.1),.12),'Path',.07,theta+R.uniform(-.025,.025))
path([(20,-11.3),(14,-12),(8,-10)],3.2)
path([(-3,-10),(-9,-16),(-20,-15),(-27,-9),(-29,-4)],3.2)
path([(-26,-2),(-20,-1),(-16,.1),(-12,1.5)],13)
path([(-8,3),(-3,5),(.5,9),(-.8,11.6)],13)
path([(-32,13),(-29,15),(-25,15),(-22,15)],25)
def shrubs(x,y,z,scale=1):
    for i in range(3):
        sphere('Terrace_Gardens',(x+R.uniform(-.5,.5)*scale,y+R.uniform(-.45,.45)*scale,z+.45*scale),
               (R.uniform(.45,.8)*scale,R.uniform(.4,.7)*scale,R.uniform(.4,.7)*scale),'GrassLight' if i==0 else 'Grass')
    if R.random()<.65:
        for i in range(4):sphere('Terrace_Gardens',(x+R.uniform(-.4,.4)*scale,y+R.uniform(-.4,.4)*scale,z+.90*scale),(.10,.10,.10),'Flower')
for x,y,z,s in [(-31,20,25,.8),(-29,28,25,.8),(-17,26,25,.8),(-13,19,25,.85),(-19,11,25,.7),
  (-21,-.2,13,.8),(-16,1,13,.65),(-8,0,13,.8),(-5,5,13,.8),(4,13,13,1),(4,18,13,.8),(-2,22,13,.8),
  (5,-13,3.2,.75),(-5,-14,3.2,.8),(-11,-18,3.2,1),(-20,-18,3.2,.9),(-25,-11,3.2,.8),(-31,-4,3.2,1),
  (23,4,3.2,1),(21,8,3.2,1.1),(19,14,3.2,1),(13,-2,3.2,1),(7,-9,3.2,.8)]:shrubs(x,y,z,s)
# Benches and small lookout terraces create deliberate destinations on the tiers.
for x,y,z,angle in [(-17,23,25,-.3),(4,17,13,.5),(-23,-14,3.2,-.7)]:
    cube('Lookout_Furniture',(x,y,z+.03),(3.0,2.3,.15),'Path',.2,angle)
    for yy in [-.22,.05,.32]:cube('Lookout_Furniture',(x,y+yy,z+.65),(2.1,.22,.13),'TimberLight',.06,angle)
    for xx in [-.8,.8]:
        rod('Lookout_Furniture',(x+xx,y-.25,z),(x+xx,y-.25,z+.65),.06,'Iron')
        rod('Lookout_Furniture',(x+xx,y+.3,z),(x+xx,y+.3,z+1.28),.06,'Iron')
    for zz in [.95,1.2]:cube('Lookout_Furniture',(x,y+.33,z+zz),(2.1,.12,.18),'TimberLight',.06,angle)
for i,a in enumerate(np.linspace(-1.2,1.4,24)):
    x,y=-23+14.4*math.cos(a),21+11.5*math.sin(a)
    if x>-10:continue
    cube('Upper_Lookout_Wall',(x,y,25.3),(.9,.5,.65),'Chalk',.13,a+math.pi/2)
# Herb troughs by the keeper homes, with cedar boards and repeated foliage.
for x,y in [(-16,8.8),(-9,8.8),(1.7,18.3)]:
    cube('Terrace_Gardens',(x,y,13.33),(2.0,.85,.65),'Timber',.10)
    for dx in [-.65,0,.65]:shrubs(x+dx,y,13.6,.5)

palette=json.loads((ART/'palette.json').read_text())
for g,objs in GROUPS.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name=g
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    uv=o.data.uv_layers.new(name='Surface_metres')
    for p in o.data.polygons:
        tile=palette[o.data.materials[p.material_index].name]['tile_metres'];axis=max(range(3),key=lambda i:abs(p.normal[i]));ax=[i for i in range(3) if i!=axis]
        for li in p.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co[ax[0]]/tile,co[ax[1]]/tile)
    changed.append(o)
for o in changed:
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.export_scene.fbx(filepath=str(ART/'FBX'/(o.name+'.fbx')),use_selection=True,apply_unit_scale=True,global_scale=1,
      axis_forward='-Y',axis_up='Z',mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,object_types={'MESH'},path_mode='STRIP')
manifest=json.loads((ART/'mesh_manifest.json').read_text());old={m['name']:m for m in manifest['meshes']}
for ob in changed:
    pts=[v.co for v in ob.data.vertices];lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
    old[ob.name]={'name':ob.name,'bounds_m':[lo,hi],'vertices':len(ob.data.vertices),'polygons':len(ob.data.polygons),'materials':[m.name for m in ob.data.materials]}
manifest['meshes']=list(old.values());manifest['polish_changes']=[o.name for o in changed]
(ART/'mesh_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(ROOT/'Validation/polish_source.json').write_text(json.dumps({'changed_meshes':[o.name for o in changed],
  'reason':'Actual UE render showed radial grass color sectors and terrain intersection hiding lower stairs; flattened grass palette and routed supported stairs outside cliff, added paths/garden destinations.'},indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'harbor.blend'))
print('POLISH_SOURCE_COMPLETE',len(changed))
