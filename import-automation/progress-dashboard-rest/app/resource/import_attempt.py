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
Import attempt resource associated with the endpoint
'/import_attempts/<string:attempt_id>'.
"""

from flask_restful import reqparse

from app import utils
from app.service import import_attempt_database
from app.service import validation
from app.model import import_attempt_model
from app.resource import base_resource

_MODEL = import_attempt_model.ImportAttempt


def set_import_attempt_default_values(import_attempt):
    """Sets default values for some fields of the import attempt and returns it.

    status is set to 'created'.
    time_created is set to the current time.
    logs is set to an empty list.
    """
    import_attempt.setdefault(
        _MODEL.status, import_attempt_model.ImportAttemptStatus.CREATED.value)
    import_attempt.setdefault(_MODEL.time_created, utils.utctime())
    import_attempt.setdefault(_MODEL.logs, [])
    return import_attempt


class ImportAttempt(base_resource.BaseResource):
    """Base class for an import attempt resource.

    Attributes:
        client: datastore Client object used to communicate with Datastore
        database: ImportAttemptDatabase object for querying and storing
            import attempts using the client
    """
    parser = reqparse.RequestParser()
    # The parser looks for these fields in the request body.
    # The Content-Type of the request must be application/json.
    optional_fields = ((_MODEL.attempt_id, str), (_MODEL.run_id,
                                                  str), (_MODEL.import_name,),
                       (_MODEL.absolute_import_name,), (_MODEL.provenance_url,),
                       (_MODEL.provenance_description,), (_MODEL.status,),
                       (_MODEL.time_created,), (_MODEL.time_completed,),
                       (_MODEL.logs, str, 'append'), (_MODEL.import_inputs,
                                                      dict, 'append'))
    utils.add_fields(parser, optional_fields, required=False)

    def __init__(self, client=None):
        """Constructs an ImportAttempt."""
        if not client:
            client = utils.create_datastore_client()
        self.client = client
        self.database = import_attempt_database.ImportAttemptDatabase(
            self.client)


class ImportAttemptByID(ImportAttempt):
    """API for managing import attempts by attempt_id associated with
    '/import/<string:attempt_id>'.

    See ImportAttempt.
    """

    def get(self, attempt_id):
        """Retrieves an import attempt by its attempt_id.

        Args:
            attempt_id: ID of the import attempt as a string

        Returns:
            The import attempt with the attempt_id if successful as a
            datastore Entity object. Otherwise, (error message, error code),
            where the error message is a string and the error code is an int.
        """
        return self._get_helper(self.database, _MODEL.attempt_id, attempt_id)

    def patch(self, attempt_id):
        """Modifies the value of a field of an existing import attempt.

        The attempt_id and run_id of an existing import attempt resource are
        forbidden to be patched.

        Args:
            attempt_id: ID of the import attempt as a string

        Returns:
            The import attempt with the attempt_id if successful as a
            datastore Entity object. Otherwise, (error message, error code),
            where the error message is a string and the error code is an int.
        """
        args = ImportAttempt.parser.parse_args()
        if _MODEL.attempt_id in args or _MODEL.run_id in args:
            return validation.get_patch_forbidden_error(
                (_MODEL.attempt_id, _MODEL.run_id))
        valid, err, code = validation.is_import_attempt_valid(
            args, attempt_id=attempt_id)
        if not valid:
            return err, code

        with self.client.transaction():
            import_attempt = self.database.get(attempt_id)
            if not import_attempt:
                return validation.get_not_found_error(_MODEL.attempt_id,
                                                      attempt_id)
            import_attempt.update(args)
            return self.database.save(import_attempt)
