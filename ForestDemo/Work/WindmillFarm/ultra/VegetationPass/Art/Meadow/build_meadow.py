"""Original rounded meadow clumps; meters, ground origin, solid opaque geometry.
No external assets. Deterministic source, export, and FBX readback QA.
"""
import bpy, math, random, json, hashlib, time
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
START=datetime.now(timezone.utc)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1.0
MATERIALS={}
for name,col in {'MeadowLeaf':(.29,.39,.18,1),'MeadowStem':(.37,.40,.21,1),'MeadowSeed':(.65,.58,.36,1)}.items():
    mat=bpy.data.materials.new(name);mat.diffuse_color=col
    mat.use_nodes=True
    mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=col
    mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.83
    MATERIALS[name]=mat

class Builder:
    def __init__(self,name):
        self.name=name;self.verts=[];self.faces=[];self.mats=[];self.responses=[]
    def add(self,verts,faces,mat,response):
        offset=len(self.verts);self.verts.extend([tuple(v) for v in verts])
        self.responses.extend([response]*len(verts))
        for f in faces:
            # Triangulation now ensures the UV charts survive export identically.
            for j in range(1,len(f)-1):
                self.faces.append((offset+f[0],offset+f[j],offset+f[j+1]));self.mats.append(mat)
    def tube(self,a,b,r0,r1,mat='MeadowStem',sides=5,response=.0):
        a,b=Vector(a),Vector(b);direction=(b-a).normalized()
        side=direction.cross(Vector((0,1,0))).normalized();up=direction.cross(side).normalized()
        v=[]
        for c,r in ((a,r0),(b,r1)):
            for k in range(sides):
                angle=k*math.tau/sides;v.append(c+side*(math.cos(angle)*r)+up*(math.sin(angle)*r))
        f=[]
        for k in range(sides):f.append((k,(k+1)%sides,(k+1)%sides+sides,k+sides))
        f.extend([tuple(reversed(range(sides))),tuple(range(sides,sides*2))])
        self.add(v,f,mat,response)
    def blade(self,base,azimuth,height,reach,width,twist=0,segments=5):
        base=Vector(base);direction=Vector((math.cos(azimuth),math.sin(azimuth),0))
        side=Vector((-direction.y,direction.x,0));v=[]
        for i in range(segments):
            t=i/(segments-.15)
            center=base+direction*(reach*t*t)+Vector((0,0,height*(1.12*t-.12*t*t)))
            sw=width*(.30+.70*math.sin(math.pi*(.12+.83*t)))*((1-t)**.32)
            side_t=side*math.cos(twist*t)+Vector((0,0,math.sin(twist*t)))
            # Diamond cross section catches soft light; entirely solid, no cards.
            v.extend([center-side_t*sw,center+Vector((0,0,.008)),center+side_t*sw,center-Vector((0,0,.004))])
        tip=base+direction*reach+Vector((0,0,height));v.append(tip)
        f=[(3,2,1,0)]
        for i in range(segments-1):
            for k in range(4):f.append((i*4+k,i*4+(k+1)%4,(i+1)*4+(k+1)%4,(i+1)*4+k))
        for k in range(4):f.append(((segments-1)*4+k,(segments-1)*4+(k+1)%4,len(v)-1))
        self.add(v,f,'MeadowLeaf',.6)
    def seed(self,center,radius,length,tilt,kind):
        # Round-ended low-poly seed/feather silhouette, not billboard alpha.
        center=Vector(center);axis=Vector(tilt).normalized();side=axis.cross(Vector((0,1,0))).normalized();other=axis.cross(side).normalized()
        profile=[(-.5,0),(-.35,.70),(-.10,1),(.16,.86),(.36,.55),(.5,0)]
        if kind=='reed':profile=[(-.5,0),(-.3,.75),(-.03,1),(.2,.74),(.4,.32),(.5,0)]
        v=[center+axis*(profile[0][0]*length)]
        sides=6
        for z,r in profile[1:-1]:
            for k in range(sides):
                angle=k*math.tau/sides;v.append(center+axis*(z*length)+side*(math.cos(angle)*r*radius)+other*(math.sin(angle)*r*radius))
        v.append(center+axis*(profile[-1][0]*length));f=[]
        for k in range(sides):f.append((0,1+(k+1)%sides,1+k))
        for j in range(len(profile)-3):
            for k in range(sides):f.append((1+j*sides+k,1+j*sides+(k+1)%sides,1+(j+1)*sides+(k+1)%sides,1+(j+1)*sides+k))
        last=1+(len(profile)-3)*sides
        for k in range(sides):f.append((last+k,last+(k+1)%sides,len(v)-1))
        self.add(v,f,'MeadowSeed',1.)
    def finish(self):
        me=bpy.data.meshes.new(self.name);me.from_pydata(self.verts,[],self.faces);me.update()
        ob=bpy.data.objects.new(self.name,me);bpy.context.collection.objects.link(ob)
        for m in MATERIALS.values():me.materials.append(m)
        names=list(MATERIALS)
        for p,m in zip(me.polygons,self.mats):p.material_index=names.index(m);p.use_smooth=True
        uv0=me.uv_layers.new(name='UV0_Unique');uv1=me.uv_layers.new(name='UV1_Density128')
        dim=math.ceil(math.sqrt(len(me.polygons)));cell=1/dim;pad=.10*cell
        for p in me.polygons:
            a,b,c=[me.vertices[i].co for i in p.vertices]
            edge=b-a;e=edge.normalized();n=edge.cross(c-a).normalized();q=n.cross(e)
            coords=[Vector((0,0)),Vector((edge.length,0)),Vector(((c-a).dot(e),(c-a).dot(q)))]
            lo=Vector((min(v.x for v in coords),min(v.y for v in coords)))
            span=max(max(v.x for v in coords)-lo.x,max(v.y for v in coords)-lo.y)
            assert span>1e-8 and abs((coords[1]-coords[0]).cross(coords[2]-coords[0]))>1e-10
            origin=Vector(((p.index%dim)*cell+pad,(p.index//dim)*cell+pad))
            for li,co in zip(p.loop_indices,coords):
                uv0.data[li].uv=origin+(co-lo)*((cell-2*pad)/span)
                uv1.data[li].uv=co*.125
        colors=me.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='POINT')
        maxz=max(v.co.z for v in me.vertices)
        for v,response in zip(me.vertices,self.responses):colors.data[v.index].color=(max(0,min(1,v.co.z/maxz)),response,0,1)
        me.uv_layers.active_index=0;me.color_attributes.active_color=colors
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
        bpy.ops.export_scene.fbx(filepath=str(ROOT/(self.name+'.fbx')),use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_space_transform=False,add_leaf_bones=False,use_mesh_modifiers=True,colors_type='LINEAR')
        return ob,{'uv0_chart_method':'one shape-preserving triangle per non-overlapping square cell','uv0_chart_count':len(me.polygons),'uv0_grid':dim,'uv0_cell_padding_uv':pad,'uv0_cell_padding_px_at1024':pad*1024,'uv1_method':'each triangle projected isometrically at 0.125UV/metre; intentional tiled chart overlap','vertex_color':'Col linear FLOAT_COLOR; R=height/globalmaxheight; G=.6 leaf,1 seed,0 stem; B0 A1'}

records=[];objects=[]
for index,(name,kind) in enumerate([('SM_MeadowTall','tall'),('SM_MeadowPlume','plume'),('SM_MeadowReed','reed')]):
    rng=random.Random(20261022+index*31);b=Builder(name)
    if kind=='tall':blades,stalks=22,7;leafheight=(.65,1.04);stemheight=(.98,1.20);radius=.34
    elif kind=='plume':blades,stalks=20,8;leafheight=(.39,.67);stemheight=(.60,.77);radius=.31
    else:blades,stalks=17,9;leafheight=(.58,1.04);stemheight=(1.25,1.55);radius=.34
    for k in range(blades):
        angle=rng.random()*math.tau;r=math.sqrt(rng.random())*radius
        base=(math.cos(angle)*r,math.sin(angle)*r,0)
        b.blade(base,angle+rng.uniform(-.9,.9),rng.uniform(*leafheight),rng.uniform(.25,.48),rng.uniform(.022,.037),rng.uniform(-.4,.4))
    for k in range(stalks):
        angle=k*2.399963+rng.uniform(-.25,.25);r=math.sqrt(rng.random())*radius*.84
        base=Vector((math.cos(angle)*r,math.sin(angle)*r,0));h=rng.uniform(*stemheight)
        drift=Vector((rng.uniform(-.10,.10),rng.uniform(-.10,.10),0));end=base+drift+Vector((0,0,h))
        bend=base+drift*.30+Vector((0,0,h*.55))
        b.tube(base,bend,.008,.006);b.tube(bend,end,.006,.004)
        if kind=='plume':seedlen=.18;seedrad=.043
        elif kind=='reed':seedlen=.24;seedrad=.051
        else:seedlen=.17;seedrad=.028
        b.seed(end+Vector((0,0,seedlen*.25)),seedrad,seedlen,(drift.x*.8,drift.y*.8,1),kind)
        if kind=='reed':
            # Six restrained side awns create a feathered reed silhouette.
            for j in range(6):
                theta=angle+j*2.399963
                s=end+Vector((0,0,.006+(j%3)*.037))
                e=s+Vector((math.cos(theta)*.072,math.sin(theta)*.072,.048))
                b.tube(s,e,.013,.0015,mat='MeadowSeed',sides=4,response=1.)
            # Elevated lance leaves make the sparse stalks read as reed.
            b.blade(base+Vector((0,0,h*.40))+drift*.22,angle+.8,.35,.30,.029,.2,segments=4)
    ob,info=b.finish();objects.append(ob);records.append({'name':name,'kind':kind,'blade_count':blades+(stalks if kind=='reed' else 0),'stalk_count':stalks,**info})

# Preserve the clean authored scene before readback.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source.blend'))

for rec in records:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    path=ROOT/(rec['name']+'.fbx');bpy.ops.import_scene.fbx(filepath=str(path),use_custom_normals=True,colors_type='LINEAR')
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(obs)==1
    ob=obs[0];me=ob.data;me.calc_loop_triangles()
    minmax=[[min((ob.matrix_world@v.co)[i] for v in me.vertices),max((ob.matrix_world@v.co)[i] for v in me.vertices)] for i in range(3)]
    densities=[];uv0deg=0;uv1deg=0;area=0;uarea=0;uv0cells=set();uv0_cell_duplicates=0;uv0_cell_violations=0
    for t in me.loop_triangles:
        pts=[ob.matrix_world@me.vertices[i].co for i in t.vertices];wa=(pts[1]-pts[0]).cross(pts[2]-pts[0]).length*.5
        assert wa>1e-10
        for channel in range(2):
            ua,ub,uc=[me.uv_layers[channel].data[i].uv for i in t.loops];ar=abs((ub-ua).cross(uc-ua))*.5
            if channel==0:
                uv0deg+=ar<1e-12
                center=(ua+ub+uc)/3;dim=rec['uv0_grid'];cellkey=(int(center.x*dim),int(center.y*dim))
                uv0_cell_duplicates+=cellkey in uv0cells;uv0cells.add(cellkey)
                for co in (ua,ub,uc):
                    uv0_cell_violations+=not(cellkey[0]+.09999 <= co.x*dim <= cellkey[0]+.90001 and cellkey[1]+.09999 <= co.y*dim <= cellkey[1]+.90001)
            else:
                uv1deg+=ar<1e-12;densities.append(1024*math.sqrt(ar/wa));area+=wa;uarea+=ar
    col=me.color_attributes.get('Col');assert col is not None
    zmax=minmax[2][1];errors=[];anchors=[];responses=[]
    for i,c in enumerate(col.data):
        vi=i if col.domain=='POINT' else me.loops[i].vertex_index
        z=(ob.matrix_world@me.vertices[vi].co).z
        errors.append(abs(c.color[0]-max(0,min(1,z/zmax))));anchors.append(c.color[0]);responses.append(c.color[1])
    outside=sum(not(-1e-6<=d.uv.x<=1.000001 and -1e-6<=d.uv.y<=1.000001) for d in me.uv_layers[0].data)
    rec.update({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'fbx_readback':{'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'bounds_m':minmax,'materials':[m.name for m in me.materials],'uv_layers':[l.name for l in me.uv_layers],'uv0_outside01_loops':outside,'uv0_collapsed_triangles':uv0deg,'uv0_cell_duplicates':uv0_cell_duplicates,'uv0_padding_cell_violations':uv0_cell_violations,'uv1_collapsed_triangles':uv1deg,'uv1_density_area_weighted_px_m':1024*math.sqrt(uarea/area),'uv1_density_min_max_px_m':[min(densities),max(densities)],'color_name':col.name,'color_domain':col.domain,'color_anchor_max_error':max(errors),'color_R_range':[min(anchors),max(anchors)],'color_G_values':sorted(set(round(v,4) for v in responses)),'unscaled_transform':list(ob.scale),'origin_m':list(ob.location)},'surface_area_m2':area})
    assert len(me.loop_triangles)<2500
    assert outside==0 and uv0deg==0 and uv1deg==0 and uv0_cell_duplicates==0 and uv0_cell_violations==0
    assert max(errors)<.002
    assert abs(1024*math.sqrt(uarea/area)-128)<.01
    assert sorted(m.name for m in me.materials)==sorted(MATERIALS)
    print('MEADOW_QA_PASS',rec['name'],len(me.loop_triangles),minmax,flush=True)

manifest={'started_at_utc':START.isoformat(),'finished_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':(datetime.now(timezone.utc)-START).total_seconds(),'units':'meters','fbx_axes':{'forward':'-Y','up':'Z'},'original_authoring':True,'external_references':[],'image_generation_used':False,'all_readback_checks_passed':True,'wind_integration':'Material vertex animation; world-height Col.R squared for rooted bend, Col.G for fine leaf/seed modulation. Bound by max localheight; base z0 black R exactly. No wind is baked into mesh.','root_placement_note':'Origin z0 at ground. Leaf diamond cross sections extend4mm belowground deliberately to hide root gaps; all z<=0 vertices have Col.R=0.','uv0_overlap_check':'Constructive guarantee: every triangle confined to separate grid cell with 10 percent cell padding, shape preserving; no charts share a cell. FBX readback checks UV range and nonzero triangles.','uv_density_note':'UV1 density exact128px/m for unscaled instance; instance scaling changes density inversely. UV1 intentionally overlaps for repeatable non-directional texture; UV0 unique.','assets':records}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('MEADOW_COMPLETE',flush=True)
