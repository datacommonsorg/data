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
Import attempt list resource associated with the endpoint '/import_attempts'.
"""

from app.resource import import_attempt
from app.service import system_run_database
from app.service import validation
from app.model import import_attempt_model
from app.model import system_run_model

_ATTEMPT = import_attempt_model.ImportAttemptModel
_RUN = system_run_model.SystemRunModel


class ImportAttemptList(import_attempt.ImportAttempt):
    """API for querying a list of import attempts based on some criteria
    and creating new import attempts.

    For methods that require a request body, the content type of the request
    must be 'application/json'.

    Attributes:
        See ImportAttempt.
        run_database: SystemRunDatabase object for querying system runs
            using the client.
    """

    def __init__(self, client=None):
        """Constructs an ImportAttemptList."""
        super().__init__(client)
        self.run_database = system_run_database.SystemRunDatabase(self.client)

    def get(self):
        """Retrieves a list of import attempts that pass the filter defined by
        the key-value mappings in the request body."""
        args = import_attempt.ImportAttempt.parser.parse_args()
        return self.database.filter(args)

    def post(self):
        """Creates a new import attempt with the fields provided in the
        request body.

        run_id must be present in the request body to link the import attempt
        to a system run.

        Returns:
            The created import attempt as a datastore Entity object with
            attempt_id set. Otherwise, (error message, error code), where
            the error message is a string and the error code is an int.
        """
        args = import_attempt.ImportAttempt.parser.parse_args()
        valid, err, code = validation.is_import_attempt_valid(args)
        if not valid:
            return err, code
        present, err, code = validation.required_fields_present(
            (_ATTEMPT.run_id,), args)
        if not present:
            return err, code

        # Only the API can modify these fields
        args.pop(_ATTEMPT.attempt_id, None)
        args.pop(_ATTEMPT.logs, None)
        import_attempt.set_import_attempt_default_values(args)

        with self.client.transaction():
            # The system run pointed to by this import attempt needs to
            # point back at the import attempt.
            run_id = args[_ATTEMPT.run_id]
            run = self.run_database.get(run_id)
            if not run:
                return validation.get_not_found_error(_ATTEMPT.run_id, run_id)

            attempt = self.database.get(make_new=True)
            attempt.update(args)
            self.database.save(attempt)

            attempts = run.setdefault(_RUN.import_attempts, [])
            attempts.append(attempt.key.name)
            self.run_database.save(run)

            return attempt
