import bpy,json,struct,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
raw=(ROOT/'RabbitBike.glb').read_bytes();p=12;doc=None;binary=None
while p<len(raw):
    n,t=struct.unpack_from('<I4s',raw,p);p+=8
    if t==b'JSON':doc=json.loads(raw[p:p+n].decode())
    elif t==b'BIN\0':binary=raw[p:p+n]
    p+=n
im=doc['images'][0];bv=doc['bufferViews'][im['bufferView']];a=bv.get('byteOffset',0);data=binary[a:a+bv['byteLength']]
path=ROOT/'validation'/'embedded_atlas_probe.png';path.write_bytes(data)
external=ROOT/'textures'/'RabbitBike_BaseColor_4096.png'
packed=bpy.data.images['RabbitBike_BaseColor_4096']
report={'external_png_sha256':hashlib.sha256(external.read_bytes()).hexdigest(),'glb_png_sha256':hashlib.sha256(data).hexdigest(),'packed_png_sha256':hashlib.sha256(bytes(packed.packed_file.data)).hexdigest() if packed.packed_file else None}
e=bpy.data.images.load(str(external),check_existing=False);g=bpy.data.images.load(str(path),check_existing=False)
ep=np.empty(len(e.pixels),dtype=np.float32);gp=np.empty(len(g.pixels),dtype=np.float32);e.pixels.foreach_get(ep);g.pixels.foreach_get(gp)
report['pixel_max_absolute_difference']=float(np.max(np.abs(ep-gp)));report['pixel_mean_absolute_difference']=float(np.mean(np.abs(ep-gp)))
print('TEXTURE_BINDING_AUDIT',json.dumps(report),flush=True)
(ROOT/'validation'/'texture_binding_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
