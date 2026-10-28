#!/usr/bin/env python3
"""Build reusable Victorian iron/glass station modules as embedded glTF 2 GLBs.

Author in metres, Z up; a single -90-degree X rotation at each scene root
converts the authored axes to glTF Y up. Repeated struts and column sections
are instances of shared meshes, not individually duplicated vertex buffers.

The texture configuration is JSON with iron, ornament and glass entries, each
containing base, normal, orm and uv ([u0,v0,u1,v1], top-left image UV).
Paths may be absolute or relative to the station project directory.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import struct
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

STATION = Path(__file__).resolve().parents[1]
OUT = STATION / 'modules' / 'shed'


def unit_box(uv):
    faces = [
        ([(.5,-.5,-.5),(.5,.5,-.5),(.5,.5,.5),(.5,-.5,.5)],(1,0,0)),
        ([(-.5,.5,-.5),(-.5,-.5,-.5),(-.5,-.5,.5),(-.5,.5,.5)],(-1,0,0)),
        ([(.5,.5,-.5),(-.5,.5,-.5),(-.5,.5,.5),(.5,.5,.5)],(0,1,0)),
        ([(-.5,-.5,-.5),(.5,-.5,-.5),(.5,-.5,.5),(-.5,-.5,.5)],(0,-1,0)),
        ([(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)],(0,0,1)),
        ([(-.5,.5,-.5),(.5,.5,-.5),(.5,-.5,-.5),(-.5,-.5,-.5)],(0,0,-1)),
    ]
    u0,v0,u1,v1=uv
    vertices=[]; normals=[]; uvs=[]; indices=[]
    for corners,normal in faces:
        i=len(vertices); vertices.extend(corners); normals.extend([normal]*4)
        uvs.extend([(u0,v1),(u1,v1),(u1,v0),(u0,v0)])
        indices.extend([i,i+1,i+2,i,i+2,i+3])
    return {'p':np.asarray(vertices,dtype=np.float32),'n':np.asarray(normals,dtype=np.float32),
            'uv':np.asarray(uvs,dtype=np.float32),'i':np.asarray(indices,dtype=np.uint16)}


def unit_column(uv, sides=10, vertical_repeats=1):
    u0,v0,u1,v1=uv
    v=[]; n=[]; t=[]; idx=[]
    # Side faces are split at each angle so a crisp cast section catches light.
    for k in range(sides):
        a=2*math.pi*k/sides; b=2*math.pi*(k+1)/sides
        pa=(.5*math.cos(a),.5*math.sin(a)); pb=(.5*math.cos(b),.5*math.sin(b))
        na=(math.cos(a),math.sin(a),0); nb=(math.cos(b),math.sin(b),0)
        i=len(v); v.extend([(pa[0],pa[1],-.5),(pb[0],pb[1],-.5),(pb[0],pb[1],.5),(pa[0],pa[1],.5)])
        n.extend([na,nb,nb,na]); ua=u0+(u1-u0)*k/sides; ub=u0+(u1-u0)*(k+1)/sides
        side_bottom=v1 if vertical_repeats==1 else v0+vertical_repeats
        t.extend([(ua,side_bottom),(ub,side_bottom),(ub,v0),(ua,v0)]); idx.extend([i,i+1,i+2,i,i+2,i+3])
    for z,sgn in [(-.5,-1),(.5,1)]:
        i=len(v); v.append((0,0,z)); n.append((0,0,sgn)); t.append(((u0+u1)/2,(v0+v1)/2))
        for k in range(sides+1):
            a=2*math.pi*k/sides
            v.append((.5*math.cos(a),.5*math.sin(a),z)); n.append((0,0,sgn))
            t.append(((u0+u1)/2+(u1-u0)*.45*math.cos(a), (v0+v1)/2+(v1-v0)*.45*math.sin(a)))
        for k in range(sides):
            idx.extend([i,i+k+2,i+k+1] if sgn<0 else [i,i+k+1,i+k+2])
    return {'p':np.asarray(v,dtype=np.float32),'n':np.asarray(n,dtype=np.float32),
            'uv':np.asarray(t,dtype=np.float32),'i':np.asarray(idx,dtype=np.uint16)}


def roof_mesh(uv, canopy=False):
    u0,v0,u1,v1=uv
    if canopy:
        pts=[(-3.,4.45),(0.,4.91),(3.,4.45)]
    else:
        pts=[(14*math.cos(a),11+11*math.sin(a)) for a in np.linspace(math.pi,0,25)]
    p=[]; n=[]; t=[]; idx=[]
    for k,(x,z) in enumerate(pts):
        if canopy:
            # smooth enough for the translucent roof; duplicate at ridge if needed
            dzdx=.46/3 if k==0 else (-.46/3 if k==2 else 0)
            normal=np.array([-dzdx,0.,1.]); normal=normal/np.linalg.norm(normal)
        else:
            a=math.pi-k*math.pi/24
            normal=np.array([math.cos(a)/14,0,math.sin(a)/11]); normal=normal/np.linalg.norm(normal)
        for y in (0.,8.):
            p.append((x,y,z)); n.append(normal); t.append((u0+(u1-u0)*k/(len(pts)-1),v0+(v1-v0)*y/8))
    for k in range(len(pts)-1):
        a=2*k; b=a+1; c=a+2; d=a+3
        # x increases. cross(+X,+Y) points toward +Z.
        idx.extend([a,c,b,b,c,d])
    return {'p':np.asarray(p,dtype=np.float32),'n':np.asarray(n,dtype=np.float32),
            'uv':np.asarray(t,dtype=np.float32),'i':np.asarray(idx,dtype=np.uint16)}


def transform(center, scale):
    m=np.eye(4); m[:3,:3]=np.diag(scale); m[:3,3]=center
    return m


def between(a,b,width,depth):
    a=np.asarray(a,dtype=float); b=np.asarray(b,dtype=float)
    z=b-a; length=np.linalg.norm(z)
    if length < 1e-7: raise ValueError('Zero-length beam')
    z=z/length
    ref=np.array([0.,1.,0.]) if abs(z[1]) < .9 else np.array([0.,0.,1.])
    x=np.cross(ref,z); x=x/np.linalg.norm(x); y=np.cross(z,x)
    m=np.eye(4); m[:3,0]=x*width; m[:3,1]=y*depth; m[:3,2]=z*length; m[:3,3]=(a+b)/2
    return m


class Builder:
    def __init__(self, name, config):
        self.name=name; self.config=config; self.meshes={}; self.nodes=[]
        for material in ('iron','ornament'):
            self.meshes['box_'+material]=(unit_box(config[material]['uv']),material)
            self.meshes['column_'+material]=(unit_column(config[material]['uv']),material)
        # Keep the same shaft geometry but repeat the iron texture about every 2 m.
        self.meshes['shaft_tall_iron']=(unit_column(config['iron']['uv'],vertical_repeats=5),'iron')
        self.meshes['shaft_short_iron']=(unit_column(config['iron']['uv'],vertical_repeats=2),'iron')
    def add(self,mesh,name,matrix): self.nodes.append((mesh,name,np.asarray(matrix,dtype=float)))
    def box(self,name,center,scale,material='iron'): self.add('box_'+material,name,transform(center,scale))
    def cylinder(self,name,center,diameter,height,material='ornament'):
        self.add('column_'+material,name,transform(center,(diameter,diameter,height)))
    def beam(self,name,a,b,w=.12,d=.12,material='iron'): self.add('box_'+material,name,between(a,b,w,d))
    def roof(self,canopy=False):
        self.meshes['glazed_roof']=(roof_mesh(self.config['glass']['uv'],canopy),'glass')
        self.add('glazed_roof','glazed_roof',np.eye(4))
    def column(self,x,y,height,scale=1.,label='column'):
        # Slim cast-iron column with separate bases, necking and capital.
        s=scale; base_h=.18*s; neck_h=.23*s; top_h=.42*s
        self.box(label+'_foot',(x,y,base_h/2),(.8*s,.8*s,base_h),'ornament')
        self.box(label+'_base',(x,y,base_h+neck_h/2),(.63*s,.63*s,neck_h),'ornament')
        h=height-base_h-neck_h-top_h
        shaft='shaft_tall_iron' if height>8 else 'shaft_short_iron'
        self.add(shaft,label+'_shaft',transform((x,y,base_h+neck_h+h/2),(.45*s,.45*s,h)))
        self.cylinder(label+'_lower_collar',(x,y,base_h+neck_h+.12*s),.53*s,.10*s,'iron')
        self.cylinder(label+'_upper_collar',(x,y,height-top_h-.10*s),.53*s,.10*s,'iron')
        self.box(label+'_capital_neck',(x,y,height-.30*s),(.62*s,.62*s,.22*s),'ornament')
        self.box(label+'_capital',(x,y,height-.09*s),(.8*s,.8*s,.18*s),'ornament')
    def bounds_and_count(self):
        lower=np.array([np.inf]*3); upper=-lower; tris=0
        used=set()
        for mesh,name,m in self.nodes:
            g,_=self.meshes[mesh]; v=g['p'].astype(float)@m[:3,:3].T+m[:3,3]
            lower=np.minimum(lower,v.min(0)); upper=np.maximum(upper,v.max(0)); tris += len(g['i'])//3; used.add(mesh)
        unique=sum(len(self.meshes[m][0]['i'])//3 for m in used)
        return lower,upper,tris,unique

    def export(self,path):
        self.meshes={k:v for k,v in self.meshes.items() if any(n[0]==k for n in self.nodes)}
        binary=bytearray(); views=[]; accessors=[]; mesh_json=[]
        def blob(data,target=None):
            while len(binary)%4: binary.append(0)
            off=len(binary); binary.extend(data)
            row={'buffer':0,'byteOffset':off,'byteLength':len(data)}
            if target: row['target']=target
            views.append(row); return len(views)-1
        def accessor(a,typ,ctype,target,with_bounds=False):
            v=blob(a.tobytes(),target); row={'bufferView':v,'componentType':ctype,'count':len(a),'type':typ}
            if with_bounds:
                a2=a.reshape(len(a),-1); row['min']=a2.min(0).astype(float).tolist(); row['max']=a2.max(0).astype(float).tolist()
            accessors.append(row); return len(accessors)-1
        materials=[m for m in ('iron','ornament','glass') if any(mat==m for _,mat in self.meshes.values())]
        material_index={m:i for i,m in enumerate(materials)}
        mesh_index={}
        for mesh,(g,mat) in self.meshes.items():
            pos=accessor(g['p'],'VEC3',5126,34962,True); norm=accessor(g['n'],'VEC3',5126,34962)
            uv=accessor(g['uv'],'VEC2',5126,34962); ind=accessor(g['i'],'SCALAR',5123,34963)
            mesh_index[mesh]=len(mesh_json)
            mesh_json.append({'name':mesh,'primitives':[{'attributes':{'POSITION':pos,'NORMAL':norm,'TEXCOORD_0':uv},'indices':ind,'material':material_index[mat]}]})
        images=[]; textures=[]; tex_lookup={}
        def texture(path):
            path=Path(path).resolve(); key=str(path)
            if key not in tex_lookup:
                data=path.read_bytes(); view=blob(data)
                mime='image/png' if path.suffix.lower()=='.png' else 'image/jpeg'
                images.append({'name':path.name,'bufferView':view,'mimeType':mime})
                textures.append({'source':len(images)-1,'sampler':0}); tex_lookup[key]=len(textures)-1
            return tex_lookup[key]
        material_json=[]
        for mat in materials:
            info=self.config[mat]; glass=mat=='glass'
            pbr={'baseColorFactor':[.88,.94,1.0,.34] if glass else [1,1,1,1],
                 'baseColorTexture':{'index':texture(info['base'])},
                 'metallicFactor':0.0 if glass else .60,'roughnessFactor':.68 if glass else 1.0,
                 'metallicRoughnessTexture':{'index':texture(info['orm'])}}
            material_json.append({'name':mat,'pbrMetallicRoughness':pbr,
                                  'normalTexture':{'index':texture(info['normal']),'scale':.08 if glass else .75},
                                  'alphaMode':'BLEND' if glass else 'OPAQUE','doubleSided':glass})
        node_json=[{'name':'author_z_up_to_gltf_y_up','rotation':[-math.sqrt(.5),0,0,math.sqrt(.5)],'children':list(range(1,len(self.nodes)+1))}]
        for mesh,name,m in self.nodes:
            node_json.append({'name':name,'mesh':mesh_index[mesh],'matrix':m.flatten(order='F').round(8).tolist()})
        doc={'asset':{'version':'2.0','generator':'Riverdale station Python mesh builder'},'scene':0,
             'scenes':[{'nodes':[0]}], 'nodes':node_json,'meshes':mesh_json,
             'materials':material_json,'textures':textures,'images':images,
             'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':10497}],
             'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors}
        json_chunk=json.dumps(doc,separators=(',',':'),allow_nan=False).encode('utf8')
        json_chunk += b' '*((-len(json_chunk))%4)
        binary += b'\0'*((-len(binary))%4)
        total=12+8+len(json_chunk)+8+len(binary)
        path.write_bytes(struct.pack('<4sII',b'glTF',2,total)+struct.pack('<I4s',len(json_chunk),b'JSON')+json_chunk+struct.pack('<I4s',len(binary),b'BIN\0')+binary)
        return {'images':len(images),'meshes':len(mesh_json),'nodes':len(node_json)}


def arch_points(outer=True):
    a=np.linspace(math.pi,0,25)
    return [(14*math.cos(t),11+11*math.sin(t)) if outer else (13.22*math.cos(t),11+10.15*math.sin(t)) for t in a]


def trussed_arch(b,y,face='arch',depth=.34,ornate=False):
    upper=arch_points(True); lower=arch_points(False)
    for k in range(24):
        ux,uz=upper[k]; vx,vz=upper[k+1]; lx,lz=lower[k]; mx,mz=lower[k+1]
        b.beam(f'{face}_outer_{k}',(ux,y,uz),(vx,y,vz),.24,depth)
        b.beam(f'{face}_inner_{k}',(lx,y,lz),(mx,y,mz),.18,depth*.8)
        b.beam(f'{face}_web_a_{k}',(ux,y,uz),(mx,y,mz),.065,depth*.65)
        b.beam(f'{face}_web_b_{k}',(lx,y,lz),(vx,y,vz),.065,depth*.65)
    if ornate:
        # A light openwork parapet gives the station entrance its silhouette.
        for k in range(24):
            x,z=upper[k]; nx,nz=upper[k+1]
            b.beam(f'{face}_parapet_{k}',(x,y,z+.48),(nx,y,nz+.48),.085,.24)
            b.beam(f'{face}_parapet_cross_a_{k}',(x,y,z),(nx,y,nz+.48),.055,.18)
            b.beam(f'{face}_parapet_cross_b_{k}',(x,y,z+.48),(nx,y,nz),.055,.18)
        for k in (3,6,9,12,15,18,21):
            x,z=upper[k]
            b.box(f'{face}_crown_pier_{k}',(x,y,z+.24),(.20,.48,.48),'ornament')
            b.box(f'{face}_crown_cap_{k}',(x,y,z+.52),(.27,.56,.10),'ornament')
    return upper,lower


def build_shed(config):
    b=Builder('shed_bay',config); b.roof(); trussed_arch(b,7.75,'rear_rib',depth=.42)
    for j,y in enumerate((2.,4.,6.)):
        points=arch_points(True)
        for k in range(24):
            b.beam(f'light_hoop_{j}_{k}',(points[k][0],y,points[k][1]),(points[k+1][0],y,points[k+1][1]),.085,.085)
    # Longitudinal glazing bars follow the roof from one seam to the next.
    for k,(x,z) in enumerate(arch_points(True)):
        b.beam(f'glazing_bar_{k}',(x,0,z),(x,8,z),.075,.075)
    for side,x in [('left',-14.),('right',14.)]:
        b.column(x,7.6,11.,1.,side+'_rear_column')
        b.beam(side+'_eaves_girder',(x,0,11),(x,8,11),.26,.26)
        b.beam(side+'_knee_brace',(x,7.75,8.7),(x*.89,7.75,12.7),.13,.18)
    return b


def build_front(config):
    b=Builder('front_arch',config); trussed_arch(b,.35,'front',depth=.50,ornate=True)
    for side,x in [('left',-14.),('right',14.)]:
        b.column(x,.4,11.,1.,side+'_front_column')
        b.box(side+'_pier',(x,.4,11.47),(.64,.64,.94),'ornament')
        b.box(side+'_pier_cap',(x,.4,11.98),(.76,.70,.13),'ornament')
        b.cylinder(side+'_finial',(x,.4,12.18),.18,.30,'ornament')
        b.beam(side+'_corner_brace',(x,.35,8.6),(x*.88,.35,12.8),.15,.23)
    return b


def build_canopy(config):
    b=Builder('platform_canopy_bay',config); b.roof(canopy=True)
    for k,y in enumerate((.08,2.,4.,6.,7.92)):
        size=.18 if k==2 else .09
        b.beam(f'canopy_rafter_left_{k}',(-2.96,y,4.46),(0,y,4.91),size,size)
        b.beam(f'canopy_rafter_right_{k}',(0,y,4.91),(2.96,y,4.46),size,size)
    for k,x in enumerate((-2.94,-2.20,-1.47,-.735,0,.735,1.47,2.20,2.94)):
        z=4.91-(abs(x)/3)*.46
        b.beam(f'canopy_purlin_{k}',(x,0,z),(x,8,z),.075,.075)
    for side,x in [('left',-2.65),('right',2.65)]:
        b.column(x,4.,4.45,.66,side+'_canopy_column')
        b.beam(side+'_canopy_transverse_knee',(x,4,3.55),(x*.66,4,4.51),.10,.12)
        b.beam(side+'_canopy_longitudinal_knee_a',(x,4,3.55),(x,2.65,4.48),.10,.12)
        b.beam(side+'_canopy_longitudinal_knee_b',(x,4,3.55),(x,5.35,4.48),.10,.12)
    return b


def prepare_config(path):
    data=json.loads(Path(path).read_text()); OUT.mkdir(parents=True,exist_ok=True)
    # A muted, cool glazing color is derived from the supplied generated slate
    # surface. The small residual mottling suggests old glazing without painting
    # a false opaque window or frame across the open roof.
    source=data['glass'].get('base_source')
    if source:
        p=Path(source); p=p if p.is_absolute() else STATION/p
        if not p.is_file(): raise FileNotFoundError(p)
        grey=Image.open(p).convert('L').filter(ImageFilter.GaussianBlur(3.0))
        grey=ImageEnhance.Contrast(grey).enhance(.28)
        glass=ImageOps.colorize(grey,black='#93abb4',white='#e6f0f1')
        glass.save(OUT/'glass_basecolor.png')
        data['glass']['base']=str((OUT/'glass_basecolor.png').resolve())
        data['glass']['base_source']=str(p.resolve())
    for material in ('iron','ornament','glass'):
        info=data[material]
        for key in ('base','normal','orm'):
            p=Path(info[key]); p=p if p.is_absolute() else STATION/p
            if not p.is_file(): raise FileNotFoundError(p)
            info[key]=str(p.resolve())
        if len(info['uv'])!=4 or not all(0 <= f <= 1 for f in info['uv']): raise ValueError(f'Invalid UV: {material}')
    return data


def relative(path):
    try: return str(Path(path).resolve().relative_to(STATION))
    except ValueError: return str(Path(path).resolve())


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True,help='JSON texture paths and UV rectangles')
    args=ap.parse_args(); config=prepare_config(args.config)
    manifest={'units':'meters','authoring_axes':{'X':'right','Y':'depth toward rear','Z':'up'},
              'gltf_root_rotation_quaternion_xyzw':[-math.sqrt(.5),0,0,math.sqrt(.5)],
              'front_direction':'-Y in authoring space','texture_regions':{},'modules':{}}
    for k,v in config.items():
        manifest['texture_regions'][k]={**{z:relative(v[z]) for z in ('base','normal','orm')},**({'base_source':relative(v['base_source'])} if 'base_source' in v else {}),'uv':v['uv']}
    builders=[build_shed(config),build_front(config),build_canopy(config)]
    design={
        'shed_bay':{'clear_span':28,'eaves_height':11,'roof_crown':22,'depth':8},
        'front_arch':{'clear_span':28,'eaves_height':11,'roof_crown':22},
        'platform_canopy_bay':{'width':6,'depth':8,'height':5},
    }
    repeats={'shed_bay':[0,8,0],'front_arch':None,'platform_canopy_bay':[0,8,0]}
    notes={'shed_bay':'Roof covers Y=0..8; main rib and columns at the far seam Y=8. Add front_arch at Y=0 for the initial support.',
           'front_arch':'Place at station front Y=0; open arched frame, with decorative crown details rising above roof crown.',
           'platform_canopy_bay':'Roof covers Y=0..8, columns at Y=4; repeat along +Y. Ground base Z=0; place on top of platform.'}
    for b in builders:
        lo,hi,tris,unique=b.bounds_and_count(); name=b.name; stats=b.export(OUT/(name+'.glb'))
        manifest['modules'][name]={'file':name+'.glb','design_dimensions_m':design[name],
          'authored_bounds_m':{'min':lo.round(4).tolist(),'max':hi.round(4).tolist()},
          'triangles_instanced':tris,'triangles_unique_meshes':unique,'repeat_pitch_m':repeats[name],
          'mesh_nodes':len(b.nodes),'export':stats,'placement':notes[name]}
        print(f'{name}: {tris} rendered triangles; {unique} unique mesh triangles; bounds {lo.round(3)} to {hi.round(3)}')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__': main()
