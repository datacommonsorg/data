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
from ..common.base import CensusPrimaryAbstractDataLoaderBase


class CensusPrimaryCensusAbstractScheduleCasteDataLoader(
        CensusPrimaryAbstractDataLoaderBase):

    def _download_and_standardize(self):
        CensusPrimaryAbstractDataLoaderBase._download_and_standardize(self)
        #These columns don't exist in this dataset, since they are at
        #District level. We are census adding standard code with 0s
        #to make their census_location_id uniform
        self.raw_df["Subdistt"] = "00000"
        self.raw_df["Town/Village"] = "000000"
        self.raw_df["Ward"] = "0000"
        self.raw_df["EB"] = "000000"
        self.census_columns = self.raw_df.columns[5:]

    def _get_base_name(self, row):
        name = "Count_" + row["populationType"]
        name = name + "_" + "ScheduleCaste"
        return name

    def _get_base_constraints(self, row):
        constraints = "socialCategory: ScheduleCaste \n"
        return constraints


if __name__ == '__main__':
    data_file_path = os.path.join(os.path.dirname(__file__),
                                  'data/pca_state_distt_sc.xls')
    #data_file_path = "http://censusindia.gov.in/2011census/SC-ST/pca_state_distt_sc.xls"

    metadata_file_path = os.path.join(
        os.path.dirname(__file__),
        '../common/primary_abstract_data_variables.csv')

    existing_stat_var = []

    mcf_file_path = os.path.join(
        os.path.dirname(__file__),
        './IndiaCensus2011_Primary_Abstract_ScheduleCaste.mcf')
    tmcf_file_path = os.path.join(
        os.path.dirname(__file__),
        './IndiaCensus2011_Primary_Abstract_ScheduleCaste.tmcf')

    csv_file_path = os.path.join(
        os.path.dirname(__file__),
        './IndiaCensus2011_Primary_Abstract_ScheduleCaste.csv')
    loader = CensusPrimaryCensusAbstractScheduleCasteDataLoader(
        data_file_path=data_file_path,
        metadata_file_path=metadata_file_path,
        mcf_file_path=mcf_file_path,
        tmcf_file_path=tmcf_file_path,
        csv_file_path=csv_file_path,
        existing_stat_var=existing_stat_var,
        census_year=2011,
        dataset_name="Primary_Abstract_ScheduleCaste")
    loader.process()
