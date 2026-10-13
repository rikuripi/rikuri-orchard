# Orchard — Copy/paste kickoff for Claude Code or Codex

Work in the **new standalone Rikuri Orchard folder** containing this starter kit, not the active Rikuri Pi checkout. Read `AGENTS.md`, `README.md`, `docs/PRODUCT_CHARTER.md`, `docs/ROADMAP_AND_GATES.md`, and `docs/ORCHESTRATION_POLICY.md`.

Your first assignment is to inspect and characterize what actually exists. Run its existing tests and launch the local Seed Box in a safe test directory. Report specific verified behavior and limitations. Do **not** claim an agent factory exists: the supplied app only stores seeds and manually changes status.

Then propose one narrowly scoped implementation for **O1: a genuine bounded task cycle**. Before any edits, write a one-page plan with: intended user-visible outcome, constraints, proposed smallest adapter (Claude or Codex), real execution isolation method, required approval boundaries, relevant test cases, exact stop conditions, and a rollback plan. Keep it provider-portable at the core; provider CLI syntax belongs in adapters.

For this assignment:
- No extra agents, worktrees, branches, PRs, external skills, package installers, plugin connections, or remote actions without explicit authorization.
- One approved coherent task only. No automatic follow-up tasks or scope expansion.
- One targeted repair round and at most one re-review; on unresolved mandatory failure return BLOCKED with evidence.
- Never bypass a failing required gate or silently loosen permissions.
- Report outcomes with `DONE`, `BLOCKED`, `NEEDS_OWNER_DECISION`, or `UNVERIFIED` and the exact tests performed.
- Preserve the existing Rikuri Pi work and documentation unchanged.

Present the O1 plan and stop for owner review. Do not start implementation of O1 within this initial assignment.
