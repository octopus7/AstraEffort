#!/usr/bin/env python3
"""Make a 15 m Victorian passenger carriage as an embedded, instanced GLB.

Authoring space is metres with X across, Y rearward, Z up. One root rotation
converts to glTF's Y-up axes. The window texture is cropped to one window per
panel; wheel spokes and surface relief remain texture detail.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import struct
import numpy as np

STATION=Path(__file__).resolve().parents[1]
OUT=STATION/'modules'/'carriage'
MATERIALS={
 'wood':('carriage_wood',[1,1,1,1],.10,1.0),
 'metal':('boiler',[1,1,1,1],.75,1.0),
 'brass':('brass',[1,1,1,1],.8,.9),
 'wheel':('wheel',[.8,.8,.8,1],.55,1.0),
 'window':('carriage_window',[1,1,1,1],.15,.9),
}
WINDOW_UV=(.34,.145,.65,.573)


def box_mesh():
    faces=[
      ([(.5,-.5,-.5),(.5,.5,-.5),(.5,.5,.5),(.5,-.5,.5)],(1,0,0)),
      ([(-.5,.5,-.5),(-.5,-.5,-.5),(-.5,-.5,.5),(-.5,.5,.5)],(-1,0,0)),
      ([(.5,.5,-.5),(-.5,.5,-.5),(-.5,.5,.5),(.5,.5,.5)],(0,1,0)),
      ([(-.5,-.5,-.5),(.5,-.5,-.5),(.5,-.5,.5),(-.5,-.5,.5)],(0,-1,0)),
      ([(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)],(0,0,1)),
      ([(-.5,.5,-.5),(.5,.5,-.5),(.5,-.5,-.5),(-.5,-.5,-.5)],(0,0,-1))]
    p=[]; n=[]; uv=[]; ix=[]
    for corners,normal in faces:
        i=len(p); p.extend(corners); n.extend([normal]*4); uv.extend([(0,1),(1,1),(1,0),(0,0)]); ix.extend([i,i+1,i+2,i,i+2,i+3])
    return geometry(p,n,uv,ix)


def geometry(p,n,uv,ix):
    return {'p':np.asarray(p,dtype=np.float32),'n':np.asarray(n,dtype=np.float32),
            'uv':np.asarray(uv,dtype=np.float32),'i':np.asarray(ix,dtype=np.uint16)}


def cylinder_mesh(sides=12):
    p=[]; n=[]; uv=[]; ix=[]
    for k in range(sides):
        a=2*math.pi*k/sides; c=2*math.pi*(k+1)/sides
        pa=(.5*math.cos(a),.5*math.sin(a)); pc=(.5*math.cos(c),.5*math.sin(c))
        i=len(p); p.extend([(pa[0],pa[1],-.5),(pc[0],pc[1],-.5),(pc[0],pc[1],.5),(pa[0],pa[1],.5)])
        n.extend([(math.cos(a),math.sin(a),0),(math.cos(c),math.sin(c),0),(math.cos(c),math.sin(c),0),(math.cos(a),math.sin(a),0)])
        uv.extend([(k/sides,1),((k+1)/sides,1),((k+1)/sides,0),(k/sides,0)]); ix.extend([i,i+1,i+2,i,i+2,i+3])
    for z,sgn in [(-.5,-1),(.5,1)]:
        i=len(p); p.append((0,0,z)); n.append((0,0,sgn)); uv.append((.5,.5))
        for k in range(sides+1):
            a=2*math.pi*k/sides; p.append((.5*math.cos(a),.5*math.sin(a),z)); n.append((0,0,sgn)); uv.append((.5+.49*math.cos(a),.5-.49*math.sin(a)))
        for k in range(sides): ix.extend([i,i+k+2,i+k+1] if sgn<0 else [i,i+k+1,i+k+2])
    return geometry(p,n,uv,ix)


def window_mesh(side):
    u0,v0,u1,v1=WINDOW_UV
    if side=='right':
        p=[(0,-.5,-.5),(0,.5,-.5),(0,.5,.5),(0,-.5,.5)]
        n=[(1,0,0)]*4; uv=[(u0,v1),(u1,v1),(u1,v0),(u0,v0)]
    elif side=='left':
        p=[(0,.5,-.5),(0,-.5,-.5),(0,-.5,.5),(0,.5,.5)]
        n=[(-1,0,0)]*4; uv=[(u0,v1),(u1,v1),(u1,v0),(u0,v0)]
    elif side=='front':
        p=[(-.5,0,-.5),(.5,0,-.5),(.5,0,.5),(-.5,0,.5)]
        n=[(0,-1,0)]*4; uv=[(u0,v1),(u1,v1),(u1,v0),(u0,v0)]
    else:
        p=[(.5,0,-.5),(-.5,0,-.5),(-.5,0,.5),(.5,0,.5)]
        n=[(0,1,0)]*4; uv=[(u0,v1),(u1,v1),(u1,v0),(u0,v0)]
    return geometry(p,n,uv,[0,1,2,0,2,3])


def wheel_mesh(sides=24):
    # Two circular, outward-facing wheel images; the cylindrical tread uses metal.
    p=[]; n=[]; uv=[]; ix=[]
    for x,sgn in [(-.5,-1),(.5,1)]:
        i=len(p); p.append((x,0,0)); n.append((sgn,0,0)); uv.append((.5,.5))
        for k in range(sides+1):
            a=2*math.pi*k/sides; y=.5*math.cos(a); z=.5*math.sin(a)
            p.append((x,y,z)); n.append((sgn,0,0)); uv.append((.5+.49*math.cos(a),.5-.49*math.sin(a)))
        for k in range(sides): ix.extend([i,i+k+2,i+k+1] if sgn<0 else [i,i+k+1,i+k+2])
    disks=geometry(p,n,uv,ix)
    p=[]; n=[]; uv=[]; ix=[]
    for k in range(sides):
        a=2*math.pi*k/sides; c=2*math.pi*(k+1)/sides
        ya,za=.5*math.cos(a),.5*math.sin(a); yc,zc=.5*math.cos(c),.5*math.sin(c); i=len(p)
        p.extend([(-.5,ya,za),(-.5,yc,zc),(.5,yc,zc),(.5,ya,za)])
        n.extend([(0,math.cos(a),math.sin(a)),(0,math.cos(c),math.sin(c)),(0,math.cos(c),math.sin(c)),(0,math.cos(a),math.sin(a))])
        uv.extend([(k/sides,0),((k+1)/sides,0),((k+1)/sides,1),(k/sides,1)]); ix.extend([i,i+1,i+2,i,i+2,i+3])
    return [(disks,'wheel'),(geometry(p,n,uv,ix),'metal')]


def roof_mesh():
    p=[]; n=[]; uv=[]; ix=[]; seg=24
    # Thin shell: upper and underside, with front/rear edges closed.
    for layer in (0,1):
        for k in range(seg+1):
            a=math.pi-k*math.pi/seg; x=1.45*math.cos(a); z=3.62+.47*math.sin(a)-layer*.06
            normal=np.array([math.cos(a)/1.45,0,math.sin(a)/.47]); normal/=np.linalg.norm(normal)
            if layer: normal=-normal
            for y in (0.,15.): p.append((x,y,z)); n.append(normal); uv.append((k/seg,y/15))
        off=layer*(seg+1)*2
        for k in range(seg):
            a=off+2*k; b=a+1; c=a+2; d=a+3
            ix.extend([a,c,b,b,c,d] if layer==0 else [a,b,c,b,d,c])
    for y,end in [(0,-1),(15,1)]:
        for k in range(seg):
            a=math.pi-k*math.pi/seg; c=math.pi-(k+1)*math.pi/seg
            x0,z0=1.45*math.cos(a),3.62+.47*math.sin(a); x1,z1=1.45*math.cos(c),3.62+.47*math.sin(c); i=len(p)
            p.extend([(x0,y,z0-.06),(x1,y,z1-.06),(x1,y,z1),(x0,y,z0)])
            n.extend([(0,end,0)]*4); uv.extend([(0,1),(1,1),(1,0),(0,0)])
            ix.extend([i,i+1,i+2,i,i+2,i+3] if end==-1 else [i,i+2,i+1,i,i+3,i+2])
    return geometry(p,n,uv,ix)


def transform(center,scale):
    m=np.eye(4); m[:3,:3]=np.diag(scale); m[:3,3]=center; return m


def between(a,b,width,depth):
    a=np.asarray(a,float); b=np.asarray(b,float); z=b-a; length=np.linalg.norm(z)
    if length<1e-8: raise ValueError('zero-length beam')
    z=z/length; ref=np.array([0.,1.,0.]) if abs(z[1])<.9 else np.array([0.,0.,1.])
    x=np.cross(ref,z); x/=np.linalg.norm(x); y=np.cross(z,x)
    m=np.eye(4); m[:3,0]=x*width; m[:3,1]=y*depth; m[:3,2]=z*length; m[:3,3]=(a+b)/2
    return m


class Carriage:
    def __init__(self):
        self.meshes={}; self.nodes=[]
        for mat in ('wood','metal','brass'):
            self.meshes['box_'+mat]=[(box_mesh(),mat)]
            self.meshes['cylinder_'+mat]=[(cylinder_mesh(),mat)]
        for side in ('left','right','front','rear'): self.meshes['window_'+side]=[(window_mesh(side),'window')]
        self.meshes['wheel_24']=wheel_mesh(); self.meshes['barrel_roof']=[(roof_mesh(),'metal')]
    def add(self,mesh,name,matrix,group=None): self.nodes.append((mesh,name,np.asarray(matrix,float),group))
    def box(self,name,center,scale,mat='metal',group=None): self.add('box_'+mat,name,transform(center,scale),group)
    def beam(self,name,a,b,width=.04,depth=.04,mat='metal',group=None): self.add('box_'+mat,name,between(a,b,width,depth),group)
    def cylinder(self,name,center,diameter,height,mat='metal',group=None,axis='z'):
        m=transform(center,(diameter,diameter,height))
        if axis=='y':
            m=np.eye(4); m[:3,0]=[diameter,0,0]; m[:3,1]=[0,0,diameter]; m[:3,2]=[0,-height,0]; m[:3,3]=center
        self.add('cylinder_'+mat,name,m,group)
    def wheel(self,name,x,y,group): self.add('wheel_24',name,transform((x,y,.45),(.14,.9,.9)),group)
    def bounds_counts(self):
        lo=np.full(3,np.inf); hi=-lo; tris=0; used=set()
        for mesh,name,m,group in self.nodes:
            for g,mat in self.meshes[mesh]:
                v=g['p'].astype(float)@m[:3,:3].T+m[:3,3]; lo=np.minimum(lo,v.min(0)); hi=np.maximum(hi,v.max(0)); tris+=len(g['i'])//3
            used.add(mesh)
        unique=sum(sum(len(g['i'])//3 for g,_ in self.meshes[mesh]) for mesh in used)
        return lo,hi,tris,unique
    def export(self,path):
        meshes={k:v for k,v in self.meshes.items() if any(n[0]==k for n in self.nodes)}
        binary=bytearray(); views=[]; accessors=[]; mesh_json=[]
        def blob(data,target=None):
            while len(binary)%4: binary.append(0)
            off=len(binary); binary.extend(data); v={'buffer':0,'byteOffset':off,'byteLength':len(data)}
            if target: v['target']=target
            views.append(v); return len(views)-1
        def accessor(a,typ,ctype,target,bounds=False):
            v=blob(a.tobytes(),target); row={'bufferView':v,'componentType':ctype,'count':len(a),'type':typ}
            if bounds:
                d=a.reshape(len(a),-1); row['min']=d.min(0).astype(float).tolist(); row['max']=d.max(0).astype(float).tolist()
            accessors.append(row); return len(accessors)-1
        names=[k for k in MATERIALS if any(mat==k for prims in meshes.values() for _,mat in prims)]; matidx={k:i for i,k in enumerate(names)}
        meshidx={}
        for mesh,prims in meshes.items():
            out=[]
            for g,mat in prims:
                pos=accessor(g['p'],'VEC3',5126,34962,True); norm=accessor(g['n'],'VEC3',5126,34962); uv=accessor(g['uv'],'VEC2',5126,34962); inds=accessor(g['i'],'SCALAR',5123,34963)
                out.append({'attributes':{'POSITION':pos,'NORMAL':norm,'TEXCOORD_0':uv},'indices':inds,'material':matidx[mat]})
            meshidx[mesh]=len(mesh_json); mesh_json.append({'name':mesh,'primitives':out})
        images=[]; textures=[]; lookup={}
        def tex(path):
            path=Path(path); key=str(path.resolve())
            if key not in lookup:
                v=blob(path.read_bytes()); images.append({'name':path.name,'bufferView':v,'mimeType':'image/png'}); textures.append({'source':len(images)-1,'sampler':0}); lookup[key]=len(textures)-1
            return lookup[key]
        mats=[]; paths={}
        for name in names:
            stem,factor,metal,rough=MATERIALS[name]
            p={k:STATION/'textures'/f'{stem}_{suffix}.png' for k,suffix in [('base','basecolor'),('normal','normal'),('orm','orm')]}
            for x in p.values():
                if not x.is_file(): raise FileNotFoundError(x)
            paths[name]={k:str(v.relative_to(STATION)) for k,v in p.items()}
            base=tex(p['base']); mr=tex(p['orm']); normal=tex(p['normal'])
            row={'name':name,'pbrMetallicRoughness':{'baseColorFactor':factor,'baseColorTexture':{'index':base},'metallicFactor':metal,'roughnessFactor':rough,'metallicRoughnessTexture':{'index':mr}},'normalTexture':{'index':normal,'scale':.55},'alphaMode':'OPAQUE'}
            if name=='window': row['emissiveTexture']={'index':base}; row['emissiveFactor']=[.14,.08,.03]
            mats.append(row)
        groups=['bogie_front','bogie_rear']; nodes=[{'name':'author_z_up_to_gltf_y_up','rotation':[-math.sqrt(.5),0,0,math.sqrt(.5)],'children':[]}]
        groups_index={}
        for group in groups:
            groups_index[group]=len(nodes); nodes.append({'name':group,'children':[]}); nodes[0]['children'].append(groups_index[group])
        for mesh,name,m,group in self.nodes:
            idx=len(nodes); nodes.append({'name':name,'mesh':meshidx[mesh],'matrix':m.flatten(order='F').round(8).tolist()})
            nodes[groups_index[group]]['children'].append(idx) if group else nodes[0]['children'].append(idx)
        doc={'asset':{'version':'2.0','generator':'Riverdale carriage Python mesh builder'},'scene':0,'scenes':[{'nodes':[0]}],
             'nodes':nodes,'meshes':mesh_json,'materials':mats,'textures':textures,'images':images,
             'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}],
             'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors}
        j=json.dumps(doc,separators=(',',':'),allow_nan=False).encode(); j+=b' '*((-len(j))%4); binary+=b'\0'*((-len(binary))%4)
        total=12+8+len(j)+8+len(binary)
        path.write_bytes(struct.pack('<4sII',b'glTF',2,total)+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(binary),b'BIN\0')+binary)
        return {'nodes':len(nodes),'meshes':len(meshes),'embedded_images':len(images),'materials':paths}


def build():
    b=Carriage()
    # The side timber, floor and black underframe form the main silhouette.
    b.box('carriage_body',(0,7.5,2.40),(2.80,13.0,2.50),'wood')
    b.box('main_underframe',(0,7.5,1.04),(2.65,14.7,.25),'metal')
    b.add('barrel_roof','barrel_roof',np.eye(4))
    # Decorative curved roofing seams are separate, reusable struts.
    for j,y in enumerate((1.20,7.5,13.8)):
        angles=np.linspace(math.pi,0,17)
        pts=[(1.42*math.cos(a),3.625+.47*math.sqrt(max(0,1-(1.42*math.cos(a)/1.45)**2))) for a in angles]
        for k in range(16): b.beam(f'roof_rib_{j}_{k}',(pts[k][0],y,pts[k][1]),(pts[k+1][0],y,pts[k+1][1]),.035,.035)
    for j,y in enumerate((2.0,4.75,7.5,10.25,13.0)):
        b.cylinder(f'roof_vent_neck_{j}',(0,y,4.125),.13,.07)
        b.cylinder(f'roof_vent_cap_{j}',(0,y,4.185),.23,.03)
    for side,x in [('left',-1.0),('right',1.0)]:
        for j,z in enumerate((1.27,1.34,1.85,3.55)):
            b.box(f'{side}_long_gold_lining_{j}',(x*1.42,7.5,z),(.035,12.95,.023),'brass')
        for j,y in enumerate(np.linspace(2.25,12.75,8)):
            b.add('window_'+side,f'side_window_{side}_{j}',transform((x*1.405,y,2.71),(1,1.10,1.42)))
            for k,zz in enumerate((1.99,3.43)):
                b.box(f'{side}_window_{j}_horizontal_frame_{k}',(x*1.422,y,zz),(.04,1.17,.04),'brass')
            for k,yy in enumerate((y-.565,y+.565)):
                b.box(f'{side}_window_{j}_vertical_frame_{k}',(x*1.422,yy,2.71),(.04,.04,1.46),'brass')
        for j,y in enumerate((1.13,13.87)):
            b.box(f'{side}_end_molding_{j}',(x*1.42,y,2.40),(.035,.075,2.35),'brass')
    # Two bogies, each with two axles and separate left/right wheel nodes.
    for label,center in [('front',4.15),('rear',10.85)]:
        group='bogie_'+label
        for side,x in [('left',-.7175),('right',.7175)]:
            for end,delta in [('front',-.90),('rear',.90)]: b.wheel(f'wheel_{label}_bogie_{side}_{end}',x,center+delta,group)
        for j,dy in enumerate((-.90,.90)):
            b.box(f'{group}_axle_{j}',(0,center+dy,.45),(1.62,.10,.10),'metal',group)
        for side,x in [('left',-.87),('right',.87)]:
            b.box(f'{group}_side_beam_{side}',(x,center,.79),(.14,2.50,.18),'metal',group)
            b.box(f'{group}_spring_block_{side}',(x,center,.65),(.16,.42,.33),'metal',group)
        b.box(f'{group}_crossbeam',(0,center,.81),(1.88,.25,.18),'metal',group)
    for j,y in enumerate((6.2,7.5,8.8)): b.box(f'underbody_equipment_{j}',(0,y,.78),(1.55,.72,.36),'metal')
    # Open end balconies and stepped corner access, all inside Y=0..15.
    for label,front in [('front',True),('rear',False)]:
        ey=.13 if front else 14.87; center=.55 if front else 14.45; door_y=.995 if front else 14.005
        b.box(f'{label}_balcony_floor',(0,center,1.05),(2.60,.90,.15),'metal')
        b.box(f'{label}_door',(0,door_y,2.29),(.97,.08,2.28),'wood')
        b.add('window_'+label,f'{label}_door_window',transform((0,.948 if front else 14.052,2.77),(.70,1,1.12)))
        for k,x in enumerate((-.5,.5)): b.box(f'{label}_door_frame_{k}',(x,door_y,2.30),(.04,.11,2.32),'brass')
        b.box(f'{label}_door_top',(0,door_y,3.45),(1.04,.11,.04),'brass')
        b.box(f'{label}_door_bottom',(0,door_y,1.16),(1.04,.11,.04),'brass')
        for k,x in enumerate(np.linspace(-1.15,1.15,7)):
            b.box(f'{label}_railing_post_{k}',(x,ey,1.58),(.055,.055,.98),'metal')
            b.box(f'{label}_railing_finial_{k}',(x,ey,2.09),(.075,.075,.07),'brass')
        for k,z in enumerate((1.24,2.05)): b.box(f'{label}_railing_bar_{k}',(0,ey,z),(2.38,.055,.055),'metal')
        for side,x in [('left',-1.22),('right',1.22)]:
            for k,z in enumerate((1.24,2.05)): b.box(f'{label}_{side}_balcony_side_bar_{k}',(x,center,z),(.055,.82,.055),'metal')
            b.box(f'{label}_{side}_balcony_side_post',(x,center,1.60),(.055,.055,.92),'metal')
            for k,z in enumerate((.42,.62,.82)):
                step_y=(.22+.16*k) if front else (14.78-.16*k)
                b.box(f'{label}_{side}_step_{k}',(x,step_y,z),(.38,.27,.07),'metal')
                b.box(f'{label}_{side}_step_gold_{k}',(x,step_y-(.125 if front else -.125),z+.04),(.38,.018,.018),'brass')
            for k,dx in enumerate((-.16,.16)):
                near_y=.20 if front else 14.80; far_y=.69 if front else 14.31
                b.beam(f'{label}_{side}_step_stringer_{k}',(x+dx,near_y,.37),(x+dx,far_y,.98),.04,.04)
        for side,x in [('left',-.88),('right',.88)]: b.cylinder(f'{label}_buffer_{side}',(x,ey,.83),.32,.18,'metal',axis='y')
        b.box(f'{label}_central_coupler',(0,.08 if front else 14.92,.73),(.40,.16,.20),'metal')
    return b


def main():
    OUT.mkdir(parents=True,exist_ok=True); b=build(); lo,hi,tris,unique=b.bounds_counts()
    info=b.export(OUT/'passenger_carriage.glb')
    manifest={'units':'meters','authoring_axes':{'X':'across track','Y':'front to rear','Z':'up'},
      'front_direction':'-Y','gltf_root_rotation_quaternion_xyzw':[-math.sqrt(.5),0,0,math.sqrt(.5)],
      'modules':{'passenger_carriage':{'file':'passenger_carriage.glb','design_dimensions_m':{'width':2.9,'length':15,'height':4.2},
      'authored_bounds_m':{'min':lo.round(4).tolist(),'max':hi.round(4).tolist()},'wheel_radius_m':.45,'wheel_centers_x_m':[-.7175,.7175],
      'rail_alignment':'Wheel bottoms are Z=0; translate asset +0.22 m in authoring Z onto the specified rail top.',
      'triangles_instanced':tris,'triangles_unique_meshes':unique,'window_texture_single_panel_uv':list(WINDOW_UV),
      'mesh_nodes':len(b.nodes),'export':info}}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('passenger_carriage:',tris,'rendered triangles,',unique,'unique mesh triangles; bounds',lo.round(4),'to',hi.round(4))

if __name__=='__main__': main()
