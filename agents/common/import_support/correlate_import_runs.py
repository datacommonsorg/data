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
"""Correlates import version history with exact GCS run summaries."""

from datetime import datetime
from datetime import timezone
import json
import posixpath
import re
import sys
from typing import Any
from urllib.parse import urlparse

from absl import app
from absl import flags
from google.api_core import exceptions
from google.auth import exceptions as auth_exceptions
from google.cloud import spanner
from google.cloud import storage

_FLAGS = flags.FLAGS

_HISTORY_COLUMNS = (
    'Version',
    'UpdateTimestamp',
    'WorkflowExecutionID',
    'Comment',
)
_IMPORT_NAME_PATTERN = re.compile(
    r'^(?P<directory>[A-Za-z0-9_/-]+):(?P<name>[A-Za-z0-9_-]+)$')
_WORKFLOW_COMMENT_PATTERN = re.compile(
    r'(?P<kind>import-workflow|ingestion-workflow):(?P<id>[^\s]+)')
_MODES = ('import_history', 'import_version')
_MAX_RUN_LIMIT = 20
_MAX_VERSION_DISCOVERY_LIMIT = 100
_MAX_EVENT_SCAN_LIMIT = 100
_SUMMARY_FILENAME = 'import_summary.json'


def _define_flags() -> None:
    flags.DEFINE_enum('mode', None, _MODES, 'Import evidence mode to query.')
    flags.mark_flag_as_required('mode')
    flags.DEFINE_string('absolute_import_name', None,
                        'Absolute Data Commons import identity.')
    flags.mark_flag_as_required('absolute_import_name')
    flags.DEFINE_string('spanner_project', None,
                        'Google Cloud project containing Spanner history.')
    flags.mark_flag_as_required('spanner_project')
    flags.DEFINE_string('spanner_instance', None,
                        'Spanner instance containing import history.')
    flags.mark_flag_as_required('spanner_instance')
    flags.DEFINE_string('spanner_database', None,
                        'Spanner database containing import history.')
    flags.mark_flag_as_required('spanner_database')
    flags.DEFINE_string('gcs_project', None,
                        'Google Cloud project containing run summaries.')
    flags.mark_flag_as_required('gcs_project')
    flags.DEFINE_string('gcs_bucket', None,
                        'GCS bucket containing import artifacts.')
    flags.mark_flag_as_required('gcs_bucket')
    flags.DEFINE_string('gcs_output_prefix', '',
                        'Optional output prefix within the GCS bucket.')
    flags.DEFINE_string('version', None,
                        'Import version for import_version mode.')
    flags.DEFINE_integer('limit', None,
                         'Maximum number of import runs to return.')
    flags.DEFINE_string('start_time', None,
                        'Optional inclusive RFC3339 history start time.')
    flags.DEFINE_string('end_time', None,
                        'Optional exclusive RFC3339 history end time.')


class ImportRunCorrelationError(ValueError):
    """Raised when import run evidence cannot be correlated."""


def parse_rfc3339(value: str) -> datetime:
    """Parses an RFC3339 timestamp and normalizes it to UTC."""
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ImportRunCorrelationError(
            f'Invalid RFC3339 timestamp: {value}') from exc
    if parsed.tzinfo is None:
        raise ImportRunCorrelationError(
            f'Timestamp must include a timezone: {value}')
    return parsed.astimezone(timezone.utc)


def normalize_import_name(absolute_import_name: str,
                          gcs_output_prefix: str = '') -> dict[str, Any]:
    """Validates an absolute import name and derives its GCS prefix."""
    match = _IMPORT_NAME_PATTERN.fullmatch(absolute_import_name)
    if not match:
        raise ImportRunCorrelationError(
            'absolute_import_name must be <manifest-directory>:<import-name>.')

    directory = match.group('directory').strip('/')
    simple_name = match.group('name')
    if not directory:
        raise ImportRunCorrelationError('Manifest directory cannot be empty.')
    output_prefix = gcs_output_prefix.strip('/')
    gcs_prefix = posixpath.join(directory, simple_name)
    if output_prefix:
        gcs_prefix = posixpath.join(output_prefix, gcs_prefix)
    name_candidates = list(dict.fromkeys((absolute_import_name, simple_name)))
    return {
        'absolute_import_name': absolute_import_name,
        'simple_import_name': simple_name,
        'gcs_prefix': gcs_prefix,
        'spanner_name_candidates': name_candidates,
    }


