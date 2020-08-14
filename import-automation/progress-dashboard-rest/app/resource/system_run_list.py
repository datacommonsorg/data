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
System run lists, the resource associated with the endpoint '/system_runs'.
"""

import http

import flask
from werkzeug import exceptions

from app import utils
from app.resource import system_run
from app.service import validation
from app.model import system_run_model


class SystemRunList(system_run.SystemRun):
    """API for querying a list of system runs based on some criteria and
    for creating new system runs.

    See SystemRun.
    """
    _parser = system_run.SystemRun.parser.copy()
    utils.add_fields(_parser, (('limit', int), ('order', str, 'append')),
                     required=False)

    def get(self):
        """Retrieves a list of system runs that pass the filter defined by
        the key-value mappings in the request body.

        The filter can only contain fields defined by SystemRun.

        This endpoint accepts two url arguments: limit and order.
        limit is an integer that specifies the maximum number of system runs
        returned and order is a list of field names to order the returned
        system runs by. Prepend - to a field name to sort it in
        descending order. The list can be specified by repeated keys. E.g.,
        ?order=status&order=-time_created.

        Returns:
            A list of system runs each as a datastore Entity object
            if successful. Otherwise, (error message, error code), where
            the error message is a string and the error code is an int.
        """
        args = None
        try:
            args = SystemRunList._parser.parse_args(strict=True)
        except exceptions.BadRequest as exc:
            return exc.description, exc.code
        order = args.pop('order', ())
        limit = args.pop('limit', None)
        for field in args:
            if field not in system_run_model.FIELDS:
                return (f'Field {field} is not a valid field for a system run',
                        http.HTTPStatus.BAD_REQUEST)
        return self.database.filter(args, order=order, limit=limit)

    def post(self):
        """Creates a new system run with the fields provided in the
        request body.

        Returns:
            The created system run as a datastore Entity object with
            run_id set. Otherwise, (error message, error code), where
            the error message is a string and the error code is an int.
        """
        args = system_run.SystemRunByID.parser.parse_args()
        valid, err, code = validation.is_system_run_valid(args)
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
