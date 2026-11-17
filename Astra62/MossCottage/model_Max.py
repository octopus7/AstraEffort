"""Build the moss-roof cottage study in a blank Blender scene."""

import bpy
import math
import random
import sys
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import normal


OUT = Path(__file__).resolve().parent
DRAFT = "--draft" in sys.argv
rng = random.Random(815720)
TAU = math.tau
V = Vector
Z = V((0, 0, 1))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "Moss Cottage | Max"
scene.unit_settings.system = "METRIC"
bpy.context.preferences.filepaths.save_version = 0


def collection(name, parent):
    coll = bpy.data.collections.new(name)
    parent.children.link(coll)
    return coll


house = collection("Moss Cottage | Max", scene.collection)
walls = collection("Walls and hand-hewn frame", house)
roofs = collection("Roofs", house)
entry = collection("Porch and front door", house)
joinery = collection("Windows and shutters", house)
hearth = collection("Chimney and rainwater goods", house)
garden = collection("Garden", house)
studio = collection("Presentation", scene.collection)
root = bpy.data.objects.new("MossCottage_Max", None)
house.objects.link(root)
root.empty_display_size = .4


def rgba(value):
    rgb = [int(value[k:k+2], 16)/255 for k in (0, 2, 4)]
    return (*[(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4) for v in rgb], 1)


def paint(name, colors, scale=3.0, grain=False, moss=False, relief=.022, metal=0.0, rough=.81, glow=None, slate_grain=False):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = rgba(colors[1])
    mat.use_nodes = True
    tree = mat.node_tree
    nodes, link = tree.nodes, tree.links.new
    shader = nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = rough
    shader.inputs["Metallic"].default_value = metal
    position = nodes.new("ShaderNodeNewGeometry").outputs["Position"]

    def noise(coords, frequency, detail=3, distortion=.16):
        n = nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = frequency
        n.inputs["Detail"].default_value = detail
        n.inputs["Distortion"].default_value = distortion
        link(coords, n.inputs["Vector"])
        return n.outputs["Fac"]

    def ramp(socket, stops):
        node = nodes.new("ShaderNodeValToRGB")
        items = node.color_ramp.elements
        for i, (x, color) in enumerate(stops):
            el = items[i] if i < 2 else items.new(x)
            el.position = x
            el.color = rgba(color)
        link(socket, node.inputs["Fac"])
        return node.outputs["Color"]

    coords = position
    if grain:
        uv = nodes.new("ShaderNodeTexCoord").outputs["UV"]
        stretch = nodes.new("ShaderNodeVectorMath")
        stretch.operation = "MULTIPLY"
        stretch.inputs[1].default_value = (21.0, 1.2, 1)
        link(uv, stretch.inputs[0])
        coords = stretch.outputs[0]
    cloud = noise(coords, scale, 3.5, .62 if grain else .20)
    result = ramp(cloud, list(zip((.20, .52, .80), colors)))
    if moss:
        islands = noise(position, 1.78, 4.4, .34)
        coverage = nodes.new("ShaderNodeMapRange")
        coverage.clamp = True
        coverage.inputs["From Min"].default_value = .52
        coverage.inputs["From Max"].default_value = .675
        link(islands, coverage.inputs["Value"])
        lichen = ramp(noise(position, 9.5), [(.2, "586722"), (.50, "818631"), (.78, "A09843")])
        mix = nodes.new("ShaderNodeMixRGB")
        link(coverage.outputs[0], mix.inputs[0])
        link(result, mix.inputs[1])
        link(lichen, mix.inputs[2])
        result = mix.outputs[0]
    if slate_grain:
        along = nodes.new("ShaderNodeVectorMath")
        along.operation = "MULTIPLY"
        along.inputs[1].default_value = (17,2.1,1)
        link(nodes.new("ShaderNodeTexCoord").outputs["UV"], along.inputs[0])
        fissures = noise(along.outputs[0],1.35,2.3,.75)
        striae = ramp(fissures,[(.22,"7E795F"),(.45,"E6E3C7"),(.75,"FCF7DC")])
        layer = nodes.new("ShaderNodeMixRGB")
        layer.blend_type="MULTIPLY"
        layer.inputs[0].default_value=.54
        link(result,layer.inputs[1])
        link(striae,layer.inputs[2])
        result=layer.outputs[0]
    link(result, shader.inputs["Base Color"])
    if relief:
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Distance"].default_value = relief
        bump.inputs["Strength"].default_value = .23
        link(noise(coords, scale * (2.0 if grain else 4.2)), bump.inputs["Height"])
        link(bump.outputs["Normal"], shader.inputs["Normal"])
    if glow:
        shader.inputs["Emission Color"].default_value = rgba(glow)
        shader.inputs["Emission Strength"].default_value = 2.5
    return mat


lime = paint("Limewash | warm chalk", ("BA976C","E5CBA5","F1E0B6"), 2.1)
lime_patch = paint("Limewash | ochre repairs", ("AF8D69","D8BB92","EAD4A7"), 2.6)
timber = paint("Oak | honey heartwood", ("63391F","9D6031","C48C4B"), 1.5, grain=True)
beamwood = paint("Oak | smoked timbers", ("412C22","805232","A77547"), 1.30, grain=True)
lightwood = paint("Oak | worn edge", ("80512C","BE884D","D8A469"), 1.5, grain=True)
doorwood = paint("Oak | oiled door", ("57311C","895333","AE7543"), 1.75, grain=True)
shadow = paint("Deep shadow", ("241C17","342A21","4F4236"), 3)
mortar = paint("Warm recessed mortar", ("786C58","958675","A89B86"), 5)
stones = [paint("Fieldstone | "+name, palette, 4.2, relief=.033) for name,palette in [
    ("sand",("978466","C3B192","D7C9AC")), ("ochre",("8B7357","B29A78","CAAE89")),
    ("ash",("838477","A8A79B","BFBAA5")), ("umber",("806D59","9E8B74","B19B7B")),
    ("honey",("9A8260","C2AA85","D3BF97"))]]
slates = [paint("Roof slate | "+name, palette, 3.6, moss=True, relief=.030,slate_grain=True) for name,palette in [
    ("olive",("4A502F","717636","90924E")), ("thyme",("454B2F","636C3D","838A52")),
    ("sage",("505638","72794A","8E935D")), ("smoke",("494932","616347","828365")),
    ("gold",("5C562C","7B793B","9D9756")), ("deep green",("3F4A32","5C693A","7B8550"))]]
caps = paint("Ridge half-rounds | lichen stone",("5E613C","8C8B55","ACA66C"),3,moss=True)
redclays = [paint("Fired clay | "+n,c,4.8) for n,c in [
    ("umber",("75452E","A7633F","C17F50")),("honey red",("925337","C47848","DE945C")),
    ("sienna",("8C482F","B56A41","CC8051"))]]
glass = [paint("Glass | "+n,p,2.8,rough=.28,metal=.12,relief=.004) for n,p in [
    ("pine",("1F3434","395351","5E7566")),("evening",("2A3F40","455B54","728372")),
    ("honey reflection",("343D35","51584B","837F65"))]]
