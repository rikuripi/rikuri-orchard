# Rikuri Pi integration — accepted direction, merge pending

The owner accepted Orchard as Rikuri Pi's software-project domain experience on October 14, 2026; normal merge remains pending. Rikuri owns production ProjectState, canonical transactions/ledger, policy/secrets/approvals/budgets, scheduling, knowledge, quality and shared developer/workspace services. Orchard specializes software artifacts, views and quality criteria. Its current local SQLite store and Codex worker are prototype infrastructure, not a second production authority.

## Maintained sources

For the owner's adjacent checkouts: [Pi ADR 0006](../../Rikuri-PI/docs/architecture/adr/0006-proposed-orchard-software-domain.md), [annotated integration plan](../../Rikuri-PI/doc/Rikuri_Pi_Orchard_Integration_Plan_2026-10-14.md), [documentation index](../../Rikuri-PI/doc/README.md), and [integration Build Record](../../Rikuri-PI/docs/build-records/2026-10-14-orchard-documentation-integration.md). These cross-repository links require the sibling Rikuri-PI checkout. Pi's live Stage Plan v2.1, Engineering Standard v1.2 and current Master Build Sequence control.

## Contract alignment before convergence

Design a provider-neutral task contract around stable project/intent/task/run/workspace/artifact/evidence identities, source revision, authorized scope, execution profile, budgets, acceptance evidence, mandatory independent gates and bounded stop conditions. DONE requires task-specific evidence; generic tests and worker statements alone are insufficient. Execution, acceptance and application remain separate outcomes. Failure or missing evidence cannot be decorated into completion by a UI.

This is accepted architectural direction with implementation still pending, not a claim that these contracts or arbitrary acceptance verification exist in v0.3. The current README, review/apply contract and verification record describe implemented behavior and limits. Start compatibility design before further adapters; retire/migrate prototype infrastructure only after applicable Rikuri services pass their gates, using a tested importer with provenance and rollback. Do not copy prototype rows directly into canonical storage.

Keep Monaco/LSP/DAP/Git/test services shared. Separate enforced policy, repository facts, per-task authority and dated model/harness/runtime guidance. The creative-studio sequencing remains in force; this proposal does not move the full IDE back to Stage 1 or expand Foundation-0. ADR owner acceptance is recorded; normal merge, schema implementation and execution experiments remain separate scoped work. This document launches none.

## Shared TaskContract draft

The single Rikuri-owned [TaskContract v1 draft](../../Rikuri-PI/docs/architecture/contracts/task-contract-v1/README.md) provides request/result schemas and synthetic success/failure/denial traces. Orchard references this definition rather than copying it. It is not wired into the existing Codex worker, review/apply database or production Rikuri APIs. Current v0.3 receipts retain their original limited meaning; importing them as verified acceptance remains prohibited without independent evidence.

## Adapter boundary design

Use the Rikuri-owned [adapter interface/evidence-handoff draft](../../Rikuri-PI/docs/architecture/contracts/task-contract-v1/ADAPTER_INTERFACE.md) for the next interface implementation proposal. It preserves native execution observations, independent acceptance and separate apply consent. The current CodexAdapter.run and Stage00 API do not yet implement this seam; no worker or migration is authorized by the document.

## November 6 amendment reconciliation

[Adaptive admission specification](ADAPTIVE_REFLECTION_ACCEPTANCE.md) records proposed Pi ADR 0020–0022 alignment and scope conflicts. Vault ownership, keys, canonical state and transaction promotion remain Rikuri responsibilities; Orchard uses scoped broker/context/execution interfaces. Model capability profiles, versioned skills and grounded experimentation compose shared services, never a second production database, router or policy authority. Existing TaskContract v1 and observation schema are untouched; new semantics need explicit versioned compatibility tests. Prototype data imports still require a validated, reversible migration and may not strengthen historical DONE receipts.

Minimal single-node seams precede any remote integration. Pi existing product Stage 3 owns Link, Stage 4 measured harness/scheduling, Stage 6 human/team governance, Stage 7 replication/resource integration and Stage 10 learned reflection. The source mesh Stage 2/3/4 order cannot replace those dependencies. Existing Foundation encrypted custody/restore, Option C and credential-free-worker scope remain. No implemented vault, mesh, strong VM isolation or adaptive improvement is claimed.

## November 6 owner acceptance of shared architectural direction

The owner accepted Pi ADRs 0020–0022 after independent review. Earlier proposed labels record the proposal origin; architectural adoption is complete, with normal merge pending. This accepts the documented Orchard alignment and stage mapping, without enabling a milestone, new adapter, migration or runtime behavior. Feature-specific acceptance remains Not yet proven; implementation requires separate scoped work and predecessor gates. [Acceptance record](build-records/2026-11-06-adr-0020-0022-owner-acceptance.md).
