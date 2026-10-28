"""Assemble the authored Y-up GLBs and preserve repeat nodes as instances."""
from pathlib import Path
import json
import math
import numpy as np
import trimesh
from pygltflib import GLTF2

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'viewer'/'assets'
manifest=json.loads((ASSETS/'manifest.json').read_text(encoding='utf-8'))
world=trimesh.Scene(base_frame='world')

def transform(placement):
    m=trimesh.transformations.euler_matrix(*placement.get('rotation',[0,0,0]),axes='sxyz')
    m[:3,:3] = m[:3,:3] @ np.diag(placement.get('scale',[1,1,1]))
    m[:3,3]=placement.get('position',[0,0,0])
    return m

for index,asset in enumerate(manifest['assets']):
    source=trimesh.load(ASSETS/asset['file'],force='scene',process=False)
    # Each source node can have a different source transform, so retain them
    # while sharing each unique mesh across the repeated 6m bays.
    for geometry_name,geometry in source.geometry.items():
        nodes=[node for node in source.graph.nodes_geometry if source.graph[node][1] == geometry_name]
        if not nodes:
            continue
        key=f"m{index}_{geometry_name}"
        first=True
        for placement_index,placement in enumerate(asset['placements']):
            for source_index,node in enumerate(nodes):
                local,_=source.graph[node]
                matrix=transform(placement) @ local
                node_name=f"m{index}_p{placement_index}_n{source_index}_{geometry_name}"
                if first:
                    world.add_geometry(geometry,geom_name=key,node_name=node_name,transform=matrix)
                    first=False
                else:
                    world.graph.update(frame_from='world',frame_to=node_name,matrix=matrix,geometry=key)

output=ROOT/'output'/'riverdale_station_assembled.glb'
output.parent.mkdir(exist_ok=True)
output.write_bytes(world.export(file_type='glb'))
loaded=trimesh.load(output,force='scene',process=False)
gltf=GLTF2().load_binary(str(output))
assert loaded.geometry and loaded.graph.nodes_geometry
assert np.isfinite(loaded.bounds).all()
assert all(not image.uri for image in gltf.images), 'GLB must embed all texture images'
assert len(loaded.graph.nodes_geometry)==len(world.graph.nodes_geometry)
stats={
    'assembled_glb':output.name,
    'bytes':output.stat().st_size,
    'bounds_y_up_m':loaded.bounds.tolist(),
    'unique_meshes':len(loaded.geometry),
    'mesh_instances':len(loaded.graph.nodes_geometry),
    'unique_triangles':sum(len(geom.faces) for geom in loaded.geometry.values()),
    'drawn_triangles':sum(len(loaded.geometry[loaded.graph[n][1]].faces) for n in loaded.graph.nodes_geometry),
    'embedded_images':len(gltf.images),
    'materials':len(gltf.materials),
    'blend_materials':sum(mat.alphaMode=='BLEND' for mat in gltf.materials),
    'double_sided_materials':sum(bool(mat.doubleSided) for mat in gltf.materials),
    'asset_placements':[(a['file'],len(a['placements'])) for a in manifest['assets']]
}
(ROOT/'output'/'assembly_stats.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(stats,indent=2,ensure_ascii=False))
