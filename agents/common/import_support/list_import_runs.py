# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Lists bounded Workflow executions and filters exact import identities."""

from datetime import datetime
from datetime import timezone
import json
import sys
from typing import Any

from absl import app
from absl import flags
from google.cloud.workflows import executions_v1

_FLAGS = flags.FlagValues()
_WORKFLOW_RESOURCE = flags.DEFINE_string(
    'workflow_resource',
    None,
    'Full projects/.../locations/.../workflows/... resource.',
    flag_values=_FLAGS)
_ABSOLUTE_IMPORT_NAME = flags.DEFINE_string(
    'absolute_import_name',
    None,
    'Exact directory:import_name identity.',
    flag_values=_FLAGS)
_START_TIME = flags.DEFINE_string('start_time',
                                  None,
                                  'Inclusive RFC3339 UTC start time.',
                                  flag_values=_FLAGS)
_END_TIME = flags.DEFINE_string('end_time',
                                None,
                                'Inclusive RFC3339 UTC end time.',
                                flag_values=_FLAGS)
_RUN_LIMIT = flags.DEFINE_integer('run_limit',
                                  10,
                                  'Maximum matching runs to return.',
                                  flag_values=_FLAGS)
_SCAN_LIMIT = flags.DEFINE_integer('scan_limit',
                                   5000,
                                   'Maximum Workflow executions to inspect.',
                                   flag_values=_FLAGS)

_MAX_RUN_LIMIT = 50
_MAX_SCAN_LIMIT = 5000
_MAX_ERROR_LENGTH = 4000


class WorkflowExecutionError(RuntimeError):
    """Raised when Workflow execution history cannot be collected."""


def parse_rfc3339(value: str) -> datetime:
    """Parses an RFC3339 timestamp and requires an explicit timezone."""
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise WorkflowExecutionError(
            f'Invalid RFC3339 timestamp: {value}') from exc
    if parsed.tzinfo is None:
        raise WorkflowExecutionError(
            f'Timestamp must include a timezone: {value}')
    return parsed.astimezone(timezone.utc)


