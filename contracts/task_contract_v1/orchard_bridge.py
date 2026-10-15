"""Read-only snapshot interpreter; never import Orchard or connect to its storage."""
import json
import sys
import uuid
if __package__:
    from .validate import ContractError, _unique_object, digest, validate_shape
else:
    from validate import ContractError, _unique_object, digest, validate_shape

MAX_BYTES = 262144
FIELDS = {"id", "request", "status", "evidence", "receipt", "application_status"}
STATES = {"NEEDS_OWNER_DECISION", "RUNNING", "DONE", "BLOCKED"}
APPLICATION_STATES = {"READY", "FAILED", "APPLYING", "APPLIED", "RESTORING",
                      "RESTORED", "INTERRUPTED", "RECOVERY_NEEDED"}

def validate_observation(observation):
    """Shape and metadata integrity only; caller content cannot confer authority."""
    validate_shape(observation, "orchard-observation.schema.json")
    selected = {"id": observation["legacy_task_id"],
                "status": observation["reported_status"],
                "application_status": observation["reported_application"]}
    if observation["metadata_sha256"] != digest(selected):
        raise ContractError("observation metadata mismatch")

def inspect_row(row):
    """Project only unauthenticated legacy metadata, without promoting any state."""
    if type(row) is not dict or set(row) - FIELDS:
        raise ContractError("unsupported row shape")
    if not {"id", "status", "application_status"} <= set(row):
        raise ContractError("missing observation fields")
    task_id, status, application = row["id"], row["status"], row["application_status"]
    if type(task_id) is not str or len(task_id) != 36:
        raise ContractError("invalid legacy task identity")
    try:
        parsed = uuid.UUID(task_id)
    except ValueError:
        raise ContractError("invalid legacy task identity") from None
    if str(parsed) != task_id or parsed.version != 4:
        raise ContractError("unsupported legacy task identity")
    if type(status) is not str or status not in STATES:
        raise ContractError("unknown legacy execution state")
    if application is not None and (type(application) is not str or application not in APPLICATION_STATES):
        raise ContractError("unknown legacy application state")
    selected = {"id": task_id, "status": status, "application_status": application}
    observation = {
        "schema_version": 1,
        "kind": "orchard_legacy_snapshot_observation",
        "legacy_task_id": task_id,
        "metadata_sha256": digest(selected),
        "reported_status": status,
        "reported_execution": {"DONE": "completed", "RUNNING": "running"}.get(status, "unknown"),
        "reported_application": application,
        "execution": "unverified",
        "acceptance": "unverified",
        "application": "unverified",
        "authority": "none",
        "freshness": "snapshot_only",
        "runtime_compatible": False,
        "missing_runtime_seams": ["prepare", "start_ack_binding", "observe_cursor",
                                 "confirmed_cancel", "trusted_capture", "independent_gate"],
    }
    validate_observation(observation)
    return observation

def decode(data):
    if type(data) is not bytes or len(data) > MAX_BYTES:
        raise ContractError("input exceeds snapshot limit")
    try:
        row = json.loads(data, object_pairs_hook=_unique_object,
                         parse_constant=lambda _: (_ for _ in ()).throw(ContractError("nonfinite input")))
        return inspect_row(row)
    except (ValueError, UnicodeError, RecursionError, TypeError):
        raise ContractError("invalid snapshot (content withheld)") from None

def main():
    # No path argument: the caller supplies an explicitly selected export via stdin.
    if len(sys.argv) != 1:
        print("REFUSED: no file or worker arguments supported", file=sys.stderr)
        return 2
    try:
        observation = decode(sys.stdin.buffer.read(MAX_BYTES + 1))
    except ContractError:
        print("REFUSED: invalid or unsupported snapshot (content withheld)", file=sys.stderr)
        return 2
    print(json.dumps(observation, sort_keys=True, allow_nan=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