iron = paint("Iron | brown-black",("272822","3E3A30","645947"),5,metal=.48,rough=.54)
copper = paint("Rainwater pipe | aged bronze",("544737","76684E","8D8462"),6,metal=.52,rough=.53)
amber = paint("Lamp | amber glass",("E19339","F4BD64","FFE2A5"),2,rough=.31,glow="FFA846")
turf = paint("Meadow | grassy earth",("66683F","88904B","A0A05F"),2.45,relief=.045)
soil = paint("Garden | humus",("61503E","80674B","A08761"),4)
leaves = [paint("Foliage | "+n,c,6,relief=.007) for n,c in [
    ("fern",("3F572D","62793B","80914D")),("apple",("5C702D","819548","A3B059")),
    ("ivy",("344C33","4D6842","688257")),("yellowgreen",("737830","989D45","B5B65D"))]]
petal = paint("Blossoms | clotted cream",("D8BD84","F1DEAF","FFF0CC"),5,relief=.004)
petal_light = paint("Blossoms | white hydrangea",("C7C7A1","E6E8C7","F4F1DB"),5,relief=.003)
pollen = paint("Blossoms | ochre pollen",("B87D29","E3AA45","FBC75F"),6)


class Part:
    """One independently editable mesh, with material slots for its pieces."""
    def __init__(self, name, coll):
        self.name, self.coll = name, coll
        self.verts, self.faces, self.indices, self.uvs = [], [], [], []
        self.materials = []

    def vertices(self, points):
        start = len(self.verts)
        self.verts.extend(tuple(p) for p in points)
        return list(range(start, len(self.verts)))

    def face(self, ids, mat, uv=None):
        if mat not in self.materials:
            self.materials.append(mat)
        self.indices.append(self.materials.index(mat))
        self.faces.append(tuple(ids))
        self.uvs.append(uv)

    def rings(self, sections, mat, closed=True, cap=True, grain=False, uv_axes=None):
        rings = [[V(p) for p in ring] for ring in sections]
        centers = [sum(r, V((0,0,0))) / len(r) for r in rings]
        if closed and normal(rings[0]).dot(centers[-1]-centers[0]) < 0:
            rings = [r[::-1] for r in rings]
        ids = [self.vertices(r) for r in rings]
        count = len(ids[0])
        def mapped(pts):
            return [(p.dot(uv_axes[0]),p.dot(uv_axes[1])) for p in pts] if uv_axes else None
        if cap and closed:
            self.face(ids[0][::-1], mat,mapped(rings[0][::-1]))
            self.face(ids[-1], mat,mapped(rings[-1]))
        tex_u = rng.uniform(0, 11) if grain else 0
        tex_v = rng.uniform(0, 11) if grain else 0
        for layer in range(len(ids)-1):
            step = (centers[layer+1]-centers[layer]).length
            for i in range(count if closed else count-1):
                j = (i+1) % count
                uv = mapped([rings[layer][i],rings[layer][j],rings[layer+1][j],rings[layer+1][i]])
                if grain:
                    width = (rings[layer][i]-rings[layer][j]).length
                    uv = [(tex_u,tex_v),(tex_u+width,tex_v),(tex_u+width,tex_v+step),(tex_u,tex_v+step)]
                self.face([ids[layer][i],ids[layer][j],ids[layer+1][j],ids[layer+1][i]],mat,uv)
            tex_v += step

    def build(self):
        if not self.faces:
            return None
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.verts, [], self.faces)
        for mat in self.materials:
            mesh.materials.append(mat)
        mesh.polygons.foreach_set("material_index", self.indices)
        if any(self.uvs):
            uv = mesh.uv_layers.new(name="Timber grain")
            for poly, coords in zip(mesh.polygons, self.uvs):
                if coords:
                    for idx, co in zip(poly.loop_indices,coords):
                        uv.data[idx].uv = co
        mesh.update()
        ob = bpy.data.objects.new(self.name,mesh)
        self.coll.objects.link(ob)
        if self.coll != studio:
            ob.parent = root
        return ob


def corners(w,d,cut):
    a,b=w/2,d/2
    c=min(cut,a*.7,b*.7)
    return [(-a+c,-b),(a-c,-b),(a,-b+c),(a,b-c),(a-c,b),(-a+c,b),(-a,b-c),(-a,-b+c)]


def cuboid(part, p, size, mat, bevel=.016):
    x,y,z=p
    w,d,h=size
    c=min(bevel,h*.22,w*.22,d*.22)
    sections=[]
    for dz, inset in [(-h/2,c*.65),(-h/2+c,0),(h/2-c,0),(h/2,c*.65)]:
        sections.append([(x+a,y+b,z+dz) for a,b in corners(w-2*inset,d-2*inset,max(c*.5,.0001))])
    part.rings(sections,mat)


def stick(part, a,b,width,depth,mat,side=(0,1,0),cut=.018):
    a,b=V(a),V(b)
    direction=(b-a).normalized()
    edge=V(side)-direction*direction.dot(V(side))
    if edge.length < .01:
        edge = direction.cross(Z if abs(direction.z)<.95 else V((1,0,0)))
    edge.normalize()
    across = direction.cross(edge).normalized()
    outline=corners(width,depth,cut)
    part.rings([[p+across*u+edge*v for u,v in outline] for p in (a,b)],mat,grain=True)


def pipe(part,points,radius,mat,sides=10):
    points=[V(p) for p in points]
    axis=(points[-1]-points[0]).normalized()
    fixed=min((V((1,0,0)),V((0,1,0)),Z), key=lambda a:abs(a.dot(axis)))
    sections=[]
    for i,p in enumerate(points):
        tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
        cross=tangent.cross(fixed)
        if cross.length < .01:
            cross=tangent.cross(Z if abs(tangent.z)<.95 else V((1,0,0)))
        cross.normalize()
        up=tangent.cross(cross)
        sections.append([p+radius*(cross*math.cos(t*TAU/sides)+up*math.sin(t*TAU/sides)) for t in range(sides)])
    part.rings(sections,mat)


def slab(part, x,y,z, w,d,h,mat, roughness=.075, turn=0):
    polygon=corners(w,d,min(w,d)*rng.uniform(.16,.29))
    rc=min(w,d)*roughness
    polygon=[(u+rng.uniform(-rc,rc),v+rng.uniform(-rc,rc)) for u,v in polygon]
    bevel=min(.063,h*.25)
    heights=[rng.uniform(-bevel*.35,bevel*.35) for _ in polygon]
    sections=[]
    for level,scale in [(0,.88),(bevel,.99),(h-bevel,1),(h,.88)]:
        section=[]
        for (u,v),dz in zip(polygon,heights):
            a=u*math.cos(turn)-v*math.sin(turn)
            b=u*math.sin(turn)+v*math.cos(turn)
            section.append((x+a*scale,y+b*scale,z+level+dz))
        sections.append(section)
    part.rings(sections,mat)


def lathe(part, p, profile, mat, sides=16):
    x,y,z=p
    rings=[[(x+r*math.cos(TAU*i/sides),y+r*math.sin(TAU*i/sides),z+h)
            for i in range(sides)] for h,r in profile]
    part.rings(rings,mat,cap=False)


