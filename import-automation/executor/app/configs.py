from google.cloud import datastore


PROJECT_ID = 'google.com:datcom-data'
CONFIGS_NAMESPACE = 'configs'
CONFIGS_KIND = CONFIGS_NAMESPACE


def get_dashboard_oauth_client_id():
    client = datastore.Client(project=PROJECT_ID, namespace=CONFIGS_NAMESPACE)
    entity_id = 'DASHBOARD_OAUTH_CLIENT_ID'
    key = datastore.Key(CONFIGS_KIND, entity_id)
    return client.get(key)[entity_id]
