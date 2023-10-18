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
Endpoints for the executor.

The endpoints are:
1) '/': Endpoint for executing imports on GitHub commits.
2) '/update': Endpoint for updating imports.
3) '/schedule': Endpoint for scheduling cron jobs for updating imports upon
                GitHub commits.
"""

import dataclasses

import flask
from google.cloud import scheduler

from app import configs
from app.executor import validation
from app.executor.scheduler_job_manager import schedule_on_commit
from app.executor import import_executor
from app.service import file_uploader
from app.service import dashboard_api
from app.service import github_api
from app.service import email_notifier
from app.service import import_service


def create_app():
    """Creates the Flask app."""
    return flask.Flask(__name__)


FLASK_APP = create_app()


@FLASK_APP.route('/', methods=['POST'])
def execute_imports():
    """Endpoint for executing imports on GitHub commits."""
    task_info = flask.request.get_json(force=True)
    if 'COMMIT_SHA' not in task_info:
        return {'error': 'COMMIT_SHA not found'}
    commit_sha = task_info['COMMIT_SHA']
    repo_name = task_info.get('REPO_NAME')
    branch_name = task_info.get('BRANCH_NAME')
    pr_number = task_info.get('PR_NUMBER')

    task_configs = task_info.get('configs', {})
    config = configs.ExecutorConfig(**task_configs)
    executor = import_executor.ImportExecutor(
        uploader=file_uploader.GCSFileUploader(
            project_id=config.gcs_project_id,
            bucket_name=config.storage_dev_bucket_name,
            path_prefix=config.storage_executor_output_prefix),
        github=github_api.GitHubRepoAPI(
            repo_owner_username=config.github_repo_owner_username,
            repo_name=config.github_repo_name,
            auth_username=config.github_auth_username,
            auth_access_token=config.github_auth_access_token),
        config=config,
        dashboard=dashboard_api.DashboardAPI(config.dashboard_oauth_client_id),
        notifier=email_notifier.EmailNotifier(config.email_account,
                                              config.email_token),
        importer=import_service.ImportServiceClient(
            project_id=config.gcs_project_id,
            executor_output_prefix=config.storage_executor_output_prefix,
            importer_output_prefix=config.storage_importer_output_prefix,
            unresolved_mcf_bucket_name=config.storage_dev_bucket_name,
            resolved_mcf_bucket_name=config.storage_importer_bucket_name,
            client_id=config.importer_oauth_client_id))
    result = executor.execute_imports_on_commit(commit_sha=commit_sha,
                                                repo_name=repo_name,
                                                branch_name=branch_name,
                                                pr_number=pr_number)
    return dataclasses.asdict(result)


@FLASK_APP.route('/update', methods=['POST'])
def scheduled_updates():
    """Endpoint for updating imports."""
    task_info = flask.request.get_json(force=True)
    if 'absolute_import_name' not in task_info:
        return {'error': 'absolute_import_name not found'}
    task_configs = task_info.get('configs', {})
    config = configs.ExecutorConfig(**task_configs)
    executor = import_executor.ImportExecutor(
        uploader=file_uploader.GCSFileUploader(
            project_id=config.gcs_project_id,
            bucket_name=config.storage_prod_bucket_name),
        github=github_api.GitHubRepoAPI(
            repo_owner_username=config.github_repo_owner_username,
            repo_name=config.github_repo_name,
            auth_username=config.github_auth_username,
            auth_access_token=config.github_auth_access_token),
        config=config)
    result = executor.execute_imports_on_update(
        task_info['absolute_import_name'])
    return dataclasses.asdict(result)


@FLASK_APP.route('/schedule', methods=['POST'])
def schedule_data_refresh_cron_jobs():
    """Endpoint for scheduling cron jobs for updating imports upon
    GitHub commits.

    How configs are passed around:
    import-automation/cloudbuild/cloudbuild*.yaml schedules how this
    endpoint is called and what config is used.

    The config is then passed down to the data refresh cron jobs
    scheduled by this endpoint.
    """
    task_info = flask.request.get_json(force=True)
    if 'COMMIT_SHA' not in task_info:
        return 'COMMIT_SHA not found'
    task_configs = task_info.get('configs', {})
    config = configs.ExecutorConfig(**task_configs)
    github = github_api.GitHubRepoAPI(
        repo_owner_username=config.github_repo_owner_username,
        repo_name=config.github_repo_name,
        auth_username=config.github_auth_username,
        auth_access_token=config.github_auth_access_token)

    res = import_executor.run_and_handle_exception(
        None,  # run_id
        None,  # dashboard
        schedule_on_commit,
        github,
        config,
        task_info['COMMIT_SHA'])
    return dataclasses.asdict(res)


@FLASK_APP.route('/_ah/start')
def start():
    """Handles start up calls from App Engine."""
    return ''


@FLASK_APP.route('/healthz')
def healthz():
    """Healthcheck endpoint"""
    return ''


def main():
    """Runs the app locally."""
    FLASK_APP.run(host='127.0.0.1', port=8080, debug=True)


if __name__ == '__main__':
    main()
