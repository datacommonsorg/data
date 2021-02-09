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
import json
import csv
import copy
import pandas as pd
import numpy as np
import tempfile
import urllib.request
from ..common.utils import title_case
from ..common.generic_base import CensusGenericDataLoaderBase


class CensusPrimaryReligiousDataLoader(CensusGenericDataLoaderBase):
    """An object that represents Census Data and its variables.
    
    Attributes:
        census_columns (list): It will have all the data column names of a dataset
        census_year : Census year
        csv_file_path : Path where cleaned csv file will be saved
        data_file_path : Input XLS file from Census of India. Can be url or local path.
        dataset_name : Census dataset name. Eg:Primary_Abstract_Data
        existing_stat_var (list): List of existing stat vars that we don't need to generate
        mcf (list): Description
        mcf_file_path : Description
        metadata_file_path : Description
        raw_df : Raw census data as dataframe
        stat_var_index (dict): local storage for census column name and corresponding statvar
        tmcf_file_path : Path where generated tmcf file will be saved
        data_categories: List data categories for which data is defined
        data_category_column: Name of the data category column

    """

    def __init__(self, data_file_path, metadata_file_path, mcf_file_path,
                 tmcf_file_path, csv_file_path, existing_stat_var, census_year,
                 dataset_name, data_categories, data_category_column):
        """
        Constructor
        
        Args:
            data_file_path :  Input XLS file from Census of India. Can be url or local path
            metadata_file_path : Meta data csv file which has attribute details
            mcf_file_path : Path where generated mcf file will be saved
            tmcf_file_path : Path where generated tmcf file will be saved
            csv_file_path : Path where cleaned csv file will be saved
            existing_stat_var : List of existing stat vars that we don't need to generate
            census_year : Census Year
            dataset_name : Census dataset name. Eg:Primary_Abstract_Data
            data_categories: List data categories for which data is defined
            data_category_column: Name of the data category column
        """
        self.data_file_path = data_file_path
        self.metadata_file_path = metadata_file_path
        self.mcf_file_path = mcf_file_path
        self.csv_file_path = csv_file_path
        self.tmcf_file_path = tmcf_file_path
        self.existing_stat_var = existing_stat_var
        self.census_year = census_year
        self.dataset_name = dataset_name
        self.raw_df = None
        self.stat_var_index = {}
        self.census_columns = []
        self.data_categories = data_categories
        self.data_category_column = data_category_column

    def _format_data(self):

        def stat_var_index_key(row, data_category_column=None):
            key = "{0}_{1}".format(row["columnName"], row["TRU"])
            if data_category_column:
                key = key + "_" + row[data_category_column]
            return key

        # Generate Census locationid
        self.raw_df["census_location_id"] = self.raw_df.apply(
            self._format_location, axis=1)

        # Remove the unwanted columns. They are census codes which we dont use
        # State,District,Subdistt,Town/Village,Ward,EB
        # We delete them only if they exists
        # From pandas documentation:
        # If errors=‘ignore’, suppress error and only existing labels are dropped
        self.raw_df.drop(
            ["State", "District", "Subdistt", "Town/Village", "Name"],
            axis=1,
            inplace=True,
            errors='ignore')

        # Once the above columns are dropped, we will have
        # First column = TRU/placeOfResidence
        # Second column = data_category_column
        # 3-N are the actual values. Let's get value columns
        value_columns = list(self.raw_df.columns[2:-1])

        # Convert the data_category_column to title case
        self.raw_df[self.data_category_column] = self.raw_df[
            self.data_category_column].apply(lambda x: title_case(x))

        # Converting rows in to columns. So the final structure will be
        # Name,TRU,columnName,value
        self.raw_df = self.raw_df.melt(
            id_vars=["census_location_id", "TRU", self.data_category_column],
            value_vars=value_columns,
            var_name='columnName',
            value_name='Value')

        # Add corresponding StatisticalVariable, based on columnName and TRU
        self.raw_df['StatisticalVariable'] = self.raw_df.apply(
            lambda row: self._get_stat_var_name(self.stat_var_index[
                stat_var_index_key(row, self.data_category_column)]),
            axis=1)

        # Add the census year
        self.raw_df['Year'] = self.census_year

        # Remove data_category_column as its not required
        self.raw_df.drop([self.data_category_column],
                         axis=1,
                         inplace=True,
                         errors='ignore')

        # Export it as CSV. It will have the following columns
        # Name,TRU,columnName,value,StatisticalVariable,Year
        self.raw_df.to_csv(self.csv_file_path, index=False, header=True)

    def _get_base_name(self, row):
        # To make the name meaningful add Religion to the
        # the name of the stat var
        name = "Count_" + row["populationType"] + "_Religion"
        return name

    def _get_stat_var_name(self, name):
        return "dcid:indianCensus/{}".format(name)

    def _get_measured_property_name(self, name):
        return "dcs:indianCensus/{}".format(name)

    def _create_variable(self,
                         data_row,
                         place_of_residence=None,
                         data_category=None):
        row = copy.deepcopy(data_row)
        name_array = []

        name_array.append(self._get_base_name(row))

        if data_category:
            name_array.append(title_case(data_category))
            row["description"] = row["description"] + " - " + data_category

        if row["age"] == "YearsUpto6":
            name_array.append("YearsUpto6")

        if row["socialCategory"] == "ScheduledCaste":
            name_array.append("ScheduledCaste")
        if row["socialCategory"] == "ScheduledTribe":
            name_array.append("ScheduledTribe")

        if row["workerStatus"] == "Worker":
            if row["workerClassification"] == "MainWorker":
                name_array.append("MainWorker")
                if row["workCategory"] != "":
                    name_array.append(row["workCategory"])

            elif row["workerClassification"] == "MarginalWorker":
                name_array.append("MarginalWorker")

                if row["workCategory"] != "":
                    name_array.append(row["workCategory"])

                if row["workPeriod"] == "[Month - 3]":
                    name_array.append("WorkedUpto3Months")

                if row["workPeriod"] == "[Month 3 6]":
                    name_array.append("Worked3To6Months")
            else:
                name_array.append("Workers")

        elif row["workerStatus"] == "NonWorker":
            name_array.append("NonWorker")

        if place_of_residence == "Urban":
            name_array.append("Urban")
            row["description"] = row["description"] + " - Urban"

        elif place_of_residence == "Rural":
            name_array.append("Rural")
            row["description"] = row["description"] + " - Rural"

        if row["gender"] == "Male":
            name_array.append("Male")

        elif row["gender"] == "Female":
            name_array.append("Female")

        name = "_".join(name_array)
        row["name"] = name

        key = "{0}_{1}".format(
            row["columnName"],
            place_of_residence if place_of_residence != None else "Total")

        if data_category:
            key = key + "_" + title_case(data_category)

        self.stat_var_index[key] = name
        row["StatisticalVariable"] = self._get_stat_var_name(name)
        row["measuredProperty"] = self._get_measured_property_name(name)
        self.mcf.append(row)

        stat_var = self.GENERIC_TEMPLATE_STAT_VAR.format(**dict(row))

        return name, stat_var

    def _create_mcf(self):
        self.mcf = []
        with open(self.metadata_file_path) as csvfile:
            reader = csv.DictReader(csvfile)
            with open(self.mcf_file_path, 'w+', newline='') as f_out:
                for data_row in reader:
                    for place_of_residence in [None, "Urban", "Rural"]:
                        if len(self.data_categories) == 0:
                            name, stat_var = self._create_variable(
                                data_row,
                                place_of_residence,
                                data_category=None)
                            # If the statvar already exists then we don't
                            # need to recreate it
                            if name in self.existing_stat_var:
                                pass
                            # we need to create statvars only for those columns that
                            # exist in the current data file
                            elif data_row[
                                    "columnName"] not in self.census_columns:
                                pass
                            else:
                                f_out.write(stat_var)
                        else:
                            for data_category in self.data_categories:
                                name, stat_var = self._create_variable(
                                    data_row,
                                    place_of_residence,
                                    data_category=data_category)
                                # If the statvar already exists then we don't
                                # need to recreate it
                                if name in self.existing_stat_var:
                                    pass
                                # We need to create statvars only for those columns that
                                # exist in the current data file
                                elif data_row[
                                        "columnName"] not in self.census_columns:
                                    pass
                                else:
                                    f_out.write(stat_var)


