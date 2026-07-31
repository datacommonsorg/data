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
"""Builds bounded, read-only snapshots of Data Commons imports."""

from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from pathlib import Path
import json
import logging
import sys
import time
from typing import Any

from absl import app
from absl import flags
from jsonschema import Draft202012Validator
from jsonschema import FormatChecker

from agents.common.import_support.collect_provenance import collect_runtime_provenance
from agents.common.import_support.command_runner import CommandError
from agents.common.import_support.command_runner import ReadOnlyCommandRunner
from agents.common.import_support.list_import_runs import filter_import_runs
from agents.common.import_support.list_import_runs import format_rfc3339
from agents.common.import_support.list_import_runs import list_workflow_execution_records
from agents.common.import_support.list_import_runs import parse_rfc3339
from agents.common.import_support.list_import_runs import WorkflowExecutionError
from agents.common.import_support.resolve_import import build_import_catalog
from agents.common.import_support.resolve_import import find_repository_root
from agents.common.import_support.resolve_import import ImportRecord
from agents.common.import_support.resolve_import import ImportResolutionError
from agents.common.import_support.resolve_import import resolve_import
from agents.common.import_support.snapshot_collectors import batch_task_start_time
from agents.common.import_support.snapshot_collectors import batch_link
from agents.common.import_support.snapshot_collectors import cloud_run_link
from agents.common.import_support.snapshot_collectors import collect_batch_for_run
from agents.common.import_support.snapshot_collectors import collect_batch_logs
from agents.common.import_support.snapshot_collectors import collect_gcs_evidence
from agents.common.import_support.snapshot_collectors import composite_status
from agents.common.import_support.snapshot_collectors import describe_ingestion_helper
from agents.common.import_support.snapshot_collectors import describe_scheduler
from agents.common.import_support.snapshot_collectors import describe_workflow
from agents.common.import_support.snapshot_collectors import list_schedulers
from agents.common.import_support.snapshot_collectors import load_executor_defaults
from agents.common.import_support.snapshot_collectors import normalize_pipeline_status
from agents.common.import_support.snapshot_collectors import now_utc
from agents.common.import_support.snapshot_collectors import parse_workflow_target
from agents.common.import_support.snapshot_collectors import read_spanner_records
from agents.common.import_support.snapshot_collectors import scheduler_link
from agents.common.import_support.snapshot_collectors import gcs_link
from agents.common.import_support.snapshot_collectors import spanner_link
from agents.common.import_support.snapshot_collectors import technical_state
from agents.common.import_support.snapshot_collectors import unavailable_batch_evidence
from agents.common.import_support.snapshot_collectors import workflow_link

_FLAGS = flags.FlagValues()


def _define_string(*args, **kwargs):
    return flags.DEFINE_string(*args, flag_values=_FLAGS, **kwargs)


def _define_integer(*args, **kwargs):
    return flags.DEFINE_integer(*args, flag_values=_FLAGS, **kwargs)


def _define_enum(*args, **kwargs):
    return flags.DEFINE_enum(*args, flag_values=_FLAGS, **kwargs)


def _define_boolean(*args, **kwargs):
    return flags.DEFINE_boolean(*args, flag_values=_FLAGS, **kwargs)


_MODE = _define_enum('mode', 'single_import', ['single_import', 'fleet'],
                     'Snapshot mode.')
_IMPORT_NAME = _define_string('import_name', '', 'Exact manifest import name.')
_MANIFEST_PATH = _define_string('manifest_path', '',
                                'Optional repository-relative manifest path.')
_ENVIRONMENT = _define_string('environment', 'prod',
                              'Environment name; production is prod.')
_SCHEDULER_PROJECT = _define_string('scheduler_project', '',
                                    'Cloud Scheduler project.')
_SCHEDULER_LOCATION = _define_string('scheduler_location', '',
                                     'Cloud Scheduler location.')
_START_TIME = _define_string('start_time', '',
                             'Inclusive RFC3339 UTC start time.')
_END_TIME = _define_string('end_time', '', 'Inclusive RFC3339 UTC end time.')
_RUN_LIMIT = _define_integer('run_limit', 10,
                             'Maximum runs returned per import.')
_SCAN_LIMIT = _define_integer('scan_limit', 5000,
                              'Maximum Workflow executions inspected.')
_IMPORT_LIMIT = _define_integer('import_limit', 100,
                                'Maximum fleet imports returned.')
_STATUS = _define_enum(
    'status', '', ['', 'failed', 'running', 'succeeded', 'skipped', 'unknown'],
    'Optional fleet composite-status filter.')
_IMPORT_NAME_PATTERN = _define_string('import_name_pattern', '',
                                      'Case-insensitive fleet name substring.')
_CONSECUTIVE_FAILURES = _define_integer(
    'consecutive_failures', 0,
    'Minimum consecutive terminal failures in fleet mode.')
_LOG_LIMIT = _define_integer('log_limit', 200,
                             'Maximum Batch log entries per run.')
_OBJECT_LIMIT = _define_integer('object_limit', 1000,
                                'Maximum GCS objects per import.')
_GCS_PROJECT = _define_string('gcs_project', '',
                              'Optional expected GCS project.')
_GCS_BUCKET = _define_string('gcs_bucket', '',
                             'Optional expected output bucket.')
_HELPER_PROJECT = _define_string(
    'helper_project', '', 'Optional ingestion-helper Cloud Run project.')
_HELPER_LOCATION = _define_string(
    'helper_location', '', 'Optional ingestion-helper Cloud Run region.')
_HELPER_SERVICE = _define_string(
    'helper_service', '', 'Expected ingestion-helper Cloud Run service name.')
_SPANNER_PROJECT = _define_string('spanner_project', '',
                                  'Optional expected Spanner project.')
_SPANNER_INSTANCE = _define_string('spanner_instance', '',
                                   'Optional expected Spanner instance.')
_SPANNER_DATABASE = _define_string('spanner_database', '',
                                   'Optional expected Spanner database.')
_HISTORY_LIMIT = _define_integer('history_limit', 50,
                                 'Maximum Spanner rows per history table.')
_BUILD_PROJECT = _define_string('build_project', '',
                                'Optional Cloud Build project.')
_BUILD_REGION = _define_string('build_region', 'global', 'Cloud Build region.')
_VERBOSE = _define_boolean(
    'verbose', False,
    'Print safe collection progress and operation timings to stderr.')
_PREVIEW_INFRASTRUCTURE = _define_boolean(
    'preview_infrastructure', False,
    'Print local infrastructure candidates without cloud access, then exit.')

