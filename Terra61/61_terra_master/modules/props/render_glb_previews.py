#!/usr/bin/env python3
"""Orthographic CPU rasterizer; imports the exported GLB and its embedded textures."""
from pathlib import Path
import numpy as np
from PIL import Image
import trimesh, sys, math
ROOT=Path(__file__).resolve().parent
scene=None

def normalized(a):
    a=np.asarray(a,dtype=float);return a/np.linalg.norm(a)

def render(camera,target,out,w=1500,h=1000):
    camera=np.array(camera,dtype=float); target=np.array(target,dtype=float)
    forward=normalized(target-camera); right=normalized(np.cross(forward,[0,1,0])); up=normalized(np.cross(right,forward))
    allv=np.concatenate([np.asarray(g.vertices) for g in scene.geometry.values()]);rel=allv-target
    xx=rel@right; yy=rel@up
    half=max((xx.max()-xx.min())/(w*.84),(yy.max()-yy.min())/(h*.80))
    scale=1/half
    centerx=(xx.max()+xx.min())*.5; centery=(yy.max()+yy.min())*.5
    yybg=np.linspace(0,1,h)[:,None,None]
    bg=np.array([207,215,214])[None,None,:]*(1-yybg)+np.array([230,226,215])[None,None,:]*yybg
    color=np.broadcast_to(bg,(h,w,3)).copy().astype(np.uint8)
    depth=np.full((h,w),np.inf,dtype=np.float32)
    sun=normalized([-0.32,.83,-.46]);fill=normalized([.8,.45,-.3])
    for name,mesh in scene.geometry.items():
        pos=np.asarray(mesh.vertices);rel=pos-target
        xyz=np.column_stack(((rel@right-centerx)*scale+w*.5,h*.5-(rel@up-centery)*scale,(pos-camera)@forward))
        tex=np.array(mesh.visual.material.baseColorTexture.convert('RGB'))
        uv=np.asarray(mesh.visual.uv)
        th,tw=tex.shape[:2]
        for ids in np.asarray(mesh.faces):
            p=xyz[ids]; minx=max(0,int(math.floor(p[:,0].min())));maxx=min(w-1,int(math.ceil(p[:,0].max())))
            miny=max(0,int(math.floor(p[:,1].min())));maxy=min(h-1,int(math.ceil(p[:,1].max())))
            if minx>maxx or miny>maxy:continue
            x0,y0=p[0,:2];x1,y1=p[1,:2];x2,y2=p[2,:2]
            den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
            if abs(den)<1e-8:continue
            gy,gx=np.mgrid[miny:maxy+1,minx:maxx+1];gx=gx+.5;gy=gy+.5
            a=((y1-y2)*(gx-x2)+(x2-x1)*(gy-y2))/den
            b=((y2-y0)*(gx-x2)+(x0-x2)*(gy-y2))/den
            c=1-a-b
            z=a*p[0,2]+b*p[1,2]+c*p[2,2]
            section=depth[miny:maxy+1,minx:maxx+1]
            mask=(a>=-1e-6)&(b>=-1e-6)&(c>=-1e-6)&(z<section)
            if not mask.any():continue
            verts=pos[ids]
            normal=np.cross(verts[1]-verts[0],verts[2]-verts[0]);norm=np.linalg.norm(normal)
            if norm<1e-10:continue
            normal/=norm
            if np.dot(normal,forward)>0:normal=-normal
            light=(1.08 if name.endswith('glow') else .64+.28*max(0,float(normal@sun))+.12*max(0,float(normal@fill)))
            pu=a*uv[ids[0],0]+b*uv[ids[1],0]+c*uv[ids[2],0]
            pv=a*uv[ids[0],1]+b*uv[ids[1],1]+c*uv[ids[2],1]
            ix=(np.mod(pu[mask],1.0)*(tw-1)).astype(int)
            iy=(np.mod(1.0-pv[mask],1.0)*(th-1)).astype(int)
            sampled=np.clip(tex[iy,ix].astype(float)*light,0,255).astype(np.uint8)
            pixels=color[miny:maxy+1,minx:maxx+1];pixels[mask]=sampled;section[mask]=z[mask]
    Image.fromarray(color).save(out)
    print('rendered',out,flush=True)


for asset in ['station_lamp','station_bench','luggage_trolley','wall_clock','facade_canopy']:
    scene=trimesh.load(ROOT/(asset+'.glb'),force='scene',process=False)
    low,high=scene.bounds; target=(low+high)*.5; span=float(np.max(high-low))
    direction=np.array([.75,.38,-1.8]) if asset=='facade_canopy' else np.array([1.2,.8,-2.6])
    camera=target+direction*span*2
    render(camera,target,ROOT/('preview_'+asset+'.png'),w=1500 if asset=='facade_canopy' else 1100,h=700 if asset=='facade_canopy' else 900)

# Both reimported GLBs share the origin, documenting the canopy/building fit.
scene=trimesh.Scene()
for prefix,path in [('facade_',ROOT.parent/'facade'/'station_facade.glb'),('canopy_',ROOT/'facade_canopy.glb')]:
    if not path.exists():continue
    part=trimesh.load(path,force='scene',process=False)
    for name,mesh in part.geometry.items():scene.add_geometry(mesh,geom_name=prefix+name,node_name=prefix+name)
render([23,15,-29],[0,5.6,3.0],ROOT/'preview_facade_and_canopy.png',w=1500,h=1000)
