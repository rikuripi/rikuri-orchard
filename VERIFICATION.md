# Verification record

## Working baseline — October 13, 2026

The first real Codex task changed the Orchard Crew heading from “Good work takes good company.” to “Good work takes extraordinary teamwork!”.

The initial authenticated turn completed, but native project-test imports failed because Homebrew SQLite's separate dynamic library was denied by the sandbox. The adapter was corrected with narrow runtime read grants, canonical Python/SQLite loading, and a preflight SQLite query before inference. After correction, all 21 tests passed inside native Codex command/exec. These checks used an empty disposable profile and refused model threads/turns.

The owner then explicitly submitted and approved a fresh heading task. The running Orchard displayed DONE with all 21 tests passing under the native sandbox. Inspection confirmed exactly one heading replacement, unchanged baseline tests, and an unchanged original source hash. After separate explicit owner permission, that index.html change was applied and visually verified on the running browser page.

This proves one real bounded task plus separately approved application. It does not prove a general software factory, a portable backend across OS versions, or automated satisfaction of arbitrary task descriptions.

The 21 repository tests include four original Seed Box tests plus checks for request/origin/consent validation; one worker; persistence/restart behavior; no automatic retry; safe snapshots and symlinks; recognizable secrets; protocol completion/failure; denied approvals; nonzero and zero tests; output/time bounds; subprocess cleanup; changed-test rejection; a clearly labeled simulated end-to-end run; SQLite runtime grant scope; and SQLite failure before model startup.

Protocol fixtures simulate model events and test output. They are not evidence of additional live model runs. Ordinary unittest execution is not evidence that the OS sandbox works; that is established by the separate native checks above.

## Repository baseline checks

The repository import will be checked using a fresh local clone, including the complete test suite, localhost HTTP startup and private-path exclusions. Its results are recorded separately after those checks run.

## Pending

In-app review/approval/apply and recovery; resumable native approvals; independent acceptance checks; robust cancellation and process/resource management; hard spend/resource limits; effective capability audits (including machine-managed configuration); more representative native tasks; other OS/runtime versions; Claude integration; third-party factory comparisons by experiment; Rikuri PI/rikurinode pilots; remote hosting.