_MAX_RUN_LIMIT = 50
_MAX_IMPORT_LIMIT = 200
_MAX_LOG_LIMIT = 500
_MAX_OBJECT_LIMIT = 1000
_MAX_HISTORY_LIMIT = 100
_LOGGER = logging.getLogger(__name__)
_HELP_FLAGS = frozenset(('-?', '--help', '--helpfull', '--helpshort'))


class SnapshotError(ValueError):
    """Raised when snapshot inputs or evidence are unsafe or ambiguous."""


@dataclass(frozen=True)
class SnapshotOptions:
    """Validated snapshot collection inputs."""

    mode: str
    import_name: str
    manifest_path: str
    environment: str
    scheduler_project: str
    scheduler_location: str
    start_time: datetime
    end_time: datetime
    run_limit: int
    scan_limit: int
    import_limit: int
    status: str
    import_name_pattern: str
    consecutive_failures: int
    log_limit: int
    object_limit: int
    gcs_project: str
    gcs_bucket: str
    helper_project: str
    helper_location: str
    helper_service: str
    spanner_project: str
    spanner_instance: str
    spanner_database: str
    history_limit: int
    build_project: str
    build_region: str
    verbose: bool


def _evidence(source_kind: str, source: str, finding: str) -> dict[str, Any]:
    return {
        'source_kind': source_kind,
        'source': source,
        'finding': finding,
        'observed_at': format_rfc3339(now_utc()),
    }


def _validate_limit(name: str, value: int, maximum: int) -> None:
    if value < 1 or value > maximum:
        raise SnapshotError(f'{name} must be between 1 and {maximum}.')


def _build_options() -> SnapshotOptions:
    now = now_utc()
    start_default = now - timedelta(
        days=90 if _MODE.value == 'single_import' else 1)
    start = parse_rfc3339(
        _START_TIME.value) if _START_TIME.value else start_default
    end = parse_rfc3339(_END_TIME.value) if _END_TIME.value else now
    if start >= end:
        raise SnapshotError('start_time must be before end_time.')
    _validate_limit('run_limit', _RUN_LIMIT.value, _MAX_RUN_LIMIT)
    _validate_limit('scan_limit', _SCAN_LIMIT.value, 5000)
    _validate_limit('import_limit', _IMPORT_LIMIT.value, _MAX_IMPORT_LIMIT)
    _validate_limit('log_limit', _LOG_LIMIT.value, _MAX_LOG_LIMIT)
    _validate_limit('object_limit', _OBJECT_LIMIT.value, _MAX_OBJECT_LIMIT)
    _validate_limit('history_limit', _HISTORY_LIMIT.value, _MAX_HISTORY_LIMIT)
    if _CONSECUTIVE_FAILURES.value < 0:
        raise SnapshotError('consecutive_failures cannot be negative.')
    if _MODE.value == 'single_import' and not _IMPORT_NAME.value:
        raise SnapshotError('--import_name is required in single_import mode.')
    return SnapshotOptions(
        mode=_MODE.value,
        import_name=_IMPORT_NAME.value,
        manifest_path=_MANIFEST_PATH.value,
        environment=_ENVIRONMENT.value,
        scheduler_project=_SCHEDULER_PROJECT.value,
        scheduler_location=_SCHEDULER_LOCATION.value,
        start_time=start,
        end_time=end,
        run_limit=_RUN_LIMIT.value,
        scan_limit=_SCAN_LIMIT.value,
        import_limit=_IMPORT_LIMIT.value,
        status=_STATUS.value,
        import_name_pattern=_IMPORT_NAME_PATTERN.value,
        consecutive_failures=_CONSECUTIVE_FAILURES.value,
        log_limit=_LOG_LIMIT.value,
        object_limit=_OBJECT_LIMIT.value,
        gcs_project=_GCS_PROJECT.value,
        gcs_bucket=_GCS_BUCKET.value,
        helper_project=_HELPER_PROJECT.value,
        helper_location=_HELPER_LOCATION.value,
        helper_service=_HELPER_SERVICE.value,
        spanner_project=_SPANNER_PROJECT.value,
        spanner_instance=_SPANNER_INSTANCE.value,
        spanner_database=_SPANNER_DATABASE.value,
        history_limit=_HISTORY_LIMIT.value,
        build_project=_BUILD_PROJECT.value,
        build_region=_BUILD_REGION.value,
        verbose=_VERBOSE.value,
    )


def _progress(options: SnapshotOptions, message: str) -> None:
    if options.verbose:
        _LOGGER.info(message)


def _selected_value(explicit: str, configured: str) -> dict[str, Any]:
    value = explicit or configured
    source = ('user_provided' if explicit else
              'repo_configured' if configured else 'unresolved')
    return {
        'value':
            value or None,
        'source':
            source,
        'repository_candidate':
            configured or None,
        'overrides_repository_candidate':
            bool(explicit and configured and explicit != configured),
    }


def _helper_service_candidate(repo_root: Path) -> str:
    helper_script = repo_root / (
        'import-automation/executor/scripts/update_import_version.sh')
    if helper_script.is_file() and 'ingestion-helper-service' in (
            helper_script.read_text(encoding='utf-8')):
        return 'ingestion-helper-service'
    return ''