def format_rfc3339(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def _timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return format_rfc3339(value)
    if hasattr(value, 'ToJsonString'):
        return value.ToJsonString()
    text = str(value)
    return text or None


def _enum_name(enum_type: Any, value: Any) -> str:
    if hasattr(value, 'name'):
        return value.name
    try:
        return enum_type(value).name
    except (TypeError, ValueError):
        return str(value)


def _parse_json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def execution_to_dict(execution: Any) -> dict[str, Any]:
    """Converts one proto-plus execution into a bounded safe dictionary."""
    error = getattr(execution, 'error', None)
    status = getattr(execution, 'status', None)
    current_steps = []
    for step in getattr(status, 'current_steps', []) if status else []:
        current_steps.append({
            'step': getattr(step, 'step', ''),
            'routine': getattr(step, 'routine', ''),
        })
    error_payload = getattr(error, 'payload', '') if error else ''
    error_context = getattr(error, 'context', '') if error else ''
    return {
        'name':
            getattr(execution, 'name', ''),
        'create_time':
            _timestamp(getattr(execution, 'create_time', None)),
        'start_time':
            _timestamp(getattr(execution, 'start_time', None)),
        'end_time':
            _timestamp(getattr(execution, 'end_time', None)),
        'duration':
            str(getattr(execution, 'duration', '') or ''),
        'state':
            _enum_name(executions_v1.Execution.State,
                       getattr(execution, 'state', 0)),
        'argument_raw':
            getattr(execution, 'argument', '') or '',
        'result_raw':
            getattr(execution, 'result', '') or '',
        'error': {
            'payload': error_payload[:_MAX_ERROR_LENGTH],
            'context': error_context[:_MAX_ERROR_LENGTH],
        } if error_payload or error_context else {},
        'workflow_revision_id':
            getattr(execution, 'workflow_revision_id', ''),
        'current_steps':
            current_steps,
        'labels':
            dict(getattr(execution, 'labels', {}) or {}),
    }


def normalize_execution(record: dict[str, Any]) -> dict[str, Any]:
    """Parses argument/result and adds stable run identity fields."""
    argument = _parse_json_object(record.pop('argument_raw', ''))
    result = _parse_json_object(record.pop('result_raw', ''))
    name = record.get('name', '')
    normalized = dict(record)
    normalized.update({
        'id': name.rsplit('/', 1)[-1] if name else '',
        'argument': {
            'import_name': argument.get('importName'),
            'has_import_config': 'importConfig' in argument,
            'resources': argument.get('resources', {}),
        },
        'result': {
            'job_id': result.get('jobId'),
            'import_name': result.get('importName'),
        } if result else {},
    })
    return normalized


def list_workflow_execution_records(
        workflow_resource: str,
        start_time: datetime,
        end_time: datetime,
        scan_limit: int = _MAX_SCAN_LIMIT,
        client: Any | None = None) -> dict[str, Any]:
    """Lists FULL executions within a bounded window."""
    if start_time >= end_time:
        raise WorkflowExecutionError('start_time must be before end_time.')
    if scan_limit < 1 or scan_limit > _MAX_SCAN_LIMIT:
        raise WorkflowExecutionError(
            f'scan_limit must be between 1 and {_MAX_SCAN_LIMIT}.')
    request = executions_v1.ListExecutionsRequest(
        parent=workflow_resource,
        page_size=100,
        view=executions_v1.ExecutionView.FULL,
        filter=(f'createTime >= "{format_rfc3339(start_time)}" AND '
                f'createTime <= "{format_rfc3339(end_time)}"'),
        order_by='createTime desc',
    )
    executions_client = client or executions_v1.ExecutionsClient()
    try:
        pager = executions_client.list_executions(request=request)
        records: list[dict[str, Any]] = []
        page_count = 0
        truncated = False
        for page in pager.pages:
            page_count += 1
            for execution in page.executions:
                if len(records) >= scan_limit:
                    truncated = True
                    break
                records.append(normalize_execution(
                    execution_to_dict(execution)))
            if truncated:
                break
    except Exception as exc:
        raise WorkflowExecutionError(
            f'Unable to list Workflow executions: {exc}') from exc
    return {
        'workflow_resource': workflow_resource,
        'start_time': format_rfc3339(start_time),
        'end_time': format_rfc3339(end_time),
        'executions': records,
        'scanned_execution_count': len(records),
        'page_count': page_count,
        'truncated': truncated,
    }


def filter_import_runs(execution_result: dict[str, Any],
                       absolute_import_name: str,
                       run_limit: int = 10) -> dict[str, Any]:
    """Selects newest exact import matches from normalized executions."""
    if run_limit < 1 or run_limit > _MAX_RUN_LIMIT:
        raise WorkflowExecutionError(
            f'run_limit must be between 1 and {_MAX_RUN_LIMIT}.')
    matches = [
        execution for execution in execution_result['executions'] if
        execution.get('argument', {}).get('import_name') == absolute_import_name
    ]
    result = dict(execution_result)
    result.pop('executions')
    result.update({
        'absolute_import_name': absolute_import_name,
        'runs': matches[:run_limit],
        'matching_execution_count': len(matches),
        'result_truncated': len(matches) > run_limit,
    })
    return result


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError('Unexpected positional arguments.')
    required = {
        '--workflow_resource': _WORKFLOW_RESOURCE.value,
        '--absolute_import_name': _ABSOLUTE_IMPORT_NAME.value,
        '--start_time': _START_TIME.value,
        '--end_time': _END_TIME.value,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise app.UsageError(f'Missing required flags: {", ".join(missing)}')
    try:
        listed = list_workflow_execution_records(
            _WORKFLOW_RESOURCE.value,
            parse_rfc3339(_START_TIME.value),
            parse_rfc3339(_END_TIME.value),
            scan_limit=_SCAN_LIMIT.value,
        )
        result = filter_import_runs(listed, _ABSOLUTE_IMPORT_NAME.value,
                                    _RUN_LIMIT.value)
    except WorkflowExecutionError as exc:
        print(json.dumps({'error': str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(3) from exc
    print(json.dumps(result, indent=2, sort_keys=True))


def _parse_flags(argv: list[str]) -> list[str]:
    remaining = flags.FLAGS(argv, known_only=True)
    return _FLAGS(remaining)


if __name__ == '__main__':
    app.run(main, flags_parser=_parse_flags)
