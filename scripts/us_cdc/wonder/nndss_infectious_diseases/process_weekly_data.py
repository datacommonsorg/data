import numpy as np
import os
import sys
import re
import string
import datetime
import pandas as pd
from absl import app, flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_statvar_dcid

FLAGS = flags.FLAGS

#TODO: Some of the functions defined here can be used while processing the annual tables and hence making the common functions as a module is preferred.

_TEMPLATE_MCF = """Node: E:NNDSWeekly->E0
typeOf: dcs:StatVarObservation
measurementMethod: C:NNDSWeekly->measurementMethod 
observationAbout: C:NNDSWeekly->observationAbout
observationDate: C:NNDSWeekly->observationDate
variableMeasured: C:NNDSWeekly->variableMeasured
value: C:NNDSWeekly->value
observationPeriod: C:NNDSWeekly->observationPeriod
"""

#NOTE: At the moment, we are ignoring the non-integer value of reported disease incidents.
_FORMAT_UNREPORTED_CASES = {
    '-': '',
    'U': '',
    'N': '',
    'NN': '',
    'NP': '',
    'NC': '',
    'P': '',
    '\*\*': ''
}

#NOTE: A map for different
_PV_MAP = {
    'confirmed': {
        'medicalStatus': 'dcs:ConfirmedCase'
    },
    'probable': {
        'medicalStatus': 'dcs:ProbableCase'
    },
    'pediatric mortality': {
        'medicalStatus': 'dcs:PediatricMortality'
    },
    'age <5': {
        'age': '[- 5 Years]'
    },
    'age < 5': {
        'age': '[- 5 Years]'
    },
    'age <5 years': {
        'age': '[- 5 Years]'
    },
    'age < 5 years': {
        'age': '[- 5 Years]'
    },
    'all serotypes': {
        'seroTypes': 'dcs:AllSerotypes'
    },
    'serotype b': {
        'seroTypes': 'dcs:BSerotype'
    },
    'unknown serotype': {
        'seroTypes': 'dcs:UnknownSerotype'
    },
    'non-b serotype': {
        'seroTypes': 'dcs:NonBSerotype'
    },
    'other serogroups': {
        'seroGroups': 'dcs:OtherSerogroups'
    },
    'unknown serogroup': {
        'seroGroups': 'dcs:UnknownSerogroups'
    },
    'all groups': {
        'seroGroups': 'dcs:AllSerogroups'
    },
    'all serogroups': {
        'seroGroups': 'dcs:AllSerogroups'
    },
    'serogroups ACWY': {
        'seroGroups': 'dcs:ACWYSerogroups'
    },
    'serogroup B': {
        'seroGroups': 'dcs:BSerogroup'
    },
    'group A': {
        'seroGroups': 'dcs:ASerogroup'
    },
    'perinatal infection': {
        'medicalCondition': 'dcs:PerinatalInfection'
    },
    'acute': {
        'medicalCondition': 'dcs:AcuteCase'
    },
    'chronic': {
        'medicalCondition': 'dcs:ChronicCase'
    },
    'imported': {
        'medicalCondition': 'dcs:ImportedCase'
    },
    'indigenous': {
        'medicalCondition': 'dcs:IndigenousCase'
    },
    'clinical': {
        'medicalCondition': 'dcs:ClinicalCase'
    }
}

#TODO: Resolve path based on the script path for tests
_PLACE_DCID_DF = pd.read_csv("./data/place_name_to_dcid.csv",
                             usecols=["Place Name", "Resolved place dcid"])
_DISEASE_DCID_DF = pd.read_csv("./data/diseases_map_to_pvs.csv")


def set_observationPeriod(column_name):
    if 'quarter' in column_name:
        return 'P1Q'
    return 'P1W'


# adapted from https://github.com/reichlab/pymmwr
def _start_date_of_year(year: int) -> datetime.date:
    """
    Return start date of the year using MMWR week rules
    """

    jan_one = datetime.date(year, 1, 1)
    diff = 7 * (jan_one.isoweekday() > 3) - jan_one.isoweekday()

    return jan_one + datetime.timedelta(days=diff)


def get_mmwr_week_end_date(year, week) -> datetime.date:
    """
    Return date from epiweek (starts at Sunday)
    """

    day_one = _start_date_of_year(year)
    diff = 7 * (week - 1)

    return day_one + datetime.timedelta(days=diff)


def resolve_reporting_places_to_dcids(place):
    try:
        # remove non printable special characters from column name
        place = ''.join(filter(lambda x: x in string.printable, place))
        place = place.strip()
        return _PLACE_DCID_DF.loc[(_PLACE_DCID_DF['Place Name'] == place),
                                  'Resolved place dcid'].values[0]
    except:
        # return empty string when no matches are found.
        return ''


