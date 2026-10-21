# Alder Pass / MountainStation xhigh implementation plan

**Goal:** A composed, original 100 × 100 m mountain railway stop in Unreal Engine 5.7.
**Architecture:** Deterministic Blender source art exported as semantic FBX assemblies; private Unreal project imports owned meshes and materials, assembles dynamic lighting and native Hello actor, and saves a conventional level. No shared editor generation, content reuse, Git mutations or delegation.
**Spec:** User assignment and AGENTS.md. Cream plaster, dark timber, muted teal roofs, sandstone masonry, layered evergreen hills. The railway curves in front of the station into an east-side tunnel; an accessible ramp links the forecourt to the platform and a gravel trail climbs behind the building.

- [x] Source artwork: terrain, railway/ballast/sleepers, station with roof and joinery, platform/ramp, arch tunnel, cargo shed, benches, lights, signs, clock, baggage, crates, fences and hillside trail.
- [x] Private UE assembly: owned materials, collision, PlayerStart, native ScreenDebugLogger, dynamic illumination, no external packages/BuiltData.
- [x] Reload validation: exact 10000 cm terrain bounds; route/collision samples; recursive Asset Registry dependencies; required actors and private roots.
- [x] Render: actual UE SceneCapture2D / editor renderer at 1920 × 1080, four specified cameras, inspect images and log actual settings.
- [x] Close editor, publish only owned assets and map, verify hashes, complete RESULT.md / STATUS.json.

Review focus: rail gauge and sleeper direction on curves; tangent alignment of tunnel portal; accessible slope and player floor; FBX coordinate/scale correctness; clean nonblack images and dependency isolation.

Execution rulings: user explicitly approved direct completion without design reconfirmation; user forbids subagents and commits. Use private scratch instead of a Git worktree. Asset scripts are evaluated through real engine evidence rather than unit tests mirroring geometry generation. Records remain in this owned Work directory.