def expected_version_uri(bucket: str, gcs_prefix: str, version: str) -> str:
    """Builds the expected GCS URI for one import version."""
    return f'gs://{bucket}/{posixpath.join(gcs_prefix, version)}'


def validate_version(version: str) -> str:
    """Validates a caller-supplied version path component."""
    value = version.strip()
    if not value or '/' in value or value in ('.', '..'):
        raise ImportRunCorrelationError(
            'version must be one non-empty GCS path component.')
    return value


def version_candidates(bucket: str, gcs_prefix: str, version: str) -> list[str]:
    """Returns the bare and full-URI forms stored in version history."""
    return [version, expected_version_uri(bucket, gcs_prefix, version)]


def normalize_stored_version(stored_version: Any, bucket: str,
                             gcs_prefix: str) -> tuple[str | None, list[str]]:
    """Normalizes a bare version or full GCS version URI."""
    if not isinstance(stored_version, str) or not stored_version.strip():
        return None, ['missing_stored_version']
    value = stored_version.strip().rstrip('/')
    if not value.startswith('gs://'):
        if '/' in value:
            return None, ['invalid_stored_version']
        return value, []

    parsed = urlparse(value)
    version = posixpath.basename(parsed.path)
    expected_parent = f'/{gcs_prefix.strip("/")}'
    warnings = []
    if parsed.netloc != bucket:
        warnings.append('stored_version_bucket_mismatch')
    if posixpath.dirname(parsed.path) != expected_parent:
        warnings.append('stored_version_prefix_mismatch')
    return version or None, warnings


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(child) for key, child in value.items()}
    return value


def _validate_time_range(start_time: datetime | None,
                         end_time: datetime | None) -> None:
    if (start_time is None) != (end_time is None):
        raise ImportRunCorrelationError(
            'start_time and end_time must be supplied together.')
    if start_time is not None and start_time >= end_time:
        raise ImportRunCorrelationError('start_time must precede end_time.')


def _execute_query(project: str, instance: str, database: str, sql: str,
                   params: dict[str, Any], param_types: dict[str, Any],
                   client: Any | None) -> list[Any]:
    spanner_client = client or spanner.Client(project=project,
                                              disable_builtin_metrics=True)
    database_client = spanner_client.instance(instance).database(database)
    try:
        with database_client.snapshot() as snapshot:
            return list(
                snapshot.execute_sql(sql,
                                     params=params,
                                     param_types=param_types))
    except Exception as exc:
        error = ImportRunCorrelationError(
            f'Unable to read ImportVersionHistory: {exc}')
        error.add_note(
            f'Database: projects/{project}/instances/{instance}/databases/{database}'
        )
        raise error from exc


def query_latest_versions(project: str,
                          instance: str,
                          database: str,
                          import_names: list[str],
                          limit: int,
                          start_time: datetime | None = None,
                          end_time: datetime | None = None,
                          client: Any | None = None) -> dict[str, Any]:
    """Discovers a bounded set of raw versions ordered by latest event."""
    if limit < 1 or limit > _MAX_VERSION_DISCOVERY_LIMIT:
        raise ImportRunCorrelationError(
            'version discovery limit must be between 1 and '
            f'{_MAX_VERSION_DISCOVERY_LIMIT}.')
    _validate_time_range(start_time, end_time)

    predicates = ['ImportName IN UNNEST(@import_names)']
    params: dict[str, Any] = {
        'import_names': import_names,
        'limit': limit + 1,
    }
    param_types: dict[str, Any] = {
        'import_names': spanner.param_types.Array(spanner.param_types.STRING),
        'limit': spanner.param_types.INT64,
    }
    if start_time is not None:
        predicates.extend(
            ('UpdateTimestamp >= @start_time', 'UpdateTimestamp < @end_time'))
        params.update({'start_time': start_time, 'end_time': end_time})
        param_types.update({
            'start_time': spanner.param_types.TIMESTAMP,
            'end_time': spanner.param_types.TIMESTAMP,
        })

    sql = ('SELECT Version, MAX(UpdateTimestamp) AS LatestUpdateTimestamp '
           'FROM ImportVersionHistory WHERE ' + ' AND '.join(predicates) +
           ' GROUP BY Version '
           'ORDER BY LatestUpdateTimestamp DESC, Version LIMIT @limit')
    raw_rows = _execute_query(project, instance, database, sql, params,
                              param_types, client)
    rows = [{
        'Version': _serialize(row[0]),
        'LatestUpdateTimestamp': _serialize(row[1]),
    } for row in raw_rows[:limit]]
    return {'rows': rows, 'truncated': len(raw_rows) > limit}


