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
"""Resolves a manifest import name to repository code and configuration."""

from dataclasses import asdict
from dataclasses import dataclass
import json
from pathlib import Path
import shlex
import sys
from typing import Any

from absl import app
from absl import flags

_FLAGS = flags.FlagValues()
_IMPORT_NAME = flags.DEFINE_string('import_name',
                                   None,
                                   'Exact manifest import_name to resolve.',
                                   flag_values=_FLAGS)
_MANIFEST_PATH = flags.DEFINE_string(
    'manifest_path',
    '',
    'Optional repository-relative manifest path for this request.',
    flag_values=_FLAGS)

MANIFEST_ROOTS = ('statvar_imports', 'scripts')


class ImportResolutionError(ValueError):
    """Raised when an import cannot be resolved unambiguously."""


@dataclass(frozen=True)
class ImportRecord:
    """A canonical manifest import specification."""

    import_name: str
    manifest_path: str
    import_directory: str
    absolute_import_name: str
    spec_index: int
    cron_schedule: str | None
    scripts: tuple[str, ...]
    source_files: tuple[str, ...]
    provenance_url: str | None
    provenance_description: str | None
    import_inputs: tuple[dict[str, str], ...]
    validation_config_file: str | None
    user_script_timeout: float | None
    resource_limits: dict[str, Any]
    config_override_keys: tuple[str, ...]
    source_paths: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result['resolution_source'] = 'manifest'
        return result


