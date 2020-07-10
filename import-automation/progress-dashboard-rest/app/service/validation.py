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
                f'Import status {status} is not allowed',
                http.HTTPStatus.FORBIDDEN)
    time_created = attempt.get('time_created')
    if time_created and not utils.iso_utc(time_created):
        return ('time_created is not in ISO format with UTC timezone',
                http.HTTPStatus.FORBIDDEN)
    return True, None, None


def system_run_valid(system_run, run_id=None):
    return True, None, None


def required_fields_present(fields, entity):
    absent = [field for field in fields if field not in entity]
    if absent:
        return (False,
                f'missing {utils.list_to_str(absent)} in the request body',
                http.HTTPStatus.BAD_REQUEST)
    return True, None, None


def get_id_not_match_error(id_field, path_id, body_id):
    return (f'{id_field} ({path_id}) in path variable does not match '
            f'{id_field} ({body_id}) in request body ',
            http.HTTPStatus.CONFLICT)


def get_not_found_error(id_field, entity_id):
    return f'{id_field} ({entity_id}) not found', http.HTTPStatus.NOT_FOUND


def get_patch_forbidden_error(fields):
    return (f'It is not allowed to patch {utils.list_to_str(fields)}',
            http.HTTPStatus.FORBIDDEN)