_DISEASE_NAME_REMAP = {
    ## Rubella
    "Rubella, congenital syndrome":
        "Coccidioidomycosis",

    ## chicken pox
    'Current week;Varicella chickenpox':
        'Current week;Chickenpox',
    ';Varicella chickenpox;Current week':
        'Current week;Chickenpox',
    'Current week;Varicella morbidity':
        'Current week;Chickenpox',
    'Varicella morbidity;Current week':
        'Current week;Chickenpox',
    'Varicella chickenpox;Current week':
        'Current week;Chickenpox',

    ## Lyme Disease
    'Lyme Disease;Current week':
        'Lyme disease;Current week',
    'Current week;Lyme Disease':
        'Lyme disease;Current week',

    ## Other Salmonellosis
    'Current week;Salmonellosis excluding typhoid fever and paratyphoid fever':
        'Current week;Salmonellosis except Salmonella Typhi infection and Salmonella Paratyphi infection',
    'Current week;Salmonellosis except Salmonella Typhi infection and Salmonella Paratyphi infection'
    'Salmonellosis excluding typhoid fever and paratyphoid fever;Current week':
        'Current week;Salmonellosis except Salmonella Typhi infection and Salmonella Paratyphi infection',
    'Salmonellosis excluding typhoid fever and paratyphoid fever;Current week':
        'Current week;Salmonellosis except Salmonella Typhi infection and Salmonella Paratyphi infection',

    ## STEC
    'Current week;Shiga toxin-producing Escherichia coli':
        'Current week;Shiga toxin-producing Escherichia Coli',
    'Current week;Shiga toxin-producing E. coli STEC':
        'Current week;Shiga toxin-producing Escherichia Coli',
    'Shiga toxin-producing Escherichia coli;Current week':
        'Current week;Shiga toxin-producing Escherichia Coli',
    'Shiga toxin-producing E. coli STEC;Current week':
        'Current week;Shiga toxin-producing Escherichia Coli',
    'Shiga toxin-producing E. coli STEC ;Current week':
        'Current week;Shiga toxin-producing Escherichia Coli',
    'Current week;Shiga toxin-producing Escherichia coli':
        'Current week;Shiga toxin-producing Escherichia Coli',

    ## Other vibriosis
    'Vibriosis any species of the family Vibrionaceae , other than toxigenic Vibrio cholerae O1 or O139;Confirmed;Current week':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Vibriosis any species of the family Vibrionaceae , other than toxigenic Vibrio cholerae O1 or O139;Probable;Current week':
        'Vibriosis excluding Cholera;Probable;Current week',
    'Probable;Vibriosis Any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139;Current week':
        'Vibriosis excluding Cholera;Probable;Current week',
    'Current week;Confirmed;Vibriosis Any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Confirmed;Vibriosis Any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139;Current week':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Vibriosis Any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139;Probable;Current week':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Confirmed;Current week;Vibriosis any species of the family Vibrionaceae , other than toxigenic Vibrio cholerae O1 or O139':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Probable;Current week;Vibriosis any species of the family Vibrionaceae , other than toxigenic Vibrio cholerae O1 or O139':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Confirmed;Current week;Vibriosis Any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Probable;Current week;Vibriosis Any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139':
        'Vibriosis excluding Cholera;Probable;Current week',
    'Vibriosis any species of the family Vibrionaceae , other than toxigenic Vibrio cholerae O1 or O139;Current week;Confirmed':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Vibriosis any species of the family Vibrionaceae , other than toxigenic Vibrio cholerae O1 or O139;Current week;Probable':
        'Vibriosis excluding Cholera;Probable;Current week',
    'Vibriosis Any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139;Current week;Probable':
        'Vibriosis excluding Cholera;Probable;Current week',
    'Current week;Vibriosis any species of the family Vibrionaceae , other than toxigenic Vibrio cholerae O1 or O139;Probable':
        'Vibriosis excluding Cholera;Probable;Current week',
    'Vibriosis Any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139;Confirmed;Current week':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Confirmed;Vibriosis any species of the family Vibrionaceae , other than toxigenic Vibrio cholerae O1 or O139;Current week':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Current week;Vibriosis Any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139;Confirmed':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Vibriosis Any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139;Current week;Confirmed':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Current week;Vibriosis Any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139;Probable':
        'Vibriosis excluding Cholera;Probable;Current week',
    'Current week;Confirmed;Vibriosis any species of the family Vibrionaceae , other than toxigenic Vibrio cholerae O1 or O139':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Current week;Probable;Vibriosis any species of the family Vibrionaceae , other than toxigenic Vibrio cholerae O1 or O139':
        'Vibriosis excluding Cholera;Probable;Current week',
    'Current week;Vibriosis any species of the family Vibrionaceae , other than toxigenic Vibrio cholerae O1 or O139;Confirmed':
        'Vibriosis excluding Cholera;Confirmed;Current week',
    'Probable;Vibriosis any species of the family Vibrionaceae , other than toxigenic Vibrio cholerae O1 or O139;Current week':
        'Vibriosis excluding Cholera;Probable;Current week',
    'Current week;Probable;Vibriosis Any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139':
        'Vibriosis excluding Cholera;Probable;Current week',

    ## Syphilis
    ';Syphilis, primary & secondary;Current week':
        'Syphilis primary and secondary;Current week',
    ';Current week;Syphilis, primary & secondary':
        'Syphilis primary and secondary;Current week',
    'Syphilis, primary & secondary;Current week':
        'Syphilis primary and secondary;Current week',
    'Syphilis, primary & secondary;Unnamed: 11_level_0;Current week':
        'Syphilis primary and secondary;Current week',
    'Current week;Syphilis, primary and secondary':
        'Syphilis primary and secondary;Current week',
    'Current week;Spotted Fever Rickettsiosis;Syphilis, primary & secondary':
        'Syphilis primary and secondary;Current week',
    'Current week;Syphilis, primary & secondary':
        'Syphilis primary and secondary;Current week',
    'Current week;Syphilis, primary & secondary;Unnamed: 11_level_0':
        'Syphilis primary and secondary;Current week',
    'Syphilis, primary and secondary;Current week':
        'Syphilis primary and secondary;Current week',
    'Syphilis, Primary and secondary;Current week':
        'Syphilis primary and secondary;Current week',
    'Unnamed: 11_level_0Syphilis, Primary and secondary;Current week':
        'Syphilis primary and secondary;Current week',
    'Unnamed: 11_level_0Syphilis primary and secondary;Current week':
        'Syphilis primary and secondary;Current week',
    'Spotted Fever RickettsiosisSyphilis primary and secondary;Current week':
        'Syphilis primary and secondary;Current week',
    'Current week;Unnamed: 11_level_0;Syphilis, primary & secondary':
        'Syphilis primary and secondary;Current week',
    'Syphilis, primary & secondary;Spotted Fever Rickettsiosis;Current week':
        'Syphilis primary and secondary;Current week',

    ## Meningococcal diseases
    'Current week;Meningococcal diseases, invasive  All groups':
        'Current week;Meningococcal disease;All groups',
    'Meningococcal diseases, invasive  All serogroups;Current week':
        'Current week;Meningococcal disease;All groups',
    'Current week;Meningococcal diseases, invasive  All serogroups':
        'Current week;Meningococcal disease;All groups',
    'Current week;Meningococcal disease Neisseria meningitidis  All serogroups':
        'Current week;Meningococcal disease;All groups',
    'Meningococcal diseases, invasive  All groups;Current week':
        'Current week;Meningococcal disease;All groups',
    'Meningococcal disease Neisseria meningitidis  All serogroups;Current week':
        'Current week;Meningococcal disease;All groups',
    'Meningococcal diseases, invasive;Serogroup unknown;Current week':
        'Current week;Meningococcal disease;Unknown serogroup',
    'Serogroup unknown;Meningococcal diseases, invasive;Current week':
        'Current week;Meningococcal disease;Unknown serogroup',
    'Serogroup unknown;Current week;Meningococcal diseases, invasive':
        'Current week;Meningococcal disease;Unknown serogroup',
    'Current week;Meningococcal diseases, invasive;Serogroup unknown':
        'Current week;Meningococcal disease;Unknown serogroup',
    'Current week;Serogroup unknown;Meningococcal diseases, invasive':
        'Current week;Meningococcal disease;Unknown serogroup',
    'Current week;Unknown serogroup;Meningococcal disease continued':
        'Current week;Meningococcal disease;Unknown serogroup',
    'Current week;Other serogroups;Meningococcal disease continued':
        'Current week;Meningococcal disease;Other serogroups',
    'Unknown serogroup;Current week;Meningococcal disease continued':
        'Current week;Meningococcal disease;Unknown serogroup',
    'Unknown serogroup;Meningococcal disease continued;Current week':
        'Current week;Meningococcal disease;Unknown serogroup',
    'Meningococcal disease continued;Current week;Other serogroups':
        'Current week;Meningococcal disease;Other serogroups',
    'Meningococcal disease continued;Unknown serogroup;Current week':
        'Current week;Meningococcal disease;Unknown serogroup',
    'Meningococcal disease continued;Other serogroups;Current week':
        'Current week;Meningococcal disease;Other serogroups',
    'Current week;Meningococcal disease continued;Unknown serogroup':
        'Current week;Meningococcal disease;Unknown serogroup',
    'Current week;Meningococcal disease continued;Other serogroups':
        'Current week;Meningococcal disease;Other serogroups',
    'Other serogroups;Current week;Meningococcal disease continued':
        'Current week;Meningococcal disease;Other serogroups',
    'Meningococcal disease continued;Current week;Unknown serogroup':
        'Current week;Meningococcal disease;Unknown serogroup',

    ## Streptococcal shock
    'Streptococcal disease, invasive, group A;Current week':
        'Streptococcal toxic shock syndrome;invasive;group A;Current week',
    'Current week;Streptococcal disease, invasive, group A':
        'Streptococcal toxic shock syndrome;invasive;group A;Current week',

    ## Cholera
    'Current week;Cholera':
        'Current week;cholera',

    ## Spotted fever
    'Spotted fever rickettsiosis;Confirmed;Current week':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Rocky Mountain spotted fever;Current week':
        'Current week;spotted fever rickettsiosis including RMSF',
    'Current week;Probable;Spotted Fever Rickettsiosis including RMSF':
        'Current week;spotted fever rickettsiosis including RMSF;Pobable',
    'Confirmed;Current week;Spotted Fever Rickettsiosis':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Confirmed;Current week;Spotted Fever Rickettsiosis including RMSF':
        'Current week;spotted fever rickettsiosis including RMSF;Confirmed',
    'Current week;Spotted Fever Rickettsiosis including RMSF ;Confirmed':
        'Current week;spotted fever rickettsiosis including RMSF;Confirmed',
    'Probable;Spotted Fever Rickettsiosis including RMSF ;Current week':
        'Current week;spotted fever rickettsiosis including RMSF;Pobable',
    'Probable;Spotted fever rickettsiosis;Current week':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Current week;Confirmed;Spotted Fever Rickettsiosis including RMSF':
        'Current week;spotted fever rickettsiosis including RMSF;Confirmed',
    'Probable;Current week;Spotted Fever Rickettsiosis including RMSF':
        'Current week;spotted fever rickettsiosis including RMSF;Pobable',
    'Syphilis, primary & secondary;Current week;Spotted Fever Rickettsiosis':
        'Current week;Spotted fever rickettsiosis',
    'Current week;Confirmed;Spotted Fever Rickettsiosis':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Confirmed;Current week;Spotted fever rickettsiosis':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Probable;Current week;Spotted Fever Rickettsiosis':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Spotted fever rickettsiosis;Probable;Current week':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Current week;Probable;Spotted fever rickettsiosis':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Current week;Rocky Mountain spotted fever':
        'Current week;spotted fever rickettsiosis including RMSF',
    'Spotted Fever Rickettsiosis;Confirmed;Current week':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Spotted Fever Rickettsiosis;Probable;Current week':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Spotted fever rickettsiosis;Confirmed;Current week':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Spotted fever rickettsiosis;Probable;Current week':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Spotted Fever Rickettsiosis including RMSF ;Confirmed;Current week':
        'Current week;spotted fever rickettsiosis including RMSF;Confirmed',
    'Spotted Fever Rickettsiosis including RMSF ;Probable;Current week':
        'Current week;spotted fever rickettsiosis including RMSF;Pobable',
    'Confirmed;Spotted Fever Rickettsiosis including RMSF ;Current week':
        'Current week;spotted fever rickettsiosis including RMSF;Confirmed',
    'Current week;Probable;Spotted Fever Rickettsiosis':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Probable;Current week;Spotted fever rickettsiosis':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Current week;Spotted fever rickettsiosis;Confirmed including RMSF':
        'Current week;spotted fever rickettsiosis including RMSF;Confirmed',
    'Spotted fever rickettsiosis;Confirmed;Current week':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Spotted Fever Rickettsiosis including RMSF ;Current week;Probable':
        'Current week;spotted fever rickettsiosis including RMSF',
    'Spotted fever rickettsiosis;Current week;Confirmed':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Spotted fever rickettsiosis;Confirmed;Current week':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Spotted fever rickettsiosis;Probable;Current week':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Spotted fever rickettsiosis;Current week;Probable':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Current week;Spotted Fever Rickettsiosis including RMSF ;Probable':
        'Current week;spotted fever rickettsiosis including RMSF;Pobable',
    'Confirmed;Spotted Fever Rickettsiosis;Current week':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Spotted Fever Rickettsiosis;Current week;Probable':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Spotted fever rickettsiosis;Probable;Current week':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Spotted fever rickettsiosis;Confirmed;Current week':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Spotted fever rickettsiosis;Confirmed;Current week':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Probable;Spotted Fever Rickettsiosis;Current week':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Spotted fever rickettsiosis;Probable;Current week':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Confirmed;Spotted fever rickettsiosis;Current week':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Spotted Fever Rickettsiosis including RMSF ;Current week;Confirmed':
        'Current week;spotted fever rickettsiosis including RMSF;Confirmed',
    'Spotted Fever Rickettsiosis;Current week;Confirmed':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Spotted fever rickettsiosis;Probable;Current week':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Spotted fever rickettsiosis;Confirmed;Current week':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Current week;Spotted Fever Rickettsiosis;Confirmed':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Spotted fever rickettsiosis;Probable;Current week':
        'Spotted fever rickettsiosis;Probable;Current week',
    'Spotted fever rickettsiosis;Confirmed;Current week':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Current week;Confirmed;Spotted fever rickettsiosis':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Current week;Spotted fever rickettsiosis;Confirmed':
        'Spotted fever rickettsiosis;Confirmed;Current week',
    'Spotted fever rickettsiosis;Confirmed;Current week including RMSF':
        'Current week;spotted fever rickettsiosis including RMSF;Confirmed',
    'Current week;Spotted Fever Rickettsiosis;Probable':
        'Spotted fever rickettsiosis;Probable;Current week',

    ## Invasive Pneumococcal Disease
    'All Ages;Invasive Pneumococcal Disease ;Current week':
        'invasive pneumococcal disease;Current week;Current week',
    'Invasive Pneumococcal Disease Age < 5;Probable;Current week':
        'invasive pneumococcal disease;Current week;Age < 5;Probable;Current week',
    'Invasive Pneumococcal Disease Age < 5;Confirmed;Current week':
        'invasive pneumococcal disease;Current week;Age < 5;Confirmed;Current week',
    'Probable;Invasive pneumococcal disease, all ages;Current week':
        'Probable;invasive pneumococcal disease;all ages;Current week',
    'Invasive Pneumococcal Disease All Ages;Confirmed;Current week':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',
    'Invasive Pneumococcal Disease All Ages;Probable;Current week':
        'invasive pneumococcal disease;Current week;All Ages;Probable;Current week',
    'Current week;Confirmed;Invasive pneumococcal disease, all ages':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',
    'Probable;Current week;Invasive pneumococcal disease, all ages':
        'Probable;Current week;invasive pneumococcal disease;all ages',
    'All Ages;Current week;Invasive Pneumococcal Disease':
        'invasive pneumococcal disease;Current week;Current week',
    'Confirmed;Invasive pneumococcal disease, all ages;Current week':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',
    'Probable;Invasive pneumococcal disease;all ages;Current week':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Confirmed;Current week;Invasive pneumococcal disease, all ages':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',
    'Current week;Probable;Invasive pneumococcal disease, all ages':
        'invasive pneumococcal disease;Current week;Current week',
    'Confirmed;Current week;Invasive Pneumococcal Disease Age < 5':
        'invasive pneumococcal disease;Current week;Age < 5;Confirmed;Current week',
    'Confirmed;Current week;Invasive Pneumococcal Disease All Ages':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',
    'Current week;Probable;Invasive Pneumococcal Disease All Ages':
        'invasive pneumococcal disease;Current week;Current week',
    'Current week;Invasive Pneumococcal Disease Age < 5;Probable':
        'invasive pneumococcal disease;Current week;Age < 5;Probable;Current week',
    'Invasive Pneumococcal Disease ;All Ages;Current week':
        'invasive pneumococcal disease;Current week;Current week',
    'Probable;Current week;Invasive pneumococcal disease;all ages':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Probable;Current week;Invasive Pneumococcal Disease All Ages':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Invasive pneumococcal disease;Current week;Probable':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Probable;Current week;Invasive Pneumococcal Disease Age < 5':
        'invasive pneumococcal disease;Current week;Age < 5;Probable;Current week',
    'Invasive pneumococcal disease;Current week;Probable':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Invasive pneumococcal disease, all ages;Current week;Probable':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Invasive Pneumococcal Disease ;Current week;All Ages':
        'invasive pneumococcal disease;Current week;Current week',
    'Invasive pneumococcal disease, all ages;Probable;Current week':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Invasive pneumococcal disease;Current week;Probable':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Current week;Invasive Pneumococcal Disease ;All Ages':
        'invasive pneumococcal disease;Current week;Current week',
    'Current week;Probable;Invasive Pneumococcal Disease Age < 5':
        'invasive pneumococcal disease;Current week;Age < 5;Probable;Current week',
    'Invasive pneumococcal disease;Current week;Probable':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Invasive pneumococcal disease, all ages;Current week;Confirmed':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',
    'Invasive pneumococcal disease, all ages;Confirmed;Current week':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',
    'Invasive pneumococcal disease;Current week;Probable':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Confirmed;Invasive Pneumococcal Disease All Ages;Current week'
    'Invasive Pneumococcal Disease All Ages;Current week;Probable':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Current week;Invasive pneumococcal disease, all ages;Probable':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Confirmed;Invasive Pneumococcal Disease Age < 5;Current week':
        'invasive pneumococcal disease;Current week;Age < 5;Confirmed;Current week',
    'Invasive Pneumococcal Disease Age < 5;Current week;Probable':
        'invasive pneumococcal disease;Current week;Age < 5;Probable;Current week',
    'Current week;All Ages;Invasive Pneumococcal Disease':
        'invasive pneumococcal disease;Current week;Current week',
    'Invasive pneumococcal disease;Confirmed;Current week':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',
    'Invasive pneumococcal disease;Current week;Probable':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Current week;Invasive pneumococcal disease, all ages;Confirmed':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',
    'Current week;Invasive Pneumococcal Disease All Ages;Confirmed':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',
    'Probable;Invasive Pneumococcal Disease All Ages;Current week':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Probable;Invasive Pneumococcal Disease Age < 5;Current week':
        'invasive pneumococcal disease;Current week;Age < 5;Probable;Current week',
    'Invasive pneumococcal disease;Current week;Probable':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Invasive Pneumococcal Disease All Ages;Current week;Confirmed':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',
    'Invasive pneumococcal disease;All Ages;Probable;Current week':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Current week;Confirmed;Invasive Pneumococcal Disease Age < 5':
        'invasive pneumococcal disease;Current week;Age < 5;Confirmed;Current week',
    'Invasive pneumococcal disease;Current week;Probable':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Invasive Pneumococcal Disease All Ages;Current week;Probable':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Invasive Pneumococcal Disease Age < 5;Current week;Confirmed':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',
    'Current week;Invasive Pneumococcal Disease Age < 5;Confirmed':
        'invasive pneumococcal disease;Current week;Age < 5;Confirmed;Current week',
    'Current week;Invasive Pneumococcal Disease All Ages;Probable':
        'invasive pneumococcal disease;Current week;Current week;Probable',
    'Current week;Confirmed;Invasive Pneumococcal Disease All Ages':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',
    'Confirmed;Invasive Pneumococcal Disease All Ages;Current week':
        'invasive pneumococcal disease;Current week;Confirmed;Current week',

    ## AIDS
    'AIDS *;Current quarter':
        'Acquired Immune Deficiency Syndrome;Current quarter',

    ## Invasive Pneumococcal Disease Drug-resistant
    'Current week;Streptococcus pneumoniae ,invasive disease Drug resistant, all ages':
        'Current week;Invasive pneumococcal disease drug resistant;All ages',
    'Streptococcus pneumoniae ,invasive disease Drug resistant, all ages;Current week':
        'Current week;Invasive pneumococcal disease drug resistant;All ages',

    ## Hansen's Disease
    "Current week;Hansen's disease":
        "Current week;Hansens disease",
    "Hansen's disease;Current week":
        "Current week;Hansens disease",

    ## Dengue
    'Dengue virus infections;dengue;Current week':
        'dengue fever;Current week',
    'Dengue virus infections;Dengue;Current week':
        'dengue fever;Current week',
    'Current week;Dengue virus infection;Dengue':
        'dengue fever;Current week',
    'Current week;Dengue virus infections;Dengue':
        'dengue fever;Current week',
    'Dengue Virus Infection;Dengue Fever ;Current week':
        'dengue fever;Current week',
    'Dengue Virus Infection;Current week;Dengue Fever':
        'dengue fever;Current week',
    'Dengue;Current week;Dengue virus infections':
        'dengue fever;Current week',
    'Dengue virus infection;Dengue;Current week':
        'dengue fever;Current week',
    'Current week;Dengue Virus Infection;Dengue Fever':
        'dengue fever;Current week',
    'Current week;Dengue':
        'dengue fever;Current week',
    'Dengue Fever ;Current week;Dengue Virus Infection':
        'dengue fever;Current week',
    'Dengue Fever;Current week;Dengue Virus Infection':
        'dengue fever;Current week',
    'Current week;Dengue':
        'dengue;Current week',
    'Dengue;Dengue virus infections;Current week':
        'dengue fever;Current week',
    'Dengue Virus Infection;Dengue Fever;Current week':
        'dengue fever;Current week',
    'Dengue virus infections;Current week;Dengue':
        'dengue fever;Current week',
    'Dengue Fever ;Dengue Virus Infection;Current week':
        'dengue fever;Current week',
    'Dengue;Current week;Dengue virus infection':
        'dengue fever;Current week',
    'Current week;Dengue':
        'dengue fever;Current week',
    'Dengue virus infection;Current week;dengue':
        'dengue fever;Current week',
    'Current week;dengue;Dengue virus infections':
        'dengue fever;Current week',
    'Dengue Fever;Dengue Virus Infection;Current week':
        'dengue fever;Current week',
    'Dengue virus infections;Current week;dengue':
        'dengue fever;Current week',
    'Dengue Fever ;Current week;dengue Virus Infection':
        'dengue fever;Current week',
    'Current week;dengue;Dengue virus infection':
        'dengue fever;Current week',
    'dengue;Current week':
        'dengue fever;Current week',
    'dengue;Current week;Dengue virus infection':
        'dengue fever;Current week',
    'dengue;Current week Fever;Dengue Virus Infection':
        'dengue fever;Current week',
    'Dengue Fever ;dengue;Current week Virus Infection':
        'dengue fever;Current week',
    'dengue;Current week Fever ;Dengue Virus Infection':
        'dengue fever;Current week',

    ## Severe dengue
    'Dengue Virus Infection;Current week;Severe Dengue':
        'Current week;Severe dengue',
    'Current week;Severe Dengue;Dengue Virus Infection':
        'Current week;Severe dengue',
    'Severe Dengue;Current week;Dengue Virus Infection':
        'Current week;Severe dengue',
    'Dengue Virus Infection;Severe Dengue;Current week':
        'Current week;Severe dengue',
    'Severe Dengue;Current week;dengue Virus Infection':
        'Current week;Severe dengue',
    'dengue;Current week Virus Infection;Severe Dengue':
        'Current week;Severe dengue',
    'Severe Dengue;Dengue Virus Infection;Current week':
        'Current week;Severe dengue',
    'Dengue virus infections;Severe dengue fever;Current week':
        'Current week;Severe dengue',

    ## Dengue-like illness
    'Dengue virus infections;Current week;dengue-like illness':
        'Current week;Dengue-like illness',
    'Current week;dengue-like illness;Dengue virus infections':
        'Current week;Dengue-like illness',
    'Current week;dengue-like illness':
        'Current week;Dengue-like illness',
    'dengue;Current week-like illness':
        'Current week;Dengue-like illness',

    ## Hepatitis A
    'Current week;Hepatitis viral, acute, by type;A':
        'Current week;Hepatitis A;Acute',
    'Current week;A;Hepatitis viral, acute, by type':
        'Current week;Hepatitis A;Acute',
    'A;Current week;Hepatitis viral, acute, by type':
        'Current week;Hepatitis A;Acute',
    'A;Hepatitis viral, acute, by type ;Current week':
        'Current week;Hepatitis A;Acute',
    'A;Hepatitis viral, acute, by type;Current week':
        'Current week;Hepatitis A;Acute',
    'Hepatitis viral, acute, by type ;A;Current week':
        'Current week;Hepatitis A;Acute',
    'Hepatitis viral, acute, by type;A;Current week':
        'Current week;Hepatitis A;Acute',
    'Hepatitis viral, acute, by type;Current week;A':
        'Current week;Hepatitis A;Acute',
    'Hepatitis viral, acute, by type ;Current week;A':
        'Current week;Hepatitis A;Acute',
    'Current week;Hepatitis viral, acute, by type ;A':
        'Current week;Hepatitis A;Acute',

    ## Hepatitis B
    'Current week;Hepatitis viral, acute, by type ;B':
        'Current week;Hepatitis B;Acute',
    'Current week;Hepatitis viral, acute, by type;B':
        'Current week;Hepatitis B;Acute',
    'Current week;B;Hepatitis viral, acute, by type':
        'Current week;Hepatitis B;Acute',
    'Hepatitis viral, acute, by type ;Current week;B':
        'Current week;Hepatitis B;Acute',
    'Hepatitis viral, acute, by type;Current week;B':
        'Current week;Hepatitis B;Acute',
    'B;Current week;Hepatitis viral, acute, by type':
        'Current week;Hepatitis B;Acute',
    'Hepatitis viral, acute, by type;B;Current week':
        'Current week;Hepatitis B;Acute',
    'B;Hepatitis viral, acute, by type ;Current week':
        'Current week;Hepatitis B;Acute',
    'Hepatitis viral, acute, by type ;B;Current week':
        'Current week;Hepatitis B;Acute',
    'B;Hepatitis viral, acute, by type;Current week':
        'Current week;Hepatitis B;Acute',

    ## Hepatitis C
    'Current week;Hepatitis viral, acute, by type;C':
        'Current week;Hepatitis C;Acute',
    'C confirmed;Hepatitis viral, acute, by type;Current week':
        'Current week;Hepatitis C;Acute;Confirmed',
    'Current week;Hepatitis viral, acute, by type;C probable':
        'Current week;Hepatitis C;Acute;Probable',
    'Current week;Confirmed;Hepatitis C viral, acute':
        'Current week;Hepatitis C;Acute;Confirmed',
    'Probable;Hepatitis C viral, acute;Current week':
        'Current week;Hepatitis C;Acute;Probable',
    'Current week;C Confirmed;Hepatitis viral, acute, by type Continued':
        'Current week;Hepatitis C;Acute;Confirmed',
    'Current week;C Probable;Hepatitis viral, acute, by type Continued':
        'Current week;Hepatitis C;Acute;Probable',
    'Current week;C;Hepatitis viral, acute, by type':
        'Current week;Hepatitis C;Acute',
    'Current week;C probable;Hepatitis viral, acute, by type':
        'Current week;Hepatitis C;Acute;Probable',
    'C Confirmed;Current week;Hepatitis viral, acute, by type Continued':
        'Current week;Hepatitis C;Acute;Confirmed',
    'Hepatitis viral, acute, by type;C;Current week':
        'Current week;Hepatitis C;Acute',
    'Hepatitis viral, acute, by type;C confirmed;Current week':
        'Current week;Hepatitis C;Acute;Confirmed',
    'Hepatitis viral, acute, by type Continued;Current week;C Confirmed':
        'Current week;Hepatitis C;Acute;Confirmed',
    'Hepatitis viral, acute, by type;Current week;C probable':
        'Current week;Hepatitis C;Acute;Probable',
    'Hepatitis viral, acute, by type Continued;Current week;C Probable':
        'Current week;Hepatitis C;Acute;Probable',
    'C;Hepatitis viral, acute, by type;Current week':
        'Current week;Hepatitis C;Acute',
    'Hepatitis viral, acute, by type;Current week;C confirmed':
        'Current week;Hepatitis C;Acute;Confirmed',
    'Hepatitis viral, acute, by type;C probable;Current week':
        'Current week;Hepatitis C;Acute;Probable',
    'C Probable;Current week;Hepatitis viral, acute, by type Continued':
        'Current week;Hepatitis C;Acute;Probable',
    'C;Current week;Hepatitis viral, acute, by type':
        'Current week;Hepatitis C;Acute',
    'Hepatitis viral, acute, by type;Current week;C':
        'Current week;Hepatitis C;Acute',
    'C probable;Current week;Hepatitis viral, acute, by type':
        'Current week;Hepatitis C;Acute;Probable',
    'C Confirmed;Hepatitis viral, acute, by type Continued;Current week':
        'Current week;Hepatitis C;Acute;Confirmed',
    'C probable;Hepatitis viral, acute, by type;Current week':
        'Current week;Hepatitis C;Acute;Probable',
    'Hepatitis viral, acute, by type Continued;C Confirmed;Current week':
        'Current week;Hepatitis C;Acute;Confirmed',
    'Hepatitis viral, acute, by type Continued;C Probable;Current week':
        'Current week;Hepatitis C;Acute;Probable',
    'C Probable;Hepatitis viral, acute, by type Continued;Current week':
        'Current week;Hepatitis C;Acute;Probable',
    'Current week;C confirmed;Hepatitis viral, acute, by type':
        'Current week;Hepatitis C;Acute;Confirmed',
    'Current week;Hepatitis viral, acute, by type Continued;C Confirmed':
        'Current week;Hepatitis C;Acute;Confirmed',
    'Current week;Hepatitis viral, acute, by type Continued;C Probable':
        'Current week;Hepatitis C;Acute;Probable',
    'C confirmed;Current week;Hepatitis viral, acute, by type':
        'Current week;Hepatitis C;Acute;Confirmed'
}


