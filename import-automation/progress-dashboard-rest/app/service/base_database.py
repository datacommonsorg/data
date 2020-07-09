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
Database service for storing logs using Google Cloud Datastore for
storage.
"""

from google.cloud import datastore

from app import utils


class BaseDatabase:
    """Base class for a Database service that stores a kind of entities using
    Google Cloud Datastore for storage.

    The datastore Client will attempt to infer credentials based on
    host environment. See
    https://cloud.google.com/docs/authentication/production#finding_credentials_automatically.

    Attributes:
        kind: Kind of the entities to store
        client: A datastore Client to communicate with Datastore
    """
    def __init__(self, kind, client=None):
        """Constructs an BaseDatabase.

        Args:
            kind: Kind of entities stored
            client: Client to communicate with Datastore.
        """
        if not client:
            client = utils.create_datastore_client()
        self.kind = kind
        self.client = client

    def get_by_id(self, entity_id=None, make_new=False):
        """Retrieves an entity from Datastore given its entity_id.

        Args:
            entity_id: ID of the entity as a string or int.
            make_new: Whether to return a new entity if the entity_id does
                not exist, as a boolean. If entity_id is None, make_new must
                be True.

        Returns:
            The import attempt with the attempt_id as a datastore Entity. None,
            if the attempt_id does not exist and make_new is False.

        Raises:
            ValueError: entity_id is None and make_new is False
        """
        if not entity_id and not make_new:
            raise ValueError('entity_id is None and make_new is False')
        if not entity_id and make_new:
            entity_id = utils.get_id()
        key = self._get_key(entity_id)
        entity = self.client.get(key)
        if make_new and not entity:
            return datastore.Entity(key)
        return entity

    def _get_key(self, entity_id):
        """Creates a datastore Key for an entity that has the entity_id.

        Args:
            entity_id: ID of the entity as a string or int.

        Returns:
            A datastore Key composed of the entity kind and the entity_id.
        """
        if entity_id:
            return self.client.key(self.kind, entity_id)
        return self.client.key(self.kind)

    def filter(self, kv_dict):
        """Retrieves a list of entities based on some criteria.

        Only equality is supported. For example,
        filter(kv_dict = {'import_name': 'cpi'}) retrieves all entities whose
        import_name is 'cpi'.

        Args:
            kv_dict: Key-value mappings used for filtering as a dict.

        Returns:
            A list of entities each as a datastore Entity that pass the filter.
        """
        query = self.client.query(kind=self.kind)
        for key, value in kv_dict.items():
            query.add_filter(key, '=', value)
        return list(query.fetch())

    def save(self, entity, id_field=None):
        """Saves the entity to Datastore.

        Args:
            entity: Entity to save to Datastore, as a datastore Entity
            id_field: Name of the ID field as a string

        Returns:
            The saved entity as a datastore Entity with the key set. If the
            key is partial before invoking this function, an integer ID will
            be generated to make the key complete.
        """
        if id_field and id_field not in entity:
            entity[id_field] = entity.key.name
        self.client.put(entity)
        return entity
