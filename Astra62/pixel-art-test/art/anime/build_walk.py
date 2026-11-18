"""Render the approved elf from separately painted arms, legs, torso and cape.

Run with Python, Pillow and NumPy. --preview-dir adds registered transparency
plates, contact sheets, tracked joint coordinates and cape-motion landmarks.
"""

import argparse
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from boot_deform import Boot
from extract_arms import ART, NATIVE, arm_coords, extract_arms

sys.path.insert(0,str(ART.parent))
from walk_cycle import body_drop, sample_foot


ASSETS=ART.parent.parent/'assets'
LAYER_DIR=ART/'layers'
HD,AA=512,1.5
SCALE,GROUND=.542,842.
TAU=math.tau
COUNTS=(4,6,8,12)
ORDER=('cape-back','far-arm-bow','far-leg','near-leg','body','near-arm','cape-front')


def v(x,y):
    return np.array([x,y],dtype=float)


def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)


def in_world(points):
    return (np.asarray(points)-v(375,GROUND))*SCALE+v(256,480)


def matte(img,mask):
    result=img.copy()
    result.putalpha(ImageChops.multiply(img.getchannel('A'),mask))
    return result


def polygon(size,points):
    result=Image.new('L',size)
    ImageDraw.Draw(result).polygon([tuple(point) for point in points],fill=255)
    return result


class Patch:
    """Original transparent artwork on a regular, deformable texture mesh."""

    def __init__(self, artwork, spacing=38):
        left,top,right,bottom = artwork.getchannel('A').getbbox()
        self.origin = v(left,top)
        tight = artwork.crop((left,top,right,bottom))
        # Premultiplied sampling preserves colored antialiased ink around hair.
        self.texture = np.asarray(tight.convert('RGBa'), dtype=np.float32)/255
        w,h = tight.size
        gx = np.linspace(0,w-1,max(2,math.ceil(w/spacing)+1))
        gy = np.linspace(0,h-1,max(2,math.ceil(h/spacing)+1))
        self.x_grid,self.y_grid=gx+left,gy+top
        self.positions = np.stack(np.meshgrid(gx,gy),axis=-1).reshape(-1,2)+self.origin
        self.triangles = []
        alpha = self.texture[:,:,3]
        for j in range(len(gy)-1):
            for i in range(len(gx)-1):
                if not alpha[math.floor(gy[j]):math.ceil(gy[j+1])+1,
                             math.floor(gx[i]):math.ceil(gx[i+1])+1].any():
                    continue
                a=j*len(gx)+i
                b,c,d=a+1,a+len(gx),a+len(gx)+1
                self.triangles.extend([(a,b,d),(a,d,c)])

    def attachments(self,points):
        """Barycentric attachments on the exact triangles used to draw the cel."""
        x,y=np.asarray(points).T
        ix=np.clip(np.searchsorted(self.x_grid,x,side='right')-1,0,len(self.x_grid)-2)
        iy=np.clip(np.searchsorted(self.y_grid,y,side='right')-1,0,len(self.y_grid)-2)
        fx=np.clip((x-self.x_grid[ix])/(self.x_grid[ix+1]-self.x_grid[ix]),0,1)
        fy=np.clip((y-self.y_grid[iy])/(self.y_grid[iy+1]-self.y_grid[iy]),0,1)
        base=iy*len(self.x_grid)+ix; right=fx>=fy
        ids=np.stack((base,np.where(right,base+1,base+len(self.x_grid)),base+len(self.x_grid)+1),axis=1)
        weights=np.stack((1-np.maximum(fx,fy),np.abs(fx-fy),np.minimum(fx,fy)),axis=1)
        return lambda vertices:np.sum(vertices[ids]*weights[:,:,None],axis=1)

    def paint(self,transform):
        return self.paint_vertices(transform(self.positions))

    def paint_vertices(self,vertices):
        size = round(HD*AA)
        screen = in_world(vertices)*AA
        local = self.positions-self.origin
        pixels = np.zeros((size,size,4),dtype=np.float32)
        sh,sw = self.texture.shape[:2]
        for ids in self.triangles:
            ids=list(ids); dest=screen[ids]; src=local[ids]
            xmin,ymin=np.maximum(0,np.floor(dest.min(axis=0)).astype(int))
            xmax,ymax=np.minimum(size-1,np.ceil(dest.max(axis=0)).astype(int))
            if xmin>xmax or ymin>ymax:
                continue
            m,n=dest[1]-dest[0],dest[2]-dest[0]
            det=m[0]*n[1]-m[1]*n[0]
            if abs(det)<1e-5:
                continue
            yy,xx=np.mgrid[ymin:ymax+1,xmin:xmax+1]
            x=xx+.5-dest[0,0]; y=yy+.5-dest[0,1]
            u=(x*n[1]-y*n[0])/det; w=(m[0]*y-m[1]*x)/det
            inside=(u>=-1e-5)&(w>=-1e-5)&(u+w<=1.00001)
            if not inside.any():
                continue
            u,w=u[inside],w[inside]
            uv=src[0]+u[:,None]*(src[1]-src[0])+w[:,None]*(src[2]-src[0])
            tx,ty=np.clip(uv[:,0],0,sw-1.001),np.clip(uv[:,1],0,sh-1.001)
            x0,y0=tx.astype(int),ty.astype(int)
            ax,ay=(tx-x0)[:,None],(ty-y0)[:,None]
            sample=(self.texture[y0,x0]*(1-ax)+self.texture[y0,x0+1]*ax)*(1-ay)
            sample+=(self.texture[y0+1,x0]*(1-ax)+self.texture[y0+1,x0+1]*ax)*ay
            visible=sample[:,3]>.001
            pixels[yy[inside][visible],xx[inside][visible]]=sample[visible]
        return pixels


