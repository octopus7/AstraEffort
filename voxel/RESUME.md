# Voxel production completed

All 18 themes, 81 models and 162 large/half variants are complete and parent-accepted. No model task remains queued. The 45-model checkpoint is preserved in commit 63e475d and the 73-exported-model checkpoint/overview in commit b3992e3. CHECKPOINT.json is a historical record of that intermediate state. The later nine themes add 36 models to the 45-model baseline.

Use README.md, index.html, overview_half_all.png and delivery_manifest.json for the current delivery. Every individual preview remains present. EXPANSION_STATE.json retains actual acceptance, pause/resume and completion records, separating recorded pauses from elapsed phase time. Per-theme RESULT/STATUS and validation evidence retain timings and limitations. References and prompts live in REF/voxel.

The old prepare_delivery.py and prepare_checkpoint.py target historical snapshots; do not run them over the final catalog. prepare_expanded_delivery.py verifies and reconstructs the final catalog/archive from frozen results after the 81-model half overview is ready.
