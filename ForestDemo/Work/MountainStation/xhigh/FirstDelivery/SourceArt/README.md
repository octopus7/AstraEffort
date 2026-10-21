# Alder Pass source artwork

All meshes, lettering, props and the palette were authored for MountainStation/xhigh by `create_art.py` in an isolated Blender 4.5 background process. `AlderPass.blend` is the original scene; the nine FBX files are semantic assemblies. No downloaded creative assets or other effort's artwork were used.

Reproduction sequence for the delivered source: `create_art.py`, `repair_art.py` (western approach grading), `refine_tunnel_art.py` (grounded tunnel rock shell), then `finalize_tunnel_source.py` (reconstruct and trim the original deterministic crown in world coordinates). The intermediate `trim_tunnel_crown.py` attempt was superseded and its result was never imported into the delivery map.

The 100 × 100 metre site uses a continuous railway curve `y = -16 + 0.004 (x + 10)^2`. Rail center spacing is 1.53 m; the 0.105 m rail heads give approximately 1.425 m between their inner edges. The platform top is 1.22 m; its west ramp rises 0.97 m over 8 m. The 5.8 m wide vaulted tunnel starts at (32, -8.944) m, aligned with the local railway tangent. Its deepest section is a closed scenic termination, not a through-route.

The station is a static exterior with timber framing, layered pitched roof, standing seams, glazed doors/windows, planters, canopy, name boards and an east gable clock. Supporting art includes the goods shelter, braced crates, barrels, benches, timetable, baggage, lanterns, fencing, trail signs, rocks, shrubs and 97 fir trees.

Unreal uses authored materials with constant colours. `/Engine/BasicShapes/Sphere` and `/Engine/MapTemplates/Sky/DaylightAmbientCubemap` are the only non-authored visual resources, used for the backdrop and ambient illumination. FBX import changes handedness; the UE assembly restores the authored X/Y arrangement using Y scale -1, recorded in validation. This is a coordinate conversion, not a camera-specific scene rotation.

Final UE assembly uses `build_scene.py`, the approach reimport helper, and `refine_look.py`. Screenshots use the engine's native `RTF_RGBA8_SRGB` render target; they receive no image editing or generated-image substitution.
