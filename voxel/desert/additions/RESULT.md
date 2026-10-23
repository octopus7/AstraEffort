# Desert water purifier addition

Original main-authored static treatment skid; the accepted desert originals were unchanged. Two filter vessels, motor-pump, three membrane cartridges, joined manifolds, three controls and service console are visible in both final actual previews. One build, no geometry correction required.

Start UTC 2026-10-23T15:36:53Z; KST 2026-10-24T00:36:53+09:00.
Finish UTC 2026-10-23T15:40:39.493781+00:00; KST 2026-10-24T00:40:39.493781+09:00.
Actual wall time 226.494 seconds; build/export/render 22.029 seconds; fresh-file validation 4.805 seconds.

Large grid 128 x 96 x 112 at 0.04m/cell; half 64 x 48 x 56 at 0.08m/cell. Same physical grid extent. Native conservative reduction, no manual half corrections.

Each assets/water_purifier/{large,half} directory has VOX, BLEND, GLB, FBX, preview.png and metadata.json. Source: build.py; palette.json; feature_validation.json; capture_manifest.json; build_validation.json. Independent parent validation: ../../validation/expansion_desert.json.

Every native file was reparsed; six fresh BLEND/GLB/FBX inspections passed exact exposed boundary, outward normals, material indices, finite grid positions, triangle counts, bounds and hashes. Native probes check both vessel cores, motor, three cartridges, header and console plus empty vessel/cartridge gaps. Two actual 768px Cycles CPU previews were personally inspected; no generated image is used as output evidence.

Reference: ../../../REF/voxel/desert/additions/reference.png, generated sequentially by main; prompt and timestamps in generation.json. Original desert palette values retained, geometry newly authored. No other theme geometry/source used.

Limitations: static palette model; no water simulation, rig, animation, collision or engine integration. Small rings/spokes simplify at half resolution. All rendered glass/indicators are opaque palette colors; no texture UVs required.
