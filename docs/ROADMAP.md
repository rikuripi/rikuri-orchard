# Orchard roadmap

Goal: a dependable software-development workshop that can eventually help build/refine Rikuri PI and rikurinode. Keep Orchard separate until its control contracts are proven. Existing Rikuri project standards remain authoritative when either becomes a target.

Each milestone needs one scoped task, an owner-recognizable outcome, permitted paths/capabilities, mandatory checks, evidence and a stopping condition. Passing generic tests cannot replace inspection of the requested behavior. No backlog entry starts work automatically.

| Milestone | Deliverable | Acceptance gate | Deferred |
|---|---|---|---|
| M0 — Baseline | Clean repository of working v0.2, truthful verification and excluded owner data | Fresh checkout starts and passes 21 tests; source matches installed baseline; no private artifacts tracked; private remote confirmed | Further agent capabilities |
| M1 — Scope tools | Research plus controlled comparison using identical tasks | Record tested versions, authentication, permission/config inheritance, artifacts, stopping behavior, latency and cost visibility; make adopt/adapt/defer decisions | Installing every candidate |
| M2 — Review and apply | Diff preview, understandable test evidence, explicit Apply, backup and recovery in Orchard UI | Owner can distinguish ready-for-review from applied; approval is bound to exact source/result hashes; stale results are rejected; denied approval changes nothing; recovery restores approved files | Automatic merge or deployment |
| M3 — Execution reliability | Cancellation, approval handling, startup diagnostics, budgets and restart recovery | Failure-injection checks for timeout, interruptions, denied network, stale source and missing runtime; no silent retries; known provider cost/resource limitations visible | Parallel fleet |
| M4 — Selected capabilities | Claude adapter and a small explicit skills/plugin list | Each capability passes the same bounded-task contract, authentication isolation, permissions and evidence checks; no silently inherited unreviewed hooks/tools | Unrestricted marketplace installation |
| M5 — Rikuri pilots | Read-only project review followed by one small explicitly approved isolated change | Respect each project's AGENTS.md/standards; protect existing work; reproduce tests; inspect outcome; apply separately with approval | Autonomous broad rewrites |
| M6 — Broader deployment | Optional private remote operation after local reliability is proven | Authentication, access controls, secure transport, isolated execution, resource controls and tested backup/recovery | Public exposure by default |

## Current progress

M1: complete a concrete comparison plan and decide the minimum integration surface for M2. The actual comparison runs require bounded tasks, account/spend consent and isolated fixtures. The read-only installed-tool audit, reusable comparison fixtures and M2 contract are now prepared. Live comparative runs remain gated by explicit task/account/budget consent and isolation; no speed/cost ranking is proven. M2 is implemented for existing-file text changes using the tested Codex backend and [its acceptance contract](REVIEW_APPLY_CONTRACT.md). All 52 repository tests pass, including 46 application tests inside native Codex execution. Browser apply and recovery were verified with an explicitly labeled authored fixture. Installing v0.3 into the owner’s running copy and a fresh authenticated model task remain pending. M3 has not started.

## M2 acceptance details

- Store immutable input/result hashes and a human-readable patch preview.
- Separate execution outcome, acceptance evidence and application outcome.
- Allow an explicit owner approval for exactly the displayed diff.
- Check original state again immediately before application; reject drift rather than overwriting owner work.
- Apply only reviewed paths, avoid path traversal/symlinks, preserve data and credentials, and handle partial failures safely.
- Record a backup/recovery receipt and prove a recovery test.
- Do not start new tasks, branches, PRs, model turns or deployment as a side effect of applying a result.

No calendar deadline is promised. Progress is measured by completed acceptance gates.
