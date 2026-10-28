"""Contract checks for the reusable station infrastructure GLBs."""
from pathlib import Path
import io
import json
import math
import os
import unittest

import numpy as np
from PIL import Image
from pygltflib import GLTF2

HERE = Path(os.environ.get('INFRA_OUTPUT', Path(__file__).resolve().parent))
MODULES = {
    'platform_segment': ([[-2, 0, 0], [2, 8, 1]], 400),
    'track_segment': ([[-1.5, 0, 0], [1.5, 8, 0.22]], 1500),
    'platform_ramp': ([[-2, 0, 0], [2, 8, 1]], 400),
    'plaza_tile': ([[-4, 0, 0], [4, 8, 0.12]], 400),
}
DTYPES = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}
SIZES = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def accessor(gltf, idx):
    a = gltf.accessors[idx]
    v = gltf.bufferViews[a.bufferView]
    count = a.count * SIZES[a.type]
    offset = (v.byteOffset or 0) + (a.byteOffset or 0)
    return np.frombuffer(gltf.binary_blob(), dtype=DTYPES[a.componentType], count=count,
                         offset=offset).reshape(a.count, SIZES[a.type])


class InfrastructureContract(unittest.TestCase):
    def test_manifest_and_expected_exports_exist(self):
        self.assertTrue((HERE / 'manifest.json').exists(), 'module manifest is missing')
        for name in MODULES:
            self.assertTrue((HERE / (name + '.glb')).exists(), f'{name} export is missing')

    def test_geometry_uv_materials_and_rotation(self):
        manifest = json.loads((HERE / 'manifest.json').read_text())
        self.assertAlmostEqual(manifest['rail_running_surface_z'], 0.22)
        self.assertAlmostEqual(manifest['rail_center_gauge'], 1.435)
        for name, (expected_bounds, budget) in MODULES.items():
            with self.subTest(module=name):
                gltf = GLTF2().load(str(HERE / (name + '.glb')))
                roots = gltf.scenes[gltf.scene].nodes
                self.assertEqual(len(roots), 1)
                root = gltf.nodes[roots[0]]
                self.assertTrue(np.allclose(root.rotation, [-math.sqrt(0.5), 0, 0, math.sqrt(0.5)]))
                self.assertIsNone(root.mesh)
                all_positions, tri_count = [], 0
                for mesh in gltf.meshes:
                    for primitive in mesh.primitives:
                        p = accessor(gltf, primitive.attributes.POSITION)
                        uv = accessor(gltf, primitive.attributes.TEXCOORD_0)
                        self.assertEqual(len(p), len(uv))
                        self.assertTrue(np.isfinite(p).all())
                        self.assertTrue(np.isfinite(uv).all())
                        normals = accessor(gltf, primitive.attributes.NORMAL)
                        self.assertTrue(np.isfinite(normals).all())
                        self.assertTrue(np.allclose(np.linalg.norm(normals, axis=1), 1, atol=1e-5))
                        self.assertIsNotNone(primitive.material)
                        mat = gltf.materials[primitive.material]
                        self.assertIsNotNone(mat.pbrMetallicRoughness.baseColorTexture)
                        self.assertIsNotNone(mat.pbrMetallicRoughness.metallicRoughnessTexture)
                        self.assertIsNotNone(mat.normalTexture)
                        idx = accessor(gltf, primitive.indices).reshape(-1)
                        self.assertTrue(len(idx) % 3 == 0)
                        self.assertLess(int(idx.max()), len(p))
                        triangles = idx.reshape(-1, 3)
                        edge1 = p[triangles[:, 1]] - p[triangles[:, 0]]
                        edge2 = p[triangles[:, 2]] - p[triangles[:, 0]]
                        cross = np.cross(edge1, edge2)
                        self.assertTrue((np.linalg.norm(cross, axis=1) > 1e-8).all())
                        self.assertTrue(((cross * normals[triangles[:, 0]]).sum(axis=1) > 0).all())
                        uv1 = uv[triangles[:, 1]] - uv[triangles[:, 0]]
                        uv2 = uv[triangles[:, 2]] - uv[triangles[:, 0]]
                        self.assertTrue((np.abs(uv1[:, 0]*uv2[:, 1] - uv1[:, 1]*uv2[:, 0]) > 1e-10).all())
                        tri_count += len(idx) // 3
                        all_positions.append(p)
                positions = np.concatenate(all_positions)
                actual_bounds = np.stack([positions.min(0), positions.max(0)])
                self.assertTrue(np.allclose(actual_bounds, expected_bounds, atol=1e-5),
                                f'{name} bounds {actual_bounds}')
                self.assertLess(tri_count, budget)
                self.assertEqual(tri_count, manifest['modules'][name]['triangle_count'])
                for img in gltf.images:
                    self.assertIsNone(img.uri)
                    self.assertIsNotNone(img.bufferView)
                    v = gltf.bufferViews[img.bufferView]
                    data = gltf.binary_blob()[v.byteOffset:v.byteOffset+v.byteLength]
                    with Image.open(io.BytesIO(data)) as picture:
                        picture.verify()
                if name == 'track_segment':
                    sleepers = next(m for m in gltf.meshes if m.name == 'wooden_sleepers')
                    sleeper_positions = accessor(gltf, sleepers.primitives[0].attributes.POSITION)
                    sleeper_edges = np.unique(np.round(sleeper_positions[:, 1], 5))
                    self.assertEqual(len(sleeper_edges), 24)
                    sleeper_centres = (sleeper_edges[::2] + sleeper_edges[1::2]) / 2
                    self.assertTrue(np.allclose(sleeper_centres, (np.arange(12)+.5)*8/12, atol=1e-5))
                    rail_centers = []
                    for rail in ('rail_left', 'rail_right'):
                        primitive = next(m for m in gltf.meshes if m.name == rail).primitives[0]
                        pos = accessor(gltf, primitive.attributes.POSITION)
                        self.assertAlmostEqual(float(pos[:, 2].max()), 0.22, places=5)
                        rail_centers.append((float(pos[:, 0].min()) + float(pos[:, 0].max())) / 2)
                    self.assertAlmostEqual(rail_centers[1] - rail_centers[0], 1.435, places=5)

    def test_plaza_top_is_continuous_paving_across_tile_seams(self):
        gltf = GLTF2().load(str(HERE / 'plaza_tile.glb'))
        surfaces = []
        for mesh in gltf.meshes:
            for primitive in mesh.primitives:
                p = accessor(gltf, primitive.attributes.POSITION)
                uv = accessor(gltf, primitive.attributes.TEXCOORD_0)
                n = accessor(gltf, primitive.attributes.NORMAL)
                idx = accessor(gltf, primitive.indices).reshape(-1, 3)
                for face in idx:
                    if np.allclose(p[face, 2], .12, atol=1e-6) and (n[face, 2] > .99).all():
                        material = gltf.materials[primitive.material]
                        texture = gltf.textures[material.pbrMetallicRoughness.baseColorTexture.index]
                        self.assertEqual(gltf.images[texture.source].name, 'paving_basecolor.png')
                        surfaces.append((p[face], uv[face]))
        self.assertTrue(surfaces, 'plaza needs a paved top')
        p = np.concatenate([v[0] for v in surfaces]); uv = np.concatenate([v[1] for v in surfaces])
        def mirrored(value):
            return 1 - np.abs((value % 2) - 1)
        left = mirrored(uv[np.isclose(p[:, 0], -4), 0]); right = mirrored(uv[np.isclose(p[:, 0], 4), 0])
        front = mirrored(uv[np.isclose(p[:, 1], 0), 1]); back = mirrored(uv[np.isclose(p[:, 1], 8), 1])
        self.assertTrue(len(left) and len(right) and len(front) and len(back))
        self.assertTrue(np.allclose(left, right[0], atol=1e-5))
        self.assertTrue(np.allclose(front, back[0], atol=1e-5))


if __name__ == '__main__':
    unittest.main()
