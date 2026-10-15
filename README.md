# Rikuri Orchard

A local-first development workshop for Rikuri PI and rikurinode. Orchard keeps tasks bounded, records evidence, and leaves consequential changes under owner control. It currently runs one Codex worker in a disposable copy of the Orchard project.

This repository captures the v0.3 review/apply implementation, including the Homebrew SQLite sandbox correction and the owner-approved heading change. It does not contain owner ideas, task history, credentials or disposable workspaces.

## Run locally

Python 3.10+; no third-party Python packages are required.

```sh
python3 -m unittest discover -s tests -v
python3 app.py
```

Open http://127.0.0.1:8765. This starts the Seed Box. Native Codex execution is disabled unless explicitly configured. Run these commands from this repository's folder.

## Enable the single Codex worker

Use an official native Codex executable. Named permission profiles and experimental app-server fields must be supported. The baseline was verified against Codex 0.162.0-alpha.2 on the owner's macOS machine. Other native runtimes are not yet verified.

Create an empty dedicated Codex profile and sign in yourself. Never copy account credentials from another profile or enter them into an Orchard task. For a NEW profile:

```sh
mkdir .orchard-codex
CODEX_HOME="$PWD/.orchard-codex" codex login
python3 app.py --codex "$(command -v codex)" --codex-home "$PWD/.orchard-codex"
```

An existing dedicated profile can be supplied using its absolute path. A profile containing config.toml is rejected. On this Mac the bundled executable was `/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`.

Submitting a task only records it. Review the selected files and limits, then explicitly approve that run. The native preflight checks Python and SQLite, and confirms denied outside reads, existing-test edits and worker network access before inference. Homebrew SQLite is readable only through its runtime-library grants; the trusted Python loader runs inside the sandbox using canonical runtime paths.

## What Orchard does

- Preserves the local Seed Box and validated manual idea states.
- Runs one task, one worker, one model turn, zero Orchard repair/retry rounds.
- Copies a fixed source/test manifest into a disposable workspace; no source database or credentials are included.
- Uses native Codex permissions with worker network disabled and human approvals. Further server requests stop the run without being approved.
- Runs project unittest discovery under native command/exec after model completion. Failed or zero tests, changed existing tests and missing explanations block success.
- Stores evidence, input hashes and results locally. Completed changes remain in the disposable workspace for review.

**DONE means a completed model turn and passing project-test gates in that copy. It does not mean applied to your working project, and it does not automatically prove arbitrary acceptance conditions.** The owner-approved heading change was inspected and applied separately. New supported results now have an in-app review/apply workflow.

## Review, apply and recover

After a successful new task, Crew shows **Ready for review**. Open **Review changes** to inspect the exact files, before/after text, full diff and test evidence. Check the separate owner permission box, then choose **Apply reviewed changes**. Run permission alone never authorizes application. Reload for interface changes; restart Orchard after Python source changes.

Applied results offer **Review recovery** and a separate permission box to restore the saved previous version. Original/result bytes, modes, hashes and receipts are retained in the local SQLite database. Back up that database alongside your project; recovery is not a substitute for external backups. Historical tasks without captured reviews require a fresh task.

Only text modifications to existing files in the fixed source manifest are supported. New files, deletions, binary results, protected-test edits and unsafe paths require an owner decision. Drifted source/results and stale review IDs are rejected. Startup marks interrupted operations for explicit recovery; it does not resume writes automatically.

## Bounds and limitations

One model turn; no automatic Orchard retry; native execution deadline 180 seconds; tests at most 60 seconds inside that deadline; protocol output budget 1 MiB; source snapshot budget 2 MiB. Provider-internal retries and activity may occur within the wall-clock bound. Startup/shutdown adds limited overhead.

Hard token/dollar, memory and workspace disk-growth caps are not implemented. Neither approval resumption nor automated acceptance-condition checks are implemented. Known-pattern secret detection is precautionary and incomplete; inspect files before authorizing transmission. The native host server remains trusted, and machine-managed tool/configuration inheritance needs a fuller capability audit. Application uses staged file replacements and durable receipts, with rollback for ordinary failures. It is not a globally atomic multi-file transaction. External writers can race path/content checks; ancestor symlink checks and inode rechecks narrow but do not eliminate that race. Use one Orchard process and avoid concurrent external edits during application/recovery. This is a single-process localhost prototype; no VPS/public-hosting security release is claimed.

## Development plan

Read [the roadmap](docs/ROADMAP.md), [tool-scoping report](docs/TOOL_SCOPING.md), [review/apply contract](docs/REVIEW_APPLY_CONTRACT.md) and [comparison pack](benchmarks/README.md), [verification record](VERIFICATION.md) and [project charter](docs/PRODUCT_CHARTER.md).

Older starter docs are retained as design history. ROADMAP.md and the current executable limits govern this baseline; planned capabilities in older files must not be presented as implemented.

No license has been chosen by the owner yet. Do not assume redistribution rights; check third-party licenses before incorporating their code. Private repository visibility is intended, but must be confirmed on GitHub.

## Repository hygiene

Git tracks source, reusable regression tests and project documentation. macOS/Linux metadata, editor recovery files, private profiles/data, Python/frontend caches, build output and temporary work are ignored. Keep one-off diagnostics in work/ or scratch/ and remove them after use when there is no repeat purpose. Automated tests use disposable temporary directories and stop their child processes.

Keep tests/ regression checks: they are reusable safety evidence, not disposable junk. Do not use blanket cleanup commands on owner data. Existing product runs and backups remain local and retained for review/recovery until an explicit retention policy is implemented; .gitignore does not delete them.

## Rikuri integration direction

Read the [integration reconciliation](docs/RIKURI_INTEGRATION.md) before designing additional adapters. The owner-accepted October 14 ADR direction places Orchard over shared Rikuri services, with early contract alignment and later validated migration. Normal merge and implementation admission remain pending; the current v0.3 behavior and limitations above remain the executable baseline.

The [read-only observation export](docs/OBSERVATION_EXPORT.md) exposes one task as shared-schema metadata with acceptance and application explicitly unverified.

Task cards offer [status details](docs/OBSERVATION_EXPORT.md#task-card-status-details) with execution reports, unverified acceptance and unverified application shown separately.
