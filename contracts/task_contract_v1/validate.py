"""Design-fixture validator. Never execute task text, paths, commands or model output."""
import copy
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

class ContractError(ValueError):
    """Invalid shape, unsupported contract or untrusted receipt."""

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()

def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError('duplicate JSON key')
        result[key] = value
    return result

def load(path):
    data = Path(path).read_bytes()
    if len(data) > 262144:
        raise ContractError('document exceeds fixture size limit')
    return json.loads(data, object_pairs_hook=_unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ContractError('non-finite JSON')))

SCHEMA_KEYS = {'$schema', '$id', '$comment', 'type', 'properties', 'required',
               'additionalProperties', 'const', 'enum', 'minLength', 'maxLength',
               'pattern', 'minimum', 'maximum', 'items', 'minItems', 'maxItems',
               'uniqueItems', 'not', 'allOf', 'if', 'then'}

def check_schema(schema):
    """Fail closed for unsupported vocabulary; not a general JSON Schema engine."""
    if not isinstance(schema, dict) or set(schema) - SCHEMA_KEYS:
        raise ContractError('unsupported schema vocabulary')
    for child in schema.get('properties', {}).values():
        check_schema(child)
    for key in ['items', 'not', 'if', 'then']:
        if key in schema:
            check_schema(schema[key])
    for child in schema.get('allOf', []):
        check_schema(child)

def schema_matches(value, schema):
    typ = schema.get('type')
    matches_type = {'object': isinstance(value, dict), 'array': isinstance(value, list),
                    'string': isinstance(value, str), 'integer': type(value) is int,
                    'boolean': type(value) is bool}
    if typ and not matches_type.get(typ, False):
        return False
    if 'const' in schema and (type(value) is not type(schema['const']) or value != schema['const']):
        return False
    if 'enum' in schema and not any(type(value) is type(v) and value == v for v in schema['enum']):
        return False
    if isinstance(value, dict):
        props = schema.get('properties', {})
        if not set(schema.get('required', [])) <= set(value):
            return False
        if schema.get('additionalProperties') is False and set(value) - set(props):
            return False
        if any(not schema_matches(v, props[k]) for k, v in value.items() if k in props):
            return False
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0) or len(value) > schema.get('maxLength', float('inf')):
            return False
        if 'pattern' in schema and not re.search(schema['pattern'], value, flags=re.ASCII):
            return False
    if type(value) is int:
        if value < schema.get('minimum', -float('inf')) or value > schema.get('maximum', float('inf')):
            return False
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0) or len(value) > schema.get('maxItems', float('inf')):
            return False
        if schema.get('uniqueItems') and len({digest(v) for v in value}) != len(value):
            return False
        if 'items' in schema and any(not schema_matches(v, schema['items']) for v in value):
            return False
    if 'not' in schema and schema_matches(value, schema['not']):
        return False
    if any(not schema_matches(value, child) for child in schema.get('allOf', [])):
        return False
    if 'if' in schema and schema_matches(value, schema['if']):
        if not schema_matches(value, schema.get('then', {})):
            return False
    return True

def validate_shape(value, filename):
    schema = load(ROOT / filename)
    check_schema(schema)
    if not schema_matches(value, schema):
        raise ContractError('schema violation (content withheld)')

def validate_contract(contract):
    validate_shape(contract, 'task-contract.schema.json')
    caps = contract['requested_capabilities']
    ids = [item['id'] for item in contract['acceptance']]
    if len(ids) != len(set(ids)):
        raise ContractError('duplicate acceptance identity')
    checks = [item['check_id'] for item in contract['acceptance']]
    if len(checks) != len(set(checks)) or set(checks) != set(caps['execute_checks']):
        raise ContractError('acceptance/check registry mismatch')
    if not set(caps['write_paths']) <= set(caps['read_paths']):
        raise ContractError('write paths must be readable')
    if contract['privacy'] == 'secret':
        raise ContractError('secret content is never model context')
    if contract['privacy'] == 'local_only' and (
            caps['network'] or not contract['execution_profile']['local']):
        raise ContractError('local-only routing violates contract')
    if caps['paid_inference'] and contract['limits']['max_cost_microusd'] == 0:
        raise ContractError('paid work has no budget')
    return contract

