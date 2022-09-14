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
This Python Script is config file
for us nces demographic private school.
"""

CSV_FILE_NAME = "us_nces_demographics_private_school.csv"
MCF_FILE_NAME = "us_nces_demographics_private_school.mcf"
TMCF_FILE_NAME = "us_nces_demographics_private_school.tmcf"
SCHOOL_TYPE = "private_school"
SPLIT_HEADER_ON_SCHOOL_TYPE = "[Private School]"

POSSIBLE_DATA_COLUMNS = [".*Students.*", ".*Teacher.*", "Percentage.*"]

EXCLUDE_DATA_COLUMNS = [
    "Total Students", "Prekindergarten and Kindergarten Students",
    "Ungraded Students", "Grades 1-8 Students", "Grades 9-12 Students"
]

POSSIBLE_PLACE_COLUMNS = [".*Lowest.*", ".*Highest.*", "Physical.*"]

EXCLUDE_PLACE_COLUMNS = []
