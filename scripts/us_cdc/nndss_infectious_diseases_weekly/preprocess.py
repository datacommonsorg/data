# Copyright 2026 Google LLC
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
"""Download, preprocess, and combine CDC NNDSS Weekly data (2006-present)."""

import datetime
import importlib.util
import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from absl import app
from absl import flags
from absl import logging
import pandas as pd

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    "historical_gcs_bucket",
    "unresolved_mcf",
    "GCS bucket containing the 2006-2021 historical baseline CSV.",
)
flags.DEFINE_string(
    "historical_gcs_blob",
    "cdc/nndss_infectious_diseases_weekly/20250206/cdc_nndss_weekly_tables.csv",
    "GCS blob path for the 2006-2021 historical baseline CSV.",
)
flags.DEFINE_string(
    "historical_local_path",
    "",
    "Optional local path to the historical baseline CSV (skips GCS download).",
)
flags.DEFINE_string(
    "input_csv",
    "",
    "Optional local path to NNDSS Socrata CSV (skips CDC download).",
)
flags.DEFINE_string(
    "output_dir",
    "",
    "Output directory for cdc_nndss_weekly_tables.csv and .tmcf.",
)
flags.DEFINE_bool(
    "skip_historical",
    False,
    "If True, skip merging the 2006-2021 historical baseline.",
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
RAW_FILENAME = "rows.csv"
INPUT_FILE = os.path.join(INPUT_DIR, RAW_FILENAME)
HISTORICAL_LOCAL_FILE = os.path.join(
    INPUT_DIR, "historical_cdc_nndss_weekly_tables.csv"
)
SOURCE_URL = (
    "https://data.cdc.gov/api/views/x9gk-5huc/rows.csv"
    "?accessType=DOWNLOAD&api_foundry=true"
)
MEASUREMENT_METHOD = "dcs:CDC_NNDSS_Diseases_WeeklyTables"
HISTORICAL_CUTOFF_DATE = "2022-01-01"
SKIP_FLAGS = {"N", "NN", "NP", "NC", "U"}

TMCF_CONTENT = """Node: E:NNDSWeekly->E0
typeOf: dcs:StatVarObservation
measurementMethod: C:NNDSWeekly->measurementMethod
observationAbout: C:NNDSWeekly->observationAbout
observationDate: C:NNDSWeekly->observationDate
variableMeasured: C:NNDSWeekly->variableMeasured
value: C:NNDSWeekly->value
observationPeriod: C:NNDSWeekly->observationPeriod
"""

OUTPUT_COLUMNS = [
    "observationDate",
    "observationAbout",
    "observationPeriod",
    "variableMeasured",
    "value",
    "measurementMethod",
]

# Canonical StatVar DCIDs (without residentStatus suffix) for CDC x9gk-5huc Labels.
# Labels mapped to None are intentionally ignored (e.g. Rabies, Animal; non-HPS
# Hantavirus; or diseases without canonical StatVars).
LABEL_TO_BASE_SV: Dict[str, Optional[str]] = {
    "Anthrax": "Count_MedicalConditionIncident_ConditionAnthraxDisease",
    "Arboviral diseases, Chikungunya virus disease": "Count_MedicalConditionIncident_ConditionChikungunya",
    "Chikungunya virus diseases": "Count_MedicalConditionIncident_ConditionChikungunya",
    "Arboviral diseases, Eastern equine encephalitis virus disease": "Count_MedicalConditionIncident_ConditionEasternEquineEncephalitis",
    "Arboviral diseases, Jamestown Canyon  virus disease": "Count_MedicalConditionIncident_ConditionJamestownCanyonVirusDisease",
    "Arboviral diseases, Jamestown Canyon": "Count_MedicalConditionIncident_ConditionJamestownCanyonVirusDisease",
    "Arboviral diseases, La Crosse  virus disease": "Count_MedicalConditionIncident_ConditionLaCrosseVirusDisease",
    "Arboviral diseases, La Crosse": "Count_MedicalConditionIncident_ConditionLaCrosseVirusDisease",
    "Arboviral diseases, Powassan virus disease": "Count_MedicalConditionIncident_ConditionPowassanVirusDisease",
    "Arboviral diseases, Powassan virus": "Count_MedicalConditionIncident_ConditionPowassanVirusDisease",
    "Arboviral diseases, St. Louis encephalitis virus disease": None,
    "Arboviral diseases, St. Louis encephalitis": None,
    "Arboviral diseases, West Nile virus disease": "Count_MedicalConditionIncident_ConditionWestNileVirusDisease",
    "Arboviral diseases, West Nile": "Count_MedicalConditionIncident_ConditionWestNileVirusDisease",
    "Arboviral diseases, Western equine encephalitis virus disease": None,
    "Arboviral diseases, Western equine encephalitis": None,
    "Babesiosis": "Count_MedicalConditionIncident_ConditionBabesiosis",
    "Botulism, Foodborne": "Count_MedicalConditionIncident_ConditionFoodborneBotulism",
    "Botulism, foodborne": "Count_MedicalConditionIncident_ConditionFoodborneBotulism",
    "Botulism, Infant": "Count_MedicalConditionIncident_ConditionInfantBotulism",
    "Botulism, infant": "Count_MedicalConditionIncident_ConditionInfantBotulism",
    "Botulism, Other (wound & unspecified)": "Count_MedicalConditionIncident_ConditionWoundBotulism",
    "Botulism, other (includes wound)": "Count_MedicalConditionIncident_ConditionWoundBotulism",
    "Brucellosis": "Count_MedicalConditionIncident_ConditionBrucellosis",
    "COVID-19-associated pediatric mortality": None,
    "Campylobacteriosis": "Count_MedicalConditionIncident_ConditionCampylobacteriosis",
    "Candida auris, clinical": "Count_MedicalConditionIncident_ConditionCandidaAuris_ClinicalCase",
    "Candida auris, screening": None,
    "Carbapenemase-producing carbapenem-resistant Enterobacteriaceae": "Count_MedicalConditionIncident_ConditionCarbapenemResistantEnterobacteriaceae",
    "Carbapenemase-Producing Organisms (CPO), Total": None,
    "Carbapenemase-Producing Organisms (CPO),Total": None,
    "Chancroid": "Count_MedicalConditionIncident_ConditionChancroid",
    "Chlamydia trachomatis infection": "Count_MedicalConditionIncident_ConditionChlamydia",
    "Cholera": "Count_MedicalConditionIncident_ConditionCholera",
    "Cholera (toxigenic Vibrio cholerae O1 or O139)": "Count_MedicalConditionIncident_ConditionCholera",
    "Coccidioidomycosis": "Count_MedicalConditionIncident_ConditionCoccidioidomycosis",
    "Coccidioidomycosis, Total": "Count_MedicalConditionIncident_ConditionCoccidioidomycosis",
    "Coccidioidomycosis, total": "Count_MedicalConditionIncident_ConditionCoccidioidomycosis",
    "Coccidioidomycosis, Confirmed": None,
    "Coccidioidomycosis, confirmed": None,
    "Coccidioidomycosis, Probable": None,
    "Coccidioidomycosis, probable": None,
    "Cronobacter invasive infection, infants, Confirmed": None,
    "Cronobacter invasive infection, infants, Probable": None,
    "Cryptosporidiosis": "Count_MedicalConditionIncident_ConditionCryptosporidiosis",
    "Cyclosporiasis": "Count_MedicalConditionIncident_ConditionCyclosporiasis",
    "Dengue virus infections, Dengue": "Count_MedicalConditionIncident_ConditionDengueDisease",
    "Dengue": "Count_MedicalConditionIncident_ConditionDengueDisease",
    "Dengue virus infections, Dengue-like illness": "Count_MedicalConditionIncident_ConditionDengueLikeIllness",
    "Dengue-like illness": "Count_MedicalConditionIncident_ConditionDengueLikeIllness",
    "Dengue virus infections, Severe dengue": "Count_MedicalConditionIncident_ConditionSevereDengue",
    "Dengue, severe": "Count_MedicalConditionIncident_ConditionSevereDengue",
    "Ehrlichiosis and Anaplasmosis, Anaplasma phagocytophilum infection": "Count_MedicalConditionIncident_ConditionHumanGranulocyticAnaplasmosis",
    "Anaplasma phagocytophilum": "Count_MedicalConditionIncident_ConditionHumanGranulocyticAnaplasmosis",
    "Ehrlichiosis and Anaplasmosis, Ehrlichia chaffeensis infection": "Count_MedicalConditionIncident_ConditionHumanMonocyticEhrlichiosis",
    "Ehrlichia chaffeensis": "Count_MedicalConditionIncident_ConditionHumanMonocyticEhrlichiosis",
    "Ehrlichiosis and Anaplasmosis, Ehrlichia ewingii infection": "Count_MedicalConditionIncident_ConditionEhrlichiaEwingiiInfection",
    "Ehrlichia ewingii": "Count_MedicalConditionIncident_ConditionEhrlichiaEwingiiInfection",
    "Ehrlichiosis and Anaplasmosis, Undetermined ehrlichiosis/anaplasmosis": "Count_MedicalConditionIncident_ConditionEhrlichiosis",
    "Ehrlichiosis/Anaplasmosis, undetermined": "Count_MedicalConditionIncident_ConditionEhrlichiosis",
    "Giardiasis": "Count_MedicalConditionIncident_ConditionGiardiasis",
    "Gonorrhea": "Count_MedicalConditionIncident_ConditionGonorrhea",
    "Haemophilus influenzae, invasive disease, Age <5 years, Non-b serotype": "Count_MedicalConditionIncident_5_LessYears_ConditionHaemophilusInfluenzae_InvasiveDisease_NonSerotypeB",
    "Haemophilus influenzae invasive disease, <5 years, other serotype (represents non-b serotype)": "Count_MedicalConditionIncident_5_LessYears_ConditionHaemophilusInfluenzae_InvasiveDisease_NonSerotypeB",
    "Haemophilus influenzae, invasive disease, Age <5 years, Nontypeable": "Count_MedicalConditionIncident_5_LessYears_ConditionHaemophilusInfluenzae_InvasiveDisease_OtherSerogroups",
    "Haemophilus influenzae invasive disease, <5 years, not typeable": "Count_MedicalConditionIncident_5_LessYears_ConditionHaemophilusInfluenzae_InvasiveDisease_OtherSerogroups",
    "Haemophilus influenzae, invasive disease, Age <5 years, Serotype b": "Count_MedicalConditionIncident_5_LessYears_ConditionHaemophilusInfluenzae_InvasiveDisease_SerotypeB",
    "Haemophilus influenzae invasive disease, <5 years, serotype B": "Count_MedicalConditionIncident_5_LessYears_ConditionHaemophilusInfluenzae_InvasiveDisease_SerotypeB",
    "Haemophilus influenzae, invasive disease, Age <5 years, Unknown serotype": "Count_MedicalConditionIncident_5_LessYears_ConditionHaemophilusInfluenzae_InvasiveDisease_UnknownSerotype",
    "Haemophilus influenzae invasive disease, <5 years, unknown or missing serotype": "Count_MedicalConditionIncident_5_LessYears_ConditionHaemophilusInfluenzae_InvasiveDisease_UnknownSerotype",
    "Haemophilus influenzae, invasive disease, All ages, all serotypes": "Count_MedicalConditionIncident_ConditionHaemophilusInfluenzae_InvasiveDisease",
    "Haemophilus influenzae, invasive disease": "Count_MedicalConditionIncident_ConditionHaemophilusInfluenzae_InvasiveDisease",
    "Hansen's disease": "Count_MedicalConditionIncident_ConditionLeprosy",
    "Leprosy (Hansen's disease)": "Count_MedicalConditionIncident_ConditionLeprosy",
    "Hantavirus infection, non-hantavirus pulmonary syndrome": None,
    "Hantavirus infection, non-Hantavirus Pulmonary Syndrome": None,
    "Hantavirus pulmonary syndrome": "Count_MedicalConditionIncident_ConditionHantavirusPulmonarySyndrome",
    "Hemolytic uremic syndrome post-diarrheal": "Count_MedicalConditionIncident_ConditionHemolyticUremicSyndrome_PostDiarrheal",
    "Hemolytic uremic syndrome postdiarrheal": "Count_MedicalConditionIncident_ConditionHemolyticUremicSyndrome_PostDiarrheal",
    "Hepatitis, A, acute": "Count_MedicalConditionIncident_ConditionHepatitisA_AcuteCondition",
    "Hepatitis A, acute": "Count_MedicalConditionIncident_ConditionHepatitisA_AcuteCondition",
    "Hepatitis A, Confirmed": None,
    "Hepatitis, B, acute": "Count_MedicalConditionIncident_ConditionHepatitisB_AcuteCondition",
    "Hepatitis B, acute": "Count_MedicalConditionIncident_ConditionHepatitisB_AcuteCondition",
    "Hepatitis B, acute, Confirmed": None,
    "Hepatitis B, acute, Probable": None,
    "Hepatitis B, chronic, Confirmed": None,
    "Hepatitis B, chronic, Probable": None,
    "Hepatitis B, perinatal infection": "Count_MedicalConditionIncident_ConditionHepatitisB_AcuteCondition_PerinatalInfection",
    "Hepatitis B, perinatal": "Count_MedicalConditionIncident_ConditionHepatitisB_AcuteCondition_PerinatalInfection",
    "Hepatitis B, perinatal, Confirmed": None,
    "Hepatitis C, acute, Confirmed": "Count_MedicalConditionIncident_ConditionHepatitisC_AcuteCondition_ConfirmedCase",
    "Hepatitis C, acute, confirmed": "Count_MedicalConditionIncident_ConditionHepatitisC_AcuteCondition_ConfirmedCase",
    "Hepatitis C, acute, Probable": "Count_MedicalConditionIncident_ConditionHepatitisC_AcuteCondition_ProbableCase",
    "Hepatitis C, acute, probable": "Count_MedicalConditionIncident_ConditionHepatitisC_AcuteCondition_ProbableCase",
    "Hepatitis C, chronic, Confirmed": None,
    "Hepatitis C, chronic, Probable": None,
    "Hepatitis C, perinatal infection": "Count_MedicalConditionIncident_ConditionHepatitisC_AcuteCondition_PerinatalInfection",
    "Hepatitis C, perinatal": "Count_MedicalConditionIncident_ConditionHepatitisC_AcuteCondition_PerinatalInfection",
    "Hepatitis C, perinatal, Confirmed": None,
    "Influenza-associated pediatric mortality": "Count_MedicalConditionIncident_ConditionInfluenza_PediatricMortality",
    "Invasive pneumococcal disease, age <5 years, Confirmed": "Count_MedicalConditionIncident_5_LessYears_ConditionStreptococcusPneumonia_InvasiveDisease_ConfirmedCase",
    "Invasive pneumococcal disease <5, confirmed": "Count_MedicalConditionIncident_5_LessYears_ConditionStreptococcusPneumonia_InvasiveDisease_ConfirmedCase",
    "Invasive pneumococcal disease, age <5 years, Probable": "Count_MedicalConditionIncident_5_LessYears_ConditionStreptococcusPneumonia_InvasiveDisease_ProbableCase",
    "Invasive pneumococcal disease <5, probable": "Count_MedicalConditionIncident_5_LessYears_ConditionStreptococcusPneumonia_InvasiveDisease_ProbableCase",
    "Invasive pneumococcal disease, all ages, Confirmed": "Count_MedicalConditionIncident_ConditionStreptococcusPneumonia_InvasiveDisease_ConfirmedCase",
    "Invasive pneumococcal disease, confirmed": "Count_MedicalConditionIncident_ConditionStreptococcusPneumonia_InvasiveDisease_ConfirmedCase",
    "Invasive pneumococcal disease, all ages, Probable": "Count_MedicalConditionIncident_ConditionStreptococcusPneumonia_InvasiveDisease_ProbableCase",
    "Invasive pneumococcal disease, probable": "Count_MedicalConditionIncident_ConditionStreptococcusPneumonia_InvasiveDisease_ProbableCase",
    "Legionellosis": "Count_MedicalConditionIncident_ConditionLegionnairesDisease",
    "Leptospirosis": "Count_MedicalConditionIncident_ConditionLeptospirosis",
    "Listeriosis, Confirmed": "Count_MedicalConditionIncident_ConditionListeriosis_ConfirmedCase",
    "Listeriosis confirmed": "Count_MedicalConditionIncident_ConditionListeriosis_ConfirmedCase",
    "Listeriosis, Probable": "Count_MedicalConditionIncident_ConditionListeriosis_ProbableCase",
    "Listeriosis probable": "Count_MedicalConditionIncident_ConditionListeriosis_ProbableCase",
    "Malaria": "Count_MedicalConditionIncident_ConditionMalaria",
    "Measles, Imported": "Count_MedicalConditionIncident_ConditionMeasles_ImportedCase",
    "Measles (rubeola), imported": "Count_MedicalConditionIncident_ConditionMeasles_ImportedCase",
    "Measles, Indigenous": "Count_MedicalConditionIncident_ConditionMeasles_IndigenousCase",
    "Measles (rubeola), indigenous": "Count_MedicalConditionIncident_ConditionMeasles_IndigenousCase",
    "Melioidosis": None,
    "Meningococcal disease, All serogroups": "Count_MedicalConditionIncident_ConditionMeningococcalMeningitis",
    "Meningococcal disease (Neisseria meningitidis)": "Count_MedicalConditionIncident_ConditionMeningococcalMeningitis",
    "Meningococcal disease, Other serogroups": "Count_MedicalConditionIncident_ConditionMeningococcalMeningitis_OtherSerogroups",
    "Infection with Neisseria meningitidis, serogroup other": "Count_MedicalConditionIncident_ConditionMeningococcalMeningitis_OtherSerogroups",
    "Meningococcal disease, Serogroup B": "Count_MedicalConditionIncident_ConditionMeningococcalMeningitis_SerogroupB",
    "Infection with Neisseria meningitidis, serogroup B": "Count_MedicalConditionIncident_ConditionMeningococcalMeningitis_SerogroupB",
    "Meningococcal disease, Serogroups ACWY": "Count_MedicalConditionIncident_ConditionMeningococcalMeningitis_ACWYSerogroup",
    "Infection with Neisseria meningitidis, vaccine serogroup (A,C,Y, W-135)": "Count_MedicalConditionIncident_ConditionMeningococcalMeningitis_ACWYSerogroup",
    "Meningococcal disease, Unknown serogroup": "Count_MedicalConditionIncident_ConditionMeningococcalMeningitis_UnknownSerogroups",
    "Infection with Neisseria meningitidis, serogroup unknown": "Count_MedicalConditionIncident_ConditionMeningococcalMeningitis_UnknownSerogroups",
    "Mpox": None,
    "Mumps": "Count_MedicalConditionIncident_ConditionMumps",
    "Novel Influenza A virus infections": "Count_MedicalConditionIncident_ConditionNovelInfluenzaAViralInfection",
    "Novel Influenza A virus infections, Total": "Count_MedicalConditionIncident_ConditionNovelInfluenzaAViralInfection",
    "Novel influenza A virus infections, initial detections of": "Count_MedicalConditionIncident_ConditionNovelInfluenzaAViralInfection",
    "Novel Influenza A virus infections, Confirmed": None,
    "Novel Influenza A virus infections, Probable": None,
    "Oropouche, non-congenital": None,
    "Pertussis": "Count_MedicalConditionIncident_ConditionPertussis",
    "Plague": "Count_MedicalConditionIncident_ConditionPlague",
    "Poliomyelitis, paralytic": None,
    "Poliovirus infection, nonparalytic": None,
    "Psittacosis": "Count_MedicalConditionIncident_ConditionPsittacosis",
    "Psittacosis (Ornithosis)": "Count_MedicalConditionIncident_ConditionPsittacosis",
    "Q fever, Acute": "Count_MedicalConditionIncident_ConditionQFever_AcuteCondition",
    "Q fever, acute": "Count_MedicalConditionIncident_ConditionQFever_AcuteCondition",
    "Q fever, Chronic": "Count_MedicalConditionIncident_ConditionQFever_ChronicCondition",
    "Q fever, chronic": "Count_MedicalConditionIncident_ConditionQFever_ChronicCondition",
    "Q fever, Total": "Count_MedicalConditionIncident_ConditionQFever",
    "Q fever, total": "Count_MedicalConditionIncident_ConditionQFever",
    "Rabies, Animal": None,
    "Rabies, Human": "Count_MedicalConditionIncident_ConditionRabiesinhuman",
    "Rabies, human": "Count_MedicalConditionIncident_ConditionRabiesinhuman",
    "Rubella": "Count_MedicalConditionIncident_ConditionRubella",
    "Rubella, congenital syndrome": "Count_MedicalConditionIncident_ConditionRubella_CongenitalDisease",
    "Salmonella Paratyphi infection": None,
    "Salmonella Typhi infection": None,
    "Salmonella enterica Typhi (S.Typhi) infection": None,
    "Salmonella enterica serotypes Paratyphi A, B (tartrate negative) and C (S. Paratyphi) infection": None,
    "SalmonellaParatyphi infection": None,
    "Salmonellosis (excluding Salmonella Typhi infection and Salmonella Paratyphi infection)": "Count_MedicalConditionIncident_ConditionSalmonellosisExceptTyphiAndParatyphi",
    "Salmonellosis (excluding S. Typhi infection and S. Paratyphi infection)": "Count_MedicalConditionIncident_ConditionSalmonellosisExceptTyphiAndParatyphi",
    "Severe acute respiratory syndrome-associated coronavirus disease": None,
    "Severe Acute Respiratory Syndrome (SARS)-associated Coronavirus disease (SARS-CoV)": None,
    "Shiga toxin-producing Escherichia coli (STEC)": "Count_MedicalConditionIncident_ConditionShigaToxinEColi",
    "Shigellosis": "Count_MedicalConditionIncident_ConditionShigellosis",
    "Smallpox": None,
    "Streptococcal toxic shock syndrome": "Count_MedicalConditionIncident_ConditionStreptococcalToxicShockSyndrome",
    "Syphilis, Congenital": "Count_MedicalConditionIncident_ConditionCongenitalSyphilis",
    "Syphilis, congenital": "Count_MedicalConditionIncident_ConditionCongenitalSyphilis",
    "Syphilis, Primary and secondary": "Count_MedicalConditionIncident_ConditionSyphilisPrimaryAndSecondary",
    "Tetanus": "Count_MedicalConditionIncident_ConditionTetanus",
    "Toxic shock syndrome (other than Streptococcal)": "Count_MedicalConditionIncident_ConditionToxicShockSyndromExceptStreptococcal",
    "Toxic-shock syndrome (other than streptococcal)": "Count_MedicalConditionIncident_ConditionToxicShockSyndromExceptStreptococcal",
    "Trichinellosis": "Count_MedicalConditionIncident_ConditionTrichinellosis",
    "Tuberculosis": "Count_MedicalConditionIncident_ConditionTuberculosis",
    "Tularemia": "Count_MedicalConditionIncident_ConditionTularemia",
    "Vancomycin-intermediate Staphylococcus aureus": "Count_MedicalConditionIncident_ConditionVancomycinIntermediateStaphylococcusAureus",
    "Vancomycin-intermediate Staphylococcus aureus (VISA)": "Count_MedicalConditionIncident_ConditionVancomycinIntermediateStaphylococcusAureus",
    "Vancomycin-resistant Staphylococcus aureus": "Count_MedicalConditionIncident_ConditionVancomycinResistantStaphylococcusAureus",
    "Vancomycin-resistant Staphylococcus aureus (VRSA)": "Count_MedicalConditionIncident_ConditionVancomycinResistantStaphylococcusAureus",
    "Varicella disease": "Count_MedicalConditionIncident_ConditionChickenpox",
    "Varicella morbidity": "Count_MedicalConditionIncident_ConditionChickenpox",
    "Varicella (Chickenpox)": "Count_MedicalConditionIncident_ConditionChickenpox",
    "Vibriosis (any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139), Confirmed": "Count_MedicalConditionIncident_ConditionVibriosisExcludingCholera_ConfirmedCase",
    "Vibriosis, confirmed": "Count_MedicalConditionIncident_ConditionVibriosisExcludingCholera_ConfirmedCase",
    "Vibriosis (any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139), Probable": "Count_MedicalConditionIncident_ConditionVibriosisExcludingCholera_ProbableCase",
    "Vibriosis, probable": "Count_MedicalConditionIncident_ConditionVibriosisExcludingCholera_ProbableCase",
    "Yellow fever": None,
    "Zika virus disease, non-congenital": "Count_MedicalConditionIncident_ConditionZikaVirusDisease_NonCongenitalDisease",
}

# Lowercased Reporting Area -> (observationAbout DCID, residentStatus suffix)
AREA_MAP: Dict[str, Tuple[Optional[str], str]] = {
    "ALABAMA": ("geoId/01", ""),
    "ALASKA": ("geoId/02", ""),
    "AMERICAN SAMOA": ("geoId/60", ""),
    "ARIZONA": ("geoId/04", ""),
    "ARKANSAS": ("geoId/05", ""),
    "CALIFORNIA": ("geoId/06", ""),
    "COLORADO": ("geoId/08", ""),
    "COMMONWEALTH OF NORTHERN MARIANA ISLANDS": ("geoId/69", ""),
    "CONNECTICUT": ("geoId/09", ""),
    "DELAWARE": ("geoId/10", ""),
    "DISTRICT OF COLUMBIA": ("geoId/11", ""),
    "EAST NORTH CENTRAL": ("usc/EastNorthCentralDivision", ""),
    "EAST SOUTH CENTRAL": ("usc/EastSouthCentralDivision", ""),
    "FLORIDA": ("geoId/12", ""),
    "GEORGIA": ("geoId/13", ""),
    "GUAM": ("geoId/66", ""),
    "HAWAII": ("geoId/15", ""),
    "IDAHO": ("geoId/16", ""),
    "ILLINOIS": ("geoId/17", ""),
    "INDIANA": ("geoId/18", ""),
    "IOWA": ("geoId/19", ""),
    "KANSAS": ("geoId/20", ""),
    "KENTUCKY": ("geoId/21", ""),
    "LOUISIANA": ("geoId/22", ""),
    "MAINE": ("geoId/23", ""),
    "MARYLAND": ("geoId/24", ""),
    "MASSACHUSETTS": ("geoId/25", ""),
    "MICHIGAN": ("geoId/26", ""),
    "MIDDLE ATLANTIC": ("usc/MiddleAtlanticDivision", ""),
    "MINNESOTA": ("geoId/27", ""),
    "MISSISSIPPI": ("geoId/28", ""),
    "MISSOURI": ("geoId/29", ""),
    "MONTANA": ("geoId/30", ""),
    "MOUNTAIN": ("usc/MountainDivision", ""),
    "NEBRASKA": ("geoId/31", ""),
    "NEVADA": ("geoId/32", ""),
    "NEW ENGLAND": ("usc/NewEnglandDivision", ""),
    "NEW HAMPSHIRE": ("geoId/33", ""),
    "NEW JERSEY": ("geoId/34", ""),
    "NEW MEXICO": ("geoId/35", ""),
    "NEW YORK": ("NEW_YORK_EX_NYC", ""),
    "NEW YORK CITY": ("geoId/3651000", ""),
    "NON-U.S. RESIDENTS": ("country/USA", "NonUSResident"),
    "NON-US RESIDENTS": ("country/USA", "NonUSResident"),
    "NORTH CAROLINA": ("geoId/37", ""),
    "NORTH DAKOTA": ("geoId/38", ""),
    "NORTHERN MARIANA ISLANDS": ("geoId/69", ""),
    "OHIO": ("geoId/39", ""),
    "OKLAHOMA": ("geoId/40", ""),
    "OREGON": ("geoId/41", ""),
    "PACIFIC": ("usc/PacificDivision", ""),
    "PENNSYLVANIA": ("geoId/42", ""),
    "PUERTO RICO": ("geoId/72", ""),
    "RHODE ISLAND": ("geoId/44", ""),
    "SOUTH ATLANTIC": ("usc/SouthAtlanticDivision", ""),
    "SOUTH CAROLINA": ("geoId/45", ""),
    "SOUTH DAKOTA": ("geoId/46", ""),
    "TENNESSEE": ("geoId/47", ""),
    "TEXAS": ("geoId/48", ""),
    "TOTAL": ("country/USA", ""),
    "U.S. RESIDENTS": ("country/USA", "USResident"),
    "US RESIDENTS": ("country/USA", "USResident"),
    "U.S. TERRITORIES": (None, ""),
    "US TERRITORIES": (None, ""),
    "U.S. VIRGIN ISLANDS": ("geoId/78", ""),
    "VIRGIN ISLANDS OF THE U.S.": ("geoId/78", ""),
    "UTAH": ("geoId/49", ""),
    "VERMONT": ("geoId/50", ""),
    "VIRGINIA": ("geoId/51", ""),
    "WASHINGTON": ("geoId/53", ""),
    "WEST NORTH CENTRAL": ("usc/WestNorthCentralDivision", ""),
    "WEST SOUTH CENTRAL": ("usc/WestSouthCentralDivision", ""),
    "WEST VIRGINIA": ("geoId/54", ""),
    "WISCONSIN": ("geoId/55", ""),
    "WYOMING": ("geoId/56", ""),
}

_SEROTYPE_INFIX_PREFIXES = (
    "Count_MedicalConditionIncident_5_LessYears_ConditionHaemophilusInfluenzae_InvasiveDisease_",
    "Count_MedicalConditionIncident_ConditionMeningococcalMeningitis_",
)


def apply_resident_suffix(base_sv: str, suffix: str) -> str:
    """Apply USResident / NonUSResident suffix in canonical StatVar DCID order."""
    if not suffix:
        return base_sv
    for prefix in _SEROTYPE_INFIX_PREFIXES:
        if base_sv.startswith(prefix):
            tail = base_sv[len(prefix):]
            return f"{prefix}{suffix}_{tail}"
    return f"{base_sv}_{suffix}"


def _start_date_of_year(year: int) -> datetime.date:
    """Return the first day of the first MMWR week for a given year."""
    jan_one = datetime.date(year, 1, 1)
    diff = 7 * (jan_one.isoweekday() > 3) - jan_one.isoweekday()
    return jan_one + datetime.timedelta(days=diff)


def get_mmwr_week_start_date(year, week) -> Optional[str]:
    """Compute ISO YYYY-MM-DD start date for a given MMWR year and week."""
    try:
        y = int(year)
        w = int(week)
    except (ValueError, TypeError):
        return None
    if not (1 <= w <= 53):
        logging.warning(f"Invalid MMWR WEEK found: {w}. Skipping.")
        return None
    day_one = _start_date_of_year(y)
    dt = day_one + datetime.timedelta(days=7 * (w - 1))
    return dt.isoformat()


def _format_number(val: float) -> str:
    """Format integer-valued floats without trailing .0."""
    if val.is_integer():
        return str(int(val))
    return str(val)


def download_source_csv() -> str:
    """Download x9gk-5huc CSV from CDC with exponential backoff retry."""
    util_script_path = os.path.abspath(
        os.path.join(SCRIPT_DIR, "../../../util/download_util_script.py")
    )
    spec = importlib.util.spec_from_file_location(
        "download_util_script", util_script_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load download_util_script from {util_script_path}"
        )
    download_util_script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(download_util_script)
    download_file = download_util_script.download_file

    max_attempts = 3
    retry_delay = 5
    download_ok = False
    for attempt in range(1, max_attempts + 1):
        try:
            logging.info(f"Download attempt {attempt}/{max_attempts}...")
            if os.path.exists(INPUT_FILE):
                os.remove(INPUT_FILE)
            download_ok = download_file(
                url=SOURCE_URL,
                output_folder=INPUT_DIR,
                unzip=False,
                headers=None,
                tries=3,
                delay=5,
                backoff=2,
            )
            if download_ok and os.path.exists(INPUT_FILE):
                logging.info("Download completed successfully.")
                break
            logging.warning(
                f"Download attempt {attempt}/{max_attempts} returned {download_ok}."
            )
        except Exception as exc:
            logging.warning(
                f"Download attempt {attempt}/{max_attempts} raised {exc}."
            )
        if attempt < max_attempts:
            time.sleep(retry_delay)
            retry_delay *= 2

    if not download_ok or not os.path.exists(INPUT_FILE):
        logging.error("Failed to download rows.csv after all retry attempts.")
        sys.exit(1)

    size_mb = os.path.getsize(INPUT_FILE) / (1024 * 1024)
    logging.info(f"Downloaded file size: {size_mb:.2f} MB.")
    if size_mb < 0.1:
        logging.error("Downloaded file is suspiciously small (<0.1 MB).")
        sys.exit(1)
    return INPUT_FILE


def load_historical_rows(
    local_path: str, gcs_bucket: str, gcs_blob: str
) -> pd.DataFrame:
    """Load 2006-2021 historical observations from local path or GCS."""
    csv_path = local_path
    if not csv_path:
        from google.cloud import storage

        logging.info(
            f"Downloading historical archive from gs://{gcs_bucket}/{gcs_blob}..."
        )
        client = storage.Client()
        bucket = client.bucket(gcs_bucket)
        blob = bucket.blob(gcs_blob)
        blob.download_to_filename(HISTORICAL_LOCAL_FILE)
        csv_path = HISTORICAL_LOCAL_FILE

    df = pd.read_csv(csv_path, usecols=OUTPUT_COLUMNS, dtype=str)
    df = df[df["observationDate"] < HISTORICAL_CUTOFF_DATE].copy()
    logging.info(f"Loaded {len(df)} historical rows (< {HISTORICAL_CUTOFF_DATE}).")
    return df


def process_x9gk_csv(filepath: str) -> pd.DataFrame:
    """Transform x9gk-5huc Socrata CSV into cleaned Data Commons observation rows."""
    records = []
    # Track numeric NY (ex-NYC) and NYC values per (observationDate, variableMeasured)
    ny_components: Dict[Tuple[str, str], float] = {}

    reader = pd.read_csv(
        filepath, chunksize=100000, dtype=str, low_memory=False, on_bad_lines="skip"
    )
    for chunk_idx, chunk in enumerate(reader, start=1):
        logging.info(f"Processing x9gk-5huc chunk {chunk_idx}...")
        if "Current week" not in chunk.columns:
            raise KeyError("Missing required column 'Current week' in input CSV.")

        # Filter to valid numeric Current week rows without suppression flags
        if "Current week, flag" in chunk.columns:
            flag_series = chunk["Current week, flag"].fillna("").str.strip()
            chunk = chunk[~flag_series.isin(SKIP_FLAGS)]

        chunk = chunk[chunk["Current week"].notna()].copy()
        chunk["val_num"] = pd.to_numeric(chunk["Current week"], errors="coerce")
        chunk = chunk[chunk["val_num"].notna() & (chunk["val_num"] >= 0)]
        if chunk.empty:
            continue

        # Map Labels -> base StatVar DCID
        chunk["base_sv"] = chunk["Label"].map(LABEL_TO_BASE_SV)
        chunk = chunk[chunk["base_sv"].notna()]
        if chunk.empty:
            continue

        # Compute MMWR observationDate using unique (year, week) cache
        yw_pairs = chunk[["Current MMWR Year", "MMWR WEEK"]].drop_duplicates()
        date_lookup = {
            (r["Current MMWR Year"], r["MMWR WEEK"]): get_mmwr_week_start_date(
                r["Current MMWR Year"], r["MMWR WEEK"]
            )
            for _, r in yw_pairs.iterrows()
        }
        chunk["observationDate"] = [
            date_lookup.get((y, w))
            for y, w in zip(chunk["Current MMWR Year"], chunk["MMWR WEEK"])
        ]
        chunk = chunk[chunk["observationDate"].notna()]

        # Row iteration using dict records for clarity
        for rec in chunk[
            ["Reporting Area", "observationDate", "base_sv", "val_num"]
        ].to_dict("records"):
            area_key = str(rec["Reporting Area"]).strip().upper()
            area_info = AREA_MAP.get(area_key)
            if area_info is None:
                continue
            place_dcid, res_suffix = area_info
            if place_dcid is None:
                continue

            obs_date = rec["observationDate"]
            sv_dcid = apply_resident_suffix(rec["base_sv"], res_suffix)
            val_num = float(rec["val_num"])

            if place_dcid == "NEW_YORK_EX_NYC":
                key = (obs_date, sv_dcid)
                ny_components[key] = ny_components.get(key, 0.0) + val_num
                continue

            if place_dcid == "geoId/3651000":
                key = (obs_date, sv_dcid)
                ny_components[key] = ny_components.get(key, 0.0) + val_num

            records.append(
                {
                    "observationDate": obs_date,
                    "observationAbout": place_dcid,
                    "observationPeriod": "P1W",
                    "variableMeasured": sv_dcid,
                    "value": _format_number(val_num),
                    "measurementMethod": MEASUREMENT_METHOD,
                }
            )

    # Emit summed New York State (geoId/36 = NY ex-NYC + NYC)
    for (obs_date, sv_dcid), total_val in ny_components.items():
        records.append(
            {
                "observationDate": obs_date,
                "observationAbout": "geoId/36",
                "observationPeriod": "P1W",
                "variableMeasured": sv_dcid,
                "value": _format_number(total_val),
                "measurementMethod": MEASUREMENT_METHOD,
            }
        )

    out_df = pd.DataFrame(records, columns=OUTPUT_COLUMNS)
    if not out_df.empty:
        out_df = out_df.drop_duplicates(
            subset=[
                "observationDate",
                "observationAbout",
                "observationPeriod",
                "variableMeasured",
            ],
            keep="last",
        )
    logging.info(f"Processed {len(out_df)} observations from x9gk-5huc.")
    return out_df


def main(argv):
    del argv
    Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)
    output_dir = _FLAGS.output_dir or os.path.join(SCRIPT_DIR, "output")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    source_csv = _FLAGS.input_csv or download_source_csv()
    recent_df = process_x9gk_csv(source_csv)

    if _FLAGS.skip_historical:
        combined_df = recent_df
    else:
        hist_df = load_historical_rows(
            _FLAGS.historical_local_path,
            _FLAGS.historical_gcs_bucket,
            _FLAGS.historical_gcs_blob,
        )
        combined_df = pd.concat([hist_df, recent_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(
            subset=[
                "observationDate",
                "observationAbout",
                "observationPeriod",
                "variableMeasured",
            ],
            keep="last",
        )

    out_csv = os.path.join(output_dir, "cdc_nndss_weekly_tables.csv")
    out_tmcf = os.path.join(output_dir, "cdc_nndss_weekly_tables.tmcf")
    combined_df.to_csv(out_csv, index=False)
    with open(out_tmcf, "w", encoding="utf-8") as f:
        f.write(TMCF_CONTENT)
    logging.info(f"Wrote {len(combined_df)} total rows to {out_csv} and {out_tmcf}.")


if __name__ == "__main__":
    app.run(main)