def query_version_history(project: str,
                          instance: str,
                          database: str,
                          import_names: list[str],
                          limit: int,
                          start_time: datetime | None = None,
                          end_time: datetime | None = None,
                          versions: list[str] | None = None,
                          client: Any | None = None) -> dict[str, Any]:
    """Runs one bounded, parameterized ImportVersionHistory query."""
    if limit < 1 or limit > _MAX_EVENT_SCAN_LIMIT:
        raise ImportRunCorrelationError(
            f'event scan limit must be between 1 and {_MAX_EVENT_SCAN_LIMIT}.')
    _validate_time_range(start_time, end_time)

    columns = ', '.join(_HISTORY_COLUMNS)
    predicates = ['ImportName IN UNNEST(@import_names)']
    params: dict[str, Any] = {
        'import_names': import_names,
        'limit': limit + 1,
    }
    param_types: dict[str, Any] = {
        'import_names': spanner.param_types.Array(spanner.param_types.STRING),
        'limit': spanner.param_types.INT64,
    }
    if start_time is not None:
        predicates.extend(
            ('UpdateTimestamp >= @start_time', 'UpdateTimestamp < @end_time'))
        params.update({'start_time': start_time, 'end_time': end_time})
        param_types.update({
            'start_time': spanner.param_types.TIMESTAMP,
            'end_time': spanner.param_types.TIMESTAMP,
        })
    if versions:
        predicates.append('Version IN UNNEST(@versions)')
        params['versions'] = versions
        param_types['versions'] = spanner.param_types.Array(
            spanner.param_types.STRING)

    sql = (f'SELECT {columns} FROM ImportVersionHistory WHERE ' +
           ' AND '.join(predicates) +
           ' ORDER BY UpdateTimestamp DESC, ImportName, Version LIMIT @limit')
    raw_rows = _execute_query(project, instance, database, sql, params,
                              param_types, client)

    rows = [
        dict(zip(_HISTORY_COLUMNS, _serialize(tuple(row))))
        for row in raw_rows[:limit]
    ]
    return {'rows': rows, 'truncated': len(raw_rows) > limit}


def _summary_projection(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        'import_name': _serialize(summary.get('import_name')),
        'latest_version': _serialize(summary.get('latest_version')),
        'batch_job_id': _serialize(summary.get('job_id')),
        'summary_status': _serialize(summary.get('status')),
    }


def read_gcs_summary(project: str,
                     bucket_name: str,
                     gcs_prefix: str,
                     version: str,
                     simple_import_name: str,
                     client: Any | None = None) -> dict[str, Any]:
    """Reads and validates one exact GCS import summary."""
    object_name = posixpath.join(gcs_prefix, version, _SUMMARY_FILENAME)
    summary_uri = f'gs://{bucket_name}/{object_name}'
    result: dict[str, Any] = {
        'normalized_version': version,
        'summary_uri': summary_uri,
        'summary_found': False,
        'batch_job_id': None,
        'summary_status': None,
        'object_create_time': None,
        'missing': [],
        'warnings': [],
    }
    try:
        storage_client = client or storage.Client(project=project)
        blob = storage_client.bucket(bucket_name).get_blob(object_name)
        if blob is None:
            result['missing'].append('gcs_import_summary')
            return result
        summary = json.loads(blob.download_as_text())
    except exceptions.NotFound:
        result['missing'].append('gcs_import_summary')
        return result
    except exceptions.Forbidden:
        result['warnings'].append('gcs_permission_denied')
        return result
    except auth_exceptions.DefaultCredentialsError:
        result['warnings'].append('gcs_credentials_unavailable')
        return result
    except json.JSONDecodeError:
        result['warnings'].append('invalid_gcs_import_summary')
        return result
    except exceptions.GoogleAPICallError as exc:
        result['warnings'].append(
            f'gcs_summary_unavailable:{type(exc).__name__}')
        return result

    if not isinstance(summary, dict):
        result['warnings'].append('invalid_gcs_import_summary')
        return result
    result.update(_summary_projection(summary))
    result.update({
        'summary_found': True,
        'object_create_time': _serialize(getattr(blob, 'time_created', None)),
        'object_update_time': _serialize(getattr(blob, 'updated', None)),
        'generation': _serialize(getattr(blob, 'generation', None)),
    })
    identity_mismatch = False
    if result['import_name'] != simple_import_name:
        result['warnings'].append('summary_import_name_mismatch')
        identity_mismatch = True
    expected_uri = expected_version_uri(bucket_name, gcs_prefix, version)
    latest_version = result['latest_version']
    if latest_version and latest_version.rstrip('/') != expected_uri:
        result['warnings'].append('summary_latest_version_mismatch')
        identity_mismatch = True
    if identity_mismatch:
        result['summary_status'] = None
    if not result['batch_job_id']:
        result['missing'].append('batch_job_id')
    return result


