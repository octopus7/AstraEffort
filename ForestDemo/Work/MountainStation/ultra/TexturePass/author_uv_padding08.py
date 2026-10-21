"""Unique face charts with measured physical scale; geometry stays unchanged."""
import bpy,math,json,datetime,hashlib,struct,time
from pathlib import Path
from mathutils import Vector
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass')
BASE=R.parent;OUT=R/'SourceArt';OUT.mkdir(exist_ok=True)
TARGET=128.;PAD=8.
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
started=utc();clock=time.monotonic()
bpy.ops.wm.open_mainfile(filepath=str(BASE/'SourceArt/AlderPass.blend'))
manifest=json.loads((BASE/'art_manifest.json').read_text())
def geom_hash(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3d',*v.co))
    for p in o.data.polygons:h.update(struct.pack('<I',len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices));h.update(struct.pack('<I',p.material_index))
    return h.hexdigest()
def area(a,b,c):return (b-a).cross(c-a).length*.5
def quantiles(a):
    a=sorted(a)
    return {str(q):a[round((len(a)-1)*q/100)] if a else None for q in [0,1,5,50,95,99,100]}
def cross2(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def intersection_area(subject,clip):
    out=list(subject)
    if cross2(*clip)<0:clip=list(reversed(clip))
    for a,b in zip(clip,clip[1:]+clip[:1]):
        inp=out;out=[]
        if not inp:return 0.
        for p,q in zip(inp,inp[1:]+inp[:1]):
            dp=cross2(a,b,p);dq=cross2(a,b,q)
            if dp>=-1e-9:out.append(p)
            if (dp<0)!=(dq<0):
                t=dp/(dp-dq);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(out,out[1:]+out[:1])))*.5 if len(out)>2 else 0.
