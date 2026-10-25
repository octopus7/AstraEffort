# Kitchen appliances implementation plan

**Goal:** Seven distinct household appliances, each as large and half native VOX plus an actual 768px preview.
**Architecture:** A pure `make_assets()` authors native occupancy. A local runner writes and reparses VOX, then uses the read-only generic surface and studio functions for transient render geometry. A separate validator checks saved data and functional probes.
**Tech stack:** Python/NumPy, MagicaVoxel VOX 150, isolated Blender 4.5 Cycles CPU; PowerShell/System.Drawing for a contact sheet.
**Spec:** `../BRIEF.md`.

## Binding limits

- Write only this appliances batch; no Git, shared utility edits, extra agents, mesh or scene outputs.
- Fixed supplied palette, front -Y, Z up; longest large axis 128 and half 64; all large axes even.
- Same physical extents and cameras across each resolution pair; 768px, 24 samples, denoising, AgX and four CPU threads.
- Functional gaps survive reduction. Glass is opaque. Dishwasher uses one static open pose.

## Work and review focus

- [x] Author `build.py`: fridge door separation and grips; stove burners/oven grip; microwave controls/grip/side vents; open dishwasher/racks; hollow hood duct/filter; cooker lid/carry grip; kettle open spout/loop grip.
- [x] Write and run `preview_pipeline.py` using reopened files, no `run_theme()` or exporters. Record build/render timings and camera/light settings.
- [x] Run `validate.py` on every file: VOX headers, full occupancy/palette roundtrip, exact scale relationship, coordinates, hashes, PNG dimensions, meaningful cavity/clearance probes in both sizes.
- [x] Inspect all 14 actual previews with image tools; fix only demonstrated defects. Assemble `overview_half.png` from rendered half previews.
- [x] Freeze hashes and write actual `RESULT.md`, `STATUS.json`, timing, validation and image-inspection evidence; await assigned same-kitchen cross-review.

## Execution rulings

The user explicitly authorized autonomous production and exactly three workers, so no design approval, worktree/Git action, additional agent or skill-generated shared workspace is used. This batch plan and ledger remain in the assigned root. This is native art authoring with required artifact verification, not a new general-purpose software feature.
