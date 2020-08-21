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
Configurations for the dashboard API.
"""

# ID of the Google Cloud project that enables Datastore
PROJECT_ID = 'datcom-data'
# Google Cloud Datastore namespace in which entities are stored
DASHBOARD_NAMESPACE = 'import-progress-dashboard'
# Google Cloud Storage bucket in which log messages are be stored
LOG_BUCKET_NAME = 'dashboard-progress-logs'
