#!/usr/bin/env python3
"""Render actual GLB meshes with UV textures via a small orthographic CPU rasterizer.
No external renderer, geometry reconstruction, or network access is needed.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageFilter
import trimesh

HERE=Path(__file__).resolve().parent

def norm(a):
    a=np.asarray(a,dtype=float); return a/np.linalg.norm(a)

def render(name, eye, target, width, height, fieldwidth=None):
    scene=trimesh.load(HERE/'steam_locomotive.glb', force='scene', process=False)
    # Decode the real scene with node transforms, UVs and embedded base colors.
    meshes=[]
    for node in scene.graph.nodes_geometry:
        transform,geom_name=scene.graph[node]; geo=scene.geometry[geom_name]
        verts=trimesh.transform_points(geo.vertices,transform)
        mat=geo.visual.material; tex=getattr(mat,'baseColorTexture',None)
        tex=np.asarray(tex.convert('RGB'),dtype=np.float32) if tex is not None else None
        fac=getattr(mat,'baseColorFactor',None)
        fac=np.asarray(fac[:3],dtype=np.float32)/255 if fac is not None else np.ones(3,dtype=np.float32)
        uv=geo.visual.uv if getattr(geo.visual,'uv',None) is not None else np.zeros((len(verts),2))
        meshes.append((geom_name,verts,geo.faces,uv,tex,fac))
    eye=np.array(eye,dtype=float); target=np.array(target,dtype=float)
    forward=norm(target-eye); right=norm(np.cross(forward,[0.,1.,0.])); up=norm(np.cross(right,forward))
    allpoints=np.vstack([m[1] for m in meshes]); q=allpoints-target
    projx=q@right; projy=q@up
    if fieldwidth is None:
        xhalf=max(abs(projx.min()),abs(projx.max()))*1.12
        yhalf=max(abs(projy.min()),abs(projy.max()))*1.18
        scale=min(width/(2*xhalf),height/(2*yhalf))
    else: scale=width/fieldwidth
    yy=np.linspace(0,1,height)[:,None]
    col0=np.array([228,225,219]); col1=np.array([193,192,189])
    bg=(col0[None,None,:]*(1-yy[:,:,None])+col1[None,None,:]*yy[:,:,None])
    color=np.broadcast_to(bg,(height,width,3)).copy().astype(np.uint8)
    depth=np.full((height,width),np.inf,np.float32)
    light=norm([-4,10,-6]); light2=norm([6,4,8]); rendered=0
    for name_,verts,faces,uv,tex,fac in meshes:
        diff=verts-target
        screen=np.empty((len(verts),3),dtype=float)
        screen[:,0]=width*.5+(diff@right)*scale
        screen[:,1]=height*.53-(diff@up)*scale
        screen[:,2]=(verts-eye)@forward
        for face in faces:
            p=screen[face]; world=verts[face]
            normal=np.cross(world[1]-world[0],world[2]-world[0]); length=np.linalg.norm(normal)
            if length<1e-12: continue
            normal/=length
            if np.dot(normal,eye-world.mean(axis=0))<=0: continue
            xmin=max(0,int(math.floor(p[:,0].min()))); xmax=min(width-1,int(math.ceil(p[:,0].max())))
            ymin=max(0,int(math.floor(p[:,1].min()))); ymax=min(height-1,int(math.ceil(p[:,1].max())))
            if xmin>xmax or ymin>ymax: continue
            x0,y0=p[0,:2]; x1,y1=p[1,:2]; x2,y2=p[2,:2]
            denominator=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
            if abs(denominator)<1e-9: continue
            ys,xs=np.mgrid[ymin:ymax+1,xmin:xmax+1]; xs=xs+.5; ys=ys+.5
            a=((y1-y2)*(xs-x2)+(x2-x1)*(ys-y2))/denominator
            b=((y2-y0)*(xs-x2)+(x0-x2)*(ys-y2))/denominator
            c=1-a-b
            inside=(a>=-1e-7)&(b>=-1e-7)&(c>=-1e-7)
            d=a*p[0,2]+b*p[1,2]+c*p[2,2]
            sl=depth[ymin:ymax+1,xmin:xmax+1]
            inside &= d<sl
            if not inside.any(): continue
            sl[inside]=d[inside]
            if tex is None:
                rgb=np.broadcast_to(fac*255,(int(inside.sum()),3)).copy()
            else:
                uvface=uv[face]
                u=(a*uvface[0,0]+b*uvface[1,0]+c*uvface[2,0])[inside]
                v=(a*uvface[0,1]+b*uvface[1,1]+c*uvface[2,1])[inside]
                ti=(np.floor((u%1)*tex.shape[1]).astype(int)).clip(0,tex.shape[1]-1)
                tj=(np.floor(((1-v)%1)*tex.shape[0]).astype(int)).clip(0,tex.shape[0]-1)
                rgb=tex[tj,ti]*fac
            intensity=.62+.30*max(0,float(np.dot(normal,light)))+.12*max(0,float(np.dot(normal,light2)))
            if 'Polished' in name_: intensity=min(1.13,intensity+0.17)
            dst=color[ymin:ymax+1,xmin:xmax+1]
            dst[inside]=np.clip(rgb*intensity,0,255).astype(np.uint8)
            rendered+=1
    Image.fromarray(color).save(HERE/name)
    print(name,'rasterized_triangles',rendered,'image_size',width,height,flush=True)

if __name__=='__main__':
    render('preview_three_quarter.png',[17,9,-15],[0,2.0,6.2],2000,1250)
    render('preview_side.png',[24,7,6.2],[0,2.0,6.2],2000,1100)
    render('preview_front.png',[7,5,-15],[0,2.0,3.6],1500,1200)