def build_infrastructure_preview(repo_root: Path,
                                 options: SnapshotOptions) -> dict[str, Any]:
    """Returns repository-derived candidates without accessing the cloud."""
    defaults = load_executor_defaults(repo_root)
    use_defaults = options.environment == 'prod'
    configured_project = str(defaults.get('gcp_project_id') or
                             '') if use_defaults else ''
    configured_location = str(defaults.get('scheduler_location') or
                              '') if use_defaults else ''
    scheduler_project = _selected_value(options.scheduler_project,
                                        configured_project)
    scheduler_location = _selected_value(options.scheduler_location,
                                         configured_location)
    project = str(scheduler_project['value'] or '')
    location = str(scheduler_location['value'] or '')

    configured_workflow = str(defaults.get('cloud_workflow_id') or
                              '') if use_defaults else ''
    workflow_resource = ''
    if project and location and configured_workflow:
        workflow_resource = (
            f'projects/{project}/locations/{location}/workflows/'
            f'{configured_workflow}')

    configured_gcs_project = str(defaults.get('gcs_project_id') or
                                 '') if use_defaults else ''
    configured_gcs_bucket = str(defaults.get('storage_prod_bucket_name') or
                                '') if use_defaults else ''
    gcs_project = _selected_value(options.gcs_project, configured_gcs_project)
    gcs_bucket = _selected_value(options.gcs_bucket, configured_gcs_bucket)

    helper_project = _selected_value(options.helper_project, '')
    if not options.helper_project and project:
        helper_project['value'] = project
        helper_project['source'] = 'derived_from_scheduler'
    helper_location = _selected_value(options.helper_location, '')
    if not options.helper_location and location:
        helper_location['value'] = location
        helper_location['source'] = 'derived_from_scheduler'
    configured_helper = _helper_service_candidate(
        repo_root) if use_defaults else ''
    helper_service = _selected_value(options.helper_service, configured_helper)

    spanner_values = {
        'project': options.spanner_project or None,
        'instance': options.spanner_instance or None,
        'database': options.spanner_database or None,
    }
    supplied_spanner = [value for value in spanner_values.values() if value]
    if len(supplied_spanner) == len(spanner_values):
        spanner_status = 'selected'
        spanner_source = 'user_provided'
    elif supplied_spanner:
        spanner_status = 'incomplete'
        spanner_source = 'user_provided'
    else:
        spanner_status = 'derive_from_live_ingestion_helper'
        spanner_source = 'live_observed_required'

    missing_scheduler = [
        name for name, value in (
            ('scheduler_project', project),
            ('scheduler_location', location),
        ) if not value
    ]
    missing_spanner = ([
        f'spanner_{name}' for name, value in spanner_values.items() if not value
    ] if spanner_status == 'incomplete' else [])
    unresolved = missing_scheduler + missing_spanner
    blocked_reads = []
    if unresolved:
        blocked_reads.append('all_cloud_reads')
    if spanner_status == 'incomplete':
        blocked_reads.append('spanner')
    warnings = []
    for name, selected in (('scheduler_project', scheduler_project),
                           ('scheduler_location',
                            scheduler_location), ('gcs_project', gcs_project),
                           ('gcs_bucket', gcs_bucket), ('helper_project',
                                                        helper_project),
                           ('helper_location', helper_location),
                           ('helper_service', helper_service)):
        if selected['overrides_repository_candidate']:
            warnings.append(
                f'User-provided {name} replaces repository candidate '
                f'{selected["repository_candidate"]}.')

    return {
        'cloud_access_performed': False,
        'ready_for_cloud': not unresolved,
        'environment': {
            'name':
                options.environment,
            'source':
                'default' if options.environment == 'prod' else 'user_provided',
        },
        'query': {
            'mode': options.mode,
            'import_name': options.import_name or None,
            'start_time': format_rfc3339(options.start_time),
            'end_time': format_rfc3339(options.end_time),
            'limits': {
                'run_limit': options.run_limit,
                'scan_limit': options.scan_limit,
                'import_limit': options.import_limit,
                'log_limit': options.log_limit,
                'object_limit': options.object_limit,
                'history_limit': options.history_limit,
            },
        },
        'resources': {
            'scheduler': {
                'project': scheduler_project,
                'location': scheduler_location,
            },
            'workflow': {
                'resource_candidate':
                    workflow_resource or None,
                'source':
                    'repo_configured'
                    if workflow_resource else 'resolve_from_live_scheduler',
            },
            'gcs': {
                'project': gcs_project,
                'bucket': gcs_bucket,
            },
            'ingestion_helper': {
                'project': helper_project,
                'location': helper_location,
                'service': helper_service,
            },
            'spanner': {
                **spanner_values,
                'source': spanner_source,
                'status': spanner_status,
            },
        },
        'unresolved': unresolved,
        'blocked_reads': blocked_reads,
        'warnings': warnings,
    }


def _resolve_environment(repo_root: Path,
                         options: SnapshotOptions) -> dict[str, Any]:
    preview = build_infrastructure_preview(repo_root, options)
    defaults = load_executor_defaults(repo_root)
    scheduler = preview['resources']['scheduler']
    project = str(scheduler['project']['value'] or '')
    location = str(scheduler['location']['value'] or '')
    facts = []
    helper_service_candidate = str(
        preview['resources']['ingestion_helper']['service']['value'] or '')
    if options.environment == 'prod':
        configured_project = str(defaults.get('gcp_project_id') or '')
        configured_location = str(defaults.get('scheduler_location') or '')
        if configured_project:
            facts.append(
                _evidence(
                    'repo_configured',
                    'import-automation/executor/app/configs.py',
                    'Scheduler project candidate: '
                    f'{configured_project}'))
        if configured_location:
            facts.append(
                _evidence(
                    'repo_configured',
                    'import-automation/executor/app/configs.py',
                    'Scheduler location candidate: '
                    f'{configured_location}'))
        if helper_service_candidate:
            facts.append(
                _evidence(
                    'repo_configured', 'import-automation/executor/scripts/'
                    'update_import_version.sh',
                    'Ingestion helper service candidate: '
                    f'{helper_service_candidate}'))
    if not project or not location:
        raise SnapshotError(
            'Scheduler project and location are unresolved. Provide both; '
            'non-production infrastructure is never inferred.')
    if preview['resources']['spanner']['status'] == 'incomplete':
        raise SnapshotError(
            'Spanner coordinates are incomplete. Provide project, instance, '
            'and database together, or omit all three for live resolution.')
    if options.scheduler_project:
        facts.append(
            _evidence('user_provided', '--scheduler_project',
                      f'Scheduler project: {project}'))
    if options.scheduler_location:
        facts.append(
            _evidence('user_provided', '--scheduler_location',
                      f'Scheduler location: {location}'))
    for warning in preview['warnings']:
        facts.append(_evidence('derived', 'infrastructure preview', warning))
    return {
        'name': options.environment,
        'scheduler_project': project,
        'scheduler_location': location,
        'facts': facts,
        'repo_defaults': defaults,
        'ingestion_helper_service_candidate': helper_service_candidate,
    }


def _new_snapshot(options: SnapshotOptions,
                  environment: dict[str, Any]) -> dict[str, Any]:
    return {
        'schema_version': 1,
        'generated_at': format_rfc3339(now_utc()),
        'environment': {
            key: value
            for key, value in environment.items()
            if key != 'repo_defaults'
        },
        'query': {
            'mode': options.mode,
            'start_time': format_rfc3339(options.start_time),
            'end_time': format_rfc3339(options.end_time),
            'limits': {
                'run_limit': options.run_limit,
                'scan_limit': options.scan_limit,
                'import_limit': options.import_limit,
                'log_limit': options.log_limit,
                'object_limit': options.object_limit,
                'history_limit': options.history_limit,
            },
            'status': options.status or None,
            'import_name_pattern': options.import_name_pattern or None,
            'consecutive_failures': options.consecutive_failures,
            'truncated': False,
        },
        'imports': [],
        'evidence': list(environment['facts']),
        'warnings': [],
    }


