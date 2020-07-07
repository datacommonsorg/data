from google.cloud import secretmanager


PROJECT_ID = 'google.com:datcom-data'
MANIFEST_FILENAME = 'manifest.json'
REQUIREMENTS_FILENAME = 'requirements.txt'
REPO_OWNER_USERNAME = 'intrepiditee'
GITHUB_AUTH_USERNAME = 'intrepiditee'


def _get_secret(secret_id, version_id='latest'):
    client = secretmanager.SecretManagerServiceClient()
    name = client.secret_version_path(PROJECT_ID, secret_id, version_id)
    response = client.access_secret_version(name)
    return response.payload.data.decode('UTF-8')


def get_dashboard_oauth_client_id(version_id='latest'):
    return _get_secret('DASHBOARD_OAUTH_CLIENT_ID', version_id)


def get_github_auth_access_token(version_id='latest'):
    return _get_secret('GITHUB_AUTH_ACCESS_TOKEN', version_id)