class Roof:
    """The same sagging deck supports the slate, fascia, and ridge profiles."""
    def __init__(self,name,origin,length,run,eave,rise,cross,sag):
        self.name=name
        self.origin=V((*origin,0))
        self.length,self.run,self.eave,self.rise=length,run,eave,rise
        self.U=V((0,1,0)) if cross else V((1,0,0))
        self.V=V((-1,0,0)) if cross else V((0,1,0))
        self.sag=sag
        self.coll=collection(name,roofs)

    def point(self,u,v,offset=0):
        t=abs(v)/self.run
        z=self.eave + self.rise*(1-t) - self.rise*.11*math.sin(min(t,1)*math.pi)
        z+=self.sag*((2*u/self.length)**2-.45) + .022*math.sin(u*1.55+.35)*min(t,1)
        return self.origin+self.U*u+self.V*v+Z*(z+offset)

    def build(self, rows, width):
        self.row_pitch=self.run/rows
        deck=Part(self.name+" | boarding and rafter tails",self.coll)
        fascia=Part(self.name+" | carved verge boards",self.coll)
        for s in [-1,1]:
            for i in range(9):
                a=-self.length/2+self.length*i/9
                b=a+self.length/9
                for j in range(4):
                    c=s*self.run*j/4
                    d=s*self.run*(j+1)/4
                    footprint=[(a,c),(b,c),(b,d),(a,d)]
                    deck.rings([[self.point(u,v,z) for u,v in footprint] for z in (-.14,-.045)],beamwood)
                stick(fascia,self.point(a,s*self.run,-.115),self.point(b,s*self.run,-.115),.20,.13,lightwood,self.V)
            n_rafters=max(4,round(self.length/.53))
            for i in range(n_rafters):
                u=-self.length/2+.16+i*(self.length-.32)/(n_rafters-1)
                stick(deck,self.point(u,s*(self.run-.46),-.20),self.point(u,s*(self.run-.03),-.20),.115,.13,beamwood,self.U)
            for u in [-self.length/2,self.length/2]:
                for j in range(5):
                    stick(fascia,self.point(u,s*self.run*j/5,-.072),self.point(u,s*self.run*(j+1)/5,-.072),.17,.135,timber,self.U)
            shingles=Part(self.name+(" | near" if s<0 else " | far")+" slope slates",self.coll)
            stations=max(3,round(self.length/width))
            interval=self.length/stations
            pitch=self.run/rows
            for row in range(rows):
                offset=.48 if row%2 else 0
                cuts=[-self.length/2]+[-self.length/2+interval*(k+offset+rng.uniform(-.105,.105))
                           for k in range(0 if offset else 1,stations)]+[self.length/2]
                for left,right in zip(cuts,cuts[1:]):
                    a,b=left+.005,right-.005
                    tip=self.run-pitch*row+rng.uniform(-.020,.020)
                    head=max(.012,self.run-pitch*(row+1)-.085)
                    wid=b-a
                    cut1=min(.082,wid*.21)*rng.uniform(.40,1.25)
                    cut2=min(.073,wid*.22)*rng.uniform(.50,1.20)
                    irregular=rng.uniform(-.028,.028)
                    border=[(a+.018,head),(b-.012,head+.01),(b,tip-cut2),
                            (b-cut2,tip+irregular),((a+b)/2,tip+.012),
                            (a+cut1,tip-.004+irregular*.3),(a,tip-cut1*.76)]
                    center=(a+b)/2
                    tilt=rng.uniform(-.065,.065)
                    variation=rng.uniform(-.009,.009)
                    rings=[]
                    for skin,edge in [(-.012,.010),(.057,0),(.084,.014)]:
                        line=[]
                        for u,v in border:
                            k=(v-head)/max(.1,tip-head)
                            uu=u+math.copysign(min(abs(center-u),edge),center-u)
                            vv=v+(.009 if k<.15 else -edge*.6)
                            lift=skin + k*.065 + variation + tilt*(u-center)
                            line.append(self.point(uu,s*vv,lift))
                        rings.append(line)
                    shingles.rings(rings,rng.choice(slates),uv_axes=(self.U,self.V))
            shingles.build()
        deck.build()
        fascia.build()
        ridge=Part(self.name+" | overlapping barrel ridge",self.coll)
        n=max(4,round(self.length/.47))
        span=self.length/n
        rad=min(.173,self.run*.16)
        for i in range(n):
            a=-self.length/2+i*span-.019
            tunnel=[]
            for du,factor in [(0,1.13),(.045,1.14),(.065,1.02),(span+.038,.96)]:
                u=a+du
                outline=[]
                for k in range(13):
                    angle=math.pi*k/12
                    v=rad*factor*math.cos(angle)
                    outline.append(self.point(u,0,.01)+self.V*v+Z*(rad*factor*math.sin(angle)))
                for k in range(12,-1,-1):
                    angle=math.pi*k/12
                    outline.append(self.point(u,0,.003)+self.V*((rad*.65)*math.cos(angle))+Z*(rad*.65*math.sin(angle)))
                tunnel.append(outline)
            ridge.rings(tunnel,caps)
        ridge.build()


main=Roof("Main roof",(0,.13),6.50,2.56,3.05,2.18,False,.26)
porch=Roof("Porch canopy",(-1.35,-2.34),2.88,1.28,2.59,1.06,True,.11)
dormer=Roof("Eyebrow dormer",(.79,-1.07),2.38,.78,4.04,.77,True,.055)
main.build(8,.47)
porch.build(4,.43)
dormer.build(3,.36)


class Facade:
    def __init__(self,origin,horizontal,outward):
        self.origin=V(origin)
        self.U=V(horizontal)
        self.D=V(outward)

    def p(self,u,z,d=0):
        return self.origin + self.U*u + self.D*d + Z*z

    def panel(self,part,outline,front,back,mat):
        part.rings([[self.p(u,z,d) for u,z in outline] for d in [back,front]],mat)

    def board(self,part,u1,z1,u2,z2,d,width,depth,mat):
        stick(part,self.p(u1,z1,d),self.p(u2,z2,d),width,depth,mat,self.D)

    def fill(self,part,half,foot,head,holes):
        cuts={-half,0,half}
        cuts.update(-half+2*half*i/10 for i in range(1,10))
        for u,w,lo,hi in holes:
            cuts.update((u-w/2,u+w/2))
        edges=sorted(cuts)
        for a,b in zip(edges,edges[1:]):
            openings=sorted((lo,hi) for u,w,lo,hi in holes if abs((a+b)/2-u)<w/2)
            bottom=foot
            for lo,hi in openings:
                if lo>bottom:
                    self.panel(part,[(a,bottom),(b,bottom),(b,lo),(a,lo)],0,-.14,lime)
                bottom=max(bottom,hi)
            if min(head(a),head(b))>bottom:
                self.panel(part,[(a,bottom),(b,bottom),(b,head(b)),(a,head(a))],0,-.14,lime)


front=Facade((0,-2.00,0),(1,0,0),(0,-1,0))
back=Facade((0,2.14,0),(-1,0,0),(0,1,0))
right=Facade((2.80,.07,0),(0,1,0),(1,0,0))
left=Facade((-2.80,.07,0),(0,-1,0),(-1,0,0))
def wallhead(face,u):
    x,y,_=face.p(u,0)
    return main.point(x,y-main.origin.y,-.087).z


