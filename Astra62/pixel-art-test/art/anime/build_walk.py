"""Render the approved elf from separately painted arms, legs, torso and cape.

Run with Python, Pillow and NumPy. --preview-dir adds registered transparency
plates, contact sheets, tracked joint coordinates and cape-motion landmarks.
"""

import argparse
import json
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from extract_arms import ART, NATIVE, arm_coords, extract_arms


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

    def paint(self, transform):
        size = round(HD*AA)
        screen = in_world(transform(self.positions))*AA
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



def track(keys,phase):
    return np.array([np.interp(phase,keys[:,0],column) for column in keys.T[1:]])


# In-phase heel contact, flat stance, toe-off, lift, passing and recovery.
FOOT=np.array([(0,579,-26,0),(.09,530,-4,0),(.24,455,0,0),(.36,392,5,0),
               (.44,338,15,0),(.5,289,26,0),(.58,288,36,16),(.66,318,30,43),
               (.75,389,10,57),(.84,473,-10,48),(.925,541,-22,24),(1,579,-26,0)])
BOB=np.array([(0,0),(.1,7),(.21,1),(.31,-7),(.405,-8),(.5,0)])
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


class Leg:
    def __init__(self,artwork,nodes,angle,side):
        self.patch=Patch(artwork,18)
        self.nodes,self.angle,self.side=nodes,angle,side
        hip,knee,ankle=nodes
        axis=(ankle-hip)/np.linalg.norm(ankle-hip)
        self.knee=smooth(((self.patch.positions-knee)@axis+28)/56)[:,None]
        axis=(ankle-knee)/np.linalg.norm(ankle-knee)
        foot=smooth(((self.patch.positions-ankle)@axis+22)/46)
        self.foot=np.maximum(foot,smooth((self.patch.positions[:,1]-ankle[1]+1)/33))[:,None]
        alpha=np.asarray(artwork)[:,:,3]
        yy,xx=np.where(alpha>90)
        points=np.stack((xx,yy),axis=1)
        self.sole=points[yy>ankle[1]]-ankle

    def draw(self,phase,bob):
        x,angle,lift=track(FOOT,phase)
        hip,knee,ankle=self.nodes
        rotation=math.radians(angle-self.angle)
        support=np.max(self.sole[:,0]*math.sin(rotation)+self.sole[:,1]*math.cos(rotation))
        end=v(x,GROUND-lift-support)
        start=v(464+28*math.cos(TAU*phase)+self.side*3,hip[1]+bob)
        middle=joint(start,end,np.linalg.norm(knee-hip),np.linalg.norm(ankle-knee),1)
        def flex(points):
            upper=align(points,hip,knee,start,middle)
            lower=align(points,knee,ankle,middle,end)
            foot=rotated(points,ankle,end,rotation)
            limb=upper*(1-self.knee)+lower*self.knee
            return limb*(1-self.foot)+foot*self.foot
        return self.patch.paint(flex),(start,middle,end)


def body_motion(points,phase,bob):
    x,y=points.T; roll=math.sin(TAU*phase)
    hair=smooth((401-x)/224)*smooth((421-y)/84)*smooth((y-83)/101)
    skirt=smooth((y-384)/124)*smooth((610-x)/75)
    dx=2.5*roll*smooth((529-y)/220)+hair*9.2*math.sin(TAU*phase-.7)+skirt*3*roll
    dy=bob+hair*13*math.sin(TAU*phase-.52)+skirt*1.7*math.sin(2*TAU*phase-.25)
    return np.stack((x+dx,y+dy),axis=1)


