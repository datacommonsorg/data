import os

from google.cloud import datastore

CONFIGS_NAMESPACE = 'configs'
CONFIGS_KIND = 'config'
MANIFEST_FILENAME = 'manifest.json'
REQUIREMENTS_FILENAME = 'requirements.txt'
USER_SCRIPT_TIMEOUT = 600
VENV_CREATE_TIMEOUT = 600
GITHUB_AUTH_USERNAME = 'intrepiditee'


#
# Environment specific variables
#
def standalone():
    return 'STANDALONE_MODE' in os.environ

PROJECT_ID = 'datcom-cronjobs' if standalone() else 'google.com:datcom-data'
REPO_OWNER_USERNAME = 'datacommonsorg' if standalone() else 'intrepiditee'
REPO_NAME = 'data' if standalone() else 'data-demo'
BUCKET_NAME = 'datcom-prod-imports' if standalone() else 'import-inputs'


def _get_config(entity_id):
    client = datastore.Client(project=PROJECT_ID, namespace=CONFIGS_NAMESPACE)
    key = client.key(CONFIGS_KIND, entity_id)
    return client.get(key)[entity_id]


def get_dashboard_oauth_client_id():
    if standalone(): return ''
    return _get_config('DASHBOARD_OAUTH_CLIENT_ID')


def get_github_auth_access_token():
    if standalone(): return ''
    return _get_config('GITHUB_AUTH_ACCESS_TOKEN')


def production():
    return 'EXECUTOR_PRODUCTION' in os.environ
