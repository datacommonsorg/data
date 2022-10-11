# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Replacement Functions for specific Column Values
which are common for all the US Education Inputs.
"""
import pandas as pd

_COEDUCATIONAL = {
    "1-Coed (school has male and female students)": "Coeducational",
    "2-All-female (school only has all-female students)": "AllFemale",
    "3-All-male (school only has all-male students)": "AllMale",
    "†": "",
    "–":""
}

_RELIGIOUS = {
    "1-Catholic": "Catholic",
    "2-Other religious": "Nonsectarian",
    "3-Nonsectarian": "OtherReligious",
    "†": ""
}

_SCHOOL_TYPE = {
    "1-Regular Elementary or Secondary":
        "NCES_RegularElementaryOrSecondarySchool",
    "2-Montessori":
        "NCES_MontessoriSchool",
    "3-Special Program Emphasis":
        "NCES_SpecialProgramEmphasisSchool",
    "4-Special Education":
        "NCES_SpecialEducationSchool",
    "5-Career/technical/vocational":
        "NCES_CareerOrTechnicalOrVocational",
    "6-Alternative/other":
        "NCES_AlternativeOrOtherSchool",
    "7-Early Childhood Program/child care center":
        "NCES_EarlyChildhoodProgramOrChildCareCenter",
    "†":
        "NCES_DataMissing",
    "–":"NCES_DataMissing",
}

_SCHOOL_GRADE = {
    "Elementary Teachers": "Elementary",
    "Secondary Teachers": "Secondary",
    "Prekindergarten and Kindergarten": "PreKindergartenAndKindergarten",
    "Prekindergarten": "PreKindergarten",
    "Ungraded Students":"NCESUngradedClasses",
    "Kindergarten": "Kindergarten",
    "Transitional Kindergarten": "TransitionalKindergarten",
    "Grades 1-8": "SchoolGrade1To8",
    "Grades 9-12": "SchoolGrade9To12",
    "1st grade": "SchoolGrade1",
    "1st Grade": "SchoolGrade1",
    "Grade 1": "SchoolGrade1",
    "2nd grade": "SchoolGrade2",
    "2nd Grade": "SchoolGrade2",
    "Grade 2": "SchoolGrade2",
    "3rd grade": "SchoolGrade3",
    "3rd Grade": "SchoolGrade3",
    "Grade 3": "SchoolGrade3",
    "4th grade": "SchoolGrade4",
    "4th Grade": "SchoolGrade4",
    "Grade 4": "SchoolGrade4",
    "5th grade": "SchoolGrade5",
    "5th Grade": "SchoolGrade5",
    "Grade 5": "SchoolGrade5",
    "6th grade": "SchoolGrade6",
    "6th Grade": "SchoolGrade6",
    "Grade 6": "SchoolGrade6",
    "7th grade": "SchoolGrade7",
    "7th Grade": "SchoolGrade7",
    "Grade 7": "SchoolGrade7",
    "8th grade": "SchoolGrade8",
    "8th Grade": "SchoolGrade8",
    "Grade 8": "SchoolGrade8",
    "9th grade": "SchoolGrade9",
    "9th Grade": "SchoolGrade9",
    "Grade 9": "SchoolGrade9",
    "10th grade": "SchoolGrade10",
    "10th Grade": "SchoolGrade10",
    "Grade 10": "SchoolGrade10",
    "11th grade": "SchoolGrade11",
    "11th Grade": "SchoolGrade11",
    "Grade 11": "SchoolGrade11",
    "12th grade": "SchoolGrade12",
    "12th Grade": "SchoolGrade12",
    "Grade 12": "SchoolGrade12",
    "13th grade": "SchoolGrade13",
    "13th Grade": "SchoolGrade13",
    "Grade 13": "SchoolGrade13",
    "Ungraded":"",
    "†": "",
    "–":"",
    # "All Ungraded": "",
    "Adult Education": "AdultEducation",
    "Transitional 1st grade":"TransitionalGrade1"
}

_PHYSICAL_ADD = {"†": "","–":""}

# pylint:disable=line-too-long
_SCHOOL_LEVEL = {
    "1-Elementary (school has one or more of grades K-6 and does not have any grade higher than the 8th grade).":
        "ElementarySchool",
    "2-Secondary (school has one or more of grades 7-12 and does not have any grade lower than 7th grade).":
        "SecondarySchool",
    "3-Combined (school has one or more of grades K-6 and one or more of grades 9-12. Schools in which all students are ungraded are also classified as combined).":
        "ElementarySchool__SecondarySchool",
    "†":
        "",
    "–":""
}
# pylint:enable=line-too-long

_RACE_ = {
    "American Indian/Alaska Native": "AmericanIndianOrAlaskaNative",
    "Asian or Asian/Pacific Islander": "Asian",
    "Black or African American": "Black",
    "BlackOrAfricanAmericanAlone": "Black",
    'Nat. Hawaiian or Other Pacific Isl.': 'HawaiianNativeOrPacificIslander',
    "Hispanic": "HispanicOrLatino",
    'White': 'White',
    "Two or More Races": "TwoOrMoreRaces",
    "Black": "Black"
}

_LUNCH = {
    "Reduced-price Lunch": "ReducedLunch",
    "Free and Reduced Lunch": "FreeOrReducedLunch",
    "Free Lunch": "FreeLunch"
}

_SCHOOL_STAFF = {
    "Paraprofessionals/Instructional Aides":
        "ParaprofessionalsAidesOrInstructionalAides",
    "Instructional Coordinators":
        "InstructionalCoordinators",
    "Elementary School Counselor":
        "ElementarySchoolCounselor",
    "Secondary School Counselor":
        "SecondarySchoolCounselor",
    "Other Guidance Counselors":
        "SchoolOtherGuidanceCounselors",
    "Total Guidance Counselors":
        "TotalGuidanceCounselors",
    "Librarians/media specialists":
        "LibrariansSpecialistsOrMediaSpecialists",
    "Media Support Staff":
        "MediaSupportStaff",
    "LEA Administrators":
        "LEAAdministrators",
    "LEA Administrative Support Staff":
        "LEAAdministrativeSupportStaff",
    "School Administrators":
        "SchoolAdministrators",
    "School Administrative Support Staff":
        "SchoolAdministrativeSupportStaff",
    "Student Support Services Staff":
        "StudentSupportServicesStaff",
    "School Psychologist":
        "SchoolPsychologist",
    "Other Support Services Staff":
        "SchoolOtherSupportServicesStaff",
    "†":
        "",
}

COLUMNS = {
    "Private School Name": "Private_School_Name",
    "School ID - NCES Assigned": "SchoolID",
    "School Type": "School_Type",
    "School Level": "School_Level",
    "School's Religious Affiliation or Orientation": "School_Religion",
    "Lowest Grade Taught": "Lowest_Grade",
    "Highest Grade Taught": "Highest_Grade",
    "Physical Address": "Physical_Address",
    "Phone Number": "PhoneNumber"
}

_GENDER = {"female": "Female", "male": "Male"}

_LOCALE = {"†":"","–":"",": Mid-size":": Midsize"}
_UNREADABLE_TEXT = {"†":"","–":""}


def replace_values(data_df: pd.DataFrame, replace_with_all_mappers=False):
    """
    Replaces columns values with the defined mappers.
    """
    cols_mapper = {
        "Coeducational": _COEDUCATIONAL,
        "School's Religious Affiliation or Orientation": _RELIGIOUS,
        "Lowest Grade Taught": _SCHOOL_GRADE,
        "Highest Grade Taught": _SCHOOL_GRADE,
        "School Type": _SCHOOL_TYPE,
        "School Level": _SCHOOL_LEVEL,
        "Race": _RACE_,
        "Lunch": _LUNCH,
        "SchoolStaff": _SCHOOL_STAFF,
        "Gender": _GENDER,
        "Physical Address": _PHYSICAL_ADD,
        "Physical_Address": _PHYSICAL_ADD,
        "ZIP": _UNREADABLE_TEXT,
        "Phone Number": _UNREADABLE_TEXT,
        "PhoneNumber": _UNREADABLE_TEXT,
        "Agency_level":_UNREADABLE_TEXT,
        "Lowest_Grade": _SCHOOL_GRADE,
        "Highest_Grade": _SCHOOL_GRADE,
        "Latitude": _UNREADABLE_TEXT,
        "Longitude": _UNREADABLE_TEXT,
        "Locale_temp": _LOCALE,
        "School_Type":_UNREADABLE_TEXT,
        "State_school_ID": _UNREADABLE_TEXT,
        "School_level": _UNREADABLE_TEXT,
        "County_code": _UNREADABLE_TEXT,
        "City":_UNREADABLE_TEXT,
        "LowestGrade":_UNREADABLE_TEXT,
        "HighestGrade":_UNREADABLE_TEXT
    }

    df_columns = data_df.columns.to_list()
    for column, replacements in cols_mapper.items():
        if replace_with_all_mappers:
            data_df = data_df.replace(replacements, regex=True)
            continue
        if column in df_columns:
            if isinstance(replacements, list):
                for replacement in replacements:
                    data_df = data_df.replace({column: replacement})
            else:
                data_df = data_df.replace({column: replacements})

    return data_df