def format_column_header(column_list):
    for index, col_name in enumerate(column_list):
        # remove non printable special characters from column name
        col_name = ''.join(filter(lambda x: x in string.printable, col_name))
        # remove the double spaces amd tab spaces to single space
        col_name = col_name.replace(' ;', ';')
        col_name = col_name.replace('  ', ' ')
        col_name = col_name.replace('  ;', ';')
        col_name = col_name.replace('\t', ' ')
        col_name = col_name.replace('\t. ', '. ')
        col_name = col_name.replace('cont"d', 'contd.')
        col_name = col_name.replace('(', '')
        col_name = col_name.replace(')', '')
        # Some disease in column names need to be fixed to match the disease map
        for k, v in _DISEASE_NAME_REMAP.items():
            col_name = col_name.replace(k, v)
        # update the column name
        column_list[index] = col_name.strip()
    # for some datasets the first column is poorly formatted
    column_list[0] = 'Reporting Area'
    return column_list


def concat_rows_with_column_headers(rows_with_col_names, df_column_list):
    # some tows have NaN as the first element, we replace it with ''
    rows_with_col_names = rows_with_col_names.fillna('')
    # works with table structure where column=0 is always the 'Reporting Area' and the the other columns are the case counts with different aggregations
    rows_with_col_names = rows_with_col_names.groupby(df_column_list[0])[
        df_column_list[1:]].agg(lambda d: ";".join(set(d))).reset_index()

    ## some csvs do not have data and need will throw an exception when column names are flattened.
    try:
        ## flatten column names to list
        column_list = rows_with_col_names.loc[0, :].values.flatten().tolist()
        ## remove non-printable
        return column_list
    except:
        # Dataframe does not have any data points and is pobably a note.
        return []


