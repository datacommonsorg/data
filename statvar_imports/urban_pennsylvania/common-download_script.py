# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# How to run the script to download the files:
# python3 download_script.py

import pandas as pd
import requests
import csv
import json
from absl import app
from absl import logging

logging.set_verbosity(logging.INFO)

# Configuration of the datasets

# Configuration 1: Public-and-Private-Education-Institutions-2017
config_1 = {
    "api_url": "https://data.pa.gov/resource/a5nq-sy2w.json",
    "output_filename": "Public-and-Private-Education-Institutions-2017-Cur.csv",
    "column_mapping": {
        'administrative_unit_number': 'Administrative Unit Number (AUN)', 'local_education_agency_lea': 'Local Education Agency (LEA)', 'lea_type': 'LEA Type', 'school_number': 'School Number', 'school': 'School', 'county': 'County', 'address_line_1': 'Address Line 1', 'address_line_2': 'Address Line 2', 'city': 'City', 'state': 'State', 'zip_code': 'Zip Code', 'zip_code_extension': 'Zip Code Extension', 'school_year_2017_2018': 'School Year 2017-2018', 'lea_school_key': 'LEA School Key', 'location_1': 'Location 1', 'location_2': 'Location 2', 'latitude': 'Latitude', 'longitude': 'Longitude', 'geocoded_wkt': 'Georeferenced Longitude & Latitude',
    },
    "desired_columns": ['Administrative Unit Number (AUN)', 'Local Education Agency (LEA)', 'LEA Type', 'School Number', 'School', 'County', 'Address Line 1', 'Address Line 2', 'City', 'State', 'Zip Code', 'Zip Code Extension', 'School Year 2017-2018', 'LEA School Key', 'Location 1', 'Location 2', 'Latitude', 'Longitude', 'Georeferenced Longitude & Latitude'],
    "coord_column_name": "georeferenced_latitude_longitude",
    "coord_format_type": "list"
}

# Configuration 2: Educational-Attainment-by-Age-Range-and-Gender-200
config_2 = {
    "api_url": "https://data.pa.gov/resource/xwn6-8rmw.json",
    "output_filename": "Educational-Attainment-by-Age-Range-and-Gender-200.csv",
    "column_mapping": {
        "census_year": "Census Year", "county_fips_code": "County FIPS Code", "economic_development_region": "Economic Development Region", "workforce_development_area": "Workforce Development Area", "county_name": "County Name", "county_code": "County Code", "age_range": "Age Range", "gender": "Gender", "total_population": "Total Population", "no_high_school_diploma": "No High School Diploma", "high_school_diploma_or": "High School Diploma Or Equivalent", "some_college_no_degree": "Some College No Degree", "associate_s_degree": "Associate's Degree", "bachelor_s_degree": "Bachelor's Degree", "graduate_or_professional": "Graduate or Professional Degree", "total_post_secondary": "Total Post-Secondary Degrees", "latitude": "Latitude", "longitude": "Longitude", "geocoded_coords": "New Georeferenced Column"
    },
    "desired_columns": ["Census Year", "County FIPS Code", "Economic Development Region", "Workforce Development Area", "County Name", "County Code", "Age Range", "Gender", "Total Population", "No High School Diploma", "High School Diploma Or Equivalent", "Some College No Degree", "Associate's Degree", "Bachelor's Degree", "Graduate or Professional Degree", "Total Post-Secondary Degrees", "New Georeferenced Column"],
    "coord_column_name": "geocoded_column",
    "coord_format_type": "dict"
}

