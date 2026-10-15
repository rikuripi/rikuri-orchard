# Orchard read-only observation export

## Task Contract
- Outcome: Export a single Orchard task as a schema-v1 unverified legacy observation through the application.
- Scope: Routine read-only integration: Orchard observations.py, GET route in app.py, explicit crew FILES dependencies, contracts/task_contract_v1 distribution, tests/test_observations.py, README and docs/OBSERVATION_EXPORT.md. Rikuri bridge package-safe import and this build record. No execution/apply/recovery behavior or production data operations.
- Done when: Actual handler returns validated single-task metadata; consent/text/evidence/receipt omitted; disabled/missing/unknown/error/foreign-origin cases refuse safely; SQLite connection refuses writes; shared source distribution hashes match; all60 Orchard regressions pass inside approved Ubuntu fixture layer, independent review and diff/link checks.
- Authority: Owner Next approved this read-only export and disposable application regressions. Reuse approved inspected-fixture namespace layer. One required verifier for shared Rikuri change; no live storage, native server/model, credentials, commit/push/PR or full project gate.
- Limits: One task, two repair/review cycles maximum. Two harness corrections consumed during baseline; no further repair cycles available this task.

## Baseline and plan
Baseline52 Orchard tests passed in Ubuntu before repository edits (exit0, no skips). First harness attempt exited1 before tests because unchanged launcher requires contract/tests; added inert root marker. Second reached52 tests with3 PermissionErrors: immutable444 modes copied into benchmark workspaces. Harness now copies inspected source into owned temporary directory and sets owned copy files644/directories755 after safety admissions, leaving immutable staged source protected. Tests/launcher unchanged. Third baseline run52passed. Global controls unchanged; staging removed each time.

GET /api/tasks/<uuid>/observation selects only task id/status and joined review status with one statement through SQLite URI mode=ro and query_only. No Crew.list, review constructor, receipt decode or worker invocation. Fixed shape/digest validation through exact shared source distribution; application status remains an unverified claim. Distribution is packaging, not a second contract authority. Include its dependencies in native disposable source list, but native runtime qualification remains unproven.

## Completion — DONE for approved integration
- Ubuntu baseline52existing tests passed before edits; final60application regressions passed, no skips, exit0 (eight new export cases). Actual handler entry point and snapshot cold import exercised; no HTTP listener or native model runtime launched.
- Host14standalone bridge tests passed after package-safe import. Three shared source files match exact distribution/manifest hashes. Local documentation links and both repository diff --check pass.
- Independent source review PASS, no Important/nits across bugs/security/compliance. Reviewer checked actual schema/query, distribution and test evidence; did not independently execute tests. Reviewer initially ran Git inspection from projectless cwd (not a git repository), corrected repo checks passed.
- Final24file allowlist, immutable stage and unchanged namespace launcher passed admission; test-owned writable copy removed, global controls unchanged, guest staging removed.
- Two harness corrections recorded above; no further repair cycles used. No production credentials/data, canonical mutation, real worker, commit/push/PR or deployment.
- Full Rikuri Ubuntu gate, guard suite and native worker requalification remain unproven. No stage/merge claim.
- Evidence: /Users/hchome/Documents/Codex/2026-10-14/i-have-two-new-documentation-in/outputs/orchard-export/verification.md, test-output.txt, baseline-pass.txt, two failure logs and manifest.json.
- Next recommended task, not started: show read-only observations in Orchard UI, with separate reported execution, unverified acceptance and application.
