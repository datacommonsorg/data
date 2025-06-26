# Copyright 2025 Google LLC
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
import numpy as np

_COEDUCATIONAL = {
    "1-Coed (school has male and female students)": "Coeducational",
    "2-All-female (school only has all-female students)": "AllFemale",
    "3-All-male (school only has all-male students)": "AllMale",
    np.nan: "",
    "–": ""
}

_RELIGIOUS_AFFILIATION = {
    "1-Catholic": "Catholic",
    "2-Other religious": "OtherReligious",
    "3-Nonsectarian": "Nonsectarian",
    np.nan: ""
}

_RELIGIOUS = {
    "–":
        "",
    "African Methodist Episcopal":
        "AfricanMethodistEpiscopal",
    "Amish":
        "Amish",
    "Assembly of God":
        "AssemblyOfGod",
    "Baptist":
        "Baptist",
    "Brethren":
        "Brethren",
    "Calvinist":
        "Calvinism",
    "Christian (no specific denomination)":
        "Christianity",
    "Church of Christ":
        "ChurchOfChrist",
    "Church of God":
        "ChurchOfGod",
    "Church of God in Christ":
        "ChurchOfGodInChrist",
    "Church of the Nazarene":
        "ChurchOfTheNazarene",
    "Disciples of Christ":
        "DisciplesOfChrist",
    "Episcopal":
        "Episcopalians",
    "Evangelical Lutheran Church in America (formerly AELC or ALC or LCA)":
        "EvangelicalLutheranChurchInAmerica",
    "Friends":
        "FriendsChurch",
    "Greek Orthodox":
        "GreekOrthodox",
    "Islamic":
        "Islam",
    "Jewish":
        "Judaism",
    "Latter Day Saints":
        "LatterDaySaints",
    "Lutheran Church – Missouri Synod":
        "LutheranChurchMissouriSynod",
    "Mennonite":
        "Mennonite",
    "Methodist":
        "Methodism",
    "Nonsectarian":
        "Nonsectarian",
    "Other":
        "NCES_OtherReligion",
    "Other Lutheran":
        "NCES_OtherLutheran",
    "Pentecostal":
        "Pentecostalism",
    "Presbyterian":
        "Presbyterian",
    "Roman Catholic":
        "RomanCatholicism",
    "Seventh–Day Adventist":
        "SeventhDayAdventist",
    "Wisconsin Evangelical Lutheran Synod":
        "WisconsinEvangelicalLutheranSynod",
    "Catholic":
        "Catholicism",
    np.nan:
        ""
}

_SCHOOL_TYPE = {
    "1-Regular Elementary or Secondary":
        "NCES_Regular",
    "1-Regular Elementary or Secondary":
        "NCES_Regular",
    "2-Montessori":
        "Montessori",
    "3-Special Program Emphasis":
        "NCES_SpecialProgramEmphasis",
    "4-Special Education":
        "NCES_SpecialEducation",
    "5-Career/technical/vocational":
        "NCES_CareerOrTechnicalOrVocational",
    "6-Alternative/other":
        "NCES_AlternativeOrOther",
    "7-Early Childhood Program/child care center":
        "NCES_EarlyChildhoodProgramOrChildCareCenter",
    np.nan:
        "NCES_DataMissing",
    "–":
        "NCES_DataMissing",
}

_SCHOOL_GRADE = {
    "Elementary Teachers": "ElementaryTeacher",
    "Secondary Teachers": "SecondaryTeacher",
    "Prekindergarten and Kindergarten": "PreKindergartenAndKindergarten",
    "Prekindergarten": "PreKindergarten",
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
    np.nan: "NCES_GradeDataMissing",
    "–": "NCES_GradeDataMissing",
    "All Ungraded": "NCESUngradedClasses",
    "Adult Education": "AdultEducation",
    "Transitional 1st grade": "TransitionalGrade1",
    "Ungraded Students": "UngradedClasses",
    "Ungraded Teachers": "UngradedTeacher"
}

_SCHOOL_GRADE_PLACE = {
    "Elementary Teachers": "Elementary",
    "Secondary Teachers": "Secondary",
    "Prekindergarten and Kindergarten": "PreKindergartenAndKindergarten",
    "Ungraded": "NCESUngradedClasses",
    "Prekindergarten": "PreKindergarten",
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
    np.nan: "NCES_GradeDataMissing",
    "–": "NCES_GradeDataMissing",
    "Adult Education": "AdultEducation",
    "Transitional 1st grade": "TransitionalGrade1"
}

_PHYSICAL_ADD = {np.nan: "", "–": "", "Po Box": "PO BOX"}

