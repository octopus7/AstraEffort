# Independent implementation and rendered-scene review

Review recorded 2026-10-22, with final evidence read at 13:43–13:44 UTC / 22:43–22:44 KST. This is a read-only review of WindmillFarm/ultra Work and its private Project only. The reviewer did not run UE or Blender, use Git, read another theme's resources, or change implementation/assets. This report is the only reviewer-authored file.

## Initial decision — superseded by the correction review below

**Hold publication for the barn prop-placement correction below.** The scene design, four required rendered views, ownership closure, saved-map load and latest runtime evidence otherwise support delivery. After correcting the props, save and verify the changed private map, refresh affected scene evidence, close the editor, and apply the parent's publication/hash gate. This review does not certify later edits or the shared published copy.

## Actionable finding

### P2 — Barn-side/rear props float or intersect the architecture

In the reviewed `ue_assemble.py`, lines 21 and 23–25:

- `StackedHayTop` is placed at `(18.2,19.5,1.05)` metres. `QA/SM_HayBale.json` gives local minimum Z=0 and maximum Z=0.784500003m. Applying `landscape_design.height()` to the lower bales puts their tops at 0.771753229m and 0.772552873m. The upper bale consequently floats at least **0.277447127m above both supports**.
- `StackedHayB` at `(19,19.6)` crosses the rear wall. `Art/Farm/generator.py:289` puts `Barn_BackPlaster` at local Y=3.43m with thickness 0.24m. With `BARN=(23,16)`, the wall occupies world Y=19.31–19.55m. The bale spans Y=19.2185–19.9815m and lies within that wall's X extent. The upper bale crosses the rear/side corner as well.
- `RainBarrel` at `(27.8,13.4)` has measured radius 0.40997049m, while the east plaster wall occupies X=27.74–27.98m (`Art/Farm/generator.py:251`). Its centre is inside the wall thickness, rather than outside the building.

Move the full hay stack to clear ground outside the barn envelope, set the top bale from the measured supporting surface, and move the barrel beyond the frame/window envelope. These require actor-placement changes only. The standard final camera views largely conceal the hay stack, so use a targeted contact check as well as the regular captures. This was reported directly to the parent during review.

## Resolved during review

The initial final run's `validation.json` at 13:37:56 UTC reported `all_passed=false`. `capture_final_error.json` identified `PlayerController.get_pawn()` as unavailable, aborting before the runtime checks. Its process still exited 0 because the pipeline caught the exception and quit normally. The parent corrected the reflected call to `get_controlled_pawn()` and ran a fresh runtime check while retaining the finished images.

The replacement validation at **2026-10-22T22:40:40.620548+09:00** reports all 15 checks true. Its detail supports possession of `DefaultPawn`; three blocking traces against `FarmGround`; a blocking trace against `WindmillTower`; a non-overlapping pawn sweep stopped by the ground; 200cm horizontal displacement; and ended PIE. The old error is historical, not evidence that the replacement check failed. Publication must check the required keys and `all_passed`, not process exit alone.

## Evidence and successful checks

- Read ASSIGNMENT, DESIGN and PLAN before reviewing `ue_common.py`, `ue_import.py`, `ue_assemble.py`, `ue_capture_pipeline.py`, `Run-Private.ps1`, the UV/source manifests and independent mesh QA. Also read the relevant original barn/hay source and private-map filename.
- Inspected all four `Screenshots/Polish` renders and all six final PNGs. The final overview and top-down view show a coherent bounded farm, four planted fields, orchard trees, connected broad dirt paths, the landmark windmill, barn, shed and working props. The corrected actors are upright. The muted greens, terracotta, plaster and timber fit the calm rounded game-art direction. No prohibited faces, hearts or decorative clouds were observed.
- Windmill and barn scale/readability are credible in the rendered views; the mill foundation/entrance steps and visible barn footprint have plausible ground contact. Main path approaches remain visibly open. This is a visual assessment of the shown views, not an exhaustive actor-contact proof.
- Final `windmill_motion_t0.png` and `windmill_motion_t1.png` visibly differ in rotor angle. Their recorded world times are 15.959140308s and 20.176052313s. This supports visible material-driven motion; it does not establish physical rotor animation/collision.
- Independently parsed each final PNG's IHDR: all six are **1920×1080**. Capture metadata records actual UE5.7 SceneCapture2D, D3D12 SM5, High/sg2, FinalColorLDR/RGBA8/gamma2.2, camera positions/rotations, warmup frames and capture times.
- The latest validation records the saved map reloaded, 10000.001953cm ground X/Y extents, non-World-Partition, no external actor/object or BuiltData files, dynamic lighting and upright static actor placement. The dependency closure contains only `/Game/WindmillFarm/ultra/**` and `/Game/Maps/WindmillFarm_ultra`.
- Reviewed import and assembly code confines new assets to the owned root. Engine sphere/cubemap references are read-only built-ins. `Run-Private.ps1` targets the new private project through the shared isolated runner; the inspected timing records identify priority 2. Bootstrap creates a separate content-only private project and its own Config. No cross-theme creative-resource references were found in the reviewed scripts.

## Material/UV claims and remaining limitations

