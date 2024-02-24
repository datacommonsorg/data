# Copyright 2020 Google LLC
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
"""Module scheduling cron jobs.

Currently scheduling can only occur through commit messages
in the format of "SCHEDULES=<target1>,<target2>,...

where a <target> is in the format of <path/to/manifest.json>:<import name>

Example commit message:
"
This change schedules the cron of india covid stats

SCHEDULES=IMPORTS=scripts/covid19_india/cases_count_states_data:covid19IndiaCasesCountStatesData
"
"""

from dataclasses import dataclass
import os
import logging
import json
import traceback
import tempfile
from typing import Dict

from app import configs
from app.service import github_api
from app.executor import import_target
from app.executor import import_executor
from app.executor import cloud_scheduler


def schedule_on_commit(github: github_api.GitHubRepoAPI,
                       config: configs.ExecutorConfig, commit_sha: str):
    """Creates or updates all schedules associated with a commit."""
    targets = import_target.find_targets_in_commit(commit_sha, 'SCHEDULES',
                                                   github)
    if not targets:
        return import_executor.ExecutionResult(
            'pass', [], 'No import target specified in commit message')
    logging.info('Found targets in commit message: %s', ",".join(targets))
    manifest_dirs = github.find_dirs_in_commit_containing_file(
        commit_sha, config.manifest_filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = github.download_repo(tmpdir, commit_sha,
                                        config.repo_download_timeout)
        logging.info('Downloaded repo with commit: %s', commit_sha)

        imports_to_execute = import_target.find_imports_to_execute(
            targets=targets,
            manifest_dirs=manifest_dirs,
            manifest_filename=config.manifest_filename,
            repo_dir=repo_dir)

        scheduled = []
        for relative_dir, spec in imports_to_execute:
            schedule = spec.get('cron_schedule')
            if not schedule:
                manifest_path = os.path.join(relative_dir,
                                             config.manifest_filename)
                raise KeyError(f'cron_schedule not found in {manifest_path}')
            try:
                absolute_import_name = import_target.get_absolute_import_name(
                    relative_dir, spec['import_name'])
                logging.info('Scheduling a data update job for %s',
                             absolute_import_name)
                job = _create_or_update_import_schedule(absolute_import_name,
                                                        schedule, config)
                scheduled.append(job)
            except Exception:
                raise import_executor.ExecutionError(
                    import_executor.ExecutionResult('failed', scheduled,
                                                    traceback.format_exc()))
        return import_executor.ExecutionResult('succeeded', scheduled,
                                               'No issues')


def _create_or_update_import_schedule(absolute_import_name, schedule: str,
                                      config: configs.ExecutorConfig):
    """Create/Update the import schedule for 1 import."""
    # Note: this is the content of what is passed to /update API
    # inside each cronjob http calls.
    json_encoded_job_body = json.dumps({
        'absolute_import_name': absolute_import_name,
        'configs': config.get_data_refresh_config()
    }).encode()

    if config.executor_type == "GKE":
        req = cloud_scheduler.http_job_request(absolute_import_name, schedule,
                                               json_encoded_job_body)
    elif config.executor_type == "GAE":
        req = cloud_scheduler.appengine_job_request(absolute_import_name,
                                                    schedule,
                                                    json_encoded_job_body)
    else:
        raise Exception(
            "Invalid executor_type %s, expects one of ('GKE', 'GAE')",
            config.executor_type)

    return cloud_scheduler.create_or_update_job(config.gcp_project_id,
                                                config.scheduler_location, req)
