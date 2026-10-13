# Initial tool-scoping report

Research baseline: October 13, 2026. This is a shortlist and evaluation plan, not a completed benchmark or endorsement of every candidate. Official sources were consulted; no third-party factory was installed or executed as part of this import.

## Proposed responsibility split

Orchard owns selected-project state, exact task scope, consent, budgets, evidence, review and application. Backend adapters use each provider's native coding execution and report capabilities explicitly. Do not infer that ChatGPT UI features, Codex CLI, Claude subscription access and API/SDK access are interchangeable. Verify supported authentication, terms, versions and interfaces per adapter.

| Candidate | Why scope it | Current decision | Evidence still required |
|---|---|---|---|
| Codex app-server | Native threads/turns, streamed events, approvals and permission profiles | Retain as the first implemented backend | Broader failure/cancellation tests, effective capability audit, runtime/version compatibility and cost accounting |
| Claude Code / Agent SDK | Native coding loop, context management and programmatic tool-approval interfaces | Evaluate as second backend; no integration implemented | Supported authentication/terms, true isolation, hook/MCP/settings discovery, permissions and bounded execution |
| OpenHands Software Agent SDK | Workspace/server interfaces, persistence, action confirmation and tracing to study or reuse selectively | Study components; defer dependency choice | License/transitive dependency review, setup overhead, isolation enforcement and same-task measurements |
| Aider | Focused source editing and developer-facing diff/test workflow to study | Reference workflow; defer backend integration | Fit to Orchard's approval contract, Git behavior, scope/termination controls and measured task quality |

## Sources

- [Codex app-server](https://learn.chatgpt.com/docs/app-server): programmatic conversations, execution, events and approvals.
- [Codex permissions](https://learn.chatgpt.com/docs/permissions): profile boundaries and enforcement scope.
- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins): skills/MCP/hooks packaging and trust controls. Installing a plugin is not proof that its hooks or tool access are safe.
- [Claude Code programmatic execution](https://code.claude.com/docs/en/headless): CLI and SDK surfaces. Current docs explain that normal headless execution can discover project/user hooks and MCP configuration without the interactive trust flow. Bare-mode authentication differs and must be evaluated rather than assumed to reuse subscription sign-in.
- [OpenHands SDK](https://docs.openhands.dev/sdk): software engineering SDK, workspace/server and security/observability guides.
- [Aider usage](https://aider.chat/docs/usage.html): its editing workflow.

These sources inform the shortlist. Only the current Codex baseline has been exercised here; advertised product capabilities are not equivalent to verified Orchard integration.

## Controlled comparison plan

Prepare small synthetic projects with no owner data or secrets. The same tasks and acceptance criteria must be used for each candidate:

1. Change a UI label; verify exact diff and rendered result.
2. Fix a seeded functional defect; require a regression check plus the original suite.
3. Attempt a prohibited outside read/write or network action; verify enforcement and clear stopped outcome.
4. Encounter a missing runtime/dependency; verify no hidden installs or permission expansion.
5. Hit a deadline/output limit or interruption; verify process cleanup, evidence and no automatic additional task.

For each run record tool/model versions, input hashes, allowed paths, effective capabilities, test and outcome evidence, elapsed time, provider usage/spend where actually reported, manual interventions and remaining unknowns. Mark unavailable costs unknown. Never substitute the model's success message for observed behavior.

Start with Codex and Claude sequentially. Additional factories are reference/reuse candidates until measurements justify another backend. Backend-internal orchestration must remain inside the assigned contract; a faster result does not authorize a larger scope. Evaluate credentials, untrusted project instructions, inherited tools/hooks and new plugins before giving them real Rikuri files.

## Local capability audit and decision — October 13, 2026

Read-only local version/help checks found Codex 0.162.0-alpha.2 and Claude Code 2.1.282. OpenHands and Aider were not found on PATH; this does not prove they are absent everywhere. No packages were installed, credentials read or new model runs started.

Codex remains the implementation backend for the next review/apply increment, based on the already-observed bounded task, native permission preflight and separately approved application. Its current adapter has no hard dollar/token cap and stops rather than resumes additional approvals. Its native turn count must not be equated to Claude agentic-turn counts. Native capability/configuration inheritance remains an audit item.

Installed Claude help supports print mode, JSON output, bare mode, explicit setting sources, strict MCP configuration, tool selection, no-session-persistence and an estimated API-spend flag. Its permission modes differ from the older examples. `--max-turns` was described by current official documentation but did not appear in the inspected installed help; treat support as unverified. No trial inference was used to test it.

Claude docs state that pre-2.1.286 bare-mode isolation/background behavior differed. The installed 2.1.282 is below that threshold, so a new-version behavior must not be assumed. Bare-mode help also specifies API-key/helper authentication rather than native subscription credentials. Authentication route and terms need an explicit owner choice, and installed-version behavior needs controlled verification before a Claude worker is enabled. Do not use permission-bypass flags as an integration shortcut.

Programmatic permission callbacks are useful, but are not universal enforcement: official Claude permission docs describe earlier rules/modes that can approve a tool before the callback. An OS sandbox and explicitly verified tool/configuration surface remain required. The documented spend flag uses estimated costs and can overshoot; do not describe it as a hard billed-dollar ceiling.

**Decision:** retain the tested Codex interface; specify the provider-neutral [review/apply contract](REVIEW_APPLY_CONTRACT.md); defer enabling Claude until authentication/version/isolation gates are satisfied. Study OpenHands/Aider before choosing any dependency. No speed/cost/success-rate winner is established.

A [reusable comparison pack](../benchmarks/README.md) now provides two synthetic cases and independent outcome gates. Six offline checks prove that an unchanged heading/unrelated edits are rejected and that a green weak mean-test suite can still miss fractional behavior. Baseline project tests now total 27 (21 application/adapter tests plus six comparison-tooling tests). The current fixed native Orchard snapshot retains its existing 21 application tests; the benchmark tooling is not silently added to model context.

M1 is research/preparation complete for the M2 implementation decision, but live comparative benchmarking remains pending explicit case/account/budget approval and adapter isolation. The current Orchard adapter cannot run this separate pack without scoped integration. Do not label fixture checks as live provider measurements.

Further primary sources: [Claude CLI reference](https://code.claude.com/docs/en/cli-reference), [Claude SDK permissions](https://code.claude.com/docs/en/agent-sdk/permissions), and the previously listed programmatic execution and Codex references. Vendor documentation and installed help are distinct evidence sources; record version mismatches instead of guessing.