# Configuration 3: Public-School-Enrollments-by-County-Grade-and-Gend
config_3 = {
    "api_url": "https://data.pa.gov/resource/jtmp-qscb.json",
    "output_filename": "Public-School-Enrollments-by-County-Grade-and-Gend.csv",
    "column_mapping": {
        'school_year': 'School Year', 'county_code': 'County Code', 'county': 'County', 'gender': 'Gender', 'pre_kindergarten_half_day': 'Pre-Kindergarten Half Day', 'pre_kindergarten_full_day': 'Pre-Kindergarten Full Day', 'k4_half_day': 'K4 Half Day', 'k4_full_day': 'K4 Full Day', 'k5_half_day': 'K5 Half Day', 'k5_full_day': 'K5 Full Day', '_1st_grade': '1st Grade', '_2nd_grade': '2nd Grade', '_3rd_grade': '3rd Grade', '_4th_grade': '4th Grade', '_5th_grade': '5th Grade', '_6th_grade': '6th Grade', '_7th_grade': '7th Grade', '_8th_grade': '8th Grade', '_9th_grade': '9th Grade', '_10th_grade': '10th Grade', '_11th_grade': '11th Grade', '_12th_grade': '12th Grade', 'total': 'Total'
    },
    "desired_columns": ["School Year", "County Code", "County", "Gender", "Pre-Kindergarten Half Day", "Pre-Kindergarten Full Day", "K4 Half Day", "K4 Full Day", "K5 Half Day", "K5 Full Day", "1st Grade", "2nd Grade", "3rd Grade", "4th Grade", "5th Grade", "6th Grade", "7th Grade", "8th Grade", "9th Grade", "10th Grade", "11th Grade", "12th Grade", "Total"],
    "coord_column_name": None, 
    "coord_format_type": None
}
#Configuration 4: Undergraduate-STEM-Enrollment-at-Publicly-Supporte
config_4 = {
    "api_url": "https://data.pa.gov/resource/r75w-4bue.json",
    "output_filename": "Undergraduate-STEM-Enrollment-at-Publicly-Supporte.csv",
    "column_mapping": {
        "date_collected": "Date Collected", "date_available": "Date Available", "type": "Type", "college": "College", "cip": "CIP", "area_of_study": "Area of Study", "count": "Count",
    },
    "desired_columns": ["Date Collected", "Date Available", "Type", "College", "CIP", "Area of Study", "Count"],
    "coord_column_name": None,
    "coord_format_type": None
}
#Configuration 5: Post-Secondary-Completions-Total-Awards-Degrees-SY
config_5 = {
    "api_url": "https://data.pa.gov/resource/jqcu-bcsg.json",
    "output_filename": "Post-Secondary-Completions-Total-Awards-Degrees-SY.csv",
    "column_mapping": {
        "unit_id": "Unit ID", "institution_name": "Institution Name", "year": "Year", "associate_s_degree": "Associate's Degree", "bachelor_s_degree": "Bachelor's Degree", "master_s_degree": "Master's Degree", "doctor_s_degree_research_scholarship": "Doctor's Degree - Research/Scholarship", "doctor_s_degree_professional_practice": "Doctor's Degree - Professional Practice", "doctor_s_degree_other": "Doctor's Degree - Other",
    },
    "desired_columns": ["Unit ID", "Institution Name", "Year", "Associate's Degree", "Bachelor's Degree", "Master's Degree", "Doctor's Degree - Research/Scholarship", "Doctor's Degree - Professional Practice", "Doctor's Degree - Other"],
    "coord_column_name": None,
    "coord_format_type": None
}

#Configuration 6: Public-School-Enrollment-by-County-Grade-and-Race
config_6 = {
    "api_url": "https://data.pa.gov/resource/wb8u-h3s8.json",
    "output_filename": "Public-School-Enrollment-by-County-Grade-and-Race.csv",
    "column_mapping": {
        "county_code": "County Code", "county": "County", "race": "Race", "pkh": "Pre-Kindergarten Half Day", "pkf": "Pre-Kindergarten Full Day", "k4h": "K4 Half Day", "k4f": "K4 Full Day", "k5h": "K5 Half Day", "k5f": "K5 Full Day", "_001": "1st Grade", "_002": "2nd Grade", "_003": "3rd Grade", "_004": "4th Grade", "_005": "5th Grade", "_006": "6th Grade", "_007": "7th Grade", "_008": "8th Grade", "_009": "9th Grade", "_010": "10th Grade", "_011": "11th Grade", "_012": "12th Grade", "total": "Total"
    },
    "desired_columns": ["County Code", "County", "Race", "Pre-Kindergarten Half Day", "Pre-Kindergarten Full Day", "K4 Half Day", "K4 Full Day", "K5 Half Day", "K5 Full Day", "1st Grade", "2nd Grade", "3rd Grade", "4th Grade", "5th Grade", "6th Grade", "7th Grade", "8th Grade", "9th Grade", "10th Grade", "11th Grade", "12th Grade", "Total"],
    "coord_format_type": None
}