def process_nndss_weekly(input_filepath: str):
    ## from the csv files get the year, and week count
    filename = input_filepath.split('/')[-1]
    year = int(filename[10:14])
    week = int(filename[25:27])

    ## get the ending date for the week -- date is subject to the week definition in https://ndc.services.cdc.gov/wp-content/uploads/MMWR_Week_overview.pdf
    observation_date = get_mmwr_week_end_date(year, week)

    df = pd.read_csv(input_filepath, header=None)

    ## fix the column names of the file - the head of the dataframe has all the rows that have the column name
    rows_with_col_names = df[(df[0] == 'Reporting Area') |
                             (df[0] == 'Reporting  Area') |
                             (df[0] == 'Reporting area') |
                             (df[0] == 'Reporting  area')]
    column_list = concat_rows_with_column_headers(rows_with_col_names,
                                                  df.columns.tolist())

    # remove rows starting with 'Notes' or 'Total' or 'Notice'
    df = df[(df[0] != 'Notice') | (df[0] != 'Notes') | (df[0] != 'Total') |
            (df[0] != '"Notice"') | (df[0] != '"Notes"') |
            (df[0] != '"Total"') | (df[0] != '"Erratum"')]

    # remove rows that had column names
    df = df[~df.isin(rows_with_col_names)].dropna()

    # if dataframe
    if len(column_list) > 2:
        # some csvs have a header row which has values starting from 0 to num_columns - 1 as the first row. We see if there such rows and drop them
        df = df.drop([0], errors='ignore')
        del rows_with_col_names

        # format column names
        column_list = format_column_header(column_list)
        # update columns of the dataframe
        df.columns = column_list

        # select columns of interest i.e. current week statistics
        current_week_stat_cols = [
            col for col in column_list if 'current' in col.lower()
        ]
        selected_cols = [column_list[0]] + current_week_stat_cols

        # filter the dataframe to current week stat columns
        df = df[selected_cols]

        # un-pivot the dataframe to place, column, value
        df = df.melt(id_vars=['Reporting Area'],
                     value_vars=current_week_stat_cols,
                     var_name='column_name',
                     value_name='value')

        # add the observation date to the dataframe
        df['observationDate'] = observation_date

        # add the observation period based on the column names
        df['observationPeriod'] = df['column_name'].apply(set_observationPeriod)

        # convert the place names to geoIds
        df['observationAbout'] = df['Reporting Area'].apply(
            resolve_reporting_places_to_dcids)

        # fix the value column based on the data notes mentioned in NNDSS
        df['value'] = df['value'].replace(to_replace=_FORMAT_UNREPORTED_CASES,
                                          regex=True)

        # add the week as a column to the dataframe for easy validation
        df['week'] = week

        return df