def over(back,front):
    return front+back*(1-front[:,:,3:4])


def align(points,a,b,c,d):
    old=b-a; new=d-c
    a0=math.atan2(old[1],old[0]); a1=math.atan2(new[1],new[0]); ang=a1-a0
    co,si=math.cos(ang),math.sin(ang)
    rot=np.array([[co,si],[-si,co]])
    return c+(points-a)@rot*(np.linalg.norm(new)/np.linalg.norm(old))


def rotated(points,src,pivot,angle):
    co,si=math.cos(angle),math.sin(angle)
    return pivot+(points-src)@np.array([[co,si],[-si,co]])


def joint(start,end,length_a,length_b,side):
    diff=end-start; length=np.linalg.norm(diff); axis=diff/length
    along=min(length_a,(length**2+length_a**2-length_b**2)/(2*length))
    if length>=length_a+length_b:
        return start+diff*(length_a/(length_a+length_b))
    bend=math.sqrt(max(0,length_a**2-along**2))
    return start+axis*along+side*np.array([axis[1],-axis[0]])*bend



FAR_LEG=np.array([(433,501),(380,620),(289,765)],float)
NEAR_LEG=np.array([(495,497),(529,629),(579,768)],float)
NEAR_ARM=arm_coords([(805,412),(772,554),(853,683)],True)
FAR_ARM=arm_coords([(1109,426),(1171,529),(1316,552)],False)


def registered_layer(directory,name):
    path=directory/(name+'.png')
    with Image.open(path) as im:
        if im.mode!='RGBA' or im.size!=NATIVE:
            raise ValueError(f'{path} must be a transparent 704×854 RGBA plate.')
        return im.copy()


