"""Continuous hindfoot, vamp and toe deformation in the drawing's sole frame."""

import math

import numpy as np


def smooth(value):
    value=np.clip(value,0,1)
    return value*value*(3-2*value)


def direction(vector):
    return vector/np.linalg.norm(vector)


def rotate(points,angle):
    c,s=np.cos(angle),np.sin(angle)
    x,y=points.T
    return np.column_stack((c*x-s*y,s*x+c*y))


class Boot:
    """Landmarks lie on each differently angled illustrated outsole.

    Sole X is measured along the boot's own heel/ball/toe axis. The broad
    arch transitions from the articulated heel into the planted forefoot.
    The leather above it shortens toward the inside of the bend.
    """

    def __init__(self,artwork,ankle,near):
        self.ankle=ankle
        if near:
            self.heel=np.array([579.,842.]); self.ball=np.array([630.,825.]); self.toe=np.array([678.,800.])
            self.crease_paths=[[(597,788),(604,790),(611,789),(616,787)],
                               [(598,794),(604,796),(610,795)]]
        else:
            self.heel=np.array([239.,796.]); self.ball=np.array([283.,835.]); self.toe=np.array([328.,837.])
            self.crease_paths=[[(266,804),(272,807),(280,807),(284,805)],
                               [(267,811),(274,813),(280,812)]]
        back=direction(self.ball-self.heel); front=direction(self.toe-self.ball)
        self.axis=direction(back+front)
        self.normal=np.array([-self.axis[1],self.axis[0]])
        self.front_axis=front
        self.front_normal=np.array([-front[1],front[0]])
        self.hind_angle=math.atan2(back[1],back[0])
        self.fore_angle=math.atan2(front[1],front[0])
        self.hind_length=np.linalg.norm(self.ball-self.heel)
        self.toe_length=np.linalg.norm(self.toe-self.ball)
        alpha=np.asarray(artwork.getchannel('A'))
        ys,xs=np.nonzero(alpha>105)
        pixels=np.stack((xs,ys),axis=1)
        # All possible plantar contact texels, including the outsole edges.
        self.sole_pixels=pixels[ys>ankle[1]-4]
        relative=self.sole_pixels-self.ball
        u=relative@self.front_axis
        normal=relative@self.front_normal
        self.stations=np.arange(0,self.toe_length+1,1.)
        profile=np.array([max(normal[np.abs(u-s)<1.4],default=0.) for s in self.stations])
        base=np.linspace(profile[0],profile[-1],len(profile))
        self.rocker=np.clip(profile-base,-1.5,4.8)

    def local(self,points,foot):
        heel_angle=math.radians(foot.heel_deg)-self.hind_angle
        toe_angle=math.radians(foot.toe_deg)-self.fore_angle
        delta=points-self.ball
        length=delta@self.axis
        height=np.maximum(0,-delta@self.normal)
        # The flex line runs obliquely up through the vamp. Heel and toe
        # maintain their full painted length on opposite sides of that line.
        transition=smooth((length-.13*np.minimum(height,37)+.39*self.hind_length)/(.68*self.hind_length))
        angle=heel_angle+(toe_angle-heel_angle)*transition
        plantar=delta@self.front_axis
        loaded=smooth((15-abs(foot.toe_deg))/12)*smooth((10-foot.lift)/10)
        pressure=loaded*smooth(plantar/6)*smooth((self.toe_length-plantar)/7)
        flex=pressure*np.interp(plantar,self.stations,self.rocker,left=0.,right=0.)
        delta=delta-flex[:,None]*self.front_normal
        curl=smooth((foot.heel_deg-foot.toe_deg-3)/40)
        folded=np.exp(-((length+3)/(.41*self.hind_length))**2)
        squeeze=np.minimum(height,35)*.15*curl*folded*smooth(height/12)
        delta=delta+squeeze[:,None]*self.normal
        joint_offset=rotate((self.ball-self.ankle)[None,:],heel_angle)[0]
        return joint_offset+rotate(delta,angle)

    def tint_folds(self,rgba,crease_pixels,strength):
        """Darken two narrow moving folds only inside painted leather."""
        alpha=rgba[:,:,3:4]
        amount=crease_pixels[:,:,None]*strength
        pigment=np.array([.355,.195,.155],dtype=np.float32)
        rgba[:,:,:3]=rgba[:,:,:3]*(1-amount)+pigment*alpha*amount
