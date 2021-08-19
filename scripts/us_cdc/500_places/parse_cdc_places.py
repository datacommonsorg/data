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
Date: 8/19/2021
Description: This script cleans a csv file of census tract, county,
zip code, or city level CDC 500 PLACES data downloaded from the CDC.
URL: https://chronicdata.cdc.gov/browse?category=500+Cities+%26+Places
@input_file     filepath to the original csv that needs to be cleaned
@output_file    filepath to the csv to which the cleaned data is written
python3 parse_cdc_places.py input_file output_file
'''

import sys
import pandas as pd
import numpy as np

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
        "Percent_Person_21To65Years_Female_ReceivedCervicalCancerScreening"
}

# Mapping of StatVar dcids to StatVar names
STATVAR_NAMES_MAP = {
    "Percent_Person_65OrMoreYears_WithAllTeethLoss":
        "Prevalence of 65 Or More Years, All Teeth Loss",
    "Percent_Person_50To74Years_Female_ReceivedMammography":
        "Prevalence of 50 - 74 Years, Female, Mammography",
    "Percent_Person_WithArthritis":
        "Prevalence of Arthritis",
    "Percent_Person_WithStroke":
        "Prevalence of Stroke",
    "Percent_Person_Obesity":
        "Prevalence of Obesity",
    "Percent_Person_WithAsthma":
        "Prevalence of Asthma",
    "Percent_Person_WithDiabetes":
        "Prevalence of Diabetes",
    "Percent_Person_BingeDrinking":
        "Prevalence of Binge Drinking",
    "Percent_Person_Smoking":
        "Prevalence of Smoking",
    "Percent_Person_SleepLessThan7Hours":
        "Prevalence of Sleep Less Than 7 Hours",
    "Percent_Person_50To75Years_ReceivedColorectalCancerScreening":
        "Prevalence of 50 - 75 Years, Colorectal Cancer Screening",
    "Percent_Person_WithCancerExcludingSkinCancer":
        "Prevalence of Cancer Excluding Skin Cancer",
    "Percent_Person_WithPhysicalHealthNotGood":
        "Prevalence of Physical Health Not Good",
    "Percent_Person_65OrMoreYears_Male_ReceivedCorePreventiveServices":
        "Prevalence of 65 Years or More, Male, Core Preventive Services",
    "Percent_Person_65OrMoreYears_Female_ReceivedCorePreventiveServices":
        "Prevalence of 65 Years or More, Female, Core Preventive Services",
    "Percent_Person_ReceivedAnnualCheckup":
        "Prevalence of Annual Checkup",
    "Percent_Person_WithHighBloodPressure":
        "Prevalence of High Blood Pressure",
    "Percent_Person_ReceivedDentalVisit":
        "Prevalence of Dental Visit",
    "Percent_Person_WithMentalHealthNotGood":
        "Prevalence of Mental Health Not Good",
    "Percent_Person_PhysicalInactivity":
        "Prevalence of Physical Inactivity",
    "Percent_Person_18To64Years_ReceivedNoHealthInsurance":
        "Prevalence of 18 - 64 Years, No Health Insurance",
    "Percent_Person_WithChronicObstructivePulmonaryDisease":
        "Prevalence of Chronic Obstructive Pulmonary Disease",
    "Percent_Person_ReceivedCholesterolScreening":
        "Prevalence of Cholesterol Screening",
    "Percent_Person_WithChronicKidneyDisease":
        "Prevalence of Chronic Kidney Disease",
    "Percent_Person_WithHighCholesterol":
        "Prevalence of High Cholesterol",
    "Percent_Person_18OrMoreYears_WithHighBloodPressure_ReceivedTakingBloodPressureMedication":
        "Prevalence of 18 Years or More, High Blood Pressure, Taking Blood Pressure Medication",
    "Percent_Person_WithCoronaryHeartDisease":
        "Prevalence of Coronary Heart Disease",
    "Percent_Person_21To65Years_Female_ReceivedCervicalCancerScreening":
        "Prevalence of 21 - 65 Years, Female, Received Cervical Cancer Screening"
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


def clean_census_tract_data(data):
    """
    Args:
        data: pandas dataframe with census tract-level data to be cleaned
    Returns:
        a dataframe with cleaned census tract-level data
    """
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
    return data


def clean_county_data(data):
    """
    Args:
        data: pandas dataframe with county-level data to be cleaned
    Returns:
        a dataframe with cleaned county-level data
    """
    data["LocationID"] = data["LocationID"].apply(generate_county_dcids)
    data.rename(columns={
        'MeasureId': 'StatVar',
        'LocationID': 'Location'
    },
                inplace=True)
    data = data.drop(columns=[
        "Measure", "Category", "DataSource", "Data_Value_Type", "StateAbbr",
        "StateDesc", "Data_Value_Unit", "Data_Value_Footnote_Symbol",
        "Data_Value_Footnote", "geolocation", "LocationName", "CategoryID",
        "Short_Question_Text", "Latitude", "Longitude"
    ])
    return data


def clean_city_data(data):
    """
    Args:
        data: pandas dataframe with city-level data to be cleaned
    Returns:
        a dataframe with cleaned city-level data
    """
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


def generate_statvar_names(data):
    """
    Args:
        data: pandas dataframe with data to be cleaned
    Returns:
        a dataframe with additional columns of StatVar names
    """
    data[
        "Low_Confidence_Limit_StatVar"] = "dcs:LowerConfidenceIntervalLimit_" + data[
            "MeasureId"].map(MEASURE_TO_STATVAR_MAP)
    data[
        "High_Confidence_Limit_StatVar"] = "dcs:UpperConfidenceIntervalLimit_" + data[
            "MeasureId"].map(MEASURE_TO_STATVAR_MAP)
    data["Population_StatVar"] = "dcs:SampleSize_" + data["MeasureId"].map(
        MEASURE_TO_STATVAR_MAP)
    data["MeasureId"] = "dcs:" + data["MeasureId"].map(MEASURE_TO_STATVAR_MAP)
    data["DataValueTypeID"] = "dcs:" + data["DataValueTypeID"].map(
        DATA_VALUE_TYPE_MAP)
    data["ConfidenceLevelTypeID"] = data["DataValueTypeID"] + "ConfidenceLevel"
    return data


def clean_cdc_places_data(input_file, output_file, sep):
    """
    Args:
        input_file: path to a comma-separated CDC Places data file
        output_file: path for the cleaned csv to be stored
    Returns:
        a cleaned csv file
    """
    print("Cleaning file...")
    data = pd.read_csv(input_file, sep=sep)
    data = generate_statvar_names(data)
    if "Tract" in input_file:
        data = clean_census_tract_data(data)
    elif "County" in input_file:
        data = clean_county_data(data)
    elif "City" in input_file:
        data = clean_city_data(data)
    data = data.replace(np.nan, '', regex=True)
    print("Writing to output file...")
    data.to_csv(output_file, index=False)
    print("Finished cleaning file!")


def main():
    """Main function to generate the cleaned csv file."""
    sep = ","
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    if len(sys.argv) > 3:
        sep = sys.argv[3].strip('sep=')
    clean_cdc_places_data(input_file, output_file, sep)


if __name__ == "__main__":
    main()
