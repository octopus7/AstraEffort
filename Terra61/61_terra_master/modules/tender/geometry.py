import math
import numpy as np
import trimesh

def unit(v):
    a=np.asarray(v,dtype=float);return a/np.linalg.norm(a)

class Builder:
    def __init__(self):self.v=[];self.f=[];self.uv=[]
    def quad(self,p,uv=None):
        if uv is None:uv=[(0,0),(0,1),(1,1),(1,0)]
        n=len(self.v);self.v.extend(p);self.uv.extend(uv);self.f.extend([(n,n+1,n+2),(n,n+2,n+3)])
    def tri(self,p,uv=None):
        if uv is None:uv=[(0,0)]*3
        n=len(self.v);self.v.extend(p);self.uv.extend(uv);self.f.append((n,n+1,n+2))
    def mesh(self,material):
        m=trimesh.Trimesh(vertices=np.asarray(self.v,dtype=np.float32),faces=np.asarray(self.f,dtype=np.int64),process=False)
        m.visual=trimesh.visual.texture.TextureVisuals(uv=np.asarray(self.uv,dtype=np.float32),material=material)
        return m


def box(b,x0,x1,y0,y1,z0,z1):
    # Faces point outward. Spatial UVs are continuous at sensible scale.
    faces=[([(x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(x1,y1,z0)],lambda x,y,z:(x/2,z/4)),
      ([(x1,y0,z0),(x1,y0,z1),(x0,y0,z1),(x0,y0,z0)],lambda x,y,z:(x/2,z/4)),
      ([(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0)],lambda x,y,z:(z/4,y/2)),
      ([(x1,y0,z1),(x1,y0,z0),(x1,y1,z0),(x1,y1,z1)],lambda x,y,z:(z/4,y/2)),
      ([(x0,y0,z0),(x0,y1,z0),(x1,y1,z0),(x1,y0,z0)],lambda x,y,z:(x/2,y/2)),
      ([(x1,y0,z1),(x1,y1,z1),(x0,y1,z1),(x0,y0,z1)],lambda x,y,z:(x/2,y/2))]
    for p,fn in faces:b.quad(p,[fn(*v) for v in p])


def frame(axis):
    axis=unit(axis); ref=np.array([0.,1.,0.]) if abs(axis[1])<.85 else np.array([1.,0.,0.])
    u=unit(ref-axis*np.dot(ref,axis));v=np.cross(axis,u)
    return axis,u,v


def cylinder(b,p0,p1,r,segments=16,caps=True,uvscale=1):
    p0=np.asarray(p0,float);p1=np.asarray(p1,float);axis,u,v=frame(p1-p0)
    ring=[]
    for i in range(segments+1):
        a=2*math.pi*i/segments; ring.append(math.cos(a)*u+math.sin(a)*v)
    for i in range(segments):
        a,beta=ring[i],ring[i+1]
        b.quad([p0+r*a,p0+r*beta,p1+r*beta,p1+r*a],[(i/segments,0),((i+1)/segments,0),((i+1)/segments,uvscale),(i/segments,uvscale)])
        if caps:
            ua=(.5+.5*math.cos(2*math.pi*i/segments),.5+.5*math.sin(2*math.pi*i/segments));ub=(.5+.5*math.cos(2*math.pi*(i+1)/segments),.5+.5*math.sin(2*math.pi*(i+1)/segments))
            b.tri([p0,p0+r*beta,p0+r*a],[(.5,.5),ub,ua]);b.tri([p1,p1+r*a,p1+r*beta],[(.5,.5),ua,ub])


def annulus(b,p0,p1,outer,inner,segments=32):
    p0=np.asarray(p0,float);p1=np.asarray(p1,float);axis,u,v=frame(p1-p0)
    for i in range(segments):
        a=2*math.pi*i/segments;c=2*math.pi*(i+1)/segments
        A=math.cos(a)*u+math.sin(a)*v;C=math.cos(c)*u+math.sin(c)*v
        # Outer wall, inner wall, and annular end faces.
        b.quad([p0+outer*A,p0+outer*C,p1+outer*C,p1+outer*A])
        b.quad([p0+inner*C,p0+inner*A,p1+inner*A,p1+inner*C])
        b.quad([p0+outer*C,p0+outer*A,p0+inner*A,p0+inner*C])
        b.quad([p1+outer*A,p1+outer*C,p1+inner*C,p1+inner*A])


def beam(b,p0,p1,width,depth):
    p0=np.asarray(p0,float);p1=np.asarray(p1,float);axis,u,v=frame(p1-p0)
    ring=[width*u/2+depth*v/2,-width*u/2+depth*v/2,-width*u/2-depth*v/2,width*u/2-depth*v/2]
    for i in range(4):
        a=ring[i]; c=ring[(i+1)%4];b.quad([p0+a,p0+c,p1+c,p1+a])
    b.quad([p0+ring[3],p0+ring[2],p0+ring[1],p0+ring[0]])
    b.quad([p1+ring[0],p1+ring[1],p1+ring[2],p1+ring[3]])


def disc(b,center,normal,r,segments=40):
    c=np.asarray(center,float);axis,u,v=frame(normal)
    for i in range(segments):
        a=2*math.pi*i/segments;z=2*math.pi*(i+1)/segments
        A=math.cos(a)*u+math.sin(a)*v;Z=math.cos(z)*u+math.sin(z)*v
        b.tri([c,c+r*A,c+r*Z],[(.5,.5),(.5+.5*math.cos(a),.5+.5*math.sin(a)),(.5+.5*math.cos(z),.5+.5*math.sin(z))])