def classify_workflow_reference(row: dict[str, Any]) -> dict[str, Any]:
    """Classifies typed and comment-based Workflow execution references."""
    typed_id = row.get('WorkflowExecutionID') or None
    comment = row.get('Comment') or ''
    match = _WORKFLOW_COMMENT_PATTERN.search(comment)
    comment_id = match.group('id') if match else None
    kind = match.group('kind').replace('-', '_') if match else 'unknown'
    if not match and comment.startswith('version-override:'):
        kind = 'version_override'
    elif not match and 'revert' in comment.casefold():
        kind = 'rollback'

    if typed_id and comment_id and typed_id != comment_id:
        return {
            'kind': kind,
            'execution_id': None,
            'typed_execution_id': typed_id,
            'comment_execution_id': comment_id,
            'source': 'conflicting_fields',
            'confidence': 'ambiguous',
        }
    execution_id = comment_id or typed_id
    if comment_id and typed_id:
        source = 'comment_and_typed_column'
    elif comment_id:
        source = 'comment'
    elif typed_id:
        source = 'typed_column'
    else:
        source = None
    return {
        'kind': kind,
        'execution_id': execution_id,
        'typed_execution_id': typed_id,
        'comment_execution_id': comment_id,
        'source': source,
        'confidence': 'exact' if execution_id else 'unknown',
    }


def _history_event(row: dict[str, Any], bucket: str,
                   gcs_prefix: str) -> dict[str, Any]:
    version, warnings = normalize_stored_version(row.get('Version'), bucket,
                                                 gcs_prefix)
    workflow = classify_workflow_reference(row)
    return {
        'version': version,
        'update_timestamp': row.get('UpdateTimestamp'),
        'workflow': workflow,
        'warnings': warnings,
    }


def _select_import_workflow(
        events: list[dict[str, Any]]) -> tuple[str | None, Any, list[str]]:
    """Selects one unambiguous ET Workflow reference for a version."""
    references: dict[str, Any] = {}
    issues = []
    for event in events:
        workflow = event['workflow']
        if workflow['kind'] != 'import_workflow':
            continue
        if workflow['confidence'] == 'ambiguous':
            issues.append('conflicting_import_workflow_fields')
            continue
        execution_id = workflow['execution_id']
        if execution_id and execution_id not in references:
            references[execution_id] = event['update_timestamp']
    if len(references) == 1:
        return (*next(iter(references.items())), issues)
    if len(references) > 1:
        issues.append('multiple_import_workflow_executions')
    return None, None, issues


def _run_record(version: str, gcs_bucket: str, gcs_prefix: str,
                events: list[dict[str, Any]],
                summary: dict[str, Any]) -> dict[str, Any]:
    """Builds one minimal ET run record from correlated evidence."""
    workflow_id, workflow_time, issues = _select_import_workflow(events)
    batch_job_id = summary.get('batch_job_id')
    missing = []
    if workflow_id is None:
        missing.append('workflow_execution_id')
    if not summary.get('summary_found'):
        missing.append('gcs_import_summary')
    if not batch_job_id:
        missing.append('batch_job_id')
    issues.extend(summary.get('warnings', []))
    result = {
        'version': version,
        'gcs_base_path': expected_version_uri(gcs_bucket, gcs_prefix, version),
        'workflow_execution_id': workflow_id,
        'batch_job_id': batch_job_id,
        'summary_status': summary.get('summary_status'),
        'workflow_recorded_at': workflow_time,
        'gcs_summary_created_at': summary.get('object_create_time'),
        'missing': missing,
    }
    if issues:
        result['issues'] = list(dict.fromkeys(issues))
    return result