def split_legs(art):
    """Keep the entire scalloped underskirt with the torso. Both legs receive
    closed skin under the skirt so crossing poses reveal continuous thighs."""
    hem=np.array([(0,531),(391,531),(399,538),
        (406,539),(411,540),(413,546),(420,549),(426,547),(429,552),
        (434,555),(439,553),(441,556),(445,559),(451,561),(455,563),
        (461,561),(466,561),(470,562),(474,560),(478,561),(482,557),
        (486,557),(490,554),(494,554),(500,551),(504,551),(508,548),
        (512,547),(516,546),(520,544),(525,545),(530,542),(536,541),
        (541,539),(551,537),(704,537)],float)
    yy,xx=np.indices((art.height,art.width))
    threshold=np.interp(xx,hem[:,0],hem[:,1])
    lower=yy>=threshold
    far=lower&(xx<465)
    near=lower&~far
    # Below the skirt the two reference legs have a wide clear-space gap.
    # For the lower boot/toe the fixed separator never meets either leg.
    body=matte(art,Image.fromarray(np.where(lower,0,255).astype('uint8')))
    raw=np.asarray(art)

    def make_piece(region,outline,fill,far_side=False):
        base=Image.new('RGBA',NATIVE)
        ImageDraw.Draw(base).polygon(outline,fill=fill,outline='#bd8276',width=1)
        rgba=np.array(base)
        blend=smooth((570-yy)/48)*.85
        is_skin=rgba[:,:,0]>210
        for c,tone in enumerate((249,184,174)):
            channel=rgba[:,:,c].astype(float)
            channel=np.where(is_skin,channel*(1-blend)+tone*blend,channel)
            rgba[:,:,c]=channel.astype('uint8')
        piece=Image.fromarray(rgba)
        visible=raw.copy()
        coverage=smooth((yy-threshold+1)/5)
        # Edges beside skin may contain antialiasing from the immobile lace.
        # Recover the native leg color there, with the divided skirt above it.
        visible[:,:,3]=(visible[:,:,3]*region*coverage).round().astype('uint8')
        connected=Image.fromarray(np.where(visible[:,:,3]>8,255,0).astype('uint8')).copy()
        ImageDraw.floodfill(connected,(374,615) if far_side else (532,615),126)
        support=connected.point(lambda k:255 if k==126 else 0).filter(ImageFilter.MaxFilter(3))
        visible[:,:,3]*=(np.asarray(support)>0)
        piece.alpha_composite(Image.fromarray(visible))
        if far_side:
            rgba=np.array(piece)
            rgba[:,:,:3]=np.clip(rgba[:,:,:3]*[.936,.916,.958]+[4.,2.,3.],0,255).astype('uint8')
            piece=Image.fromarray(rgba)
        return piece

    far_art=make_piece(far,[(398,507),(436,493),(458,499),(472,517),(463,546),
        (452,564),(437,573),(413,562),(393,555),(390,546)],'#ffd3c9',True)
    near_art=make_piece(near,[(454,506),(497,490),(522,501),(536,523),(542,548),
        (535,559),(503,572),(483,573),(472,562),(454,526)],'#ffd7cf')
    return body,far_art,near_art


def pelvis_drift(phase):
    return 3.1*math.sin(2*TAU*phase-.24)


class Leg:
    def __init__(self,artwork,nodes,side):
        self.patch=Patch(artwork,9)
        self.nodes,self.side=nodes,side
        hip,knee,ankle=nodes
        self.boot=Boot(artwork,ankle,side>0)
        directions=(ankle-hip)/np.linalg.norm(ankle-hip)
        self.knee=smooth(((self.patch.positions-knee)@directions+29)/58)[:,None]
        shaft=(ankle-knee)/np.linalg.norm(ankle-knee)
        p=self.patch.positions-ankle
        shoe=np.maximum(smooth((p@shaft+18)/48),smooth((p[:,1]+3)/35))
        # At the toe this weight is one even when the reference tibia slopes
        # backwards. The boot ribbon and the upper shaft stay on the shin.
        forward=(self.patch.positions-self.boot.ball)@self.boot.axis
        shoe=np.maximum(shoe,smooth((forward+32)/32)*smooth((p[:,1]+30)/23))
        self.foot=shoe[:,None]
        self.outsole_attachment=self.patch.attachments(self.boot.sole_pixels)
        self.mark_attachment=self.patch.attachments([self.boot.heel,self.boot.ball,self.boot.toe])
        self.fold_attachments=[self.patch.attachments(path) for path in self.boot.crease_paths]
        flat=self.boot.local(self.patch.positions,sample_foot(.16))
        self.flat_ball_x=self.mark_attachment(flat)[1,0]

    def pose(self,phase,bob):
        foot=sample_foot(phase)
        hip,knee,ankle=self.nodes
        cosine=math.cos(TAU*phase)
        start=v(464+27*cosine+self.side*3+pelvis_drift(phase),
                hip[1]+bob+2.+3.1*math.sin(TAU*phase-.15))
        boot_local=self.boot.local(self.patch.positions,foot)
        support=self.outsole_attachment(boot_local)[:,1].max()
        # On the treadmill the flat ankle track is also the planted ball's
        # transport track. Rolling over that ball moves the ankle forward;
        # release the correction as the airborne leg takes over.
        planted=smooth((foot.heel_deg-.3)/20)*(1-smooth((phase-.565)/.15))
        ball_x=self.mark_attachment(boot_local)[1,0]
        end=v(foot.x+planted*(self.flat_ball_x-ball_x),GROUND-foot.lift-support)
        thigh_length=np.linalg.norm(knee-hip)
        shin_length=np.linalg.norm(ankle-knee)

        def position_vertices():
            middle=joint(start,end,thigh_length,shin_length,1)
            upper=align(self.patch.positions,hip,knee,start,middle)
            lower=align(self.patch.positions,knee,ankle,middle,end)
            leg=upper*(1-self.knee)+lower*self.knee
            vertices=leg*(1-self.foot)+(boot_local+end)*self.foot
            return middle,vertices

        middle,vertices=position_vertices()
        sole=self.outsole_attachment(vertices)
        delta=GROUND-foot.lift-sole[:,1].max()
        if abs(delta)>.025:
            end[1]+=delta
            middle,vertices=position_vertices()
            sole=self.outsole_attachment(vertices)
        marks=self.mark_attachment(vertices)
        contact=sole[np.argmax(sole[:,1])]
        return vertices,(start,middle,end,*marks,contact),foot

    def draw(self,phase,bob):
        vertices,joints,foot=self.pose(phase,bob)
        layer=self.patch.paint_vertices(vertices)
        strength=float(smooth((foot.heel_deg-foot.toe_deg-4)/42))
        if strength>0:
            size=round(HD*AA)
            crease=Image.new('L',(size,size))
            brush=ImageDraw.Draw(crease)
            for index,attachment in enumerate(self.fold_attachments):
                points=in_world(attachment(vertices))*AA
                brush.line([tuple(p) for p in points],fill=123-index*33,width=2,joint='curve')
            self.boot.tint_folds(layer,np.asarray(crease,dtype=np.float32)/255,strength)
        return layer,joints