def _empty_import(record: ImportRecord) -> dict[str, Any]:
    return {
        'identity': record.to_dict(),
        'auto_refresh': {
            'configured': bool(record.cron_schedule),
            'configured_schedule': record.cron_schedule,
            'deployed': False,
        },
        'deployment': {},
        'links': {},
        'latest_run_id': None,
        'latest_successful_run_id': None,
        'latest_successful_run': {
            'id': None,
            'version': None,
            'timestamp': None,
            'source': None,
            'complete': False,
        },
        'version_pointers': {},
        'state_records': {},
        'runs': [],
        'warnings': [],
    }


def _consistent_value(name: str, explicit: str, observed: list[tuple[str, Any]],
                      warnings: list[str]) -> str:
    candidates = [(source, str(value)) for source, value in observed if value]
    if explicit:
        candidates.append(('user-provided flag', explicit))
    values = {value for _, value in candidates}
    if len(values) > 1:
        detail = ', '.join(f'{source}={value}' for source, value in candidates)
        warnings.append(f'Conflicting {name} values; skipped dependent reads: '
                        f'{detail}')
        return ''
    return next(iter(values), '')


def _publication_observed(summary: dict[str, Any], pointers: dict[str, Any],
                          state_records: dict[str, Any], run_id: str) -> bool:
    latest_version = str(summary.get('latest_version') or '').rstrip('/')
    version = latest_version.rsplit('/', 1)[-1] if latest_version else ''
    accepted = str(pointers.get('accepted', {}).get('value') or '').strip()
    if version and accepted == version:
        return True
    status = state_records.get('import_status', {})
    current = str(status.get('LatestVersion') or '').rstrip('/')
    if latest_version and current == latest_version:
        return True
    for event in state_records.get('version_history', []):
        event_version = str(event.get('Version') or '').rstrip('/')
        comment = str(event.get('Comment') or '')
        if version and event_version == version:
            return True
        if run_id and f'import-workflow:{run_id}' in comment:
            return True
    return False


def _downstream_state(summary: dict[str, Any],
                      state_records: dict[str, Any]) -> tuple[str, list[Any]]:
    version = str(summary.get('latest_version') or
                  '').rstrip('/').rsplit('/', 1)[-1]
    downstream_ids = {
        str(event.get('WorkflowExecutionID') or '').rsplit('/', 1)[-1]
        for event in state_records.get('version_history', [])
        if version and str(event.get('Version') or '') == version and
        str(event.get('Comment') or '').startswith('ingestion-workflow:')
    }
    matches = [
        row for row in state_records.get('downstream_ingestion_history', [])
        if str(row.get('WorkflowExecutionID') or '').rsplit('/', 1)[-1] in
        downstream_ids
    ]
    if not matches:
        return 'unknown', []
    failed = any(row.get('IngestionFailure') for row in matches)
    return ('failed' if failed else 'observed'), matches


def _import_workflow_id(comment: Any) -> str | None:
    marker = 'import-workflow:'
    value = str(comment or '')
    if marker not in value:
        return None
    remainder = value.split(marker, 1)[1].strip()
    if not remainder:
        return None
    execution_id = remainder.split(maxsplit=1)[0]
    return execution_id.rstrip('.,;') or None


def _latest_successful_run(runs: list[dict[str, Any]],
                           state_records: dict[str, Any]) -> dict[str, Any]:
    candidates = []
    for run in runs:
        if run.get('status', {}).get('composite') != 'succeeded':
            continue
        candidates.append({
            'id': run.get('id'),
            'version': run.get('version'),
            'timestamp': (run.get('end_time') or run.get('start_time') or
                          run.get('create_time')),
            'source': 'workflow_run',
            'complete': True,
        })
    for event in state_records.get('version_history', []):
        status = str(event.get('Status') or '').rsplit('.', 1)[-1].upper()
        execution_id = _import_workflow_id(event.get('Comment'))
        if status != 'STAGING' or not execution_id:
            continue
        candidates.append({
            'id': execution_id,
            'version': event.get('Version'),
            'timestamp': event.get('UpdateTimestamp'),
            'source': 'spanner_version_history',
            'complete': True,
        })
    if candidates:
        return max(candidates,
                   key=lambda candidate: candidate.get('timestamp') or '')
    return {
        'id': None,
        'version': None,
        'timestamp': None,
        'source': None,
        'complete': False,
    }


def _job_id_aliases(value: Any) -> set[str]:
    text = str(value or '')
    return {text, text.rsplit('/', 1)[-1]} if text else set()


def _batch_job_ids(batch: dict[str, Any],
                   include_expected: bool = True) -> set[str]:
    result = (_job_id_aliases(batch.get('expected_job_id'))
              if include_expected else set())
    for job in batch.get('jobs', []):
        for value in (job.get('uid'), job.get('batch_job_name'),
                      job.get('resource_name')):
            result.update(_job_id_aliases(value))
    return result


def _acquisition_sources(record: ImportRecord) -> list[dict[str, Any]]:
    sources = []
    if record.provenance_url:
        sources.append({
            'uri': record.provenance_url,
            'description': record.provenance_description,
            'source': 'manifest.provenance_url',
        })
    sources.extend({
        'path': source,
        'source': 'manifest.source_files',
    } for source in record.source_files)
    return sources


