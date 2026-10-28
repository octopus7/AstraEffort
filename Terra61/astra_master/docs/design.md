# Riverdale Steam Station — Asset Production

User direction: use the attached Victorian steam station concept, generate individual module reference images in the main conversation, run exactly three GPT-6.1 Terra Max modeling workers, and reassign them as they finish. Prefer texture detail to additional faces. Main handles imagery, review, assembly, delivery.

Implementation choice: portable glTF 2.0 / GLB, Python-authored low-poly geometry, image-generated texture atlases, self-contained local WebGL viewer and rendered PNG previews. No dependency on a DCC application for geometry. All deliveries will be packaged together.

Coordinate contract: meters. Authoring coordinates X right, Y station depth, Z up. Ground Z=0. Export glTF Y-up with one root rotation (-90 degrees about X); JSON geometry data stays Z-up. Station front faces negative Y. Train travels along Y with front towards negative Y. Rail gauge is a visually plausible 1.435 m between rail centers. All module origins on ground; explicitly document wheel/rail offsets.

Scene layout: a 48 m facade left of a 28 m span train shed, roof rising from 11 m eaves to 22 m crown, depth 48 m. Platforms 1 m high. Keep repeated pieces as reusable instances. The camera looks from the front-right toward the facade and locomotive.

Geometry policy: large silhouette, door/window recesses, arch curves, columns, roof ribs and vehicle wheels are geometry. Brick courses, rivets, fine ornamental relief, scratches, wood grain, wheel spoke details and most moldings are textures/normal maps. No individually modeled bricks or micro-rivets. UV charts are explicit and stable. Reusable material regions may be shared; hero face charts receive more area. This is a game environment approximation, not a construction plan or a 1:1 replica of generated concept art.

Module waves:
1. architecture: station hall, repeat facade bay, dome tower; shed: repeat steel arch roof bay; infrastructure: platform and track repeat segments.
2. train: steam locomotive+tender, passenger carriage; furnishings: gaslamp, bench, luggage cart/crates, station clock and signs.
3. main assembles scene, renders actual meshes from multiple viewpoints, audits GLB/UV/texture references and reports counts.

Reference images and texture atlas prompts are kept alongside generated source images. PBR maps derived from generated base images are approximate, not scanned material data. Deliverables include GLBs, texture sources/maps, source scripts, modular manifest, a local viewer, preview PNGs, and import notes.