# pylint:disable=line-too-long
_SCHOOL_LEVEL = {
    "1-Elementary (school has one or more of grades K-6 and does not have any grade higher than the 8th grade).":
        "ElementarySchool",
    "1-ElementarySchool (school has one or more of grades K-6 and does not have any grade higher than the 8th grade).":
        "ElementarySchool",
    "2-Secondary (school has one or more of grades 7-12 and does not have any grade lower than 7th grade).":
        "SecondarySchool",
    "3-Combined (school has one or more of grades K-6 and one or more of grades 9-12. Schools in which all students are ungraded are also classified as combined).":
        "ElementarySchool__SecondarySchool__UngradedSchool",
    "1-Primary":
        "PrimarySchool",
    "Middle":
        "MiddleSchool",
    "2-Middle":
        "MiddleSchool",
    "Elementary":
        "ElementarySchool",
    "High":
        "HighSchool",
    "3-High":
        "HighSchool",
    "Not Reported":
        "NCES_SchoolLevelDataMissing",
    "Prekindergarten":
        "PreKindergarten",
    "Not Applicable":
        "NCES_SchoolLevelDataNotApplicable",
    "Other":
        "NCES_SchoolLevelOther",
    "4-Other":
        "NCES_SchoolLevelOther",
    "Adult Education":
        "AdultEducation",
    "Ungraded":
        "UngradedSchool",
    "Secondary":
        "SecondarySchool",
    np.nan:
        "",
    "–":
        ""
}
# pylint:enable=line-too-long

_RACE_ = {
    "American Indian/Alaska Native": "AmericanIndianOrAlaskaNative",
    "Asian or Asian/Pacific Islander": "Asian",
    "Black or African American": "Black",
    "BlackOrAfricanAmericanAlone": "Black",
    "Nat. Hawaiian or Other Pacific Isl.": "HawaiianNativeOrPacificIslander",
    "Hispanic": "HispanicOrLatino",
    # 'White': 'White',
    "Two or More Races": "TwoOrMoreRaces",
    "Black": "Black"
}

_LUNCH = {
    "Reduced-price Lunch":
        "ReducedLunch",
    "Free and Reduced Lunch":
        "DirectCertificationLunch",
    "Free Lunch":
        "FreeLunch",
    "No":
        "NCES_NationalSchoolLunchProgramNo",
    "Yes participating without using any Provision or the CEO":
        "NCES_NationalSchoolLunchProgramYesWithoutAnyProvisionOrCEO",
    "Yes under Community Eligibility Option (CEO)":
        "NCES_NationalSchoolLunchProgramYesUnderCEO",
    "Yes under Provision 1":
        "NCES_NationalSchoolLunchProgramYesUnderProvision1",
    "Yes under Provision 2":
        "NCES_NationalSchoolLunchProgramYesUnderProvision2",
    "Yes under Provision 3":
        "NCES_NationalSchoolLunchProgramYesUnderProvision3",
    np.nan:
        "NCES_MagnetDataMissing",
    "–":
        "NCES_MagnetDataMissing"
}