def validate_result(contract, result):
    validate_contract(contract)
    validate_shape(result, 'task-result.schema.json')
    if (result['task_id'], result['run_id'], result['contract_sha256']) != (
            contract['task_id'], contract['run_id'], digest(contract)):
        raise ContractError('result is not bound to contract')
    if result['terminal'] == 'DONE':
        expected = {(c['id'], c['check_id']) for c in contract['acceptance']}
        actual = {(e['criterion_id'], e['check_id']) for e in result['evidence']}
        if actual != expected or len(result['evidence']) != len(expected):
            raise ContractError('missing or duplicate task acceptance evidence')
        if any(a['path'] not in contract['requested_capabilities']['write_paths'] for a in result['artifacts']):
            raise ContractError('artifact outside contract write scope')
        artifacts = {a['sha256'] for a in result['artifacts']}
        for evidence in result['evidence']:
            if (evidence['verifier_actor_id'] != contract['independent_gate']['verifier_actor_id']
                    or evidence['artifact_sha256'] not in artifacts):
                raise ContractError('evidence actor/artifact mismatch')
    elif result['acceptance'] == 'passed' or result['independent_gate'] == 'passed':
        raise ContractError('non-DONE result cannot claim passed acceptance/gate')
    return result

# Trusted runner-authored fixtures, never eval/exec of submitted source.
GOOD_SOURCE = 'def mean(values):\n    if not values: raise ValueError("empty")\n    return sum(values) / len(values)\n'
BAD_SOURCE = 'def mean(values):\n    if not values: raise ValueError("empty")\n    return sum(values) // len(values)\n'

def good_mean(values):
    if not values:
        raise ValueError('empty')
    return sum(values) / len(values)

def bad_mean(values):
    if not values:
        raise ValueError('empty')
    return sum(values) // len(values)

FIXTURES = {'correct': (GOOD_SOURCE, good_mean), 'incorrect': (BAD_SOURCE, bad_mean)}

def fractional_check(function):
    return function([1, 2]) == 1.5 and function([-2, 1]) == -0.5

def empty_check(function):
    try:
        function([])
    except ValueError:
        return True
    return False

CHECKS = {'mean_fractional': fractional_check, 'mean_empty': empty_check}