def trunk_frame(points,phase,bob):
    pelvis=v(464,500)
    angle=math.radians(1.05)*math.sin(TAU*phase-.28)
    return rotated(points,pelvis,pelvis+v(pelvis_drift(phase),bob),angle)


def body_motion(points,phase,bob):
    x,y=points.T; phase_angle=TAU*phase
    torso=trunk_frame(points,phase,bob)
    neck=v(456,230)
    neck_world=trunk_frame(neck[None,:],phase,bob)[0]
    head=rotated(points,neck,neck_world,math.radians(.26)*math.sin(phase_angle-.46))
    # Face, ribbon and ear share a rigid head. Only the neck transition and
    # the distal ponytail are allowed to bend.
    head_weight=1-smooth((y-222)/44)
    tail=smooth((408-x)/224)*smooth((426-y)/92)*smooth((y-86)/107)
    head_weight=np.maximum(head_weight,tail)
    pose=torso*(1-head_weight[:,None])+head*head_weight[:,None]
    skirt=smooth((y-388)/150)*smooth((611-x)/76)
    lateral=np.clip((x-463)/92,-1,1)
    pose[:,0]+=tail*(11.2*math.sin(phase_angle-.76)+1.7*math.sin(2*phase_angle-.38))
    pose[:,1]+=tail*(16.0*math.sin(phase_angle-.71)-2.3*math.cos(2*phase_angle))
    pose[:,0]+=skirt*(5.0*math.sin(phase_angle-.58)+1.1*math.sin(2*phase_angle))
    pose[:,1]+=skirt*(2.5*math.sin(2*phase_angle-.45)-2.9*lateral*math.cos(phase_angle-.22))
    return pose


def cape_motion(points,phase,bob,front):
    x,y=points.T; a=TAU*phase
    result=trunk_frame(points,phase,bob)
    if front:
        free=smooth((472-x)/170)*smooth((y-242)/71)
        result[:,0]+=free*(5.4*math.sin(a-1.03)+.8*math.sin(2*a-.37))
        result[:,1]+=free*(6.5*math.sin(a-.9)+.9*math.sin(2*a-.65))
    else:
        free=np.maximum(smooth((459-x)/214)*smooth((y-258)/185),.28*smooth((y-338)/195))
        result[:,0]+=free*(17*math.sin(a-1.08)+2.2*math.sin(2*a-.55))
        result[:,1]+=free*(20*math.sin(a-.88)-2.6*math.cos(2*a-.23))
    return result


