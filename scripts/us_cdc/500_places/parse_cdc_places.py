# Copyright 2021 Google LLC
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
'''
Author: Padma Gundapaneni @padma-g
Date: 8/30/2021
Description: This script cleans a csv file of census tract, county,
or city level CDC 500 PLACES data downloaded from the CDC.
URL: https://chronicdata.cdc.gov/browse?category=500+Cities+%26+Places
@input_file     filepath to the original csv that needs to be cleaned
@output_file    filepath to the csv to which the cleaned data is written
@delimiter      delimiter used in the original csv
python3 parse_cdc_places.py
'''

import os
import sys
import pandas as pd
import numpy as np
import json
from absl import logging
from absl import flags
from absl import app
from google.cloud import storage

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_MODULE_DIR, '../../../util/'))
import file_util

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'config_path', 'gs://unresolved_mcf/cdc/cdc500places/download_config.json',
    'Path to config file')
_MODULE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'gcs_output')
_INPUT_FILE_PATH = os.path.join(_MODULE_DIR, 'input_files')
_OUTPUT_FILE_PATH = os.path.join(_MODULE_DIR, 'cleaned_csv')


def read_config_file_from_gcs(file_path):
    with file_util.FileIO(file_path, 'r') as f:
        CONFIG_FILE = json.load(f)
    return CONFIG_FILE


# Mapping of measure abbreviations to StatVar dcids
MEASURE_TO_STATVAR_MAP = {
    "TEETHLOST":
        "Percent_Person_65OrMoreYears_WithAllTeethLoss",
    "MAMMOUSE":
        "Percent_Person_50To74Years_Female_ReceivedMammography",
    "ARTHRITIS":
        "Percent_Person_WithArthritis",
    "STROKE":
        "Percent_Person_WithStroke",
    "OBESITY":
        "Percent_Person_Obesity",
    "CASTHMA":
        "Percent_Person_WithAsthma",
    "DIABETES":
        "Percent_Person_WithDiabetes",
    "BINGE":
        "Percent_Person_BingeDrinking",
    "CSMOKING":
        "Percent_Person_Smoking",
    "SLEEP":
        "Percent_Person_SleepLessThan7Hours",
    "COLON_SCREEN":
        "Percent_Person_50To75Years_ReceivedColorectalCancerScreening",
    "CANCER":
        "Percent_Person_WithCancerExcludingSkinCancer",
    "PHLTH":
        "Percent_Person_WithPhysicalHealthNotGood",
    "COREM":
        "Percent_Person_65OrMoreYears_Male_ReceivedCorePreventiveServices",
    "COREW":
        "Percent_Person_65OrMoreYears_Female_ReceivedCorePreventiveServices",
    "CHECKUP":
        "Percent_Person_ReceivedAnnualCheckup",
    "BPHIGH":
        "Percent_Person_WithHighBloodPressure",
    "DENTAL":
        "Percent_Person_ReceivedDentalVisit",
    "MHLTH":
        "Percent_Person_WithMentalHealthNotGood",
    "LPA":
        "Percent_Person_PhysicalInactivity",
    "ACCESS2":
        "Percent_Person_18To64Years_ReceivedNoHealthInsurance",
    "COPD":
        "Percent_Person_WithChronicObstructivePulmonaryDisease",
    "CHOLSCREEN":
        "Percent_Person_ReceivedCholesterolScreening",
    "KIDNEY":
        "Percent_Person_WithChronicKidneyDisease",
    "HIGHCHOL":
        "Percent_Person_WithHighCholesterol",
    "BPMED":
        "Percent_Person_18OrMoreYears_WithHighBloodPressure_ReceivedTakingBloodPressureMedication",
    "CHD":
        "Percent_Person_WithCoronaryHeartDisease",
    "CERVICAL":
        "Percent_Person_21To65Years_Female_ReceivedCervicalCancerScreening",
    "DEPRESSION":
        "Percent_Person_18OrMoreYears_WithDepression",
    "VISION":
        "Percent_Person_18OrMoreYears_WithVisionDisability",
    "MOBILITY":
        "Percent_Person_18OrMoreYears_WithMobilityDisability",
    "SELFCARE":
        "Percent_Person_18OrMoreYears_WithSelfCareDisability",
    "DISABILITY":
        "Percent_Person_18OrMoreYears_WithAnyDisability",
    "INDEPLIVE":
        "Percent_Person_18OrMoreYears_WithIndependentLivingDisability",
    "GHLTH":
        "Percent_Person_18OrMoreYears_WithPoorGeneralHealth",
    "COGNITION":
        "Percent_Person_18OrMoreYears_WithCognitiveDisability",
    "HEARING":
        "Percent_Person_18OrMoreYears_WithHearingDisability",
    "LACKTRPT":
        "Count_Person_18OrMoreYears_LackReliableTransport_AsAFractionOf_Count_Person_18OrMoreYears",
    "HOUSINSECU":
        "Count_Person_18OrMoreYears_HousingInsecurity_AsAFractionOf_Count_Person_18OrMoreYears",
    "EMOTIONSPT":
        "Count_Person_18OrMoreYears_LackSocialAndEmotionalSupport_AsAFractionOf_Count_Person_18OrMoreYears",
    "FOODSTAMP":
        "Count_Person_18OrMoreYears_ReceivedFoodStamp_AsAFractionOf_Count_Person_18OrMoreYears",
    "FOODINSECU":
        "Count_Person_18OrMoreYears_FoodInsecurity_AsAFractionOf_Count_Person_18OrMoreYears",
    "SHUTUTILITY":
        "Count_Person_18OrMoreYears_UtilityServiceShutoffThreat_AsAFractionOf_Count_Person_18OrMoreYears",
    "ISOLATION":
        "Count_Person_18OrMoreYears_SociallyIsolated_AsAFractionOf_Count_Person_18OrMoreYears",
}

