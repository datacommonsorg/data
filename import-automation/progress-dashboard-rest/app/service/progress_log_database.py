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
Database service for storing progress logs using Google Cloud Datastore
for storage. Log messages are optionally stored in a Google Cloud Storage
bucket using LogMessageManager.
"""

from app.service import base_database
from app.service import log_message_manager


class ProgressLogDatabase(base_database.BaseDatabase):
    """Database service for storing progress logs using Google Cloud Datastore
    for storage. Log messages are optionally stored in a Google Cloud Storage
    bucket using LogMessageManager.

    Attributes:
        See BaseDatabase.
        message_manager: LogMessageManager object to store log messages
    """
    kind = 'progress-log'

    def __init__(self, client=None, message_manager=None):
        """Constructs a LogDatabase.

        Args:
            client: datastore Client object to communicate with Datastore.
            message_manager: LogMessageManager object to store log messages.
        """
        super().__init__(ProgressLogDatabase.kind, client, 'log_id')
        if not message_manager:
            message_manager = log_message_manager.LogMessageManager()
        self.message_manager = message_manager

    def get(self, entity_id=None, make_new=False, load_content=False):
        """Retrieves a progress log from Datastore given its ID.

        Args:
            entity_id: See BaseDatabase.get.
            make_new: See BaseDatabase.get.
            load_content: Whether to load the message of the log from the
                bucket, as a boolean.

        Returns:
            See BaseDatabase.get. If load_content=True, the value of
            the message field of the returned entity will be loaded
            from the bucket. Otherwise, the value will be the URI of the
            message in the bucket.

        Raises:
            ValueError: See BaseDatabase.get.
            google.cloud.NotFound: See LogMessageManager.load_message.
        """
        log = super().get(entity_id, make_new)
        if log and not make_new and load_content:
            log['message'] = self.message_manager.load_message(log.key.name)
        return log

    def save(self, entity, save_content=False):
        """Saves a progress log to Datastore.

        Args:
            entity: See BaseDatabase.save.
            save_content: Whether to store the message of the log to a bucket,
                as a boolean.

        Returns:
            See BaseDatabase.save. If save_content=True, the value of
            the message field of the returned entity will be the URI of where
            the message is stored in the bucket. Otherwise, the value is not
            modified.
        """
        if save_content:
            entity['message'] = self.message_manager.save_message(
                entity['message'], entity.key.name)
        return super().save(entity)

    def load_logs(self, log_ids):
        """Loads the log messages of a set of logs from the bucket.

        The messages of the logs must have been previously saved
        using save(log, save_content=True).

        Args:
            log_ids: A set of log_id's specifying the progress logs whose
                messages are to be loaded, or any iterable container.

        Returns:
            A list of progress logs whose messages are loaded from the bucket
            each as a datastore Entity object.

        Raises:
            google.cloud.NotFound: See get.
        """
        logs = []
        for log_id in log_ids:
            logs.append(self.get(entity_id=log_id, load_content=True))
        return logs
