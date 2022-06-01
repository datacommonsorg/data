import pandas as pd
import numpy as np

INPUT_TO_OUTPUT_PATHS = {
    "source_data/NRI_Table_Counties.csv": "output/nri_counties_table.csv",
    "source_data/NRI_Table_CensusTracts.csv": "output/nri_tracts_table.csv",
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

def process_csv(input_path, output_path):
    data_table = pd.read_csv(input_path)

    # the TMCF generated in generate_schema_and_tmcf.py expect to find the
    # geoID in the field "DCID_GeoID"
    data_table["DCID_GeoID"] = data_table.apply(fips_to_geoid, axis=1)

    # we want to replace empty cells with 0s so that the import tool does not
    # have to assume what this is about [citation needed (snny)]
    data_table = data_table.fillna(0)

    data_table.to_csv(output_path)

if __name__ == "__main__":
    for input_path in INPUT_TO_OUTPUT_PATHS:
        output_path = INPUT_TO_OUTPUT_PATHS[input_path]
        process_csv(input_path, output_path)
