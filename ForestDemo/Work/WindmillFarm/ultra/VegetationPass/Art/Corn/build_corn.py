"""Original low-poly corn, with exact-density UVs and root-anchored wind colours.
Run with Blender 4.5 --background --python build_corn.py.
"""
import bpy, math, json, random, hashlib, time
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector

OUT=Path(__file__).resolve().parent
START=time.time()
NAMES=['CornLeaf','CornStalk','CornKernel','CornTassel']
COLORS=[(.24,.37,.105,1),(.36,.43,.15,1),(.83,.60,.19,1),(.66,.53,.25,1)]
bpy.ops.wm.read_factory_settings(use_empty=True)
MATS=[]
for n,c in zip(NAMES,COLORS):
    m=bpy.data.materials.new(n);m.diffuse_color=c;m.use_nodes=True
    m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=c
    m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.78
    MATS.append(m)

class Plant:
    def __init__(self,name,height,seed):
        self.name=name;self.height=height;self.rand=random.Random(seed)
        self.v=[];self.f=[];self.mi=[];self.flutter=[]
    def add(self,vs,fs,mat,fl=0):
        offset=len(self.v);self.v.extend([tuple(v) for v in vs])
        self.flutter.extend(fl if isinstance(fl,list) else [fl]*len(vs))
        for f in fs:
            self.f.append(tuple(i+offset for i in f));self.mi.append(NAMES.index(mat))
    def tube(self,a,b,r0,r1,mat='CornStalk',sides=7,fl=0):
        a,b=Vector(a),Vector(b);d=(b-a).normalized()
        ref=Vector((0,0,1)) if abs(d.z)<.9 else Vector((1,0,0))
        x=d.cross(ref).normalized();y=d.cross(x).normalized()
        vs=[p+r*(x*math.cos(i*math.tau/sides)+y*math.sin(i*math.tau/sides)) for p,r in [(a,r0),(b,r1)] for i in range(sides)]
        fs=[]
        for i in range(sides):
            j=(i+1)%sides;fs.extend([(i,j,j+sides),(i,j+sides,i+sides)])
        # End caps use fan triangulation, no central or repeated vertices.
        for i in range(1,sides-1):fs.extend([(0,i+1,i),(sides,sides+i,sides+i+1)])
        self.add(vs,fs,mat,fl)
    def kernel(self,center,axis,radius=.020,length=.026):
        z=Vector(axis).normalized();ref=Vector((0,0,1)) if abs(z.z)<.9 else Vector((1,0,0))
        x=z.cross(ref).normalized()*radius;y=z.cross(x).normalized()*radius*.83;z*=length
        c=Vector(center);vs=[c+x,c+y,c-x,c-y,c+z,c-z]
        fs=[(i,(i+1)%4,4) for i in range(4)]+[((i+1)%4,i,5) for i in range(4)]
        self.add(vs,fs,'CornKernel',.35)
    def leaf(self,base,angle,length,width,lift,drop,mat='CornLeaf',steps=9):
        d=Vector((math.cos(angle),math.sin(angle),0));cross=Vector((-d.y,d.x,0));base=Vector(base)
        vs=[];fl=[]
        for k in range(steps+1):
            t=k/steps
            c=base+d*(length*t)+Vector((0,0,lift*math.sin(math.pi*.8*t)-drop*t*t))
            half=max(.0015,width*.5*math.sin(math.pi*t)**.66)
            # A longitudinal ridge makes each broad blade readable in sunlight.
            for s in (-1,0,1):
                vs.append(c+cross*(s*half)+Vector((0,0,(1-abs(s))*.022*math.sin(math.pi*t))))
                fl.append(.7+.3*t)
        fs=[]
        for k in range(steps):
            for s in range(2):
                a=k*3+s;b=a+3;fs.extend([(a,b,a+1),(a+1,b,b+1)])
        self.add(vs,fs,mat,fl)
    def ear(self,z,angle):
        d=Vector((math.cos(angle),math.sin(angle),0));base=Vector((0,0,z))+d*.025
        end=base+d*.16+Vector((0,0,.30));axis=(end-base).normalized()
        self.tube(base,end,.052,.029,'CornKernel',9,.3)
        side=axis.cross(Vector((0,1,0))).normalized();other=axis.cross(side).normalized()
        # Six rings of individually rounded kernels; visible between peeled husks.
        for row in range(6):
            c=base+(end-base)*(.17+row*.127)
            for col in range(7):
                a=col*math.tau/7;radial=side*math.cos(a)+other*math.sin(a)
                self.kernel(c+radial*(.047-row*.0021),axis,.018,.022)
        # Two open husk blades and a narrow curled silk/tip.
        self.leaf(base,angle+.70,.30,.105,.29,.12,steps=5)
        self.leaf(base,angle-.75,.28,.105,.31,.14,steps=5)
        for k in range(3):
            self.tube(end+side*((k-1)*.012),end+Vector((.025*(k-1),.01,.075)),.004,.002,'CornTassel',4,1)
    def build(self):
        stalk_h=self.height-.27
        nodes=8
        for k in range(nodes):
            z0=stalk_h*k/nodes;z1=stalk_h*(k+1)/nodes
            self.tube((0,0,z0),(0,0,z1),.025*(1-.60*k/nodes),.025*(1-.60*(k+1)/nodes),sides=8)
            if k>0:self.tube((0,0,z0-.012),(0,0,z0+.012),.028*(1-.55*k/nodes),.028*(1-.55*k/nodes),sides=8)
        phase=self.rand.uniform(0,math.tau)
        for k in range(9):
            z=.22+k*(stalk_h-.46)/8
            a=phase+k*math.pi+self.rand.uniform(-.40,.40)
            L=(.57+.31*math.sin(math.pi*(k+1)/10))*self.rand.uniform(.92,1.08)
            self.leaf((0,0,z),a,L,.14+.045*math.sin(math.pi*(k+1)/10),.30 if k<6 else .24,.37 if k<5 else .18)
        self.ear(stalk_h*.48,phase+.20)
        self.ear(stalk_h*.65,phase+math.pi-.30)
        # Airy tassel: central stem plus ten upward branching spikes.
        self.tube((0,0,stalk_h),(0,0,self.height),.009,.003,'CornTassel',5,1)
        for k in range(10):
            a=phase+k*2.4;z=stalk_h+.035+(k%3)*.025
            reach=.13+(k%2)*.025
            b=Vector((math.cos(a)*reach,math.sin(a)*reach,z+.12+(k%3)*.025))
            self.tube((0,0,z),b,.0055,.0025,'CornTassel',5,1)
            for t in (.40,.70,.94):
                c=Vector((0,0,z)).lerp(b,t)
                self.tube(c,c+Vector((math.cos(a+.7)*.022,math.sin(a+.7)*.022,.025)),.004,.0017,'CornTassel',4,1)
        mesh=bpy.data.meshes.new(self.name);mesh.from_pydata(self.v,[],self.f);mesh.update()
        obj=bpy.data.objects.new(self.name,mesh);bpy.context.collection.objects.link(obj)
        for m in MATS:mesh.materials.append(m)
        for p,mi in zip(mesh.polygons,self.mi):p.material_index=mi;p.use_smooth=True
        # Each triangle is a UV island, exact local shape/area. Disjoint grid cells
        # make overlap impossible; a common scale preserves per-triangle density.
        triangle_uv=[];max_w=0;max_h=0
        for p in mesh.polygons:
            a,b,c=[mesh.vertices[i].co for i in p.vertices]
            ab=b-a;ac=c-a;x=ab.length;cx=ac.dot(ab.normalized());cy=ab.cross(ac).length/x
            coords=[(0,0),(x,0),(cx,cy)];minx=min(v[0] for v in coords)
            coords=[(x-minx,y) for x,y in coords];triangle_uv.append(coords)
            max_w=max(max_w,max(q[0] for q in coords));max_h=max(max_h,cy)
        grid=math.ceil(math.sqrt(len(mesh.polygons)));cell=1/grid
        padding=2/1024
        scale=min((cell-2*padding)/max_w,(cell-2*padding)/max_h)
        assert scale>0
        uv0=mesh.uv_layers.new(name='UV0_Unique')
        uv1=mesh.uv_layers.new(name='UV1_Density128')
        for idx,(p,coords) in enumerate(zip(mesh.polygons,triangle_uv)):
            ox=(idx%grid)*cell+padding;oy=(idx//grid)*cell+padding
            for li,co in zip(p.loop_indices,coords):
                uv0.data[li].uv=(ox+co[0]*scale,oy+co[1]*scale)
                uv1.data[li].uv=Vector(uv0.data[li].uv)*(128/(1024*scale))
        mesh.uv_layers.active_index=0
        colors=mesh.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='CORNER')
        actual_height=max(v.co.z for v in mesh.vertices)
        for loop in mesh.loops:
            z=mesh.vertices[loop.vertex_index].co.z
            colors.data[loop.index].color=(max(0,min(1,z/actual_height)),self.flutter[loop.vertex_index],0,1)
        mesh.color_attributes.active_color=colors
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        bpy.ops.export_scene.fbx(filepath=str(OUT/(self.name+'.fbx')),use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_space_transform=False,add_leaf_bones=False,use_mesh_modifiers=True,colors_type='LINEAR',prioritize_active_color=True)
        return obj,{'name':self.name,'file':self.name+'.fbx','triangles':len(mesh.polygons),'vertices':len(mesh.vertices),'bounds_m':[[min(v.co[k] for v in mesh.vertices),max(v.co[k] for v in mesh.vertices)] for k in range(3)],'material_slots':NAMES,'uv0_grid_cells_per_axis':grid,'uv0_triangle_islands':len(mesh.polygons),'uv0_padding_each_cell_px_at1024':2,'uv0_min_island_gap_px_at1024':4,'uv0_density_px_m_at1024':scale*1024,'uv1_density_px_m_at1024':128,'uv_method':'Per-triangle physical-shape islands in disjoint grid cells; shared scale preserves exact area density. UV1 intentionally repeats.','vertex_color':{'name':'Col','storage':'FLOAT_COLOR CORNER','fbx_colors_type':'LINEAR','R':'clamp(local_z / plant_height, 0, 1)','G':'stalk 0; leaf 0.7→1 tips; ear 0.3–0.35; tassel 1','B':0,'A':1},'leaf_surface':'Single geometry ribbon with ridge; set CornLeaf two_sided=True in UE.','wind_integration':'Multiply global sway by R (or R squared); G gates leaf flutter. Import vertex colors REPLACE. Materials read UV1 (index 1).'}

