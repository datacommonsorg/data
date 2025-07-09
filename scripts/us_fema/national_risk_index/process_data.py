import json
import os
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from absl import app
from absl import flags
from datetime import datetime
from google.cloud import storage

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_MODULE_DIR, '../../../util/'))
import file_util
from io import StringIO
from absl import logging

FLAGS = flags.FLAGS
flags.DEFINE_string('output_path',
                    'gs://unresolved_mcf/us_fema/national_risk_index/latest/',
                    'The local path to download the files')

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


def convert_month_year(date_str):
    """
  Converts a date string in the format "Month Year" to "YYYY_MM".

  Args:
    date_str: The input date string (e.g., "March 2023").

  Returns:
    The converted date string in the format "YYYY_MM".
  """
    try:
        date_obj = datetime.strptime(date_str,
                                     '%B %Y')  # Parse the input string
        year = str(date_obj.year)
        month = str(date_obj.month).zfill(
            2)  # Pad single-digit months with zero
        return f"{year}-{month}"
    except Exception as e:
        logging.fatal(f"An error occurred: {e}")
        sys.exit(1)


def rename_file(file_path, nri_ver):
    file = Path(file_path)
    new_file_path = file.stem + "_" + nri_ver + file.suffix  # Modify filename
    new_file_path = file.with_name(new_file_path)
    return new_file_path


def rename_gcs_file_path(gcs_path, nri_vers):
    file_name_with_ext = gcs_path.split("/")[-1]
    file_name, ext = file_name_with_ext.rsplit(".", 1)
    new_file_name_with_ext = f"{file_name}_{nri_vers}.{ext}"
    new_gcs_path = gcs_path.replace(file_name_with_ext, new_file_name_with_ext)
    return new_gcs_path


def process_csv(input_path, output_path, csv_structure_f, out_put_file_name):
    try:
        data_table = pd.read_csv(input_path)
        nri_ver = data_table["NRI_VER"].iloc[1]

        # TODO: interpret empty values. semantics of empty values is described in
        # Table 2 of the Technical Documentation available at:
        # https://www.fema.gov/sites/default/files/documents/fema_national-risk-index_technical-documentation.pdf

        # the column structure should be the same between the county and tract tables
        # so we normalize it with the list of fields "csv_structure"
        with open(csv_structure_f, "r") as json_file:
            csv_structure = json.load(json_file)
        normalized_table = data_table[csv_structure]
        nri_month_year = convert_month_year(nri_ver)
        normalized_table["OBSER_DATE"] = nri_month_year

        # - after the structure is normalized, add the DCID_GeoID field to the first location
        # - the TMCF generated in generate_schema_and_tmcf.py expect to find the
        # geoID in the field "DCID_GeoID"
        normalized_table.insert(0, "DCID_GeoID",
                                data_table.apply(fips_to_geoid, axis=1))
        new_output_path = rename_gcs_file_path(output_path, nri_month_year)
        normalized_table.to_csv(out_put_file_name)
        file_util.file_copy(out_put_file_name, new_output_path)
        new_input_file = rename_file(input_path, nri_month_year)
        os.rename(input_path, new_input_file)
    except FileNotFoundError as e:
        logging.error(f"FileNotFoundError: {e}")
    except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")


def main(argv):

    for input_path in INPUT_TO_OUTPUT_PATHS:
        out_put_file_name = INPUT_TO_OUTPUT_PATHS[input_path]
        output_path_new = FLAGS.output_path.rstrip(
            "/") + "/" + out_put_file_name
        process_csv(input_path, output_path_new, "output/csv_columns.json",
                    str(out_put_file_name))


if __name__ == "__main__":
    app.run(main)
