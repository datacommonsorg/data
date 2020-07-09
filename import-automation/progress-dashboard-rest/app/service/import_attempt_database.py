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
Database service for storing import attempts using Google Cloud Datastore for
storage.
"""

from app.service import base_database


class ImportAttemptDatabase(base_database.BaseDatabase):
    """Database service for storing import attempts using Google Cloud Datastore
    for storage.

    See BaseDatabase.
    """
    kind = 'import-attempt'

    def __init__(self, client=None):
        """Constructs an ImportAttemptDatabase.

        See BaseDatabase.
        """
        super().__init__(ImportAttemptDatabase.kind, client)

    def save(self, entity, id_field='attempt_id'):
        return super().save(entity, id_field)
