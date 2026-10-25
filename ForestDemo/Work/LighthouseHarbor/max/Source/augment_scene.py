import bpy, bmesh, math, json
from pathlib import Path
ROOT=Path('D:/github/AstraEffort/ForestDemo/Work/LighthouseHarbor/max')
ART=ROOT/'SourceArt'
bpy.ops.wm.open_mainfile(filepath=str(ART/'harbor.blend'))
def export(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.export_scene.fbx(filepath=str(ART/'FBX'/(o.name+'.fbx')),use_selection=True,apply_unit_scale=True,global_scale=1,
      axis_forward='-Y',axis_up='Z',mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,object_types={'MESH'},path_mode='STRIP')
v=[];f=[];N=32
for x,r in [(.65,.35),(24,2.0)]:
    for i in range(N):
        a=i*2*math.pi/N;v.append((-22+x,19+r*math.cos(a),45.5+r*math.sin(a)))
for i in range(N):f.append((i,(i+1)%N,(i+1)%N+N,i+N))
me=bpy.data.meshes.new('Beacon_Beam');me.from_pydata(v,[],f);me.update()
o=bpy.data.objects.new('Beacon_Beam',me);bpy.context.collection.objects.link(o)
ma=bpy.data.materials.new('Beacon');ma.diffuse_color=(1,.8,.4,.15);me.materials.append(ma)
uv=me.uv_layers.new(name='Beam_falloff')
for p in me.polygons:
    for li in p.loop_indices:
        vi=me.loops[li].vertex_index;uv.data[li].uv=(0 if vi<N else 1,(vi%N)/N)
export(o)
# Original raised lettering; geometry is delivered, no font dependency in the UE scene.
texts=[]
for body,loc,size,name in [('TIDE & TWINE',(21,-10.65,6.42),.33,'Workshop_Lettering'),('07',(-22,15.55,29.0),.46,'Lighthouse_Plaque')]:
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.align_x='CENTER';cu.extrude=.008;cu.bevel_depth=.004;cu.bevel_resolution=1
    tx=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(tx);tx.location=loc;tx.rotation_euler=(math.pi/2,0,0)
    bpy.ops.object.select_all(action='DESELECT');tx.select_set(True);bpy.context.view_layer.objects.active=tx;bpy.ops.object.convert(target='MESH')
    tx.data.materials.append(bpy.data.materials['Copper']);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    layer=tx.data.uv_layers.new(name='Surface_metres')
    for poly in tx.data.polygons:
        for li in poly.loop_indices:
            co=tx.data.vertices[tx.data.loops[li].vertex_index].co;layer.data[li].uv=(co.x/3,co.z/3)
    texts.append(tx);export(tx)
manifest=json.loads((ART/'mesh_manifest.json').read_text(encoding='utf-8'))
for ob in [o]+texts:
    pts=[p.co for p in ob.data.vertices]
    manifest['meshes'].append({'name':ob.name,'bounds_m':[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],
      'vertices':len(ob.data.vertices),'polygons':len(ob.data.polygons),'materials':[m.name for m in ob.data.materials],
      'uv_density_px_per_m_min':0 if ob==o else 170.6,'uv_density_px_per_m_max':0 if ob==o else 170.6})
(ART/'mesh_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'harbor.blend'))
print('AUGMENT_COMPLETE')
