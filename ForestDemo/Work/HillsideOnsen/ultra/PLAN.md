# Implementation plan

- [x] Prepare a private project and original authoring source under owned paths.
- [x] Author terrain, terraced foundations, baths, buildings, paths/stairs, rails, stream and vegetation; generate surface maps and measured UV evidence.
- [x] Import into private Unreal, author distinct materials and animated water/steam, assemble and save a non-World-Partition map.
- [x] Reload from a fresh process; test bounds, foundations, routes, collision, actual PIE, UVs/materials/effects and recursive dependencies.
- [x] Capture and inspect actual 1920x1080 overview, top_down, hot_spring and village_path views plus timed effect evidence.
- [x] Confirm private editor closure, publish only owned validated assets/map, compare hashes, and write separate RESULT/STATUS.

Interfaces: authoring exports mesh FBX files, material descriptors and a scene manifest; Unreal consumes those and writes packages. Verification consumes the saved map plus source evidence. Capture consumes the same verified packages. Publication checks capture and package hashes before copying. No source-art task is considered a runtime validation.

Implementation and evidence stay in this Work folder. Skill defaults concerning Git commits, worktrees, shared docs paths and repeated approval gates are superseded by the user's explicit isolation, no-Git and autonomous-execution instructions. Do not write redundant unit tests for one-off art authoring; perform geometric checks and engine-level behavioral verification.
