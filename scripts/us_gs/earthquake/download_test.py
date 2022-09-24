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
"""Tests for download.py"""

import datetime
import os
import sys
from typing import Dict
import unittest

from scripts.us_gs.earthquake.download import count_and_download
from scripts.us_gs.earthquake.download import filename

MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(0, MODULE_DIR)


class USGSEarthquakeDownloadTest(unittest.TestCase):

    def test_download_2011_03_11(self):
        date_from = datetime.datetime.strptime('2011-03-11', '%Y-%m-%d').date()
        date_until = datetime.datetime.strptime('2011-03-12', '%Y-%m-%d').date()
        try:
            diff = count_and_download(date_from, date_until, MODULE_DIR)
            self.assertEqual(len(diff), 0)
        finally:
            os.remove(
                os.path.join(MODULE_DIR, filename(date_from, date_until, 0)))
