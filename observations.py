"""Read one task's metadata without opening a worker or mutating logical storage."""
from contextlib import closing
from pathlib import Path
import sqlite3
import uuid
from contracts.task_contract_v1.orchard_bridge import inspect_row
from contracts.task_contract_v1.validate import ContractError

class ObservationError(ValueError):
    pass

def readonly_connection(db):
    # mode=ro refuses creation and SQL writes; query_only is an additional guard.
    connection = sqlite3.connect(Path(db).resolve().as_uri()+"?mode=ro", uri=True, timeout=1)
    connection.execute("PRAGMA query_only=ON")
    return connection

def export_observation(db, task_id):
    try:
        parsed=uuid.UUID(task_id)
        if str(parsed)!=task_id or parsed.version!=4:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ObservationError("Invalid task identity") from None
    try:
        with closing(readonly_connection(db)) as connection:
            # One statement: same snapshot for both reported states. Never select payloads.
            row=connection.execute(
                "SELECT t.id, substr(t.status,1,65), substr(r.status,1,65) "
                "FROM tasks t LEFT JOIN reviews r ON r.task_id=t.id WHERE t.id=?",
                (task_id,)).fetchone()
        if row is None:
            return None
        return inspect_row(dict(id=row[0],status=row[1],application_status=row[2]))
    except (sqlite3.Error, OSError, ContractError):
        raise ObservationError("Observation unavailable or unsupported; no verification claimed") from None