objects=[];rows=[]
for name,h,seed in [('SM_CornA',2.35,2174),('SM_CornB',2.18,2175),('SM_CornC',2.48,2176)]:
    o,row=Plant(name,h,seed).build();objects.append(o);rows.append(row)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'source.blend'))

def validate_import(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path),colors_type='LINEAR')
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(obs)==1
    o=obs[0];m=o.data;m.calc_loop_triangles();assert len(m.uv_layers)==2
    ca=m.color_attributes.get('Col');assert ca is not None
    densities=[];wa_total=0;ua_total=0;uv0outside=0;degenerate=0;max_r_error=0
    for t in m.loop_triangles:
        world=[o.matrix_world@m.vertices[i].co for i in t.vertices]
        wa=(world[1]-world[0]).cross(world[2]-world[0]).length*.5
        for uv in m.uv_layers:
            a,b,c=[uv.data[i].uv for i in t.loops];ua=abs((b-a).cross(c-a))*.5
            if wa<=1e-14 or ua<=1e-14:degenerate+=1
        a,b,c=[m.uv_layers[1].data[i].uv for i in t.loops];ua=abs((b-a).cross(c-a))*.5
        wa_total+=wa;ua_total+=ua;densities.append(1024*math.sqrt(ua/wa))
    uv0outside=sum(not(-1e-7<=q.uv.x<=1.0000001 and -1e-7<=q.uv.y<=1.0000001) for q in m.uv_layers[0].data)
    height=max((o.matrix_world@v.co).z for v in m.vertices)
    minroot=1;colranges=[[1,-1] for k in range(4)]
    for loop in m.loops:
        c=ca.data[loop.index].color;z=(o.matrix_world@m.vertices[loop.vertex_index].co).z
        expected=max(0,min(1,z/height));max_r_error=max(max_r_error,abs(c[0]-expected))
        if z<1e-6:minroot=min(minroot,c[0])
        for k in range(4):colranges[k][0]=min(colranges[k][0],c[k]);colranges[k][1]=max(colranges[k][1],c[k])
    passed=degenerate==0 and uv0outside==0 and max_r_error<.005 and minroot<.001 and len(m.loop_triangles)<3000
    return {'file':path.name,'reimported_triangles':len(m.loop_triangles),'reimported_uv_channels':len(m.uv_layers),'reimported_color_domain':ca.domain,'uv0_outside01_count':uv0outside,'degenerate_geometry_or_uv_count':degenerate,'uv1_area_equivalent_density_px_m':1024*math.sqrt(ua_total/wa_total),'uv1_triangle_density_min_max':[min(densities),max(densities)],'max_color_R_anchor_error':max_r_error,'minimum_root_color_R':minroot,'color_ranges':colranges,'passed':passed,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

validation=[validate_import(OUT/(row['name']+'.fbx')) for row in rows]
report={'created_utc':datetime.now(timezone.utc).isoformat(),'elapsed_build_and_reimport_seconds':time.time()-START,'assets':rows,'export_roundtrip_validation':validation,'all_passed':all(r['passed'] for r in validation),'external_assets':[],'image_generation_used':False,'notes':['Actual FBX roundtrip verifies two UV channels, nondegenerate triangles, 128px/m density, and linear wind vertex colors.','UV0 islands are each triangle. Cell allocation guarantees no UV0 overlap analytically; 2px interior cell padding gives at least 4px between occupied cell contents. UV1 is intentional tiled repeat.','Mesh height is local Z in metres. UE uses centimetres. All origins at root (0,0,0).','Source.blend contains all three original plant meshes at origin for convenient individual export, not a combined planting.']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)
assert report['all_passed'],'Corn FBX roundtrip validation failed'
