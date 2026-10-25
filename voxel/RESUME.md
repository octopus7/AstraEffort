# Voxel progress checkpoint

The user requested a commit of progress so far. All three voxel workers are frozen; no voxel Blender job remains active. Resume only after the next user continuation. Earlier completed outputs remain unchanged.

- Parent-accepted: 13 themes, 61 models, 122 large/half variants. This includes the prior 45-model checkpoint (63e475d) plus forestry, construction, fire_rescue and bakery, four models each.
- Submitted and frozen: airfield and recycling, eight more models / sixteen variants. Airfield has a passing parent format report; its primary image review is still pending. Recycling has passing worker format/native/visual checks, but parent verification and image review remain pending. Neither theme has parent acceptance yet.
- Work in progress: geothermal, four models / eight variants. The existing first export finished with exit 0. No geothermal primary preview has been inspected and independent native/import verification remains undone; see geothermal/RESULT.md. Do not describe it as complete.
- Not started: canal and camping, four models each. Their references are already ready.
- All nine new-theme reference sheets, prompts and generation records are saved under REF/voxel, generated sequentially by main. No further reference generation is needed.

Next: inspect all eight airfield previews and confirm its frozen parent report, then accept with _tools/accept_expansion.py. Verify and inspect all eight recycling previews, then accept. After continuation, worker1 may start canal following airfield acceptance; worker2 may start camping following recycling acceptance. Worker3 resumes geothermal verification and any demonstrated corrections. Preserve original worker start times and record the checkpoint pause separately. Main coordinates final reviews and packaging. Exact names are in EXPANSION_STATE.json.

Workers remain gpt-6-astra/max. A separate Fast API setting is unavailable. Theme ownership remains strict. Use isolated background Blender with four threads; do not modify ForestDemo, other Blender sets, shared application state or global addons. Only main runs Git.

Large grids have longest axis 128; half grids divide every axis by two and double cell size, retaining physical grid extent. Each variant has VOX, BLEND, GLB, FBX, preview and metadata. Main acceptance requires fresh format verification and personal inspection of every final primary preview.

CHECKPOINT.json records current counts and fresh hash/syntax checks. The existing index.html and delivery_manifest.json still describe the earlier 45-model catalog; the first39 manifest and original local ZIP remain preserved. New outputs are directly under their theme folders. Do not run old prepare_delivery.py or prepare_checkpoint.py over this checkpoint. Final prepare_expanded_delivery.py must wait until all 15 expansion units are accepted, then build the 18-theme / 81-model / 162-variant catalog and archive. Its source is syntax-checked only so far; final runtime packaging is pending.

No push was requested. This is a progress checkpoint, not completion of the 81-model task.
