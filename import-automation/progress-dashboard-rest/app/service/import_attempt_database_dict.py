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
Database service for storing import attempts using a dictionary for storage.
Used mainly for testing.
"""


class ImportAttemptDatabaseDict:
    """ Database service for storing import attempts using a dictionary
    for storage.

    Used mainly for testing.
    """
    # Storage for import attempts mapping attempt_id to attempts
    attempts = {}

    def reset():
        """Clears the storage dict."""
        ImportAttemptDatabaseDict.attempts = {}

    def get_by_id(self, attempt_id, make_new=False):
        """Retrieves an import attempt given its attempt_id.

        Args:
            attempt_id: ID of the attempt as a string.
            make_new: Whether to return a new attempt if the attempt_id does
                not exist as a boolean.

        Returns:
            The import attempt with the attempt_id as a dict. None,
            if the attempt_id does not exist and make_new is False.
        """
        attempt = ImportAttemptDatabaseDict.attempts.get(attempt_id)
        if make_new and not attempt:
            return ImportAttemptDatabaseDict.attempts.setdefault(attempt_id, {
                'attempt_id': attempt_id
            })
        return attempt

    def filter(self, kv_dict):
        """Retrieves a list of import attempts based on some criteria.

        Only equality is supported. For example,
        filter(kv_dict = {'import_name': 'cpi'}) retrieves all
        attempts whose import_name is 'cpi'.

        Args:
            kv_dict: Key-value mappings used for filtering as a dict.

        Returns:
            A list of import attempts each as a dict that pass the filter.
        """
        ans = []
        for attempt in ImportAttemptDatabaseDict.attempts.values():
            found = True
            for key, value in kv_dict.items():
                if attempt[key] != value:
                    found = False
                    break
            if found:
                ans.append(attempt)
        return ans

    def save(self, attempt):
        """Saves the import attempt represented as a dict."""
        ImportAttemptDatabaseDict.attempts[attempt['attempt_id']] = attempt
        return attempt
