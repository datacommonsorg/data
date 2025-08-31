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

_COMMON_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(1, _COMMON_PATH)
from download import download_files
from download_config import *

if (sys.argv[1].lower() == 'point'):
    INPUT_URLS = point_input_urls
    folders = point_folders
elif (sys.argv[1].lower() == 'nonpoint'):
    INPUT_URLS = nonpoint_input_urls
    folders = nonpoint_folders
elif (sys.argv[1].lower() == 'onroad'):
    INPUT_URLS = onroad_input_urls
    folders = onroad_folders
else:
    INPUT_URLS = nonroad_input_urls
    folders = nonroad_folders

download_files(INPUT_URLS, folders)