def face_stone(part,face,u,d,z,w,thick,h,mat):
    p=face.p(u,z,d)
    slab(part,p.x,p.y,p.z,w,thick,h,mat,.035,math.atan2(face.U.y,face.U.x))


plinth=Part("Strip foundation | recessed pointing",walls)
cuboid(plinth,(0,.07,.32),(5.68,4.22,.64),mortar,.075)
plinth.build()
body=Part("Plaster shell | recessed door and window openings",walls)
basework=Part("Coursed limestone foundation",walls)
frame=Part("Corner posts and gable trusses",walls)
patch=Part("Exposed lime and corner stones",walls)
openings=[(front,2.80,[(-1.33,1.28,.44,2.45),(1.03,1.22,1.18,2.25)]),
          (right,2.07,[(.03,1.01,1.33,2.30)]),(back,2.80,[(-.91,1.04,1.30,2.29)]),
          (left,2.07,[(-.42,.90,1.36,2.27)])]
for face,half,holes in openings:
    face.fill(body,half,.55,lambda u:wallhead(face,u),holes)
    for j,(z,h) in enumerate([(.055,.23),(.283,.245),(.525,.21)]):
        count=round(half*2/.64)
        spacing=half*2/count
        stops=[-half]+[-half+(i+(.46 if j%2 else 0))*spacing+rng.uniform(-.065,.065)
                         for i in range(0 if j%2 else 1,count)]+[half]
        for a,b in zip(stops,stops[1:]):
            face_stone(basework,face,(a+b)/2,.045,z,b-a-.01,.22,h,rng.choice(stones))
    for s in [-1,1]:
        u=s*(half-.05)
        face.board(frame,u,.64,u,wallhead(face,u)-.04,.022,.155,.12,beamwood)
    for k in range(10):
        u=rng.uniform(-half+.13,half-.13)
        z=rng.choice((rng.uniform(.75,.96),wallhead(face,u)-rng.uniform(.22,.37)))
        if any(abs(u-uc)<width/2+.13 and lo-.12<z<hi+.12 for uc,width,lo,hi in holes):
            continue
        w=rng.uniform(.055,.16)
        face.panel(patch,[(u-w,z),(u-w*.8,z+.046),(u+w*.12,z+.072),(u+w,z+.04),(u+w*.55,z-.017)],
                   .003,0,lime_patch)
for face in [right,left]:
    face.board(frame,-2.05,2.94,2.05,2.94,.055,.15,.15,timber)
    face.board(frame,.06,2.95,.06,wallhead(face,.06)-.055,.055,.16,.15,beamwood)
    for s in [-1,1]:
        face.board(frame,s*1.48,2.97,s*.54,wallhead(face,s*.54)-.11,.055,.13,.13,timber)
for part in (body,basework,frame,patch):
    part.build()


def window(name,face,u,z,w,h,shutters=False):
    case=Part(name+" | oak casement",joinery)
    panes=Part(name+" | glass and stone sill",joinery)
    left_edge,right_edge=u-w/2,u+w/2
    bottom,top=z-h/2,z+h/2
    face.panel(panes,[(left_edge-.02,bottom-.02),(right_edge+.02,bottom-.02),
                      (right_edge+.02,top+.02),(left_edge-.02,top+.02)],-.125,-.16,shadow)
    for i in [0,1]:
        for j in [0,1]:
            a=left_edge+i*w/2+.018
            b=bottom+j*h/2+.018
            face.panel(panes,[(a,b),(a+w/2-.036,b),(a+w/2-.036,b+h/2-.036),(a,b+h/2-.036)],
                       -.087,-.119,glass[(i+j*2)%3])
    for col in [left_edge,u,right_edge]:
        outer=col!=u
        face.board(case,col,bottom-.047,col,top+.045,.014 if outer else -.02,
                   .105 if outer else .044,.14 if outer else .065,timber if outer else lightwood)
    for row in [bottom,z,top]:
        outer=row!=z
        face.board(case,left_edge-.088 if outer else left_edge,row,right_edge+(.088 if outer else 0),
                   row,.018 if outer else -.028,.105 if outer else .044,.15 if outer else .068,
                   timber if outer else lightwood)
    face_stone(panes,face,u,.065,bottom-.165,w+.31,.36,.12,stones[0])
    if shutters:
        for s in [-1,1]:
            center=u+s*(w/2+.32)
            for i in [-1,0,1]:
                uu=center+i*.143
                face.board(case,uu,bottom-.045,uu,top+.045,.10,.139,.085,timber if i!=0 else lightwood)
            for row in [bottom+.16,top-.16]:
                face.board(case,center-.239,row,center+.239,row,.164,.081,.069,beamwood)
                for du in [-.15,.15]:
                    pipe(case,[face.p(center+du,row,.194),face.p(center+du,row,.213)],.015,iron,8)
            face.board(case,center-.15*s,bottom+.22,center+.15*s,top-.21,.151,.056,.035,timber)
    case.build()
    panes.build()


window("Front flower window",front,1.03,1.715,1.22,1.07,True)
window("East window",right,.03,1.815,1.01,.97)
window("North window",back,-.91,1.795,1.04,.99)
window("West window",left,-.42,1.815,.90,.91)

# The dormer's cheeks disappear into the main slate slope at its upper end.
df=Facade((dormer.origin.x,-2.18,0),(1,0,0),(0,-1,0))
cheeks=Part("Dormer | plaster cheeks and open window",roofs)
df.fill(cheeks,.648,3.10,lambda u:dormer.point(df.origin.y-dormer.origin.y,-u,-.08).z,[(0,.74,3.48,4.17)])
dframe=Part("Dormer | timber framing",roofs)
for side in [-1,1]:
    x=dormer.origin.x+side*.648
    sidewall=Facade((x,-1.4,0),(0,side,0),(side,0,0))
    sidewall.fill(cheeks,.78,3.10,
                  lambda u:dormer.point(sidewall.p(u,0).y-dormer.origin.y,-side*.648,-.074).z,[])
    df.board(dframe,side*.60,3.29,side*.60,4.07,.038,.092,.096,timber)
df.board(dframe,-.65,4.23,.65,4.23,.032,.087,.10,beamwood)
df.board(dframe,0,4.25,0,4.69,.03,.085,.10,timber)
cheeks.build()
dframe.build()
window("Dormer",df,0,3.825,.74,.69)

# Slab-by-slab landing and treads with staggered joints.
steps=Part("Landing and three limestone treads",entry)
for xcenter,ycenter,w,d,h,rows in [
    (-1.34,-2.83,2.32,1.70,.47,3),(-1.34,-3.87,1.83,.44,.34,1),
    (-1.34,-4.24,1.72,.38,.215,1),(-1.34,-4.54,1.56,.31,.115,1)]:
    cuboid(steps,(xcenter,ycenter,h*.45),(w-.10,d-.06,h*.90),mortar,.045)
    for j in range(rows):
        breaks=[0,.28,.63,1] if j%2==0 else [0,.18,.51,.83,1]
        for a,b in zip(breaks,breaks[1:]):
            slab(steps,xcenter-w/2+(a+b)*w/2,ycenter-d/2+(j+.5)*d/rows,
                 h*.61,(b-a)*w-.011,d/rows-.014,h*.39,rng.choice(stones[:3]),.038)
