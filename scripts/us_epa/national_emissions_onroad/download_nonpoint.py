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

INPUT_URLS = [
    "https://gaftp.epa.gov/air/nei/2017/data_summaries/2017v1/2017neiApr_nonpoint.zip",
    "https://gaftp.epa.gov/air/nei/2014/data_summaries/2014v2/2014neiv2_nonpoint.zip",
    "https://gaftp.epa.gov/air/nei/2011/data_summaries/2011v2/2011neiv2_nonpoint.zip",
    "https://gaftp.epa.gov/air/nei/2008/data_summaries/2008neiv3_nonpoint.zip"
]
folders = [
    '2014_2014neiv2_nonpoint', '2008_2008neiv3_nonpoint'
]

download_files(INPUT_URLS,folders)
