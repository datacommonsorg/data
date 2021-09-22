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
"""General class to shard while writing strings to file."""


class ShardingWriter:
    """Helper class for writing strings to sharded files."""

    def __init__(self, base_path, file_extension='mcf', shard_size=104857600):
        self._base_path = base_path
        self._file_extension = file_extension
        self._shard_size = shard_size
        self._shard_id = 0
        self._nbytes = 0
        self._fptr = None

    def write(self, data):
        """Write to current sharded file if the file has not exceeded size limit."""
        if not self._fptr:
            dest_file = '%s_%s.%s' % (self._base_path, self._shard_id,
                                      self._file_extension)
            self._fptr = open(dest_file, 'w')

        self._fptr.write(data)
        self._nbytes += len(data)
        if self._nbytes > self._shard_size:
            # Rollover shard.
            self._fptr.close()
            self._fptr = None
            self._nbytes = 0
            self._shard_id += 1