steps.build()

posts=Part("Porch | feet, posts, and arched knee braces",entry)
py=-3.55
for side in [-1,1]:
    x=porch.origin.x+side*1.025
    slab(posts,x,py,.46,.40,.40,.22,stones[0],.035)
    stick(posts,(x,py,.665),(x+side*.013,py,2.62),.205,.23,timber)
    stick(posts,(x,-3.71,2.55),(x,-1.93,2.55),.197,.19,beamwood)
    # Curved oak corbel beneath the tie.
    shape=[(0,0),(.55,0),(.55,-.07),(.445,-.10),(.34,-.16),(.24,-.235),
           (.162,-.33),(.098,-.45),(.077,-.54),(0,-.54)]
    posts.rings([[(x-side*u,py+dy,2.54+v) for u,v in shape] for dy in [-.095,.095]],timber)
    posts.rings([[(x+dx,py+u,2.55+v) for u,v in shape] for dx in [-.074,.074]],timber)
    for z in [2.48,.89]:
        pipe(posts,[(x,py-.122,z),(x,py-.14,z)],.027,beamwood,8)
stick(posts,(-2.50,py,2.56),(-.20,py,2.56),.20,.205,beamwood)
stick(posts,(porch.origin.x,py,2.56),(porch.origin.x,py,3.60),.14,.15,timber)
for s in [-1,1]:
    stick(posts,(porch.origin.x+s*.85,py,2.60),(porch.origin.x+s*.29,py,3.31),.096,.12,timber)
posts.build()

doorface=Facade((0,-2.56,0),(1,0,0),(0,-1,0))
vest=Part("Porch | shelter around the recessed door",entry)
du=-1.33
for s in [-1,1]:
    x=du+s*.835
    cheek=Facade((x,-2.255,0),(0,s,0),(s,0,0))
    cheek.fill(vest,.305,.45,lambda u:porch.point(cheek.p(u,0).y-porch.origin.y,-(x-porch.origin.x),-.085).z,[])
    a,b=sorted((du+s*.64,x))
    doorface.panel(vest,[(a,.45),(b,.45),(b,2.55),(a,2.55)],0,-.13,lime)
    doorface.board(vest,x,.48,x,2.91,.025,.095,.115,timber)
outline=[(du-.835,2.45),(du+.835,2.45)]
outline.extend((x,porch.point(-2.56-porch.origin.y,-(x-porch.origin.x),-.096).z)
               for x in [du+.835,du+.42,du,du-.42,du-.835])
doorface.panel(vest,outline,0,-.14,lime)
vest.build()
door=Part("Front door | shaped boards, casing and hardware",entry)
def arch_top(x):
    return 2.25+.185*math.sqrt(max(0,1-(x/.64)**2))
doorface.panel(door,[(du-.65,.44),(du+.65,.44),(du+.65,2.46),(du-.65,2.46)],-.090,-.14,shadow)
for i in range(7):
    a=-.61+i*1.22/7+.004
    b=-.61+(i+1)*1.22/7-.004
    # Vertical texture is carried up each door stave.
    doorface.board(door,du+(a+b)/2,.485,du+(a+b)/2,min(arch_top(a),arch_top(b)),.003,
                b-a,.095,doorwood if i%3 else timber)
for s in [-1,1]:
    doorface.board(door,du+s*.661,.45,du+s*.661,2.26,.04,.15,.22,beamwood)
for i in range(14):
    a=math.pi*i/14
    b=math.pi*(i+1)/14
    outline=[(du+.58*math.cos(a),2.25+.135*math.sin(a)),
             (du+.58*math.cos(b),2.25+.135*math.sin(b)),
             (du+.736*math.cos(b),2.25+.272*math.sin(b)),
             (du+.736*math.cos(a),2.25+.272*math.sin(a))]
    doorface.panel(door,outline,.144,-.02,timber)
for z in [.83,1.97]:
    doorface.panel(door,[(du-.56,z-.048),(du-.27,z-.03),(du-.13,z),
                      (du-.27,z+.03),(du-.56,z+.048)],.071,.048,iron)
    for x in [-.51,-.33]:
        pipe(door,[doorface.p(du+x,z,.069),doorface.p(du+x,z,.081)],.016,copper,8)
pipe(door,[doorface.p(du+.39,1.48,.055),doorface.p(du+.39,1.48,.12)],.045,iron)
angles=[i*TAU/18 for i in range(19)]
pipe(door,[doorface.p(du+.39+.062*math.cos(a),1.424+.08*math.sin(a),.133) for a in angles],.014,iron,8)
door.build()

bench=Part("Porch | carpenter's stool",entry)
for dx in [-.15,.15]:
    for dy in [-.115,.115]:
        stick(bench,(-2.16+dx*1.2,-2.59+dy*1.25,.47),(-2.16+dx,-2.59+dy,.88),
              .060,.060,beamwood,cut=.008)
for k in [-1,0,1]:
    stick(bench,(-2.41,-2.59+k*.125,.90),(-1.91,-2.59+k*.125,.90),.125,.074,timber,(0,0,1))
bench.build().location.y=-.31

lantern=Part("Porch | hanging glazed lantern",entry)
lx,ly=-2.16,-3.83
pipe(lantern,[(lx-.19,-3.57,2.60),(lx-.19,-3.71,2.64),(lx-.09,ly,2.67),
              (lx,ly,2.59),(lx,ly,2.39)],.023,iron)
def square_lamp(z,r):
    return [(lx+x*r,ly+y*r,z) for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]
lantern.rings([square_lamp(2.30,.19),square_lamp(2.335,.18),square_lamp(2.445,.060)],iron)
lantern.rings([square_lamp(1.99,.10),square_lamp(2.29,.146)],amber)
lantern.rings([square_lamp(1.945,.06),square_lamp(1.985,.12),square_lamp(2.01,.12)],iron)
for a,b in zip(square_lamp(1.98,.12),square_lamp(2.30,.155)):
    pipe(lantern,[a,b],.014,iron,6)
lantern.build()


def chimney_ring(part,cx,cy,z,width,opening,h,mat):
    surface=corners(width,width,width*.10)
    hole=corners(opening,opening,opening*.10)
    for i in range(8):
        j=(i+1)%8
        shape=[surface[i],surface[j],hole[j],hole[i]]
        part.rings([[(cx+x,cy+y,z+dz) for x,y in shape] for dz in [0,h]],mat)


cx,cy=1.99,-.42
chimney=Part("Chimney | battered coursed stone and deep flue",hearth)
metalwork=Part("Chimney | folded lead apron",hearth)
extent=.57
ring_shape=corners(2*extent,2*extent,.07)
metalwork.rings([[main.point(cx+x,cy+y-main.origin.y,z) for x,y in ring_shape] for z in [.082,.115]],copper)
chimney_ring(chimney,cx,cy,4.04,.79,.46,1.97,mortar)
for row in range(8):
    z=4.04+row*.242
    outside=1.018-row*.021
    thick=.20
    d=outside/2-thick/2
    for side in [-1,1]:
        for axis in [0,1]:
            full=(axis==row%2)
            span=outside if full else outside-2*thick+.013
            pieces=2 if full or row%3==0 else 1
            cut=rng.uniform(.39,.59)
            breaks=[0,cut,1] if pieces==2 else [0,1]
            for a,b in zip(breaks,breaks[1:]):
                u=((a+b)/2-.5)*span
                x,y=(cx+u,cy+side*d) if axis==0 else (cx+side*d,cy+u)
                slab(chimney,x,y,z,(b-a)*span-.013,thick+.018,.243,rng.choice(stones),.038,axis*math.pi/2)
