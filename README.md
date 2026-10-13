# Rikuri Orchard

A local-first development workshop for Rikuri PI and rikurinode. Orchard keeps tasks bounded, records evidence, and leaves consequential changes under owner control. It currently runs one Codex worker in a disposable copy of the Orchard project.

This repository captures the working v0.2 baseline, including the Homebrew SQLite sandbox correction and the owner-approved heading change. It does not contain owner ideas, task history, credentials or disposable workspaces.

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

## What this baseline does

- Preserves the local Seed Box and validated manual idea states.
- Runs one task, one worker, one model turn, zero Orchard repair/retry rounds.
- Copies a fixed source/test manifest into a disposable workspace; no source database or credentials are included.
- Uses native Codex permissions with worker network disabled and human approvals. Further server requests stop the run without being approved.
- Runs project unittest discovery under native command/exec after model completion. Failed or zero tests, changed existing tests and missing explanations block success.
- Stores evidence, input hashes and results locally. Completed changes remain in the disposable workspace for review.

**DONE means a completed model turn and passing project-test gates in that copy. It does not mean applied to your working project, and it does not automatically prove arbitrary acceptance conditions.** The owner-approved heading change was inspected and applied separately. An in-app review/apply workflow is the next product milestone.

## Bounds and limitations

One model turn; no automatic Orchard retry; native execution deadline 180 seconds; tests at most 60 seconds inside that deadline; protocol output budget 1 MiB; source snapshot budget 2 MiB. Provider-internal retries and activity may occur within the wall-clock bound. Startup/shutdown adds limited overhead.

Hard token/dollar, memory and workspace disk-growth caps are not implemented. Neither approval resumption nor automated acceptance-condition checks are implemented. Known-pattern secret detection is precautionary and incomplete; inspect files before authorizing transmission. The native host server remains trusted, and machine-managed tool/configuration inheritance needs a fuller capability audit. This is a single-process localhost prototype; no VPS/public-hosting security release is claimed.

## Development plan

Read [the roadmap](docs/ROADMAP.md), [initial tool-scoping report](docs/TOOL_SCOPING.md), [verification record](VERIFICATION.md) and [project charter](docs/PRODUCT_CHARTER.md).

Older starter docs are retained as design history. ROADMAP.md and the current executable limits govern this baseline; planned capabilities in older files must not be presented as implemented.

No license has been chosen by the owner yet. Do not assume redistribution rights; check third-party licenses before incorporating their code. Private repository visibility is intended, but must be confirmed on GitHub.
