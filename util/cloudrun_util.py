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
"""Utility functions for Cloud Run environment."""

import os


def running_on_cloudrun() -> bool:
    """Check if running on Cloud Run.
    
    Returns:
        bool: True if running on Cloud Run services or jobs, False otherwise.
    """
    return bool(os.getenv('K_SERVICE')) or bool(os.getenv('CLOUD_RUN_JOB'))