# Mapping of data value type abbreviations to StatVar dcids
DATA_VALUE_TYPE_MAP = {
    "CrdPrv": "CrudePrevalence",
    "AgeAdjPrv": "AgeAdjustedPrevalence"
}


def generate_census_tract_dcids(ctfips):
    """
    Args:
        ctfips: a census tract FIPS code
    Returns:
        the matching dcid for the FIPS code
    """
    dcid = "dcid:geoId/" + str(ctfips).zfill(11)
    return dcid


def generate_county_dcids(countyfips):
    """
    Args:
        countyfips: a county FIPS code
    Returns:
        the matching dcid for the FIPS code
    """
    if countyfips != 59:
        dcid = "dcid:geoId/" + str(countyfips).zfill(5)
    else:
        dcid = "dcid:country/USA"
    return dcid


def generate_city_dcids(cityfips):
    """
    Args:
        cityfips: a county FIPS code
    Returns:
        the matching dcid for the FIPS code
    """
    dcid = "dcid:geoId/" + str(cityfips).zfill(7)
    return dcid


def generate_zip_code_dcids(zipcode):
    """
    Args:
        zipcode: a zip code
    Returns:
        the matching dcid for the zip code
    """
    dcid = "dcid:zip/" + str(zipcode).zfill(5)
    return dcid


def clean_census_tract_data(data):
    """
    Args:
        data: pandas dataframe with census tract-level data to be cleaned
    Returns:
        a dataframe with cleaned census tract-level data
    """
    try:
        data["LocationName"] = data["LocationName"].apply(
            generate_census_tract_dcids)
        data.rename(columns={
            'MeasureId': 'StatVar',
            'LocationName': 'Location'
        },
                    inplace=True)
        data = data.drop(columns=[
            "Measure", "Category", "DataSource", "Data_Value_Type", "StateAbbr",
            "StateDesc", "CountyName", "CountyFIPS", "Data_Value_Unit",
            "Data_Value_Footnote_Symbol", "Data_Value_Footnote", "Geolocation",
            "LocationID", "CategoryID", "Short_Question_Text"
        ])
        data = data[[
            'Year', 'Data_Value', 'Low_Confidence_Limit',
            'High_Confidence_Limit', 'TotalPopulation', 'Location', 'StatVar',
            'DataValueTypeID', 'release_year', 'Low_Confidence_Limit_StatVar',
            'High_Confidence_Limit_StatVar', 'Population_StatVar'
        ]]
        return data
    except Exception as e:
        logging.fatal(f"Error processing census tract input file {e}")


def clean_county_data(data):
    """
    Args:
        data: pandas dataframe with county-level data to be cleaned
    Returns:if not os.path.exists(_OUTPUT_FILE_PATH):
    os.mkdir(_OUTPUT_FILE_PATH)
        a dataframe with cleaned county-level data
    """
    try:
        data["LocationID"] = data["LocationID"].apply(generate_county_dcids)
        data.rename(columns={
            'MeasureId': 'StatVar',
            'LocationID': 'Location'
        },
                    inplace=True)
        data = data.drop(columns=[
            "Measure", "Category", "DataSource", "Data_Value_Type", "StateAbbr",
            "StateDesc", "Data_Value_Unit", "Data_Value_Footnote_Symbol",
            "Data_Value_Footnote", "Geolocation", "LocationName", "CategoryID",
            "Short_Question_Text"
        ])
        return data
    except Exception as e:
        logging.fatal(f"Error processing county input file {e}")


def clean_city_data(data):
    """
    Args:
        data: pandas dataframe with city-level data to be cleaned
    Returns:
        a dataframe with cleaned city-level data
    """
    try:
        data["LocationID"] = data["LocationID"].apply(generate_city_dcids)
        data.rename(columns={
            'MeasureId': 'StatVar',
            'LocationID': 'Location'
        },
                    inplace=True)
        data = data.drop(columns=[
            "Measure", "Category", "DataSource", "Data_Value_Type", "StateAbbr",
            "StateDesc", "Data_Value_Unit", "Data_Value_Footnote_Symbol",
            "Data_Value_Footnote", "Geolocation", "LocationName", "CategoryID",
            "Short_Question_Text"
        ])
        return data
    except Exception as e:
        logging.fatal(f"Error processing city input file {e}")


