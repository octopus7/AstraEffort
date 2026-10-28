"""Copy finished modules and generate repeatable station placements."""
from pathlib import Path
import json, math, shutil

ROOT=Path(__file__).resolve().parents[1]
dest=ROOT/'viewer'/'assets';dest.mkdir(parents=True,exist_ok=True)
entries=[]
def add(module,source,short,placements,double=False):
    src=ROOT/'modules'/module/source
    if not src.exists():
        print('Not yet available:',src)
        return
    shutil.copy2(src,dest/short)
    entries.append({'file':short,'doubleSided':double,'placements':[{'position':p} if len(p)==3 else {'position':p[:3],'rotation':[0,p[3],0]} for p in placements]})

bays=8
places=[[0,0,n*6] for n in range(bays)]
add('facade','station_facade.glb','facade.glb',[[20,0,0]])
add('props','facade_canopy.glb','facade_canopy.glb',[[20,0,0]])
add('forecourt','station_forecourt.glb','forecourt.glb',[[20,0,0]])
add('platform','platform_track_bay.glb','platform.glb',places)
add('shed','train_shed_bay.glb','shed.glb',places,True)
add('shed','train_shed_end_frame.glb','shed_end.glb',[[0,0,47.72]],True)
add('locomotive','steam_locomotive.glb','locomotive.glb',[[-4,.24,2]])
add('tender','coal_tender.glb','tender.glb',[[-4,.24,14.95]])
add('carriage','victorian_carriage.glb','carriage.glb',[[-4,.24,21.85]])
add('props','station_lamp.glb','lamp.glb',[[1.1,.9,4], [1.1,.9,16], [1.1,.9,28], [1.1,.9,40], [15,0,-7], [25,0,-7]])
add('props','station_bench.glb','bench.glb',[[0,.9,8,math.pi/2], [0,.9,21,math.pi/2], [0,.9,34,math.pi/2], [8,.9,10,math.pi/2], [8,.9,32,math.pi/2]])
add('props','luggage_trolley.glb','trolley.glb',[[.0,.9,13,math.pi/2],[8,.9,22,math.pi/2]])
add('props','wall_clock.glb','clock.glb',[[9.2,4.3,0]])
add('cargo','platform_sign.glb','platform_sign.glb',[[0,.9,2.8], [0,.9,24.5]])
add('cargo','cargo_crate.glb','cargo_crate.glb',[[8,.9,16],[8.5,.9,17],[-8,.9,30]])
add('cargo','cargo_barrel.glb','cargo_barrel.glb',[[8,.9,18],[-8,.9,28]])

(dest/'manifest.json').write_text(json.dumps({'bays':bays,'assets':entries},ensure_ascii=False,indent=2),encoding='utf-8')
print('Viewer assets:',len(entries),'placements:',sum(len(e['placements']) for e in entries))
