# Quietwater Grove source art

All meshes were independently generated in this chat using `generate_art.py` in a separate Blender 4.5 background process. Seed 43175 fixes the layout and variations. No downloaded models, textures or other effort assets were used.

`SourceArt/Quietwater_Source.blend` contains the 27 reusable mesh sources (unhide objects to inspect). The same folder contains individual FBX exports. `scene_manifest.json` stores the palette, exact asset material slots, transform placements, height samples and feature locations. Blender source coordinates are metres; the UE importer uses centimetres with the Y axis mirrored. Trees use explicit branching tubes and custom asymmetrical crown meshes, pine whorls are curved ring surfaces, rocks are rounded irregular meshes, and ferns have individually shaped leaflets.

The terrain is a 100m square, 144 by 144 quad surface with a continuous coastal slope and a separate excavated lake. Vertex paint blends a curved coastal sand band, lake banks, grass and a winding trail. Lake and sea use separate meshes/materials. Foliage, rocks, landing, bench, log and understory are individual reusable assets, not a single baked scene mesh.

UE materials are owned procedural graphs. The only shared visual resource used for ambient lighting is the permitted engine `DaylightAmbientCubemap`. SkyAtmosphere supplies the clear sky; no decorative clouds or face motifs are present.

Production scripts operate only inside the private scratch project. `build_level.py` regenerates material graphs, imports missing source meshes and assembles the map. `review_pipeline.py` reloads the saved map, recursively checks package references, captures real render targets and starts PIE collision validation. No image-generation or image post-processing is used for evidence.

Implementation notes: use named `Rotator` arguments (UE Python positional order is roll, pitch, yaw). Render captures are explicitly refreshed every tick because an offscreen editor does not guarantee the active viewport is realtime. NullRHI is suitable for the API probe but crashed on mesh placement in this engine build; production uses D3D12 rendering.
