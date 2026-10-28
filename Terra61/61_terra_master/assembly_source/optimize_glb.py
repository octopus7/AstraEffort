"""Shrink embedded opaque base-colour PNGs to high-quality JPEG.

Geometry, transforms, UVs, original dimensions, and alpha-bearing images stay
unchanged. The original separately supplied module files remain untouched.
"""
from pathlib import Path
from io import BytesIO
import json
from PIL import Image
from pygltflib import GLTF2
import trimesh

ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'output'/'riverdale_station_assembled.glb'
dst=ROOT/'output'/'riverdale_station_assembled_optimized.glb'
gltf=GLTF2().load_binary(str(src))
old_blob=gltf.binary_blob()
assert all(view.buffer == 0 for view in gltf.bufferViews)
image_by_view={image.bufferView:image for image in gltf.images if image.bufferView is not None}
new_blob=bytearray();converted=0
for index,view in enumerate(gltf.bufferViews):
    old_start=view.byteOffset or 0
    raw=old_blob[old_start:old_start+view.byteLength]
    img_desc=image_by_view.get(index)
    if img_desc is not None and img_desc.mimeType == 'image/png':
        img=Image.open(BytesIO(raw))
        if img.mode in ('RGB','L') and len(raw)>30000:
            buf=BytesIO()
            img.convert('RGB').save(buf,format='JPEG',quality=94,subsampling=0,optimize=True)
            jpeg=buf.getvalue()
            if len(jpeg)<len(raw):
                raw=jpeg;img_desc.mimeType='image/jpeg';converted+=1
    while len(new_blob)%4:new_blob.append(0)
    view.byteOffset=len(new_blob)
    view.byteLength=len(raw)
    new_blob.extend(raw)
while len(new_blob)%4:new_blob.append(0)
gltf.buffers[0].byteLength=len(new_blob)
gltf.set_binary_blob(bytes(new_blob))
gltf.save_binary(str(dst))
old=trimesh.load(src,force='scene',process=False)
new=trimesh.load(dst,force='scene',process=False)
assert len(old.graph.nodes_geometry)==len(new.graph.nodes_geometry)
assert len(old.geometry)==len(new.geometry)
assert all((old.bounds-new.bounds).ravel()==0)
assert sum(len(x.faces) for x in old.geometry.values())==sum(len(x.faces) for x in new.geometry.values())
check=GLTF2().load_binary(str(dst))
assert all(not image.uri for image in check.images)
assert any(image.mimeType=='image/jpeg' for image in check.images)
source_check=GLTF2().load_binary(str(src))
source_binary=source_check.binary_blob(); destination_binary=check.binary_blob()
for i,original_view in enumerate(source_check.bufferViews):
    if i in image_by_view:
        continue
    new_view=check.bufferViews[i]
    old_start=original_view.byteOffset or 0; new_start=new_view.byteOffset or 0
    assert source_binary[old_start:old_start+original_view.byteLength] == destination_binary[new_start:new_start+new_view.byteLength], f'Non-image buffer view {i} changed'
report={'original_bytes':src.stat().st_size,'optimized_bytes':dst.stat().st_size,'converted_opaque_textures':converted,'geometry_changed':False,'alpha_textures_preserved':True,'quality':94,'chroma_subsampling':0}
(ROOT/'output'/'optimization_stats.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
