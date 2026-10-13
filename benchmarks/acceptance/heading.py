"""Check an exact approved edit without running candidate code."""
from pathlib import Path

BEFORE = (Path(__file__).resolve().parents[1] / 'cases/heading/index.html').read_bytes()
AFTER = BEFORE.replace(b'Small steps, verified results.', b'Good work takes extraordinary teamwork!', 1)

def check(project):
    candidate = Path(project) / 'index.html'
    if candidate.is_symlink():
        raise ValueError('Candidate page must be an ordinary file')
    if candidate.read_bytes() != AFTER:
        raise ValueError('The requested heading is missing or unrelated content changed')
