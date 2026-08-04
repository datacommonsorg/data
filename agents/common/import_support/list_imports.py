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

from dataclasses import dataclass
from difflib import SequenceMatcher
import json
from pathlib import Path
import sys
from typing import Any

from absl import app
from absl import flags

_FLAGS = flags.FLAGS

_MANIFEST_ROOTS = ('statvar_imports', 'scripts')
_MAX_LIMIT = 100
_MIN_FUZZY_QUERY_LENGTH = 3
_MIN_FUZZY_SIMILARITY = 0.6


def _define_flags() -> None:
    flags.DEFINE_string(
        'query', '',
        'Optional import_name query with case-insensitive and fuzzy matching.')
    flags.DEFINE_enum('autorefresh', 'any',
                      ('any', 'configured', 'not_configured'),
                      'Filter by repository-configured cron intent.')
    flags.DEFINE_integer('limit', 5, 'Maximum number of imports to return.')


class ImportCatalogError(ValueError):
    """Raised when the repository import catalog cannot be queried."""


@dataclass(frozen=True)
class ImportRecord:
    """Compact identity and refresh intent for one manifest import."""

    import_name: str
    manifest_path: str
    import_directory: str
    absolute_import_name: str
    cron_schedule: str | None


def find_repository_root(start: Path | None = None) -> Path:
    """Finds and validates the Data Commons data repository root."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if all((candidate / item).exists()
               for item in ('statvar_imports', 'scripts', 'import-automation',
                            'requirements_all.txt', 'run_tests.sh')):
            return candidate
    raise ImportCatalogError(
        'Run from the Data Commons data repository or one of its directories.')


def _manifest_paths(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    for root in _MANIFEST_ROOTS:
        paths.extend((repo_root / root).glob('**/manifest.json'))
    return sorted(path.resolve() for path in paths)


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise ImportCatalogError(f'Unable to parse {path}: {exc}') from exc
    if not isinstance(value, dict):
        raise ImportCatalogError(f'Manifest is not a JSON object: {path}')
    specifications = value.get('import_specifications')
    if not isinstance(specifications, list):
        raise ImportCatalogError(
            f'Manifest has no import_specifications list: {path}')
    return value


def _record_from_spec(repo_root: Path, manifest_path: Path, spec_index: int,
                      spec: dict[str, Any]) -> ImportRecord:
    import_name = spec.get('import_name')
    if not isinstance(import_name, str) or not import_name.strip():
        relative_manifest = manifest_path.relative_to(repo_root)
        raise ImportCatalogError(
            f'Empty import_name in {relative_manifest} specification {spec_index}'
        )
    import_directory = manifest_path.parent
    relative_directory = import_directory.relative_to(repo_root).as_posix()
    cron_schedule = spec.get('cron_schedule')
    # TODO: Keep this format aligned with import-automation's absolute import
    # name contract.
    return ImportRecord(
        import_name=import_name,
        manifest_path=manifest_path.relative_to(repo_root).as_posix(),
        import_directory=relative_directory,
        absolute_import_name=f'{relative_directory}:{import_name}',
        cron_schedule=cron_schedule if isinstance(cron_schedule, str) else None,
    )


def build_import_catalog(repo_root: Path) -> dict[str, list[ImportRecord]]:
    """Builds an in-memory catalog from the two approved manifest roots."""
    repo_root = repo_root.resolve()
    catalog: dict[str, list[ImportRecord]] = {}
    for manifest_path in _manifest_paths(repo_root):
        manifest = _load_manifest(manifest_path)
        for index, spec in enumerate(manifest['import_specifications']):
            if not isinstance(spec, dict):
                raise ImportCatalogError(
                    f'Invalid specification {index} in '
                    f'{manifest_path.relative_to(repo_root)}')
            record = _record_from_spec(repo_root, manifest_path, index, spec)
            catalog.setdefault(record.import_name, []).append(record)
    return catalog


def _has_configured_autorefresh(record: ImportRecord) -> bool:
    return bool(record.cron_schedule and record.cron_schedule.strip())


def _compact_record(record: ImportRecord) -> dict[str, Any]:
    return {
        'absolute_import_name': record.absolute_import_name,
        'configured_autorefresh': _has_configured_autorefresh(record),
        'cron_schedule': record.cron_schedule,
        'gcs_object_prefix': f'{record.import_directory}/{record.import_name}',
        'import_directory': record.import_directory,
        'import_name': record.import_name,
        'manifest_path': record.manifest_path,
    }


def _similarity(query: str, record: ImportRecord) -> float:
    return SequenceMatcher(None, query, record.import_name.casefold()).ratio()


def _rank_records(records: list[ImportRecord],
                  query: str) -> list[ImportRecord]:
    return sorted(records,
                  key=lambda record:
                  (-_similarity(query, record), record.import_name.casefold(),
                   record.import_name, record.manifest_path))


def _query_records(records: list[ImportRecord],
                   query: str) -> tuple[str, list[ImportRecord]]:
    stripped_query = query.strip()
    normalized_query = stripped_query.casefold()
    if not normalized_query:
        return 'all', records

    exact = [
        record for record in records if record.import_name == stripped_query
    ]
    if exact:
        return 'exact', exact

    case_insensitive_exact = [
        record for record in records
        if record.import_name.casefold() == normalized_query
    ]
    if case_insensitive_exact:
        return 'case_insensitive_exact', _rank_records(case_insensitive_exact,
                                                       normalized_query)

    prefix = [
        record for record in records
        if record.import_name.casefold().startswith(normalized_query)
    ]
    if prefix:
        return 'prefix', _rank_records(prefix, normalized_query)

    substring = [
        record for record in records
        if normalized_query in record.import_name.casefold()
    ]
    if substring:
        return 'substring', _rank_records(substring, normalized_query)

    if len(normalized_query) >= _MIN_FUZZY_QUERY_LENGTH:
        fuzzy = [
            record for record in records
            if _similarity(normalized_query, record) >= _MIN_FUZZY_SIMILARITY
        ]
        if fuzzy:
            return 'fuzzy', _rank_records(fuzzy, normalized_query)

    return 'none', []


def list_imports(catalog: dict[str, list[ImportRecord]],
                 query: str = '',
                 autorefresh: str = 'any',
                 limit: int = 5) -> dict[str, Any]:
    """Queries the manifest catalog and returns bounded deterministic JSON."""
    if limit < 1 or limit > _MAX_LIMIT:
        raise ImportCatalogError(f'limit must be between 1 and {_MAX_LIMIT}.')
    if autorefresh not in ('any', 'configured', 'not_configured'):
        raise ImportCatalogError(
            'autorefresh must be any, configured, or not_configured.')

    records: list[ImportRecord] = []
    for import_name, matches in catalog.items():
        if len(matches) != 1:
            locations = ', '.join(record.manifest_path for record in matches)
            raise ImportCatalogError(
                f'Import name {import_name!r} is not unique: {locations}')
        records.append(matches[0])

    records.sort(key=lambda record: (record.import_name.casefold(), record.
                                     import_name, record.manifest_path))
    match_strategy, query_matches = _query_records(records, query)
    matches = []
    for record in query_matches:
        configured = _has_configured_autorefresh(record)
        if autorefresh == 'configured' and not configured:
            continue
        if autorefresh == 'not_configured' and configured:
            continue
        matches.append(record)

    returned = matches[:limit]
    return {
        'filters': {
            'autorefresh': autorefresh,
            'query': query,
        },
        'limit': limit,
        'matched_import_count': len(matches),
        'match_strategy': match_strategy,
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
                              query=_FLAGS.query,
                              autorefresh=_FLAGS.autorefresh,
                              limit=_FLAGS.limit)
    except ImportCatalogError as exc:
        print(json.dumps({'error': str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == '__main__':
    _define_flags()
    app.run(main)
