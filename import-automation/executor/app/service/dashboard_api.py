import enum
import logging

from app import utils
from app import configs
from app.service import iap

_DASHBOARD_API_HOST = 'https://datcom-data.uc.r.appspot.com'

_DASHBOARD_RUN_LIST = _DASHBOARD_API_HOST + '/system_runs'
_DASHBOARD_RUN_BY_ID = _DASHBOARD_RUN_LIST + '/{attempt_id}'

_DASHBOARD_ATTEMPT_LIST = _DASHBOARD_API_HOST + '/import_attempts'
_DASHBOARD_ATTEMPT_BY_ID = _DASHBOARD_ATTEMPT_LIST + '/{attempt_id}'

_DASHBOARD_LOG_LIST = _DASHBOARD_API_HOST + '/logs'
_DASHBOARD_LOG_BY_ID = _DASHBOARD_LOG_LIST + '/{log_id}'

_STANDALONE = 'STANDALONE'


class LogLevel(enum.Enum):
    """Allowed log levels of a log.
    The level of a log can only be one of these.
    """
    CRITICAL = 'critical'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'
    DEBUG = 'debug'


class DashboardAPI:

    def __init__(self, client_id=None):
        if configs.standalone(): return
        if not client_id:
            client_id = configs.get_dashboard_oauth_client_id()
        self.client_id = client_id
        self.iap = iap.IAPRequest(client_id)

    def _log_helper(self,
                    message, level,
                    attempt_id=None, run_id=None, time_logged=None):
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

        return self.log(log)

    def log(self, log):
        if configs.standalone():
          if log['level'] == LogLevel.CRITICAL:
            logging.critical(log['message'])
          elif log['level'] == LogLevel.ERROR:
            logging.error(log['message'])
          elif log['level'] == LogLevel.WARNING:
            logging.warning(log['message'])
          elif log['level'] == LogLevel.INFO:
            logging.info(log['message'])
          else:
            logging.debug(log['message'])

          if 'return_code' in log:
            if log['return_code']:
              logging.error('Sub-process returned: ' + str(log['return_code']))
              logging.info('Sub-process stderr: ' + log['stderr'])
            else:
              logging.info('Sub-process succeeded')

          return ''

        response = self.iap.post(_DASHBOARD_LOG_LIST, json=log).json()
        response.raise_for_status()
        return response

    def critical(self, message, attempt_id=None, run_id=None, time_logged=None):
        return self._log_helper(
            message, LogLevel.CRITICAL, attempt_id, run_id, time_logged)

    def error(self, message, attempt_id=None, run_id=None, time_logged=None):
        return self._log_helper(
            message, LogLevel.ERROR, attempt_id, run_id, time_logged)

    def warning(self, message, attempt_id=None, run_id=None, time_logged=None):
        return self._log_helper(
            message, LogLevel.WARNING, attempt_id, run_id, time_logged)

    def info(self, message, attempt_id=None, run_id=None, time_logged=None):
        return self._log_helper(
            message, LogLevel.INFO, attempt_id, run_id, time_logged)

    def debug(self, message, attempt_id=None, run_id=None, time_logged=None):
        return self._log_helper(
            message, LogLevel.DEBUG, attempt_id, run_id, time_logged)

    def init_run(self, system_run):
        if configs.standalone(): return {'run_id': _STANDALONE}
        return self.iap.post(_DASHBOARD_RUN_LIST, json=system_run).json()

    def init_attempt(self, import_attempt):
        if configs.standalone(): return {'attempt_id': _STANDALONE}
        return self.iap.post(_DASHBOARD_ATTEMPT_LIST, json=import_attempt).json()

    def update_attempt(self, import_attempt, attempt_id=None):
        if configs.standalone(): return {'attempt_id': _STANDALONE}
        if not attempt_id:
            attempt_id = import_attempt['attempt_id']
        return self.iap.patch(
            _DASHBOARD_ATTEMPT_BY_ID.format_map({'attempt_id': attempt_id}),
            json=import_attempt).json()

    def update_run(self, system_run, run_id=None):
        if configs.standalone(): return {'run_id': _STANDALONE}
        if not run_id:
            run_id = system_run['run_id']
        return self.iap.patch(
            _DASHBOARD_RUN_BY_ID.format_map({'run_id': run_id}),
            json=system_run).json()


def construct_log(message, level=LogLevel.INFO, time_logged=None,
                  run_id=None, attempt_id=None, process=None):
    """Constructs a progress log that can be sent to the dashboard.

    Args:
        message: Log message as a string.
        level: Log level as a string.
        time_logged: Time logged in ISO format with UTC timezone as a string.
        run_id: ID of the system run to link to as a string.
        attempt_id: ID of the import attempt to link to as a string.
        process: subprocess.CompletedProcess object that has been executed and
            that needs to be logged.

    Returns:
        Constructed progress log ready to be sent to the dashboard as a dict.

    Raises:
        ValueError: Neither run_id nor attempt_id is specified.
    """
    if not run_id and not attempt_id:
        raise ValueError('Neither run_id nor attempt_id is specified')
    if not time_logged:
        time_logged = utils.utctime()
    log = {'message': message, 'level': level, 'time_logged': time_logged}
    if run_id:
        log['run_id'] = run_id
    if attempt_id:
        log['attempt_id'] = attempt_id
    if process:
        log['args'] = (utils.list_to_str(process.args, ' ')
                       if isinstance(process.args, list)
                       else process.args)
        log['return_code'] = process.returncode
        if process.returncode:
            log['level'] = LogLevel.CRITICAL
        if process.stdout:
            log['stdout'] = process.stdout
        if process.stderr:
            log['stderr'] = process.stderr
    return log
