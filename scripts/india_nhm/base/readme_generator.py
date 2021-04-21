# Copyright 2020 Google LLC
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

import os
import sys


class ReadMeGen():
    """
    """
    def __init__(self, dataset_name, dataset_description, data_level,
                 cols_dict):
        self.dataset_name = dataset_name
        self.dataset_description = dataset_description
        self.data_level = data_level
        self.cols_dict = cols_dict

    def _initial_stuff(self):
        INITIAL_STUFF = """# {dataset_description} - 2008 to 2020
        
## About the dataset
{dataset_description} for the years 2008 to 2020. Available in National Health Mission data portal.

Source: Health Information Management System (HIMS), Ministry of Health and Family Welfare

### Download URL
Available for download as xls and zip files.

[Performance of Key Indicators in HIMS ({data_level})](https://nrhm-mis.nic.in/hmisreports/frmstandard_reports.aspx)

### Overview
{dataset_description} is available for financial year starting from 2008. The xls files are under 'data/' folder.
The dataset contains key performance indicators of {dataset_description} for the particular financial year. 
"""

        return INITIAL_STUFF.format(
            dataset_description=self.dataset_description,
            data_level=self.data_level)

    def _cleaned_data(self):
        CLEANED_DATA = """
#### Cleaned data
- [{dataset_name}.csv]({dataset_name}.csv)

The cleaned csv has the following columns:
"""
        for k, v in self.cols_dict.items():
            CLEANED_DATA += "\n- {}: {}".format(v, k)

        return CLEANED_DATA.format(dataset_name=self.dataset_name)

    def _artifacts(self):
        ARTIFACTS = """

#### TMCF
- [{dataset_name}.tmcf]({dataset_name}.tmcf)

#### Scripts
- [preprocess.py](preprocess.py): Clean up data and generate TMCF file
        """

        return ARTIFACTS.format(dataset_name=self.dataset_name)

    def gen_readme(self):
        with open('README.md', 'w+') as out:
            out.write(self._initial_stuff())
            out.write(self._cleaned_data())
            out.write(self._artifacts())
