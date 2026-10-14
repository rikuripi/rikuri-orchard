# Verification record

## Working baseline — October 13, 2026

The first real Codex task changed the Orchard Crew heading from “Good work takes good company.” to “Good work takes extraordinary teamwork!”.

The initial authenticated turn completed, but native project-test imports failed because Homebrew SQLite's separate dynamic library was denied by the sandbox. The adapter was corrected with narrow runtime read grants, canonical Python/SQLite loading, and a preflight SQLite query before inference. After correction, all 21 tests passed inside native Codex command/exec. These checks used an empty disposable profile and refused model threads/turns.

The owner then explicitly submitted and approved a fresh heading task. The running Orchard displayed DONE with all 21 tests passing under the native sandbox. Inspection confirmed exactly one heading replacement, unchanged baseline tests, and an unchanged original source hash. After separate explicit owner permission, that index.html change was applied and visually verified on the running browser page.

This proves one real bounded task plus separately approved application. It does not prove a general software factory, a portable backend across OS versions, or automated satisfaction of arbitrary task descriptions.

The 21 repository tests include four original Seed Box tests plus checks for request/origin/consent validation; one worker; persistence/restart behavior; no automatic retry; safe snapshots and symlinks; recognizable secrets; protocol completion/failure; denied approvals; nonzero and zero tests; output/time bounds; subprocess cleanup; changed-test rejection; a clearly labeled simulated end-to-end run; SQLite runtime grant scope; and SQLite failure before model startup.

Protocol fixtures simulate model events and test output. They are not evidence of additional live model runs. Ordinary unittest execution is not evidence that the OS sandbox works; that is established by the separate native checks above.

## Repository baseline checks

A fresh local clone of baseline commit 2f9a15a passed all 21 tests. Its app.py started on an ephemeral localhost port using a disposable database; health reported Codex disabled, the approved heading was served, and Seed Box HTTP create/list succeeded. The test server was stopped afterwards. These ordinary localhost checks are separate from the earlier native-sandbox evidence.

The five executable/UI/test files matched the installed working Orchard byte-for-byte. Git ignore checks covered the dedicated sign-in profile, .env, Codex credentials, databases and sidecars, disposable runs, logs, caches and page backups. A known-signature credential scan found no such values in the selected source/docs; it is not an exhaustive secret-detection guarantee. Only the explicit source/docs/test manifest was staged.

The intended remote is https://github.com/rikuripi/rikuri-orchard.git. GitHub's connected app, git ls-remote and the local gh repository request returned not-found. Local gh identified its signed-in account as hchengit. That initial attempt made no push. After the owner granted access, GitHub confirmed the repository exists, is private, uses main as its default branch, and permits hchengit to push. The remote had no refs before import. Publish the prepared baseline using a normal main push, then verify its remote commit and fresh remote checkout.

## Pending

Installation of v0.3 into the owner’s running copy and a fresh authenticated v0.3 task; resumable native approvals; independent acceptance checks; robust cancellation and process/resource management; hard spend/resource limits; effective capability audits (including machine-managed configuration); more representative native tasks; other OS/runtime versions; Claude integration; third-party factory comparisons by experiment; Rikuri PI/rikurinode pilots; remote hosting.

## Comparison preparation

The project suite now has 27 passing tests: the existing 21 plus six reusable authored-fixture checks. The new cases demonstrate exact-diff acceptance for a heading and behavioral acceptance of fractional means independent of a weak green baseline suite. These checks execute only authored synthetic fixture code, not provider outputs. Fixture projects use TemporaryDirectory and subprocess timeouts and clean up after use. No live comparative model run, new credential access or package installation occurred. The existing native worker's fixed snapshot remains unchanged and includes its original 21 application/adapter tests.

Read-only installed help/version evidence and current official documentation informed the backend decision and REVIEW_APPLY_CONTRACT.md. Claude 2.1.282 has not been declared isolated or benchmarked; its version/authentication differences remain explicit. The M2 UI is specified, not implemented in this commit.


## v0.3 review/apply/recovery — October 13, 2026

All 52 repository tests passed: the previous 27 plus 25 reusable review/recovery tests. These cover read-only review, separate explicit consent, exact digest, source/result drift, protected tests, unsupported files, unsafe paths, modes, integrity, one-worker serialization, idempotency, partial failures, journal failure, conflicting external edits, interrupted-operation recovery and HTTP origin protection. Existing Seed Box regressions remain passing.

All 46 application/adapter/review tests passed inside actual native Codex command/exec in a disposable snapshot. The empty disposable profile refused thread/start and turn/start: no inference or account credentials were used. SQLite access and denied outside reads, baseline-test writes and worker network checks passed. No sandbox grant was broadened to fix the review path checks.

An explicitly labeled authored browser fixture on a separate local port ran project tests, captured a heading change, displayed Ready for review and an exact diff, required an unchecked owner consent box, applied the change, displayed Applied and served the changed heading after reload. Separate recovery consent restored the original heading and displayed Previous version restored. Task text containing an HTML image/event-handler payload appeared literally with zero image nodes. This proves the browser/application path for authored fixture results, not a new authenticated model task or general acceptance of arbitrary requests.

The fixture server was stopped and its temporary source/database/profile removed. One-off verification scripts and generated caches were removed; reusable regression tests remain. Original/result backups in real owner storage have not been deleted. The running owner v0.2 app, its data, sign-in profile and task history were not modified by these checks.

Remaining limits include unsupported additions/deletions/binary changes, no global multi-file atomicity, residual external-writer path/content races, single-process use and unverified other OS/runtime versions. Native approval resumption, hard spend/resource caps and independent acceptance checks remain pending.
