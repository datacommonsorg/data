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
from app.service import file_uploader
from app.service import email_notifier


def get_configs():
    c = configs.ExecutorConfig()

    # replace.
    c.gcp_project_id = "datcom-import-automation"
    c.importer_oauth_client_id = "251280076183-ivh5hjgshftv3rgo4mc03t3vbkgdj3at.apps.googleusercontent.com"
    c.github_auth_username = "dc-org2018"
    c.github_auth_access_token = "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"
    c.github_repo_name = "data"
    c.github_repo_owner_username = "datacommonsorg"
    c.email_account = "251280076183-compute@developer.gserviceaccount.com"
    c.email_token = "251280076183-ivh5hjgshftv3rgo4mc03t3vbkgdj3at.apps.googleusercontent.com"
    c.gcs_project_id = "datcom-204919"
    c.storage_prod_bucket_name = "datcom-prod-imports"
    c.executor_type = "GKE"
    c.user_script_args = [
        # "--usda_api_key=569256A0-9CF4-34F0-86F3-FC477003330A",
        "--start_year=2023"
    ]

    return c


def _create_or_update_import_schedule(absolute_import_name, schedule: str,
                                      config: configs.ExecutorConfig):
    """Create/Update the import schedule for 1 import."""
    # Note: this is the content of what is passed to /update API
    # inside each cronjob http calls.
    json_encoded_job_body = json.dumps({
        'absolute_import_name': absolute_import_name,
        'configs': config.get_data_refresh_config()
    }).encode()

    req = cloud_scheduler.http_job_request(
        absolute_import_name,
        schedule,
        json_encoded_job_body,
        gke_caller_service_account=
        'default-service-account@datcom-import-automation.iam.gserviceaccount.com',
        gke_oauth_audience=
        '251280076183-ivh5hjgshftv3rgo4mc03t3vbkgdj3at.apps.googleusercontent.com'
    )

    return cloud_scheduler.create_or_update_job(config.gcp_project_id,
                                                config.scheduler_location, req)


print("hello world")
import_name = "scripts/us_usda/quickstats:UsdaAgSurvey"
schedule = "0 10 * * 2"
c = get_configs()

#print(import_name)

#print(_create_or_update_import_schedule(import_name, schedule, c))

# executor = import_executor.ImportExecutor(
#     uploader=file_uploader.GCSFileUploader(
#         project_id=c.gcs_project_id, bucket_name=c.storage_prod_bucket_name),
#     github=github_api.GitHubRepoAPI(
#         repo_owner_username=c.github_repo_owner_username,
#         repo_name=c.github_repo_name,
#         auth_username=c.github_auth_username,
#         auth_access_token=c.github_auth_access_token),
#     config=c)

# executor.execute_imports_on_update(import_name)

notifier = email_notifier.EmailNotifier("datacommonsorg@gmail.com",
                                        "ahjuntbvjlqdyjqg")
notifier.send("hello testing", "checking if this reaches",
              ["jehangiramjad+automation@gmail.com"])