def clean_zip_code_data(data):
    """
    Args:
        data: pandas dataframe with zip code-level data to be cleaned
    Returns:
        a dataframe with cleaned zip code-level data
    """
    try:
        data["LocationID"] = data["LocationID"].apply(generate_zip_code_dcids)
        data.rename(columns={
            'MeasureId': 'StatVar',
            'LocationID': 'Location'
        },
                    inplace=True)
        data = data.drop(columns=[
            "Measure", "Category", "DataSource", "Data_Value_Type",
            "Data_Value_Unit", "Data_Value_Footnote_Symbol",
            "Data_Value_Footnote", "Geolocation", "LocationName", "CategoryID",
            "Short_Question_Text"
        ])
        return data
    except Exception as e:
        logging.fatal(f"Error processing zipcode input file {e}")


def generate_statvar_names(data):
    """
    Args:
        data: pandas dataframe with data to be cleaned
    Returns:
        a dataframe with additional columns of StatVar names
    """
    try:
        data[
            "Low_Confidence_Limit_StatVar"] = "dcs:LowerConfidenceIntervalLimit_" + data[
                "MeasureId"].map(MEASURE_TO_STATVAR_MAP)
        data[
            "High_Confidence_Limit_StatVar"] = "dcs:UpperConfidenceIntervalLimit_" + data[
                "MeasureId"].map(MEASURE_TO_STATVAR_MAP)
        data["Population_StatVar"] = "dcs:SampleSize_" + data["MeasureId"].map(
            MEASURE_TO_STATVAR_MAP)
        data["MeasureId"] = "dcs:" + data["MeasureId"].map(
            MEASURE_TO_STATVAR_MAP)
        data["DataValueTypeID"] = "dcs:" + data["DataValueTypeID"].map(
            DATA_VALUE_TYPE_MAP)
        return data
    except Exception as e:
        logging.fatal(f"Error additional columns of StatVar names {e}")


def clean_cdc_places_data(input_file, file_type, sep, release_year):
    """
    Args:
        input_file: path to a comma-separated CDC Places data file
        output_file: path for the cleaned csv to be stored
    Returns:
        a cleaned dataframe
    """
    logging.info(
        f"Processing input files for {file_type} for the year {release_year}")
    data = pd.read_csv(input_file, sep=sep)
    data["release_year"] = release_year
    data = generate_statvar_names(data)
    if "CensusTract" == file_type:
        data = clean_census_tract_data(data)
    elif "County" == file_type:
        data = clean_county_data(data)
    elif "City" == file_type:
        data = clean_city_data(data)
    elif "ZipCode" == file_type:
        data = clean_zip_code_data(data)
    data = data.replace(np.nan, '', regex=True)
    return data


def main(_):
    """Main function to generate the cleaned csv file."""
    logging.set_verbosity(2)
    #Creating output directory if not present
    if not os.path.exists(_OUTPUT_FILE_PATH):
        os.mkdir(_OUTPUT_FILE_PATH)
        logging.info(f"created output directory: {_OUTPUT_FILE_PATH}")
    CONFIG_FILE = read_config_file_from_gcs(_FLAGS.config_path)
    sep = ","
    for file_type in ["County", "City", "ZipCode", "CensusTract"]:
        FINAL_LIST = []
        for release_year in CONFIG_FILE:
            for file in release_year['parameter']:
                if file['FILE_TYPE'] == file_type:
                    input_file = os.path.join(_INPUT_FILE_PATH,
                                              file['FILE_NAME'])
                    FINAL_LIST.append(
                        clean_cdc_places_data(input_file, file_type, sep,
                                              release_year['release_year']))
        try:
            df_final = pd.concat(FINAL_LIST)
            df_final = df_final.sort_values(by='release_year')
            # Added drop duplicate as all the year data are not present
            # as part of latest year release of data only points modified
            # are present for previoud years in the latest year.
            df_final = df_final.drop_duplicates(
                subset=[
                    'Year', 'Location', 'StatVar', 'DataValueTypeID',
                    'Low_Confidence_Limit_StatVar',
                    'High_Confidence_Limit_StatVar', 'Population_StatVar'
                ],
                # add all columns headers except value columns to get
                # modified value from latest year release
                keep='last')
            df_final = df_final.drop('release_year', axis=1)
            output_file = os.path.join(_OUTPUT_FILE_PATH, file_type + ".csv")
            logging.info(
                f"Writing output CSV for {file_type} for the year {release_year['release_year']}"
            )
            df_final.to_csv(output_file, index=False)
        except Exception as e:
            logging.fatal(f"Error in processing and generating output {e}")


if __name__ == "__main__":

    app.run(main)