chimney_ring(chimney,cx,cy,5.978,.94,.49,.135,stones[0])
chimney_ring(chimney,cx,cy,6.099,.73,.46,.08,redclays[0])
chimney_ring(chimney,cx,cy,6.169,.665,.46,.185,redclays[1])
chimney_ring(chimney,cx,cy,6.34,.765,.445,.11,redclays[2])
chimney_ring(chimney,cx,cy,6.441,.735,.451,.046,redclays[0])
for side in [-1,1]:
    for axis in [0,1]:
        span=.769 if axis==0 else .455
        for k in [-1,1]:
            u=k*span*.25
            x,y=(cx+u,cy+side*.302) if axis==0 else (cx+side*.302,cy+u)
            slab(chimney,x,y,6.465,span/2-.006,.163,.059,
                 redclays[1 if k==side else 2],.012,axis*math.pi/2)
cuboid(chimney,(cx,cy,5.71),(.48,.48,.04),shadow)
chimney.build()
metalwork.build()

rain=Part("Bronze eaves trough, downpipe and brackets",hearth)
stations=[-.01, .5,1.0,1.52,2.02,2.53,2.91,3.12]
trough=[]
for x in stations:
    p=main.point(x,-main.run,-.12)+V((0,-.032,0))
    profile=[]
    for radius,angles in [(.090,range(13)),(.074,reversed(range(13)))]:
        for j in angles:
            a=math.pi*j/12
            profile.append(p+V((0,radius*math.cos(a),-radius*math.sin(a))))
    trough.append(profile)
rain.rings(trough,copper)
drain_x=2.62
lip=main.point(drain_x,-main.run,-.19)
drain=[lip,lip-Z*.18,V((drain_x,-2.43,lip.z-.26)),V((drain_x,-2.17,lip.z-.42)),
       V((drain_x,-2.12,lip.z-.52)),V((drain_x,-2.12,.43)),V((drain_x,-2.16,.32)),V((drain_x,-2.28,.28))]
pipe(rain,drain,.057,copper,14)
for z in [.71,1.75,2.35]:
    pipe(rain,[(drain_x,-2.12,z-.021),(drain_x,-2.12,z+.021)],.070,iron,12)
rain.build()


def blade(part,base,tip,width,across,mat,lift=Z,heart=False):
    base,tip=V(base),V(tip)
    delta=tip-base
    across=V(across).normalized()*width
    lift=V(lift).normalized()*delta.length
    span=[(0,0),(.22,-.86),(.49,-1),(.75,-.62),(1,0),(.72,.60),(.44,1),(.21,.83)]
    if heart:
        span=[(.05,0),(-.035,-.48),(.16,-1),(.42,-.90),(.70,-.53),(1,0),
              (.74,.47),(.40,.96),(.14,.98),(-.045,.43)]
    border=part.vertices([base+delta*t+across*w+lift*(.105*math.sin(math.pi*t)) for t,w in span])
    center=part.vertices([base+delta*.43+lift*.175])[0]
    for i in range(len(border)):
        part.face([border[i],border[(i+1)%len(border)],center],mat)


def bloom(part,c,r,white=False,petals=5):
    center=V(c)
    color=petal_light if white else petal
    phase=rng.uniform(0,TAU)
    for k in range(petals):
        a=phase+TAU*k/petals
        forward=V((math.cos(a),math.sin(a),0))*r
        side=V((-math.sin(a),math.cos(a),0))*r
        shape=[center+forward*.08,center+forward*.48-side*.31,
               center+forward*.91-side*.29+Z*r*.17,center+forward+Z*r*.2,
               center+forward*.90+side*.29+Z*r*.17,center+forward*.46+side*.31]
        ids=part.vertices(shape+[center+forward*.56+Z*r*.14])
        for i in range(6):
            part.face([ids[i],ids[(i+1)%6],ids[-1]],color)
    lathe(part,center-Z*r*.02,[(0,r*.19),(r*.12,r*.225),(r*.16,r*.10)],pollen,7)


planter=Part("Front window | banded flower box",garden)
for y in [-2.17,-2.49]:
    for z in [.985,1.093]:
        stick(planter,(.31,y,z),(1.75,y,z),.11,.068,timber,(0,1,0))
for x in [.335,1.725]:
    stick(planter,(x,-2.50,1.04),(x,-2.15,1.04),.206,.075,beamwood,(1,0,0))
for x in [.46,1.61]:
    cuboid(planter,(x,-2.527,1.036),(.047,.026,.219),iron,.008)
cuboid(planter,(1.03,-2.33,1.07),(1.35,.25,.06),soil)
planter.build()
flowers=Part("Window garden | trailing leaves and daisies",garden)
for i in range(65):
    x=rng.uniform(.39,1.66)
    y=rng.uniform(-2.445,-2.22)
    p=V((x,y,1.10+rng.uniform(0,.10)))
    a=rng.uniform(0,TAU)
    forward=V((math.cos(a),math.sin(a),rng.uniform(.02,.80)))
    blade(flowers,p,p+forward*rng.uniform(.09,.19),rng.uniform(.03,.059),
          (-math.sin(a),math.cos(a),0),rng.choice(leaves))
for i in range(23):
    x=rng.uniform(.43,1.61)
    y=rng.uniform(-2.46,-2.23)
    h=rng.uniform(.10,.24)
    pipe(flowers,[(x,y,1.10),(x+.03,y-.025,1.10+h)],.0048,leaves[0],5)
    bloom(flowers,(x+.03,y-.025,1.10+h),rng.uniform(.039,.065),i%3==0)
for k in range(5):
    x=.42+k*.27+rng.uniform(-.06,.06)
    line=[V((x+.026*math.sin(t*2+k),-2.51-.034*t,1.19-.071*t)) for t in range(rng.randint(4,7))]
    pipe(flowers,line,.007,leaves[2],6)
    for j,p in enumerate(line[1:]):
        side=(-1)**j
        blade(flowers,p,p+V((side*.077,-.016,-.08)),.042,(1,0,.2),leaves[j%3],(0,-1,0),True)
flowers.build()

pot=Part("Rolled terracotta pot",garden)
px,py=-2.84,-2.85
lathe(pot,(px,py,.025),[(0,.229),(.055,.242),(.11,.23),(.30,.33),(.46,.354),
                         (.50,.37),(.53,.378),(.56,.37),(.56,.317),(.46,.316)],redclays[1],24)