class FakeController:
    """In-memory simulator, not production permissions or durable idempotency."""
    def __init__(self):
        self.results = {}
        self.worker_calls = 0
        self.gate_calls = 0

    def run(self, contract, grant, *, fixture='correct', cancelled=False, missing_evidence=False):
        validate_contract(contract)
        bound = digest(contract)
        run_id = contract['run_id']
        if run_id in self.results:
            previous = self.results[run_id]
            if previous['contract_sha256'] != bound:
                raise ContractError('run identity reused for another contract')
            return copy.deepcopy(previous)
        result = {'schema_version': 1, 'task_id': contract['task_id'], 'run_id': run_id,
                  'contract_sha256': bound, 'terminal': 'BLOCKED', 'execution': 'not_started',
                  'acceptance': 'unverified', 'application': 'not_applied',
                  'independent_gate': 'not_run', 'reason': 'not admitted', 'evidence': [], 'artifacts': []}
        def finish(state, reason):
            result['terminal'], result['reason'] = state, reason
            validate_result(contract, result)
            self.results[run_id] = copy.deepcopy(result)
            return copy.deepcopy(result)
        if cancelled:
            return finish('CANCELLED', 'cancelled before execution')
        # grant is a separate, trusted runner input; task content never issues it.
        if not grant or grant.get('contract_sha256') != bound:
            return finish('NEEDS_OWNER_DECISION', 'missing or stale external grant')
        caps = contract['requested_capabilities']
        if (grant.get('source_revision') != contract['source']['revision']
                or grant.get('worker_actor_id') == contract['independent_gate']['verifier_actor_id']
                or not grant.get('worker_actor_id')):
            return finish('BLOCKED', 'source or independent actor mismatch')
        for key in ['read_paths', 'write_paths', 'execute_checks']:
            if not set(caps[key]) <= set(grant.get(key, [])):
                return finish('BLOCKED', 'requested capabilities exceed external grant')
        if caps['network'] or caps['paid_inference']:
            return finish('BLOCKED', 'fixture supports no network or paid work')
        if (contract['privacy'] == 'local_only' and not grant.get('no_network_proven')):
            return finish('BLOCKED', 'fixture has no admitted no-network evidence')
        if (grant.get('max_cost_microusd') is None or grant['max_cost_microusd'] < 0
                or contract['limits']['max_cost_microusd'] > grant['max_cost_microusd']):
            return finish('BLOCKED', 'unknown or exceeded budget ceiling')
        if (grant.get('wall_seconds') is None
                or contract['limits']['wall_seconds'] > grant['wall_seconds']
                or contract['limits']['max_attempts'] != 1):
            return finish('BLOCKED', 'fixture supports one bounded attempt only')
        if (contract['independent_gate']['gate_id'] != 'mean-acceptance-v1'
                or set(caps['read_paths']) != {'mean.py'} or set(caps['write_paths']) != {'mean.py'}
                or any(c not in CHECKS for c in caps['execute_checks']) or fixture not in FIXTURES):
            return finish('BLOCKED', 'unsupported synthetic path/check/fixture')
        self.worker_calls += 1
        source, function = FIXTURES[fixture]
        artifact_hash = hashlib.sha256(source.encode()).hexdigest()
        result['execution'] = 'completed'
        result['artifacts'] = [{'artifact_ref': 'content_01ARZ3NDEKTSV4RRFFQ69G5FA6', 'path': 'mean.py', 'sha256': artifact_hash}]
        if missing_evidence:
            return finish('UNVERIFIED', 'worker completed; acceptance evidence absent')
        self.gate_calls += 1
        for index, criterion in enumerate(contract['acceptance']):
            passed = CHECKS[criterion['check_id']](function)
            result['evidence'].append({'criterion_id': criterion['id'], 'check_id': criterion['check_id'],
                                      'passed': passed, 'evidence_ref': 'content_01ARZ3NDEKTSV4RRFFQ69G5FA' + str(index + 7),
                                      'artifact_sha256': artifact_hash,
                                      'verifier_actor_id': contract['independent_gate']['verifier_actor_id']})
        passed = all(e['passed'] for e in result['evidence'])
        result['acceptance'] = 'passed' if passed else 'failed'
        result['independent_gate'] = 'passed' if passed else 'failed'
        return finish('DONE' if passed else 'BLOCKED', 'acceptance passed; stop' if passed else 'mandatory acceptance failed; stop')

def example():
    return load(ROOT / 'examples/mean-task.json')

def fixture_grant(contract):
    """Synthetic external approval. Never exported as a production grant API."""
    return {'contract_sha256': digest(contract), 'source_revision': contract['source']['revision'],
            'worker_actor_id': 'actor_01ARZ3NDEKTSV4RRFFQ69G5FAW',
            'read_paths': ['mean.py'], 'write_paths': ['mean.py'],
            'execute_checks': list(CHECKS), 'max_cost_microusd': 0, 'wall_seconds': 30,
            'no_network_proven': False}

if __name__ == '__main__':
    task = example()
    traces = {}
    for label, options in [('success', {}), ('acceptance_failure', {'fixture': 'incorrect'}),
                           ('missing_evidence', {'missing_evidence': True})]:
        controller = FakeController()
        traces[label] = controller.run(task, fixture_grant(task), **options)
    traces['denial'] = FakeController().run(task, None)
    print(json.dumps({'synthetic_only': True, 'traces': traces}, indent=2))
