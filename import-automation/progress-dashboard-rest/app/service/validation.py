import http

from app import utils
from app.resource import import_attempt


def import_attempt_valid(attempt, attempt_id=None):
    if attempt_id and attempt_id != attempt.get('attempt_id'):
        return (False,
                import_attempt.ID_NOT_MATCH_ERROR,
                http.HTTPStatus.CONFLICT)
    status = attempt.get('status')
    if status and status not in attempt.IMPORT_ATTEMPT_STATUS:
        return (False,
                'Import status {} is not allowed'.format(status),
                http.HTTPStatus.FORBIDDEN)
    time_created = attempt.get('time_created')
    if time_created and not utils.iso_utc(time_created):
        return ('time_created is not in ISO format with UTC timezone',
                http.HTTPStatus.FORBIDDEN)
    return True, None, None


def system_run_valid(system_run):
    return True, None, None