def correlate_import_runs(mode: str,
                          absolute_import_name: str,
                          spanner_project: str,
                          spanner_instance: str,
                          spanner_database: str,
                          gcs_project: str,
                          gcs_bucket: str,
                          gcs_output_prefix: str = '',
                          version: str | None = None,
                          limit: int | None = None,
                          start_time: datetime | None = None,
                          end_time: datetime | None = None,
                          spanner_client: Any | None = None,
                          storage_client: Any | None = None) -> dict[str, Any]:
    """Correlates bounded Spanner history with exact GCS summaries."""
    if mode not in _MODES:
        raise ImportRunCorrelationError(f'Unsupported mode: {mode}')
    if limit is not None and (limit < 1 or limit > _MAX_RUN_LIMIT):
        raise ImportRunCorrelationError(
            f'limit must be between 1 and {_MAX_RUN_LIMIT}.')
    identity = normalize_import_name(absolute_import_name, gcs_output_prefix)
    run_limit = limit or 1
    selected_versions = []
    discovery_truncated = False
    issues = []
    if mode == 'import_version':
        if start_time is not None or end_time is not None:
            raise ImportRunCorrelationError(
                'UTC range is only valid for import_history mode.')
        if version is None:
            raise ImportRunCorrelationError(
                'version is required for import_version mode.')
        selected_versions.append(validate_version(version))
    elif version is not None:
        raise ImportRunCorrelationError(
            'version is only valid for import_version mode.')
    else:
        discovery = query_latest_versions(spanner_project,
                                          spanner_instance,
                                          spanner_database,
                                          identity['spanner_name_candidates'],
                                          _MAX_VERSION_DISCOVERY_LIMIT,
                                          start_time=start_time,
                                          end_time=end_time,
                                          client=spanner_client)
        normalized_versions = []
        rejected_before_limit = False
        for row in discovery['rows']:
            discovered_version, warnings = normalize_stored_version(
                row.get('Version'), gcs_bucket, identity['gcs_prefix'])
            if discovered_version is None or warnings:
                if len(normalized_versions) < run_limit:
                    rejected_before_limit = True
                continue
            if discovered_version not in normalized_versions:
                normalized_versions.append(discovered_version)
        selected_versions.extend(normalized_versions[:run_limit])
        discovery_truncated = (discovery['truncated'] or
                               len(normalized_versions) > run_limit or
                               rejected_before_limit)
        if rejected_before_limit:
            issues.append('newer_history_version_rejected')

    detail_version_candidates = [
        candidate for selected_version in selected_versions for candidate in
        version_candidates(gcs_bucket, identity['gcs_prefix'], selected_version)
    ]
    history = {'rows': [], 'truncated': False}
    if detail_version_candidates:
        history = query_version_history(spanner_project,
                                        spanner_instance,
                                        spanner_database,
                                        identity['spanner_name_candidates'],
                                        _MAX_EVENT_SCAN_LIMIT,
                                        start_time=start_time,
                                        end_time=end_time,
                                        versions=detail_version_candidates,
                                        client=spanner_client)
    events = [
        _history_event(row, gcs_bucket, identity['gcs_prefix'])
        for row in history['rows']
    ]

    events_by_version: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        event_version = event['version']
        if event_version and not event['warnings']:
            events_by_version.setdefault(event_version, []).append(event)

    summaries = [
        read_gcs_summary(gcs_project,
                         gcs_bucket,
                         identity['gcs_prefix'],
                         item,
                         identity['simple_import_name'],
                         client=storage_client) for item in selected_versions
    ]
    summaries_by_version = {
        summary['normalized_version']: summary for summary in summaries
    }
    runs = [
        _run_record(item, gcs_bucket, identity['gcs_prefix'],
                    events_by_version.get(item, []), summaries_by_version[item])
        for item in selected_versions
    ]
    result = {
        'mode': mode,
        'import_name': absolute_import_name,
        'runs': runs,
        'truncated': discovery_truncated or history['truncated'],
    }
    if issues:
        result['issues'] = issues
    return result


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError('Unexpected positional arguments.')
    try:
        start_time = (parse_rfc3339(_FLAGS.start_time)
                      if _FLAGS.start_time else None)
        end_time = (parse_rfc3339(_FLAGS.end_time) if _FLAGS.end_time else None)
        result = correlate_import_runs(
            _FLAGS.mode,
            _FLAGS.absolute_import_name,
            _FLAGS.spanner_project,
            _FLAGS.spanner_instance,
            _FLAGS.spanner_database,
            _FLAGS.gcs_project,
            _FLAGS.gcs_bucket,
            gcs_output_prefix=_FLAGS.gcs_output_prefix,
            version=_FLAGS.version,
            limit=_FLAGS.limit,
            start_time=start_time,
            end_time=end_time)
    except ImportRunCorrelationError as exc:
        print(json.dumps({'error': str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(3) from exc
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    _define_flags()
    app.run(main)
