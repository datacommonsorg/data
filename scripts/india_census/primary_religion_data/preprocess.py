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
from os import path
import urllib.request
from ..common.utils import title_case

CENSUS_DATA_COLUMN_START = 7

dcid_mapping = {}
dcid_mapping["Hindu"] = "dcs:Hinduism"
dcid_mapping["Muslim"] = "dcs:Islam"
dcid_mapping["Christian"] = "dcs:Christianity"
dcid_mapping["Sikh"] = "dcs:Sikhism"
dcid_mapping["Buddhist"] = "dcs:Buddhism"
dcid_mapping["Jain"] = "dcs:Jainism"
dcid_mapping[
    "Other religions and persuasions"] = "dcs:IndiaCensus_OtherReligionAndPersuasions"
dcid_mapping["Religion not stated"] = "dcs:ReligionNotStated"

TEMPLATE_STAT_VAR = """Node: dcid:{name}
name: "{description}"
description: "{description}"
typeOf: dcs:StatisticalVariable
populationType: dcs:{populationType}
statType: dcs:{statType}
measuredProperty: dcs:{measuredProperty}
{constraints}

"""

TEMPLATE_TMCF = """Node: E:IndiaCensus{year}_{dataset_name}->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:IndiaCensus{year}_{dataset_name}->StatisticalVariable
observationDate: C:IndiaCensus{year}_{dataset_name}->Year
observationAbout: E:IndiaCensus{year}_{dataset_name}->E1
value: C:IndiaCensus{year}_{dataset_name}->Value

Node: E:IndiaCensus{year}_{dataset_name}->E1
typeOf: schema:Place
indianCensusAreaCode{year}: C:IndiaCensus{year}_{dataset_name}->census_location_id"""


