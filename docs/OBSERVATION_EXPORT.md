# Read-only observation export

GET /api/tasks/<task-uuid>/observation returns one {observation: ...} object using the shared Orchard legacy snapshot observation v1 contract. The worker must already be configured for its task storage to be available; this endpoint never starts it. A disabled store returns409; missing task404; unsupported metadata or database failure409; invalid host or foreign Origin403. Local CLI requests without Origin follow the existing policy. Responses inherit no-store headers.

Only task identity, status and joined review status are selected in one SQLite statement through mode=ro plus query_only. No request/evidence/receipt is selected or decoded. These connection settings prevent SQL writes/creation; SQLite may manage read-related WAL sidecars. This is not a promise of zero filesystem activity, database-file sandboxing or authentication against other local processes.

DONE/APPLIED remain reported claims. Execution, acceptance and application stay unverified, authority none and runtime compatibility false. No Rikuri canonical import or state promotion occurs.

The three files in contracts/task_contract_v1 are exact distributions of Rikuri-PI's task-contract-v1 shared source, with local SHA256 manifest. Update source there, inspect it and resynchronize together; do not fork the contract here. Manifest hashes detect distribution drift in tests; they are not runtime authentication. Existing small custom checker strict integer ingress semantics are retained. All dependencies are in the worker snapshot FILES list; changing that snapshot is not evidence that the native runtime has been requalified.

Verification uses authored fixtures in disposable SQLite databases. Existing task/review/apply behavior is covered by application regressions. No credentials, model calls or live database are part of verification.

[Integration direction](RIKURI_INTEGRATION.md)

## Task-card status details

Orchard Crew labels the existing headline as a reported task status. Each card has an on-demand Load status details button and three distinct fields: Execution report, Acceptance, and Application. Acceptance stays Unverified; application reports are shown alongside Unverified. Completion never becomes verified acceptance.

Loading or refreshing performs only GET for that task. Refresh clears previous claims first; unavailable, mismatched or unsupported responses leave a visible generic message and unverified values. Other task permission/review/apply controls retain their existing separate behavior. The client checks displayed identity/version/status and unverified invariants; it does not replace the server's full schema/digest validation.

Optional UI regression command: node tests/observation_ui.cjs. Supply an installed Playwright module via normal Node resolution (or NODE_PATH), and ORCHARD_TEST_BROWSER for an installed compatible Chrome executable. No browser download is performed. The script uses a fresh profile and intercepts every page request with synthetic fixtures; it never connects to a running Orchard or its data. ORCHARD_UI_OUTPUT optionally saves desktop/mobile screenshots.

## Full browser / HTTP / SQLite regression

Optional command: node tests/observation_e2e.cjs, with the same Playwright/browser environment as the UI regression; ORCHARD_TEST_PYTHON optionally chooses the installed Python executable. The script starts observation_http_fixture.py itself. Do not point it at a running Orchard.

The fixture initializes the real application/task/review schemas in a TemporaryDirectory, binds127.0.0.1 on an ephemeral port, and serves the real GET handler. POST and worker starts are explicitly refused in this test fixture. Stdin-only controls change synthetic status between phases; per-phase database hashes verify browser/HTTP reads did not change the database. Requests use only the assigned loopback origin, with no response mocking in this integration test. Success, HTTP refusal, failed refresh and recovery are checked; normal cleanup stops both browser/server and removes fixture storage. This is not native-runtime or production-security qualification.