def generate_statvar_map_for_columns(column_list, place_list):

    sv_map = {}
    dcid_df = pd.DataFrame(
        columns=['Reporting Area', 'column_name', 'variableMeasured'])
    for column in column_list:
        # initialize the statvar dict for the current column
        svdict = {}
        svdict['populationType'] = 'dcs:MedicalConditionIncident'
        svdict['typeOf'] = 'dcs:StatisticalVariable'
        svdict['statType'] = 'dcs:measuredValue'
        svdict['measuredProperty'] = 'dcs:count'

        # column names have multiple pvs which are joined with ';'
        column_components = column.split(';')

        # remove duplicates substring from column name
        column_components = list(set(column_components))

        # flatten comma-separated components
        column_components = [
            i.strip() for i in column_components for i in i.split(',')
        ]

        for component in column_components:
            component = component.strip()
            if not (component.lower() in _PV_MAP.keys()):
                # map to disease
                mapped_disease = _DISEASE_DCID_DF[
                    _DISEASE_DCID_DF['name'].str.contains(component)][[
                        'name', 'dcid'
                    ]]

                # when we have the best match i.e, only one row
                if mapped_disease.shape[0] == 1:
                    svdict['incidentType'] = 'dcs:' + str(
                        mapped_disease['dcid'].values[0])
                    disease = str(mapped_disease['name'].values[0])
                    disease = ''.join([e.title() for e in disease.split()])
                    disease = disease.replace(',', '')
                    svdict['disease'] = 'dcs:' + disease

            else:
                # check if the component is a key in _PV_MAP
                # add additional pvs from the column_name
                for key in _PV_MAP:
                    if key in component.lower():
                        #TODO: Handle the case when two values for same prop occurs
                        svdict.update(_PV_MAP[key])

        # add pvs that are dependent on the place
        patterns_for_resident_pvs = ['Non-US', 'U.S. Residents', 'US Residents']

        places_with_resident_pvs = [
            place for place in place_list if any(
                substring in place for substring in patterns_for_resident_pvs)
        ]

        # TODO: Move the repeated code to a function
        # generate dcid
        dcid = get_statvar_dcid(svdict, ignore_props=['incidentType'])

        # add to column_map
        key = 'Node: dcid:' + dcid
        if key not in sv_map.keys():
            sv_map[key] = svdict

        for place in place_list:
            if place not in places_with_resident_pvs:
                dcid_df = dcid_df.append(
                    {
                        'Reporting Area': place,
                        'column_name': column,
                        'variableMeasured': dcid
                    },
                    ignore_index=True)

        ## if there are places with additional pvs, update the map and dataframe
        for place in places_with_resident_pvs:

            if 'Non-' not in place.strip():
                svdict_tmp = svdict.copy()
                svdict_tmp['residentStatus'] = 'dcs:USResident'
                # generate dcid
                dcid = get_statvar_dcid(svdict_tmp,
                                        ignore_props=['incidentType'])

                # add to column_map
                key = 'Node: dcid:' + dcid
                if key not in sv_map.keys():
                    sv_map[key] = svdict_tmp
                dcid_df = dcid_df.append(
                    {
                        'Reporting Area': place,
                        'column_name': column,
                        'variableMeasured': dcid
                    },
                    ignore_index=True)

            elif 'Non-' in place.strip():
                svdict_tmp = svdict.copy()
                svdict_tmp['residentStatus'] = 'dcs:NonUSResident'
                # generate dcid
                dcid = get_statvar_dcid(svdict_tmp,
                                        ignore_props=['incidentType'])

                # add to column_map
                key = 'Node: dcid:' + dcid
                if key not in sv_map.keys():
                    sv_map[key] = svdict_tmp
                dcid_df = dcid_df.append(
                    {
                        'Reporting Area': place,
                        'column_name': column,
                        'variableMeasured': dcid
                    },
                    ignore_index=True)

            else:
                # generate dcid
                dcid = get_statvar_dcid(svdict, ignore_props=['incidentType'])

                # add to column_map
                key = 'Node: dcid:' + dcid
                if key not in sv_map.keys():
                    sv_map[key] = svdict
                dcid_df = dcid_df.append(
                    {
                        'Reporting Area': place,
                        'column_name': column,
                        'variableMeasured': dcid
                    },
                    ignore_index=True)

    return sv_map, dcid_df


