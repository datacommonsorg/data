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

from app import configs
from app.service import base_database
from app.service import log_message


class LogDatabase(base_database.BaseDatabase):
    """Database service for storing logs using Google Cloud Datastore
    for storage.

    See BaseDatabase.
    """
    kind = 'log'

    def __init__(self, client=None):
        """Constructs a LogDatabase.

        See BaseDatabase.
        """
        super().__init__(LogDatabase.kind, client)

    def get_by_id(self, entity_id=None, make_new=False, bucket=None, load_content=False):
        if load_content and not bucket:
            raise ValueError('load_content is True but no bucket is provided')
        log = super().get_by_id(entity_id, make_new)
        if log and load_content:
            log_message.load_log_messages((log,), bucket)
        return log

    def save(self, entity, id_field='log_id'):
        message = entity.pop('message')
        super().save(entity, id_field)
        entity['message'] = log_message.save_log_message(
            message, str(entity.id))
        return super().save(entity)