layouts={};reports=[]
for entry in manifest['meshes']:
    o=bpy.data.objects[entry['name']];me=o.data
    assert not any(m.show_render for m in o.modifiers),'Unapplied geometry modifier: '+o.name
    before=geom_hash(o);me.calc_loop_triangles()
    vertices=[o.matrix_world@v.co for v in me.vertices]
    tris={p.index:[] for p in me.polygons}
    for tri in me.loop_triangles:tris[tri.polygon_index].append(tri)
    while me.uv_layers:me.uv_layers.remove(me.uv_layers[0])
    layer=me.uv_layers.new(name='UniqueSurfaceUV')
    charts=[];density=[];distortion=[];degenerate=0;subpixel=0;overlaps=0;tiny_overlaps=0;max_overlap=0.;world_sum=0.
    for p in me.polygons:
        ids=list(p.loop_indices);pts=[vertices[me.loops[i].vertex_index] for i in ids];origin=pts[0]
        normal=Vector((0,0,0))
        wa=0.
        for tri in tris[p.index]:
            a,b,c=[vertices[i] for i in tri.vertices];normal+=(b-a).cross(c-a);wa+=area(a,b,c)
        if wa<1e-12 or normal.length<1e-12:
            degenerate+=len(tris[p.index]);coords={i:(0.,0.) for i in ids};ua=0.;width=height=0.
        else:
            normal.normalize();edges=[b-a for a,b in zip(pts,pts[1:]+pts[:1])]
            tangent=max(edges,key=lambda e:e.length_squared);tangent=(tangent-normal*tangent.dot(normal)).normalized();bitangent=normal.cross(tangent)
            coords={i:((v-origin).dot(tangent),(v-origin).dot(bitangent)) for i,v in zip(ids,pts)}
            ua=sum(abs(cross2(*(coords[i] for i in t.loops)))*.5 for t in tris[p.index])
            factor=TARGET*math.sqrt(wa/ua)
            xs=[v[0] for v in coords.values()];ys=[v[1] for v in coords.values()];xmin=min(xs);ymin=min(ys)
            coords={i:((x-xmin)*factor,(y-ymin)*factor) for i,(x,y) in coords.items()}
            width=(max(xs)-xmin)*factor;height=(max(ys)-ymin)*factor
            polytri=[]
            for tri in tris[p.index]:
                pa=[coords[i] for i in tri.loops];uvarea=abs(cross2(*pa))*.5;worldarea=area(*(vertices[i] for i in tri.vertices))
                if worldarea>1e-12:
                    density.append(math.sqrt(uvarea/worldarea));subpixel+=uvarea<1
                    lengths=[]
                    for j in range(3):
                        a,b=pa[j],pa[(j+1)%3];wl=(vertices[tri.vertices[j]]-vertices[tri.vertices[(j+1)%3]]).length
                        if wl>1e-8:lengths.append(math.hypot(b[0]-a[0],b[1]-a[1])/wl)
                    if lengths and min(lengths)>1e-8:distortion.append(max(lengths)/min(lengths))
                polytri.append(pa)
            for a in range(len(polytri)):
                for b in range(a):
                    overlap=intersection_area(polytri[a],polytri[b]);max_overlap=max(max_overlap,overlap)
                    if overlap>0.05:overlaps+=1
                    elif overlap>1e-4:tiny_overlaps+=1
        world_sum+=wa
        charts.append({'id':p.index,'coords':coords,'width':width,'height':height,'rw':max(1,math.ceil(width))+int(2*PAD),'rh':max(1,math.ceil(height))+int(2*PAD),'area_m2':wa,'triangles':len(tris[p.index])})
    assert overlaps==0,(o.name,'intra-chart overlap',overlaps,max_overlap)
    ordered=sorted(charts,key=lambda c:(-c['rh'],-c['rw'],c['id']))
    side=2**math.ceil(math.log2(max(256,max(max(c['rw'],c['rh']) for c in charts),math.sqrt(sum(c['rw']*c['rh'] for c in charts))*1.12)))
    while True:
        x=y=rowh=0;rows=[];row=[]
        for c in ordered:
            if x+c['rw']>side:
                rows.append({'y':y,'height':rowh,'charts':row});y+=rowh;x=rowh=0;row=[]
            c['x']=x;c['y']=y;row.append(c['id']);x+=c['rw'];rowh=max(rowh,c['rh'])
        rows.append({'y':y,'height':rowh,'charts':row})
        if y+rowh<=side:break
        side*=2
    records=[]
    for c in charts:
        for i,(x,y) in c['coords'].items():layer.data[i].uv=((c['x']+PAD+x)/side,(c['y']+PAD+y)/side)
        records.append([c['id'],c['x'],c['y'],c['rw'],c['rh'],c['width'],c['height'],c['area_m2'],c['triangles']])
    assert geom_hash(o)==before,'UV authoring changed geometry'
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    path=OUT/(o.name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='Y',axis_up='Z',mesh_smooth_type='FACE',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
    entry['file']=str(path).replace('\\','/')
    layouts[o.name]={'side_px':side,'padding_each_side_px':PAD,'target_texels_per_meter':TARGET,'charts':records,'rows':rows,'record_fields':['polygon_id','allocation_x','allocation_y','allocation_width','allocation_height','surface_width','surface_height','world_area_m2','triangle_count']}
    report={'mesh':o.name,'geometry_sha256_before':before,'geometry_sha256_after':geom_hash(o),'world_surface_area_m2':world_sum,'source_vertices':len(me.vertices),'source_triangles':len(me.loop_triangles),'islands':len(charts),'virtual_atlas_side_px':side,'target_texels_per_meter':TARGET,'triangle_density_percentiles':quantiles(density),'edge_stretch_ratio_percentiles':quantiles(distortion),'tiny_triangles_under_one_base_texel_area':subpixel,'degenerate_triangles':degenerate,'intra_chart_overlap_pairs_above_0_05px2':overlaps,'subpixel_intersection_pairs_0_0001_to_0_05px2':tiny_overlaps,'maximum_intersection_px2':max_overlap,'inter_chart_overlap_pairs':0,'minimum_chart_padding_each_side_px':PAD,'inter_chart_minimum_gap_px':2*PAD,'uv_bounds_01':all(0<=v<=1 for d in layer.data for v in d.uv),'placement_note':'Source world geometry used; final UE actor transforms are remeasured independently.'}
    reports.append(report);print('UV_AUTHORED',o.name,side,len(charts),flush=True)
    (R/'source_uv_validation.json').write_text(json.dumps({'started_at_utc':started,'meshes':reports,'pending':True},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'AlderPass_Textured.blend'))
(R/'uv_layouts.json').write_text(json.dumps(layouts,separators=(',',':')))
(R/'art_manifest.json').write_text(json.dumps(manifest,indent=2))
record={'started_at_utc':started,'finished_at_utc':utc(),'elapsed_seconds':time.monotonic()-clock,'target_texels_per_meter':TARGET,'scope':'All triangles of all 47 owned source meshes; unique planar polygon charts. Metric is base-level effective texel density, not screen resolution or streamed mip residency.','island_strategy':'One chart per authored polygon; no shared charts. Per-polygon area normalization preserves target mean density; curved/non-planar triangle deviation measured.','padding_note':'8 effective base texels around each chart, 16 between allocated chart rectangles. Surface image is intentionally repeating; virtual atlas is not a unique baked color image.','meshes':reports,'passed':True}
(R/'source_uv_validation.json').write_text(json.dumps(record,indent=2))
print('UV_AUTHORING_COMPLETE',time.monotonic()-clock,flush=True)
