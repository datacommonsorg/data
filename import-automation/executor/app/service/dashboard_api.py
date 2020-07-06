import requests

from app import utils
from app.service import iap


DASHBOARD_IMPORT_API = '''
https://datcom-data.uc.r.appspot.com/import/{attempt_id}
'''.strip()

DASHBOARD_LOG_API = '''
https://datcom-data.uc.r.appspot.com/import/{attempt_id}/logs
'''


def dashboard_update(client_id, import_attempt):
    attempt_id = import_attempt['attempt_id']
    query = DASHBOARD_IMPORT_API.format_map({'attempt_id': attempt_id})
    response = iap.patch(query, client_id, json=import_attempt)
    return response


def dashboard_init_progress(client_id, import_attempt):
    attempt_id = import_attempt['attempt_id']
    query = DASHBOARD_IMPORT_API.format_map({'attempt_id': attempt_id})
    response = iap.put(query, client_id, json=import_attempt)
    return response


def _dashboard_log(client_id, attempt_id, message, level, time_logged=None):
    if not time_logged:
        time_logged = utils.utctime()

    return iap.post(
        DASHBOARD_LOG_API.format_map({'attempt_id': attempt_id}),
        client_id,
        json={
            'message': message,
            'level': level,
            'time_logged': time_logged
        }
    )


def dashboard_log_info(client_id, attempt_id, message, time=None):
    return _dashboard_log(client_id, attempt_id, message, 'info', time)


def dashboard_log_warning(client_id, attempt_id, message, time=None):
    return _dashboard_log(client_id, attempt_id, message, 'warning', time)


def dashboard_log_severe(client_id, attempt_id, message, time=None):
    return _dashboard_log(client_id, attempt_id, message, 'severe', time)
