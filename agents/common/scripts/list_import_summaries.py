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
"""Provides a bounded set of finalized import summaries from GCS."""

from datetime import date
import json
import posixpath
import re
import sys
from typing import Any

from absl import app
from absl import flags
from google.api_core import exceptions
from google.auth import exceptions as auth_exceptions
from google.cloud import storage

_FLAGS = flags.FLAGS

_IMPORT_NAME_PATTERN = re.compile(
    r'^(?P<directory>[A-Za-z0-9_/-]+):(?P<name>[A-Za-z0-9_-]+)$')
_VERSION_PATTERN = re.compile(
    r'^(?P<year>\d{4})_(?P<month>\d{2})_(?P<day>\d{2})T'
    r'\d{2}_\d{2}_\d{2}(?:_\d{1,6})?_\d{2}_\d{2}$')
_SUMMARY_FILENAME = 'import_summary.json'
_MAX_RESULT_LIMIT = 5
_SCAN_LIMIT = 100


def _define_flags() -> None:
    flags.DEFINE_string('absolute_import_name', None,
                        'Absolute Data Commons import identity.')
    flags.mark_flag_as_required('absolute_import_name')
    flags.DEFINE_string('gcs_project', None,
                        'Google Cloud project containing run summaries.')
    flags.mark_flag_as_required('gcs_project')
    flags.DEFINE_string('gcs_bucket', None,
                        'GCS bucket containing import artifacts.')
    flags.mark_flag_as_required('gcs_bucket')
    flags.DEFINE_integer('limit', 5,
                         'Maximum number of summaries to return (1-5).')


class ImportSummaryListError(ValueError):
    """Raised when import summaries cannot be listed safely."""


def normalize_import_name(absolute_import_name: str) -> dict[str, str]:
    """Validates an absolute import name and derives its exact GCS prefix."""
    match = _IMPORT_NAME_PATTERN.fullmatch(absolute_import_name)
    if not match:
        raise ImportSummaryListError(
            'absolute_import_name must be <manifest-directory>:<import-name>.')

    directory = match.group('directory').strip('/')
    if not directory or '//' in directory:
        raise ImportSummaryListError(
            'Manifest directory must contain non-empty path components.')
    simple_name = match.group('name')
    prefix = posixpath.join(directory, simple_name)
    return {
        'absolute_import_name': absolute_import_name,
        'simple_import_name': simple_name,
        'gcs_prefix': f'{prefix}/',
    }


def _version_date(version: str) -> str | None:
    match = _VERSION_PATTERN.fullmatch(version)
    if not match:
        return None
    try:
        parsed = date(int(match.group('year')), int(match.group('month')),
                      int(match.group('day')))
    except ValueError:
        return None
    return parsed.isoformat()


def _version_from_object_name(object_name: str, prefix: str) -> str | None:
    if not object_name.startswith(prefix):
        return None
    relative_name = object_name[len(prefix):]
    parts = relative_name.split('/')
    if len(parts) != 2 or parts[1] != _SUMMARY_FILENAME:
        return None
    return parts[0]


def _read_batch_job_id(
        blob: Any, version: str,
        simple_import_name: str) -> tuple[str | None, dict[str, str] | None]:
    try:
        summary = json.loads(blob.download_as_text())
    except exceptions.NotFound:
        return None, {'code': 'summary_missing', 'version': version}
    except exceptions.Forbidden:
        return None, {'code': 'summary_permission_denied', 'version': version}
    except auth_exceptions.DefaultCredentialsError:
        return None, {'code': 'gcs_credentials_unavailable', 'version': version}
    except exceptions.GoogleAPICallError:
        return None, {'code': 'summary_read_failed', 'version': version}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, {'code': 'invalid_summary_json', 'version': version}

    if not isinstance(summary, dict):
        return None, {'code': 'invalid_summary_json', 'version': version}
    if summary.get('import_name') != simple_import_name:
        return None, {'code': 'summary_import_mismatch', 'version': version}
    job_id = summary.get('job_id')
    if not isinstance(job_id, str) or not job_id.strip():
        return None, {'code': 'summary_job_id_missing', 'version': version}
    return job_id, None


def list_import_summaries(absolute_import_name: str,
                          gcs_project: str,
                          gcs_bucket: str,
                          limit: int = 5,
                          client: Any | None = None) -> dict[str, Any]:
    """Returns recent timestamp-named summaries without scanning unbounded data."""
    if limit < 1 or limit > _MAX_RESULT_LIMIT:
        raise ImportSummaryListError(
            f'limit must be between 1 and {_MAX_RESULT_LIMIT}.')
    identity = normalize_import_name(absolute_import_name)
    prefix = identity['gcs_prefix']
    match_glob = f'{prefix}*/{_SUMMARY_FILENAME}'

    try:
        storage_client = client or storage.Client(project=gcs_project)
        blobs = list(
            storage_client.list_blobs(gcs_bucket,
                                      prefix=prefix,
                                      match_glob=match_glob,
                                      max_results=_SCAN_LIMIT + 1,
                                      page_size=_SCAN_LIMIT + 1,
                                      fields='items(name),nextPageToken'))
    except exceptions.Forbidden as exc:
        raise ImportSummaryListError(
            'Permission denied while listing import summaries.') from exc
    except auth_exceptions.DefaultCredentialsError as exc:
        raise ImportSummaryListError(
            'Application Default Credentials are unavailable.') from exc
    except exceptions.GoogleAPICallError as exc:
        raise ImportSummaryListError(
            f'Unable to list import summaries: {type(exc).__name__}.') from exc

    output: dict[str, Any] = {
        'absolute_import_name': absolute_import_name,
        'limit': limit,
        'scan_limit': _SCAN_LIMIT,
        'scanned_summary_count': len(blobs),
        'scan_truncated': len(blobs) > _SCAN_LIMIT,
        'skipped_non_timestamp_count': 0,
        'returned_summary_count': 0,
        'results': [],
        'issues': [],
    }
    if output['scan_truncated']:
        output['issues'].append({'code': 'summary_scan_limit_exceeded'})
        return output

    candidates: list[tuple[str, str, Any]] = []
    for blob in blobs:
        version = _version_from_object_name(blob.name, prefix)
        version_date = _version_date(version) if version else None
        if version is None or version_date is None:
            output['skipped_non_timestamp_count'] += 1
            continue
        candidates.append((version, version_date, blob))

    candidates.sort(key=lambda item: item[0], reverse=True)
    for version, version_date, blob in candidates[:limit]:
        batch_job_id, issue = _read_batch_job_id(blob, version,
                                                 identity['simple_import_name'])
        gcs_version_uri = (
            f'gs://{gcs_bucket}/{posixpath.join(prefix, version)}')
        output['results'].append({
            'version': version,
            'date': version_date,
            'gcs_version_uri': gcs_version_uri,
            'batch_job_id': batch_job_id,
        })
        if issue:
            output['issues'].append(issue)
    output['returned_summary_count'] = len(output['results'])
    return output


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError('Unexpected positional arguments.')
    try:
        output = list_import_summaries(
            absolute_import_name=_FLAGS.absolute_import_name,
            gcs_project=_FLAGS.gcs_project,
            gcs_bucket=_FLAGS.gcs_bucket,
            limit=_FLAGS.limit)
    except ImportSummaryListError as exc:
        print(json.dumps({'error': str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == '__main__':
    _define_flags()
    app.run(main)
