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
Mock classes of Google Datastore Client Library classes.
"""


class DatastoreEntityMock(dict):
    """Mock class of google.cloud.datastore.Entity."""

    def __init__(self, attempt_id, **kwargs):
        """Constructs a DatastoreEntityMock whose key is the attempt_id."""
        super().__init__()
        # Unused
        del kwargs
        self['attempt_id'] = attempt_id


class DatastoreClientMock:
    """Mock class of google.cloud.datastore.Client that uses a dictionary
    for storage and strings for keys."""

    def __init__(self, **kwargs):
        """Constructs a DatastoreClientMock."""
        # Unused
        del kwargs
        self.attempts = {}

    def get(self, attempt_id):
        """Retrieves the attempt with the given ID."""
        return self.attempts.get(attempt_id)

    def put(self, import_attempt):
        """Saves the given attempt into storage."""
        self.attempts[import_attempt['attempt_id']] = import_attempt

    def key(self, kind, attempt_id):
        """Converts the attempt_id into a key."""
        # Unused
        del kind
        return attempt_id

    def query(self, kind):
        """Returns a DatastoreQueryMock object that can be used filter
        existing import attempts."""
        # Unused
        del kind
        return DatastoreQueryMock(self)


class DatastoreQueryMock:
    """Mock class of google.cloud.datastore.Query."""

    def __init__(self, client_mock):
        """Constructs a DatastoreQueryMock with the given DatastoreClientMock
        object."""
        self.filters = []
        self.client_mock = client_mock

    def add_filter(self, key, operator, value):
        """Adds a filter key = value."""
        # Unused
        del operator
        self.filters.append((key, value))

    def fetch(self):
        """Applies the filers and returns an iterator of import attempts that
        pass."""
        ans = []
        for attempt in self.client_mock.attempts.values():
            found = True
            for key, value in self.filters:
                if attempt.get(key) != value:
                    found = False
                    break
            if found:
                ans.append(attempt)
        return iter(ans)
