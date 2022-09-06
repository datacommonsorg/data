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
}

_RELIGIOUS = {
    "1-Catholic": "Catholic",
    "2-Other religious": "Nonsectarian",
    "3-Nonsectarian": "OtherReligious"
}

_SCHOOL_TYPE = {
    "1-Regular Elementary or Secondary": \
        "NCES_PrivateSchoolTypeRegularElementaryOrSecondary",
    "2-Montessori": \
        "NCES_PrivateSchoolTypeMontessori",
    "3-Special Program Emphasis": \
        "NCES_PrivateSchoolTypeSpecialProgramEmphasis",
    "4-Special Education": \
        "NCES_PrivateSchoolTypeSpecialEducation",
    "5-Career/technical/vocational": \
        "NCES_PrivateSchoolTypeCareerOrTechnicalOrVocational",
    "6-Alternative/other": \
        "NCES_PrivateSchoolTypeAlternativeOrOther",
    "7-Early Childhood Program/child care center": \
        "NCES_PrivateSchoolTypeEarlyChildhoodProgramOrChildCareCenter",
    "†": "NCES_PrivateSchoolTypeDataMissing"
}

_SCHOOL_GRADE = {
    "Grade 5 Students [Private School] 1997-98"
    "Prekindergarten": "PreKindergarten",
    "Kindergarten": "Kindergarten",
    "Transitional Kindergarten": "TransitionalKindergarten",
    "1st grade": "SchoolGrade1",
    "2nd grade": "SchoolGrade2",
    "3rd grade": "SchoolGrade3",
    "4th grade": "SchoolGrade4",
    "5th grade": "SchoolGrade5",
    "6th grade": "SchoolGrade6",
    "7th grade": "SchoolGrade7",
    "8th grade": "SchoolGrade8",
    "9th grade": "SchoolGrade9",
    "10th grade": "SchoolGrade10",
    "Grade 10 Students": "SchoolGrade10",
    "11th grade": "SchoolGrade11",
    "Grade 11 Students": "SchoolGrade11",
    "12th grade": "SchoolGrade12",
    "Grade 12 Students": "SchoolGrade12",
    "13th grade": "SchoolGrade13",
    "†": "YetToDefine",
    "All Ungraded": "AllUngrade",
   
    
}

{
    
}

_SCHOOL_LEVEL = {
    "1-Elementary (school has one or more of grades K-6 and does not have any grade higher than the 8th grade).": "ElementarySchool",
    "2-Secondary (school has one or more of grades 7-12 and does not have any grade lower than 7th grade).": "SecondarySchool",
    "3-Combined (school has one or more of grades K-6 and one or more of grades 9-12. Schools in which all students are ungraded are also classified as combined).": "ElementarySchool__SecondarySchool"
}

_RACE_ = {
    "American Indian/Alaska Native Students": "AmericanIndianOrAlaskaNative",
    "Asian or Asian/Pacific Islander Students": "AsianOrPacificIslander",
    "Black or African American Student":"BlackOrAfricanAmericanAlone",
    'Nat. Hawaiian or Other Pacific Isl. Students':'dcs:HawaiianNativeOrPacificIslander',
    "Hispanic Students":"HispanicOrLatino",
    'Two or More Races Students':'TwoOrMoreRaces',
    'White Students':'White',
}

def replace_values(data_df: pd.DataFrame):

    cols_mapper = {
        "Coeducational": _COEDUCATIONAL,
        "School's Religious Affiliation or Orientation": _RELIGIOUS,
        "Lowest Grade Taught": _SCHOOL_GRADE,
        "Highest Grade Taught": _SCHOOL_GRADE,
        "School Type": _SCHOOL_TYPE,
        "School Level": _SCHOOL_LEVEL,
        # "Race": _RACE_,
        "sv_name": [_RACE_, _SCHOOL_GRADE]
    }

    df_columns = data_df.columns.to_list()
    for column, replacements in cols_mapper.items():
       if column in df_columns:
            if isinstance(replacements, list):
                for replacement in replacements:
                    data_df = data_df.replace({column: replacement})
            else:
                data_df = data_df.replace({column: replacements})

    return data_df