def cape_motion(points,phase,bob,front):
    x,y=points.T; roll=math.sin(TAU*phase)
    if front:
        free=smooth((460-x)/164)*smooth((y-229)/66)
        dx=2.5*roll+free*4*math.sin(TAU*phase-1.1)
        dy=bob+free*4.7*math.sin(TAU*phase-.77)
    else:
        free=np.maximum(smooth((462-x)/212)*smooth((y-239)/190),.22*smooth((y-335)/196))
        dx=2.2*roll*(1-free)+free*14*math.sin(TAU*phase-1.05)
        dy=bob+free*17*math.sin(TAU*phase-.8)
    return np.stack((x+dx,y+dy),axis=1)


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
    shoulder=sh+v(2.5*roll,bob)
    same_phase=phase if near else (phase+.5)%1
    same_cos=math.cos(TAU*same_phase)
    ankle_x=track(FOOT,same_phase)[0]
    stride=(ankle_x-(464+28*same_cos)+30)/117
    swing=.62*same_cos+.38*stride
    if near:
        wrist=v(sh[0]+3-70*swing,sh[1]+158+bob-10*wave**2+2*roll)
    else:
        wrist=wr+v(-8-25*swing,bob-4*math.cos(2*TAU*phase-.48))
    elbow=joint(shoulder,wrist,np.linalg.norm(el-sh),np.linalg.norm(wr-el),-1)
    return shoulder,elbow,wrist


def arm_flex(patch,nodes,target):
    sh,el,wr=nodes; shoulder,elbow,wrist=target
    axis=(wr-sh)/np.linalg.norm(wr-sh)
    weight=smooth(((patch.positions-el)@axis+20)/41)[:,None]
    def transformed(points):
        upper=align(points,sh,el,shoulder,elbow)
        lower=align(points,el,wr,elbow,wrist)
        return upper*(1-weight)+lower*weight
    return patch.paint(transformed)


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
        rotation=.042*math.cos(TAU*phase-.14)
        follow=lambda points:rotated(points,FAR_ARM[2],target[2],rotation)
        endpoints=follow(arm_coords([(1342,212),(1148,783)],False))
        screen=in_world(endpoints)*AA
        plane=Image.new('RGBA',(round(HD*AA),round(HD*AA)))
        ImageDraw.Draw(plane).line([tuple(k) for k in screen],fill=(171,106,71,235),width=1)
        string=np.asarray(plane.convert('RGBa'),dtype=np.float32)/255
        layer=over(string,arm_flex(self.upper,FAR_ARM,target))
        return over(layer,self.distal.paint(follow)),target


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
        self.far_leg=Leg(far,FAR_LEG,26,-1)
        self.near_leg=Leg(near,NEAR_LEG,-26,1)
        self.far_arm=FarArm(registered_layer(directory,'far-arm-bow'))
        self.near_arm=Patch(registered_layer(directory,'near-arm'),12)

    def frame(self,phase):
        bob=track(BOB,phase%.5)[0]
        torso=lambda pts:body_motion(pts,phase,bob)
        front=lambda pts:cape_motion(pts,phase,bob,True)
        back=lambda pts:cape_motion(pts,phase,bob,False)
        far_leg,far_lower=self.far_leg.draw((phase+.5)%1,bob)
        near_leg,near_lower=self.near_leg.draw(phase,bob)
        far_arm,far_upper=self.far_arm.draw(phase,bob)
        near_upper=arm_joints(NEAR_ARM,phase,bob,True)
        near_arm=arm_flex(self.near_arm,NEAR_ARM,near_upper)
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
            skeleton[side]=keypoints([*lower,*upper],['hip','knee','ankle','shoulder','elbow','wrist'])
        cloth={'back_tip':back(np.array([[190.,606.]]))[0],
               'back_upper':back(np.array([[430.,277.]]))[0],
               'front_tip':front(np.array([[288.,330.]]))[0],
               'front_clasp':front(np.array([[484.,267.]]))[0],
               'hair_tip':torso(np.array([[87.,384.]]))[0]}
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
    return {'cycle_seconds':1,'direction':'right','layer_order_back_to_front':ORDER,
            'native_layer_size':NATIVE,'camera_near_arm':'empty, in front of torso',
            'camera_far_arm':'carrying floral bow, behind torso',
            'units':'512px cell; relative x with each side’s 12-sample mean subtracted',
            'evidence':evidence,'sheets':sheets,'joint_positions_512':{p:poses[p] for p in phase_names}}


def write_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def render(layer_dir,output,proof=None):
    hero=Ranger(layer_dir)
    poses={}; frames={}
    output.mkdir(parents=True,exist_ok=True)
    for phase in sorted({Fraction(i,n) for n in COUNTS for i in range(n)}):
        f,plates,skeleton=hero.frame(float(phase))
        frames[phase]=f; poses[str(phase)]=skeleton
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
