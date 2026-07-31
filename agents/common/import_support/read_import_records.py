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
"""Runs one focused, parameterized, read-only import query in Spanner."""

import argparse
from datetime import datetime
import json
import sys
from typing import Any

from google.cloud import spanner

_MAX_LIMIT = 100
_COLUMNS = {
    'current':
        ('ImportName', 'LatestVersion', 'GraphPath', 'State', 'JobId',
         'WorkflowId', 'ExecutionTime', 'DataVolume', 'DataImportTimestamp',
         'StatusUpdateTimestamp', 'NextRefreshTimestamp'),
    'version_history':
        ('ImportName', 'Version', 'UpdateTimestamp', 'WorkflowExecutionID',
         'Status', 'ExecutionTime', 'NodeCount', 'EdgeCount',
         'ObservationCount', 'TimeSeriesCount', 'Comment'),
    'ingestion_history':
        ('WorkflowExecutionID', 'CreationTimestamp', 'CompletionTimestamp',
         'IngestionFailure', 'Status', 'Stage', 'DataflowJobID',
         'IngestedImports', 'ExecutionTime', 'NodeCount', 'EdgeCount',
         'ObservationCount', 'TimeSeriesCount'),
}


class SpannerReadError(RuntimeError):
    """Raised when a focused Spanner read cannot be completed."""


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


def _query(query_name: str,
           limit: int) -> tuple[str, dict[str, Any], dict[str, Any]]:
    columns = ', '.join(_COLUMNS[query_name])
    params: dict[str, Any] = {}
    param_types: dict[str, Any] = {}
    if query_name == 'current':
        return (f'SELECT {columns} FROM ImportStatus '
                'WHERE ImportName = @import_name', params, param_types)
    params['limit'] = limit + 1
    param_types['limit'] = spanner.param_types.INT64
    if query_name == 'version_history':
        return (f'SELECT {columns} FROM ImportVersionHistory '
                'WHERE ImportName = @import_name '
                'ORDER BY UpdateTimestamp DESC LIMIT @limit', params,
                param_types)
    return (f'SELECT {columns} FROM IngestionHistory '
            'WHERE @import_name IN UNNEST(IngestedImports) '
            'ORDER BY CreationTimestamp DESC LIMIT @limit', params, param_types)


def read_import_records(project: str,
                        instance: str,
                        database: str,
                        import_name: str,
                        query_name: str,
                        limit: int = 10,
                        client: Any | None = None) -> dict[str, Any]:
    """Executes exactly one allowlisted SELECT with bound parameters."""
    if query_name not in _COLUMNS:
        raise SpannerReadError(f'Unsupported query: {query_name}')
    if limit < 1 or limit > _MAX_LIMIT:
        raise SpannerReadError(f'limit must be between 1 and {_MAX_LIMIT}.')

    sql, extra_params, extra_types = _query(query_name, limit)
    params = {'import_name': import_name, **extra_params}
    param_types = {
        'import_name': spanner.param_types.STRING,
        **extra_types,
    }
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
        error = SpannerReadError(f'Unable to read {query_name}: {exc}')
        error.add_note(
            f'Database: projects/{project}/instances/{instance}/databases/{database}'
        )
        raise error from exc

    result_limit = 1 if query_name == 'current' else limit
    rows = [
        dict(zip(_COLUMNS[query_name], _serialize(tuple(row))))
        for row in raw_rows[:result_limit]
    ]
    return {
        'database_resource':
            f'projects/{project}/instances/{instance}/databases/{database}',
        'import_name':
            import_name,
        'limit':
            result_limit,
        'query':
            query_name,
        'rows':
            rows,
        'truncated':
            query_name != 'current' and len(raw_rows) > limit,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Run one bounded read-only import query in Spanner.')
    parser.add_argument('--project', required=True)
    parser.add_argument('--instance', required=True)
    parser.add_argument('--database', required=True)
    parser.add_argument('--import_name', required=True)
    parser.add_argument('--query', required=True, choices=tuple(_COLUMNS))
    parser.add_argument('--limit', type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    try:
        result = read_import_records(args.project,
                                     args.instance,
                                     args.database,
                                     args.import_name,
                                     args.query,
                                     limit=args.limit)
    except SpannerReadError as exc:
        print(json.dumps({'error': str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(3) from exc
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
