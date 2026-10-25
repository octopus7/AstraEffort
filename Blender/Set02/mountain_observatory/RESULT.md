# Mountain observatory — ready for review

Finished independent Set02 asset based only on `REF/Set02/mountain_observatory.png` and the approved task. All files below are stable and contained in this assigned folder.

- Recorded production start: **2026-10-23T12:15:41+00:00 UTC** / **2026-10-23T21:15:41+09:00 KST** (timer recorded after brief/reference inspection).
- Finished: **2026-10-23T12:36:17.606962+00:00 UTC** / **2026-10-23T21:36:17.606962+09:00 KST**.
- Elapsed recorded wall time: **1236.61 seconds**. Three measured build/render script runs: **299.95 seconds** total. Final independent validation: **7.05 seconds**. No image generation, installations, shared scene use, or Git mutations.

## Delivered

- [Native BLEND](mountain_observatory.blend), [GLB](mountain_observatory.glb), [FBX](mountain_observatory.fbx).
- [Source](build.py), [independent validator](validate.py), [validation report](validation.json), [capture manifest](capture_manifest.json).
- Actual inspected Blender renders: [hero](renders/hero.png), [rear](renders/rear.png). Both 1440×1080, Cycles CPU, four threads, 32 samples, denoising, orthographic camera, large soft studio lights, warm pale gray background. Final view and timestamp details are in the manifest.

## Model and checks

**335 named editable mesh components; 226,944 evaluated triangles; 114,060 native vertices.** True transformed-vertex dimensions: **7.0500 × 6.0600 × 5.9949 m**. Bounds minimum `[-2.660000, -3.400000, 0.000000]`; maximum `[4.390000, 2.660000, 5.994853]`. Meters, Z up, front −Y, lowest asset surface exactly Z=0.

The dome consists of two thick shell sides, a separate closed rear panel, ivory curved shutter rails, recessed dark tracks, rollers, and a bearing assembly. Its front slit is physically open. The short upward optical telescope has a hollow barrel, recessed blue lens, trunnions, fork and pedestal. The hollow rotunda has real cut door/window openings; the rounded service annex has recessed openings, louvers, rear service door, terrace railing and attached utility parts. Broad curved steps, foundation bands, masonry joints and restrained hardware complete the reference form.

All final modifiers are baked, with explicit triangulation for export parity. `ASSET` contains geometry only; `STUDIO` contains camera, lights and floor. GLB/FBX export only `ASSET`. Each component has a real UV layer, smart-projected islands and 0.018 island margin; these are independent component layouts, not a shared atlas. Materials are named solid Principled PBR colors; no external images are required.

A separate Blender 4.5.12 LTS process opened the saved BLEND, then imported GLB and FBX into fresh empty scenes. **Every final check passed:** nonempty finite geometry, exact triangle parity, transformed bounds, UV/material coverage, zero missing images, zero zero-area geometry triangles, zero degenerate UV triangles, baked modifiers, no exported studio objects, and closed component topology after position-only welding. Maximum bounds delta: GLB **0.000000000 m**, FBX **0.000000242 m**. Geometry area threshold: 1e−12 m²; UV area threshold: 1e−14.

Two targeted saved-scene ray tests also passed: the front slit ray reaches the closed **rear** panel, and the optical-axis ray first reaches the inset lens through the hollow barrel. Final SHA-256 hashes and file sizes are recorded in `validation.json`; no asset or render was changed afterward.

## Commands and corrections

Private build command (three runs, exit 0):

```text
"C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background --factory-startup --threads 4 --python-exit-code 1 --python "D:/github/AstraEffort/Blender/Set02/mountain_observatory/build.py"
```

Fresh validation command (final exit 0):

```text
"C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background --factory-startup --threads 4 --python-exit-code 1 --python "D:/github/AstraEffort/Blender/Set02/mountain_observatory/validate.py"
```

The initial check correctly failed on four collapsed UV triangles caused by near-duplicate dome bevel vertices. A 1 μm position weld removed the slivers before unwrapping. An optical-axis diagnostic found a barrel end cap hiding the lens; the final barrel is hollow. Rear-image inspection also found a conduit partly buried by the rounded wall; it was moved outward with attached saddles. Final front and rear images were inspected after correction. Diagnostic evidence and execution logs remain in this folder.

## Decisions and limits

The reference's rear closure is reconstructed as a fixed back shutter while the front remains open. Rear service details are coherent new hidden-side construction. This is a clean, restrained rounded static asset: no mechanism rig, animation, collision, LODs or full traversable building interior. Glazing and lens use opaque coated PBR surfaces; no optical/refraction simulation. No image textures, generated wear, or texture atlas were requested. FBX material appearance can vary by importer; the native file and GLB retain the intended PBR material assignments. Assembled components intentionally intersect at their attachments and are not one boolean-union mesh.
