# Observation status UI

## Task Contract
- Outcome: Show task execution reports separately from unverified acceptance and application.
- Scope: Routine UI integration in index.html, reusable tests/observation_ui.cjs and docs/OBSERVATION_EXPORT.md plus README reference. Preserve task approval/review/apply/recovery logic; no backend, shared schema or snapshot manifest changes.
- Done when: On-demand GET populates three status fields; unsupported/mismatched responses fail visibly without retaining previous claims; legacy headline is explicitly reported; real-browser synthetic cases cover successful and failed loading, refresh, no accidental writes, hostile content and responsive layout; existing60application regressions pass in approved Ubuntu fixture layer; diff/links pass.
- Authority: Owner Next approved UI. Fresh disposable browser profile, request interception for synthetic fixture responses, no actual service/storage/credentials/model. Existing approved Ubuntu inspected-fixture launcher for Python regressions. No commit/push/PR/deploy. Orchard rules do not require a coding subagent/reviewer for this UI-only change; no subagent launched.
- Limits: One task, at most two repair/review cycles. No install or paid work; stop after verification.

## Baseline and plan
Current application/source bytes match the prior60test passing Ubuntu snapshot exactly (verified hashes before edits). Existing UI combines reported execution and application in a headline. Change it to an explicit legacy report; add a read-only status details panel loaded by user action, preserving separate consequence/approval controls. Client display guards check only the consumed identity/version/status and unverified invariants; authoritative full schema/digest validation stays server-side. Error messages contain no server payload. Clear stale details before refresh.

Browser verification uses bundled Playwright1.62.1 Apache2 tooling and installed Chrome in a new temporary profile; all page requests intercepted and fulfilled from authored fixtures or aborted. This is not an OS network containment claim. No package installation. Ubuntu launcher remains unchanged. Full Rikuri gate and native-worker requalification remain unproven.

## Completion — DONE for UI scope
- Browser regression script passed in fresh Chrome with intercepted synthetic responses: success/on-demand GET, failed refresh clears old claims, wrong identity/false acceptance/version/hostile content/malformed response refused, running/no application report, mobile stacking/no overflow, no POST/page errors/unknown destinations.
- Desktop/mobile screenshots visually inspected. Tests execute actual page JavaScript/DOM, with HTTP responses authored in the harness, not a real Orchard server.
- Ubuntu60existing application/export regressions passed, no skips, exit0.25file snapshot; unchanged approved launcher/admissions/global controls; owned copy and staging removed.
- Local documentation links/anchors and git diff --check passed. Zero repair cycles. Optional test tooling only; no installed dependencies.
- No independent coding agent/review required or used for this Orchard-only task. No backend/shared-contract/FILES changes.
- Evidence: /Users/hchome/Documents/Codex/2026-10-14/i-have-two-new-documentation-in/outputs/observation-ui/verification.md, browser-tests.txt, ubuntu-tests.txt, manifest.json, desktop.png and mobile.png.
- Full Rikuri gate, native runtime qualification and browser-to-real-HTTP/SQLite integration remain unproven. No production data, credentials, real worker, commit/push/PR/deploy.
- Next recommended task, not started: verify complete browser-to-HTTP-to-SQLite observation flow with disposable task fixtures.
