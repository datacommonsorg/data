# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Functions for validating system runs, import attempts, and progress logs
without querying the database.

is_import_attempt_valid, is_system_run_valid, is_progress_log_valid, and
required_fields_present, _is_value_defined, _id_matches, _is_field_iso_utc
return a tuple consisting of:
1) a boolean indicating whether the import attempt is valid;
2) an error message, as a string, explaining the error;
3) the appropriate HTTP status code, as an int, for the error.
   If the first element is True, the other two are None.

get_not_found_error and get_patch_forbidden_error return a tuple consisting of:
1) an error message, as a string, explaining the error;
2) the appropriate HTTP status code, as an int, for the error.
"""

import datetime
import http

import app.model.system_run_model
from app import utils
from app.resource import system_run
from app.model import import_attempt_model
from app.model import progress_log_model


def is_import_attempt_valid(attempt, attempt_id=None):
    """Validates an import attempt.

    Checks that:
        1) If attempt_id is provided, the attempt_id field, if present, of the
           import attempt agrees with it.
        2) The status field, if present, of the import attempt has a value
           defined by IMPORT_ATTEMPT_STATUS.
        3) The time_created field, if present, is in ISO 8601 format with
            UTC timezone.
        4) The time_completed field, if present, is in ISO 8601 format with
            UTC timezone.

    Args:
        attempt: Import attempt to validate as a dict.
        attempt_id: The expected ID of the import attempt specified as a
            path variable in the URL, as a string.

    Returns:
        See module docstring.
    """
    valid, err, code = _id_matches(attempt, 'attempt_id', attempt_id)
    if not valid:
        return valid, err, code

    valid, err, code = _is_value_defined(
        attempt, 'status', import_attempt_model.IMPORT_ATTEMPT_STATUS)
    if not valid:
        return valid, err, code

    valid, err, code = _is_field_iso_utc(attempt, 'time_created')
    if not valid:
        return valid, err, code

    valid, err, code = _is_field_iso_utc(attempt, 'time_completed')
    if not valid:
        return valid, err, code

    return True, None, None


def is_system_run_valid(run, run_id=None):
    """Validates a system run.

    Checks that:
        1) If run_id is provided, the run_id field, if present, of the
           system run agrees with it.
        2) The status field, if present, of the system run has a value
           defined by SYSTEM_RUN_STATUS.
        3) The time_created field, if present, is in ISO 8601 format with
            UTC timezone.
        4) The time_completed field, if present, is in ISO 8601 format
        with UTC timezone.

    Args:
        run: System run to validate as a dict.
        run_id: The expected ID of the system run specified as a
            path variable in the URL, as a string..

    Returns:
        See module docstring.
    """
    valid, err, code = _id_matches(run, 'run_id', run_id)
    if not valid:
        return valid, err, code

    valid, err, code = _is_value_defined(
        run, 'status', app.model.system_run_model.SYSTEM_RUN_STATUS)
    if not valid:
        return valid, err, code

    valid, err, code = _is_field_iso_utc(run, 'time_created')
    if not valid:
        return valid, err, code

    valid, err, code = _is_field_iso_utc(run, 'time_completed')
    if not valid:
        return valid, err, code

    return True, None, None


def is_progress_log_valid(log, log_id=None):
    """Validates a progress log.

    Checks that:
        1) If log_id is provided, the log_id field, if present, of the
           progress log agrees with it.
        2) The level field, if present, of the progress log has a value
           defined by LOG_LEVELS.
        3) The time_logged field, if present, is in ISO 8601 format with
            UTC timezone.

    Args:
        log: Progress log to validate as a dict.
        log_id: The expected ID of the progress log specified as a
            path variable in the URL, as a string.

    Returns:
        See module docstring.
    """
    valid, err, code = _id_matches(log, 'log_id', log_id)
    if not valid:
        return valid, err, code

    valid, err, code = _is_value_defined(log, 'level',
                                         progress_log_model.LOG_LEVELS)
    if not valid:
        return valid, err, code

    valid, err, code = _is_field_iso_utc(log, 'time_logged')
    if not valid:
        return valid, err, code

    return True, None, None


def required_fields_present(fields, entity, all_present=True):
    """Checks if required fields are present in an entity.

    Args:
        fields: List of the required fields each as a string.
        entity: Entity supposed to contained the fields, as a dict.
        all_present: Whether all fields need to be present, as a boolean. If
            False, the function returns True as long as some of the fields
            are present.

    Returns:
        See module docstring.
    """
    absent = [field for field in fields if field not in entity]
    if ((all_present and absent) or
        (not all_present and len(absent) == len(fields))):
        return (False,
                f'missing {utils.list_to_str(absent)} in the request body',
                http.HTTPStatus.FORBIDDEN)
    return True, None, None


def get_not_found_error(id_field, entity_id):
    """Returns an error message and HTTP status code for a NOT FOUND error.

    Args:
        id_field: Name of the ID field whose value does not exist, as a string.
        entity_id: ID that does not exist, as a string.

    Returns:
        See module docstring.
    """
    return f'{id_field} {entity_id} not found', http.HTTPStatus.NOT_FOUND


def get_patch_forbidden_error(fields):
    """Returns an error message and HTTP status code for an error of attempting
    to patch fields not allowed to be patched.

    Args:
        fields: List of names of the fields being patched, each as a string.

    Returns:
        See module docstring.
    """
    return (f'It is not allowed to patch {utils.list_to_str(fields)}',
            http.HTTPStatus.FORBIDDEN)


def _id_matches(entity, id_field, path_id):
    """Checks if the ID field of an entity agrees with the ID specified in the
    URL as a path variable.

    Args:
        entity: Entity as a dict.
        id_field: Name of the ID field as a string.
        path_id: ID specified as a path variable in the URL, as a string. This
            is optional. If None, the function does not perform the check.

    Returns:
        See module docstring.
    """
    entity_id = entity.get(id_field, path_id)
    if path_id and path_id != entity_id:
        return (False, f'{id_field} {path_id} in path variable does not match '
                f'{id_field} {entity_id} in request body ',
                http.HTTPStatus.CONFLICT)
    return True, None, None


def _is_value_defined(entity, field_name, defined_values):
    """Checks if a value of a field of an entity is defined.

    Args:
        entity: Entity as a dict.
        field_name: Name of the field as a string. If this field does not exist
            in the entity, the function does not perform the check.
        defined_values: Collection of defined values. Each of the elements
            should be of the same type as the value of the field.

    Returns:
        See module docstring.
    """
    status = entity.get(field_name)
    if status and status not in defined_values:
        return (False, f'{field_name} {status} is not allowed',
                http.HTTPStatus.FORBIDDEN)
    return True, None, None


def _is_field_iso_utc(entity, field_name):
    """Checks if a field that holds a time string of an entity is valid
    if present.

    Args:
        entity: Entity that has the field, as a dict.
        field_name: Name of the field that holds the time string, as a string.
             If this field does not exist in the entity, the function does not
             perform the check.

    Returns:
        See module doc string.
    """
    time = entity.get(field_name)
    if time and not _is_iso_utc(time):
        return (False, f'{field_name} {time} is not in ISO 8601 format with '
                f'UTC timezone', http.HTTPStatus.FORBIDDEN)
    return True, None, None


def _is_iso_utc(time):
    """Checks if a time string is in ISO 8601 format with UTC timezone.

    Not every ISO 8601 format is accepted. This function primarily only accepts
    time strings of the form 'YYYY-MM-DDTHH:MM:SS.ffffff+00:00', e.g.,
    '2020-06-30T04:28:53.717569+00:00'. See
    https://docs.python.org/3/library/datetime.html#datetime.datetime.fromisoformat.

    Args:
        time: Time string to check.

    Returns:
        True, if the time string is valid. False, otherwise.
    """
    try:
        time = datetime.datetime.fromisoformat(time)
        if time.tzname() != 'UTC':
            return False
    except ValueError:
        return False
    return True