lathe(pot,(px,py,.025),[(.347,.341),(.366,.349),(.383,.347)],redclays[0],24)
cuboid(pot,(px,py,.49),(.43,.43,.08),soil,.065)
pot.build()
hyd=Part("Potted hydrangea | stems, foliage and florets",garden)
for k in range(22):
    a=k*2.39996
    reach=rng.uniform(.18,.43)
    start=V((px+.032*math.cos(a),py+.032*math.sin(a),.52+rng.uniform(.02,.18)))
    tip=start+V((math.cos(a)*reach,math.sin(a)*reach,rng.uniform(.08,.26)))
    blade(hyd,start,tip,.096,(-math.sin(a),math.cos(a),0),rng.choice(leaves[:3]))
for k,(dx,dy,h,r) in enumerate([(-.19,.01,.97,.13),(.15,.09,1.03,.145),(.01,-.13,.92,.14),
                                  (-.06,.14,1.12,.14),(.19,-.085,.87,.108)]):
    stem=V((px+dx,py+dy,h))
    pipe(hyd,[(px,py,.53),((px+stem.x)/2,(py+stem.y)/2,.75),stem],.014,leaves[2],6)
    for j in range(24):
        fract=(j+.5)/24
        a=j*2.39996+k
        radius=r*math.sqrt(fract)
        loc=stem+V((radius*math.cos(a),radius*math.sin(a),r*.75*math.sqrt(1-fract)))
        bloom(hyd,loc,.036 if k!=4 else .031,True,4)
hyd.build()

ivy=Part("Ivy | branching tendrils on east corner",garden)
for face,start,width,height in [(front,2.30,.39,2.64),(right,-1.79,.70,2.94)]:
    paths=[]
    stem=[(start+.073*math.sin(j*.72),.12+j*height/16) for j in range(17)]
    paths.append(stem)
    for j,s in [(4,1),(7,-1),(9,1),(11,-1)]:
        u,z=stem[j]
        paths.append([(u+s*width*t/6+.052*math.sin(t*.65),z+.085*t+.037*math.sin(t)) for t in range(7)])
    for path in paths:
        pipe(ivy,[face.p(u,z,.113+.009*math.sin(z*3)) for u,z in path],.011,beamwood,6)
        for j,(u,z) in enumerate(path):
            for side in [-1,1]:
                length=rng.uniform(.080,.155)
                origin=face.p(u,z+side*.03,.126)
                end=origin+face.U*(side*length)+Z*rng.uniform(-.082,.055)+face.D*.030
                delta=end-origin
                across=face.D.cross(delta)
                blade(ivy,origin,end,length*.46,across,rng.choice(leaves[:3]),face.D,True)
ivy.build()

# A shallow planted plot follows the footprint and narrows around the approach.
ground=Part("Garden plot | turf and soil edge",garden)
outline=[(-3.33,-2.77),(-3.24,-3.26),(-2.90,-3.70),(-2.56,-3.98),(-2.43,-4.53),
         (-2.23,-5.06),(-1.88,-5.45),(-1.48,-5.66),(-.94,-5.63),(-.53,-5.26),(-.37,-4.76),
         (-.12,-4.21),(.30,-3.76),(.79,-3.48),(1.45,-3.28),(2.01,-3.24),(2.55,-3.07),
         (3.06,-2.83),(3.33,-2.39),(3.44,-1.88),(3.42,-1.29),(3.57,-.69),(3.48,.14),
         (3.55,.82),(3.43,1.60),(3.22,2.18),(2.89,2.54),(2.36,2.78),(1.80,2.83),
         (1.12,2.90),(.47,2.79),(-.26,2.87),(-.96,2.92),(-1.68,2.77),(-2.38,2.81),
         (-2.96,2.59),(-3.30,2.21),(-3.37,1.48),(-3.49,.81),(-3.42,.20),(-3.49,-.50),
         (-3.39,-1.26),(-3.46,-1.94)]
edge=[]
for i,(x,y) in enumerate(outline):
    u,v=outline[(i+1)%len(outline)]
    edge.extend([(x,y),((x+u)/2+rng.uniform(-.04,.04),(y+v)/2+rng.uniform(-.035,.035))])
outer=[(x,y,-.052+rng.uniform(-.008,.006)) for x,y in edge]
shoulder=[(x*.986,(y+.7)*.986-.7,.012+rng.uniform(-.015,.018)) for x,y in edge]
inner=[(x*.94,(y+.7)*.94-.7,.045+rng.uniform(-.009,.014)) for x,y in edge]
ids=[ground.vertices(p) for p in [outer,shoulder,inner]]
for j in range(len(edge)):
    k=(j+1)%len(edge)
    for band,mat in enumerate((soil,turf)):
        ground.face([ids[band][j],ids[band][k],ids[band+1][k],ids[band+1][j]],mat)
ground.face(ids[2],turf)
ground.face(ids[0][::-1],soil)
ground.build()

path=Part("Garden | flagstone path and scattered stones",garden)
for x,y,w,d,angle in [(-1.33,-4.91,.81,.34,.14),(-1.19,-5.23,.68,.30,-.13),(-1.08,-5.48,.55,.22,.12)]:
    slab(path,x,y,.042,w,d,.074,rng.choice(stones[:3]),.074,angle)
for j in range(52):
    k=rng.randrange(len(edge))
    x,y=edge[k]
    x*=rng.uniform(.88,.97)
    y=(y+.7)*rng.uniform(.90,.97)-.70
    if -2.24<x<-.45 and y<-3.76:
        continue
    r=rng.uniform(.025,.113)
    slab(path,x,y,.045,r*1.69,r,r*.53,rng.choice(stones),.08,rng.uniform(-1,1))
path.build()

growth=Part("Garden | grasses, sorrel and buttercups",garden)
for j in range(630):
    x,y=rng.choice(edge)
    t=rng.uniform(.81,.986)
    x=x*t+rng.uniform(-.035,.035)
    y=(y+.7)*t-.7+rng.uniform(-.035,.035)
    if -2.30<x<-.44 and y<-3.67:
        continue
    for k in range(rng.randint(3,6)):
        a=rng.uniform(0,TAU)
        p=V((x+rng.uniform(-.051,.051),y+rng.uniform(-.051,.051),.043))
        h=rng.uniform(.06,.155)
        blade(growth,p,p+V((math.cos(a)*h*.55,math.sin(a)*h*.55,h)),
              h*rng.uniform(.075,.17),(-math.sin(a),math.cos(a),0),rng.choice(leaves))
    if j%17==0:
        stem=V((x+.025,y-.022,.18+rng.uniform(0,.065)))
        pipe(growth,[(x,y,.045),stem],.005,leaves[0],5)
        bloom(growth,stem,rng.uniform(.038,.054),j%3==0)
for x,y in [(2.72,-2.54),(3.03,-1.72),(-2.83,-3.29),(-2.23,-4.0),(2.91,1.84)]:
    for k in range(6):
        a=k*TAU/6+rng.uniform(-.25,.25)
        d=V((math.cos(a),math.sin(a),0))
        side=Z.cross(d)
        length=rng.uniform(.19,.36)
        points=[V((x,y,.066))+d*(length*i/7)+Z*(.14*math.sin(math.pi*i/9)) for i in range(8)]
        pipe(growth,points,.005,leaves[2],5)
        for i in range(1,7):
            for s in [-1,1]:
                start=points[i]
                blade(growth,start,start+side*(s*length*.24*(1-i*.10))+d*.036+Z*.02,.018,d,leaves[k%3])
