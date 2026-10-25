# Mine elevator headhouse — ready for review

Delivered `mine_elevator.blend`, `mine_elevator.glb`, `mine_elevator.fbx`, reproducible `build.py`, actual `renders/hero.png` and `renders/rear.png`, `capture_manifest.json`, `validation.json`, and `visual_review.json`. All files are under `D:/github/AstraEffort/Blender/Set02/mine_elevator/`.

626 named editable mesh parts; **145,712 triangles**. True transformed-vertex dimensions: **5.2200 × 4.8793 × 8.0600 m**. Bounds minimum: (-1.940000, -1.974266, 0.000000); maximum: (3.280000, 2.905000, 8.060000). Meters, Z up, front −Y, lowest surface Z=0.

The open portal contains a separate floor-equipped lift cage, two diamond-mesh gate leaves, two I-section guide rails and four carriage stations. Above are four stout posts, a two-groove sheave with six spokes per face, a through axle, two continuous tangent-routed ropes and a powered winding drum. A fourteen-step stair reaches the open service deck. The rounded annex has a door, twelve vent louvers, maintenance panel and conduits. Rear bracing and a softly curved canopy complete the structure.

Hidden-geometry decisions: the full stair descends behind the annex; the winding drum is visible on its roof, giving the ropes explicit endpoints. The rear lower shaft is lined. The source reference is `D:/github/AstraEffort/REF/Set02/mine_elevator.png`, supplied by the parent; no other creative asset or external web reference was used.

Final hero and rear were rendered with Blender 4.5.12 LTS, Cycles CPU, four threads, 32 samples, denoising, 1440×1080, orthographic cameras and soft studio lighting. Both actual final images were inspected. Initial cropping was corrected; an observed pulley/canopy interference was corrected by lowering the axle 0.12 m, leaving nominal 0.097 m clearance. Superseded capture timings remain in the manifest.

Fresh-process verification opened the saved BLEND, then independently imported GLB and FBX into empty scenes: all **13 checks passed**. Mesh counts, exact triangle counts and transformed bounds agree. All faces have UVs and materials; no nonfinite geometry, zero-area geometric/UV triangles, missing images, cameras/lights/floor in exports, or nonmanifold edges after position-only seam welding. Final hashes are in `validation.json`; no render or asset was changed after validation.

Production timer began after brief/reference inspection: **2026-10-23T12:15:19.695345+00:00 UTC** / **2026-10-23T21:15:19.695345+09:00 KST**. Finished **2026-10-23T12:42:49.658161+00:00 UTC** / **2026-10-23T21:42:49.658161+09:00 KST**. Elapsed **1649.963 wall seconds**. First build/export/render run: 183.625 s; all six actual capture operations, including superseded framing passes: 234.603 s; fresh final validation: 5.229 s. These phase times overlap the build time and are not additive.

Commands: private `blender.exe --background --factory-startup --threads 4 --python-exit-code 1 --python <script>` ran `build.py`, `finalize_captures.py`, `clearance_fix.py`, and `validate.py`; each exited 0. Logs and correction scripts are included locally. No shared Blender scene, child agents, image generation, installations, Git operations or unrelated creative resources were used.

Limitations: solid named PBR materials with per-component UV islands; no image textures or shared atlas. Static visualization, not a load-certified lifting mechanism; no rig, animation, collision or LODs. Clearances and structural proportions are artistic reconstruction, not engineering certification. Separate mating parts intentionally overlap at joints. Source uses baked triangulated geometry for stable exports.
