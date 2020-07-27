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
"""
Class for scheduling import updates using Google Cloud Scheduler.
"""

import os
import logging
import json
import traceback
import tempfile
from typing import Dict, List

from google.cloud import scheduler
from google.protobuf import json_format

from app import configs
from app import utils
from app.service import dashboard_api
from app.service import github_api
from app.executor import import_target
from app.executor import import_executor
from app.executor import validation


class UpdateScheduler:
    """Class for scheduling import updates using Google Cloud Scheduler.

    The scheduled jobs use the '/update' endpoint to update imports.

    Attributes:
        client: CloudSchedulerClient object for managing Google Cloud
            Scheduler jobs.
        github: GitHubRepoAPI object for querying the GitHub API.
        config: ExecutorConfig object containing configurations for
            Cloud Scheduler.
        dashboard: DashboardAPI for communicating with the
            import progress dashboard. If not provided, the scheduler will not
            communicate with the dashboard.

    Returns:
        Created job as a dict.
    """

    def __init__(self,
                 client: scheduler.CloudSchedulerClient,
                 github: github_api.GitHubRepoAPI,
                 config: configs.ExecutorConfig,
                 dashboard: dashboard_api.DashboardAPI = None):
        self.client = client
        self.github = github
        self.config = config
        self.dashboard = dashboard

    def schedule_on_commit(
            self,
            commit_sha: str,
            repo_name: str = None,
            branch_name: str = None,
            pr_number: str = None) -> import_executor.ExecutionResult:
        """Schedules periodic updates for imports specified in the commit
        message of a GitHub commit.

        Args:
            commit_sha: ID of the commit as a string.
            repo_name: Name of the repository the commit is for as a string.
            branch_name: Name of the branch the commit is for as a string.
            pr_number: If the commit is a part of a pull request, the number of
                the pull request as an int.

        Returns:
            ExecutionResult object whose imports_executed field contains the
            jobs created each as a dict.
        """
        run_id = None
        try:
            if self.dashboard:
                run_id = import_executor._init_run_helper(
                    dashboard=self.dashboard,
                    commit_sha=commit_sha,
                    repo_name=repo_name,
                    branch_name=branch_name,
                    pr_number=pr_number)['run_id']
        except Exception:
            logging.exception(import_executor._SYSTEM_RUN_INIT_FAILED_MESSAGE)
            return import_executor._create_system_run_init_failed_result(
                traceback.format_exc())

        return import_executor._run_and_handle_exception(
            run_id, self.dashboard, self._schedule_on_commit_helper, commit_sha,
            run_id)

    def _schedule_on_commit_helper(
            self, commit_sha: str,
            run_id: str) -> import_executor.ExecutionResult:

        commit_info = self.github.query_commit(commit_sha)
        commit_message = commit_info['commit']['message']
        manifest_dirs = self.github.find_dirs_in_commit_containing_file(
            commit_sha, self.config.manifest_filename)
        targets = import_target.parse_commit_message_targets(
            commit_message, 'SCHEDULES')
        if not targets:
            message = ('No import target specified in commit message '
                       f'({commit_message})')
            return import_executor.ExecutionResult('pass', [], message)

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = self.github.download_repo(tmpdir, commit_sha)
            repo_dir = os.path.join(tmpdir, repo_dir)
            validation.are_import_targets_valid(targets, list(manifest_dirs),
                                                repo_dir,
                                                self.config.manifest_filename)
            for target in import_target.filter_absolute_import_names(targets):
                import_dir, _ = import_target.split_absolute_import_name(target)
                manifest_dirs.add(import_dir)

            scheduled = []
            for import_dir in manifest_dirs:
                absolute_import_dir = os.path.join(repo_dir, import_dir)
                manifest_path = os.path.join(absolute_import_dir,
                                             self.config.manifest_filename)
                manifest = import_executor.parse_manifest(manifest_path)
                validation.is_manifest_valid(manifest, repo_dir, import_dir)

                for spec in manifest['import_specifications']:
                    schedule = spec.get('cron_schedule')
                    if not schedule:
                        raise KeyError(
                            f'cron_schedule not found in {manifest_path}')
                    try:
                        scheduled.append(
                            self.create_schedule(
                                import_target.get_absolute_import_name(
                                    import_dir, spec['import_name']), schedule))
                    except Exception:
                        raise import_executor.ExecutionError(
                            import_executor.ExecutionResult(
                                'failed', scheduled, traceback.format_exc()))
            return import_executor.ExecutionResult('succeeded', scheduled,
                                                   'No issues')

    def create_schedule(self, absolute_import_name: str, schedule: str) -> Dict:
        """Schedules periodic updates for an import.

        The body field of the app_engine_http_target field is converted from
        bytes to dict.

        Example:
            The method call
                create_schedule('scripts/us_fed:treasury', '* * * * *')
            schedules a cron job that updates the import every minute. The
            name of the job is 'scripts_us_fed_treasury' and the description
            is 'scripts/us_fed:treasury'. See _create_job_body for
            exact job definition.

        Attributes:
            absolute_import_name: Absolute import name of the import to be
                updated. This is used as the name of the job.
            schedule: Cron schedule for the updates as a string. See
                https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules.

        Returns:
            Created job as a dict.

        Raises:
            Same exceptions as CloudSchedulerClient.create_job.
        """
        location_path = self.client.location_path(
            self.config.gcp_project_id,
            self.config.scheduler_location)
        job = self.client.create_job(
            location_path,
            self._create_job_body(absolute_import_name, schedule))
        scheduled = json_format.MessageToDict(
            job, preserving_proto_field_name=True)
        scheduled['app_engine_http_target']['body'] = json.loads(
            job.app_engine_http_target.body)
        return scheduled

    def delete_schedule(self, absolute_import_name):
        """Deletes an update schedule for an import.

        Args:
            absolute_import_name: Absolute import name of the import
                as a string.

        Raises:
            Same exceptions as CloudSchedulerClient.delete_job.
        """
        job_path = self.client.job_path(
            self.config.gcp_project_id,
            self.config.scheduler_location,
            _fix_absolute_import_name(absolute_import_name))
        self.client.delete_job(job_path)

    def _create_job_body(self, absolute_import_name: str,
                         schedule: str) -> Dict:
        """Creates the body of a Cloud Scheduler job for updating an import.

        This function does not schedule any jobs.

        Args:
            absolute_import_name: Absolute import name of the import
                as a string.
            schedule: Cron schedule for the updates as a string.

        Returns:
            The body of a Cloud Scheduler job as a dict that is ready to be used
            as an argument to CloudSchedulerClient.create_job.
        """
        job_name = self.client.job_path(
            self.config.gcp_project_id,
            self.config.scheduler_location,
            _fix_absolute_import_name(absolute_import_name))
        return {
            'name': job_name,
            'description': absolute_import_name,
            'schedule': schedule,
            'time_zone': 'Etc/UTC',
            'app_engine_http_target': {
                'http_method':
                    'POST',
                'app_engine_routing': {
                    'service': 'default',
                },
                'relative_uri':
                    '/update',
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body':
                    json.dumps({
                        'absolute_import_name': absolute_import_name,
                        'configs': {
                            'github_repo_name':
                                self.config.github_repo_name,
                            'github_repo_owner_username':
                                self.config.github_repo_owner_username,
                            'github_auth_username':
                                self.config.github_auth_username,
                            'github_auth_access_token':
                                self.config.github_auth_access_token,
                            'dashboard_oauth_client_id':
                                self.config.dashboard_oauth_client_id
                        }
                    }).encode()
            },
            'retry_config': {
                'retry_count': 2,
                'min_backoff_duration': {
                    # 1h
                    'seconds': 60 * 60
                }
            },
            'attempt_deadline': {
                # 24h
                'seconds': 24 * 60 * 60
            }
        }


def _fix_absolute_import_name(absolute_import_name: str) -> str:
    """Replaces all the forward slashes and colons in an absolute import name
    with underscores. This is for conforming to restrictions of Cloud Scheduler
    job names."""
    return absolute_import_name.replace('/', '_').replace(':', '_')
