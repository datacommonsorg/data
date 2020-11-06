import os
import json
import csv
import copy
import pandas as pd
import numpy as np
import urllib.request

TEMPLATE_STAT_VAR = """
Node: dcid:{name}
description: "{description}"
typeOf: dcs:StatisticalVariable
populationType: dcs:{populationType}
statType: dcs:{statType}
measuredProperty: dcs:{measuredProperty}
{constraints}
"""

TEMPLATE_TMCF = """
Node: E:IndiaCensus{year}_{dataset_name}->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:IndiaCensus{year}_{dataset_name}->StatisticalVariable
observationDate: C:IndiaCensus{year}_{dataset_name}->Year
observationAbout: C:IndiaCensus{year}_{dataset_name}->Name
value: C:IndiaCensus{year}_{dataset_name}->value
"""

census_location_id_pattern = "COI{year}-{state}-{district}-{subdistt}-{town_or_village}-{ward}-{eb}"


class CensusDataLoader:

    def __init__(self, data_file_path, metadata_file_path, mcf_file_path,
                 tmcf_file_path, csv_file_path, existing_stat_var, census_year,
                 social_category, dataset_name):
        self.data_file_path = data_file_path
        self.metadata_file_path = metadata_file_path
        self.mcf_file_path = mcf_file_path
        self.csv_file_path = csv_file_path
        self.tmcf_file_path = tmcf_file_path
        self.existing_stat_var = existing_stat_var
        self.census_year = census_year
        self.social_category = social_category
        self.dataset_name = dataset_name
        self.raw_df = None
        self.stat_var_index = {}

    def _download(self):
        dtype = {
            'State': str,
            'District': str,
            'Subdistt': str,
            "Town/Village": str,
            "Ward": str,
            "EB": str
        }
        self.raw_df = pd.read_excel(self.data_file_path, dtype=dtype)

    def _format_data(self):

        #Generate Census locationid
        self.raw_df["census_location_id"] = self.raw_df.apply(
            lambda row: census_location_id_pattern.format(
                year=self.census_year,
                state=row["State"],
                district=row["District"],
                subdistt=row["Subdistt"],
                town_or_village=row["Town/Village"],
                ward=row["Ward"],
                eb=row["EB"]),
            axis=1)

        #Remove the unwanted columns
        #They are census codes which we dont use
        #State,District,Subdistt,Town/Village,Ward,EB
        self.raw_df.drop([
            "State", "District", "Subdistt", "Town/Village", "Ward", "EB",
            "Level", "Name"
        ],
                         axis=1,
                         inplace=True)
        #first column is Name of the place
        #second column is Name of the TRU/placeOfResidence
        #3-N are the actual values
        value_columns = list(self.raw_df.columns[1:-1])

        #converting rows in to columns. So the filnal structure will be
        #Name,TRU,columnName,value
        self.raw_df = self.raw_df.melt(id_vars=["census_location_id", "TRU"],
                                       value_vars=value_columns,
                                       var_name='columnName',
                                       value_name='Value')
        #Add corresponding StatisticalVariable, based on columnName and TRU
        self.raw_df['StatisticalVariable'] = self.raw_df.apply(
            lambda row: self.stat_var_index["{0}_{1}".format(
                row["columnName"], row["TRU"])],
            axis=1)
        #add the census year
        self.raw_df['Year'] = self.census_year

        #remove the rows for which we dont have dcids defined
        location2dcid_json_path = os.path.join(
            os.path.dirname(__file__) +
            "/../geo/data/india_census_2011_location_to_dcid.json")
        location2dcid = dict(json.loads(open(location2dcid_json_path).read()))
        self.raw_df = self.raw_df[self.raw_df['census_location_id'].isin(
            location2dcid.keys())]

        #replace census_location_id with dcid
        self.raw_df['Region'] = self.raw_df.apply(
            lambda row: location2dcid[row['census_location_id']], axis=1)

        #Export it as CSV. It will have the following columns
        #Name,TRU,columnName,value,StatisticalVariable,Year
        self.raw_df.to_csv(self.csv_file_path, index=False, header=True)

    def _create_variable(self, data_row, place_of_residence=None):
        row = copy.deepcopy(data_row)
        name = "Count_" + row["populationType"]
        constraints = ""

        if self.social_category == "ScheduleCaste":
            name = name + "_" + "ScheduleCaste"
            constraints = constraints + "socialCategory: ScheduleCaste \n"

        if self.social_category == "ScheduleTribe":
            name = name + "_" + "ScheduleTribe"
            constraints = constraints + "socialCategory: ScheduleTribe \n"

        if row["age"] == "YearsUpto6":
            name = name + "_" + "YearsUpto6"
            constraints = constraints + "age: dcid:YearsUpto6 \n"
        else:
            pass

        if row["workerStatus"] == "Worker":
            constraints = constraints + "workerStatus: Worker \n"
            if row["workerClassification"] == "MainWorker":
                name = name + "_" + "MainWorkers"
                constraints = constraints + "workerClassification: MainWorker \n"
                if row["workCategory"] != "":
                    name = name + "_" + row["workCategory"]
                    constraints = constraints + "workCategory:" + row[
                        "workCategory"] + " \n"

            elif row["workerClassification"] == "MarginalWorker":
                name = name + "_" + "MarginalWorkers"
                constraints = constraints + "workerClassification: MarginalWorker \n"
                if row["workCategory"] != "":
                    name = name + "_" + row["workCategory"]
                    constraints = constraints + "workCategory:" + row[
                        "workCategory"] + " \n"

                if row["workPeriod"] == "[Month - 3]":
                    name = name + "_" + "WorkedUpto3Months"
                    constraints = constraints + "workPeriod:" + row[
                        "workPeriod"] + " \n"

                if row["workPeriod"] == "[Month 3 6]":
                    name = name + "_" + "Worked3To6Months"
                    constraints = constraints + "workPeriod:" + row[
                        "workPeriod"] + " \n"
            else:
                name = name + "_" + "Workers"

        elif row["workerStatus"] == "NonWorker":
            name = name + "_" + "NonWorkers"
            constraints = constraints + "workerStatus: NonWorker \n"

        if place_of_residence == "Urban":
            name = name + "_" + "Urban"
            constraints = constraints + "placeOfResidence: dcs:Urban \n"
            row["description"] = row["description"] + " - Urban"

        elif place_of_residence == "Rural":
            name = name + "_" + "Rural"
            constraints = constraints + "placeOfResidence: dcs:Rural \n"
            row["description"] = row["description"] + " - Rural"

        if row["gender"] == "Male":
            name = name + "_" + "Male"
            constraints = constraints + "gender: schema:Male \n"

        elif row["gender"] == "Female":
            name = name + "_" + "Female"
            constraints = constraints + "gender: schema:Female \n"

        row["name"] = name
        row["constraints"] = constraints

        key = "{0}_{1}".format(
            row["columnName"],
            place_of_residence if place_of_residence != None else "Total")
        self.stat_var_index[key] = name

        self.mcf.append(row)
        stat_var = TEMPLATE_STAT_VAR.format(**dict(row))
        stat_var = stat_var + "\n"
        return name, stat_var

    def _create_mcf(self):
        self.mcf = []
        with open(self.metadata_file_path) as csvfile:
            reader = csv.DictReader(csvfile)
            with open(self.mcf_file_path, 'w+', newline='') as f_out:
                for data_row in reader:
                    for place_of_residence in [None, "Urban", "Rural"]:
                        name, stat_var = self._create_variable(
                            data_row, place_of_residence)
                        if name in self.existing_stat_var:
                            pass
                        else:
                            f_out.write(stat_var)

    def _create_tmcf(self):
        with open(self.tmcf_file_path, 'w+', newline='') as f_out:
            f_out.write(
                TEMPLATE_TMCF.format(year=self.census_year,
                                     dataset_name=self.dataset_name))

    def process(self):
        self._download()
        self._create_mcf()
        self._create_tmcf()
        self._format_data()
