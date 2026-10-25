# Set05 — Marine work

Status: **produced_unreviewed**. Review: **deferred_by_user**.

Production start: 2026-10-25T05:49:38.053153+00:00 UTC / 2026-10-25T14:49:38.053153+09:00 KST.
Production finish: 2026-10-25T05:57:15.735339+00:00 UTC / 2026-10-25T14:57:15.735339+09:00 KST.
Wall time: 457.682 s, starting after brief/reference intake. Four Blender process durations sum to 205.695 s. Actual CPU render durations sum to 181.983 s.

All four isolated Blender 4.5.12 processes completed with return code 0. The 24 required deliverable files exist and are nonempty. Sizes and SHA256 hashes are inventory records, not independent validation.

| Asset | Process seconds | Authored mesh parts | Delivered files |
|---|---:|---:|---|
| catamaran_workboat | 50.237 | 227 | [catamaran_workboat/](catamaran_workboat/): BLEND, GLB, FBX, metadata, hero/rear PNG |
| underwater_service_robot | 47.092 | 180 | [underwater_service_robot/](underwater_service_robot/): BLEND, GLB, FBX, metadata, hero/rear PNG |
| docking_lift_platform | 53.956 | 415 | [docking_lift_platform/](docking_lift_platform/): BLEND, GLB, FBX, metadata, hero/rear PNG |
| marine_equipment_workshop | 54.410 | 224 | [marine_equipment_workshop/](marine_equipment_workshop/): BLEND, GLB, FBX, metadata, hero/rear PNG |

Editable named parts and edge modifiers are preserved in BLEND. ASSET and STUDIO collections are separate. Exports contain selected asset meshes and their solid PBR materials. Each component received a local UV layout during construction. Actual 960×960 Cycles CPU studio renders were produced and were not opened or inspected.

The supplied references were used as design inputs. [Local reference mirror](REF/) remains read-only. Original geometry is authored in [build.py](build.py); the reproducible process wrapper is [run_build.py](run_build.py). Detailed process records are in [logs/process_results.json](logs/process_results.json) and [delivery_manifest.json](delivery_manifest.json).

Limitations: visual fidelity/framing, mesh/UV quality and export roundtrips remain unreviewed. These are static solid-palette assets with no weathering maps, rig, animation, collision, LODs or physical simulation. The subdued glazing is opaque. Dimensions/counts come from the authoring scene and are production measurements only.

The set is frozen after production. No Git operations, installations, additional agents, image generation, cross-set asset reads, shared Blender scene writes or independent review passes were performed.