def hair_protection(body):
    pixels=np.asarray(body); r,g,b=pixels[:,:,:3].astype(float).transpose(2,0,1)
    y,x=np.indices(r.shape)
    warm=(r>g+7)&(g>b+12)
    # Traced on the native lock over the collar. The shoulder and the pink
    # quiver feathers remain behind the near arm.
    lock=polygon(NATIVE,[(441,205),(465,205),(469,215),(472,219),(472,234),
        (469,242),(465,247),(461,252),(457,258),(457,264),(460,267),(463,267),
        (466,266),(464,271),(458,272),(453,268),(447,264),(445,258),(448,251),
        (452,247),(456,243),(460,243),(463,240),(461,237),(461,232),(447,228),(441,224)])
    trailing=np.interp(x,[0,145,175,245,280,309,335,357,379,392],
                       [415,408,366,348,337,322,318,303,288,265])
    protect=((y<222)|((x>=473)&(y<233))|((x>=498)&(y<278)&warm)
             |((x<=392)&(y<trailing)&warm)|(np.asarray(lock)>0))
    return matte(body,Image.fromarray(np.where(protect,255,0).astype('uint8')))


def arm_joints(nodes,phase,bob,near):
    sh,el,wr=nodes
    wave,roll=math.cos(TAU*phase),math.sin(TAU*phase)
    same_phase=phase if near else (phase+.5)%1
    same_cos=math.cos(TAU*same_phase)
    shoulder=trunk_frame(sh[None,:],phase,bob)[0]+v(-3.4*same_cos,-1.8*math.sin(TAU*same_phase))
    ankle_x=sample_foot(same_phase).x
    stride=(ankle_x-(464+27*same_cos)+15)/103
    swing=.58*same_cos+.42*stride
    if near:
        wrist=shoulder+v(5-70*swing+2*roll,153-11*wave**2+5.4*roll+10*swing)
    else:
        wrist=shoulder+(wr-sh)+v(-12-22*swing,2.5*roll-5.4*math.cos(2*TAU*phase-.48)-2*wave)
    elbow=joint(shoulder,wrist,np.linalg.norm(el-sh),np.linalg.norm(wr-el),-1)
    return shoulder,elbow,wrist


def arm_vertices(patch,nodes,target,hand_angle=0.):
    sh,el,wr=nodes; shoulder,elbow,wrist=target
    axis=(wr-sh)/np.linalg.norm(wr-sh)
    weight=smooth(((patch.positions-el)@axis+20)/41)[:,None]
    points=patch.positions
    upper=align(points,sh,el,shoulder,elbow)
    lower=align(points,el,wr,elbow,wrist)
    result=upper*(1-weight)+lower*weight
    if hand_angle:
        hand_axis=(wr-el)/np.linalg.norm(wr-el)
        hand=smooth(((points-wr)@hand_axis+2)/20)[:,None]
        result=result*(1-hand)+rotated(lower,wrist,wrist,hand_angle)*hand
    return result


class FarArm:
    """The detailed grip/hand and both floral bow limbs stay together. The
    forearm flexes under the wrist cuff, and the string travels with the bow."""

    def __init__(self,art):
        art=art.copy(); alpha=art.getchannel('A')
        # Both pieces of the drawn string meet behind the sleeve in the
        # original. Replace them with a single taut string when the elbow moves.
        d=ImageDraw.Draw(alpha)
        for path in [[(1337,221),(1278,344),(1204,499)],[(1198,561),(1174,667),(1149,780)]]:
            pts=arm_coords(path,False)
            d.line([tuple(q) for q in pts],fill=0,width=6)
        art.putalpha(alpha)
        shape=[(1041,350),(1200,350),(1202,485),(1224,496),(1272,512),
               (1324,517),(1326,569),(1316,590),(1260,594),(1191,576),
               (1150,561),(1100,515),(1040,514)]
        proximal=polygon(NATIVE,arm_coords(shape,False))
        self.upper=Patch(matte(art,proximal),13)
        tight=proximal.filter(ImageFilter.MinFilter(5))
        distal=matte(art,ImageChops.invert(tight))
        component=distal.getchannel('A').point(lambda k:255 if k>18 else 0)
        seed=tuple(np.round(arm_coords([1347,552],False)).astype(int))
        if component.getpixel(seed)==0:
            raise ValueError('The bow-holding hand is absent at its registration point.')
        ImageDraw.floodfill(component,seed,128)
        distal=matte(distal,component.point(lambda k:255 if k==128 else 0).filter(ImageFilter.MaxFilter(3)))
        self.distal=Patch(distal,17)

    def draw(self,phase,bob):
        target=arm_joints(FAR_ARM,phase,bob,False)
        rotation=.051*math.cos(TAU*phase-.27)+.012*math.sin(2*TAU*phase-.18)
        follow=lambda points:rotated(points,FAR_ARM[2],target[2],rotation)
        endpoints=follow(arm_coords([(1342,212),(1148,783)],False))
        screen=in_world(endpoints)*AA
        plane=Image.new('RGBA',(round(HD*AA),round(HD*AA)))
        ImageDraw.Draw(plane).line([tuple(k) for k in screen],fill=(171,106,71,235),width=1)
        string=np.asarray(plane.convert('RGBa'),dtype=np.float32)/255
        layer=over(string,self.upper.paint_vertices(arm_vertices(self.upper,FAR_ARM,target)))
        grip=follow(arm_coords([[1364,551]],False))[0]
        return over(layer,self.distal.paint(follow)),target,(grip,*endpoints)


