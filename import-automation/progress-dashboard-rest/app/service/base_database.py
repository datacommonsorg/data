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
Base class for a Database service that stores some kind of entities using
Google Cloud Datastore for storage.
"""

from google.cloud import datastore

from app import utils


class BaseDatabase:
    """Base class for a Database service that stores some kind of entities using
    Google Cloud Datastore for storage.

    New datastore Entity objects must be created using get(make_new=True).

    The datastore Client will attempt to infer credentials based on
    host environment. See
    https://cloud.google.com/docs/authentication/production#finding_credentials_automatically.

    Attributes:
        kind: Kind of entities to store as a string
        client: datastore Client object to communicate with Datastore
    """

    def __init__(self, kind, client=None, id_field=None):
        """Constructs an BaseDatabase.

        Args:
            kind: Kind of entities stored
            client: Client to communicate with Datastore.
            id_field: Name of the ID field of an entity as a string.
                Every operation checks if id_field is not already a field in the
                entity. If not, it will be added to the entity with the value of
                the key name.
        """
        if not client:
            client = utils.create_datastore_client()
        self.kind = kind
        self.client = client
        self.id_field = id_field

    def get(self, entity_id=None, make_new=False):
        """Retrieves an entity from Datastore given its entity_id.

        Args:
            entity_id: ID of the entity as a string.
            make_new: Whether to return a new entity if the entity_id does
                not exist, as a boolean. If entity_id is None, make_new must
                be True.

        Returns:
            The entity with the entity_id, as a datastore Entity. None,
            if the entity_id does not exist and make_new is False.

        Raises:
            ValueError: entity_id is None and make_new is False
        """
        if not entity_id and not make_new:
            raise ValueError('entity_id is None and make_new is False')
        if not entity_id:
            entity = datastore.Entity(self._get_key(utils.get_id()))
        else:
            entity = self.client.get(self._get_key(entity_id))
            if not entity:
                if make_new:
                    entity = datastore.Entity(self._get_key(utils.get_id()))
                else:
                    return None
        entity[self.id_field] = entity.key.name
        return entity

    def _get_key(self, entity_id):
        """Creates a datastore Key for an entity that has the entity_id.

        Args:
            entity_id: ID of the entity as a string.

        Returns:
            A datastore Key object composed of the entity kind and
            the entity_id.
        """
        if entity_id:
            return self.client.key(self.kind, entity_id)
        return self.client.key(self.kind)

    def filter(self, kv_dict):
        """Retrieves a list of entities based on some criteria.

        Only equality is supported. For example,
        filter(kv_dict={'foo': 'bar'}) retrieves all entities whose
        foo field is 'bar'.

        Args:
            kv_dict: Key-value mappings used for filtering as a dict.

        Returns:
            A list of entities that pass the filter each as a datastore Entity.
        """
        query = self.client.query(kind=self.kind)
        for key, value in kv_dict.items():
            query.add_filter(key, '=', value)
        return list(query.fetch())

    def save(self, entity):
        """Saves the entity to Datastore.

        Args:
            entity: Entity to save to Datastore as a datastore Entity. The
                entity must have a complete key.

        Returns:
            The saved entity as a datastore Entity.

        Raises:
            ValueError: Key of the entity is not set or is partial.
        """
        if not entity.key or not entity.key.name:
            raise ValueError('Key of the entity is not set or is partial.')
        if self.id_field and self.id_field not in entity:
            entity[self.id_field] = entity.key.name
        self.client.put(entity)
        return entity
