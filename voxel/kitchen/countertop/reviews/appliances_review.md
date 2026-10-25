# Independent appliances review

**Spec compliance: PASS. Visual/technical quality: PASS.** No blocking or minor defect requiring correction was found.

Reviewer: countertop worker. Read-only target: `voxel/kitchen/appliances`.
Actual start: 2026-10-25T05:38:00+00:00 UTC / 2026-10-25T14:38:00+09:00 KST.  
Actual finish: 2026-10-25T05:40:42.880561+00:00 UTC / 2026-10-25T14:40:42.880561+09:00 KST.  
Review wall time: **162.881 seconds**; independent native/hash check: **2.515 seconds**.

## Spec-compliance evidence

- Exact seven required appliance slugs with fourteen VOX150 files and fourteen 768px PNGs.
- All saved native dimensions, common palette, coordinates and metadata checked independently.
- All seven saved half grids exactly match 2x reduction of their saved large grids, with doubled meter scale and identical physical extents.
- All 64 declared functional probes independently resampled from saved native data.
- All 67 frozen files match SHA256; native/PNG hashes agree across metadata, capture and validation evidence.
- All seven camera/light/render pairs match, with Cycles CPU, four threads, 24 samples, denoising and AgX.
- Read-only pipeline inspection confirms surface construction consumes reparsed VOX, using the shared build_surface and add_studio helpers.
- No forbidden scene, exchange mesh or engine artifacts found.

The refrigerator occupies about 1.984m vertically within its 2.048m grid; the kettle grid is 0.3392m high. These are consistent with the requested household scale guidance.

## Visual and technical observations

All fourteen final primary PNGs were individually opened with `view_image`, followed by the labeled contact sheet. The final repaired hood images, rather than superseded captures, were reviewed.

| Asset | Large preview | Half preview |
|---|---|---|
| double_door_fridge | Cream double-door silhouette is clear. Door seam and the two sage pulls remain visibly separate, with clean stepped corner rounding, plinth and feet. Whole model is framed. | Door separation, projecting pulls and base survive reduction. The outer form is intentionally more angular; no clipping or filled grip clearance is apparent. |
| range_oven | Four burner rests, four front knobs, oven pull and opaque blue-gray oven window read clearly. Cream/sage body and charcoal grates suit the brief. | All four burners and knobs remain distinct. Oven-pull clearance is visible and the closed door remains readable. Same-camera framing is preserved. |
| microwave | Wide microwave shape, opaque framed window, sage handle, dial/button and right-side ventilation slots are recognizable. Vents are actual visible recesses. | Handle remains separate from the front and all four side slots survive. Control shapes and the window border remain legible despite coarser steps. |
| dishwasher | Lowered static door, open wash chamber, two rack fronts, visible plate spacing and door dispenser are readable. Interior is dark but the important rack structure is distinct. | Open chamber and rack gaps survive native reduction; plates remain individually separated. Some upper items are naturally hidden behind the top rack/roof in this one camera. |
| range_hood | FINAL repaired preview: both visible sloped canopy surfaces are continuous with no unintended slit. Top duct opening, cream chimney, sage trim and front controls are clear. | FINAL repaired preview: continuous stepped canopy, open top duct and three control buttons remain readable. Underside filter is outside this camera view and is assessed via saved-native probes. |
| rice_cooker | Rounded cream cooker, separated sage lid band, open carry-handle loop, lid fittings, front control panel and feet form a clear appliance silhouette. | Carry-handle opening remains visible and control blocks stay distinct. Coarser circular steps are expected; no broken connection or unintended closure is visible. |
| electric_kettle | Kettle has a visible open spout mouth, generous open handle, lid, electric base, switch and opaque level panel. Its full silhouette fits the image. | Handle loop and spout mouth remain open and readable. Lid, base and switch remain distinct. The chunky spout and handle match the restrained voxel style. |

**Repaired hood:** no unintended side slit remains in the final views. Six saved-native checks per resolution confirm canopy shell, central airway, top duct, filter gap, chimney wall and filter bar.

## Findings and limits

Findings requiring owner action: **none**. No target files or frozen countertop production files were modified. All 73 countertop frozen production hashes also remain unchanged.

- Single prescribed three-quarter camera does not expose every rear/underside surface; those functional regions were checked in saved native data where probes are supplied.
- Glass is intentionally opaque. Dishwasher uses one static lowered-door pose; no operation, animation or mechanics are implied.
- This review parsed saved files and recomputed reduction/features, but did not rerun target authoring, rendering or the target development suite. Authored-to-saved roundtrip is supported by hash-matched producer evidence and pipeline inspection.
- Production timings are reported by the producer; this review records its own real timestamps separately.

Detailed per-image SHA256 values and inspection notes: `appliances_review.json`. Independent parsing, scale, reduction, probe and frozen-file results: `appliances_check.json`; reproducible read-only checker: `check_appliances.py`.
