# Full-stack read-only observation verification

## Task Contract
- Outcome: Prove the browser status panel reaches the real HTTP handler and disposable SQLite storage without granting authority or changing stored state.
- Scope: Routine test-only integration: tests/observation_http_fixture.py, tests/observation_e2e.cjs, docs/OBSERVATION_EXPORT.md and this record. No application/shared-schema/worker behavior changes.
- Done when: Real browser success plus unsupported-status refresh failure and recovery; real HTTP headers/missing/foreign-origin refusals and digest correct; per-phase SQLite bytes unchanged by reads; no POST or worker start; browser/server stopped and temp files removed; existing60Ubuntu regressions and prior synthetic UI regressions remain green; diff/links pass.
- Authority: Owner Next approved full browser→HTTP→SQLite disposable flow. Fresh browser profile and temporary127.0.0.1 port/server/database. No live storage, credentials, native runtime/model or external destination. Fixture controls only stdin. Existing approved Ubuntu layer for application regressions. No coding agent/reviewer required by Orchard-only test scope. No install/commit/push/PR/deploy.
- Limits: One task, at most two repair/review cycles; time-bounded requests/child process cleanup; no paid work or follow-on task.

## Baseline and plan
Verified exact source bytes against previous passing60-test Ubuntu snapshot before edits. Reuse real Handler.do_GET, Crew.list and actual schema initializers with synthetic task/review rows. Fixture subclass rejects POST and worker starts, leaving GET path real; test-only controls deliberately change fixture status between read phases. Database hashes must match expected bytes before each mutation and after each browser/HTTP phase. This proves read effects for this rollback-journal fixture, not universal WAL-sidecar behavior, OS containment, production authentication or native-runtime admission.

## Red run / repair1
First integration exited1 at Host refusal assertion (200 !==403). Foreign Origin403 already passed. Node fetch normalizes/ignores the supplied Host in this environment; replace this one transport with node:http explicit-header request, retaining expected403. No application code, expected status, test baseline or security control changed. Failed output retained in outputs/observation-e2e/header-transport-failure.txt. Fixture cleanup ran through EOF/finally on failure.

## Completion — DONE for approved full-stack verification
- Real browser→actual HTTP Handler→disposable SQLite flow passed, including schema-bound metadata digest, payload omission, JSON/no-store/nosniff headers, actual Host/Origin403 and missing404.
- Unsupported fixture status produced409 and cleared stale browser claims; stdin restore recovered the panel. Per-phase database bytes unchanged by reads; no POST/worker start.
- Browser/server stopped and owned SQLite/source/run directories removed; cleanup assertions passed. Screenshot inspected.
- Existing synthetic UI regressions passed; Ubuntu60application/export tests passed, no skips, exit0, exact27file snapshot. Unchanged launcher/admissions/global protections; guest copy/staging removed.
- One transport repair used, recorded above; no application/schema/worker changes this task.
- Documentation links and git diff --check passed. No subagent review required/performed in this Orchard-only scope.
- Evidence: /Users/hchome/Documents/Codex/2026-10-14/i-have-two-new-documentation-in/outputs/observation-e2e/verification.md and linked logs/manifest/screenshot.
- Full Rikuri Ubuntu build gate/native-runtime requalification remain unproven. Changes uncommitted, no push/PR/deployment.
- Next recommended task, not started: qualify the complete integration against the full Rikuri Ubuntu build gate in an isolated checkout.
