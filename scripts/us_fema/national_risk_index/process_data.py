import json
import os
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from absl import app
from absl import flags
# Configure logging
logging.basicConfig(
    filename="file_errors.log",  # Log file name
    level=logging.ERROR,         # Log level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
)

FLAGS = flags.FLAGS
flags.DEFINE_string('output_path', 'output', 'The local path to download the files')

# if not os.path.exists(FLAGS.output_path):
#             pathlib.Path(FLAGS.output_path).mkdir(parents=True, exist_ok=True)
INPUT_TO_OUTPUT_PATHS = {
    "source_data/NRI_Table_Counties.csv": "nri_counties_table.csv",
    "source_data/NRI_Table_CensusTracts.csv": "nri_tracts_table.csv",
}


def fips_to_geoid(row):
    """
    Given a row of CSV data from the FEMA NRI source table, calculated the GeoID of the place
    in the DC format, which includes trailing and leading zeros.

    Handles the distinction between rows for counties and tracts.

    Returns the geoID as a string, with the "geoId/" prefix.
    """
    # (for counties)we zfill to 5, because in a State-County FIPS, state takes
    # up to 2 digis and the county 3 (for a total of 5), however, in the FEMA
    # dataset, the trailing zero for States with State FIPS < 10 is ommitted
    # for example:

    # California State FIPS is 6
    # Alameda County, CA FIPS is 1.
    # The correct GeoId would be 06001
    # However, the FEMA study puts this down at 6001 in the STCOFIPS field

    # tract FIPS are of length 11

    if "TRACTFIPS" in row:
        field = "TRACTFIPS"
        length = 11
    else:  # this is a county row
        field = "STCOFIPS"
        length = 5

    return "geoId/" + str(row[field]).zfill(length)

def rename_file (file_path,nri_ver):
    file = Path(file_path)
    new_file_path = file.stem + "_"+ nri_ver + file.suffix  # Modify filename
    new_file_path = file.with_name(new_file_path) 
    return new_file_path


def process_csv(input_path, output_path, csv_structure_f):
    try:
        data_table = pd.read_csv(input_path)
        nri_ver =data_table["NRI_VER"].iloc[1]
        
        # TODO: interpret empty values. semantics of empty values is described in
        # Table 2 of the Technical Documentation available at:
        # https://www.fema.gov/sites/default/files/documents/fema_national-risk-index_technical-documentation.pdf

        # the column structure should be the same between the county and tract tables
        # so we normalize it with the list of fields "csv_structure"
        with open(csv_structure_f, "r") as json_file:
            csv_structure = json.load(json_file)
        normalized_table = data_table[csv_structure]
        normalized_table["OBSER_DATE"] = nri_ver

        # - after the structure is normalized, add the DCID_GeoID field to the first location
        # - the TMCF generated in generate_schema_and_tmcf.py expect to find the
        # geoID in the field "DCID_GeoID"
        normalized_table.insert(0, "DCID_GeoID",
                                data_table.apply(fips_to_geoid, axis=1))
       
        new_output_path  = rename_file(output_path, nri_ver)
        normalized_table.to_csv(new_output_path)
        new_input_file =rename_file(input_path, nri_ver)
        os.rename(input_path, new_input_file)
    
        print("****************************",new_input_file)
        # for filename in os.listdir(folder_path):
        #     if filename.endswith(".csv"):
        #         old_filepath = os.path.join(folder_path, filename)
        #         new_filename = filename + suffix + ".csv"  # Add suffix before existing extension
        #         new_filepath = os.path.join(folder_path, new_filename)
        #         try:
        #             os.rename(old_filepath, new_filepath)
        #             print(f"Renamed {old_filepath} to {new_filepath}")
        #         except OSError as e:
        #             print(f"Error renaming {old_filepath}: {e}")

        
       
    except FileNotFoundError as e:
        logging.error(f"FileNotFoundError: {e}")
        print(f"Error: The file '{input_path}' was not found.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}")

def main(argv):
    # path = "source_data/"
    # input_files =os.listdir(path)
    # file_name = "source_data/" + input_files[0]
    # data_table = pd.read_csv(file_name)
    # nri_ver =data_table["NRI_VER"].iloc[1]
    # for files in input_files:
    #     file = Path(files)
    #     new_input_path = file.stem + "_"+ nri_ver + file.suffix  # Modify filename
    #     new_input_path = file.with_name(new_input_path) 
    #     print(new_input_path)
    print(FLAGS.output_path)
       
    for input_path in INPUT_TO_OUTPUT_PATHS:
        
        output_path_new = os.path.join(FLAGS.output_path, INPUT_TO_OUTPUT_PATHS[input_path])
       
        process_csv(input_path, output_path_new, "output/csv_columns.json")
if __name__ == "__main__":
  app.run(main)