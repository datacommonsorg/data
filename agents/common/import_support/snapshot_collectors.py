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
"""Read-only collectors used to build import information snapshots."""

import ast
import base64
import binascii
from datetime import datetime
from datetime import timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import quote

from google.cloud import spanner

from agents.common.import_support.command_runner import CommandError
from agents.common.import_support.command_runner import ReadOnlyCommandRunner
from agents.common.import_support.list_import_runs import format_rfc3339

_WORKFLOW_TARGET = re.compile(
    r'^https://workflowexecutions\.googleapis\.com/v1/'
    r'projects/(?P<project>[^/]+)/locations/(?P<location>[^/]+)/'
    r'workflows/(?P<workflow>[^/]+)/executions$')
_SAFE_WORKFLOW_ENV = {
    'GCS_BUCKET_ID', 'GCS_MOUNT_BUCKET', 'GOOGLE_CLOUD_PROJECT_ID', 'LOCATION',
    'PROJECT_NUMBER'
}
_SAFE_HELPER_ENV = {
    'GCS_BUCKET_ID', 'SPANNER_PROJECT_ID', 'SPANNER_INSTANCE_ID',
    'SPANNER_DATABASE_ID'
}
_SAFE_IMPORT_CONFIG = {
    'gcp_project_id', 'gcs_project_id', 'storage_prod_bucket_name',
    'storage_version_filename'
}
_STRUCTURED_LOG_TYPES = ('auto-import-job-stage', 'auto-import-job-status')
_SUMMARY_LIMIT = 50
_SPANNER_COLUMNS = {
    'ImportStatus': {
        'ImportName', 'LatestVersion', 'GraphPath', 'State', 'JobId',
        'WorkflowId', 'ExecutionTime', 'DataVolume', 'DataImportTimestamp',
        'StatusUpdateTimestamp', 'NextRefreshTimestamp'
    },
    'ImportVersionHistory': {
        'ImportName', 'Version', 'UpdateTimestamp', 'WorkflowExecutionID',
        'Status', 'ExecutionTime', 'NodeCount', 'EdgeCount', 'ObservationCount',
        'TimeSeriesCount', 'Comment'
    },
    'IngestionHistory': {
        'WorkflowExecutionID', 'CreationTimestamp', 'CompletionTimestamp',
        'IngestionFailure', 'Status', 'Stage', 'DataflowJobID',
        'IngestedImports', 'ExecutionTime', 'NodeCount', 'EdgeCount',
        'ObservationCount', 'TimeSeriesCount'
    },
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def load_executor_defaults(repo_root: Path) -> dict[str, Any]:
    """Reads literal ExecutorConfig defaults without importing production code."""
    config_path = repo_root / 'import-automation/executor/app/configs.py'
    tree = ast.parse(config_path.read_text(encoding='utf-8'),
                     filename=str(config_path))
    values: dict[str, Any] = {}
    wanted = {
        'gcp_project_id', 'gcs_project_id', 'storage_prod_bucket_name',
        'storage_version_filename', 'storage_version_history_filename',
        'scheduler_location', 'cloud_workflow_id'
    }
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != 'ExecutorConfig':
            continue
        for item in node.body:
            if not isinstance(item, ast.AnnAssign):
                continue
            if not isinstance(item.target, ast.Name):
                continue
            if item.target.id not in wanted or item.value is None:
                continue
            try:
                values[item.target.id] = ast.literal_eval(item.value)
            except (ValueError, TypeError):
                continue
    return values


def _pick(mapping: dict[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in mapping:
            return mapping[name]
    return default


def _decode_json(value: str | bytes | None) -> dict[str, Any]:
    if not value:
        return {}
    if isinstance(value, bytes):
        value = value.decode('utf-8')
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def decode_scheduler_job(job: dict[str, Any]) -> dict[str, Any]:
    """Returns allowlisted Scheduler data and a decoded Workflow argument."""
    target = _pick(job, 'httpTarget', 'http_target', default={}) or {}
    body = target.get('body')
    outer: dict[str, Any] = {}
    if isinstance(body, str):
        try:
            outer = _decode_json(base64.b64decode(body, validate=True))
        except (ValueError, binascii.Error):
            outer = _decode_json(body)
    elif isinstance(body, bytes):
        outer = _decode_json(body)
    elif isinstance(body, dict):
        outer = body
    argument_value = outer.get('argument')
    argument = (_decode_json(argument_value) if isinstance(
        argument_value, (str, bytes)) else
                argument_value if isinstance(argument_value, dict) else {})
    import_config_value = argument.get('importConfig')
    import_config = (
        _decode_json(import_config_value) if isinstance(import_config_value,
                                                        (str, bytes)) else
        import_config_value if isinstance(import_config_value, dict) else {})
    retry = _pick(job, 'retryConfig', 'retry_config', default={}) or {}
    return {
        'resource_name': job.get('name'),
        'description': job.get('description'),
        'state': job.get('state'),
        'schedule': job.get('schedule'),
        'time_zone': _pick(job, 'timeZone', 'time_zone'),
        'retry_config': {
            'retry_count':
                _pick(retry, 'retryCount', 'retry_count'),
            'max_retry_duration':
                _pick(retry, 'maxRetryDuration', 'max_retry_duration'),
            'min_backoff_duration':
                _pick(retry, 'minBackoffDuration', 'min_backoff_duration'),
            'max_backoff_duration':
                _pick(retry, 'maxBackoffDuration', 'max_backoff_duration'),
        },
        'attempt_deadline': _pick(job, 'attemptDeadline', 'attempt_deadline'),
        'last_attempt_time': _pick(job, 'lastAttemptTime', 'last_attempt_time'),
        'schedule_time': _pick(job, 'scheduleTime', 'schedule_time'),
        'status': job.get('status', {}),
        'target_uri': target.get('uri'),
        'target_import_name': argument.get('importName'),
        'target_has_import_config': 'importConfig' in argument,
        'target_import_config': {
            key: value
            for key, value in import_config.items()
            if key in _SAFE_IMPORT_CONFIG
        },
        'target_resources': argument.get('resources', {}),
    }


def parse_workflow_target(uri: str) -> dict[str, str]:
    match = _WORKFLOW_TARGET.match(uri or '')
    if not match:
        raise ValueError(f'Unsupported Scheduler Workflow target: {uri}')
    values = match.groupdict()
    values['resource'] = (
        f'projects/{values["project"]}/locations/{values["location"]}/'
        f'workflows/{values["workflow"]}')
    return values


def safe_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    env = _pick(workflow, 'userEnvVars', 'user_env_vars', default={}) or {}
    source = _pick(workflow, 'sourceContents', 'source_contents', default='')
    source_hash = hashlib.sha256(source.encode(
        'utf-8')).hexdigest() if isinstance(source, str) and source else None
    helper_match = (re.search(r'https://([a-z][a-z0-9-]*-service)-', source)
                    if isinstance(source, str) else None)
    return {
        'resource_name':
            workflow.get('name'),
        'state':
            workflow.get('state'),
        'revision_id':
            _pick(workflow, 'revisionId', 'revision_id'),
        'update_time':
            _pick(workflow, 'updateTime', 'update_time'),
        'service_account':
            _pick(workflow, 'serviceAccount', 'service_account'),
        'call_log_level':
            _pick(workflow, 'callLogLevel', 'call_log_level'),
        'execution_history_level':
            _pick(workflow, 'executionHistoryLevel', 'execution_history_level'),
        'user_environment': {
            key: value
            for key, value in env.items()
            if key in _SAFE_WORKFLOW_ENV
        },
        'source_sha256':
            source_hash,
        'ingestion_helper_service':
            helper_match.group(1) if helper_match else None,
    }


def describe_scheduler(runner: ReadOnlyCommandRunner, import_name: str,
                       absolute_import_name: str, project: str,
                       location: str) -> dict[str, Any]:
    raw = runner.run_json([
        'gcloud', 'scheduler', 'jobs', 'describe', import_name,
        f'--project={project}', f'--location={location}', '--format=json'
    ])
    safe = decode_scheduler_job(raw)
    safe['description_matches'] = safe['description'] == absolute_import_name
    safe['target_import_matches'] = (
        safe['target_import_name'] == absolute_import_name)
    safe['verified'] = (safe['description_matches'] and
                        safe['target_import_matches'])
    return safe


def list_schedulers(runner: ReadOnlyCommandRunner,
                    project: str,
                    location: str,
                    limit: int = 1000) -> list[dict[str, Any]]:
    raw = runner.run_json([
        'gcloud', 'scheduler', 'jobs', 'list', f'--project={project}',
        f'--location={location}', f'--limit={limit}', '--format=json'
    ])
    return [decode_scheduler_job(job) for job in raw if isinstance(job, dict)]


def describe_workflow(runner: ReadOnlyCommandRunner,
                      target: dict[str, str],
                      revision_id: str = '') -> dict[str, Any]:
    args = [
        'gcloud', 'workflows', 'describe', target['workflow'],
        f'--project={target["project"]}', f'--location={target["location"]}'
    ]
    if revision_id:
        args.append(f'--revision-id={revision_id}')
    args.append('--format=json')
    return safe_workflow(runner.run_json(args))


def _container_env(service: dict[str, Any]) -> dict[str, str]:
    template = service.get('spec', {}).get('template', {})
    containers = template.get('spec', {}).get('containers', [])
    if not containers:
        template = service.get('template', {})
        containers = template.get('containers', [])
    values: dict[str, str] = {}
    for container in containers:
        for item in container.get('env', []):
            name = item.get('name')
            value = item.get('value')
            if name in _SAFE_HELPER_ENV and isinstance(value, str):
                values[name] = value
    return values


def describe_ingestion_helper(runner: ReadOnlyCommandRunner, project: str,
                              location: str,
                              service_name: str) -> dict[str, Any]:
    raw = runner.run_json([
        'gcloud', 'run', 'services', 'describe', service_name,
        f'--project={project}', f'--region={location}', '--format=json'
    ])
    metadata = raw.get('metadata', {})
    status = raw.get('status', {})
    return {
        'resource_name': metadata.get('name') or raw.get('name'),
        'url': status.get('url') or raw.get('uri'),
        'latest_revision': status.get('latestReadyRevisionName'),
        'environment': _container_env(raw),
    }


def derive_batch_prefix(import_name: str) -> str:
    return import_name[:50].lower().replace('_', '-') + '-'


def _batch_runnable(job: dict[str, Any]) -> dict[str, Any]:
    groups = _pick(job, 'taskGroups', 'task_groups', default=[]) or []
    if not groups:
        return {}
    task_spec = _pick(groups[0], 'taskSpec', 'task_spec', default={}) or {}
    runnables = task_spec.get('runnables', [])
    return runnables[0] if runnables else {}


def batch_import_identity(job: dict[str, Any]) -> str | None:
    runnable = _batch_runnable(job)
    env = runnable.get('environment', {}).get('variables', {})
    if env.get('IMPORT_NAME'):
        return env['IMPORT_NAME']
    container = runnable.get('container', {})
    for command in container.get('commands', []):
        if command.startswith('--import_name='):
            return command.split('=', 1)[1]
    return None


def _batch_import_config(job: dict[str, Any]) -> dict[str, Any]:
    container = _batch_runnable(job).get('container', {})
    for command in container.get('commands', []):
        if not command.startswith('--import_config='):
            continue
        config = _decode_json(command.split('=', 1)[1])
        return {
            key: value
            for key, value in config.items()
            if key in _SAFE_IMPORT_CONFIG
        }
    return {}


def safe_batch_job(job: dict[str, Any]) -> dict[str, Any]:
    runnable = _batch_runnable(job)
    container = runnable.get('container', {})
    env = runnable.get('environment', {}).get('variables', {})
    groups = _pick(job, 'taskGroups', 'task_groups', default=[]) or []
    task_spec = (_pick(groups[0], 'taskSpec', 'task_spec', default={})
                 if groups else {}) or {}
    allocation = _pick(job, 'allocationPolicy', 'allocation_policy',
                       default={}) or {}
    return {
        'resource_name':
            job.get('name'),
        'uid':
            job.get('uid'),
        'create_time':
            _pick(job, 'createTime', 'create_time'),
        'update_time':
            _pick(job, 'updateTime', 'update_time'),
        'status':
            _safe_batch_status(job.get('status', {})),
        'import_identity':
            batch_import_identity(job),
        'import_config':
            _batch_import_config(job),
        'batch_job_name':
            env.get('BATCH_JOB_NAME'),
        'image_uri':
            _pick(container, 'imageUri', 'image_uri'),
        'compute_resource':
            _pick(task_spec, 'computeResource', 'compute_resource', default={}),
        'allocation_policy': {
            'instances': allocation.get('instances', []),
        },
    }


def _safe_batch_status(status: Any) -> dict[str, Any]:
    if not isinstance(status, dict):
        return {}
    safe_events = []
    events = _pick(status, 'statusEvents', 'status_events', default=[]) or []
    for event in events if isinstance(events, list) else []:
        if not isinstance(event, dict):
            continue
        safe_events.append({
            'type': _pick(event, 'type', 'type_'),
            'event_time': _pick(event, 'eventTime', 'event_time'),
            'task_state': _pick(event, 'taskState', 'task_state'),
        })
    return {
        'state': status.get('state'),
        'status_events': safe_events,
    }


def safe_batch_tasks(tasks: Any) -> list[dict[str, Any]]:
    result = []
    for task in tasks if isinstance(tasks, list) else []:
        result.append({
            'resource_name': task.get('name'),
            'status': _safe_batch_status(task.get('status', {})),
        })
    return result


def batch_task_start_time(job: dict[str, Any]) -> str | None:
    """Returns the earliest observed RUNNING task event for one Batch job."""
    timestamps = []
    for task in job.get('tasks', []):
        status = task.get('status', {})
        for event in status.get('status_events', []):
            if str(event.get('task_state') or '').upper() != 'RUNNING':
                continue
            timestamp = event.get('event_time')
            if timestamp:
                timestamps.append(str(timestamp))
    return min(timestamps) if timestamps else None


def _describe_batch_job(runner: ReadOnlyCommandRunner, project: str,
                        location: str, job_id: str) -> dict[str, Any]:
    job_id = job_id.rsplit('/', 1)[-1]
    job = runner.run_json([
        'gcloud', 'batch', 'jobs', 'describe', job_id, f'--project={project}',
        f'--location={location}', '--format=json'
    ])
    tasks = runner.run_json([
        'gcloud', 'batch', 'tasks', 'list', f'--job={job_id}',
        f'--project={project}', f'--location={location}', '--format=json'
    ])
    safe = safe_batch_job(job)
    safe['tasks'] = safe_batch_tasks(tasks)
    return safe


def collect_batch_for_run(runner: ReadOnlyCommandRunner, run: dict[str, Any],
                          expected_import_name: str, project: str,
                          location: str) -> dict[str, Any]:
    """Joins one Workflow execution to verified Batch evidence."""
    job_id = run.get('result', {}).get('job_id')
    if job_id:
        job = _describe_batch_job(runner, project, location, job_id)
        matches = job.get('import_identity') == expected_import_name
        return {
            'correlation': 'exact' if matches else 'ambiguous',
            'evidence': [
                'workflow.result.jobId', 'batch runnable import identity'
            ],
            'expected_job_id': job_id,
            'unavailable_reason': None,
            'jobs': [job],
        }
    start = run.get('start_time') or run.get('create_time')
    if not start:
        return unavailable_batch_evidence(run, 'missing_job_id_and_start_time')
    end = run.get('end_time') or format_rfc3339(now_utc())
    simple_name = expected_import_name.rsplit(':', 1)[-1]
    prefix = derive_batch_prefix(simple_name)
    raw_candidates = runner.run_json([
        'gcloud', 'batch', 'jobs', 'list', f'--project={project}',
        f'--location={location}',
        f'--filter=name:{prefix} AND createTime>="{start}" AND createTime<="{end}"',
        '--limit=20', '--format=json'
    ])
    matches = []
    for candidate in raw_candidates if isinstance(raw_candidates, list) else []:
        candidate_id = (candidate.get('name') or '').rsplit('/', 1)[-1]
        if not candidate_id:
            continue
        described = _describe_batch_job(runner, project, location, candidate_id)
        if described.get('import_identity') == expected_import_name:
            matches.append(described)
    if len(matches) == 1:
        return {
            'correlation': 'time_correlated',
            'evidence': [
                'bounded execution time', 'batch runnable import identity'
            ],
            'expected_job_id': None,
            'unavailable_reason': None,
            'jobs': matches,
        }
    return {
        'correlation': 'ambiguous' if matches else 'unknown',
        'evidence': [
            'bounded execution time', 'batch runnable import identity'
        ],
        'expected_job_id': None,
        'unavailable_reason': None if matches else 'no_verified_batch_job',
        'jobs': matches,
    }


def unavailable_batch_evidence(run: dict[str, Any],
                               reason: str) -> dict[str, Any]:
    """Returns the stable shape for unavailable Batch evidence."""
    expected_job_id = run.get('result', {}).get('job_id')
    evidence = ['workflow.result.jobId'] if expected_job_id else []
    return {
        'correlation': 'unknown',
        'evidence': evidence,
        'expected_job_id': expected_job_id,
        'unavailable_reason': reason,
        'jobs': [],
    }


def safe_log_entry(entry: dict[str, Any]) -> dict[str, Any]:
    payload = entry.get('jsonPayload', {})
    if not isinstance(payload, dict):
        payload = {}
    allowed_payload = {
        key: payload.get(key)
        for key in ('log_type', 'import_name', 'stage_name', 'status',
                    'latency_secs', 'data_bytes')
        if isinstance(payload.get(key), (str, int, float, bool))
    }
    if ('stage_name' not in allowed_payload and
            isinstance(payload.get('stage'), (str, int, float, bool))):
        allowed_payload['stage_name'] = payload['stage']
    if ('latency_secs' not in allowed_payload and
            isinstance(payload.get('latency'), (str, int, float, bool))):
        allowed_payload['latency_secs'] = payload['latency']
    labels = entry.get('labels', {}) or {}
    return {
        'timestamp': entry.get('timestamp'),
        'severity': entry.get('severity'),
        'log_name': entry.get('logName'),
        'job_uid': labels.get('job_uid'),
        'json_payload': allowed_payload,
    }


def collect_batch_logs(runner: ReadOnlyCommandRunner, project: str,
                       job_uid: str, start_time: str, end_time: str,
                       limit: int) -> tuple[list[dict[str, Any]], bool]:
    log_types = ' OR '.join(f'jsonPayload.log_type="{log_type}"'
                            for log_type in _STRUCTURED_LOG_TYPES)
    log_filter = (f'logName="projects/{project}/logs/batch_task_logs" '
                  f'AND labels.job_uid="{job_uid}" '
                  f'AND timestamp>="{start_time}" AND timestamp<="{end_time}" '
                  f'AND ({log_types})')
    entries = runner.run_json([
        'gcloud', 'logging', 'read', log_filter, f'--project={project}',
        '--order=desc', f'--limit={limit + 1}', '--format=json'
    ],
                              timeout=120)
    raw_entries = entries if isinstance(entries, list) else []
    safe_entries = [
        safe_log_entry(entry)
        for entry in raw_entries
        if isinstance(entry, dict) and
        isinstance(entry.get('jsonPayload'), dict) and
        entry['jsonPayload'].get('log_type') in _STRUCTURED_LOG_TYPES
    ]
    truncated = len(safe_entries) > limit
    return list(reversed(safe_entries[:limit])), truncated


def _object_uri(item: dict[str, Any]) -> str | None:
    if item.get('url'):
        return item['url']
    name = item.get('name')
    bucket = item.get('bucket')
    if isinstance(bucket, str) and bucket.startswith('gs://'):
        bucket = bucket[5:]
    if name and bucket:
        return f'gs://{bucket}/{name}'
    return name if isinstance(name, str) and name.startswith('gs://') else None


def safe_storage_object(item: dict[str, Any]) -> dict[str, Any] | None:
    uri = _object_uri(item)
    if not uri:
        return None
    return {
        'uri': uri,
        'size': item.get('size'),
        'generation': item.get('generation'),
        'updated': item.get('updated') or item.get('updateTime'),
    }


def list_import_objects(runner: ReadOnlyCommandRunner, project: str,
                        bucket: str, base_prefix: str,
                        object_limit: int) -> tuple[list[dict[str, Any]], bool]:
    raw = runner.run_json([
        'gcloud', 'storage', 'objects', 'list',
        f'gs://{bucket}/{base_prefix}/**', f'--project={project}',
        '--sort-by=~name', f'--limit={object_limit + 1}', '--format=json'
    ],
                          timeout=180)
    objects = []
    for item in raw if isinstance(raw, list) else []:
        safe = safe_storage_object(item)
        if safe:
            objects.append(safe)
    return objects[:object_limit], len(objects) > object_limit


def list_import_summaries(
        runner: ReadOnlyCommandRunner, project: str, bucket: str,
        base_prefix: str) -> tuple[list[dict[str, Any]], bool]:
    raw = runner.run_json([
        'gcloud', 'storage', 'objects', 'list',
        f'gs://{bucket}/{base_prefix}/**/import_summary.json',
        f'--project={project}', '--sort-by=~name',
        f'--limit={_SUMMARY_LIMIT + 1}', '--format=json'
    ],
                          timeout=180)
    summaries = []
    for item in raw if isinstance(raw, list) else []:
        safe = safe_storage_object(item)
        if safe:
            summaries.append(safe)
    return summaries[:_SUMMARY_LIMIT], len(summaries) > _SUMMARY_LIMIT


def read_storage_text(runner: ReadOnlyCommandRunner, project: str,
                      uri: str) -> str:
    return runner.run_text(
        ['gcloud', 'storage', 'cat', uri, f'--project={project}'],
        timeout=90).strip()


def _category(uri: str, import_input_basenames: set[str]) -> str | None:
    if '/source_files/' in uri:
        return 'raw_source_files'
    if '/validation/' in uri:
        return 'validation'
    if '/genmcf/' in uri:
        return 'resolved_mcf' if uri.endswith('.mcf') else 'genmcf_outputs'
    if uri.rsplit('/', 1)[-1] in import_input_basenames:
        return 'import_tool_inputs'
    return None


def collect_gcs_evidence(runner: ReadOnlyCommandRunner,
                         project: str,
                         bucket: str,
                         base_prefix: str,
                         import_inputs: tuple[dict[str, str], ...],
                         expected_import_name: str,
                         job_ids: set[str],
                         accepted_pointer_name: str,
                         object_limit: int = 1000) -> dict[str, Any]:
    """Lists actual objects and joins summaries to Batch job IDs."""
    warnings: list[str] = []
    pointers: dict[str, Any] = {}
    for role, filename in (('staging', 'staging_version.txt'),
                           ('accepted', accepted_pointer_name)):
        uri = f'gs://{bucket}/{base_prefix}/{filename}'
        try:
            pointers[role] = {
                'filename': filename,
                'config_field':
                    ('storage_version_filename' if role == 'accepted' else None
                    ),
                'uri': uri,
                'value': read_storage_text(runner, project, uri),
            }
        except CommandError as exc:
            pointers[role] = {
                'filename': filename,
                'config_field':
                    ('storage_version_filename' if role == 'accepted' else None
                    ),
                'uri': uri,
                'value': None,
                'error': str(exc),
            }
    try:
        summary_objects, summary_truncated = list_import_summaries(
            runner, project, bucket, base_prefix)
    except CommandError as exc:
        summary_objects = []
        summary_truncated = False
        warnings.append(f'GCS summary listing unavailable: {exc}')
    try:
        objects, objects_truncated = list_import_objects(
            runner, project, bucket, base_prefix, object_limit)
    except CommandError as exc:
        objects = []
        objects_truncated = False
        warnings.append(f'GCS object listing unavailable: {exc}')
    summaries: dict[str, dict[str, Any]] = {}
    for item in summary_objects:
        try:
            summary = _decode_json(
                read_storage_text(runner, project, item['uri']))
        except CommandError as exc:
            warnings.append(f'Unable to read {item["uri"]}: {exc}')
            continue
        job_id = str(summary.get('job_id') or '')
        if (summary.get('import_name') == expected_import_name and job_id and
            (not job_ids or job_id in job_ids) and job_id not in summaries):
            version_uri = item['uri'].rsplit('/', 1)[0]
            summary['summary_uri'] = item['uri']
            summary['version_uri'] = version_uri
            summaries[job_id] = summary
    input_basenames = {
        Path(path).name
        for import_input in import_inputs
        for path in import_input.values()
        if isinstance(path, str)
    }
    artifacts_by_job: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for job_id, summary in summaries.items():
        categories = {
            'acquisition_sources': [],
            'raw_source_files': [],
            'import_tool_inputs': [],
            'genmcf_outputs': [],
            'resolved_mcf': [],
            'unresolved_mcf': [],
            'validation': [],
        }
        version_uri = summary['version_uri'] + '/'
        for item in objects:
            if not item['uri'].startswith(version_uri):
                continue
            category = _category(item['uri'], input_basenames)
            if category:
                categories[category].append(item)
        artifacts_by_job[job_id] = categories
    return {
        'base_uri': f'gs://{bucket}/{base_prefix}/',
        'version_pointers': pointers,
        'objects': objects,
        'summaries_by_job_id': summaries,
        'artifacts_by_job_id': artifacts_by_job,
        'summary_truncated': summary_truncated,
        'objects_truncated': objects_truncated,
        'truncated': summary_truncated or objects_truncated,
        'warnings': warnings,
    }


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return format_rfc3339(value)
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(child) for key, child in value.items()}
    return value


def _query_rows(snapshot: Any, sql: str, columns: list[str], params: dict[str,
                                                                          Any],
                param_types: dict[str, Any]) -> list[dict[str, Any]]:
    rows = snapshot.execute_sql(sql, params=params, param_types=param_types)
    return [dict(zip(columns, _serialize(tuple(row)))) for row in rows]


def read_spanner_records(project: str,
                         instance: str,
                         database: str,
                         import_name: str,
                         limit: int = 50,
                         client: Any | None = None) -> dict[str, Any]:
    """Reads current, version, and downstream history with bound parameters."""
    spanner_client = client or spanner.Client(project=project)
    db = spanner_client.instance(instance).database(database)
    params = {'import_name': import_name}
    types = {'import_name': spanner.param_types.STRING}
    with db.snapshot() as snapshot:
        schema_rows = snapshot.execute_sql(
            'SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS '
            'WHERE TABLE_NAME IN UNNEST(@table_names)',
            params={'table_names': list(_SPANNER_COLUMNS)},
            param_types={
                'table_names':
                    spanner.param_types.Array(spanner.param_types.STRING)
            })
        observed_columns: dict[str, set[str]] = {}
        for table_name, column_name in schema_rows:
            observed_columns.setdefault(table_name, set()).add(column_name)
        missing = {
            table_name:
                sorted(columns - observed_columns.get(table_name, set()))
            for table_name, columns in _SPANNER_COLUMNS.items()
            if columns - observed_columns.get(table_name, set())
        }
        if missing:
            raise ValueError(f'Unsupported Spanner schema; missing: {missing}')
        status_columns = [
            'ImportName', 'LatestVersion', 'GraphPath', 'State', 'JobId',
            'WorkflowId', 'ExecutionTime', 'DataVolume', 'DataImportTimestamp',
            'StatusUpdateTimestamp', 'NextRefreshTimestamp'
        ]
        status = _query_rows(
            snapshot, 'SELECT ' + ', '.join(status_columns) +
            ' FROM ImportStatus WHERE ImportName = @import_name',
            status_columns, params, types)
        history_params = {**params, 'limit': limit + 1}
        history_types = {**types, 'limit': spanner.param_types.INT64}
        version_columns = [
            'ImportName', 'Version', 'UpdateTimestamp', 'WorkflowExecutionID',
            'Status', 'ExecutionTime', 'NodeCount', 'EdgeCount',
            'ObservationCount', 'TimeSeriesCount', 'Comment'
        ]
        version_rows = _query_rows(
            snapshot, 'SELECT ' + ', '.join(version_columns) +
            ' FROM ImportVersionHistory WHERE ImportName = @import_name '
            'ORDER BY UpdateTimestamp DESC LIMIT @limit', version_columns,
            history_params, history_types)
        ingestion_columns = [
            'WorkflowExecutionID', 'CreationTimestamp', 'CompletionTimestamp',
            'IngestionFailure', 'Status', 'Stage', 'DataflowJobID',
            'IngestedImports', 'ExecutionTime', 'NodeCount', 'EdgeCount',
            'ObservationCount', 'TimeSeriesCount'
        ]
        ingestion_rows = _query_rows(
            snapshot, 'SELECT ' + ', '.join(ingestion_columns) +
            ' FROM IngestionHistory WHERE @import_name IN '
            'UNNEST(IngestedImports) ORDER BY CreationTimestamp DESC '
            'LIMIT @limit', ingestion_columns, history_params, history_types)
    return {
        'database_resource':
            f'projects/{project}/instances/{instance}/databases/{database}',
        'import_status':
            status[0] if status else {},
        'version_history':
            version_rows[:limit],
        'downstream_ingestion_history':
            ingestion_rows[:limit],
        'truncated': {
            'version_history': len(version_rows) > limit,
            'downstream_ingestion_history': len(ingestion_rows) > limit,
        },
        'limit':
            limit,
    }


def scheduler_link(project: str, location: str) -> str:
    return ('https://console.cloud.google.com/cloudscheduler?project=' +
            quote(project) + '&location=' + quote(location))


def workflow_link(project: str, location: str, workflow: str) -> str:
    return ('https://console.cloud.google.com/workflows/workflow/' +
            quote(location) + '/' + quote(workflow) + '/executions?project=' +
            quote(project))


def batch_link(project: str, location: str, job_id: str) -> str:
    return ('https://console.cloud.google.com/batch/jobsDetail/regions/' +
            quote(location) + '/jobs/' + quote(job_id) + '?project=' +
            quote(project))


def gcs_link(project: str, bucket: str, prefix: str) -> str:
    return ('https://console.cloud.google.com/storage/browser/' +
            quote(bucket) + '/' + quote(prefix) + '?project=' + quote(project))


def cloud_run_link(project: str, location: str, service: str) -> str:
    return ('https://console.cloud.google.com/run/detail/' + quote(location) +
            '/' + quote(service) + '/metrics?project=' + quote(project))


def spanner_link(project: str, instance: str, database: str) -> str:
    return ('https://console.cloud.google.com/spanner/instances/' +
            quote(instance) + '/databases/' + quote(database) +
            '/details?project=' + quote(project))


def normalize_pipeline_status(summary: dict[str, Any]) -> str | None:
    value = summary.get('status')
    if isinstance(value, dict):
        value = value.get('name') or value.get('value')
    if not value:
        return None
    return str(value).rsplit('.', 1)[-1].upper()


def technical_state(run: dict[str, Any], batch_jobs: list[dict[str,
                                                               Any]]) -> str:
    workflow_state = str(run.get('state') or '').upper()
    batch_states = [
        str(job.get('status', {}).get('state') or '').upper()
        for job in batch_jobs
    ]
    if workflow_state in ('ACTIVE', 'QUEUED') or any(
            state in ('QUEUED', 'SCHEDULED', 'RUNNING')
            for state in batch_states):
        return 'running'
    if workflow_state in ('FAILED', 'CANCELLED', 'UNAVAILABLE') or any(
            state in ('FAILED', 'DELETION_IN_PROGRESS')
            for state in batch_states):
        return 'failed'
    return 'completed' if workflow_state == 'SUCCEEDED' else 'unknown'


def composite_status(run: dict[str, Any], batch_jobs: list[dict[str, Any]],
                     summary: dict[str,
                                   Any], publication_observed: bool) -> str:
    technical = technical_state(run, batch_jobs)
    if technical in ('running', 'failed'):
        return technical
    pipeline = normalize_pipeline_status(summary)
    if pipeline == 'VALIDATION' or pipeline == 'FAILURE':
        return 'failed'
    if pipeline == 'SKIP':
        return 'skipped'
    if pipeline == 'STAGING' and publication_observed:
        return 'succeeded'
    return 'unknown'
