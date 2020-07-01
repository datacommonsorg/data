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

from google.cloud import datastore

from app import configs


class ImportAttemptDatabase:
    """Database service for storing import attempts using Google Cloud Datastore
    for storage.

    The datastore Client will attempt to infer credentials based on
    host environment. See
    https://cloud.google.com/docs/authentication/production#finding_credentials_automatically.

    Attributes:
        client: A datastore Client to communicate with Datastore
    """
    kind = 'import-attempt'

    def __init__(self, project=configs.PROJECT_ID,
                 namespace=configs.DASHBOARD_NAMESPACE):
        """Constructs an ImportAttemptDatabase.

        Args:
            project: ID of the Google Cloud project as a string.
            namespace: namespace in which the import attempts will be stored
                as a string.
        """
        self.client = datastore.Client(project=project, namespace=namespace)

    def get_by_id(self, attempt_id, make_new=False):
        """Retrieves an import attempt from Datastore given its attempt_id.

        Args:
            attempt_id: ID of the attempt as a string.
            make_new: Whether to return a new attempt if the attempt_id does
                not exist as a boolean.

        Returns:
            The import attempt with the attempt_id as a datastore Entity. None,
            if the attempt_id does not exist and make_new is False.
        """
        key = self._get_key(attempt_id)
        import_attempt = self.client.get(key)
        if make_new and not import_attempt:
            return datastore.Entity(key, exclude_from_indexes=('logs',))
        return import_attempt

    def filter(self, kv_dict):
        """Retrieves a list of import attempts based on some criteria.

        Only equality is supported. For example,
        filter(kv_dict = {'import_name': 'cpi'}) retrieves all attempts whose
        import_name is 'cpi'.

        Args:
            kv_dict: Key-value mappings used for filtering as a dict.

        Returns:
            A list of import attempts each as a datastore Entity
            that pass the filter.
        """
        query = self.client.query(kind=ImportAttemptDatabase.kind)
        for key, value in kv_dict.items():
            query.add_filter(key, '=', value)
        return list(query.fetch())

    def _get_key(self, attempt_id):
        """Creates a datastore Key for an import attempt that
        has the attempt_id.

        Args:
            attempt_id: ID of the attempt as a string

        Returns:
            A datastore Key composed of the import attempt kind and the
            attempt_id.
        """
        return self.client.key(ImportAttemptDatabase.kind, attempt_id)

    def save(self, import_attempt):
        """Saves the import attempt as a datastore Entity to Datastore."""
        self.client.put(import_attempt)
        return import_attempt
