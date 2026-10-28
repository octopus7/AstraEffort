#!/usr/bin/env python3
"""Build a single 20x10m forecourt slab with embedded AI paving material."""
from pathlib import Path
from PIL import Image
import numpy as np
import trimesh, json, shutil
ROOT=Path(__file__).resolve().parent
TEX=ROOT/'textures';TEX.mkdir(exist_ok=True)
source=ROOT.parents[1]/'materials'/'ai_worn_platform_paving.png'
local=TEX/'ai_worn_platform_paving.png'
if source.exists() and source.resolve()!=local.resolve():shutil.copy2(source,local)
if not local.exists():raise FileNotFoundError('The supplied AI paving image is required.')
# Bake four mirrored copies into one texture tile. This preserves continuity at
# boundaries even when a generic importer replaces GLB sampler settings.
im=Image.open(local).convert('RGB').resize((1024,768),Image.Resampling.LANCZOS)
tile=Image.new('RGB',(2048,1536))
tile.paste(im,(0,0));tile.paste(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(1024,0))
tile.paste(im.transpose(Image.Transpose.FLIP_TOP_BOTTOM),(0,768))
tile.paste(im.transpose(Image.Transpose.ROTATE_180),(1024,768))
tilepath=TEX/'paving_mirrored_repeat.png';tile.save(tilepath)
# Each of the six rectangular slab faces uses four separate UV/normal vertices.
# There is one slab, not a mesh for each individual paving stone.
facesets=[
 # top, bottom
 [(-10,0,-10),(-10,0,0),(10,0,0),(10,0,-10)],
 [(-10,-.2,0),(-10,-.2,-10),(10,-.2,-10),(10,-.2,0)],
 # left, right
 [(-10,-.2,-10),(-10,-.2,0),(-10,0,0),(-10,0,-10)],
 [(10,-.2,0),(10,-.2,-10),(10,0,-10),(10,0,0)],
 # front, rear
 [(-10,-.2,-10),(-10,0,-10),(10,0,-10),(10,-.2,-10)],
 [(10,-.2,0),(10,0,0),(-10,0,0),(-10,-.2,0)],
]
vertices=[];uv=[];faces=[]
for idx,quad in enumerate(facesets):
 start=len(vertices);vertices.extend(quad)
 for x,y,z in quad:
  if idx in (0,1):uv.append(((x+10)/4.4,(z+10)/3.6))
  elif idx in (2,3):uv.append(((z+10)/4.4,(y+.2)/3.6))
  else:uv.append(((x+10)/4.4,(y+.2)/3.6))
 faces.extend([(start,start+1,start+2),(start,start+2,start+3)])
mat=trimesh.visual.material.PBRMaterial(name='paving',baseColorTexture=Image.open(tilepath),metallicFactor=0,roughnessFactor=.96,doubleSided=False)
mesh=trimesh.Trimesh(vertices=np.asarray(vertices,dtype=np.float32),faces=np.asarray(faces,dtype=np.int64),process=False)
mesh.visual=trimesh.visual.TextureVisuals(uv=np.asarray(uv,dtype=np.float32),material=mat)
_=mesh.vertex_normals
scene=trimesh.Scene(base_frame='world');scene.add_geometry(mesh,geom_name='forecourt_slab',node_name='forecourt_slab')
path=ROOT/'station_forecourt.glb';path.write_bytes(scene.export(file_type='glb'))
loaded=trimesh.load(path,force='scene',process=False)
stats={'file':str(path),'bounds_m':np.round(loaded.bounds,5).tolist(),'meshes':len(loaded.geometry),'triangles':sum(len(m.faces) for m in loaded.geometry.values()),'vertices':sum(len(m.vertices) for m in loaded.geometry.values()),'texture_repeat_m':[4.4,3.6],'source_cell_m':[2.2,1.8],'sampler':'REPEAT (default), with mirroring baked into texture'}
(ROOT/'model_stats.json').write_text(json.dumps(stats,indent=2)+'\n')
print(json.dumps(stats,indent=2))
