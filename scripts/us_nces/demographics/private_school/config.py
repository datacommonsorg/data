CSV_FILE_NAME = "us_nces_private_school.csv"
MCF_FILE_NAME = "us_nces_private_school.mcf"
TMCF_FILE_NAME = "us_nces_private_school.tmcf"
SCHOOL_TYPE = "privateschool"
SPLIT_HEADER_ON_SCHOOL_TYPE = "[Private School]"

POSSIBLE_DATA_COLUMNS = [
    ".*Students.*",
    ".*Teacher.*",
    "Percentage.*",
    # 'Grade 6 Students', 'Grade 4 Students', 'Grade 9 Students', 'Grade 10 Students'
    # 'Prekindergarten Students', 'Kindergarten Students'
]

EXCLUDE_DATA_COLUMNS = [
   "Total Students","Prekindergarten and Kindergarten Students", "Ungraded Students",	"Grades 1-8 Students" ,	"Grades 9-12 Students" 
]

