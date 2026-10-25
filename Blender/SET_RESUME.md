# Ongoing ordinary rounded model production

Read SET_BATCH_STATE.json for the current group and per-set progress, SET_BATCH_PLAN.md for selected themes, and SET_WORKER_BRIEF.md for output rules. Main owns these documents, reference generation and Git. Workers own only their assigned SetNN directory; its REF subfolder is main-owned.

Latest user instruction on 2026-10-25 KST: continue choosing and producing further sets after the original nine, until the user says to stop. Do not stop automatically at Set11 or after any subsequent completed group. Three sets per group, four models per set, one explicitly configured gpt-6-astra/max worker per set. A separate Fast selector is unavailable. No extra agents beyond these three set workers.

Main generates one image per model sequentially with built-in image_gen. Save originals and prompts in REF/SetNN and preserve identical copies in Blender/SetNN/REF. Existing Set01/02 references have also been copied locally. Workers may view their own references to author geometry, but neither main nor workers inspect the generated model renders or run model validation. The user defers review. Only output process completion, expected nonempty files and delivery inventory are checked.

Commit each finished group before starting the next group's reference production. User explicitly authorized these commits. No push. Git index writes need sandbox escalation; use the existing exact-path inventory helper, never stage unrelated work or clear an existing index. Blender/BatchTools/scratch stores ignored commit receipts; prior receipt hashes are incorporated into the next tracked ledger update. The current batch's containing_commit value resolves to its own delivery commit.

Group 1 (Set03–05) committed 2140c8bf1ae5196efb92cb486076688118f1d66b. Subsequent progress lives in the state ledger and ignored commit receipts. Do not modify or resume the already-complete voxel library, which was committed separately as dcbaeb3.

Useful main commands, run with Blender's bundled Python 4.5 and -X utf8:

- BatchTools/batch_control.py begin NUMBER: carry previous commit receipt into state, start next group.
- BatchTools/prepare_next_prompts.py NUMBER: create initial group 2 or 3 prompts/task roots once, after the prior commit.
- BatchTools/prepare_continuation.py Blender/BatchTools/groupN_selection.json: for group 4 and later, append three new main-selected themes/assets to the ledger and plan and create their prompts/task roots; requires the prior commit receipt. Then run begin NUMBER. The main-authored group4_selection.json is already prepared for Set12–14.
- BatchTools/record_reference.py SET SLUG SOURCE START FINISH: save one completed image, mirror references, update reference count.
- BatchTools/batch_control.py dispatch SET WORKER: record actual worker dispatch after all four references exist.
- BatchTools/batch_control.py collect NUMBER: only after all three workers freeze produced_unreviewed; inventory required nonempty files and successful process records, update catalog.
- BatchTools/batch_control.py stage-list NUMBER: prepare exact allowed paths while index is empty.
- BatchTools/batch_control.py commit NUMBER: escalated Git add/commit of that exact inventory, then ignored receipt.

If a user stop arrives, stop launching work and notify the active workers immediately. Preserve all existing outputs and record actual incomplete status; never claim incomplete outputs are complete or reviewed. Continue only when the user resumes.
