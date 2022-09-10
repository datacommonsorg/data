CSV_FILE_NAME = "us_nces_public_school.csv"
MCF_FILE_NAME = "us_nces_public_school.mcf"
TMCF_FILE_NAME = "us_nces_public_school.tmcf"
SCHOOL_TYPE = "publicschool"
SPLIT_HEADER_ON_SCHOOL_TYPE = "[Public School]"

POSSIBLE_DATA_COLUMNS = [
    ".*Students.*",
    ".*Lunch.*",
    ".*Teacher.*",
    ".*American.*",
    ".*Asian.*",
    ".*Hispanic.*",
    ".*Black.*",
    ".*White.*",
    ".*Adult Education.*"
]

EXCLUDE_DATA_COLUMNS = [
   'Migrant Students', 'Total Students - Calculated Sum of Reported Grade Totals', 'Total Students All Grades',
   'Ungraded', 'Unknown', 'unknown', 'Total Race/Ethnicity', 'Grades 1-8 Students', 'Grades 9-12 Students'
]