def _collect_run(
        repo_root: Path,
        runner: ReadOnlyCommandRunner,
        options: SnapshotOptions,
        environment: dict[str, Any],
        record: ImportRecord,
        workflow: dict[str, Any],
        run: dict[str, Any],
        gcs: dict[str, Any],
        state_records: dict[str, Any],
        batch: dict[str, Any] | None = None,
        include_expensive: bool = True,
        workflow_revision: dict[str, Any] | None = None) -> dict[str, Any]:
    result = dict(run)
    result['artifacts'] = {
        'acquisition_sources': _acquisition_sources(record),
        'raw_source_files': [],
        'import_tool_inputs': [],
        'genmcf_outputs': [],
        'resolved_mcf': [],
        'unresolved_mcf': [],
        'validation': [],
    }
    result['logs'] = []
    result['logs_truncated'] = False
    result['warnings'] = []
    if batch is None:
        try:
            batch = collect_batch_for_run(runner, run,
                                          record.absolute_import_name,
                                          environment['scheduler_project'],
                                          environment['scheduler_location'])
        except CommandError as exc:
            result['warnings'].append(f'Batch evidence unavailable: {exc}')
            batch = unavailable_batch_evidence(run, 'batch_lookup_failed')
    else:
        normalized = unavailable_batch_evidence(
            run,
            batch.get('unavailable_reason') or 'batch_evidence_incomplete')
        normalized.update(batch)
        if batch.get('correlation') and batch.get('jobs'):
            normalized['unavailable_reason'] = batch.get('unavailable_reason')
        batch = normalized
    if batch.get('unavailable_reason') and not any(
            warning.startswith('Batch evidence unavailable')
            for warning in result['warnings']):
        result['warnings'].append('Batch evidence unavailable: ' +
                                  str(batch['unavailable_reason']))
    result['batch'] = batch
    candidate_jobs = batch.get('jobs', [])
    jobs = (candidate_jobs
            if batch.get('correlation') in ('exact', 'time_correlated') else [])
    result['resources'] = {
        'workflow_execution': {
            key: run.get(key)
            for key in ('name', 'id', 'state', 'create_time', 'start_time',
                        'end_time', 'workflow_revision_id')
        },
        'workflow_revision': workflow_revision or {},
        'batch_jobs': candidate_jobs,
    }
    job_ids = _batch_job_ids(batch, include_expected=False)
    expected_job_ids = (_job_id_aliases(batch.get('expected_job_id'))
                        if batch.get('unavailable_reason') else set())
    summary = {}
    summary_correlation = 'unknown'
    summaries = gcs.get('summaries_by_job_id', {})
    for job_id in (*sorted(job_ids), *sorted(expected_job_ids - job_ids)):
        if job_id in summaries:
            summary = summaries[job_id]
            result['artifacts'].update(
                gcs.get('artifacts_by_job_id', {}).get(job_id, {}))
            summary_correlation = ('exact' if job_id in job_ids else
                                   'strongly_correlated')
            break
    result['import_summary'] = summary
    result['artifacts']['import_summary'] = summary
    result['version'] = summary.get('latest_version')
    if include_expensive:
        for job in jobs:
            uid = job.get('uid')
            start = run.get('start_time') or run.get('create_time')
            end = run.get('end_time') or format_rfc3339(options.end_time)
            if uid and start:
                try:
                    logs, truncated = collect_batch_logs(
                        runner, environment['scheduler_project'], uid, start,
                        end, options.log_limit)
                    result['logs'].extend(logs)
                    result['logs_truncated'] |= truncated
                except CommandError as exc:
                    result['warnings'].append(
                        f'Batch logs unavailable for {uid}: {exc}')
    published = _publication_observed(summary, gcs.get('version_pointers', {}),
                                      state_records, run.get('id', ''))
    downstream, downstream_rows = _downstream_state(summary, state_records)
    pipeline = normalize_pipeline_status(summary) or 'unknown'
    result['status'] = {
        'workflow': str(run.get('state') or 'unknown').lower(),
        'batch': [
            str(job.get('status', {}).get('state') or 'unknown').lower()
            for job in jobs
        ],
        'technical': technical_state(run, jobs),
        'pipeline': pipeline.lower(),
        'semantic_validation':
            ('failed' if pipeline == 'VALIDATION' else
             'passed' if pipeline in ('STAGING', 'SKIP') else 'unknown'),
        'publication': 'observed' if published else 'unknown',
        'downstream_ingestion': downstream,
        'composite': composite_status(run, jobs, summary, published),
    }
    result['downstream_ingestion_records'] = downstream_rows
    result['correlation'] = {
        'workflow_to_batch': batch.get('correlation', 'unknown'),
        'batch_evidence': batch.get('evidence', []),
        'batch_to_summary': summary_correlation,
    }
    if jobs:
        job = jobs[0]
        job_id = str(job.get('resource_name') or '').rsplit('/', 1)[-1]
        result['links'] = {
            'batch':
                batch_link(environment['scheduler_project'],
                           environment['scheduler_location'], job_id)
        }
        image_uri = job.get('image_uri')
        task_start = batch_task_start_time(job)
        time_basis = 'batch_task_running_event'
        if not task_start:
            task_start = job.get('create_time')
            time_basis = 'batch_job_create_time'
        if not task_start:
            task_start = run.get('start_time') or run.get('create_time')
            time_basis = 'workflow_start_time'
        if include_expensive and image_uri and task_start:
            try:
                result['runtime_provenance'] = collect_runtime_provenance(
                    repo_root=repo_root,
                    image_uri=image_uri,
                    task_start_time=task_start,
                    workflow_revision_id=run.get('workflow_revision_id') or
                    workflow.get('revision_id') or '',
                    build_project=options.build_project,
                    build_region=options.build_region,
                    runner=runner,
                )
                result['runtime_provenance']['workflow_source_sha256'] = ((
                    workflow_revision or {}).get('source_sha256'))
                result['runtime_provenance']['task_start_time'] = task_start
                result['runtime_provenance']['time_basis'] = time_basis
            except (CommandError, ValueError) as exc:
                result['warnings'].append(
                    f'Runtime provenance unavailable: {exc}')
    return result


def _collect_workflow_revisions(runner: ReadOnlyCommandRunner,
                                target: dict[str, str], runs: list[dict[str,
                                                                        Any]],
                                warnings: list[str]) -> dict[str, Any]:
    revisions = {}
    revision_ids = {
        run.get('workflow_revision_id')
        for run in runs
        if run.get('workflow_revision_id')
    }
    for revision_id in sorted(revision_ids):
        try:
            revisions[revision_id] = describe_workflow(runner,
                                                       target,
                                                       revision_id=revision_id)
        except CommandError as exc:
            warnings.append(
                f'Workflow revision {revision_id} unavailable: {exc}')
    return revisions


