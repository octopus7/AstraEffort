# Airfield — ready for review

Four original models / eight variants are frozen under `assets/{propeller_plane,airport_tug,maintenance_hangar,control_tower}/{large,half}/`. Each variant has native VOX 150, BLEND, GLB, FBX, actual `preview.png`, and metadata.

| Model | Large grid | Half grid |
|---|---|---|
| propeller_plane | 128×104×64 | 64×52×32 |
| airport_tug | 80×128×72 | 40×64×36 |
| maintenance_hangar | 128×112×104 | 64×56×52 |
| control_tower | 92×92×128 | 46×46×64 |

Large cells are 0.05m; half cells are 0.10m, preserving physical grid extents. Geometry and the ivory/aviation-blue/ochre palette were newly authored from this theme's `REF/voxel/airfield/reference.png` only. `build.py` supplies pure `make_assets()`; no other theme creative resources were read or reused.

**Evidence:** one isolated four-thread build, no rebuild or optional views. All eight actual previews inspected. `validation_export.json` passes **24 fresh BLEND/GLB/FBX imports**, checking native hashes/palette, exact exposed surface, outward normals, triangle counts, materials, bounds and export studio exclusion. `validation_features.json` passes **42 saved-native probes** for broad wings, both propeller blades, landing wheels, towbar/open eye, the empty hangar portal/bay and tower glazing. Tower rays toward the common camera find **571 large / 123 half unoccluded front-glass cells**. All four camera pairs match.

**Actual timing:** start 2026-10-23T16:47:30Z / 2026-10-24T01:47:30+09:00; finish 2026-10-23T17:01:51.491334+00:00 / 2026-10-24T02:01:51.491334+09:00. Wall **861.491s**. Build **87.890s** (rendering included: 83.163s). Fresh-format verifier **6.930s**; native probes **0.365s**. Exact commands, UTC process timings and logs are retained. No UE or worker image-generation process was used.

Limits: static opaque palette assets, without rig/animation/collision/LOD chain/engine integration. Rear hangar equipment is dark under the common studio lighting; its open bay remains clear. Half reduction can expand occupied bounds by 0.05m. No GUI inspection is claimed. Source, palette, capture manifest, visual review and a frozen file-hash manifest accompany this result. Parent acceptance is pending; canal was not started.
