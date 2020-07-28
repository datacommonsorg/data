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
System run resource associated with the endpoint
'/system_runs/<string:run_id>'.
"""

import enum

import flask_restful
from flask_restful import reqparse

from app.model import system_run_model
from app.service import system_run_database
from app.service import validation
from app import utils

_MODEL = system_run_model.SystemRunModel


class SystemRunStatus(enum.Enum):
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
    system_run.setdefault(_MODEL.import_attempts, [])
    system_run.setdefault(_MODEL.status, SystemRunStatus.CREATED.value)
    system_run.setdefault(_MODEL.time_created, utils.utctime())
    system_run.setdefault(_MODEL.logs, [])
    return system_run


class SystemRun(flask_restful.Resource):
    """Base class for a system run resource.

    Attributes:
        client: datastore Client object used to communicate with Datastore
        database: SystemRunDatabase object for querying and storing
            system runs using the client
    """
    parser = reqparse.RequestParser()
    optional_fields = ((_MODEL.run_id, str), (_MODEL.repo_name,),
                       (_MODEL.branch_name,), (_MODEL.pr_number, int),
                       (_MODEL.commit_sha,), (_MODEL.time_created,),
                       (_MODEL.time_completed,), (_MODEL.import_attempts, str,
                                                  'append'),
                       (_MODEL.logs, str, 'append'), (_MODEL.status,))
    utils.add_fields(parser, optional_fields, required=False)

    def __init__(self):
        """Constructs a SystemRun."""
        self.client = utils.create_datastore_client()
        self.database = system_run_database.SystemRunDatabase(self.client)


class SystemRunByID(SystemRun):
    """API for managing system runs by run_id associated with the endpoint
    '/system_runs/<string:run_id>'.

    See SystemRun.
    """

    def get(self, run_id):
        """Retrieves a system run by its run_id.

        Args:
            run_id: ID of the system run as a string

        Returns:
            The system run with the run_id if successful as a
            datastore Entity object. Otherwise, (error message, error code),
            where the error message is a string and the error code is an int.
        """
        run = self.database.get(run_id)
        if not run:
            return validation.get_not_found_error(_MODEL.run_id, run_id)
        return run

    def patch(self, run_id):
        """Modifies the value of a field of an existing system run.

        The run_id and import_attempts of an existing system run are
        forbidden to be patched.

        Args:
            run_id: ID of the system run as a string

        Returns:
            The system run with the run_id if successful as a
            datastore Entity object. Otherwise, (error message, error code),
            where the error message is a string and the error code is an int.
        """
        args = SystemRunByID.parser.parse_args()
        if _MODEL.run_id in args or _MODEL.import_attempts in args:
            return validation.get_patch_forbidden_error(
                (_MODEL.run_id, _MODEL.import_attempts))
        valid, err, code = validation.is_system_run_valid(args, run_id=run_id)
        if not valid:
            return err, code

        with self.client.transaction():
            run = self.database.get(run_id)
            if not run:
                return validation.get_not_found_error(_MODEL.run_id, run_id)
            run.update(args)
            return self.database.save(run)
