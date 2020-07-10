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
System run list resource associated with the endpoint '/system_runs'.
"""

import flask_restful

from app import utils
from app.resource import system_run
from app.service import system_run_database
from app.service import validation


class SystemRunList(flask_restful.Resource):
    """API for querying a list of system runs based on some criteria and
    for creating new system runs."""

    def __init__(self):
        self.client = utils.create_datastore_client()
        self.database = system_run_database.SystemRunDatabase(
            client=self.client)

    def get(self):
        """Retrieves a list of system runs that pass the filter defined by
        the key-value mappings in the request body.

        Returns:
            A list of system runs each as a datastore Entity object.
        """
        args = system_run.SystemRun.parser.parse_args()
        return self.database.filter(args)

    def post(self):
        """Creates a new system run with the fields provided in the
        request body.

        Returns:
            The created system run as a datastore Entity object with
            run_id set. Otherwise, (error message, error code), where
            the error message is a string and the error code is an int.
        """
        args = system_run.SystemRun.parser.parse_args()
        valid, err, code = validation.system_run_valid(args)
        if not valid:
            return err, code

        # Only the API can modify these fields
        args.pop('run_id', None)
        args.pop('import_attempts', None)
        args.pop('logs', None)
        system_run.set_system_run_default_values(args)

        with self.client.transaction():
            run = self.database.get(make_new=True)
            run.update(args)
            return self.database.save(run)