if __name__ == '__main__':

    metadata_file_path = os.path.join(
        os.path.dirname(__file__),
        '../common/primary_abstract_data_variables.csv')

    # These are basic statvars
    existing_stat_var = []

    # These are generated as part of `primary_census_abstract_data`
    # No need to create them again or include them in MCF
    existing_stat_var.extend([])

    data_categories = [
        "Total", "Hindu", "Muslim", "Christian", "Sikh", "Buddhist", "Jain",
        "Other religions and persuasions", "Religion not stated"
    ]

    mcf_file_path = os.path.join(
        os.path.dirname(__file__),
        './IndiaCensus2011_Primary_Abstract_Religion.mcf')
    tmcf_file_path = os.path.join(
        os.path.dirname(__file__),
        './IndiaCensus2011_Primary_Abstract_Religion.tmcf')
    csv_file_path = os.path.join(
        os.path.dirname(__file__),
        './IndiaCensus2011_Primary_Abstract_Religion.csv')

    # This is the data file for India
    data_file_path = os.path.join(os.path.dirname(__file__),
                                  'data/RL-0000.xlsx')

    # Create the MCF. TMCF and Final CSV file for
    # India level data file
    # TODO: Currently we are using only a meaninful unique name for
    # statvar. The schema is not defined. It needs to be defined.
    loader = CensusPrimaryReligiousDataLoader(
        data_file_path=data_file_path,
        metadata_file_path=metadata_file_path,
        mcf_file_path=mcf_file_path,
        tmcf_file_path=tmcf_file_path,
        csv_file_path=csv_file_path,
        existing_stat_var=existing_stat_var,
        census_year=2011,
        dataset_name="Primary_Abstract_Religion",
        data_categories=data_categories,
        data_category_column="Religion")
    loader.process()

    # Iterate through state files and just create the final CSV file
    # We already have the MCF and TMCF file

    state_data_files = [
        "RL-0100", "RL-0200", "RL-0300", "RL-0400", "RL-0500", "RL-0600",
        "RL-0700", "RL-0800", "RL-0900", "RL-1000", "RL-1100", "RL-1200",
        "RL-1300", "RL-1400", "RL-1500", "RL-1600", "RL-1700", "RL-1800",
        "RL-1900", "RL-2000", "RL-2100", "RL-2200", "RL-2300", "RL-2400",
        "RL-2500", "RL-2600", "RL-2700", "RL-2800", "RL-2900", "RL-3000",
        "RL-3100", "RL-3200", "RL-3300", "RL-3400", "RL-3500"
    ]
    tmp_dir = tempfile.gettempdir()

    # we dont need to redefine the tmcf file and mcf file
    # we can reuse the ones we used already. Hence discard them
    tmcf_file_path = os.path.join(tmp_dir, "temp.tmcf")
    mcf_file_path = os.path.join(tmp_dir, "temp.mcf")

    for state_data_file in state_data_files:

        data_file_path = os.path.join(
            os.path.dirname(__file__), 'data/{state_data_file}.xlsx'.format(
                state_data_file=state_data_file))

        csv_file_name = "./IndiaCensus2011_Primary_Abstract_Religion_{state_data_file}.csv".format(
            state_data_file=state_data_file)
        csv_file_path = os.path.join(os.path.dirname(__file__), csv_file_name)
        loader = CensusPrimaryReligiousDataLoader(
            data_file_path=data_file_path,
            metadata_file_path=metadata_file_path,
            mcf_file_path=mcf_file_path,
            tmcf_file_path=tmcf_file_path,
            csv_file_path=csv_file_path,
            existing_stat_var=existing_stat_var,
            census_year=2011,
            dataset_name="Primary_Abstract_Religion",
            data_categories=data_categories,
            data_category_column="Religion")
        loader.process()
