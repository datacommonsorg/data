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
"""Unittest for timer.py"""

import time
import unittest

from timer import Timer


class TimerTest(unittest.TestCase):

    def test_timer_time(self):
        t = Timer()
        self.assertEqual(round(t.time(), 1), 0)
        time.sleep(0.1)
        # time returns the onterval in seconds from object creation
        self.assertEqual(round(t.time(), 1), 0.1)

    def test_timer_start(self):
        t = Timer()
        time.sleep(0.1)
        t.start()
        # Timer on start is reset to 0
        self.assertEqual(round(t.time(), 1), 0)
        time.sleep(0.1)
        # time() is the interval from start
        self.assertEqual(round(t.time(), 1), 0.1)

    def test_timer_stop(self):
        t = Timer()
        t.start()
        time.sleep(0.1)
        t.stop()
        self.assertEqual(round(t.time(), 1), 0.1)
        time.sleep(0.1)
        # time(0 still returns interval from start() to stop()
        # even if more time has elapsed.
        self.assertEqual(round(t.time(), 1), 0.1)
