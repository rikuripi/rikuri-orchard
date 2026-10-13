# Controlled comparison pack

Two reusable synthetic projects and independent acceptance gates. No provider adapter, model call, credential, benchmark result or install is included. fixtures deliberately contain a weak passing baseline to test whether result verification catches missed requirements.

| Case | Exact task | Editable files | Independent acceptance |
|---|---|---|---|
| heading | Replace only the h1 text “Small steps, verified results.” with “Good work takes extraordinary teamwork!” | index.html | acceptance/heading.py requires the exact approved result, rejecting unchanged/unrelated edits and symlinks |
| mean | Correct arithmetic mean so fractional and negative-fractional results are preserved. Keep empty-input ValueError and original tests unchanged. | mean.py; optionally new tests | acceptance/mean.py checks fractional, negative, single-value and empty-input behavior separately from the passing original suite |

## Run authorization contract

One case/backend per explicitly approved attempt. Start with 180 seconds wall time, one worker, zero Orchard retries and a 1 MiB captured-output budget. Native Codex turns and Claude agentic turns have different semantics; record both and do not label them equivalent. Provider cost caps must state whether they are estimates or hard account limits. No unlimited run is authorized by this document.

Approve the exact nonsecret synthetic files, task, provider/account, limits and any known cost uncertainty before transmission. No Rikuri files, credentials, owner databases or task history enter these cases. Keep worker network disabled; explicitly list provider inference endpoints separately. No fallback model, external install, remote write, subagent, PR, branch, deployment or extra task is part of a case.

Copy one case into an owned disposable directory. Record its hashes and protect original tests plus the acceptance code from worker edits. Supply the acceptance file as read-only to the verifier. Verify the exact diff and original-file integrity, then run baseline tests and independent behavioral acceptance inside the approved native/OS sandbox. The mean acceptance script imports candidate Python and therefore MUST NOT run unreviewed model output on the host. The project-level fixture tests execute only authored synthetic code.

No ready-made command here launches a model. Orchard's existing adapter snapshots its own fixed project manifest; it cannot be claimed to run this pack without a separately scoped integration. Do not run ordinary headless Claude in a project carrying inherited hooks/MCP settings.

## Evidence record per approved run

Case/backend version; model; authentication route (no tokens); approved input hashes and paths; sandbox preflight; effective tools/configuration; turn semantics; terminal status; exact diff; baseline results; independent acceptance results; elapsed time; reported usage/estimated cost; unknowns; manual interventions; cleanup result. Model summaries alone are not acceptance evidence.

Review/preserve the minimal result receipt in the approved evidence location. Dispose of the owned fixture workspace and one-off logs after review if not needed for a failure reproduction. Keep these authored cases and acceptance gates: they are the reusable measurement kit.

Current result: six offline fixture-validation tests pass as part of the project suite. No Codex-versus-Claude live benchmark has run, so speed, price and success-rate rankings remain unknown.