def process_api_data(api_url, output_filename, column_mapping, desired_columns, coord_column_name=None, coord_format_type=None):
    """
    Fetches data from an API, processes it, and saves it to a CSV file.

    Args:
        api_url (str): The API endpoint URL.
        output_filename (str): The name of the CSV file to save.
        column_mapping (dict): A dictionary to map API keys to desired headers.
        desired_columns (list): The final list of columns for the CSV.
        coord_column_name (str): The name of the coordinate column in the raw data.
        coord_format_type (str): "list" for [long, lat] or "dict" for {'lat':..., 'long':...}.
    """
    all_data = []
    offset = 0
    limit = 1000

    logging.info(f"Starting to retrieve data from {api_url}")

    while True:
        params = {'$offset': offset, '$limit': limit}

        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()

            data = response.json()

            if not data:
                logging.warning(
                    "No more data received. All records have been retrieved.")
                break

            all_data.extend(data)

            logging.info(
                f"Retrieved {len(data)} records (Offset: {offset}). Total records: {len(all_data)}")

            offset += limit

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to retrieve data from {api_url}: {e}")
            return
        except Exception as e:
            logging.fatal(f"An unexpected error occurred: {e}")
            return

    if all_data:
        try:
            dataframe = pd.DataFrame(all_data)

            # Coordinate Processing based on format type
            if coord_column_name:
                def process_coords(row):
                    geo_ref = row.get(coord_column_name)

                    if isinstance(geo_ref, dict):
                        if coord_format_type == "list" and "coordinates" in geo_ref:
                            coords = geo_ref["coordinates"]
                            return pd.Series([coords[1], coords[0], f"POINT ({coords[0]} {coords[1]})"])
                        elif coord_format_type == "dict" and 'latitude' in geo_ref and 'longitude' in geo_ref:
                            latitude = geo_ref['latitude']
                            longitude = geo_ref['longitude']
                            return pd.Series([latitude, longitude, f"({latitude}, {longitude})"])
                    return pd.Series(["", "", ""])

                if coord_format_type == "list":
                    dataframe[["latitude", "longitude", "geocoded_wkt"]] = dataframe.apply(
                        process_coords, axis=1)
                elif coord_format_type == "dict":
                    dataframe[["latitude", "longitude", "geocoded_coords"]] = dataframe.apply(
                        process_coords, axis=1)

                # Drop the original geocoded column to avoid conflicts
                if coord_column_name in dataframe.columns:
                    dataframe = dataframe.drop(columns=[coord_column_name])

            # Rename columns  based on the provided mapping
            dataframe = dataframe.rename(columns=column_mapping)

            # Select and reorder the final desired columns
            dataframe = dataframe.reindex(columns=desired_columns)

            # CSV file creation to store the data
            dataframe.to_csv(output_filename, index=False)

            logging.info(
                f"Successfully processed and saved {len(all_data)} records to '{output_filename}'")
        except Exception as e:
            logging.error(
                f"Error processing or saving data for {output_filename}: {e}")
    else:
        logging.warning(
            "No data was retrieved. The CSV file was not created.")


def main(_):
    """
    Main function to orchestrate the data download process for all configured datasets.
    """
    datasets = [config_1, config_2, config_3, config_4, config_5, config_6]
    for i, config in enumerate(datasets, 1):
        process_api_data(**config)
        logging.info(f"Download of dataset {i} is completed.")


if __name__ == "__main__":
    app.run(main)