def rasterize(pixels):
    alpha=pixels[:,:,3:4]; straight=np.zeros_like(pixels)
    np.divide(pixels[:,:,:3],alpha,out=straight[:,:,:3],where=alpha>.0001)
    straight[:,:,3:4]=alpha
    return Image.fromarray(np.clip(straight*255+.5,0,255).astype('uint8')).resize((HD,HD),Image.Resampling.LANCZOS)


def subtract_cover(pixels,cover):
    return pixels*(1-cover[:,:,3:4])


def keypoints(points,names):
    return {name:in_world(xy).round(3).tolist() for name,xy in zip(names,points)}


class Ranger:
    def __init__(self,directory):
        body,far,near=split_legs(registered_layer(directory,'body'))
        self.body=Patch(body,19)
        self.hair=Patch(hair_protection(body),22)
        self.front=Patch(registered_layer(directory,'cape-front'),16)
        self.back=Patch(registered_layer(directory,'cape-back'),23)
        self.far_leg=Leg(far,FAR_LEG,-1)
        self.near_leg=Leg(near,NEAR_LEG,1)
        self.far_arm=FarArm(registered_layer(directory,'far-arm-bow'))
        self.near_arm=Patch(registered_layer(directory,'near-arm'),12)
        self.fingertip=self.near_arm.attachments(arm_coords([[897,801]],True))

    def frame(self,phase):
        bob=body_drop(phase)
        torso=lambda pts:body_motion(pts,phase,bob)
        front=lambda pts:cape_motion(pts,phase,bob,True)
        back=lambda pts:cape_motion(pts,phase,bob,False)
        far_leg,far_lower=self.far_leg.draw((phase+.5)%1,bob)
        near_leg,near_lower=self.near_leg.draw(phase,bob)
        far_arm,far_upper,bow_marks=self.far_arm.draw(phase,bob)
        near_upper=arm_joints(NEAR_ARM,phase,bob,True)
        hand_vertices=arm_vertices(self.near_arm,NEAR_ARM,near_upper,
                                   math.radians(11)*math.sin(TAU*phase-.78))
        near_arm=self.near_arm.paint_vertices(hand_vertices)
        hair=self.hair.paint(torso)
        layers={'cape-back':self.back.paint(back),'far-arm-bow':far_arm,
                'far-leg':far_leg,'near-leg':near_leg,'body':self.body.paint(torso),
                'near-arm':subtract_cover(near_arm,hair),
                'cape-front':subtract_cover(self.front.paint(front),hair)}
        plates={name:rasterize(layers[name]) for name in ORDER}
        # Actual export is composited from exactly the same registered native
        # plates used by the phase-zero layer inspection.
        frame=Image.new('RGBA',(HD,HD))
        for plate in plates.values():
            frame.alpha_composite(plate)
        skeleton={}
        for side,lower,upper in [('near',near_lower,near_upper),('far',far_lower,far_upper)]:
            skeleton[side]=keypoints([*lower,*upper],
                ['hip','knee','ankle','heel','ball','toe','contact','shoulder','elbow','wrist'])
        skeleton['near'].update(keypoints(self.fingertip(hand_vertices),['fingertip']))
        skeleton['far'].update(keypoints(bow_marks,['grip','bow_top','bow_bottom']))
        cloth={'back_tip':back(np.array([[190.,606.]]))[0],
               'back_upper':back(np.array([[430.,277.]]))[0],
               'front_tip':front(np.array([[288.,330.]]))[0],
               'front_clasp':front(np.array([[484.,267.]]))[0],
               'clasp_on_torso':torso(np.array([[484.,267.]]))[0],
               'hair_tip':torso(np.array([[87.,384.]]))[0],
               'hair_tie':torso(np.array([[391.,110.]]))[0],
               'eye':torso(np.array([[498.,182.]]))[0],
               'face_nose':torso(np.array([[541.,204.]]))[0],
               'skirt_hem':torso(np.array([[548.,513.]]))[0],
               'belt':torso(np.array([[477.,378.]]))[0]}
        skeleton['landmarks']=keypoints(cloth.values(),cloth.keys())
        return frame,plates,skeleton


