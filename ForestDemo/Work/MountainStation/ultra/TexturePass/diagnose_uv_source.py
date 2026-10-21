import bpy,json
from pathlib import Path
R=Path(r'D:/github/AstraEffort/ForestDemo/Work/MountainStation/ultra/TexturePass')
bpy.ops.wm.open_mainfile(filepath=str(R/'SourceArt/AlderPass_Textured.blend'))
o=bpy.data.objects['SM_Terrain'];side=32768
items=[]
for p in list(o.data.polygons)[195:210]:
    items.append({'polygon':p.index,'verts':[list(o.data.vertices[i].co) for i in p.vertices],'uv_px':[[x*side for x in o.data.uv_layers[0].data[i].uv] for i in p.loop_indices]})
(R/'diagnostic_blend_uv.json').write_text(json.dumps(items,indent=2))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'SourceArt/SM_Terrain.fbx'))
o=next(o for o in bpy.data.objects if o.type=='MESH')
items=[]
for p in list(o.data.polygons)[195:210]:
    items.append({'polygon':p.index,'verts':[list(o.data.vertices[i].co) for i in p.vertices],'uv_px':[[x*side for x in o.data.uv_layers[0].data[i].uv] for i in p.loop_indices]})
(R/'diagnostic_fbx_uv.json').write_text(json.dumps(items,indent=2))
