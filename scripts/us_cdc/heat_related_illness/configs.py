URLS_CONFIG = [
    "https://ephtracking.cdc.gov/qr/370/1/ALL/ALL/1/{year}/0?apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
    "https://ephtracking.cdc.gov/qr/431/1/ALL/ALL/1/{year}/0?apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
    "https://ephtracking.cdc.gov/qr/431/3/ALL/ALL/1/{year}/0?AgeBandId=1,2,3,4,5&apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
    "https://ephtracking.cdc.gov/qr/431/4/ALL/ALL/1/{year}/0?GenderId=1,2&apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
    "https://ephtracking.cdc.gov/qr/431/37/ALL/ALL/1/{year}/0?AgeBandId=1,2,3,4,5&GenderId=1,2&apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
    "https://ephtracking.cdc.gov/qr/438/1/ALL/ALL/1/{year}/0?apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
    "https://ephtracking.cdc.gov/qr/438/3/ALL/ALL/1/{year}/0?AgeBandId=1,2,3,4,5&apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
    "https://ephtracking.cdc.gov/qr/438/4/ALL/ALL/1/{year}/0?GenderId=1,2&apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
    "https://ephtracking.cdc.gov/qr/438/37/ALL/ALL/1/{year}/0?AgeBandId=1,2,3,4,5&GenderId=1,2&apiToken=637DD2EF-507F-4938-8380-54A179C3132A"
]

INPUT_HTML_FILES = "./source_data/html_files/"

INPUT_CSV_FILES = "./source_data/csv_files"

COMBINED_INPUT_CSV_FILE = "./input_files/"

STRING_TO_MATCH = [
    "deaths", "hospitalizations", "hospitalization_age",
    "hospitalizatin_gender", "hospitlizations_age_gender", "edVisits",
    "edVisit_age", "edVists_gender", "edVsits_age_gender"
]

CONFIG_PATH = "./config.json"

OUTPUT_PATH = "./output_files"

_TMCF_TEMPLATE = ("Node: E:EPHHeatIllness->E0\n"
                  "typeOf: dcs:StatVarObservation\n"
                  "measurementMethod: C:EPHHeatIllness->measurementMethod\n"
                  "observationAbout: C:EPHHeatIllness->Geo\n"
                  "observationDate: C:EPHHeatIllness->Year\n"
                  "variableMeasured: C:EPHHeatIllness->StatVar\n"
                  "observationPeriod: P5M\n"
                  "value: C:EPHHeatIllness->Quantity\n")
