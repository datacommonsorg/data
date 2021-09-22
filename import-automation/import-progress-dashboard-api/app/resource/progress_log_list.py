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
Progress log list resource associated with the endpoint '/logs'.
See app/model/progress_log_model.py and app/resource/progress_log.py for what
a progress log is.
"""

import http

from app import utils
from app.resource import progress_log
from app.model import import_attempt_model
from app.model import system_run_model
from app.model import progress_log_model
from app.service import validation

_ATTEMPT = import_attempt_model.ImportAttempt
_RUN = system_run_model.SystemRun
_LOG = progress_log_model.ProgressLog


def add_log_to_entity(log_id, entity):
    """Adds a progress log pointer to an entity.

    Args:
        log_id: ID of the progress log as a string.
        entity: An import attempt or system run datastore Entity object.

    Returns:
        The same input entity with one log added, as a datastore Entity object.
    """
    log_ids = entity.setdefault(_ATTEMPT.logs, [])
    log_ids.append(log_id)
    return entity


class ProgressLogList(progress_log.ProgressLog):
    """API associated with the endpoint '/logs' for creating new progress logs.

    Attributes:
        See ProgressLog.
    """

    def post(self):
        """Creates a new progress log with the fields provided in the
        request body.

        Log level can only be one of the levels defined by LogLevel.
        A progress log must be at least linked to a system run and can
        optionally be linked to an import attempt.

        Returns:
            The created progress log as a datastore Entity object with
            log_id set. Otherwise, (error message, error code), where
            the error message is a string and the error code is an int.
        """
        args = progress_log.ProgressLog.parser.parse_args()
        args.pop(_LOG.log_id, None)
        args.setdefault('time_logged', utils.utctime())

        valid, err, code = validation.is_progress_log_valid(args)
        if not valid:
            return err, code

        valid, err, code = validation.required_fields_present(
            (_LOG.run_id, _LOG.level, _LOG.message), args)
        if not valid:
            return err, code

        run_id = args.get('run_id')
        attempt_id = args.get('attempt_id')
        run = None
        attempt = None

        with self.client.transaction():
            if run_id:
                run = self.run_database.get(run_id)
                if not run:
                    return validation.get_not_found_error(_RUN.run_id, run_id)
            if attempt_id:
                attempt = self.attempt_database.get(attempt_id)
                if not attempt:
                    return validation.get_not_found_error(
                        _ATTEMPT.attempt_id, attempt_id)
            if run and attempt:
                if attempt_id not in run[_RUN.import_attempts]:
                    return ('The import attempt specified by the attempt_id '
                            f'{attempt_id} in the request body is not '
                            'executed by the system run specified by the '
                            f'run_id {run_id} in the request body',
                            http.HTTPStatus.CONFLICT)

            log = self.log_database.get(make_new=True)
            log.update(args)
            log = self.log_database.save(log, save_content=True)
            if run:
                self.run_database.save(add_log_to_entity(log.key.name, run))
            if attempt:
                self.attempt_database.save(
                    add_log_to_entity(log.key.name, attempt))
            return log
