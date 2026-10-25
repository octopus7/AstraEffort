"""Original WindmillFarm layout. Metres, x east, y north, z up."""
import math
PATHS=[([(-7,-50),(-10,-36),(-8,-25),(-4,-15),(-3,-5),(-6,5),(-6,11)],2.5),
       ([(0,-4),(9,-1),(17,5),(24,10),(33,8),(43,2),(50,0)],2.2),
       ([(-7,-23),(-17,-22),(-29,-19),(-35,-10),(-34,3)],1.6),
       ([(10,-1),(15,-12),(18,-25),(24,-37)],1.4)]
FIELDS=[{'center':(-26,-29),'size':(17,13),'kind':'wheat'},
        {'center':(-28,-8),'size':(15,14),'kind':'wheat'},
        {'center':(25,-22),'size':(13,16),'kind':'vegetable'},
        {'center':(8,-32),'size':(8,11),'kind':'vegetable'}]
MILL=(-6,13)
BARN=(23,16)
SHED=(34,3)

def height(x,y):
    # Near-flat central buildings and paths, slightly undulating pastures.
    edge=min(1,max(0,(max(abs(x),abs(y))-25)/20))
    return .10*math.sin(x*.13)*math.cos(y*.09)+edge*(.50+.38*math.sin(x*.10+y*.12))

def path_distance(x,y):
    best=999
    for points,width in PATHS:
        for a,b in zip(points,points[1:]):
            dx,dy=b[0]-a[0],b[1]-a[1]
            t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
            best=min(best,math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)-width)
    # Working court softly merges with the path network.
    best=min(best,(math.hypot(x/12,(y-1)/9)-1)*8)
    return best

def in_field(x,y,pad=0):
    return any(abs(x-f['center'][0])<f['size'][0]/2+pad and abs(y-f['center'][1])<f['size'][1]/2+pad for f in FIELDS)
