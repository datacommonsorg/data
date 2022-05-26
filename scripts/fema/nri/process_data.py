import pandas as pd
import numpy as np

INPUT_DATA_PATH = "source_data/NRI_Table_Counties.csv"
OUTPUT_DATA_PATH = "output/nri_counties_table.csv"

data_table = pd.read_csv(INPUT_DATA_PATH)

# we zfill to 5, because in a State-County FIPS, state takes up to
# 2 digis and the county 3 (for a total of 5), however, in the FEMA
# dataset, the trailing zero for States with State FIPS < 10 is ommitted
# for example;
# California State FIPS is 6
# Alameda County, CA FIPS is 1.
# The correct GeoId would be 06001
# However, the FEMA study puts this down at 6001 in the STCOFIPS field
fips_to_geoid = lambda row: "geoId/" + str(row["STCOFIPS"]).zfill(5) 

# the TMCF generated in generate_schema_and_tmcf.py expect to find the 
# geoID in the field "DCID_GeoID"
data_table["DCID_GeoID"] = data_table.apply(fips_to_geoid, axis = 1)

# we want to replace empty cells with 0s so that the import tool does not
# have to assume what this is about [citation needed (snny)]
data_table = data_table.fillna(0)

data_table.to_csv(OUTPUT_DATA_PATH)