def _collect_state_records(runner: ReadOnlyCommandRunner,
                           options: SnapshotOptions, environment: dict[str,
                                                                       Any],
                           workflow: dict[str, Any], expected_gcs_bucket: str,
                           import_name: str, warnings: list[str],
                           client: Any | None) -> dict[str, Any]:
    helper_project = _consistent_value(
        'ingestion helper project', options.helper_project,
        [('Workflow target', environment['scheduler_project'])], warnings)
    helper_location = _consistent_value(
        'ingestion helper location', options.helper_location,
        [('Workflow target', environment['scheduler_location'])], warnings)
    helper_service = _consistent_value(
        'ingestion helper service', options.helper_service,
        [('Workflow source', workflow.get('ingestion_helper_service')),
         ('repository candidate',
          environment.get('ingestion_helper_service_candidate'))], warnings)
    helper = {}
    if helper_project and helper_location and helper_service:
        try:
            helper = describe_ingestion_helper(runner, helper_project,
                                               helper_location, helper_service)
        except CommandError as exc:
            warnings.append(f'Ingestion helper unavailable: {exc}')
    elif helper_project:
        warnings.append(
            'Ingestion helper location or service name is unresolved; skipped '
            'helper and Spanner discovery.')
    helper_env = helper.get('environment', {})
    result: dict[str, Any] = {'ingestion_helper': helper}
    links = {}
    if helper:
        links['ingestion_helper'] = cloud_run_link(helper_project,
                                                   helper_location,
                                                   helper_service)
    helper_bucket = str(helper_env.get('GCS_BUCKET_ID') or '')
    if expected_gcs_bucket and helper_bucket and helper_bucket != expected_gcs_bucket:
        warnings.append(
            'Ingestion helper GCS bucket conflicts with the verified executor '
            'bucket; skipped Spanner reads and cross-system joins.')
        result['links'] = links
        return result
    spanner_project = _consistent_value(
        'Spanner project', options.spanner_project,
        [('ingestion helper', helper_env.get('SPANNER_PROJECT_ID'))], warnings)
    spanner_instance = _consistent_value(
        'Spanner instance', options.spanner_instance,
        [('ingestion helper', helper_env.get('SPANNER_INSTANCE_ID'))], warnings)
    spanner_database = _consistent_value(
        'Spanner database', options.spanner_database,
        [('ingestion helper', helper_env.get('SPANNER_DATABASE_ID'))], warnings)
    if spanner_project and spanner_instance and spanner_database:
        try:
            started = time.monotonic()
            database_resource = (
                f'projects/{spanner_project}/instances/{spanner_instance}/'
                f'databases/{spanner_database}')
            _progress(
                options, f'Reading Spanner records from {database_resource} '
                f'for {import_name}; '
                f'history_limit={options.history_limit}')
            result.update(
                read_spanner_records(spanner_project,
                                     spanner_instance,
                                     spanner_database,
                                     import_name,
                                     options.history_limit,
                                     client=client))
            _progress(
                options, f'Completed Spanner records for {import_name}; '
                f'version_history={len(result.get("version_history", []))}; '
                'downstream_history='
                f'{len(result.get("downstream_ingestion_history", []))}; '
                f'elapsed={time.monotonic() - started:.1f}s')
            links['spanner'] = spanner_link(spanner_project, spanner_instance,
                                            spanner_database)
        except Exception as exc:
            warnings.append(f'Spanner records unavailable: {exc}')
    elif any((spanner_project, spanner_instance, spanner_database)):
        warnings.append(
            'Spanner coordinates are incomplete; skipped Spanner reads.')
    result['links'] = links
    return result


def collect_import(
        repo_root: Path,
        runner: ReadOnlyCommandRunner,
        options: SnapshotOptions,
        environment: dict[str, Any],
        record: ImportRecord,
        workflow_client: Any | None = None,
        spanner_client: Any | None = None,
        scheduler: dict[str, Any] | None = None,
        workflow: dict[str, Any] | None = None,
        listed_executions: dict[str, Any] | None = None) -> dict[str, Any]:
    """Collects one import without turning missing permissions into guesses."""
    _progress(options, f'Collecting import {record.absolute_import_name}')
    result = _empty_import(record)
    try:
        scheduler = scheduler or describe_scheduler(
            runner, record.import_name, record.absolute_import_name,
            environment['scheduler_project'], environment['scheduler_location'])
    except CommandError as exc:
        result['warnings'].append(f'Scheduler evidence unavailable: {exc}')
        return result
    result['deployment']['scheduler'] = scheduler
    result['auto_refresh']['deployed'] = bool(scheduler.get('verified'))
    result['links']['scheduler'] = scheduler_link(
        environment['scheduler_project'], environment['scheduler_location'])
    if not scheduler.get('verified'):
        result['warnings'].append(
            'Scheduler identity was not verified against both description and '
            'Workflow target importName; dependent reads were skipped.')
        return result
    try:
        target = parse_workflow_target(scheduler.get('target_uri') or '')
    except ValueError as exc:
        result['warnings'].append(str(exc))
        return result
    try:
        workflow = workflow or describe_workflow(runner, target)
    except CommandError as exc:
        result['warnings'].append(f'Workflow evidence unavailable: {exc}')
        workflow = {}
    result['deployment']['workflow'] = workflow
    result['links']['workflow'] = workflow_link(target['project'],
                                                target['location'],
                                                target['workflow'])
    if listed_executions is None:
        try:
            started = time.monotonic()
            _progress(
                options,
                f'Listing Workflow executions for {target["resource"]}; '
                f'window={format_rfc3339(options.start_time)}..'
                f'{format_rfc3339(options.end_time)}; '
                f'scan_limit={options.scan_limit}')
            listed_executions = list_workflow_execution_records(
                target['resource'],
                options.start_time,
                options.end_time,
                options.scan_limit,
                client=workflow_client)
            _progress(
                options, 'Completed Workflow execution listing; '
                f'scanned={listed_executions["scanned_execution_count"]}; '
                f'pages={listed_executions["page_count"]}; '
                f'elapsed={time.monotonic() - started:.1f}s')
        except WorkflowExecutionError as exc:
            result['warnings'].append(str(exc))
            listed_executions = {
                'workflow_resource': target['resource'],
                'executions': [],
                'truncated': False,
            }
    runs_result = filter_import_runs(listed_executions,
                                     record.absolute_import_name,
                                     options.run_limit)
    result['deployment']['workflow_execution_scan'] = {
        key: value for key, value in runs_result.items() if key not in ('runs',)
    }
    raw_runs = runs_result['runs']
    _progress(
        options, f'Matched {len(raw_runs)} Workflow runs for '
        f'{record.absolute_import_name}')
    batches = []
    for run in raw_runs:
        try:
            batches.append(
                collect_batch_for_run(runner, run, record.absolute_import_name,
                                      target['project'], target['location']))
        except CommandError:
            batches.append(
                unavailable_batch_evidence(run, 'batch_lookup_failed'))
    batch_configs = [('Batch runnable',
                      job.get('import_config',
                              {}).get('storage_prod_bucket_name'))
                     for batch in batches
                     if batch.get('correlation') in ('exact', 'time_correlated')
                     for job in batch.get('jobs', [])]
    target_config = scheduler.get('target_import_config', {})
    workflow_env = workflow.get('user_environment', {})
    gcs_bucket = _consistent_value(
        'GCS bucket', options.gcs_bucket,
        [('Scheduler target', target_config.get('storage_prod_bucket_name')),
         ('Workflow environment', workflow_env.get('GCS_BUCKET_ID')),
         *batch_configs], result['warnings'])
    gcs_project = _consistent_value(
        'GCS project', options.gcs_project,
        [('Scheduler target', target_config.get('gcs_project_id'))],
        result['warnings'])
    defaults = environment['repo_defaults']
    if not gcs_project and options.environment == 'prod' and not any(
            'Conflicting GCS project' in warning
            for warning in result['warnings']):
        gcs_project = str(defaults.get('gcs_project_id') or '')
    accepted_pointer = str(
        target_config.get('storage_version_filename') or
        defaults.get('storage_version_filename') or 'latest_version.txt')
    job_ids = set()
    for batch in batches:
        job_ids.update(
            _batch_job_ids(batch,
                           include_expected=bool(
                               batch.get('unavailable_reason'))))
    gcs = {}
    if gcs_bucket and gcs_project:
        _progress(
            options, f'Collecting GCS evidence for '
            f'{record.absolute_import_name}; object_limit='
            f'{options.object_limit}')
        gcs = collect_gcs_evidence(
            runner, gcs_project, gcs_bucket,
            record.absolute_import_name.replace(':', '/'), record.import_inputs,
            record.import_name, job_ids, accepted_pointer, options.object_limit)
        result['warnings'].extend(gcs.get('warnings', []))
        result['version_pointers'] = gcs.get('version_pointers', {})
        result['deployment']['gcs'] = {
            key: value
            for key, value in gcs.items()
            if key not in ('objects', 'summaries_by_job_id',
                           'artifacts_by_job_id', 'version_pointers')
        }
        result['links']['gcs'] = gcs_link(
            gcs_project, gcs_bucket,
            record.absolute_import_name.replace(':', '/'))
        _progress(
            options,
            f'Completed GCS evidence for {record.absolute_import_name}; '
            f'summaries={len(gcs.get("summaries_by_job_id", {}))}; '
            f'objects={len(gcs.get("objects", []))}; '
            f'truncated={gcs.get("truncated", False)}')
    else:
        result['warnings'].append(
            'GCS project or bucket is unresolved; skipped artifact reads.')
    result['version_pointers']['configured_history'] = {
        'config_field': 'storage_version_history_filename',
        'filename': defaults.get('storage_version_history_filename'),
        'authority': 'not_used_by_current_executor',
    }
    result['state_records'] = {}
    result['runs'] = [
        _collect_run(repo_root,
                     runner,
                     options, {
                         **environment,
                         'scheduler_project': target['project'],
                         'scheduler_location': target['location'],
                     },
                     record,
                     workflow,
                     run,
                     gcs,
                     result['state_records'],
                     batch,
                     include_expensive=False,
                     workflow_revision=None)
        for run, batch in zip(raw_runs, batches)
    ]
    if options.mode == 'single_import' or _fleet_matches(result, options):
        result['state_records'] = _collect_state_records(
            runner, options, {
                **environment,
                'scheduler_project': target['project'],
                'scheduler_location': target['location'],
            }, workflow, gcs_bucket, record.import_name, result['warnings'],
            spanner_client)
        result['links'].update(result['state_records'].pop('links', {}))
        revisions = _collect_workflow_revisions(runner, target, raw_runs,
                                                result['warnings'])
        result['deployment']['workflow_revisions'] = revisions
        result['runs'] = [
            _collect_run(
                repo_root,
                runner,
                options, {
                    **environment,
                    'scheduler_project': target['project'],
                    'scheduler_location': target['location'],
                },
                record,
                workflow,
                run,
                gcs,
                result['state_records'],
                batch,
                include_expensive=True,
                workflow_revision=revisions.get(
                    run.get('workflow_revision_id')))
            for run, batch in zip(raw_runs, batches)
        ]
    result[
        'latest_run_id'] = result['runs'][0]['id'] if result['runs'] else None
    result['latest_successful_run'] = _latest_successful_run(
        result['runs'], result['state_records'])
    result['latest_successful_run_id'] = result['latest_successful_run']['id']
    result['links']['batch_jobs'] = [
        run['links']['batch']
        for run in result['runs']
        if run.get('links', {}).get('batch')
    ]
    _progress(
        options, f'Completed import {record.absolute_import_name}; '
        f'runs={len(result["runs"])}; warnings='
        f'{len(result["warnings"])}')
    return result


