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

from app.service import base_database


def load_message(log_id, bucket):
    blob = bucket.blob(log_id)
    return blob.download_as_string().encode(blob.content_encoding)


def save_log_message(message, log_id, bucket):
    blob = bucket.blob(log_id)
    blob.upload_from_string(message)
    return log_id


class ProgressLogDatabase(base_database.BaseDatabase):
    """Database service for storing logs using Google Cloud Datastore
    for storage.

    See BaseDatabase.
    """
    kind = 'progress-log'

    def __init__(self, client=None):
        """Constructs a LogDatabase.

        See BaseDatabase.
        """
        super().__init__(ProgressLogDatabase.kind, client)

    def get_by_id(self, entity_id=None, make_new=False, bucket=None, load_content=False):
        if load_content and not bucket:
            raise ValueError('load_content is True but no bucket is provided')
        log = super().get_by_id(entity_id, make_new)
        if log and load_content:
            log['message'] = load_message(log.key.name, bucket)
        return log

    def save(self, entity, id_field='log_id', bucket=None, save_content=False):
        if save_content and not bucket:
            raise ValueError('save_content is True but no bucket is provided')
        entity[id_field] = entity.key.name
        if save_content:
            entity['message'] = save_log_message(entity['message'], entity.key.name)
        return super().save(entity, id_field)

    def load_logs(self, log_ids, bucket):
        return [self.load_log(log_id, bucket) for log_id in log_ids]

    def load_log(self, log_id, bucket):
        return self.get_by_id(
            entity_id=log_id, bucket=bucket, load_content=True)
