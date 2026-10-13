# Orchard — Thin-slice roadmap and completion gates

This roadmap applies to **Orchard**, not Rikuri Foundation-0 Stage 00. Never reinterpret a calendar target as permission to skip a gate. Do not run new stages automatically.

## O0 — First Seed (provided local prototype)

**Scope:** Browser Seed Box + SQLite persistence + manual status updates. No AI execution. No third-party dependencies or external services.

**Accept when:** A seed can be added; restart preserves it; illegal state jumps are rejected; all local tests pass; the UI does not claim autonomous progress. This starter includes those basic tests but still requires the owner to run it on their machine before claiming their environment is verified.

## O1 — First real growth cycle (next approved task)

One orchestrator; one coding worker; optional independent reviewer; no parallel jobs. A plain-language task gets explicit acceptance tests and cost/time budget. Worker executes in an approved, controlled workspace, returns diff, test results and a durable receipt. Provider adapter is either Claude **or** Codex initially. A reviewer must not be the only source of evidence. Failed checks create a BLOCKED state; repair is bounded, not indefinite.

**Required proof:** One genuine user-requested change proceeds from seed → work order → execution → targeted tests → independent gate → verified outcome without surprise worktrees/PRs or further work after DONE. Demonstrate a required test failing and becoming BLOCKED; prove that no false completion is claimed.

## O2 — Owner controls and safe workspaces

Plain-English approvals, real out-of-process capability enforcement, disposable workspaces, limited network, audit receipts, refusal tests, cost caps, crash recovery and idempotent retries. A sandbox's real restriction must be tested; prompts alone never count as enforcement.

## O3 — Multiple workers and Git integration

Conditional dependency scheduling, worktrees only when justified, concurrency quotas, GitHub Issues intake and PR delivery according to repo policy, merge conflict handling, bounded reviewers, job leases and durable restart.

## O4 — Observation and measured improvement

Error/performance/CPU/memory telemetry, independent task scoring, model and harness benchmarks, candidate workflow experiments, promotion gates, rollback, Gardener's Journal with provenance and conflict/staleness checks. Never automatically weaken security because a metric improved.

## O5 — Integration with Rikuri Pi

Bring the verified Orchard control plane behind Rikuri's established state, policy and knowledge service interfaces. No direct writes to Rikuri canonical databases by model/worker processes; no replacement of Foundation-0 protected gates.

## Hard exclusions until the applicable stage

No unattended plugin/skill installation, no arbitrary execution of downloaded repository instructions, no deployment, no production credentials, no autonomous recursive team creation, no unlimited review/repair loops, no global permission grants, no self-modifying protected policies.
