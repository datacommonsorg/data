# Copyright 2025 Google LLC
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
"""Class to get execution time."""

import time


class Timer:
    """Class to track duration.

  Starts tracking time on creation of object or call to start()
  time() returns the seconds since start.
  stop() stopes the timer.


  Usage:
    duration = Timer()

    # some setup

    duration.start()
    # some processing

    # Get duration in seconds since start.
    print(f'Processing time: {duration.time():.4f}')
  """

    def __init__(self):
        self._end_time = 0
        self.start()

    def start(self):
        """Start the timer."""
        self._start_time = time.perf_counter()

    def stop(self):
        """Stop the timer."""
        self._end_time = time.perf_counter()

    def time(self) -> float:
        """Returns the time in seconds since start.
    If the timer has been stopped, returns the interval between start to stop."""
        if self._end_time > self._start_time:
            return self._end_time - self._start_time
        return time.perf_counter() - self._start_time
