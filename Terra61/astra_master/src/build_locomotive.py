#!/usr/bin/env python3
"""Build a textured steam locomotive and separate coal tender as GLB.

X is across the vehicle, Y points to the rear, Z is up. Both modules start
at Y=0 and touch the ground at Z=0. Place their root at rail height 0.22 m.
The infrastructure builder provides the shared GLB/material exporter.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
import build_infrastructure as glb

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'modules'/'locomotive'
TEX=ROOT/'textures'
GAUGE=1.435

# Physical repeats for ordinary metal, but wheel/cab artwork uses explicit charts.
glb.MATERIALS.update({
 'boiler': {'image':'boiler','uv_m':(4.2,2.0),'roughness':.83,'metallic':.75},
 'dark_metal':{'image':'rail','uv_m':(1.5,1.5),'roughness':.72,'metallic':.65,'tint':(.65,.72,.8,1)},
 'loco_iron':{'image':'iron','uv_m':(1.5,1.5),'roughness':.78,'metallic':.65},
 'lamp_amber':{'image':'brass','uv_m':(1,1),'roughness':.48,'metallic':0,'tint':(1,.9,.48,1)},
 'wheel_face':{'image':'wheel','uv_m':(1,1),'roughness':.68,'metallic':.75},
 'cab_number':{'image':'cab','uv_m':(1,1),'roughness':.82,'metallic':.55},
 'brass':{'image':'brass','uv_m':(1,1),'roughness':.65,'metallic':.85},
 'red_paint':{'image':'carriage_wood','uv_m':(2.0,1.0),'roughness':.75,'metallic':.25},
 'coal':{'image':'ballast','uv_m':(.42,.42),'roughness':.96,'metallic':0,'tint':(.28,.28,.28,1)},
})


class Part(glb.Part):
    def chart(self, material, verts, uvs):
        """Add a convex face with explicit UV coordinates and flat normal."""
        verts=np.asarray(verts,dtype=float); uvs=np.asarray(uvs,dtype=float)
        normal=np.cross(verts[1]-verts[0],verts[2]-verts[0]); size=np.linalg.norm(normal)
        if size<1e-12: raise ValueError(f'Degenerate face in {self.name}')
        normal/=size
        s=self.sections[material]; start=len(s['p'])
        s['p'].extend(verts.tolist()); s['n'].extend([normal.tolist()]*len(verts)); s['uv'].extend(uvs.tolist())
        for i in range(1,len(verts)-1): s['idx'].extend((start,start+i,start+i+1))


def box(part, mat, b): glb.box(part,mat,b)


def cylinder_y(part, material, x, z, radius, y0, y1, n=24, caps=True, repeat=1.0):
    """Cylinder longitudinal to the track; explicit continuous cylindrical UV."""
    for i in range(n):
        a=2*math.pi*i/n; b=2*math.pi*(i+1)/n
        c0=(x+radius*math.cos(a),z+radius*math.sin(a)); c1=(x+radius*math.cos(b),z+radius*math.sin(b))
        verts=[(c0[0],y0,c0[1]),(c0[0],y1,c0[1]),(c1[0],y1,c1[1]),(c1[0],y0,c1[1])]
        u0=y0/repeat; u1=y1/repeat; v0=i/n; v1=(i+1)/n
        part.chart(material,verts,[(u0,v0),(u1,v0),(u1,v1),(u0,v1)])
        if caps:
            uv0=(.5+.5*math.cos(a),.5-.5*math.sin(a)); uv1=(.5+.5*math.cos(b),.5-.5*math.sin(b))
            part.chart(material,[(x,y0,z),(c0[0],y0,c0[1]),(c1[0],y0,c1[1])],[(.5,.5),uv0,uv1])
            part.chart(material,[(x,y1,z),(c1[0],y1,c1[1]),(c0[0],y1,c0[1])],[(.5,.5),uv1,uv0])


def cylinder_z(part, material, x, y, radius, z0, z1, n=16, caps=True):
    for i in range(n):
        a=2*math.pi*i/n; b=2*math.pi*(i+1)/n
        p0=(x+radius*math.cos(a),y+radius*math.sin(a)); p1=(x+radius*math.cos(b),y+radius*math.sin(b))
        part.chart(material,[(p0[0],p0[1],z0),(p1[0],p1[1],z0),(p1[0],p1[1],z1),(p0[0],p0[1],z1)],
                   [(i/n,0),((i+1)/n,0),((i+1)/n,1),(i/n,1)])
        if caps:
            uv0=(.5+.5*math.cos(a),.5+.5*math.sin(a)); uv1=(.5+.5*math.cos(b),.5+.5*math.sin(b))
            part.chart(material,[(x,y,z0),(p1[0],p1[1],z0),(p0[0],p0[1],z0)],[(.5,.5),uv1,uv0])
            part.chart(material,[(x,y,z1),(p0[0],p0[1],z1),(p1[0],p1[1],z1)],[(.5,.5),uv0,uv1])


def wheel(name, x, y, radius, depth=.18, n=24):
    part=Part(name); z=radius; x0=x-depth/2; x1=x+depth/2
    for i in range(n):
        a=2*math.pi*i/n; b=2*math.pi*(i+1)/n
        p0=(y+radius*math.cos(a),z+radius*math.sin(a)); p1=(y+radius*math.cos(b),z+radius*math.sin(b))
        # Winding makes the visible edge point radially outwards.
        part.chart('dark_metal',[(x1,p0[0],p0[1]),(x0,p0[0],p0[1]),(x0,p1[0],p1[1]),(x1,p1[0],p1[1])],
                   [(0,i/n),(1,i/n),(1,(i+1)/n),(0,(i+1)/n)])
        uv0=(.5+.5*math.cos(a),.5-.5*math.sin(a)); uv1=(.5+.5*math.cos(b),.5-.5*math.sin(b))
        # The wheel artwork is a complete chart on each disk, not repeated wedges.
        part.chart('wheel_face',[(x0,y,z),(x0,p1[0],p1[1]),(x0,p0[0],p0[1])],[(.5,.5),uv1,uv0])
        part.chart('wheel_face',[(x1,y,z),(x1,p0[0],p0[1]),(x1,p1[0],p1[1])],[(.5,.5),uv0,uv1])
    return part


def cylinder_x(part,material,x0,x1,y,z,r,n=12):
    for i in range(n):
        a=2*math.pi*i/n; b=2*math.pi*(i+1)/n
        p0=(y+r*math.cos(a),z+r*math.sin(a)); p1=(y+r*math.cos(b),z+r*math.sin(b))
        part.chart(material,[(x1,*p0),(x0,*p0),(x0,*p1),(x1,*p1)],[(0,i/n),(1,i/n),(1,(i+1)/n),(0,(i+1)/n)])
        uv0=(.5+.5*math.cos(a),.5+.5*math.sin(a)); uv1=(.5+.5*math.cos(b),.5+.5*math.sin(b))
        part.chart(material,[(x0,y,z),(x0,*p1),(x0,*p0)],[(.5,.5),uv1,uv0])
        part.chart(material,[(x1,y,z),(x1,*p0),(x1,*p1)],[(.5,.5),uv0,uv1])


def front_ring(part,mat,x,z,inner,outer,y,n=24):
    for i in range(n):
        a=2*math.pi*i/n; b=2*math.pi*(i+1)/n
        def p(r,t): return (x+r*math.cos(t),y,z+r*math.sin(t))
        pts=[p(inner,a),p(outer,a),p(outer,b),p(inner,b)]
        part.chart(mat,pts,[((v[0]-x)/2+0.5,(v[2]-z)/2+0.5) for v in pts])


def rod(part, material, x0, x1, y0,z0,y1,z1,width):
    """A thin rectangular connecting rod running in the Y/Z plane."""
    dy=y1-y0; dz=z1-z0; size=math.hypot(dy,dz)
    py=-dz/size*width/2; pz=dy/size*width/2
    yz=[(y0-py,z0-pz),(y1-py,z1-pz),(y1+py,z1+pz),(y0+py,z0+pz)]
    # Ends x0 and x1 are CCW in YZ; outward normals are -X/+X.
    for x,order in ((x0,(3,2,1,0)),(x1,(0,1,2,3))):
        pts=[(x,*yz[i]) for i in order]
        part.polygon(material,pts,uv_axes=(1,2))
    for i in range(4):
        a=yz[i]; b=yz[(i+1)%4]
        pts=[(x0,*a),(x0,*b),(x1,*b),(x1,*a)]
        # Depending on the rod edge, project along its nonzero direction.
        axes=(0,1) if abs(a[0]-b[0])>abs(a[1]-b[1]) else (0,2)
        part.polygon(material,pts,uv_axes=axes)


def cab_number_panel(part,x,side):
    y0,y1=7.55,9.55; z0,z1=1.83,2.9
    def uv(y,z):
        u=(y-y0)/(y1-y0) if side=='R' else (y1-y)/(y1-y0)
        return (u,.25+.5*(z1-z)/(z1-z0))
    if side=='R': points=[(x,y0,z0),(x,y1,z0),(x,y1,z1),(x,y0,z1)]
    else: points=[(x,y1,z0),(x,y0,z0),(x,y0,z1),(x,y1,z1)]
    part.chart('cab_number',points,[uv(y,z) for _,y,z in points])


def roof(part):
    profile=[(-1.30,4.02),(-1.15,4.15),(-.6,4.23),(0,4.26),(.6,4.23),(1.15,4.15),(1.30,4.02)]
    for (x0,z0),(x1,z1) in zip(profile,profile[1:]):
        part.polygon('loco_iron',[(x0,7.3,z0),(x1,7.3,z1),(x1,9.8,z1),(x0,9.8,z0)],uv_axes=(0,1))


def locomotive():
    parts=[]
    p=Part('locomotive_frame_and_footplate')
    box(p,'loco_iron',[(-1.4,.3,1.38),(1.4,9.8,1.57)])
    box(p,'loco_iron',[(-1.18,9.8,.65),(1.18,10,1.5)])
    parts.append(p)
    # A narrow structural centre leaves the driving wheels and rods visible.
    p=Part('inner_chassis'); box(p,'loco_iron',[(-.42,.45,.55),(.42,9.65,1.38)]); parts.append(p)
    p=Part('front_buffer_beam'); box(p,'red_paint',[(-1.4,.22,1.0),(1.4,.45,1.34)]); parts.append(p)
    p=Part('front_buffers')
    for x in (-.85,.85):
        cylinder_y(p,'loco_iron',x,1.17,.20,0,.1,n=16)
        cylinder_y(p,'brass',x,1.17,.09,.10,.24,n=12)
    parts.append(p)
    p=Part('round_boiler'); cylinder_y(p,'boiler',0,2.6,1.05,.72,7.4,n=28,repeat=4.2); parts.append(p)
    p=Part('smokebox_and_front_disk')
    cylinder_y(p,'loco_iron',0,2.6,1.07,.34,.78,n=28,repeat=2.0)
    cylinder_y(p,'boiler',0,2.6,.82,.28,.35,n=28,repeat=2.0)
    front_ring(p,'brass',0,2.6,.84,.88,.277,n=28)
    cylinder_y(p,'brass',0,2.6,.105,.20,.28,n=12)
    parts.append(p)
    p=Part('front_headlamp')
    box(p,'loco_iron',[(-.06,.26,3.56),(.06,.40,3.69)])
    cylinder_y(p,'loco_iron',0,3.78,.145,.12,.35,n=12)
    cylinder_y(p,'lamp_amber',0,3.78,.105,.105,.12,n=12)
    front_ring(p,'brass',0,3.78,.108,.145,.104,n=12)
    parts.append(p)
    p=Part('boiler_bands')
    for y in (1.5,3.0,4.6,6.2,7.15): cylinder_y(p,'brass',0,2.6,1.057,y,y+.035,n=28,caps=False,repeat=1.0)
    parts.append(p)
    p=Part('chimney')
    cylinder_z(p,'loco_iron',0,1.28,.24,3.58,4.42,n=18)
    cylinder_z(p,'brass',0,1.28,.30,4.42,4.5,n=18)
    parts.append(p)
    p=Part('steam_domes')
    cylinder_z(p,'loco_iron',0,4.0,.34,3.53,4.02,n=18)
    cylinder_z(p,'brass',0,4.0,.35,4.02,4.09,n=18)
    cylinder_z(p,'loco_iron',0,6.05,.24,3.57,3.98,n=16)
    cylinder_z(p,'brass',0,6.05,.25,3.98,4.06,n=16)
    parts.append(p)
    p=Part('boiler_side_pipes')
    for x in (-1.055,1.055): cylinder_y(p,'brass',x,2.32,.028,1.0,7.1,n=8)
    parts.append(p)
    p=Part('cab_lower_body')
    for x0,x1 in ((-1.22,-1.08),(1.08,1.22)): box(p,'loco_iron',[(x0,7.38,1.57),(x1,9.72,2.92)])
    box(p,'loco_iron',[(-1.1,9.57,1.57),(1.1,9.72,2.9)])
    parts.append(p)
    p=Part('cab_number_726')
    cab_number_panel(p,-1.221,'L'); cab_number_panel(p,1.221,'R'); parts.append(p)
    p=Part('cab_window_frames')
    for x0,x1 in ((-1.22,-1.08),(1.08,1.22)):
        for y0,y1,z0,z1 in ((7.38,7.56,2.9,4.02),(9.54,9.72,2.9,4.02),
                           (8.48,8.60,2.9,4.02),(7.56,9.54,2.9,3.04),(7.56,9.54,3.87,4.02)):
            box(p,'loco_iron',[(x0,y0,z0),(x1,y1,z1)])
    # Rear framing keeps windows open for a real view through the cab.
    for x0,x1,z0,z1 in ((-1.1,-.95,2.9,4.02),(.95,1.1,2.9,4.02),(-.10,.10,2.9,4.02),(-.95,.95,3.87,4.02)):
        box(p,'loco_iron',[(x0,9.58,z0),(x1,9.72,z1)])
    parts.append(p)
    p=Part('cab_roof'); roof(p); parts.append(p)
    driving_y=(3.15,5.10,7.05)
    for i,y in enumerate(driving_y,1):
        for side,x in (('L',-GAUGE/2),('R',GAUGE/2)):
            parts.append(wheel(f'driving_wheel_{side}_{i}',x,y,.96))
    for side,x in (('L',-GAUGE/2),('R',GAUGE/2)):
        parts.append(wheel(f'leading_wheel_{side}',x,1.18,.48))
    p=Part('driving_rod_assembly')
    for sign in (-1,1):
        x=sign*(GAUGE/2+.105)
        rod(p,'brass',x-.025,x+.025,driving_y[0],.96,driving_y[-1],.96,.10)
        rod(p,'dark_metal',x-.03,x+.03,1.65,1.23,driving_y[0],.96,.11)
        for y in driving_y:
            center=sign*(GAUGE/2+.14)
            cylinder_x(p,'brass',center-.025,center+.025,y,.96,.11,n=12)
    parts.append(p)
    return parts


def tender():
    parts=[]
    p=Part('tender_frame')
    box(p,'dark_metal',[(-1.4,.14,.95),(1.4,4.86,1.2)])
    box(p,'red_paint',[(-1.4,0,1.0),(1.4,.14,1.28)])
    box(p,'red_paint',[(-1.4,4.86,1.0),(1.4,5,1.28)])
    parts.append(p)
    p=Part('tender_coal_bunker')
    for x0,x1 in ((-1.22,-1.09),(1.09,1.22)):
        box(p,'boiler',[(x0,.4,1.2),(x1,4.6,3.15)])
    for y0,y1 in ((.4,.53),(4.47,4.6)):
        box(p,'boiler',[(-1.1,y0,1.2),(1.1,y1,3.15)])
    parts.append(p)
    p=Part('tender_red_border')
    for side in (-1,1):
        x=side*1.225; x0,x1=x-.012,x+.012
        for y0,y1,z0,z1 in ((.52,4.48,1.30,1.34),(.52,4.48,3.02,3.06),
                           (.52,.56,1.34,3.02),(4.44,4.48,1.34,3.02)):
            box(p,'red_paint',[(x0,y0,z0),(x1,y1,z1)])
    parts.append(p)
    p=Part('textured_coal_load')
    xs=(-1.08,0,1.08); ys=(.53,1.5,2.5,3.5,4.47)
    def z(x,y): return 3.14+.46*max(0,1-(x/1.08)**2)*max(0,1-((y-2.5)/1.97)**2)
    for i in range(len(xs)-1):
        for j in range(len(ys)-1):
            points=[(xs[i],ys[j],z(xs[i],ys[j])),(xs[i+1],ys[j],z(xs[i+1],ys[j])),
                    (xs[i+1],ys[j+1],z(xs[i+1],ys[j+1])),(xs[i],ys[j+1],z(xs[i],ys[j+1]))]
            p.polygon('coal',points[:3],uv_axes=(0,1)); p.polygon('coal',[points[0],points[2],points[3]],uv_axes=(0,1))
    parts.append(p)
    for i,y in enumerate((1.0,4.0),1):
        for side,x in (('L',-GAUGE/2),('R',GAUGE/2)):
            parts.append(wheel(f'tender_wheel_{side}_{i}',x,y,.54))
    p=Part('tender_buffers')
    for x in (-.85,.85):
        cylinder_y(p,'dark_metal',x,1.14,.18,0,.08,n=12)
        cylinder_y(p,'dark_metal',x,1.14,.18,4.92,5,n=12)
    parts.append(p)
    return parts


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--textures',type=Path,default=TEX); parser.add_argument('--out',type=Path,default=OUT)
    parser.add_argument('--only',choices=('locomotive','tender'),
                        help='Rebuild one module and update its existing manifest entry.')
    args=parser.parse_args()
    makers={'locomotive':locomotive,'tender':tender}
    if args.only:
        manifest_path=args.out/'manifest.json'
        if not manifest_path.is_file(): parser.error('--only requires an existing manifest')
        manifest=json.loads(manifest_path.read_text())
        entries={args.only:glb.export(args.only,makers[args.only](),args.textures,args.out)}
    else:
        entries={name:glb.export(name,maker(),args.textures,args.out) for name,maker in makers.items()}
    for entry in entries.values():
        for special in ('wheel_face','cab_number'):
            entry['texture_repeat_m'].pop(special,None)
        entry['explicit_uv_charts']={'wheel_face':'One complete wheel image per side disk.',
                                    **({'cab_number':'Central 50% of the image, mapped to the side panel.'}
                                       if 'cab_number' in entry['material_images'] else {})}
    if args.only:
        manifest['modules'].update(entries)
        manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(entries[args.only],indent=2))
        return
    manifest={'description':'Victorian steam locomotive and separate coal tender.',
              'author_axes':'X right, Y rearward, Z up; front Y=0 and wheel contact Z=0',
              'export_axes':'glTF Y-up with one -90 degree X root rotation',
              'wheel_center_gauge':GAUGE,'wheel_contact_z':0,'rail_placement_z':.22,
              'assembly':'Place the tender behind the locomotive at author Y approximately 10.1 m. Both roots are raised 0.22 m to touch the rail tops.',
              'materials_note':'Image textures, approximate normal maps and packed metallic/roughness maps are embedded; wheel spokes and cab number are image charts.',
              'modules':entries}
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__': main()
