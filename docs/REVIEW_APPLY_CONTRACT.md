# Review and apply — implementation contract

Status: specified, not implemented. Next bounded implementation task; no model or apply action is authorized by this file.

## Owner outcome

From Orchard Crew, inspect a completed task's exact changes and test evidence, then explicitly apply those reviewed changes to the selected working project. Show whether work is ready for review or actually applied. Keep a recovery copy and give plain-English evidence on success or failure.

## First implementation scope

One worker, one local Orchard project, one human-reviewed result at a time. Use the existing Codex backend; comparison research does not justify replacing its already-verified execution. No Claude dependency, fleet, branch, worktree, PR, deployment, remote hosting, plugin install or new autonomous task. Preserve Seed Box data and behavior and the understated interface.

Begin with modifications to existing files in the exact captured source manifest. New files, deletions, binary files, oversized results, changes to original protected tests, symlinks and path traversal are held for owner decision rather than applied by an incomplete mechanism. Expanding that supported set is a later explicit task.

## Data and lifecycle

Keep execution status and application status separate. Existing DONE receipts remain historical execution evidence. Display completed supported results as **Ready for review** until application succeeds, then **Applied**. BLOCKED/NEEDS_OWNER_DECISION remain plainly visible; do not imply that a passing generic suite proves the requested outcome.

A review receipt must bind task ID, source manifest and hashes, captured result hashes, the human-readable diff, mandatory test evidence and the limitations of that evidence. Persist/reconstruct from immutable captured data; never rebuild an already-approved patch silently from a mutable workspace. Render task text and diff as text, not executable HTML.

GET review must be read-only. POST apply must carry explicit owner consent and the exact review ID/digest shown. Apply no files on missing consent, old/different digest, incomplete tests, source drift or unsupported changes. Require same-origin/host protections at least as strict as current Seed Box writes. Do not interpret a model approval or a previous task-run checkbox as apply consent.

## Safe application and recovery

- Recheck every captured original, reviewed result and path immediately before writes. The owner application can change while a task runs. A lock serializes Orchard operations but is not a filesystem-wide lock: document remaining external-writer race limits and narrow them before claiming transactional guarantees.
- Restrict writes to reviewed canonical project paths. Reject symlink parents/targets, traversal, alternate manifests and result mutation. Never write auth/profile files, databases, logs or policy paths through a broader unchecked path.
- Before changing application source, retain original bytes and hashes in the ignored recovery location. Stage result files on the same filesystem. Preserve original file permissions; ensure a failed preparation does not change the project.
- Handle partial-write failure explicitly: restore only the files written by this apply if they still match this operation's bytes. If an external writer changed them, stop and preserve evidence rather than overwrite their work. Do not claim global atomicity for multiple file replacements.
- Persist a durable application/recovery receipt, so a process interruption is detectable. Startup recovery requires review; it does not silently resume an apply or start a model task.
- Repeated apply requests must be idempotent: no second write, duplicate backup, additional model turn or reapplication over newer owner changes.
- Recovery requires explicit owner consent, checks that applied files have not drifted, and restores precisely the saved originals. Never delete the recovery copy merely because application succeeded.

## Required acceptance checks

1. Real Seed Box regressions still pass; app startup and save/list remain usable.
2. A completed result presents the exact changed paths/diff, real test results and Ready for review.
3. Missing/denied consent, stale review digest, changed original/result bytes and unsafe paths make zero application writes.
4. Applying a known heading change updates the served browser page and shows Applied, with a recovery receipt.
5. Duplicate approval returns the existing outcome without modifying files.
6. A preparation failure leaves original files intact; an injected later failure demonstrates the documented rollback path and preserves conflicting external edits.
7. Owner-approved recovery restores the exact prior bytes. A drifted applied file is held for a decision rather than overwritten.
8. Task completion or application never starts another task. Application does not require another model inference.
9. API and rendered diff resist origin misuse and HTML/script content. Verify the real browser result; a backend success string alone is insufficient.
10. One-off verification scripts/temp projects are cleaned up. Keep reusable regression checks in tests/ and owner recovery/evidence in ignored local storage.

## Stop condition

Deliver tested code and browser evidence for the supported existing-file flow; state unsupported paths and crash/race limits honestly. Do not advance to live Rikuri projects or unrelated backlog items in the same task.
