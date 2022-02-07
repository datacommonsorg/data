# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A script to process FBI Hate Crime data."""

import os
import sys
import json
import pandas as pd
import numpy as np
import copy
from utils import flatten_by_column, make_time_place_aggregation

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))

from statvar_dcid_generator import get_statvar_dcid, _PREPEND_APPEND_REPLACE_MAP

_CACHE_DIR = os.path.join(_SCRIPT_PATH, 'cache')

# Columns to input from source data
_INPUT_COLUMNS = [
    'INCIDENT_ID', 'DATA_YEAR', 'OFFENDER_RACE', 'OFFENDER_ETHNICITY',
    'STATE_ABBR', 'OFFENSE_NAME', 'BIAS_DESC', 'AGENCY_TYPE_NAME',
    'MULTIPLE_OFFENSE', 'MULTIPLE_BIAS', 'PUB_AGENCY_NAME',
    'TOTAL_OFFENDER_COUNT', 'ADULT_OFFENDER_COUNT', 'JUVENILE_OFFENDER_COUNT',
    'INCIDENT_DATE', 'VICTIM_TYPES', 'LOCATION_NAME', 'VICTIM_COUNT',
    'ADULT_VICTIM_COUNT', 'JUVENILE_VICTIM_COUNT'
]

# A dict to map bias descriptions to their bias category
_BIAS_CATEGORY_MAP = {
    'Anti-Black or African American':
        'race',
    'Anti-White':
        'race',
    'Anti-Native Hawaiian or Other Pacific Islander':
        'race',
    'Anti-Arab':
        'race',
    'Anti-Asian':
        'race',
    'Anti-American Indian or Alaska Native':
        'race',
    'Anti-Other Race/Ethnicity/Ancestry':
        'race',
    'Anti-Multiple Races, Group':
        'race',
    'Anti-Protestant':
        'religion',
    'Anti-Other Religion':
        'religion',
    'Anti-Jewish':
        'religion',
    'Anti-Islamic (Muslim)':
        'religion',
    'Anti-Jehovah\'s Witness':
        'religion',
    'Anti-Mormon':
        'religion',
    'Anti-Buddhist':
        'religion',
    'Anti-Sikh':
        'religion',
    'Anti-Other Christian':
        'religion',
    'Anti-Hindu':
        'religion',
    'Anti-Catholic':
        'religion',
    'Anti-Eastern Orthodox (Russian, Greek, Other)':
        'religion',
    'Anti-Atheism/Agnosticism':
        'religion',
    'Anti-Multiple Religions, Group':
        'religion',
    'Anti-Heterosexual':
        'sexualOrientation',
    'Anti-Lesbian (Female)':
        'sexualOrientation',
    'Anti-Lesbian, Gay, Bisexual, or Transgender (Mixed Group)':
        'sexualOrientation',
    'Anti-Bisexual':
        'sexualOrientation',
    'Anti-Gay (Male)':
        'sexualOrientation',
    'Anti-Hispanic or Latino':
        'ethnicity',
    'Anti-Physical Disability':
        'disabilityStatus',
    'Anti-Mental Disability':
        'disabilityStatus',
    'Anti-Male':
        'gender',
    'Anti-Female':
        'gender',
    'Anti-Transgender':
        'TransgenderOrGenderNonConforming',
    'Anti-Gender Non-Conforming':
        'TransgenderOrGenderNonConforming',
    'Unknown (offender\'s motivation not known)':
        'UnknownBias'
}

# A dict to map offenses to categories of crime
_OFFENSE_CATEGORY_MAP = {
    "Intimidation": "CrimeAgainstPerson",
    "Simple Assault": "CrimeAgainstPerson",
    "Aggravated Assault": "CrimeAgainstPerson",
    "Robbery": "CrimeAgainstProperty",
    "Destruction/Damage/Vandalism of Property": "CrimeAgainstProperty",
    "Arson": "CrimeAgainstProperty",
    "Murder and Nonnegligent Manslaughter": "CrimeAgainstPerson",
    "Burglary/Breaking & Entering": "CrimeAgainstProperty",
    "Rape": "CrimeAgainstPerson",
    "Motor Vehicle Theft": "CrimeAgainstProperty",
    "Drug/Narcotic Violations": "CrimeAgainstSociety",
    "Weapon Law Violations": "CrimeAgainstSociety",
    "Theft From Motor Vehicle": "CrimeAgainstProperty",
    "Shoplifting": "CrimeAgainstProperty",
    "All Other Larceny": "CrimeAgainstProperty",
    "Theft of Motor Vehicle Parts or Accessories": "CrimeAgainstProperty",
    "Fondling": "CrimeAgainstPerson",
    "Counterfeiting/Forgery": "CrimeAgainstProperty",
    "Kidnapping/Abduction": "CrimeAgainstPerson",
    "Theft From Building": "CrimeAgainstProperty",
    "Pornography/Obscene Material": "CrimeAgainstSociety",
    "Embezzlement": "CrimeAgainstProperty",
    "Purse-snatching": "CrimeAgainstProperty",
    "Drug Equipment Violations": "CrimeAgainstSociety",
    "Credit Card/Automated Teller Machine Fraud": "CrimeAgainstProperty",
    "Sexual Assault With An Object": "CrimeAgainstPerson",
    "False Pretenses/Swindle/Confidence Game": "CrimeAgainstProperty",
    "Pocket-picking": "CrimeAgainstProperty",
    "Welfare Fraud": "CrimeAgainstProperty",
    "Extortion/Blackmail": "CrimeAgainstProperty",
    "Stolen Property Offenses": "CrimeAgainstProperty",
    "Incest": "CrimeAgainstPerson",
    "Sodomy": "CrimeAgainstPerson",
    "Negligent Manslaughter": "CrimeAgainstPerson",
    "Statutory Rape": "CrimeAgainstPerson",
    "Theft From Coin-Operated Machine or Device": "CrimeAgainstProperty",
    "Impersonation": "CrimeAgainstProperty",
    "Prostitution": "CrimeAgainstSociety",
    "Wire Fraud": "CrimeAgainstProperty",
    "Assisting or Promoting Prostitution": "CrimeAgainstSociety",
    "Purchasing Prostitution": "CrimeAgainstSociety",
    "Bribery": "CrimeAgainstProperty",
    "Identity Theft": "CrimeAgainstProperty",
    "Human Trafficking, Commercial Sex Acts": "CrimeAgainstPerson",
    "Hacking/Computer Invasion": "CrimeAgainstProperty",
    "Betting/Wagering": "CrimeAgainstSociety",
    "Animal Cruelty": "CrimeAgainstSociety",
    "Not Specified": "Not Specified"
}