growth.build()

# Accumulations follow gutters and tile seams, leaving the large roof planes legible.
pad_mat=paint("Moss | velvet cushions",("50612B","717E35","96A046"),12,relief=.012)
lichen_mat=paint("Lichen | grey gold",("7C824D","91985C","A7A36A"),16,relief=.005)
cushions=Part("Roof | moss at sheltered joints",roofs)
patches=[(main,1.57,-.65,.39,.18),(main,2.06,-.95,.43,.14),(main,.04,-1.61,.21,.42),
         (main,-2.35,-1.64,.20,.50),(main,-.21,-.40,.52,.19),(main,-2.19,.72,.43,.22),
         (main,.77,1.95,.52,.24),(main,2.54,-1.85,.26,.26),(porch,-.13,-.89,.28,.14),
         (porch,-1.17,.58,.24,.20),(dormer,-.23,.44,.17,.13)]
for roof,u0,v0,spread_u,spread_v in patches:
    for j in range(17):
        a=rng.uniform(0,TAU)
        distance=math.sqrt(rng.random())
        u=u0+math.cos(a)*distance*spread_u
        v=v0+math.sin(a)*distance*spread_v
        r=rng.uniform(.026,.088)*(1.34-.52*distance)
        coords=[(r*math.cos(i*TAU/11)*rng.uniform(.78,1.19),r*.76*math.sin(i*TAU/11)*rng.uniform(.74,1.16)) for i in range(11)]
        levels=[]
        for s,h in [(1,-.004),(.84,.008),(.41,.024)]:
            ring=[]
            for x,y in coords:
                vv=v+y*s
                within=((roof.run-abs(vv))%roof.row_pitch)/(roof.row_pitch+.085)
                ring.append(roof.point(u+x*s,vv,.085+.065*(1-within)+h))
            levels.append(ring)
        cushions.rings(levels,pad_mat if j%7 else lichen_mat)
cushions.build()

# Clean paper sweep and a directional late-morning studio rig.
paper=bpy.data.materials.new("Studio | warm ivory")
paper.diffuse_color=rgba("F5EBD5")
paper.use_nodes=True
paper.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=paper.diffuse_color
paper_nodes=paper.node_tree.nodes
paper_link=paper.node_tree.links.new
paper_glow=paper_nodes.new("ShaderNodeEmission")
paper_glow.inputs["Color"].default_value=rgba("FFF3D9")
paper_glow.inputs["Strength"].default_value=2.0
paper_mix=paper_nodes.new("ShaderNodeMixShader")
camera_fill=paper_nodes.new("ShaderNodeMath")
camera_fill.operation="MULTIPLY"
camera_fill.inputs[1].default_value=.41
paper_link(paper_nodes.new("ShaderNodeLightPath").outputs["Is Camera Ray"],camera_fill.inputs[0])
paper_link(camera_fill.outputs[0],paper_mix.inputs[0])
paper_link(paper_nodes.get("Principled BSDF").outputs[0],paper_mix.inputs[1])
paper_link(paper_glow.outputs[0],paper_mix.inputs[2])
paper_link(paper_mix.outputs[0],paper_nodes.get("Material Output").inputs["Surface"])
plane=Part("Matte sweep",studio)
plane.face(plane.vertices([(-200,-200,-.062),(200,-200,-.062),(200,200,-.062),(-200,200,-.062)]),paper)
plane.build()
world=bpy.data.worlds.new("Soft sky fill")
scene.world=world
world.use_nodes=True
bg=world.node_tree.nodes.get("Background")
bg.inputs[0].default_value=(.78,.85,1,1)
bg.inputs[1].default_value=.25


def area(name,p,target,power,size,color):
    data=bpy.data.lights.new(name,"AREA")
    data.shape="DISK"
    data.size=size
    data.energy=power
    data.color=color
    ob=bpy.data.objects.new(name,data)
    studio.objects.link(ob)
    ob.location=p
    ob.rotation_euler=(V(target)-ob.location).to_track_quat("-Z","Y").to_euler()


area("Key | afternoon sun",(-5.3,-6.6,9.1),(0,-.5,1.65),1490,2.8,(1,.86,.65))
area("Fill | sky bounce",(5.0,-4.2,6.9),(0,-1,1.9),365,5.6,(.79,.88,1))
area("Rim | roof glint",(1.4,5.5,9.2),(0,0,2.7),615,4.3,(1,.92,.74))
wick_data=bpy.data.lights.new("Lantern glow","POINT")
wick_data.energy=17
wick_data.color=(1,.53,.17)
wick_data.shadow_soft_size=.12
wick=bpy.data.objects.new("Lantern glow",wick_data)
studio.objects.link(wick)
wick.location=(lx+.06,ly+.07,2.04)

camera_data=bpy.data.cameras.new("60 degree review lens")
camera=bpy.data.objects.new("Preview | 60 degrees down",camera_data)
studio.objects.link(camera)
target=V((0,-.55,1.87))
elevation=math.radians(60)
azimuth=math.radians(25)
camera.location=target+18*V((math.cos(elevation)*math.sin(azimuth),-math.cos(elevation)*math.cos(azimuth),math.sin(elevation)))
camera.rotation_euler=(target-camera.location).to_track_quat("-Z","Y").to_euler()
camera_data.type="ORTHO"
camera_data.ortho_scale=11.85
scene.camera=camera

for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    tree=mat.node_tree
    output=next((n for n in tree.nodes if n.type=="OUTPUT_MATERIAL"),None)
    levels={}
    def place(node,depth):
        if node in levels and levels[node]>=depth:
            return
        levels[node]=depth
        for socket in node.inputs:
            for connection in socket.links:
                place(connection.from_node,depth+1)
    if output:
        place(output,0)
    by_depth={}
    for node,depth in levels.items():
        index=by_depth.get(depth,0)
        node.location=(-depth*285,-index*370)
        by_depth[depth]=index+1

scene.render.engine="CYCLES"
scene.cycles.samples=12 if DRAFT else 64
scene.cycles.adaptive_threshold=.065 if DRAFT else .030
scene.cycles.use_denoising=True
scene.cycles.max_bounces=6
scene.render.resolution_x=1560
scene.render.resolution_y=1360
scene.render.resolution_percentage=55 if DRAFT else 100
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGB"
scene.view_settings.view_transform="AgX"
scene.view_settings.look="AgX - Medium High Contrast"
scene.render.film_transparent=False
for screen in bpy.data.screens:
    for area_handle in screen.areas:
        if area_handle.type=="VIEW_3D":
            space=area_handle.spaces.active
            space.region_3d.view_perspective="CAMERA"
            space.region_3d.view_camera_zoom=6
            space.region_3d.view_distance=11
            space.region_3d.view_location=target
            space.shading.color_type="MATERIAL"
            space.shading.light="STUDIO"
            space.shading.show_cavity=True
            space.overlay.show_overlays=False

if DRAFT:
    scene.render.filepath=str(OUT/"Draft_Max.png")
else:
    scene.render.filepath="//Preview_Max.png"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"MossCottage_Max.blend"),compress=True,relative_remap=False)
bpy.ops.render.render(write_still=True)
print("Rendered",bpy.path.abspath(scene.render.filepath),flush=True)