def _fleet_matches(item: dict[str, Any], options: SnapshotOptions) -> bool:
    runs = item['runs']
    latest = runs[0]['status']['composite'] if runs else 'unknown'
    if options.status and latest != options.status:
        return False
    if options.import_name_pattern and options.import_name_pattern.lower(
    ) not in item['identity']['import_name'].lower():
        return False
    if options.consecutive_failures:
        failures = 0
        for run in runs:
            status = run['status']['composite']
            if status == 'failed':
                failures += 1
            else:
                break
        if failures < options.consecutive_failures:
            return False
    return True


def _item_truncated(item: dict[str, Any]) -> bool:
    scan = item.get('deployment', {}).get('workflow_execution_scan', {})
    gcs = item.get('deployment', {}).get('gcs', {})
    spanner_truncation = item.get('state_records', {}).get('truncated', {})
    return bool(
        scan.get('truncated') or scan.get('result_truncated') or
        gcs.get('truncated') or any(spanner_truncation.values()))


def _candidate_import_names(executions: list[dict[str, Any]],
                            by_absolute: dict[str, ImportRecord], pattern: str,
                            limit: int) -> tuple[list[str], bool]:
    candidates = []
    seen = set()
    normalized_pattern = pattern.lower()
    for execution in executions:
        absolute_name = execution.get('argument', {}).get('import_name')
        record = by_absolute.get(absolute_name)
        if not record or absolute_name in seen:
            continue
        seen.add(absolute_name)
        if normalized_pattern and normalized_pattern not in record.import_name.lower(
        ):
            continue
        candidates.append(absolute_name)
    return candidates[:limit], len(candidates) > limit


