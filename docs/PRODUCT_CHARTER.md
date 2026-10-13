# Rikuri Orchard — Product Charter (Draft 0.1)

## Mission

Make creation of dependable software accessible to people who describe *what they want*, without requiring them to understand the technical implementation, while retaining verifiable engineering evidence for experienced reviewers.

**Product promise:** An idea grows into a demonstrably useful result through bounded, observable, reversible work. Trust follows evidence, not an agent's confidence.

**Personality:** Premium, calm, warmly illustrated, slightly whimsical. 90% professional clarity, 10% subtle orchard imagery. Never childish language or animations masking risk. Reduced-motion and dense technical modes belong in the full product.

## Orchard language (presentation only)

| User-facing | Real engineering meaning |
|---|---|
| Seed Box | Idea and request intake, including eventual GitHub Issues |
| Field Map | Project graph, dependency map and progress |
| Orchard Crew | Role-based agents (coordinator, builder, reviewer, security) |
| Greenhouse | Isolated, disposable experiments; externally sourced code treated as untrusted |
| Orchard Gate | Clearly explained consequential human approval requests |
| Weather Report | Runtime application/infrastructure/agent observability |
| Tool Shed | Approved adapters, environments, skills and integrations |
| Harvest Board | Verified deliverables and their evidence |
| Gardener's Journal | Provenance-backed lessons, failure patterns and experiments |

The underlying project lifecycle remains **Frame → Shape → Plan → Execute → Verify → Deliver → Learn**, specialized to software when appropriate. `DONE`, `BLOCKED`, `NEEDS_OWNER_DECISION`, and `UNVERIFIED` are real status terms; orchard metaphors must not replace them.

## Audience and trust

- Novice: outcome in one sentence, concise decisions, truthful progress and an observable demo.
- Professional: technical context on demand, tests, traces, diffs, exact scopes and reproducible evidence.
- Both views derive from the same canonical records.

## Nonnegotiable properties

1. Explicit bounded delegation and finite stopping rules.
2. Security permissions are checked by enforcement outside the reasoning agent; no self-granted authority.
3. No silent failures, false-green status or scaffold-as-evidence claims.
4. Provenance-aware and reversible improvement of agents/workflows.
5. Model/harness/runtime interchange via adapters; do not trap core project state in provider files.
6. Conservative handling of third-party instructions, dependencies and skills.
7. Preserve real Rikuri state under Rikuri-controlled APIs and transactional update rules.

## Product boundary

Orchard is a software-project profile of Rikuri's broader project-lifecycle design. It can begin as a standalone companion and be integrated after its control-plane contracts are proven. It does not replace the authoritative Rikuri PRD, architecture, Stage 00 plan or Engineering Standard.

## First release to demonstrate

Someone enters an idea into the Seed Box; it survives restart; the interface reflects its true status; the system never claims it has built, reviewed or secured software when it has not. Then add *one real, bounded coding task* using a provider adapter and verifiable outcome record. Only then add parallel work.
