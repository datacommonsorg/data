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
System run resources associated with the endpoints
'/system_runs/<int:run_id>' and '/system_runs'.
"""

from enum import Enum
import http

import flask_restful
from flask_restful import reqparse

from app.service import system_run_database
from app.service import validation
from app import utils


class SystemRunStatus(Enum):
    """Allowed status of a system run.

    The status of a system run can only be one of these.
    """
    CREATED = 'created'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


SYSTEM_RUN_STATUS = frozenset(status.value for status in SystemRunStatus)


def set_system_run_default_values(system_run):
    """Sets default values for some fields of a system run.

    import_attempts is set to an empty list.
    status is set to 'created'.
    time_created is set to the current time.
    logs is set to an empty list.

    Args:
        system_run: System run as a dict.

    Returns:
        The same system run with the fields set, as a dict.
    """
    system_run.setdefault('import_attempts', [])
    system_run.setdefault('status', SystemRunStatus.CREATED.value)
    system_run.setdefault('time_created', utils.utctime())
    system_run.setdefault('logs', [])
    return system_run


class SystemRun(flask_restful.Resource):
    """Base class for an system run resource."""
    parser = reqparse.RequestParser()
    optional_fields = (
        ('run_id', str), ('repo_name',), ('branch_name',), ('pr_number', int),
        ('commit_sha',), ('time_created',), ('time_completed',),
        ('import_attempts', str, 'append'), ('logs', str, 'append'),
        ('status',)
    )
    utils.add_fields(parser, optional_fields, required=False)


class SystemRunByID(SystemRun):
    """API for managing system runs by run_id associated with the endpoint
    '/system_runs/<int:run_id>'.

    Attributes:
        database
        client
    """

    def __init__(self):
        self.database = system_run_database.SystemRunDatabase()
        self.client = self.database.client

    def get(self, run_id):
        """Retrieves a system run by its run_id.

        Args:
            run_id: ID of the system run as a string

        Returns:
            The system run with the run_id if successful as an Entity.
            Otherwise, (error message, error code), where the error message is
            a string and the error code is an int.
        """
        run = self.database.get(run_id)
        if not run:
            return NOT_FOUND_ERROR, http.HTTPStatus.NOT_FOUND
        return run

    def patch(self, run_id):
        """Modifies the value of a field of an existing system run.

        The run_id and import_attempts of an existing system run resource are
        forbidden to be patched.

        Args:
            run_id: ID of the system run as a string

        Returns:
            The system run with the run_id if successful as an Entity.
            Otherwise, (error message, error code), where the error message is
            a string and the error code is an int.
        """
        args = SystemRun.parser.parse_args()
        valid, err, code = validation.system_run_valid(args, run_id=run_id)
        if not valid:
            return err, code
        if 'run_id' in args or 'import_attempts' in args:
            return ('Cannot patch run_id or import_attempts',
                    http.HTTPStatus.FORBIDDEN)

        with self.client.transaction():
            run = self.database.get(run_id)
            if not run:
                return NOT_FOUND_ERROR, http.HTTPStatus.NOT_FOUND
            run.update(args)
            return self.database.save(run)


