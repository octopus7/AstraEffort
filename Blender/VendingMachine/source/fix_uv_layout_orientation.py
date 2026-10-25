"""One-time display correction for the original diagnostic PNG (UV V points up).
The finalizer now writes the corrected convention directly; UV coordinates,
numeric validation, packed textures, blend and GLB are not changed here.
"""
import json,struct,zlib,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];marker=ROOT/'validation/uv_png_orientation.json'
if marker.exists():raise SystemExit('UV diagnostic PNG orientation already corrected.')
path=ROOT/'validation/UV_Layout_4096.png';raw=path.read_bytes();pos=8;compressed=b'';header=None
while pos<len(raw):
    n=struct.unpack_from('>I',raw,pos)[0];kind=raw[pos+4:pos+8];data=raw[pos+8:pos+8+n];pos+=n+12
    if kind==b'IHDR':header=data
    if kind==b'IDAT':compressed+=data
w,h,depth,kind,*_=struct.unpack('>IIBBBBB',header);assert depth==8 and kind==2
rows=zlib.decompress(compressed);stride=1+3*w;assert len(rows)==stride*h
assert all(rows[i*stride]==0 for i in range(h))
flipped=b''.join(rows[i*stride:(i+1)*stride] for i in range(h-1,-1,-1))
def chunk(k,data):return struct.pack('>I',len(data))+k+data+struct.pack('>I',zlib.crc32(k+data)&0xffffffff)
out=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)+chunk(b'IDAT',zlib.compress(flipped,6))+chunk(b'IEND',b'')
path.write_bytes(out)
marker.write_text(json.dumps({'timestamp_utc':datetime.now(timezone.utc).isoformat(),'uv_png_convention':'U right, V up, matching Blender atlas display','coordinates_and_numeric_validation_unchanged':True,'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':hashlib.sha256(out).hexdigest()},indent=2),encoding='utf8')
