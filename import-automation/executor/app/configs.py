import os

from google.cloud import datastore

PROJECT_ID = 'google.com:datcom-data'
CONFIGS_NAMESPACE = 'configs'
CONFIGS_KIND = 'config'
MANIFEST_FILENAME = 'manifest.json'
REQUIREMENTS_FILENAME = 'requirements.txt'
REPO_OWNER_USERNAME = 'intrepiditee'
GITHUB_AUTH_USERNAME = 'intrepiditee'
REPO_NAME = 'data-demo'
BUCKET_NAME = 'import-inputs'
USER_SCRIPT_TIMEOUT = 600
VENV_CREATE_TIMEOUT = 600


def _get_config(entity_id):
    client = datastore.Client(project=PROJECT_ID, namespace=CONFIGS_NAMESPACE)
    key = client.key(CONFIGS_KIND, entity_id)
    return client.get(key)[entity_id]


def get_dashboard_oauth_client_id():
    return _get_config('DASHBOARD_OAUTH_CLIENT_ID')


def get_github_auth_access_token():
    return _get_config('GITHUB_AUTH_ACCESS_TOKEN')


def production():
    return 'EXECUTOR_PRODUCITON' in os.environ
