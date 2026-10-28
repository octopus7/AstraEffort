# Victorian passenger carriage

`modules/carriage/passenger_carriage.glb` is a 15 m long, 2.9 m wide, 4.2 m high burgundy carriage with a barrel roof, eight warm framed windows per side, gold lining, two four-wheel bogies, and open balconies with steps at each end. The wheel spokes, painted wood, rivets, and window interiors come from image textures; this is a static exterior and does not contain a furnished interior.

Authoring coordinates are in meters, X across the track, Y from front to rear, Z up. The front faces -Y and the authored bounds are `[-1.45, 0, 0]` to `[1.45, 15, 4.2]`. Wheel centers are at X ±0.7175 m and Z 0.45 m, so the wheels touch authoring Z=0; translate the complete carriage +0.22 m in authoring Z to sit on the supplied rail tops. The front and rear bogie groups each have two axles and four separately named wheel nodes. One root quaternion `[-0.70710678, 0, 0, 0.70710678]` converts to glTF Y-up.

The carriage has **4,464 rendered triangles** and **380 unique mesh triangles**, with repeated windows, beams, wheels and other pieces instanced. A 24-segment wheel forms each rim; the round spoke pattern is textured. Each of the 16 side windows maps the same single-window crop `[0.34, 0.145, 0.65, 0.573]` in `carriage_window_basecolor.png`, upright on both sides, rather than stretching the source texture across a whole side. Frame and sill geometry stands proud of the warm window faces.

Generated base-color images and supplied normal and ORM maps for `carriage_window`, `carriage_wood`, `boiler`, `wheel`, and `brass` are embedded in the GLB. Their source paths, coordinate contract, counts, and bounds are recorded in `modules/carriage/manifest.json`. Approximate emission on the window material reinforces the warm lamps. Normal and roughness maps are derived approximations, not measured scans.

Rebuild from the station directory with `python src/build_carriage.py`.

Verification reloaded the GLB with pygltflib and trimesh and checked finite vertex data, UV ranges, valid indices, nondegenerate outward-facing triangles, embedded image decoding, all base-color/normal/ORM references, single-window UV crops, bogie hierarchy and wheel counts, rendered triangle total, and transformed Y-up bounds. Both side views were inspected using a texture-sampled software render; final appearance depends on the assembly viewer's lighting and material support.