_SCHOOL_STAFF = {
    "Paraprofessionals/Instructional Aides":
        "ParaProfessionalsAidesOrInstructionalAide",
    "Instructional Coordinators":
        "InstructionalCoordinatorOrSupervisor",
    "Elementary School Counselor":
        "ElementarySchoolCounselor",
    "Secondary School Counselor":
        "SecondarySchoolCounselor",
    "Other Guidance Counselors":
        "SchoolOtherGuidanceCounselor",
    "Total Guidance Counselors":
        "TotalGuidanceCounselor",
    "Librarians/media specialists":
        "LibrariansSpecialistsOrMediaSpecialist",
    "Media Support Staff":
        "MediaSupportStaff",
    "LEA Administrators":
        "LEAAdministrator",
    "LEA Administrative Support Staff":
        "LEAAdministrativeSupportStaff",
    "School Administrators":
        "SchoolAdministrator",
    "School Administrative Support Staff":
        "SchoolAdministrativeSupportStaff",
    "Student Support Services Staff":
        "StudentSupportServicesStaff",
    "School Psychologist":
        "SchoolPsychologist",
    "Other Support Services Staff":
        "SchoolOtherSupportServicesStaff",
    "Elementary Teachers":
        "ElementaryTeacher",
    "Secondary Teachers":
        "SecondaryTeacher",
    "Ungraded Teachers":
        "UngradedTeacher",
    np.nan:
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

_LOCALE = {
    '13-City: Small': "NCES_CitySmall",
    '21-Suburb: Large': "NCES_SuburbLarge",
    '32-Town: Distant': "NCES_TownDistant",
    '11-City: Large': "NCES_CityLarge",
    '42-Rural: Distant': "NCES_RuralDistant",
    '23-Suburb: Small': "NCES_SuburbSmall",
    '22-Suburb: Mid-size': "NCES_SuburbMidsize",
    '41-Rural: Fringe': "NCES_RuralFringe",
    '12-City: Mid-size': "NCES_CityMidsize",
    '33-Town: Remote': "NCES_TownRemote",
    '31-Town: Fringe': "NCES_TownFringe",
    '43-Rural: Remote': "NCES_RuralRemote",
    np.nan: "NCES_LocaleDataMissing",
    "–": "NCES_LocaleDataMissing"
}

_UNREADABLE_TEXT = {"–": np.nan, "†": np.nan}

_NAN = {np.nan: "", "nan": ""}

_CITY = {np.nan: "", "–": "", " ": ""}

_MAGNET = {
    "1-Yes": "NCES_MagnetYes",
    "2-No": "NCES_MagnetNo",
    np.nan: "NCES_MagnetDataMissing",
    "–": "NCES_MagnetDataMissing"
}

_CHARTER = {
    np.nan: "NCES_CharterDataMissing",
    "1-Yes": "NCES_CharterYes",
    "2-No": "NCES_CharterNo",
    "–": "NCES_CharterDataMissing"
}

_TITLE = {
    np.nan:
        "NCES_TitleISchoolStatusDataMissing",
    "–":
        "NCES_TitleISchoolStatusDataMissing",
    "6-Not a Title I school":
        "NCES_TitleISchoolStatusNotEligible",
    "5-Title I schoolwide school":
        "NCES_TitleISchoolStatusSWPAndTASProgram",
    "4-Title I schoolwide eligible school-No program":
        "NCES_TitleISchoolStatusSWPNoTASProgram",
    "1-Title I targeted assistance eligible school-No program":
        "NCES_TitleISchoolStatusTASNoTASProgram",
    "3-Title I schoolwide eligible-Title I targeted assistance program":
        "NCES_TitleISchoolStatusTASAndTASProgram",
    "2-Title I targeted assistance school":
        "NCES_TitleISchoolStatusTASNoTASProgram"
}

_SCHOOL_PUBLIC_TYPE = {
    "1-Regular school": "NCES_PublicSchoolTypeRegular",
    "4-Alternative/other school": "NCES_PublicSchoolTypeOther",
    "2-Special education school": "NCES_PublicSchoolTypeSpecialEducation",
    "3-Vocational school": "NCES_PublicSchoolTypeVocational",
    np.nan: "NCES_PublicSchoolTypeDataMissing",
    "–": "NCES_PublicSchoolTypeDataMissing"
}

_STATE_NAME = {
    'DODEA (Overseas and Domestic)':
        'NCES_DepartmentOfDefenseEducationActivity',
    "Bureau of Indian Education":
        "NCES_BureauOfIndianEducation",
    "DEPARTMENT OF DEFENSE EDUCATION ACTIVITY":
        "NCES_DepartmentOfDefenseEducationActivity",
    "DEPARTMENT OF DEFENSE":
        "NCES_DepartmentOfDefenseEducationActivity"
}


def replace_values(data_df: pd.DataFrame,
                   replace_with_all_mappers=False,
                   regex_flag=True):
    """
    Replaces columns values with the defined mappers.
    """
    cols_mapper = {
        "Coeducational": _COEDUCATIONAL,
        "School_Religion_Affiliation": _RELIGIOUS_AFFILIATION,
        "School_Religion": _RELIGIOUS,
        "School_Type": _SCHOOL_TYPE,
        "SchoolGrade": _SCHOOL_LEVEL,
        "Race": _RACE_,
        "Lunch": _LUNCH,
        "SchoolStaff": _SCHOOL_STAFF,
        "Gender": _GENDER,
        "Physical Address": _PHYSICAL_ADD,
        "Physical_Address": _PHYSICAL_ADD,
        "ZIP": _NAN,
        "Phone Number": _NAN,
        "PhoneNumber": _NAN,
        "Agency_level": _NAN,
        "Lowest_Grade": _SCHOOL_GRADE,
        "Highest_Grade": _SCHOOL_GRADE,
        "Latitude": _NAN,
        "Longitude": _NAN,
        "Locale": _LOCALE,
        "State_school_ID": _NAN,
        "School_level": _NAN,
        "County_code": _NAN,
        "ZIP4": _NAN,
        "City": _CITY,
        "Highest_Grade_Dist": _SCHOOL_GRADE_PLACE,
        "Lowest_Grade_Dist": _SCHOOL_GRADE_PLACE,
        "Highest_Grade_Public": _SCHOOL_GRADE_PLACE,
        "Lowest_Grade_Public": _SCHOOL_GRADE_PLACE,
        "Charter_School": _CHARTER,
        "School_Type_Public": _SCHOOL_PUBLIC_TYPE,
        "Title_I_School_Status": _TITLE,
        "Magnet_School": _MAGNET,
        "National_School_Lunch_Program": _LUNCH,
        "Location_ZIP4": _NAN,
        "prop_race": _RACE_,
        "prop_schoolGradeLevel": _SCHOOL_GRADE,
        "prop_gender": _GENDER,
        "prop_lunchEligibility": _LUNCH,
        "prop_facultyType": _SCHOOL_STAFF,
        "Agency_Name": _NAN,
        "School_Level_17": _SCHOOL_LEVEL,
        "School_Level_16": _SCHOOL_LEVEL,
        "State_Agency_ID": _NAN,
        "State_School_ID": _NAN,
        "State_Name": _STATE_NAME
    }

    df_columns = data_df.columns.to_list()
    for column, replacements in cols_mapper.items():
        if replace_with_all_mappers:
            data_df = data_df.replace(replacements, regex=regex_flag)
            continue
        if column in df_columns:
            if isinstance(replacements, list):
                for replacement in replacements:
                    data_df = data_df.replace({column: replacement},
                                              regex=regex_flag)
            else:
                data_df = data_df.replace({column: replacements},
                                          regex=regex_flag)
    return data_df
