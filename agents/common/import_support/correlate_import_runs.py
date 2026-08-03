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

import argparse
from datetime import datetime
from datetime import timezone
import json
import posixpath
import re
import sys
from typing import Any
from urllib.parse import urlparse

from google.api_core import exceptions
from google.auth import exceptions as auth_exceptions
from google.cloud import spanner
from google.cloud import storage

_HISTORY_COLUMNS = (
    'ImportName',
    'Version',
    'UpdateTimestamp',
    'WorkflowExecutionID',
    'Status',
    'ExecutionTime',
    'NodeCount',
    'EdgeCount',
    'ObservationCount',
    'TimeSeriesCount',
    'Comment',
)
_IMPORT_NAME_PATTERN = re.compile(
    r'^(?P<directory>[A-Za-z0-9_/-]+):(?P<name>[A-Za-z0-9_-]+)$')
_WORKFLOW_COMMENT_PATTERN = re.compile(
    r'(?P<kind>import-workflow|ingestion-workflow):(?P<id>[^\s]+)')
_MODES = ('import_history', 'import_version')
_MAX_LIMIT = 20
_SUMMARY_FILENAME = 'import_summary.json'


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
    if limit < 1 or limit > _MAX_LIMIT:
        raise ImportRunCorrelationError(
            f'limit must be between 1 and {_MAX_LIMIT}.')
    if (start_time is None) != (end_time is None):
        raise ImportRunCorrelationError(
            'start_time and end_time must be supplied together.')
    if start_time is not None and start_time >= end_time:
        raise ImportRunCorrelationError('start_time must precede end_time.')

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
    spanner_client = client or spanner.Client(project=project,
                                              disable_builtin_metrics=True)
    database_client = spanner_client.instance(instance).database(database)
    try:
        with database_client.snapshot() as snapshot:
            raw_rows = list(
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

    rows = [
        dict(zip(_HISTORY_COLUMNS, _serialize(tuple(row))))
        for row in raw_rows[:limit]
    ]
    return {'rows': rows, 'truncated': len(raw_rows) > limit}


def _summary_projection(summary: dict[str, Any]) -> dict[str, Any]:
    fields = ('import_name', 'status', 'latest_version', 'graph_path',
              'next_refresh', 'execution_time', 'data_volume', 'import_stats')
    result = {field: _serialize(summary.get(field)) for field in fields}
    result['batch_job_id'] = _serialize(summary.get('job_id'))
    return result


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
        'source': 'gcs_import_summary',
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
    if result['import_name'] != simple_import_name:
        result['warnings'].append('summary_import_name_mismatch')
    expected_uri = expected_version_uri(bucket_name, gcs_prefix, version)
    latest_version = result['latest_version']
    if latest_version and latest_version.rstrip('/') != expected_uri:
        result['warnings'].append('summary_latest_version_mismatch')
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
    missing = []
    if version is None:
        missing.append('version')
    if (workflow['typed_execution_id'] is None and
            workflow['comment_execution_id'] is None):
        missing.append('workflow_execution_id')
    return {
        'stored_import_name': row.get('ImportName'),
        'stored_version': row.get('Version'),
        'normalized_version': version,
        'update_timestamp': row.get('UpdateTimestamp'),
        'status': row.get('Status'),
        'execution_time': row.get('ExecutionTime'),
        'node_count': row.get('NodeCount'),
        'edge_count': row.get('EdgeCount'),
        'observation_count': row.get('ObservationCount'),
        'time_series_count': row.get('TimeSeriesCount'),
        'comment': row.get('Comment'),
        'workflow': workflow,
        'source': 'ImportVersionHistory',
        'gcs_summary_eligible': version is not None and not warnings,
        'missing': missing,
        'warnings': warnings,
    }


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
    if limit is not None and (limit < 1 or limit > _MAX_LIMIT):
        raise ImportRunCorrelationError(
            f'limit must be between 1 and {_MAX_LIMIT}.')
    identity = normalize_import_name(absolute_import_name, gcs_output_prefix)
    normalized_input_version = None
    stored_version_candidates = None
    query_limit = limit or 1
    if mode == 'import_version':
        if start_time is not None or end_time is not None:
            raise ImportRunCorrelationError(
                'UTC range is only valid for import_history mode.')
        if version is None:
            raise ImportRunCorrelationError(
                'version is required for import_version mode.')
        normalized_input_version = validate_version(version)
        stored_version_candidates = version_candidates(
            gcs_bucket, identity['gcs_prefix'], normalized_input_version)
        query_limit = limit or _MAX_LIMIT
    elif version is not None:
        raise ImportRunCorrelationError(
            'version is only valid for import_version mode.')

    history = query_version_history(spanner_project,
                                    spanner_instance,
                                    spanner_database,
                                    identity['spanner_name_candidates'],
                                    query_limit,
                                    start_time=start_time,
                                    end_time=end_time,
                                    versions=stored_version_candidates,
                                    client=spanner_client)
    events = [
        _history_event(row, gcs_bucket, identity['gcs_prefix'])
        for row in history['rows']
    ]

    versions_to_read = []
    if normalized_input_version:
        versions_to_read.append(normalized_input_version)
    for event in events:
        event_version = event['normalized_version']
        if (event['gcs_summary_eligible'] and
                event_version not in versions_to_read):
            versions_to_read.append(event_version)
    summaries = [
        read_gcs_summary(gcs_project,
                         gcs_bucket,
                         identity['gcs_prefix'],
                         item,
                         identity['simple_import_name'],
                         client=storage_client) for item in versions_to_read
    ]
    return {
        'mode':
            mode,
        'input': {
            **identity,
            'version': normalized_input_version,
            'start_time': _serialize(start_time),
            'end_time': _serialize(end_time),
        },
        'spanner_database':
            f'projects/{spanner_project}/instances/{spanner_instance}/databases/{spanner_database}',
        'limit':
            query_limit,
        'truncated':
            history['truncated'],
        'history_events':
            events,
        'gcs_summaries':
            summaries,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Correlate import version history with GCS summaries.')
    parser.add_argument('--mode', required=True, choices=_MODES)
    parser.add_argument('--absolute_import_name', required=True)
    parser.add_argument('--spanner_project', required=True)
    parser.add_argument('--spanner_instance', required=True)
    parser.add_argument('--spanner_database', required=True)
    parser.add_argument('--gcs_project', required=True)
    parser.add_argument('--gcs_bucket', required=True)
    parser.add_argument('--gcs_output_prefix', default='')
    parser.add_argument('--version')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--start_time')
    parser.add_argument('--end_time')
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    try:
        start_time = parse_rfc3339(args.start_time) if args.start_time else None
        end_time = parse_rfc3339(args.end_time) if args.end_time else None
        result = correlate_import_runs(args.mode,
                                       args.absolute_import_name,
                                       args.spanner_project,
                                       args.spanner_instance,
                                       args.spanner_database,
                                       args.gcs_project,
                                       args.gcs_bucket,
                                       gcs_output_prefix=args.gcs_output_prefix,
                                       version=args.version,
                                       limit=args.limit,
                                       start_time=start_time,
                                       end_time=end_time)
    except ImportRunCorrelationError as exc:
        print(json.dumps({'error': str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(3) from exc
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
