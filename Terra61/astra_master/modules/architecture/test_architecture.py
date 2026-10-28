"""Contract and binary integrity checks for the station architecture GLBs."""
from pathlib import Path
from io import BytesIO
import math
import json
import numpy as np
from PIL import Image
from pygltflib import GLTF2
import trimesh

HERE = Path(__file__).resolve().parent
NAMES = ("central_hall", "facade_bay", "dome_tower", "architecture_assembled")


def data_for(gltf, accessor_id):
    accessor = gltf.accessors[accessor_id]
    view = gltf.bufferViews[accessor.bufferView]
    dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2'}[accessor.componentType]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[accessor.type]
    offset = (view.byteOffset or 0) + (accessor.byteOffset or 0)
    data = np.frombuffer(gltf.binary_blob(), dtype=dtype, count=accessor.count * width,
                         offset=offset)
    return data.reshape(accessor.count, width)


def test_all_exports_are_valid_and_embedded():
    manifest = json.loads((HERE / 'manifest.json').read_text())
    for name in NAMES:
        path = HERE / f"{name}.glb"
        assert path.exists(), f"missing {path.name}"
        gltf = GLTF2().load_binary(path.as_posix())
        assert gltf.asset.version == "2.0"
        assert len(gltf.scenes[gltf.scene].nodes) == 1
        root = gltf.nodes[gltf.scenes[gltf.scene].nodes[0]]
        assert np.allclose(root.rotation, [-math.sqrt(0.5), 0, 0, math.sqrt(0.5)])
        assert root.children
        assert gltf.buffers[0].byteLength <= len(gltf.binary_blob())
        assert all(image.bufferView is not None and image.uri is None for image in gltf.images)
        for image in gltf.images:
            view = gltf.bufferViews[image.bufferView]
            assert (view.byteOffset or 0) + view.byteLength <= len(gltf.binary_blob())
            data = gltf.binary_blob()[(view.byteOffset or 0):(view.byteOffset or 0)+view.byteLength]
            with Image.open(BytesIO(data)) as decoded:
                decoded.verify()
        for material in gltf.materials:
            assert material.pbrMetallicRoughness.baseColorTexture is not None
            if material.name != 'door':
                assert material.normalTexture is not None
                assert material.pbrMetallicRoughness.metallicRoughnessTexture is not None
        count = 0
        for mesh in gltf.meshes:
            for primitive in mesh.primitives:
                assert primitive.attributes.TEXCOORD_0 is not None and primitive.attributes.NORMAL is not None
                pos = data_for(gltf, primitive.attributes.POSITION)
                normal = data_for(gltf, primitive.attributes.NORMAL)
                uv = data_for(gltf, primitive.attributes.TEXCOORD_0)
                indices = data_for(gltf, primitive.indices).ravel()
                assert len(pos) == len(normal) == len(uv)
                assert np.isfinite(pos).all() and np.isfinite(normal).all() and np.isfinite(uv).all()
                assert np.allclose(np.linalg.norm(normal, axis=1), 1, atol=1e-4)
                assert len(indices) % 3 == 0 and int(indices.max()) < len(pos)
                tri = pos[indices].reshape(-1, 3, 3)
                assert np.all(np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]), axis=1) > 1e-8)
                count += len(indices) // 3
        expected = (manifest['assembly']['unique_triangles'] if name == 'architecture_assembled'
                    else manifest['modules'][name]['triangles'])
        assert count == expected
        scene = trimesh.load(path.as_posix(), force="scene")
        assert len(scene.geometry) > 0
        for mesh in scene.geometry.values():
            assert np.isfinite(mesh.vertices).all()
            assert len(mesh.faces) > 0
            assert np.isfinite(mesh.visual.uv).all()
        author_bounds = (manifest['assembly']['bounds_author_z_up'] if name == 'architecture_assembled'
                         else manifest['modules'][name]['bounds_author_z_up'])
        lo, hi = np.array(author_bounds)
        y_up = [[lo[0],lo[2],-hi[1]], [hi[0],hi[2],-lo[1]]]
        assert np.allclose(scene.bounds, y_up, atol=1e-4), (name,scene.bounds,y_up)


def test_assembly_reuses_three_module_meshes():
    gltf = GLTF2().load_binary((HERE / "architecture_assembled.glb").as_posix())
    instances = [n for n in gltf.nodes if n.mesh is not None]
    assert len(instances) == 7
    assert len({n.mesh for n in instances}) == 3
    assert sorted(round(n.translation[0]) if n.translation else 0 for n in instances) == [-22, -18, -12, 0, 12, 18, 22]


def test_door_uses_high_resolution_material():
    manifest=json.loads((HERE/'manifest.json').read_text())
    door=manifest['textures']['door']
    assert door['source'].startswith('textures/door_basecolor.png')
    with Image.open(HERE / Path(door['base']).name) as img:
        assert img.width>=800 and img.height>=1400


if __name__ == "__main__":
    test_all_exports_are_valid_and_embedded()
    test_assembly_reuses_three_module_meshes()
    test_door_uses_high_resolution_material()
    print("All four architecture GLBs passed binary, PBR, geometry, orientation, and instance checks.")
