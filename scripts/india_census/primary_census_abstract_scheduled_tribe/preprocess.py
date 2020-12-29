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
import pandas as pd
from ..common.base import CensusPrimaryAbstractDataLoaderBase

CENSUS_DATA_COLUMN_START = 5


class CensusPrimaryCensusAbstractScheduledTribeDataLoader(
        CensusPrimaryAbstractDataLoaderBase):

    def _download_and_standardize(self):
        dtype = {'State': str, 'District': str}
        self.raw_df = pd.read_excel(self.data_file_path, dtype=dtype)
        self.census_columns = self.raw_df.columns[CENSUS_DATA_COLUMN_START:]

    def _get_base_name(self, row):
        name = "Count_" + row["populationType"] + "_" + "ScheduledTribe"
        return name

    def _get_base_constraints(self, row):
        constraints = "socialCategory: dcs:ScheduledTribe"
        return constraints


if __name__ == '__main__':
    data_file_path = os.path.join(os.path.dirname(__file__),
                                  'data/pca_state_distt_st.xls')

    metadata_file_path = os.path.join(
        os.path.dirname(__file__),
        '../common/primary_abstract_data_variables.csv')

    #These are basic statvars
    existing_stat_var = [
        "Count_Household",
        "Count_Person",
        "Count_Person_Urban",
        "Count_Person_Rural",
        "Count_Person_Male",
        "Count_Person_Female",
    ]

    #These are generated as part of `primary_census_abstract_data`
    #No need to create them again or include them in MCF
    existing_stat_var.extend([
        "Count_Person_ScheduledTribe",
        "Count_Person_ScheduledTribe_Urban",
        "Count_Person_ScheduledTribe_Rural",
        "Count_Person_ScheduledTribe_Male",
        "Count_Person_ScheduledTribe_Rural_Male",
        "Count_Person_ScheduledTribe_Urban_Male",
        "Count_Person_ScheduledTribe_Female",
        "Count_Person_ScheduledTribe_Urban_Female",
        "Count_Person_ScheduledTribe_Rural_Female",
    ])

    mcf_file_path = os.path.join(
        os.path.dirname(__file__),
        './IndiaCensus2011_Primary_Abstract_ScheduledTribe.mcf')
    tmcf_file_path = os.path.join(
        os.path.dirname(__file__),
        './IndiaCensus2011_Primary_Abstract_ScheduledTribe.tmcf')

    csv_file_path = os.path.join(
        os.path.dirname(__file__),
        './IndiaCensus2011_Primary_Abstract_ScheduledTribe.csv')
    loader = CensusPrimaryCensusAbstractScheduledTribeDataLoader(
        data_file_path=data_file_path,
        metadata_file_path=metadata_file_path,
        mcf_file_path=mcf_file_path,
        tmcf_file_path=tmcf_file_path,
        csv_file_path=csv_file_path,
        existing_stat_var=existing_stat_var,
        census_year=2011,
        dataset_name="Primary_Abstract_ScheduledTribe")
    loader.process()
