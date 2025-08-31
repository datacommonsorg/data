# Copyright 2022 Google LLC
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
This Python Script downloads the EPA files for NonRoad Emissions,
into the input_files folder to be made available for further processing.
"""
import os
import sys
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

_COMMON_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(1, _COMMON_PATH)
from download import download_files
from download_config import *

INPUT_URLS = point_input_urls + nonpoint_input_urls + onroad_input_urls + nonroad_input_urls + event_urls
folders = point_folders + nonpoint_folders + onroad_folders + nonroad_folders

download_files(INPUT_URLS, folders)