def find_repository_root(start: Path | None = None) -> Path:
    """Finds and validates the Data Commons data repository root."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if all((candidate / item).exists()
               for item in ('statvar_imports', 'scripts', 'import-automation',
                            'requirements_all.txt', 'run_tests.sh')):
            return candidate
    raise ImportResolutionError(
        'Run from the Data Commons data repository or one of its directories.')


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _validate_manifest_path(repo_root: Path, manifest_path: Path) -> Path:
    resolved = manifest_path
    if not resolved.is_absolute():
        resolved = repo_root / resolved
    resolved = resolved.resolve()
    if resolved.name != 'manifest.json':
        raise ImportResolutionError(
            f'Explicit manifest must be named manifest.json: {manifest_path}')
    if not any(
            _is_relative_to(resolved, (repo_root / root).resolve())
            for root in MANIFEST_ROOTS):
        raise ImportResolutionError(
            'Explicit manifest must be under statvar_imports/ or scripts/.')
    if not resolved.is_file():
        raise ImportResolutionError(f'Manifest does not exist: {manifest_path}')
    return resolved


def _manifest_paths(repo_root: Path,
                    explicit_manifest: Path | None = None) -> list[Path]:
    if explicit_manifest:
        return [_validate_manifest_path(repo_root, explicit_manifest)]
    paths: list[Path] = []
    for root in MANIFEST_ROOTS:
        paths.extend((repo_root / root).glob('**/manifest.json'))
    return sorted(path.resolve() for path in paths)


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise ImportResolutionError(f'Unable to parse {path}: {exc}') from exc
    if not isinstance(value, dict):
        raise ImportResolutionError(f'Manifest is not a JSON object: {path}')
    specifications = value.get('import_specifications')
    if not isinstance(specifications, list):
        raise ImportResolutionError(
            f'Manifest has no import_specifications list: {path}')
    return value


def _existing_repo_path(repo_root: Path, import_directory: Path,
                        raw_path: str) -> str | None:
    if not raw_path or '://' in raw_path or '*' in raw_path:
        return None
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = import_directory / candidate
    candidate = candidate.resolve()
    if not _is_relative_to(candidate, repo_root) or not candidate.exists():
        return None
    return candidate.relative_to(repo_root).as_posix()


def _source_paths(repo_root: Path, import_directory: Path,
                  spec: dict[str, Any]) -> tuple[str, ...]:
    paths = {
        import_directory.relative_to(repo_root).as_posix() + '/manifest.json'
    }
    raw_candidates: list[str] = []
    for command in spec.get('scripts', []):
        if not isinstance(command, str):
            continue
        try:
            tokens = shlex.split(command)
        except ValueError:
            tokens = command.split()
        for token in tokens:
            if token.startswith('--') and '=' in token:
                raw_candidates.append(token.split('=', 1)[1])
            elif not token.startswith('-'):
                raw_candidates.append(token)
    for import_input in spec.get('import_inputs', []):
        if isinstance(import_input, dict):
            raw_candidates.extend(value for value in import_input.values()
                                  if isinstance(value, str))
    for field in ('validation_config_file', 'requirements_file'):
        value = spec.get(field)
        if isinstance(value, str):
            raw_candidates.append(value)
    for raw_path in raw_candidates:
        existing = _existing_repo_path(repo_root, import_directory, raw_path)
        if existing:
            paths.add(existing)
    return tuple(sorted(paths))


def _record_from_spec(repo_root: Path, manifest_path: Path, spec_index: int,
                      spec: dict[str, Any]) -> ImportRecord:
    import_name = spec.get('import_name')
    if not isinstance(import_name, str) or not import_name.strip():
        relative_manifest = manifest_path.relative_to(repo_root)
        raise ImportResolutionError(
            f'Empty import_name in {relative_manifest} specification {spec_index}'
        )
    import_directory = manifest_path.parent
    relative_directory = import_directory.relative_to(repo_root).as_posix()
    scripts = spec.get('scripts', [])
    source_files = spec.get('source_files', [])
    import_inputs = spec.get('import_inputs', [])
    resource_limits = spec.get('resource_limits', {})
    config_override = spec.get('config_override', {})
    return ImportRecord(
        import_name=import_name,
        manifest_path=manifest_path.relative_to(repo_root).as_posix(),
        import_directory=relative_directory,
        absolute_import_name=f'{relative_directory}:{import_name}',
        spec_index=spec_index,
        cron_schedule=spec.get('cron_schedule'),
        scripts=tuple(value for value in scripts if isinstance(value, str)),
        source_files=tuple(
            value for value in source_files if isinstance(value, str)),
        provenance_url=(spec.get('provenance_url') if isinstance(
            spec.get('provenance_url'), str) else None),
        provenance_description=(spec.get('provenance_description') if
                                isinstance(spec.get('provenance_description'),
                                           str) else None),
        import_inputs=tuple(
            value for value in import_inputs if isinstance(value, dict)),
        validation_config_file=spec.get('validation_config_file'),
        user_script_timeout=spec.get('user_script_timeout'),
        resource_limits=resource_limits
        if isinstance(resource_limits, dict) else {},
        config_override_keys=tuple(sorted(config_override.keys()))
        if isinstance(config_override, dict) else (),
        source_paths=_source_paths(repo_root, import_directory, spec),
    )


def build_import_catalog(
        repo_root: Path,
        explicit_manifest: Path | None = None) -> dict[str, list[ImportRecord]]:
    """Builds an in-memory catalog from the two approved manifest roots."""
    catalog: dict[str, list[ImportRecord]] = {}
    for manifest_path in _manifest_paths(repo_root, explicit_manifest):
        manifest = _load_manifest(manifest_path)
        for index, spec in enumerate(manifest['import_specifications']):
            if not isinstance(spec, dict):
                raise ImportResolutionError(
                    f'Invalid specification {index} in '
                    f'{manifest_path.relative_to(repo_root)}')
            record = _record_from_spec(repo_root, manifest_path, index, spec)
            catalog.setdefault(record.import_name, []).append(record)
    return catalog


def resolve_import(catalog: dict[str, list[ImportRecord]],
                   import_name: str) -> ImportRecord:
    """Returns the unique canonical record for an exact import name."""
    matches = catalog.get(import_name, [])
    if not matches:
        raise ImportResolutionError(f'No import named {import_name!r} found.')
    if len(matches) != 1:
        locations = ', '.join(record.manifest_path for record in matches)
        raise ImportResolutionError(
            f'Import name {import_name!r} is not unique: {locations}')
    return matches[0]


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError('Unexpected positional arguments.')
    if not _IMPORT_NAME.value:
        raise app.UsageError('--import_name is required.')
    try:
        repo_root = find_repository_root()
        explicit_manifest = Path(
            _MANIFEST_PATH.value) if _MANIFEST_PATH.value else None
        catalog = build_import_catalog(repo_root, explicit_manifest)
        record = resolve_import(catalog, _IMPORT_NAME.value)
    except ImportResolutionError as exc:
        print(json.dumps({'error': str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(record.to_dict(), indent=2, sort_keys=True))


def _parse_flags(argv: list[str]) -> list[str]:
    remaining = flags.FLAGS(argv, known_only=True)
    return _FLAGS(remaining)


if __name__ == '__main__':
    app.run(main, flags_parser=_parse_flags)
