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

import filecmp
import os
import json
import tempfile
import unittest
from os import path
import pandas as pd
from india_udise.udise_schools_having_computer_available.preprocess import UDISESchoolsHavingComputerAvailable
# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocess(unittest.TestCase):

    def test_create_csv(self):
        years = ["2013-14", "2015-16", "2019-20"]
        api_report_code = "3109"
        api_map_id = "80"

        data_folder = os.path.join(module_dir_, "test_data")

        expected_csv_file_path = os.path.join(
            data_folder,
            "expected_UDISEIndia_Schools_Having_Computer_Available.csv")
        expected_mcf_file_path = os.path.join(
            data_folder,
            "expected_UDISEIndia_Schools_Having_Computer_Available.mcf")

        csv_file_path = os.path.join(
            data_folder, "UDISEIndia_Schools_Having_Computer_Available.csv")
        mcf_file_path = os.path.join(
            data_folder, "UDISEIndia_Schools_Having_Computer_Available.mcf")

        base = UDISESchoolsHavingComputerAvailable(api_report_code, api_map_id,
                                                   data_folder, csv_file_path,
                                                   mcf_file_path, years)
        base.process()

        expected_csv_file = open(expected_csv_file_path)
        expected_csv_data = expected_csv_file.read()
        expected_csv_file.close()

        expected_mcf_file = open(expected_mcf_file_path)
        expected_mcf_data = expected_mcf_file.read()
        expected_mcf_file.close()

        csv_file = open(csv_file_path)
        csv_data = csv_file.read()
        csv_file.close()

        mcf_file = open(mcf_file_path)
        mcf_data = mcf_file.read()
        mcf_file.close()

        clean_df = pd.read_csv(csv_file_path, dtype=str)
        clean_df.fillna('', inplace=True)

        if path.exists(csv_file_path):
            os.remove(csv_file_path)
        if path.exists(mcf_file_path):
            os.remove(mcf_file_path)
        self.maxDiff = None
        self.assertEqual(expected_mcf_data, mcf_data)
        self.assertEqual(expected_csv_data, csv_data)

        # Comparing the specific numbers against the report on
        # https://dashboard.udiseplus.gov.in/#/reportDashboard/sReport

        # For Year 2015-16, SRINAGAR District(0103), Total
        # Count_School_HasComputer should be 524
        row = clean_df.loc[
            clean_df["StatisticalVariable"].eq("Count_School_HasComputer") &
            clean_df["UDISECode"].eq("0103") & clean_df["Period"].eq("2016-03")]
        self.assertEqual("524", row.iloc[0]["Value"])

        # For Year 2015-16, SRINAGAR District(0103), Count_School_HasComputer_UpperPrimarySchool_Grade1To8
        # Count_School_HasComputer_UpperPrimarySchool_Grade1To8 should be 203
        row = clean_df.loc[clean_df["StatisticalVariable"].eq(
            "Count_School_HasComputer_UpperPrimarySchool_Grade1To8") &
                           clean_df["UDISECode"].eq("0103") &
                           clean_df["Period"].eq("2016-03")]
        self.assertEqual("203", row.iloc[0]["Value"])

        # For Year 2015-16, SRINAGAR District(0103), Count_School_HasComputer_SeniorSecondarySchool_Grade1To10_DepartmentOfEducation
        # Count_School_HasComputer_SeniorSecondarySchool_Grade1To10_DepartmentOfEducation should be 23
        row = clean_df.loc[clean_df["StatisticalVariable"].eq(
            "Count_School_HasComputer_SeniorSecondarySchool_Grade1To10_DepartmentOfEducation"
        ) & clean_df["UDISECode"].eq("0103") & clean_df["Period"].eq("2016-03")]
        self.assertEqual("23", row.iloc[0]["Value"])

        # For Year 2019-20, Ladakh District(37), Total
        # Count_School_HasComputer should be 336
        row = clean_df.loc[
            clean_df["StatisticalVariable"].eq("Count_School_HasComputer") &
            clean_df["UDISECode"].eq("37") & clean_df["Period"].eq("2020-03")]
        self.assertEqual("336", row.iloc[0]["Value"])
