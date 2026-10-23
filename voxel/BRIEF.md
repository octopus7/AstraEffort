# Voxel theme production

User authorized production on 2026-10-23. First recorded production timestamp: 2026-10-23T13:58:53Z / 22:58:53 KST.

Nine themes, three workers, one theme at a time per worker. User explicitly requested gpt-6-astra, max reasoning, Fast. The spawning API supports model and effort but no separate Fast setting; do not claim that it was set.

| Worker | First | Second | Third |
|---|---|---|---|
| 1 | farm | harbor | mountain_railway |
| 2 | factory | mine | spaceport |
| 3 | antarctic | desert | underwater |

## Assets
- farm: tractor, barn, silo, windmill.
- harbor: fishing_boat, lighthouse, warehouse, cargo_crane.
- factory: production_machine, conveyor, forklift, generator.
- mine: excavator, mine_cart, mine_elevator, ore_sorter.
- antarctic: research_station, snowcat, radar, weather_instrument.
- desert: exploration_rover, water_tower, solar_array, repair_garage.
- mountain_railway: locomotive, passenger_car, station, railway_bridge, cable_car.
- spaceport: transport_rocket, hangar, exploration_rover, fuel_tank, control_tower.
- underwater: submersible, dome_laboratory, connecting_tunnel, seabed_miner, docking_station.

## Design
Actual colored voxel grids, soft overall silhouettes formed by stepped curves, recognizable useful machinery and architecture. Friendly and simplified, not infantile. No smileys/hearts/cloud ornaments or unrelated decorative motifs. Restrained distinct palettes for each theme. All assets independent and newly authored.

Main alone creates theme reference sheets sequentially and saves them under REF/voxel/THEME. No worker image generation. Reference imagery is design input, never evidence of the voxel output.

## Two sizes
Default interpretation, presented to the user for optional correction: large has longest grid axis 128 cells; half has exactly half the cells on each axis (longest 64). Both retain the same physical grid extents by doubling meters per voxel for half. Preserve functional thin parts in the reduced model; record any manual corrections. Each LARGE grid dimension must be even; half dimensions need not be even. Conservative boundary expansion by up to one large voxel is expected and allowed. Do not merely scale a high-resolution mesh.

## Delivery
Each theme lives in voxel/THEME, with assets/ASSET/large and assets/ASSET/half containing native VOX, GLB, FBX, and metadata. Keep generated source, material palettes, actual render previews, build/validation logs, UTC/KST timings and RESULT/STATUS under that theme. Native VOX is authoritative; transformed meshes are outputs. Preview both versions in matching cameras.

Main owns generic utility code in voxel/_tools, coordination documents, references, independent validation and final packaging. Workers may read those utilities and their own references, and write only their current theme directory. No cross-theme creative resource reads. No ForestDemo assets/scripts, previous Blender creative assets, Git commands, installations, or shared live Blender scene. Use isolated background Blender 4.5.12 processes, at most four CPU threads each.

## Verification
Reparse every saved VOX and compare occupancy, palette, grid, bounds and count; correct 1-based palette indices; no coordinate duplicates or out-of-grid cells. Half grids exactly halve large dimensions. Verify exports contain surfaces of occupied voxels only, outward normals, valid material assignment, finite coordinates, no zero-area faces or studio cameras/lights. Freshly import GLB/FBX to verify bounds and triangles. Inspect actual renders at both resolutions. State no rig/animation/LOD chain/collision or game-engine integration unless actually supplied.
