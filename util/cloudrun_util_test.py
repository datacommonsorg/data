# Copyright 2023 Google LLC
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
"""Tests for util.cloudrun_util module."""

import os
import unittest
from unittest import mock

from util import cloudrun_util


class CloudRunUtilTest(unittest.TestCase):
    """Tests for Cloud Run utility functions."""

    def test_running_on_cloudrun_when_k_service_is_set(self):
        """Test that running_on_cloudrun returns True when K_SERVICE is set."""
        with mock.patch.dict(os.environ, {'K_SERVICE': 'my-service'}):
            self.assertTrue(cloudrun_util.running_on_cloudrun())

    def test_running_on_cloudrun_when_k_service_is_not_set(self):
        """Test that running_on_cloudrun returns False when K_SERVICE is not set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            # Ensure K_SERVICE is not in environment
            if 'K_SERVICE' in os.environ:
                del os.environ['K_SERVICE']
            self.assertFalse(cloudrun_util.running_on_cloudrun())

    def test_running_on_cloudrun_with_empty_k_service_value(self):
        """Test that running_on_cloudrun returns False when K_SERVICE is empty."""
        with mock.patch.dict(os.environ, {'K_SERVICE': ''}):
            self.assertFalse(cloudrun_util.running_on_cloudrun())