1. The surfaces use original deterministic procedural PNG textures, not an image-generation service. `Art/Textures/manifest.json` explicitly records no external images and `image_generation_service_used=false`. This matches the autonomous new-theme design; do not describe them as image-generated outputs. The source texture validation reports deterministic hashes and normal-vector checks, and the renders show distinct wood, stone/plaster, roof and canvas treatment.
2. Material texture samples use UV1, except the ground macro/detail material. UV1 is a scalar multiple of unique UV0, so its orientation is retained. The independent FBX review is the authoritative strict check: the tiny MillTower degeneracies and two microscopic positive-area overlaps remain explicit accepted exceptions. `validation.materials_and_uvs=true` proves imported channel count/material ownership and the looser source summary, **not literal zero degeneracy or zero overlap**.
3. The approximately 128px/m target is an unscaled source-mesh mean. Scene instances are deliberately scaled without inverse UV compensation: trees 0.85–1.2 imply approximately 106.7–150.6px/m; grass 0.65–1.8 implies 71.1–196.9px/m; rocks 0.65–1.5 imply 85.3–196.9px/m; crops 0.84–1.10 imply 116.4–152.4px/m, before local triangle variation. Preserve these instance-scale exceptions and the independent organic-surface density outliers in final reporting. Ground intentionally uses its separate 20.48px/m macro and 512px/m detail scheme.
4. Runtime evidence is a possessed Engine `DefaultPawn`, explicit trace/sweep checks and scripted translation. It is not a recorded human input walkthrough, walking-character implementation, exhaustive building collision test or interior-access test. The tower is the building actually probed.
5. The windmill rotor uses material World Position Offset and has collision disabled. Describe it as visual sail motion. The authored window material is opaque; a low roughness value does not create transparent glass. Neither limitation blocks the requested exterior farm scene.

## Final-image snapshot hashes

These are the images actually inspected before the prop correction; replacement evidence requires new hashes.

| Image | SHA-256 |
|---|---|
| overview | F726B906F641C2C3ECE3B54BB4BCE8676EB57D0F95AA0075BF2BABAA0E155832 |
| top_down | B47CF3E8F7D4B0A8B1D637A288E9471A9A66B7E76D74D95BE4E97B9B94CED7A5 |
| windmill | 9A174C9D2BD960FD0AA5C8763E301FA376B2BDCE8B8DD795DC507E29AB20F4DA |
| farm_detail | 5F23CBF015E81E00983E8EF774E259F88D318AE12330F359477F574D36F1C76C |
| windmill_motion_t0 | AEBF07482C9B5536B567F49EB68F09813B251C543726EC1C1BA0867DA238415A |
| windmill_motion_t1 | A1BE327176DFE281A2C89406B7A279C14557F7FCDEBA66FFE92FD67951523245 |

No external references were required. No final publication, shutdown or shared delivery hash verification was performed by this reviewer.

## Correction review — 2026-10-22 13:49 UTC / 22:49 KST

**Current decision: no remaining actionable review blocker; delivery may proceed through the parent's publication gate.** The reported hay-stack and rain-barrel placement defects are resolved. The material/UV, DefaultPawn and visual-rotor limitations above remain applicable and should remain disclosed. This decision covers the corrected private saved scene and evidence; it does not claim verification of a subsequently copied shared delivery.

Read `QA/prop_fix.json`, corrected assembly placement, the saved-map contact-check implementation, and the latest validation. Visually inspected the new `prop_contact.png`, refreshed `farm_detail.png` and refreshed `overview.png`. The diagnostic image shows the three-bale stack supported on clear ground behind the barn, with no wall intersection; the farm-detail image shows the barrel standing outside the east wall. The broader composition remains consistent.

The correction record at 13:46:55.973447 UTC places the two lower bales at design coordinates (18.0,22.0) and (19.25,22.0), the upper at (18.625,22.0), and the barrel at (28.7,13.4). Assembly now derives the upper bale's Z from the imported mesh bounds and supporting actor heights. The saved-map bounds check records:

- Upper-bale gaps to its two supports: **0.485401786cm and 0cm**, with positive XY overlap against both supports.
- Minimum clearance between the hay stack and the barn's complete bounds: **162.349873cm**.
- Barrel clearance from the east plaster-wall plane: **31.002953cm**. The rendered placement also clears the visible frame/window geometry.

The independent fresh-process `verified` phase completed at **13:48:18.0437385 UTC**, exit 0, priority 2, with 0.2425472s queue wait and 27.7114636s execution. `ue_verified.py` invokes the runtime-only entry point. Its validation, timestamped **22:48:14.046872 KST / 13:48:14.046872 UTC**, reports **all 16 required checks true**, including saved-map reload, owned dependencies, the added prop contact/clearance check and all previous PIE/collision/movement checks. This resolves the condition that validation must apply after the placement changes.

All seven refreshed PNG headers independently read **1920×1080**. The capture manifest records the refreshed capture sequence at approximately 13:47:04–13:47:18 UTC, including the added prop-contact view. The reviewer did not run UE/Blender or mutate assets to perform this follow-up.

| Corrected evidence | SHA-256 |
|---|---|
| overview.png | 552D76EE6B4F6F558F056B737BDA4294ACB3691821C1EB840B2288AC7986633A |
| top_down.png | E55BB58A0937BC0F81221A798F80BACB2E0EE9F0ABAA506C0B1F805F93E6B523 |
| windmill.png | 150603C2687079E151FF41C00643171C758A7D965F742AA3BACECBA0F4C87FDA |
| farm_detail.png | 13346B956F5184B41324117860FC5B1BEDFEF4B64FE97DE11EAB6C7E9AE879EF |
| windmill_motion_t0.png | 4F4D7402FBDCFCF4DA4C8DACB366777FE0624B893F6CA36D2CBE7D5827D2E7AD |
| windmill_motion_t1.png | C2C82E3D63273810DAA40614280BC522F2CE762FC05F127339A4218B4D1520F9 |
| prop_contact.png | 8AA52A7CACB0E49DA126F70EF80AFDD8B6F7CB1E29E04478E6C1D51D619F25F1 |
| validation.json | D9A8FAF7326FCDA3217CB0D22FA5575497F8DF973662B40BC281107788924F31 |
| QA/prop_fix.json | D874D5E6481EE21294C0E8478C1D91B04D371567FECB73B1D18AAFC8BEB3EF9E |