def main(_) -> None:
    #TODO: add path to places_to_dcid and diseases_to_pvs csv files as args to the script
    flags.DEFINE_string(
        'input_path', './data/nndss_weekly_data_updated',
        'Path to the directory with weekly data scrapped from NNDSS')
    flags.DEFINE_string(
        'output_path', './data/output',
        'Path to the directory where generated files are to be stored.')

    input_path = FLAGS.input_path
    output_path = FLAGS.output_path
    processed_dataframe_list = []

    #TODO: Parallelize this step
    # for all files in the data directory process the files and append to a common dataframe
    for filename in os.listdir(input_path):
        table_id = filename.split('table_')[1].split('.')[0]
        lowercase_in_tablename = re.findall(r'[a-z]', table_id)
        if filename.endswith('.csv') and len(lowercase_in_tablename) < 2:
            file_inputpath = os.path.join(input_path, filename)
            df = process_nndss_weekly(file_inputpath)
            processed_dataframe_list.append(df)

    # concat list of all processed data frames
    cleaned_dataframe = pd.concat(processed_dataframe_list, ignore_index=False)
    del processed_dataframe_list

    # for each unique column generate the statvar with constraints
    unique_columns = cleaned_dataframe['column_name'].unique().tolist()
    unique_places = cleaned_dataframe['Reporting Area'].unique().tolist()

    # column - statvar dictionary map
    sv_map, dcid_df = generate_statvar_map_for_columns(unique_columns,
                                                       unique_places)

    # map the statvars to column names
    cleaned_dataframe = pd.merge(cleaned_dataframe,
                                 dcid_df,
                                 on=['Reporting Area', 'column_name'],
                                 how='left')

    # set measurement method
    cleaned_dataframe[
        'measurementMethod'] = 'dcs:CDC_NNDSS_Diseases_WeeklyTables'

    #TODO: 2. If reporting area is US Territories, drop observation and make a sum of case counts across US States with mMethod = dc/Aggregate

    ## Create output directory if not present
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    # write outputs to file
    f = open(os.path.join(output_path, 'cdc_wonder_weekly.tmcf'), 'w')
    f.write(_TEMPLATE_MCF)
    f.close()

    # write statvar mcf file from col_map
    f = open(os.path.join(output_path, 'cdc_wonder_weekly.mcf'), 'w')

    for dcid, pvdict in sv_map.items():
        f.write(dcid + '\n')
        for p, v in pvdict.items():
            if p != 'disease':
                f.write(p + ":" + v + "\n")
        f.write("\n")
    f.close()

    # remove disease prop before writing

    # write csv
    cleaned_dataframe['observationAbout'].replace('', np.nan, inplace=True)
    cleaned_dataframe['value'].replace('', np.nan, inplace=True)
    cleaned_dataframe.dropna(subset=['value', 'observationAbout'], inplace=True)
    cleaned_dataframe.to_csv(os.path.join(output_path, 'cdc_wonder_weekly.csv'),
                             index=False)


if __name__ == '__main__':
    app.run(main)
