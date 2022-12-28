# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Place cache caches [lat, lng] -> places mapping in a text file."""

from typing import Dict

from util import gcs_file


class PlaceCache:
    """Cache of (lat,lng) -> DC places mapping."""

    def __init__(self, path: str):
        self._path = path
        self._read = False
        self._updated = False
        self.cache = {}

    def read(self) -> None:
        """Read cache from GCS.

        Should only be called once. Will skip on subsequent calls.
        """
        if self._read:
            return
        try:
            with gcs_file.GcsFile(self._path, 'r') as file:
                raw_cache = file.read().decode()
                for line in raw_cache.split('\n'):
                    latlng, places = self.parse(line)
                    self.cache[latlng] = places
                self._read = True
        except gcs_file.BlobNotFoundError:
            self._read = True

    def update(self, cache: Dict):
        for k, v in cache.items():
            self.cache[k] = v

    def write(self):
        """Append to the existing cache. Can only be called once."""
        if self._updated:
            return
        # Cache dict -> lines of text.
        lines = []
        for latlng, places in self.cache.items():
            line = ','.join([str(latlng[0]), str(latlng[1])] + places)
            lines.append(line)
        # Write to gcs.
        with gcs_file.GcsFile(self._path, 'w') as file:
            file.write('\n'.join(lines).encode())
            self._updated = True

    def parse(self, line: str):
        """lat,lng,place1,place2... -> (lat, lng), [place1, place2 ...]"""
        vals = line.rstrip().split(',')
        if len(vals) < 2:
            raise Exception('Bad cache line %s. Please delete it.' % line)
        latlng = (float(vals[0]), float(vals[1]))
        return latlng, vals[2:]