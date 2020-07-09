import requests

from app import utils
from app.service import iap


DASHBOARD_API_HOST = 'https://datcom-data.uc.r.appspot.com'


DASHBOARD_RUN_LIST = DASHBOARD_API_HOST + '/system_runs'
DASHBOARD_RUN_BY_ID = DASHBOARD_RUN_LIST + '/{attempt_id}'

DASHBOARD_ATTEMPT_LIST = DASHBOARD_API_HOST + '/import_attempts'
DASHBOARD_ATTEMPT_BY_ID = DASHBOARD_ATTEMPT_LIST + '/{attempt_id}'

DASHBOARD_LOG_LIST = DASHBOARD_API_HOST + '/logs'
DASHBOARD_LOG_BY_ID = DASHBOARD_LOG_LIST + '/{log_id}'


def init_run(client_id, system_run):
    return iap.post(client_id, DASHBOARD_RUN_LIST, json=system_run).json()


def init_attempt(client_id, import_attempt):
    return iap.post(client_id, DASHBOARD_ATTEMPT_LIST, json=import_attempt).json()


def update_attempt(client_id, import_attempt, attempt_id=None):
    if not attempt_id:
        attempt_id = import_attempt['attempt_id']
    return iap.patch(
        client_id,
        DASHBOARD_ATTEMPT_BY_ID.format_map({'attempt_id': attempt_id}),
        json=import_attempt).json()


def update_run(client_id, system_run, run_id=None):
    if not run_id:
        run_id = system_run['run_id']
    return iap.patch(
        client_id,
        DASHBOARD_RUN_BY_ID.format_map({'run_id': run_id}),
        json=system_run).json()


def _log(client_id, message, level, attempt_id=None, run_id=None, time_logged=None):
    if not attempt_id and not run_id:
        raise ValueError('Neither attempt_id or run_id is specified')
    if not time_logged:
        time_logged = utils.utctime()

    log = {
        'message': message,
        'level': level,
        'time_logged': time_logged
    }
    if attempt_id:
        log['attempt_id'] = attempt_id
    if run_id:
        log['run_id'] = run_id

    return iap.post(client_id, DASHBOARD_LOG_LIST, json=log).json()


def log_info(client_id, message, attempt_id=None, run_id=None, time_logged=None):
    return _log(client_id, message, 'info', attempt_id, run_id, time_logged)


def log_warning(client_id, message, attempt_id=None, run_id=None, time_logged=None):
    return _log(client_id, message, 'warning', attempt_id, run_id, time_logged)


def log_severe(client_id, message, attempt_id=None, run_id=None, time_logged=None):
    return _log(client_id, message, 'severe', attempt_id, run_id, time_logged)
