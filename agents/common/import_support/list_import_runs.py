# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Lists bounded Workflow executions with their exact import identities."""

from datetime import datetime
from datetime import timezone
import json
import sys
from typing import Any

from absl import app
from absl import flags
from google.cloud.workflows import executions_v1

_FLAGS = flags.FLAGS

_MAX_RUN_LIMIT = 100
_MAX_SCAN_LIMIT = 5000
_MAX_ERROR_LENGTH = 4000


def _define_flags() -> None:
    flags.DEFINE_string('workflow_resource', None,
                        'Full Google Cloud Workflow resource name.')
    flags.mark_flag_as_required('workflow_resource')
    flags.DEFINE_string('start_time', None,
                        'Inclusive RFC3339 execution start time.')
    flags.mark_flag_as_required('start_time')
    flags.DEFINE_string('end_time', None,
                        'Inclusive RFC3339 execution end time.')
    flags.mark_flag_as_required('end_time')
    flags.DEFINE_string('absolute_import_name', '',
                        'Optional exact Data Commons import identity.')
    flags.DEFINE_integer('run_limit', 10,
                         'Maximum number of matching runs to return.')
    flags.DEFINE_integer('scan_limit', _MAX_SCAN_LIMIT,
                         'Maximum number of Workflow executions to scan.')


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


def _execution_record(execution: Any) -> dict[str, Any]:
    """Converts one FULL execution into a bounded, safe record."""
    argument = _parse_json_object(getattr(execution, 'argument', ''))
    result = _parse_json_object(getattr(execution, 'result', ''))
    name = getattr(execution, 'name', '')
    error = getattr(execution, 'error', None)
    error_payload = getattr(error, 'payload', '') if error else ''
    error_context = getattr(error, 'context', '') if error else ''
    status = getattr(execution, 'status', None)
    current_steps = [{
        'step': getattr(step, 'step', ''),
        'routine': getattr(step, 'routine', ''),
    } for step in getattr(status, 'current_steps', []) if status]
    return {
        'batch_job_id':
            result.get('jobId'),
        'create_time':
            _timestamp(getattr(execution, 'create_time', None)),
        'current_steps':
            current_steps,
        'duration':
            str(getattr(execution, 'duration', '') or ''),
        'end_time':
            _timestamp(getattr(execution, 'end_time', None)),
        'error': {
            'context': error_context[:_MAX_ERROR_LENGTH],
            'payload': error_payload[:_MAX_ERROR_LENGTH],
        } if error_payload or error_context else {},
        'id':
            name.rsplit('/', 1)[-1] if name else '',
        'import_name':
            argument.get('importName'),
        'name':
            name,
        'result_import_name':
            result.get('importName'),
        'start_time':
            _timestamp(getattr(execution, 'start_time', None)),
        'state':
            _enum_name(executions_v1.Execution.State,
                       getattr(execution, 'state', 0)),
        'workflow_revision_id':
            getattr(execution, 'workflow_revision_id', ''),
    }


def list_workflow_execution_records(
        workflow_resource: str,
        start_time: datetime,
        end_time: datetime,
        scan_limit: int = _MAX_SCAN_LIMIT,
        client: Any | None = None) -> dict[str, Any]:
    """Lists FULL executions within a bounded window without follow-up reads."""
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
    records: list[dict[str, Any]] = []
    page_count = 0
    truncated = False
    try:
        for page in executions_client.list_executions(request=request).pages:
            page_count += 1
            for execution in page.executions:
                if len(records) >= scan_limit:
                    truncated = True
                    break
                records.append(_execution_record(execution))
            if truncated:
                break
    except Exception as exc:
        error = WorkflowExecutionError(
            f'Unable to list Workflow executions: {exc}')
        error.add_note(f'Workflow resource: {workflow_resource}')
        raise error from exc

    return {
        'end_time': format_rfc3339(end_time),
        'executions': records,
        'page_count': page_count,
        'scanned_execution_count': len(records),
        'scan_truncated': truncated,
        'start_time': format_rfc3339(start_time),
        'workflow_resource': workflow_resource,
    }


def select_runs(execution_result: dict[str, Any],
                absolute_import_name: str = '',
                run_limit: int = 10) -> dict[str, Any]:
    """Returns bounded runs, optionally filtered by exact import identity."""
    if run_limit < 1 or run_limit > _MAX_RUN_LIMIT:
        raise WorkflowExecutionError(
            f'run_limit must be between 1 and {_MAX_RUN_LIMIT}.')
    executions = execution_result['executions']
    matches = [
        execution for execution in executions if not absolute_import_name or
        execution.get('import_name') == absolute_import_name
    ]
    result = {
        key: value
        for key, value in execution_result.items()
        if key != 'executions'
    }
    result.update({
        'absolute_import_name': absolute_import_name or None,
        'matching_execution_count': len(matches),
        'result_truncated': len(matches) > run_limit,
        'run_limit': run_limit,
        'runs': matches[:run_limit],
    })
    return result


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError('Unexpected positional arguments.')
    try:
        listed = list_workflow_execution_records(
            _FLAGS.workflow_resource,
            parse_rfc3339(_FLAGS.start_time),
            parse_rfc3339(_FLAGS.end_time),
            scan_limit=_FLAGS.scan_limit,
        )
        result = select_runs(listed, _FLAGS.absolute_import_name,
                             _FLAGS.run_limit)
    except WorkflowExecutionError as exc:
        print(json.dumps({'error': str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(3) from exc
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    _define_flags()
    app.run(main)
