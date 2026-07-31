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
"""Lists a bounded catalog of repository-configured imports."""

import json
import sys
from typing import Any

from absl import app
from absl import flags

from agents.common.import_support.resolve_import import build_import_catalog
from agents.common.import_support.resolve_import import find_repository_root
from agents.common.import_support.resolve_import import ImportRecord
from agents.common.import_support.resolve_import import ImportResolutionError

_FLAGS = flags.FlagValues()
_NAME_CONTAINS = flags.DEFINE_string(
    'name_contains',
    '',
    'Optional case-insensitive import_name substring.',
    flag_values=_FLAGS)
_AUTOREFRESH = flags.DEFINE_enum('autorefresh',
                                 'any', ('any', 'configured', 'not_configured'),
                                 'Filter by repository-configured cron intent.',
                                 flag_values=_FLAGS)
_LIMIT = flags.DEFINE_integer('limit',
                              100,
                              'Maximum number of imports to return.',
                              flag_values=_FLAGS)

_MAX_LIMIT = 100


def _has_configured_autorefresh(record: ImportRecord) -> bool:
    return bool(record.cron_schedule and record.cron_schedule.strip())


def _compact_record(record: ImportRecord) -> dict[str, Any]:
    return {
        'absolute_import_name': record.absolute_import_name,
        'configured_autorefresh': _has_configured_autorefresh(record),
        'cron_schedule': record.cron_schedule,
        'import_directory': record.import_directory,
        'import_name': record.import_name,
        'manifest_path': record.manifest_path,
    }


def list_imports(catalog: dict[str, list[ImportRecord]],
                 name_contains: str = '',
                 autorefresh: str = 'any',
                 limit: int = _MAX_LIMIT) -> dict[str, Any]:
    """Filters the manifest catalog and returns bounded deterministic JSON."""
    if limit < 1 or limit > _MAX_LIMIT:
        raise ImportResolutionError(
            f'limit must be between 1 and {_MAX_LIMIT}.')
    if autorefresh not in ('any', 'configured', 'not_configured'):
        raise ImportResolutionError(
            'autorefresh must be any, configured, or not_configured.')

    records: list[ImportRecord] = []
    for import_name, matches in catalog.items():
        if len(matches) != 1:
            locations = ', '.join(record.manifest_path for record in matches)
            raise ImportResolutionError(
                f'Import name {import_name!r} is not unique: {locations}')
        records.append(matches[0])

    records.sort(key=lambda record:
                 (record.import_name.casefold(), record.manifest_path))
    name_filter = name_contains.casefold()
    matches = []
    for record in records:
        configured = _has_configured_autorefresh(record)
        if name_filter not in record.import_name.casefold():
            continue
        if autorefresh == 'configured' and not configured:
            continue
        if autorefresh == 'not_configured' and configured:
            continue
        matches.append(record)

    returned = matches[:limit]
    return {
        'filters': {
            'autorefresh': autorefresh,
            'name_contains': name_contains,
        },
        'limit': limit,
        'matched_import_count': len(matches),
        'mode': 'repository_catalog',
        'result_truncated': len(matches) > limit,
        'results': [_compact_record(record) for record in returned],
        'returned_import_count': len(returned),
        'scanned_import_count': len(records),
    }


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError('Unexpected positional arguments.')
    try:
        output = list_imports(build_import_catalog(find_repository_root()),
                              name_contains=_NAME_CONTAINS.value,
                              autorefresh=_AUTOREFRESH.value,
                              limit=_LIMIT.value)
    except ImportResolutionError as exc:
        print(json.dumps({'error': str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(output, indent=2, sort_keys=True))


def _parse_flags(argv: list[str]) -> list[str]:
    remaining = flags.FLAGS(argv, known_only=True)
    return _FLAGS(remaining)


if __name__ == '__main__':
    app.run(main, flags_parser=_parse_flags)
