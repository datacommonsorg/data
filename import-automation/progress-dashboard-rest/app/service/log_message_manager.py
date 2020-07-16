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
Storage service for storing progress log messages in
a Google Cloud Storage bucket.
"""

from app import utils


class LogMessageManager:
    """Storage service for storing progress log messages in a
    Google Cloud Storage bucket.

    Attributes:
        bucket: storage bucket object in which log messages are stored.
    """
    def __init__(self):
        """Constructs a LogMessageManager."""
        self.bucket = utils.create_storage_bucket()

    def load_message(self, log_id):
        """Loads the message of a progress log from the bucket.

        Args:
            log_id: ID of the progress log as a string

        Returns:
            The log message as a string.

        Raises:
            google.cloud.NotFound: The message of the progress log was not
            found in the bucket. This indicates that the message has never
            been saved.
        """
        return self.bucket.blob(log_id).download_as_string().decode('UTF-8')

    def save_message(self, message, log_id):
        """Saves the message of a progress log to the bucket.

        Args:
            message: The log message to save as a string.
            log_id: ID of the progress log with the message, as a string.

        Returns:
            URI of where the message is stored in the bucket as a string.
        """
        self.bucket.blob(log_id).upload_from_string(message)
        return log_id
