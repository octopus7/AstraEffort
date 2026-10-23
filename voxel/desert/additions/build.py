"""Original water-treatment skid; native voxel geometry authored by main."""
from pathlib import Path
import sys, json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'_tools'))
from voxelkit import Grid,Asset,reduce_half

PALETTE=[(0,0,0,0),(210,182,136),(239,217,178),(156,132,101),(205,99,36),(149,66,30),(64,114,116),(37,77,82),(53,56,56),(35,39,41),(88,92,89),(148,155,146),(43,72,84),(100,139,146),(39,88,109),(255,225,150)]

def make_assets():
    g=Grid((128,96,112),PALETTE)
    # Four isolating feet and open-sided structural skid.
    for x in (10,118):
        for y in (10,86):
            g.roundbox((x-7,y-7,0),(x+7,y+7,5),2,9)
            g.box((x-4,y-4,4),(x+4,y+4,13),10)
    g.roundbox((4,4,9),(124,92,15),3,1)
    g.box((10,12,12),(118,84,16),10)
    for y in (14,38,62,82):g.box((8,y,15),(120,y+3,17),2)
    # Distinct filtration vessels with actual space between them.
    for x in (33,82):
        for dx in (-10,10):g.box((x+dx-3,63,15),(x+dx+3,73,31),8)
        g.cylinder((x,68,58),18,58,2,2)
        g.ellipsoid((x,68,31),(18,18,9),1)
        g.ellipsoid((x,68,87),(18,18,12),2)
        for z in (43,78):g.cylinder((x,68,z),18.5,6,2,6)
        g.cylinder((x,68,74),18.7,3,2,4)
        for z in (35,84):g.torus((x,68,z),18,1.8,2,10)
        g.cylinder((x,68,97),11,5,2,8)
        g.cylinder((x,68,101),6,5,2,10)
        g.roundbox((x-3,65,103),(x+3,71,108),1,4)
        # Brackets occupy only the narrow side face.
        g.roundbox((x+16,64,43),(x+21,72,51),1,4)
        g.cylinder((x+21,68,47),2,2,0,11)
    # Rear overhead connection, attached to both vessel shoulders.
    for a,b in [((15,68,87),(12,68,100)),((12,68,100),(33,68,100)),((33,68,100),(82,68,100)),((82,68,100),(103,68,100)),((103,68,100),(103,68,38))]:g.beam(a,b,3,8)
    for x in (18,56,98):g.cylinder((x,68,100),4.5,4,0,4)
    # Pump assembly: stout electric motor, cooling ribs, circular pump casing.
    g.roundbox((16,17,16),(49,37,22),2,3)
    g.cylinder((29,27,31),10,26,0,6)
    for x in range(19,42,4):g.cylinder((x,27,31),11,2,0,7)
    g.cylinder((45,27,31),13,7,0,2)
    g.cylinder((49,27,31),9,4,0,10)
    g.roundbox((25,21,41),(37,33,48),2,6)
    g.box((28,20,43),(34,22,47),4)
    # Input and output pipes join actual pump casing and cartridge headers.
    for a,b in [((6,27,17),(6,27,31)),((6,27,31),(18,27,31)),((50,27,31),(54,27,31)),((54,27,31),(54,42,31)),((54,42,31),(54,42,59)),((54,42,59),(98,42,59)),((98,42,59),(103,68,59))]:g.beam(a,b,2.8,8)
    for x in (11,51):g.cylinder((x,27,31),4.5,4,0,4)
    # Three membrane cartridges separated by five-cell access gaps.
    for x in (62,78,94):
        g.cylinder((x,27,36),5.5,32,2,2)
        for z in (20,50):g.cylinder((x,27,z),6.5,4,2,4)
        g.cylinder((x,27,54),3.5,5,2,10)
        g.beam((x,27,54),(x,42,59),2.3,8)
        g.beam((x,27,20),(x,27,17),2.5,8)
    g.beam((60,27,17),(108,27,17),2.5,8)
    g.beam((108,27,17),(108,12,17),2.5,8)
    g.beam((108,12,17),(120,12,17),2.5,8)
    g.cylinder((119,12,17),4.5,4,0,4)
    # Three genuine annular handwheels with two crossed spokes.
    for x,y,z in ((10,27,39),(73,42,67),(108,16,25)):
        g.cylinder((x,y,z-3),1.8,10,2,10)
        g.torus((x,y,z+3),4.5,1.3,2,4)
        g.beam((x-4.5,y,z+3),(x+4.5,y,z+3),1,4)
        g.beam((x,y-4.5,z+3),(x,y+4.5,z+3),1,4)
    # A service console to the right, controls face forward (-Y).
    g.roundbox((108,38,16),(124,57,63),3,2)
    g.box((112,36,43),(121,39,58),8)
    g.box((113,35,48),(120,37,56),13)
    for x,c in ((113,4),(119,6)):g.cylinder((x,36,43),1.8,2,1,c)
    g.box((112,37,24),(120,39,37),6)
    g.box((120,36,29),(122,38,33),10)
    notes=['Original desert water-treatment skid, main-authored; original theme palette retained by value.', 'Two vessels, motor-pump, three membrane cartridges, connected manifolds and three handwheels.', 'Static colored representation of treatment equipment, not a fluid simulation; opaque palette materials.', 'Conservative half reduction only; no manual half-grid modifications.']
    return [Asset('water_purifier','사막 정수 장치',g,.04,notes)]

def check_features():
    a=make_assets()[0];out=[]
    for name,g,s in [('large',a.grid,1),('half',reduce_half(a.grid),2)]:
        occupied=lambda p: bool(g.data[tuple(int(v//s) for v in p)])
        probes={'left_vessel':(33,68,58),'right_vessel':(82,68,58),'pump':(29,27,31),'cartridge_1':(62,27,36),'cartridge_2':(78,27,36),'cartridge_3':(94,27,36),'header':(73,42,59),'console':(116,45,30)}
        for label,p in probes.items():assert occupied(p),(name,label)
        for label,p in {'vessel_separation':(57,68,60),'cartridge_gap':(70,27,36)}.items():assert not occupied(p),(name,label)
        out.append({'variant':name,'passed':True,'occupied_probes':list(probes),'empty_probes':['vessel_separation','cartridge_gap']})
    return out

if __name__=='__main__':
    from blender_pipeline import run_theme
    root=Path(__file__).resolve().parent
    (root/'feature_validation.json').write_text(json.dumps(check_features(),indent=2),encoding='utf-8')
    (root/'palette.json').write_text(json.dumps({'colors':PALETTE,'source':'Own desert theme palette, values retained; geometry original.'},indent=2),encoding='utf-8')
    run_theme(root,make_assets())