class CensusPrimaryReligiousDataLoader():
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

    def _download_and_standardize(self):
        dtype = {
            'State': str,
            'District': str,
            'Subdistt': str,
            "Town/Village": str
        }
        self.raw_df = pd.read_excel(self.data_file_path, dtype=dtype)
        self.census_columns = self.raw_df.columns[CENSUS_DATA_COLUMN_START:]

    def _format_location(self, row):
        # In this specific format there is no Level defined.
        # A non zero location code from the lowest administration area
        # takes the precedence.
        if row["Town/Village"] != "000000":
            return row["Town/Village"]

        elif row["Subdistt"] != "00000":
            return row["Subdistt"]

        elif row["District"] != "000":
            return row["District"]

        elif row["State"] != "00":
            return row["State"]
        else:
            # This is india level location
            return "0"

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

        # When data_category i.e religion is "Total" remove those rows
        # As they are not required
        self.raw_df = self.raw_df[
            self.raw_df[self.data_category_column] != "Total"]

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
        if path.exists(self.csv_file_path):
            self.raw_df.to_csv(self.csv_file_path,
                               mode='a',
                               index=False,
                               header=False)
        else:
            self.raw_df.to_csv(self.csv_file_path, index=False, header=True)

    def _get_base_name(self, row):
        # To make the name meaningful add Religion to the
        # the name of the stat var
        name = "Count_" + row["populationType"]
        return name

    def _get_base_constraints(self, row):
        constraints = ""
        return constraints

    def _get_stat_var_name(self, name):
        return "dcid:{}".format(name)

    def _get_measured_property_name(self, name):
        return "count"

    def _create_variable(self,
                         data_row,
                         place_of_residence=None,
                         data_category=None):
        row = copy.deepcopy(data_row)
        name_array = []
        constraints_array = []

        name_array.append(self._get_base_name(row))

        # No need to add empty constraint to the list
        if self._get_base_constraints(row) != "":
            constraints_array.append(self._get_base_constraints(row))

        name_array.append(title_case(data_category))
        row["description"] = row["description"] + " - " + data_category
        constraints_array.append("religion: " + dcid_mapping[data_category])

        if row["age"] == "YearsUpto6":
            name_array.append("YearsUpto6")
            constraints_array.append("age: dcid:YearsUpto6")

        if row["socialCategory"] == "ScheduledCaste":
            name_array.append("ScheduledCaste")
            constraints_array.append("socialCategory: dcs:ScheduledCaste")
        if row["socialCategory"] == "ScheduledTribe":
            name_array.append("ScheduledTribe")
            constraints_array.append("socialCategory: dcs:ScheduledTribe")

        if row["literacyStatus"] == "Literate":
            name_array.append("Literate")
            constraints_array.append("literacyStatus: dcs:Literate")
        elif row["literacyStatus"] == "Illiterate":
            name_array.append("Illiterate")
            constraints_array.append("literacyStatus: dcs:Illiterate")

        if row["workerStatus"] == "Worker":
            if row["workerClassification"] == "MainWorker":
                name_array.append("MainWorker")
                constraints_array.append("workerClassification: dcs:MainWorker")
                if row["workCategory"] != "":
                    name_array.append(row["workCategory"])
                    constraints_array.append("workCategory: dcs:" +
                                             row["workCategory"])

            elif row["workerClassification"] == "MarginalWorker":
                name_array.append("MarginalWorker")
                constraints_array.append(
                    "workerClassification: dcs:MarginalWorker")

                if row["workCategory"] != "":
                    name_array.append(row["workCategory"])
                    constraints_array.append("workCategory: dcs:" +
                                             row["workCategory"])

                if row["workPeriod"] == "[Month - 3]":
                    name_array.append("WorkedUpto3Months")
                    constraints_array.append("workPeriod:" + row["workPeriod"])

                if row["workPeriod"] == "[Month 3 6]":
                    name_array.append("Worked3To6Months")
                    constraints_array.append("workPeriod:" + row["workPeriod"])

            else:
                name_array.append("Workers")

        elif row["workerStatus"] == "NonWorker":
            name_array.append("NonWorker")
            constraints_array.append("workerStatus: dcs:NonWorker")

        if place_of_residence == "Urban":
            name_array.append("Urban")
            constraints_array.append(
                "placeOfResidenceClassification: dcs:Urban")
            row["description"] = row["description"] + " - Urban"

        elif place_of_residence == "Rural":
            name_array.append("Rural")
            constraints_array.append(
                "placeOfResidenceClassification: dcs:Rural")
            row["description"] = row["description"] + " - Rural"

        if row["gender"] == "Male":
            name_array.append("Male")
            constraints_array.append("gender: schema:Male")

        elif row["gender"] == "Female":
            name_array.append("Female")
            constraints_array.append("gender: schema:Female")

        name = "_".join(name_array)
        row["name"] = name
        row["constraints"] = "\n".join(constraints_array)

        key = "{0}_{1}".format(
            row["columnName"],
            place_of_residence if place_of_residence != None else "Total")

        if data_category:
            key = key + "_" + title_case(data_category)

        self.stat_var_index[key] = name
        row["StatisticalVariable"] = self._get_stat_var_name(name)
        row["measuredProperty"] = self._get_measured_property_name(name)
        self.mcf.append(row)

        stat_var = TEMPLATE_STAT_VAR.format(**dict(row))

        return name, stat_var

    def _create_mcf(self):
        self.mcf = []
        with open(self.metadata_file_path) as csvfile:
            reader = csv.DictReader(csvfile)
            with open(self.mcf_file_path, 'w+', newline='') as f_out:
                for data_row in reader:
                    for place_of_residence in [None, "Urban", "Rural"]:
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

    def _create_tmcf(self):
        with open(self.tmcf_file_path, 'w+', newline='') as f_out:
            f_out.write(
                TEMPLATE_TMCF.format(year=self.census_year,
                                     dataset_name=self.dataset_name))

    def process(self):
        self._download_and_standardize()
        self._create_mcf()
        self._create_tmcf()
        self._format_data()


if __name__ == '__main__':

    metadata_file_path = os.path.join(
        os.path.dirname(__file__),
        '../common/primary_abstract_data_variables.csv')

    # These are basic statvars
    existing_stat_var = [
        "Count_Household",
        "Count_Person",
        "Count_Person_Urban",
        "Count_Person_Rural",
        "Count_Person_Male",
        "Count_Person_Female",
    ]

    # These are generated as part of `primary_census_abstract_data`
    # No need to create them again or include them in MCF
    existing_stat_var.extend([])

    data_categories = [
        "Hindu", "Muslim", "Christian", "Sikh", "Buddhist", "Jain",
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

    # If the final CSV already exists
    # Remove it, so it can be regenerated
    if path.exists(csv_file_path):
        os.remove(csv_file_path)

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
    state_data_files = ["RL-0100", "RL-0200", "RL-0300"]
    tmp_dir = tempfile.gettempdir()

    # we dont need to redefine the tmcf file and mcf file
    # we can reuse the ones we used already. Hence discard them
    tmcf_file_path = os.path.join(tmp_dir, "temp.tmcf")
    mcf_file_path = os.path.join(tmp_dir, "temp.mcf")

    for state_data_file in state_data_files:

        data_file_path = os.path.join(
            os.path.dirname(__file__), 'data/{state_data_file}.xlsx'.format(
                state_data_file=state_data_file))

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
