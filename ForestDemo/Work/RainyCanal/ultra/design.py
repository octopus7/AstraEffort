"""New RainyCanal design; all coordinates metres, Z up, north +Y."""
CANAL_HALF=6.0
WATER_Z=-.85
BRIDGES=[('SM_StoneBridge',0,-15),('SM_TimberBridge',0,28)]
BUILDINGS=[
 ('SM_CanalHouseA',-20,-35,90),('SM_CanalShop',-20,-10,90),
 ('SM_CanalHouseB',-20,13,90),('SM_CanalHouseA',-20,37,90),
 ('SM_CanalHouseB',20,-35,-90),('SM_CanalHouseA',20,-10,-90),
 ('SM_CanalShop',20,13,-90),('SM_CanalHouseB',20,37,-90),
]
PUDDLES=[(-11,-27,3.3,1.7),(-11,-4,2.8,1.4),(11,8,3.4,1.5),(11,34,2.5,1.7),(-31,-15,2.7,1.8),(32,28,3.1,1.8)]
def path_distance(x,y):
    quay=abs(abs(x)-10.5)-4.5
    lane=min(abs(y+15)-3.5,abs(y-28)-3.0)
    outer=abs(abs(x)-32)-2.1
    door_y=min(abs(y-a) for a in (-35,-10,13,37))
    doorstep=max(abs(abs(x)-16.5)-2,door_y-1.25)
    return min(quay,lane,outer,doorstep)
def building_clear(x,y,margin=0):
    return all(abs(x-bx)>4.5+margin or abs(y-by)>5+margin for _,bx,by,_ in BUILDINGS)
