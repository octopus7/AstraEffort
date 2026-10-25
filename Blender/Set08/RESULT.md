# Set08 production result

Status: `produced_unreviewed`. Review: `deferred_by_user`.

Four original materials-processing assets were authored as named ordinary mesh components with bevels, a solid PBR palette and per-component UV layouts. ASSET and STUDIO are separate. The GLB/FBX export commands select only ASSET meshes.

- Start UTC: 2026-10-25T06:06:25+00:00
- Start KST: 2026-10-25T15:06:25+09:00
- Finish UTC: 2026-10-25T06:15:57.787163+00:00
- Finish KST: 2026-10-25T15:15:57.787163+09:00
- Elapsed wall seconds: 572.787
- Sum of Blender process seconds: 200.939
- Timing starts at the first explicit clock capture, following initial brief and skill reads.

| Asset | Process seconds | Actual return code |
|---|---:|---:|
| articulated_welding_mech | 49.473 | 0 |
| cylindrical_mixer | 53.781 | 0 |
| rounded_foundry_workshop | 49.645 | 0 |
| vertical_material_tower | 48.04 | 0 |

Delivery paths are linked in [README.md](README.md); exact file bytes and SHA256 inventory are in [delivery_manifest.json](delivery_manifest.json). Source: [build.py](build.py), [run_builds.py](run_builds.py). Logs are under [logs/](logs/).

Completion evidence: actual subprocess return codes and 24/24 expected nonempty files. Renders are actual Cycles studio renders at 960x960. They were generated but not opened or visually inspected.

Per-component UVs were authored using angle-based projection with a 2.5% island margin. No UV, geometry, image, reopen or export roundtrip validation was run. No reviewer agents were used. The set remains unreviewed as explicitly requested.

Known limitations: static meshes only; no rigging, animation, collision or LODs. Solid palette materials only; no surface textures. Reference fidelity, shading, UV quality, framing and export interchange remain deferred review items.

External references: only the four main-supplied reference images and prompts in [REF/](REF/) were used as creative inputs. No online references or other sets were inspected or reused. No worker Git actions, installations or image generation were performed.

Set frozen after production; waiting for the parent to commit the group and explicitly dispatch further work.