def strip(frames,count,size):
    result=Image.new('RGBA',(count*size,size))
    for i in range(count):
        cel=frames[Fraction(i,count)]
        if size!=HD:
            cel=cel.resize((size,size),Image.Resampling.LANCZOS)
        result.paste(cel,(i*size,0))
    return result


def contacts(frames,count,width,cols):
    proof=Image.new('RGB',(cols*width,(count//cols)*width))
    for i in range(count):
        f=frames[Fraction(i,count)].resize((width,width),Image.Resampling.LANCZOS)
        bg=Image.new('RGBA',f.size,'#8ba399' if i%2 else '#b6c0af')
        bg.alpha_composite(f)
        proof.paste(bg,(i%cols*width,i//cols*width))
    return proof


def foot_measurements(chain):
    def pitch(start,end):
        dx,dy=np.subtract(chain[end],chain[start])
        return round(math.degrees(math.atan2(dy,dx)),2)

    def flex(start,middle,end):
        first=np.subtract(chain[middle],chain[start])
        second=np.subtract(chain[end],chain[middle])
        cosine=np.dot(first,second)/(np.linalg.norm(first)*np.linalg.norm(second))
        return round(math.degrees(math.acos(np.clip(cosine,-1,1))),2)

    heel_pitch=pitch('heel','ball')
    toe_pitch=pitch('ball','toe')
    return {'hindfoot_pitch_deg':heel_pitch,'forefoot_pitch_deg':toe_pitch,
            'ball_flex_deg':round(heel_pitch-toe_pitch,2),
            'sole_clearance':round(480-chain['contact'][1],2),
            'heel_clearance':round(480-chain['heel'][1],2),
            'knee_flex_deg':flex('hip','knee','ankle'),
            'elbow_flex_deg':flex('shoulder','elbow','wrist')}


def report(frames,poses):
    phase_names=[str(Fraction(i,12)) for i in range(12)]
    evidence={}
    for side in ('near','far'):
        x=np.array([[poses[p][side][name][0] for name in ('wrist','shoulder','ankle','hip')]
                    for p in phase_names])
        offsets=np.stack([x[:,0]-x[:,1],x[:,2]-x[:,3]],axis=1)
        centered=offsets-offsets.mean(axis=0)
        evidence[side]={'neutral_wrist_minus_shoulder_x':round(float(offsets[:,0].mean()),3),
            'neutral_ankle_minus_hip_x':round(float(offsets[:,1].mean()),3),
            'pearson_r_12':round(float(np.corrcoef(*offsets.T)[0,1]),6),
            'sample_offsets_512px':{p:{'wrist':round(float(centered[i,0]),2),
            'ankle':round(float(centered[i,1]),2)} for i,p in enumerate(phase_names)}}
    sheets={}
    for count in COUNTS:
        for size,suffix in ((512,'-hd'),(64,'')):
            ground=[]
            for i in range(count):
                f=frames[Fraction(i,count)]
                if size!=HD:
                    f=f.resize((size,size),Image.Resampling.LANCZOS)
                yy=np.nonzero(np.array(f.getchannel('A'))>=110)[0]
                ground.append(int(yy.max()))
            sheets[f'anime-walk-{count:02d}{suffix}.png']={'width':size*count,'height':size,
                'unique_cells':len({frames[Fraction(i,count)].tobytes() for i in range(count)}),
                'ground_range_at_alpha110':[min(ground),max(ground)]}
    all_phases=sorted(poses,key=Fraction)
    foot_roll={p:{s:foot_measurements(poses[p][s]) for s in ('near','far')} for p in all_phases}
    return {'cycle_seconds':1,'direction':'right','layer_order_back_to_front':ORDER,
            'native_layer_size':NATIVE,'camera_near_arm':'empty, in front of torso',
            'camera_far_arm':'carrying floral bow, behind torso',
            'units':'512px cell; relative x with each side’s 12-sample mean subtracted',
            'evidence':evidence,'sheets':sheets,
            'foot_roll_512':{'floor_y':480,'pitch':'positive points down in the right-facing profile',
                 'contact':'lowest opaque outsole sample after mesh deformation','phases':foot_roll},
            'joint_positions_512':{p:poses[p] for p in all_phases}}


def write_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def write_pixel_keys(path,poses):
    names=('hip','knee','ankle','shoulder','elbow','wrist')
    keys={p:[[[round(coord/8,3) for coord in pose[s][name]] for name in names]
             for s in ('near','far')] for p,pose in poses.items()}
    lines=['  '+json.dumps(p)+': '+json.dumps(rows,separators=(',',':')) for p,rows in keys.items()]
    path.write_text('{\n'+',\n'.join(lines)+'\n}\n',encoding='utf8')


def foot_contacts(proof,poses):
    side_length=192
    board=Image.new('RGB',(side_length*4,side_length*2),'#b5c0ac')
    for row,side in enumerate(('near','far')):
        for column,local in enumerate((0,3,6,9)):
            i=(local+row*6)%12
            chain=poses[str(Fraction(i,12))][side]
            left=round(chain['ankle'][0])-side_length//2
            top=302
            tile=Image.new('RGBA',(side_length,side_length),'#a7b7ab')
            ink=ImageDraw.Draw(tile)
            ink.line((0,480-top,side_length-1,480-top),fill='#75897e',width=1)
            with Image.open(proof/'isolated-legs'/f'{side}-{i:02d}.png') as leg:
                tile.alpha_composite(leg.crop((left,top,left+side_length,top+side_length)))
            ink.text((6,5),f'{side}  {local}/12',fill='#25392d')
            board.paste(tile,(column*side_length,row*side_length))
    board.save(proof/'foot-roll-proof.png')


def render(layer_dir,output,proof=None):
    hero=Ranger(layer_dir)
    poses={}; frames={}
    output.mkdir(parents=True,exist_ok=True)
    for phase in sorted({Fraction(i,n) for n in COUNTS for i in range(n)}):
        f,plates,skeleton=hero.frame(float(phase))
        frames[phase]=f; poses[str(phase)]=skeleton
        if proof and (phase*12).denominator==1:
            i=int(phase*12)
            dest=proof/'isolated-legs'
            dest.mkdir(parents=True,exist_ok=True)
            for side in ('near','far'):
                plates[side+'-leg'].save(dest/f'{side}-{i:02d}.png')
            if i%3==0:
                f.save(proof/f'contact-{i:02d}.png')
        if proof and phase==0:
            dest=proof/'layers'
            dest.mkdir(parents=True,exist_ok=True)
            for name,plate in plates.items():
                plate.save(dest/(name+'.png'))
            f.save(proof/'phase-0-composite.png')
            write_json(dest/'painter-order.json',list(ORDER))
    for count in COUNTS:
        for size,suffix in ((HD,'-hd'),(64,'')):
            strip(frames,count,size).save(output/f'anime-walk-{count:02d}{suffix}.png')
    validation=report(frames,poses)
    if proof:
        contacts(frames,4,256,4).save(proof/'walk-04-proof.png')
        contacts(frames,12,205,6).save(proof/'walk-12-proof.png')
        foot_contacts(proof,poses)
        write_pixel_keys(proof/'pixel-pose-keys.json',poses)
        write_json(proof/'joint-coordinates.json',poses)
        write_json(proof/'gait-verification.json',validation)
    return validation


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--preview-dir',type=Path)
    parser.add_argument('--layer-dir',type=Path,default=LAYER_DIR)
    parser.add_argument('--output-dir',type=Path,default=ASSETS)
    args=parser.parse_args()
    if args.layer_dir==LAYER_DIR:
        extract_arms(ART/'approved-design.png',LAYER_DIR)
    validation=render(args.layer_dir,args.output_dir,args.preview_dir)
    if args.output_dir==ASSETS and args.layer_dir==LAYER_DIR:
        write_json(ART/'gait-verification.json',validation)
        from build_previews import build_previews
        build_previews()


if __name__=='__main__':
    main()
