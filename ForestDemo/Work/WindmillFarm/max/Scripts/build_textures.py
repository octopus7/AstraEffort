"""Original mathematical surface textures. No external image inputs."""
from pathlib import Path
import math, random, struct, zlib, json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Source/Textures'
OUT.mkdir(parents=True,exist_ok=True)
SIZE=512

def png(path, rows):
    def chunk(name,data):
        return struct.pack('!I',len(data))+name+data+struct.pack('!I',zlib.crc32(name+data)&0xffffffff)
    raw=b''.join(b'\0'+bytes(row) for row in rows)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',SIZE,SIZE,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))

for name in ['Plaster','Wood','Stone','Earth','Grass','Clay','Canvas','Straw']:
    rows=[]
    for y in range(SIZE):
        row=[]
        v=y/SIZE*math.tau
        for x in range(SIZE):
            u=x/SIZE*math.tau
            broad=math.sin(3*u+math.sin(2*v))*math.sin(4*v+0.5*math.sin(3*u))
            fine=math.sin(43*u+5*math.sin(v))*math.cos(37*v+3*math.sin(u))
            value=.92+.035*broad+.012*fine
            if name=='Wood':
                grain=math.sin(31*u+1.1*math.sin(3*v)+.4*math.sin(9*v))
                value=.87+.06*broad+.045*grain+.012*fine
            elif name=='Stone':
                value=.86+.08*broad+.028*math.sin(15*u+math.sin(19*v))+.015*fine
            elif name=='Earth': value=.84+.09*broad+.035*fine
            elif name=='Grass': value=.88+.065*broad+.028*fine
            elif name=='Clay': value=.9+.04*broad+.02*fine
            elif name=='Canvas': value=.9+.022*math.sin(160*u)+.022*math.sin(160*v)+.02*broad
            elif name=='Straw': value=.88+.045*math.sin(41*u+2*math.sin(v))+.04*broad
            q=max(0,min(255,round(value*255)))
            row += [q,q,q]
        rows.append(row)
    png(OUT/(name+'.png'),rows)
print(json.dumps({'textures':[p.name for p in sorted(OUT.glob('*.png'))],'size':[SIZE,SIZE]}))
