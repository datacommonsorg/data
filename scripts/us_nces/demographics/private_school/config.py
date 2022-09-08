CSV_FILE_NAME = "us_nces_private_school.csv"
MCF_FILE_NAME = "us_nces_private_school.mcf"
TMCF_FILE_NAME = "us_nces_private_school.tmcf"
SCHOOL_TYPE = "privateschool"
SPLIT_HEADER_ON_SCHOOL_TYPE = "[Private School]"

POSSIBLE_DATA_COLUMNS = [
    ".*Teacher.*", #"Percentage.*", ".*Students.*"
]

EXCLUDE_DATA_COLUMNS = [
   "Total Students (Ungraded & PK-12)","Total Students (Ungraded & K-12)", 	"Prekindergarten and Kindergarten Students", "Ungraded Students",	"Grades 1-8 Students" ,	"Grades 9-12 Students" 
]

TEACHER_MCF_PROP = (
    "Node: dcid:Count_Teacher\n"
    "populationType: dcs:Teacher\n"
    "statType: dcs:measuredValue\n"
    "measuredProperty: dcs:count")

STUDENT_TEACHER_MCF_PROP = (
     "Node: dcid:Percent_Student_AsAFractionOf_Count_Teacher\n"
    "populationType: dcs:Teacher\n"
    "statType: dcs:measuredValue\n"
    "measuredProperty: dcs:count\n"
    "measurementDenominator: dcs:Count_Teacher"

)

ADDITIONAL_MCF_NODES = [TEACHER_MCF_PROP, STUDENT_TEACHER_MCF_PROP]

