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
Base class for system run, import attempt, and progress log resources.
"""

import flask_restful

from app.service import validation


class BaseResource(flask_restful.Resource):
    """Base class for system run, import attempt, and progress log resources."""
    @classmethod
    def _get_helper(cls, database, id_field, entity_id):
        """Retrieves an entity specified by its entity_id from the database.

        Args:
            database: Instance of one of SystemRunDatabase,
                ImportAttemptDatabase, and ProgressLogDatabase.
            id_field: Name of the ID field of the entity as a string.
            entity_id: ID of the entity as a string.

        Returns:
            The entity with the entity_id if successful as a datastore Entity
            object. Otherwise, (error message, error code), where the error
            message is a string and the error code is an int.
        """
        entity = database.get(entity_id)
        if not entity:
            return validation.get_not_found_error(id_field, entity_id)
        return entity