def collect_fleet(repo_root: Path,
                  runner: ReadOnlyCommandRunner,
                  options: SnapshotOptions,
                  environment: dict[str, Any],
                  catalog: dict[str, list[ImportRecord]],
                  snapshot: dict[str, Any],
                  workflow_client: Any | None = None,
                  spanner_client: Any | None = None) -> None:
    try:
        schedulers = list_schedulers(runner, environment['scheduler_project'],
                                     environment['scheduler_location'])
    except CommandError as exc:
        snapshot['warnings'].append(f'Scheduler listing unavailable: {exc}')
        return
    scheduler_by_import = {
        scheduler.get('target_import_name'): scheduler
        for scheduler in schedulers
        if scheduler.get('target_import_name')
    }
    target_by_resource: dict[str, dict[str, str]] = {}
    for scheduler in schedulers:
        try:
            target = parse_workflow_target(scheduler.get('target_uri') or '')
        except ValueError:
            continue
        target_by_resource[target['resource']] = target
    listed_by_resource = {}
    workflow_by_resource = {}
    all_executions = []
    for resource, target in target_by_resource.items():
        try:
            started = time.monotonic()
            _progress(
                options, f'Listing fleet Workflow executions for {resource}; '
                f'scan_limit={options.scan_limit}')
            listed = list_workflow_execution_records(resource,
                                                     options.start_time,
                                                     options.end_time,
                                                     options.scan_limit,
                                                     client=workflow_client)
            _progress(
                options,
                f'Completed fleet Workflow execution listing for {resource}; '
                f'scanned={listed["scanned_execution_count"]}; '
                f'pages={listed["page_count"]}; '
                f'elapsed={time.monotonic() - started:.1f}s')
            listed_by_resource[resource] = listed
            all_executions.extend(listed['executions'])
            snapshot['query']['truncated'] |= listed['truncated']
        except WorkflowExecutionError as exc:
            snapshot['warnings'].append(str(exc))
            continue
        try:
            workflow_by_resource[resource] = describe_workflow(runner, target)
        except CommandError as exc:
            snapshot['warnings'].append(
                f'Workflow {resource} unavailable: {exc}')
            workflow_by_resource[resource] = {}
    by_absolute = {
        record.absolute_import_name: record for records in catalog.values()
        for record in records
    }
    all_executions.sort(
        key=lambda execution: execution.get('create_time') or '', reverse=True)
    candidate_names, candidates_truncated = _candidate_import_names(
        all_executions, by_absolute, options.import_name_pattern,
        _MAX_IMPORT_LIMIT)
    if candidates_truncated:
        snapshot['query']['truncated'] = True
    for absolute_name in candidate_names:
        record = by_absolute[absolute_name]
        scheduler = scheduler_by_import.get(absolute_name)
        if not scheduler:
            item = _empty_import(record)
            item['warnings'].append(
                'No Scheduler target matched the execution import identity.')
        else:
            try:
                target = parse_workflow_target(scheduler['target_uri'])
            except ValueError as exc:
                item = _empty_import(record)
                item['warnings'].append(str(exc))
            else:
                listed = listed_by_resource.get(
                    target['resource'], {
                        'workflow_resource': target['resource'],
                        'executions': [],
                        'truncated': False,
                    })
                item = collect_import(
                    repo_root,
                    runner,
                    options,
                    environment,
                    record,
                    workflow_client=workflow_client,
                    spanner_client=spanner_client,
                    scheduler={
                        **scheduler,
                        'description_matches':
                            scheduler.get('description') == absolute_name,
                        'target_import_matches':
                            True,
                        'verified':
                            scheduler.get('description') == absolute_name,
                    },
                    workflow=workflow_by_resource.get(target['resource'], {}),
                    listed_executions=listed,
                )
        if _fleet_matches(item, options):
            snapshot['imports'].append(item)
            snapshot['query']['truncated'] |= _item_truncated(item)
            if len(snapshot['imports']) >= options.import_limit:
                snapshot['query']['truncated'] = True
                break


def build_snapshot(repo_root: Path,
                   options: SnapshotOptions,
                   runner: ReadOnlyCommandRunner | None = None,
                   workflow_client: Any | None = None,
                   spanner_client: Any | None = None) -> dict[str, Any]:
    """Builds one schema-versioned snapshot."""
    if options.consecutive_failures > options.run_limit:
        raise SnapshotError('consecutive_failures cannot exceed run_limit.')
    _progress(
        options, f'Starting snapshot; mode={options.mode}; '
        f'environment={options.environment}; '
        f'window={format_rfc3339(options.start_time)}..'
        f'{format_rfc3339(options.end_time)}')
    environment = _resolve_environment(repo_root, options)
    snapshot = _new_snapshot(options, environment)
    command_runner = runner or ReadOnlyCommandRunner(repo_root,
                                                     verbose=options.verbose)
    manifest = Path(options.manifest_path) if options.manifest_path else None
    started = time.monotonic()
    _progress(options, 'Scanning repository import manifests')
    catalog = build_import_catalog(repo_root, manifest)
    _progress(
        options, f'Completed manifest scan; import_names={len(catalog)}; '
        f'elapsed={time.monotonic() - started:.1f}s')
    if options.mode == 'single_import':
        record = resolve_import(catalog, options.import_name)
        item = collect_import(repo_root, command_runner, options, environment,
                              record, workflow_client, spanner_client)
        snapshot['imports'].append(item)
        snapshot['query']['truncated'] = _item_truncated(item)
    else:
        collect_fleet(repo_root, command_runner, options, environment, catalog,
                      snapshot, workflow_client, spanner_client)
    _progress(
        options, f'Completed snapshot collection; imports='
        f'{len(snapshot["imports"])}; warnings='
        f'{len(snapshot["warnings"])}')
    return snapshot


def validate_snapshot(repo_root: Path, snapshot: dict[str, Any]) -> None:
    schema_path = repo_root / 'agents/common/schemas/import_snapshot.schema.json'
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(snapshot),
                    key=lambda error: error.path)
    if errors:
        message = '; '.join(error.message for error in errors[:5])
        raise SnapshotError(f'Generated snapshot failed schema validation: '
                            f'{message}')


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError('Unexpected positional arguments.')
    try:
        repo_root = find_repository_root()
        options = _build_options()
        if _PREVIEW_INFRASTRUCTURE.value:
            preview = build_infrastructure_preview(repo_root, options)
            print(json.dumps(preview, indent=2, sort_keys=True))
            return
        if options.verbose:
            logging.getLogger('agents.common.import_support').setLevel(
                logging.INFO)
        snapshot = build_snapshot(repo_root, options)
        _progress(options, 'Validating snapshot schema')
        validate_snapshot(repo_root, snapshot)
        _progress(options, 'Snapshot schema is valid; writing JSON output')
    except ImportResolutionError as exc:
        print(json.dumps({'error': str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(2) from exc
    except (SnapshotError, WorkflowExecutionError) as exc:
        print(json.dumps({'error': str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(3) from exc
    except Exception as exc:
        print(json.dumps({'error': f'Unexpected collector failure: {exc}'},
                         indent=2),
              file=sys.stderr)
        raise SystemExit(4) from exc
    print(json.dumps(snapshot, indent=2, sort_keys=True))


def _collector_help() -> str:
    return (__doc__ + '\n\nCollector flags:\n' +
            _FLAGS.get_help(include_special_flags=False))


def _parse_flags(argv: list[str]) -> list[str]:
    if _HELP_FLAGS.intersection(argv[1:]):
        print(_collector_help())
        raise SystemExit(0)
    remaining = flags.FLAGS(argv, known_only=True)
    return _FLAGS(remaining)


if __name__ == '__main__':
    app.run(main, flags_parser=_parse_flags)