# A dict to generate aggregations on the source data
_AGGREGATIONS = {
    'incidents.csv': [{  # Total Criminal Incidents
        'df': 'incident_df',
        'args': {
            'groupby_cols': [],
            'agg_dict': {
                'INCIDENT_ID': 'nunique'
            },
            'population_type': 'CriminalIncidents'
        }
    }],
    'incidents_bias.csv': [
        {  # Incidents grouped by bias motivation (anti-white, ...)
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['BIAS_DESC'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents grouped into single bias / multiple bias
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents grouped by bias category (race,religion, gender, ...)
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        }
    ],
    'incidents_offense.csv': [
        {  # Incidents by crime type (arson, robbery, ...)
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_NAME'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by crime category
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        }
    ],
    'incidents_offense_bias.csv': [
        {  # Incidents by crime type and bias motivation
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_DESC', 'OFFENSE_NAME'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents grouped by crime type and single bias / multiple bias
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS', 'OFFENSE_NAME'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents grouped by crime type and bias category
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY', 'OFFENSE_NAME'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by crime type and bias motivation
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_DESC', 'OFFENSE_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents grouped by crime type and single bias / multiple bias
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS', 'OFFENSE_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents grouped by crime type and bias category
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY', 'OFFENSE_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        }
    ],
    'incidents_offenderrace.csv': [{  # Total incidents by offender race
        'df': 'incident_df',
        'args': {
            'groupby_cols': ['OFFENDER_RACE'],
            'agg_dict': {
                'INCIDENT_ID': 'count'
            },
            'population_type': 'CriminalIncidents'
        }
    }],
    'incidents_offenderethnicity.csv':
        [{  # Total incidents by offender ethnicity
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['OFFENDER_ETHNICITY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        }],
    'incidents_offenderrace_bias.csv': [
        {  # Incidents by offender race and bias motivation
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['OFFENDER_RACE', 'BIAS_DESC'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by offender race and single bias / multiple bias
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['OFFENDER_RACE', 'MULTIPLE_BIAS'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by offender race and bias category
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['OFFENDER_RACE', 'BIAS_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        }
    ],
    'incidents_offenderethnicity_bias.csv': [
        {  # Incidents by offender ethnicity and bias motivation
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['OFFENDER_ETHNICITY', 'BIAS_DESC'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by offender ethnicity and single bias / multiple bias
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['OFFENDER_ETHNICITY', 'MULTIPLE_BIAS'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by offender ethnicity and bias category
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['OFFENDER_ETHNICITY', 'BIAS_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        }
    ],
    'offenses.csv': [{  # Total Criminal Offenses
        'df': 'offense_df',
        'args': {
            'groupby_cols': [],
            'agg_dict': {
                'INCIDENT_ID': 'count'
            },
            'population_type': 'CriminalIncidents',
            'measurement_qualifier': 'Offense'
        }
    }],
    'victims.csv': [{  # Total Victims
        'df': 'incident_df',
        'args': {
            'groupby_cols': [],
            'agg_dict': {
                'VICTIM_COUNT': 'sum'
            },
            'population_type': 'CriminalIncidents',
            'measurement_qualifier': 'Victim'
        }
    }],
    'offenders.csv': [
        {  # Total Offenders
            'df': 'incident_df',
            'args': {
                'groupby_cols': [],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender'
            }
        },
        {  # Total known and unknown Offenders
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['OFFENDER_CATEGORY'],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender'
            }
        }
    ],
    'incidents_victimtype_bias.csv': [
        {  # Incidents by victim type
            'df': 'victim_df',
            'args': {
                'groupby_cols': ['VICTIM_TYPES'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by victim type and bias motivation
            'df': 'single_bias_victim',
            'args': {
                'groupby_cols': ['VICTIM_TYPES', 'BIAS_DESC'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by victim type and single bias / multiple bias
            'df': 'victim_df',
            'args': {
                'groupby_cols': ['VICTIM_TYPES', 'MULTIPLE_BIAS'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by victim type and bias category
            'df': 'single_bias_victim',
            'args': {
                'groupby_cols': ['VICTIM_TYPES', 'BIAS_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        }
    ],
    'incidents_location_bias.csv': [
        {  # Incidents by location of crime
            'df': 'location_df',
            'args': {
                'groupby_cols': ['LOCATION_NAME'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by location of crime and single bias / multiple bias
            'df': 'location_df',
            'args': {
                'groupby_cols': ['LOCATION_NAME', 'MULTIPLE_BIAS'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by location of crime and bias category
            'df': 'single_bias_location',
            'args': {
                'groupby_cols': ['LOCATION_NAME', 'BIAS_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        }
    ],
    'incidents_multiple_location_bias.csv': [
        {  # Incidents by location of crime
            'df': 'location_df',
            'args': {
                'groupby_cols': ['MULTIPLE_LOCATION_NAME'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by location of crime and single bias / multiple bias
            'df': 'location_df',
            'args': {
                'groupby_cols': ['MULTIPLE_LOCATION_NAME', 'MULTIPLE_BIAS'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by location of crime and bias category
            'df': 'single_bias_location',
            'args': {
                'groupby_cols': ['MULTIPLE_LOCATION_NAME', 'BIAS_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        }
    ],
    'offense_bias.csv': [
        {  # Offenses grouped by bias motivation
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_DESC'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses grouped by single bias / multiple bias
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses grouped by bias category
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
    ],
    'offense_offensetype.csv': [
        {  # Offenses grouped by offense type
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_NAME'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses grouped by offense category
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        }
    ],
    'offense_victimtype.csv': [{  # Offenses grouped by offense type
        'df': 'offense_victim_df',
        'args': {
            'groupby_cols': ['VICTIM_TYPES'],
            'agg_dict': {
                'INCIDENT_ID': 'count'
            },
            'population_type': 'CriminalIncidents',
            'measurement_qualifier': 'Offense'
        }
    }],
    'offense_offensetype_victimtype.csv': [
        {  # Offenses grouped by offense type
            'df': 'offense_single_victimtype_df',
            'args': {
                'groupby_cols': ['OFFENSE_NAME', 'VICTIM_TYPES'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses grouped by offense category
            'df': 'offense_single_victimtype_df',
            'args': {
                'groupby_cols': ['OFFENSE_CATEGORY', 'VICTIM_TYPES'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        }
    ],
    'offense_offensetype_victimtype_multiple.csv': [
        {  # Offenses grouped by offense type
            'df': 'offense_multiple_victimtype_df',
            'args': {
                'groupby_cols': ['OFFENSE_NAME', 'MULTIPLE_VICTIM_TYPE'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses grouped by offense category
            'df': 'offense_multiple_victimtype_df',
            'args': {
                'groupby_cols': ['OFFENSE_CATEGORY', 'MULTIPLE_VICTIM_TYPE'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        }
    ],
    'offense_offensetype_offenderrace.csv': [
        {  # Offenses grouped by offense type
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_NAME', 'OFFENDER_RACE'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses grouped by offense category
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_CATEGORY', 'OFFENDER_RACE'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        }
    ],
    'offense_offensetype_offenderethnicity.csv': [
        {  # Offenses grouped by offense type
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_NAME', 'OFFENDER_ETHNICITY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses grouped by offense category
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_CATEGORY', 'OFFENDER_ETHNICITY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        }
    ],
    'offense_offensetype_offendercategory.csv': [
        {  # Offenses grouped by offense type
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_NAME', 'OFFENDER_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses grouped by offense category
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_CATEGORY', 'OFFENDER_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        }
    ],
    'offenses_offense_bias.csv': [
        {  # Offenses by crime type and bias motivation
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_DESC', 'OFFENSE_NAME'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses grouped by crime type and single bias / multiple bias
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS', 'OFFENSE_NAME'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses grouped by crime type and bias category
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY', 'OFFENSE_NAME'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses by crime type and bias motivation
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_DESC', 'OFFENSE_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses grouped by crime type and single bias / multiple bias
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS', 'OFFENSE_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses grouped by crime type and bias category
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY', 'OFFENSE_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        }
    ],
    'offenses_offenderrace_bias.csv': [
        {  # Offenses by offender race and bias motivation
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['OFFENDER_RACE', 'BIAS_DESC'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses by offender race and single bias / multiple bias
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENDER_RACE', 'MULTIPLE_BIAS'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses by offender race and bias category
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['OFFENDER_RACE', 'BIAS_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses by offender race and bias category
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['OFFENDER_RACE'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        }
    ],
    'offenses_offenderethnicity_bias.csv': [
        {  # Offenses by offender ethnicity and bias motivation
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['OFFENDER_ETHNICITY', 'BIAS_DESC'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses by offender ethnicity and single bias / multiple bias
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENDER_ETHNICITY', 'MULTIPLE_BIAS'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses by offender ethnicity and bias category
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['OFFENDER_ETHNICITY', 'BIAS_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses by offender ethnicity
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['OFFENDER_ETHNICITY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        }
    ],
    'offenses_offendertype_bias.csv': [
        {  # Offenses by offender race and bias motivation
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['OFFENDER_CATEGORY', 'BIAS_DESC'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses by offender race and single bias / multiple bias
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENDER_CATEGORY', 'MULTIPLE_BIAS'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        },
        {  # Offenses by offender race and bias category
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['OFFENDER_CATEGORY', 'BIAS_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offense'
            }
        }
    ],
    'victims_bias.csv': [
        {  # Victims grouped by bias motivation (anti-white, ...)
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['BIAS_DESC'],
                'agg_dict': {
                    'VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim'
            }
        },
        {  # Victims grouped into single bias / multiple bias
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS'],
                'agg_dict': {
                    'VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim'
            }
        },
        {  # Victims grouped by bias category (race,religion, gender, ...)
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY'],
                'agg_dict': {
                    'VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim'
            }
        }
    ],
    'victims_adult_bias.csv': [
        {  # Victims grouped by bias motivation (anti-white, ...)
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['BIAS_DESC'],
                'agg_dict': {
                    'ADULT_VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim',
                'common_pvs': {
                    'victimAge': '[18 - Years]'
                }
            }
        },
        {  # Victims grouped into single bias / multiple bias
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS'],
                'agg_dict': {
                    'ADULT_VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim',
                'common_pvs': {
                    'victimAge': '[18 - Years]'
                }
            }
        },
        {  # Victims grouped by bias category (race,religion, gender, ...)
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY'],
                'agg_dict': {
                    'ADULT_VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim',
                'common_pvs': {
                    'victimAge': '[18 - Years]'
                }
            }
        }
    ],
    'victims_juvenile_bias.csv': [
        {  # Victims grouped by bias motivation (anti-white, ...)
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['BIAS_DESC'],
                'agg_dict': {
                    'JUVENILE_VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim',
                'common_pvs': {
                    'victimAge': '[- 17 Years]'
                }
            }
        },
        {  # Victims grouped into single bias / multiple bias
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS'],
                'agg_dict': {
                    'JUVENILE_VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim',
                'common_pvs': {
                    'victimAge': '[- 17 Years]'
                }
            }
        },
        {  # Victims grouped by bias category (race,religion, gender, ...)
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY'],
                'agg_dict': {
                    'JUVENILE_VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim',
                'common_pvs': {
                    'victimAge': '[- 17 Years]'
                }
            }
        }
    ],
    'victims_offense.csv': [
        {  # Victims by crime type (arson, robbery, ...)
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_NAME'],
                'agg_dict': {
                    'VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim'
            }
        },
        {  # Victims by crime category
            'df': 'unq_offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_CATEGORY'],
                'agg_dict': {
                    'VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim'
            }
        }
    ],
    'victims_offense_bias.csv': [
        {  # Offenses by crime type and bias motivation
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_DESC', 'OFFENSE_NAME'],
                'agg_dict': {
                    'VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim'
            }
        },
        {  # Offenses grouped by crime type and single bias / multiple bias
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS', 'OFFENSE_NAME'],
                'agg_dict': {
                    'VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim'
            }
        },
        {  # Offenses grouped by crime type and bias category
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY', 'OFFENSE_NAME'],
                'agg_dict': {
                    'VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim'
            }
        },
        {  # Offenses by crime type and bias motivation
            'df': 'unq_single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_DESC', 'OFFENSE_CATEGORY'],
                'agg_dict': {
                    'VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim'
            }
        },
        {  # Offenses grouped by crime type and single bias / multiple bias
            'df': 'unq_offense_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS', 'OFFENSE_CATEGORY'],
                'agg_dict': {
                    'VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim'
            }
        },
        {  # Offenses grouped by crime type and bias category
            'df': 'unq_single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY', 'OFFENSE_CATEGORY'],
                'agg_dict': {
                    'VICTIM_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Victim'
            }
        }
    ],
    'offenders_bias.csv': [
        {  # Offenders grouped by bias motivation (anti-white, ...)
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['BIAS_DESC'],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender'
            }
        },
        {  # Offenders grouped into single bias / multiple bias
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS'],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender'
            }
        },
        {  # Offenders grouped by bias category (race,religion, gender, ...)
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY'],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender'
            }
        }
    ],
    'offenders_type_bias.csv': [
        {  # Offenders grouped by bias motivation (anti-white, ...)
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['BIAS_DESC', 'OFFENDER_CATEGORY'],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender'
            }
        },
        {  # Offenders grouped into single bias / multiple bias
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS', 'OFFENDER_CATEGORY'],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender'
            }
        },
        {  # Offenders grouped by bias category (race,religion, gender, ...)
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY', 'OFFENDER_CATEGORY'],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender'
            }
        }
    ],
    'offenders_offense.csv': [
        {  # Offenders by crime type (arson, robbery, ...)
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_NAME'],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender'
            }
        },
        {  # Offenders by crime category
            'df': 'unq_offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_CATEGORY'],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender'
            }
        }
    ],
    'offenders_type_offense.csv': [
        {  # Offenders by crime type (arson, robbery, ...)
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_NAME', 'OFFENDER_CATEGORY'],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender'
            }
        },
        {  # Offenders by crime category
            'df': 'unq_offense_df',
            'args': {
                'groupby_cols': ['OFFENSE_CATEGORY', 'OFFENDER_CATEGORY'],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender'
            }
        }
    ],
    'offenders_offenderrace.csv': [
        {  # Offenders grouped into single bias / multiple bias
            'df': 'known_offender_race',
            'args': {
                'groupby_cols': [],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender',
                'common_pvs': {
                    'offenderType': 'KnownOffenderRace'
                }
            }
        },
        {  # Offenders grouped into single bias / multiple bias
            'df': 'known_offender_age',
            'args': {
                'groupby_cols': [],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender',
                'common_pvs': {
                    'offenderType': 'KnownOffenderAge'
                }
            }
        },
        {  # Offenders grouped into single bias / multiple bias
            'df': 'known_offender',
            'args': {
                'groupby_cols': ['OFFENDER_RACE'],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender',
                'common_pvs': {
                    'offenderType': 'KnownOffenderRace'
                }
            }
        }
    ],
    'offenders_offenderethnicity.csv': [
        {  # Offenders grouped into single bias / multiple bias
            'df': 'known_offender_ethnicity',
            'args': {
                'groupby_cols': [],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender',
                'common_pvs': {
                    'offenderType': 'KnownOffenderEthnicity'
                }
            }
        },
        {  # Offenders grouped into single bias / multiple bias
            'df': 'known_offender',
            'args': {
                'groupby_cols': ['OFFENDER_ETHNICITY'],
                'agg_dict': {
                    'TOTAL_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender',
                'common_pvs': {
                    'offenderType': 'KnownOffenderEthnicity'
                }
            }
        }
    ],
    'offenders_offenderadult.csv': [
        {  # Offenders grouped into single bias / multiple bias
            'df': 'known_offender',
            'args': {
                'groupby_cols': [],
                'agg_dict': {
                    'ADULT_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender',
                'common_pvs': {
                    'offenderAge': '[18 - Years]',
                    'offenderType': 'KnownOffenderAge'
                }
            }
        }
    ],
    'offenders_offenderjuvenile.csv': [
        {  # Offenders grouped into single bias / multiple bias
            'df': 'known_offender',
            'args': {
                'groupby_cols': [],
                'agg_dict': {
                    'JUVENILE_OFFENDER_COUNT': 'sum'
                },
                'population_type': 'CriminalIncidents',
                'measurement_qualifier': 'Offender',
                'common_pvs': {
                    'offenderAge': '[- 17 Years]',
                    'offenderType': 'KnownOffenderAge'
                }
            }
        }
    ],
}


def _create_df_dict(df: pd.DataFrame, use_cache: bool = False) -> dict:
    """Applies transformations on the hate crime dataframe. These transformed
    dataframes are then used in the aggregations.

    Args:
        df: A pandas.DataFrame of the hate crime data.

    Returns:
        A dictionary which has transformation name as key and the transformed
        dataframe as it's value.
    """
    # Create cache dir if not present
    if use_cache and not os.path.exists(_CACHE_DIR):
        os.mkdir(_CACHE_DIR)

    fill_unknown_cols = ['OFFENDER_RACE', 'OFFENDER_ETHNICITY']

    df['BIAS_CATEGORY'] = ''
    df_dict = {}

    df[fill_unknown_cols] = df[fill_unknown_cols].fillna('Unknown')

    incident_path = os.path.join(_CACHE_DIR, 'incident.csv')
    if use_cache and os.path.exists(incident_path):
        incident_df = pd.read_csv(incident_path)
    else:
        incident_df = df.apply(_add_bias_category, axis=1)
        incident_df = incident_df.apply(_add_offender_category, axis=1)
        incident_df = incident_df.apply(_add_multiple_victims, axis=1)
        incident_df = incident_df.apply(_add_multiple_locations, axis=1)
        incident_df.to_csv(incident_path, index=False)
    df_dict['incident_df'] = incident_df

    offense_path = os.path.join(_CACHE_DIR, 'offense.csv')
    if use_cache and os.path.exists(offense_path):
        offense_df = pd.read_csv(offense_path)
    else:
        offense_df = flatten_by_column(incident_df, 'OFFENSE_NAME')
        offense_df = offense_df.apply(_add_offense_category, axis=1)
        offense_df.to_csv(offense_path, index=False)
    df_dict['offense_df'] = offense_df

    location_path = os.path.join(_CACHE_DIR, 'location.csv')
    if use_cache and os.path.exists(location_path):
        location_df = pd.read_csv(location_path)
    else:
        location_df = flatten_by_column(incident_df, 'LOCATION_NAME')
        location_df.to_csv(location_path, index=False)
    df_dict['location_df'] = location_df

    victim_path = os.path.join(_CACHE_DIR, 'victim.csv')
    if use_cache and os.path.exists(victim_path):
        victim_df = pd.read_csv(victim_path)
    else:
        victim_df = flatten_by_column(incident_df, 'VICTIM_TYPES')
        victim_df.to_csv(victim_path, index=False)
    df_dict['victim_df'] = victim_df

    offense_victim_path = os.path.join(_CACHE_DIR, 'offense_victim.csv')
    if use_cache and os.path.exists(offense_victim_path):
        offense_victim_df = pd.read_csv(offense_victim_path)
    else:
        offense_victim_df = flatten_by_column(offense_df, 'VICTIM_TYPES')
        offense_victim_df.to_csv(victim_path, index=False)
    df_dict['offense_victim_df'] = offense_victim_df

    sb_incidents_path = os.path.join(_CACHE_DIR, 'sb_incidents.csv')
    if use_cache and os.path.exists(sb_incidents_path):
        single_bias_incidents = pd.read_csv(sb_incidents_path)
    else:
        single_bias_incidents = incident_df[incident_df['MULTIPLE_BIAS'] == 'S']
        single_bias_incidents.to_csv(sb_incidents_path, index=False)
    df_dict['single_bias_incidents'] = single_bias_incidents

    sb_offenses_path = os.path.join(_CACHE_DIR, 'sb_offenses.csv')
    if use_cache and os.path.exists(sb_offenses_path):
        single_bias_offenses = pd.read_csv(sb_offenses_path)
    else:
        single_bias_offenses = offense_df[offense_df['MULTIPLE_BIAS'] == 'S']
        single_bias_offenses.to_csv(sb_offenses_path, index=False)
    df_dict['single_bias_offenses'] = single_bias_offenses

    sb_location_path = os.path.join(_CACHE_DIR, 'sb_location.csv')
    if use_cache and os.path.exists(sb_location_path):
        single_bias_location = pd.read_csv(sb_location_path)
    else:
        single_bias_location = location_df[location_df['MULTIPLE_BIAS'] == 'S']
        single_bias_location.to_csv(sb_location_path, index=False)
    df_dict['single_bias_location'] = single_bias_location

    sb_victim_path = os.path.join(_CACHE_DIR, 'sb_victim.csv')
    if use_cache and os.path.exists(sb_victim_path):
        single_bias_victim = pd.read_csv(sb_victim_path)
    else:
        single_bias_victim = victim_df[victim_df['MULTIPLE_BIAS'] == 'S']
        single_bias_victim.to_csv(sb_victim_path, index=False)
    df_dict['single_bias_victim'] = single_bias_victim

    known_offender_path = os.path.join(_CACHE_DIR, 'known_offender.csv')
    if use_cache and os.path.exists(known_offender_path):
        known_offender = pd.read_csv(known_offender_path)
    else:
        known_offender = incident_df[incident_df['OFFENDER_CATEGORY'] ==
                                     'KnownOffender']
        known_offender.to_csv(known_offender_path, index=False)
    df_dict['known_offender'] = known_offender
    df_dict['known_offender_race'] = known_offender[
        (df['OFFENDER_RACE'] != np.nan) & (df['OFFENDER_RACE'] != 'Unknown')]
    df_dict['known_offender_ethnicity'] = known_offender[
        (df['OFFENDER_ETHNICITY'] != np.nan) &
        (df['OFFENDER_ETHNICITY'] != 'Unknown')]
    df_dict['known_offender_age'] = known_offender[
        (df['JUVENILE_OFFENDER_COUNT'] != np.nan) |
        (df['ADULT_OFFENDER_COUNT'] != np.nan)]

    os_victimtype_path = os.path.join(_CACHE_DIR, 'os_victimtype.csv')
    if use_cache and os.path.exists(os_victimtype_path):
        offense_single_victimtype_df = pd.read_csv(os_victimtype_path)
    else:
        offense_single_victimtype_df = offense_df[
            offense_df['MULTIPLE_VICTIM_TYPE'] == 'S']
        offense_single_victimtype_df.to_csv(os_victimtype_path, index=False)
    df_dict['offense_single_victimtype_df'] = offense_single_victimtype_df

    om_victimtype_path = os.path.join(_CACHE_DIR, 'om_victimtype.csv')
    if use_cache and os.path.exists(om_victimtype_path):
        offense_multiple_victimtype_df = pd.read_csv(om_victimtype_path)
    else:
        offense_multiple_victimtype_df = offense_df[
            offense_df['MULTIPLE_VICTIM_TYPE'] == 'M']
        offense_multiple_victimtype_df.to_csv(om_victimtype_path, index=False)
    df_dict['offense_multiple_victimtype_df'] = offense_multiple_victimtype_df

    unq_offense_path = os.path.join(_CACHE_DIR, 'unq_offense.csv')
    if use_cache and os.path.exists(unq_offense_path):
        unq_offense_df = pd.read_csv(unq_offense_path)
    else:
        unq_offense_df = offense_df.drop_duplicates(
            subset=['INCIDENT_ID', 'OFFENSE_CATEGORY'])
        unq_offense_df.to_csv(unq_offense_path, index=False)
    df_dict['unq_offense_df'] = unq_offense_df

    unq_sb_offenses_path = os.path.join(_CACHE_DIR, 'unq_sb_offenses.csv')
    if use_cache and os.path.exists(unq_sb_offenses_path):
        unq_single_bias_offenses = pd.read_csv(unq_sb_offenses_path)
    else:
        unq_single_bias_offenses = single_bias_offenses.drop_duplicates(
            subset=['INCIDENT_ID', 'OFFENSE_CATEGORY'])
        unq_single_bias_offenses.to_csv(unq_sb_offenses_path, index=False)
    df_dict['unq_single_bias_offenses'] = unq_single_bias_offenses

    return df_dict


def _add_bias_category(row):
    """A function to add the bias category based on the bias motivation. To be
    used with pandas.DataFrame.apply().
    """
    row['BIAS_CATEGORY'] = _BIAS_CATEGORY_MAP.get(row['BIAS_DESC'],
                                                  'MultipleBias')
    return row


def _add_offense_category(row):
    """A function to add the offense category based on the offense type. To be
    used with pandas.DataFrame.apply()
    """
    row['OFFENSE_CATEGORY'] = _OFFENSE_CATEGORY_MAP.get(row['OFFENSE_NAME'], '')
    return row


def _add_offender_category(row):
    """A function to add the offender category. To be used with
    pandas.DataFrame.apply().
    """
    row['OFFENDER_CATEGORY'] = 'UnknownOffender'

    # If offender's age, race or ethnicity is known, then it is a known offender
    if (row['ADULT_OFFENDER_COUNT'] !=
            np.nan) or (row['JUVENILE_OFFENDER_COUNT'] != np.nan) or (
                (row['OFFENDER_RACE'] != np.nan) and
                (row['OFFENDER_RACE'] != 'Unknown')) or (
                    (row['OFFENDER_ETHNICITY'] != np.nan) and
                    (row['OFFENDER_ETHNICITY'] != 'Unknown')):
        row['OFFENDER_CATEGORY'] = 'KnownOffender'
    return row


def _add_multiple_victims(row):
    """A function to add the victim types. To be used with
    pandas.DataFrame.apply()."""
    if ';' in row['VICTIM_TYPES']:
        row['MULTIPLE_VICTIM_TYPE'] = 'M'
    else:
        row['MULTIPLE_VICTIM_TYPE'] = 'S'
    return row


def _add_multiple_locations(row):
    """A function to add the victim types. To be used with
    pandas.DataFrame.apply()."""
    if ';' in row['LOCATION_NAME']:
        row['MULTIPLE_LOCATION_NAME'] = 'M'
    else:
        row['MULTIPLE_LOCATION_NAME'] = 'S'
    return row


def _get_dpv(statvar: dict, config: dict) -> list:
    """A function that goes through the statvar dict and the config and returns
    a list of properties to ignore when generating the dcid.

    Args:
        statvar: A dictionary of prop:values of the statvar
        config: A dict which expects the keys to be the column name and
          value to be another dict. This dict maps column values to key-value
          pairs of a statvar. See scripts/fbi/hate_crime/config.json for an
          example. In this function, the '_DPV_' key is used to identify 
          dependent properties.

    Returns:
        A list of properties to ignore when generating the dcid.
    """
    ignore_props = []
    for spec in config['_DPV_']:
        if spec['cprop'] in statvar:
            dpv_prop = spec['dpv']['prop']
            dpv_val = spec['dpv']['val']
            if dpv_val == statvar.get(dpv_prop, None):
                ignore_props.append(dpv_prop)
    return ignore_props


def _gen_statvar_mcf(df: pd.DataFrame,
                     config: dict,
                     population_type: str = None,
                     measurement_qualifier: str = None,
                     common_pvs: dict = None):
    """A function that creates statvars and assigns the dcid after going through
    each row in the dataframe.

    Args:
        df: A pandas dataframe whose rows are referenced to create the statvar.
        config: A dict which expects the keys to be the column name and
          value to be another dict. This dict maps column values to key-value
          pairs of a statvar. See scripts/fbi/hate_crime/config.json for an
          example.
        population_type: The populationType to assign to each statvar. If None,
          the prop is not added to the statvar.
        measurement_qualifier: The measurementQualifier to assign to each
          statvar. If None, the prop is not added to the statvar.

    Returns:
        A modified dataframe with an additional column 'StatVar' whose value is
        the statvar dcid for it's corresponding row. Also returns a statvar list
        which containts all the generated statvars.
    """
    statvar_list = []
    statvar_dcid_list = []
    df_copy = df.copy()
    for _, row in df_copy.iterrows():
        statvar = {**config['_COMMON_']}
        for col in df_copy.columns:
            if col in config:
                if row[col] in config[col]:
                    statvar.update(config[col][row[col]])

        if population_type is not None:
            statvar['populationType'] = population_type
        if measurement_qualifier is not None:
            statvar['measurementQualifier'] = measurement_qualifier
        if common_pvs is not None:
            statvar.update(common_pvs)

        ignore_props = _get_dpv(statvar, config)
        statvar['Node'] = get_statvar_dcid(statvar, ignore_props=ignore_props)

        statvar_dcid_list.append(statvar['Node'])
        statvar_list.append(statvar)
    df_copy['StatVar'] = statvar_dcid_list
    return df_copy, statvar_list


def is_quantity_range(val: str) -> bool:
    """Checks if [] are present in val.
    """
    if '[' in val and ']' in val:
        return True
    return False


def _write_statvar_mcf(statvar_list: list, f):
    """Writes statvars to a file.

    Args:
        statvar_list: A list of statvars. Each statvar is expected to be a dict.
        f: file handle for the .mcf file.
    """
    dcid_set = set()
    final_mcf = ''
    for sv in statvar_list:
        statvar_mcf_list = []
        dcid = sv['Node']
        if dcid in dcid_set:
            continue
        dcid_set.add(dcid)
        for p, v in sv.items():
            if p != 'Node':
                if is_quantity_range(v):
                    statvar_mcf_list.append(f'{p}: {v}')
                else:
                    statvar_mcf_list.append(f'{p}: dcs:{v}')
        statvar_mcf = 'Node: dcid:' + dcid + '\n' + '\n'.join(statvar_mcf_list)
        final_mcf += statvar_mcf + '\n\n'

    f.write(final_mcf)


def _create_aggr(input_df: pd.DataFrame,
                 config: dict,
                 statvar_list: list,
                 groupby_cols: list,
                 agg_dict: dict,
                 population_type: str = None,
                 measurement_qualifier: str = None,
                 common_pvs: dict = None):
    """A wrapper function that calls utils.make_time_place_aggregations and uses
    it's output to generate statvar MCF.

    Args:
        df: A list of statvars. Each statvar is expected to be a dict.
        f: file handle for the .mcf file.

    Returns:
        A list of transformed dataframes with an additional column in each
        that points to it's statvar dcid.
    """
    output_df_list = make_time_place_aggregation(input_df,
                                                 groupby_cols=groupby_cols,
                                                 agg_dict=agg_dict,
                                                 multi_index=False)

    for idx in range(len(output_df_list)):
        output_df_list[idx], statvars = _gen_statvar_mcf(
            output_df_list[idx],
            config,
            population_type=population_type,
            measurement_qualifier=measurement_qualifier,
            common_pvs=common_pvs)
        statvar_list.extend(statvars)

    return output_df_list


def _write_to_csv(df: pd.DataFrame, csv_file_name: str):
    """Writes a dataframe to a .csv file. Removes rows with an empty place value
    before writing.

    Args:
        df: A pandas dataframe to write to csv.
        csv_file_name: The filename of the csv.
    """
    df['Place'].replace('', np.nan, inplace=True)
    df.dropna(subset=['Place'], inplace=True)
    df.to_csv(csv_file_name, index=False)


if __name__ == '__main__':
    source_data_path = os.path.join(_SCRIPT_PATH, 'source_data',
                                    'hate_crime.csv')
    df = pd.read_csv(source_data_path, usecols=_INPUT_COLUMNS)

    with open('config.json', 'r') as f:
        config = json.load(f)

    config_old = copy.deepcopy(config)
    config_old['_COMMON_']['isHateCrime'] = 'True'
    config_old['BIAS_CATEGORY']['TransgenderOrGenderNonConforming'] = {
        'biasMotivation': 'TransgenderOrGenderNonConforming'
    }
    config_old['_DPV_'] = []

    _PREPEND_APPEND_REPLACE_MAP.pop('targetedRace', None)
    _PREPEND_APPEND_REPLACE_MAP.pop('targetedEthnicity', None)
    _PREPEND_APPEND_REPLACE_MAP.pop('targetedReligion', None)
    _PREPEND_APPEND_REPLACE_MAP.pop('targetedSexualOrientation', None)
    _PREPEND_APPEND_REPLACE_MAP.pop('targetedDisabilityStatus', None)
    _PREPEND_APPEND_REPLACE_MAP.pop('targetedGender', None)

    df_dict = _create_df_dict(df, False)

    # Incidents by StatVar
    # df_dict['incident_df'], statvar_list = _gen_statvar_mcf(
    #     df_dict['incident_df'], config, population_type='HateCrimeIncidents')

    # incident_by_statvar = make_time_place_aggregation(
    #     df_dict['incident_df'],
    #     groupby_cols=['StatVar'],
    #     agg_dict={'INCIDENT_ID': 'count'},
    #     multi_index=False)
    # output_csv_path = os.path.join(_SCRIPT_PATH, 'output', 'output.csv')
    # _write_to_csv(pd.concat(incident_by_statvar), output_csv_path)

    # output_mcf_path = os.path.join(_SCRIPT_PATH, 'output', 'output.mcf')
    # with open(output_mcf_path, 'w') as f:
    #     _write_statvar_mcf(statvar_list, f)

    # Aggregations
    statvar_list = []
    final_columns = ['DATA_YEAR', 'Place', 'StatVar', 'Value']
    if not os.path.exists(os.path.join(_SCRIPT_PATH, 'aggregations')):
        os.mkdir(os.path.join(_SCRIPT_PATH, 'aggregations'))

    all_aggr = []
    for file_name, aggregations in _AGGREGATIONS.items():
        print(file_name)
        aggr_list = []
        for aggr_map in aggregations:
            aggr_df = df_dict[aggr_map['df']]
            if 'query' in aggr_map:
                aggr_df = df_dict[aggr_map['df']].query(aggr_map['query'])
            aggr = _create_aggr(aggr_df, config_old, statvar_list,
                                **aggr_map['args'])
            aggr_list.extend(aggr)
            all_aggr.extend(aggr)
        aggr_csv_path = os.path.join(_SCRIPT_PATH, 'aggregations', file_name)
        _write_to_csv(pd.concat(aggr_list)[final_columns], aggr_csv_path)

    all_aggr_csv_path = os.path.join(_SCRIPT_PATH, 'aggregations',
                                     'aggregation.csv')
    _write_to_csv(pd.concat(all_aggr)[final_columns], all_aggr_csv_path)

    aggr_mcf_path = os.path.join(_SCRIPT_PATH, 'aggregations',
                                 'aggregation.mcf')
    with open(aggr_mcf_path, 'w') as f:
        _write_statvar_mcf(statvar_list, f)
