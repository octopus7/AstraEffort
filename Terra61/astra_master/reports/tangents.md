# Tangent export pass

`src/add_tangents.py` adds a float32 `VEC4` tangent accessor to each normal-mapped primitive that lacks one. It derives tangents from the primitive's positions, normals, selected texture coordinates and indices, orthogonalizes them against the normal, and sets glTF handedness. Degenerate UVs use a finite perpendicular fallback. The reader handles interleaved/strided and normalized integer components, sparse accessors, non-indexed geometry, and triangle, strip or fan primitives. An existing embedded GLB buffer 0 is required; any additional buffers may be external or data URIs.

Run the pass after the model-building scripts have finished, for example:

```sh
python station/src/add_tangents.py 'station/modules/**/*.glb'
```

A single GLB path is also accepted. Each replacement is atomic; a GLB with no missing tangents is left byte-for-byte unchanged. Rebuilding a module with its source script will remove the added tangent data, so rerun the pass after any rebuild.

Verification used copies under `/tmp`, never the live module files. The official Khronos `gltf-validator` returned **0 errors and 0 warnings across 20 copied modules**. Their 25,632 original triangles, original binary buffer bytes, mesh and material references, root transforms, and scene bounds were preserved. A second pass left all 20 files byte-for-byte unchanged. Additional synthetic checks covered interleaved normalized attributes, mirrored and degenerate UVs, sparse accessors, strip/fan conversion, and an invalid index rejected without changing its file.
