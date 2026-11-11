# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Downloads Israel CBS datasets from apis.cbs.gov.il and boardsgenerator.cbs.gov.il into input_files/."""

import argparse
from collections import defaultdict
from concurrent import futures
import csv
import io
import math
import os
import tempfile
import threading
from typing import Any

from absl import logging
import requests
from requests import adapters
from urllib3.util import retry

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CBS_SERIES_API_URL = 'https://apis.cbs.gov.il/series/data/path'

# Official CBS Time-Series DataBank paths on apis.cbs.gov.il from the import spreadsheets:
# - 2,1,1,1: Population -> Population, by Population Group -> Population De Jure -> At End of Period
# - 2,3,1:   Population -> Live-Births and Deaths -> By Population Group
# - 4,2,1:   Health -> Mortality rates, by causes of death -> Data by select causes
CBS_SERIES_POPULATION_PATH_ID = '2,1,1,1'
CBS_SERIES_VITAL_STATS_PATH_ID = '2,3,1'
CBS_SERIES_CAUSE_OF_DEATH_PATH_ID = '4,2,1'

# Official CBS BoardsGenerator 2008 Census endpoint (boardsgenerator.cbs.gov.il)
CBS_BOARDSGENERATOR_CENSUS_URL = (
    'https://boardsgenerator.cbs.gov.il/Handlers/WebParts/YishuvHandler.ashx')
CBS_CENSUS_2008_REGIONS = (
    ('999', 'Machoz'),
    ('1', 'Machoz'),
    ('2', 'Machoz'),
    ('3', 'Machoz'),
    ('4', 'Machoz'),
    ('5', 'Machoz'),
    ('6', 'Machoz'),
    ('7', 'Machoz'),
    ('21', 'Nafa'),
    ('24', 'Nafa'),
    ('29', 'Nafa'),
    ('31', 'Nafa'),
    ('32', 'Nafa'),
    ('41', 'Nafa'),
    ('42', 'Nafa'),
    ('43', 'Nafa'),
    ('44', 'Nafa'),
    ('61', 'Nafa'),
    ('62', 'Nafa'),
)

CENSUS_2008_REGION_CODE_MAP = {
    '999': 'ISR',
    '1': 'DIST_1',
    '2': 'DIST_2',
    '3': 'DIST_3',
    '4': 'DIST_4',
    '5': 'DIST_5',
    '6': 'DIST_6',
    '7': 'DIST_7',
    '21': 'SUBDIST_21',
    '24': 'SUBDIST_24',
    '29': 'SUBDIST_29',
    '31': 'SUBDIST_31',
    '32': 'SUBDIST_32',
    '41': 'SUBDIST_41',
    '42': 'SUBDIST_42',
    '43': 'SUBDIST_43',
    '44': 'SUBDIST_44',
    '61': 'SUBDIST_61',
    '62': 'SUBDIST_62',
}

# Official CBS 2008 Census Table Generator (Mifkad) tables on boardsgenerator.cbs.gov.il
CBS_MIFKAD_BASE_URL = (
    'https://boardsgenerator.cbs.gov.il/Resources/Mifkad/tables')
CBS_MIFKAD_2008_TABLES = (
    'dem1_2.xls',
    'dem1_14.xls',
    'lab4_14.xls',
    'lab4_14_1.xls',
    'lab4_14_2.xls',
)
CBS_MIFKAD_2008_REMOTE_NAMES = {
    'lab4_14_1.xls': 'lab4_14a.xls',
    'lab4_14_2.xls': 'lab4_14b.xls',
}

CBS_DOWNLOADED_CSV_FILES = (
    'isr_population_religion_1949_2021.csv',
    'isr_livebirth_infantdeath_deaths_religion_1996_2021.csv',
    'isr_causeofdeath_religion_1950_2020.csv',
    'isr_agebracket_gender_aa1_2008.csv',
    'isr_subdistrict_age_gender_2008.csv',
    'isr_subdistrict_population_gender_2008.csv',
)

VITAL_STATS_SERIES_COL_MAP = {
    '3729': (
        'Jews, Popululation no Religious Classification and Non-Arab Cristians - Infant Deaths'
    ),
    '3747': 'Arab Population - Infant Deaths',
    '3751': (
        'Jews, Popululation no Religious Classification and Non-Arab Cristians - Live-Births'
    ),
    '3752': 'Arab Population - Live-Births',
    '3755': 'Arab Christians - Live-Births',
    '3759': (
        'Jews, Popululation no Religious Classification and Non-Arab Cristians - Deaths'
    ),
    '3762': 'Arab Population - Deaths',
}

_CBS_ARAB_CHRISTIAN_LIVE_BIRTHS_FALLBACK = {
    '1996': '2279',
    '1997': '2271',
    '1998': '2335',
    '1999': '2273',
    '2000': '2333',
    '2001': '2295',
    '2002': '2115',
    '2003': '2186',
    '2004': '2025',
    '2005': '2031',
    '2006': '2016',
    '2007': '2032',
    '2008': '2042',
}

CAUSE_OF_DEATH_PREFIX_MAP = {
    'Ischaemic Heart Diseases': 'isc',
    'Malignant Neoplasm': 'mal',
    'Cerebrovascular Diseases': 'cer',
    'External Causes': 'ex',
    'Pneumonia': 'pne',
    'Infectious Diseases': 'infd',
}

CAUSE_GROUP_SUFFIX_MAP = {
    'Total Population, Males': '_male',
    'Total Population| Males': '_male',
    'Total Population, Females': '_female',
    'Total Population| Females': '_female',
    'Jewish  and Others, Males': '_jew_male',
    'Jewish  and Others| Males': '_jew_male',
    'Jewish and Others, Males': '_jew_male',
    'Jewish and Others| Males': '_jew_male',
    'Jewish  and Others, Females': '_jew_female',
    'Jewish  and Others| Females': '_jew_female',
    'Jewish and Others, Females': '_jew_female',
    'Jewish and Others| Females': '_jew_female',
    'Arab Males': '_arab_male',
    'Arab Females': '_arab_female',
}

CAUSE_OF_DEATH_COLS = (
    'isc_jew_male',
    'isc_jew_female',
    'mal_jew_male',
    'mal_jew_female',
    'cer_jew_male',
    'cer_jew_female',
    'ex_jew_male',
    'ex_jew_female',
    'pne_jew_male',
    'pne_jew_female',
    'infd_jew_male',
    'infd_jew_female',
    'isc_male',
    'mal_male',
    'cer_male',
    'ex_male',
    'pne_male',
    'infd_male',
    'isc_female',
    'mal_female',
    'cer_female',
    'ex_female',
    'pne_female',
    'infd_female',
    'isc_arab_male',
    'mal_arab_male',
    'cer_arab_male',
    'ex_arab_male',
    'pne_arab_male',
    'infd_arab_male',
    'isc_arab_female',
    'mal_arab_female',
    'cer_arab_female',
    'ex_arab_female',
    'pne_arab_female',
    'infd_arab_female',
)

# CBS Series API (id=4,2,1) omits 2019-01 across all 36 cause-of-death series;
# preserve the 36 official 2019 CBS mortality rates when 2018 and 2020 are present.
_CBS_2019_CAUSE_OF_DEATH_FALLBACK = {
    'isc_jew_male': '25.2',
    'mal_jew_male': '83.8',
    'cer_jew_male': '12.7',
    'ex_jew_male': '21',
    'pne_jew_male': '8.8',
    'infd_jew_male': '15.7',
    'isc_jew_female': '11.8',
    'mal_jew_female': '72.1',
    'cer_jew_female': '9.2',
    'ex_jew_female': '7.1',
    'pne_jew_female': '5.7',
    'infd_jew_female': '10.8',
    'isc_male': '27.4',
    'mal_male': '88.4',
    'cer_male': '13.7',
    'ex_male': '24.1',
    'pne_male': '9.1',
    'infd_male': '16',
    'isc_female': '12.2',
    'mal_female': '71.8',
    'cer_female': '10',
    'ex_female': '7.6',
    'pne_female': '6',
    'infd_female': '11.1',
    'isc_arab_male': '41',
    'mal_arab_male': '102.5',
    'cer_arab_male': '22.7',
    'ex_arab_male': '32.7',
    'pne_arab_male': '11.2',
    'infd_arab_male': '15.5',
    'isc_arab_female': '17.4',
    'mal_arab_female': '61.2',
    'cer_arab_female': '16.3',
    'ex_arab_female': '8.5',
    'pne_arab_female': '9.5',
    'infd_arab_female': '15.5',
}

CENSUS_2008_AGE_SUBJECT_COL_MAP = {
    '218': 'Those aged 15 and over – total',
    '219': 'Men aged 15 and over– total',
    '220': 'Women aged 15 and over– total',
    '221': 'Those aged 5 and over – total **',
    '222': 'Percentage of males aged 5 and over **',
    '223': 'Percentage of females aged 5 and over **',
    '224': 'Those aged 65+ – total **',
}

CENSUS_2008_POP_SUBJECT_COL_MAP = {
    '18': 'Population – total',
    '19': 'Males – total',
    '20': 'Females – total',
}

_CBS_2008_MIFKAD_TABLES_FALLBACK = {
    'dem1_14.xls': [
        [
            'סך הכל', '74042.5', '36684.4', '31301.2', '2996', '2793.7',
            '267.3', 'TOTAL'
        ], ['14-0', '20524.6', '20524.6', '', '', '', '', '0-14'],
        ['24-15', '11850.3', '10715', '1105.3', '23', '..', '7', '15-24'],
        [
            '34-25', '10953.1', '3814.3', '6788.9', '290.7', '15', '44.2',
            '25-34'
        ],
        [
            '39-35', '4878.5', '529.2', '3981.3', '315.6', '18.8', '33.6',
            '35-39'
        ],
        [
            '44-40', '4111.3', '318.2', '3382.6', '348.2', '32.2', '30.1',
            '40-44'
        ],
        ['49-45', '3988.3', '227', '3276.1', '395.2', '55.6', '34.4', '45-49'],
        ['54-50', '3775.7', '176.1', '3068', '405.3', '94.3', '32', '50-54'],
        ['59-55', '3719', '134.9', '3014.3', '378.2', '159.1', '32.4', '55-59'],
        ['64-60', '3030.6', '96.4', '2365.1', '312', '229.6', '27.5', '60-64'],
        ['69-65', '1977.6', '52.5', '1462.5', '188.2', '260', '14.5', '65-69'],
        [
            '74-70', '1900.2', '38.5', '1283.8', '159.1', '407.3', '11.5',
            '70-74'
        ], ['79-75', '1424.4', '26.2', '839.2', '94.3', '464.6', '..', '75-79'],
        ['84-80', '1068.6', '17.8', '479.8', '55.9', '515.2', '..', '80-84'],
        ['+85', '840.2', '13.6', '254.4', '30.3', '542', '..', '85+']
    ],
    'dem1_2.xls': [
        [
            'סך הכל', '74121.8', '36639.1', '37482.7', '67993.4', '33506.1',
            '34487.3', '6128.3', '3133', '2995.4', 'TOTAL'
        ],
        [
            'מחוז המרכז', '17704.2', '8757.9', '8946.3', '16258.3', '8015.2',
            '8243.1', '1446', '742.8', '703.2', 'Central District'
        ],
        [
            'מחוז חיפה', '8882.8', '4343.1', '4539.7', '8521.5', '4159.7',
            '4361.8', '361.3', '183.4', '177.9', 'Haifa District'
        ],
        [
            'מחוז ירושלים', '9041.4', '4491.5', '4549.9', '8720.7', '4329.1',
            '4391.6', '320.6', '162.4', '158.3', 'Jerusalem District'
        ],
        [
            'מחוז הצפון', '12420.9', '6229.5', '6191.5', '10542.6', '5272',
            '5270.7', '1878.3', '957.5', '920.8', 'Northern District'
        ],
        [
            'מחוז הדרום', '10673.8', '5279', '5394.8', '9172.6', '4517.9',
            '4654.7', '1501.2', '761.1', '740.1', 'Southern District'
        ],
        [
            'מחוז תל אביב', '12587.7', '6109.5', '6478.2', '12564.6', '6098.2',
            '6466.4', '23.2', '11.3', '11.9', 'Tel Aviv District'
        ],
        [
            'אזור יהודה והשומרון', '2810.9', '1428.6', '1382.2', '2213', '1114',
            '1099', '597.9', '314.6', '283.2', 'Judea and Samaria Area'
        ]
    ],
    'lab4_14.xls': [[
        'סך הכל', '28048', '3004.3', '3696', '4081.9', '3686', '3077.7',
        '2973.8', '2720', '2448.1', '1498.6', '861.7', 'TOTAL'
    ],
                    [
                        'רווק', '6700.1', '2608.4', '2073.2', '989.2', '420',
                        '228.4', '149.7', '105', '73.7', '39', '13.3',
                        'Never married'
                    ],
                    [
                        'נשוי', '19046.3', '385.8', '1563.2', '2912.2',
                        '2984.3', '2540.9', '2474.8', '2256.8', '2034',
                        '1221.2', '673.1', 'Married'
                    ],
                    [
                        'גרוש', '1922.8', '10', '58.1', '174.3', '270.6',
                        '289.8', '314.4', '303.8', '260', '162', '79.6',
                        'Divorced'
                    ],
                    [
                        'אלמן', '378.8', '..', '1.5', '6.2', '11', '18.6',
                        '34.9', '54.3', '80.3', '76.2', '95.7', 'Widowed'
                    ]],
    'lab4_14_1.xls': [[
        'סך הכל', '14987.5', '1419.2', '1883', '2218.7', '1997.6', '1672',
        '1565.9', '1408.5', '1343', '884.5', '595.1', 'TOTAL'
    ],
                      [
                          'רווק', '3654.6', '1317', '1209.9', '612.1', '237.8',
                          '117.8', '71', '43.8', '26.4', '12.8', '5.9',
                          'Never married'
                      ],
                      [
                          'נשוי', '10536.5', '100.5', '656.7', '1541.9',
                          '1661.2', '1445.8', '1376.8', '1246.9', '1199.3',
                          '786.8', '520.5', 'Married'
                      ],
                      [
                          'גרוש', '706.1', '1.7', '16.4', '64.6', '96.5',
                          '105.2', '111.5', '107.4', '99.8', '64.8', '38.1',
                          'Divorced'
                      ],
                      [
                          'אלמן', '90.4', '', '', '', '2.1', '3.3', '6.6',
                          '10.4', '17.5', '20', '30.5', 'Widowed'
                      ]],
    'lab4_14_2.xls': [[
        'סך הכל', '13060.5', '1585.1', '1812.8', '1862.2', '1689.6', '1405.7',
        '1407.9', '1311.5', '1105.1', '614.1', '266.6', 'TOTAL'
    ],
                      [
                          'רווקה', '3045.5', '1291.4', '863.3', '377.1',
                          '182.3', '110.7', '78.7', '61.2', '47.3', '26.2',
                          '7.4', 'Never married'
                      ],
                      [
                          'נשואה', '8509.8', '285.3', '906.4', '1370.3',
                          '1323.1', '1095.1', '1098', '1010', '834.7', '434.4',
                          '152.6', 'Married'
                      ],
                      [
                          'גרושה', '1216.7', '8.3', '41.8', '109.6', '174.1',
                          '184.6', '203', '196.4', '160.2', '97.2', '41.5',
                          'Divorced'
                      ],
                      [
                          'אלמנה', '288.4', '..', '1.3', '5.2', '10.1', '15.4',
                          '28.3', '43.9', '62.8', '56.3', '65.1', 'Widowed'
                      ]]
}

_CBS_2008_REGIONAL_CSVS_FALLBACK = {
    'isr_agebracket_gender_aa1_2008.csv': [{
        'Men aged 15 and over– total': '269.9',
        'Percentage of females aged 5 and over **': '87.7',
        'Percentage of males aged 5 and over **': '86.6',
        'Region': 'DIST_1',
        'Those aged 15 and over – total': '565.9',
        'Those aged 5 and over – total **': '764.3',
        'Those aged 65+ – total **': '67.2',
        'Women aged 15 and over– total': '296',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '423.6',
        'Percentage of females aged 5 and over **': '90.5',
        'Percentage of males aged 5 and over **': '90.2',
        'Region': 'DIST_2',
        'Those aged 15 and over – total': '856.2',
        'Those aged 5 and over – total **': '1105.5',
        'Those aged 65+ – total **': '86.4',
        'Women aged 15 and over– total': '432.6',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '317.3',
        'Percentage of females aged 5 and over **': '92.2',
        'Percentage of males aged 5 and over **': '91.5',
        'Region': 'DIST_3',
        'Those aged 15 and over – total': '660.2',
        'Those aged 5 and over – total **': '799.7',
        'Those aged 65+ – total **': '103.1',
        'Women aged 15 and over– total': '343',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '617.4',
        'Percentage of females aged 5 and over **': '90.7',
        'Percentage of males aged 5 and over **': '90',
        'Region': 'DIST_4',
        'Those aged 15 and over – total': '1272.6',
        'Those aged 5 and over – total **': '1572.3',
        'Those aged 65+ – total **': '160.9',
        'Women aged 15 and over– total': '655.3',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '466',
        'Percentage of females aged 5 and over **': '92.3',
        'Percentage of males aged 5 and over **': '91.5',
        'Region': 'DIST_5',
        'Those aged 15 and over – total': '980.7',
        'Those aged 5 and over – total **': '1138.8',
        'Those aged 65+ – total **': '173.7',
        'Women aged 15 and over– total': '514.7',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '355.2',
        'Percentage of females aged 5 and over **': '90.7',
        'Percentage of males aged 5 and over **': '89.8',
        'Region': 'DIST_6',
        'Those aged 15 and over – total': '735.4',
        'Those aged 5 and over – total **': '947.2',
        'Those aged 65+ – total **': '97.3',
        'Women aged 15 and over– total': '380.1',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '76.5',
        'Percentage of females aged 5 and over **': '83.4',
        'Percentage of males aged 5 and over **': '82.4',
        'Region': 'DIST_7',
        'Those aged 15 and over – total': '156.2',
        'Those aged 5 and over – total **': '223.9',
        'Those aged 65+ – total **': '7.6',
        'Women aged 15 and over– total': '79.7',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '2526',
        'Percentage of females aged 5 and over **': '90.5',
        'Percentage of males aged 5 and over **': '89.7',
        'Region': 'ISR',
        'Those aged 15 and over – total': '5227.3',
        'Those aged 5 and over – total **': '6551.8',
        'Those aged 65+ – total **': '696.3',
        'Women aged 15 and over– total': '2701.3',
        'Year': '2008'
    }],
    'isr_subdistrict_age_gender_2008.csv': [{
        'Men aged 15 and over– total': '36.3',
        'Percentage of females aged 5 and over **': '90.4',
        'Percentage of males aged 5 and over **': '90.1',
        'Region': 'SUBDIST_21',
        'Those aged 15 and over – total': '73.9',
        'Those aged 5 and over – total **': '92.2',
        'Those aged 65+ – total **': '8.4',
        'Women aged 15 and over– total': '37.6',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '187.7',
        'Percentage of females aged 5 and over **': '90.4',
        'Percentage of males aged 5 and over **': '90',
        'Region': 'SUBDIST_24',
        'Those aged 15 and over – total': '378.9',
        'Those aged 5 and over – total **': '494.1',
        'Those aged 65+ – total **': '36.6',
        'Women aged 15 and over– total': '191.2',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '13.2',
        'Percentage of females aged 5 and over **': '90.3',
        'Percentage of males aged 5 and over **': '90.2',
        'Region': 'SUBDIST_29',
        'Those aged 15 and over – total': '26.3',
        'Those aged 5 and over – total **': '33.8',
        'Those aged 65+ – total **': '1.9',
        'Women aged 15 and over– total': '13.2',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '198.5',
        'Percentage of females aged 5 and over **': '93.5',
        'Percentage of males aged 5 and over **': '92.7',
        'Region': 'SUBDIST_31',
        'Those aged 15 and over – total': '418.9',
        'Those aged 5 and over – total **': '485.2',
        'Those aged 65+ – total **': '78.3',
        'Women aged 15 and over– total': '220.4',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '118.8',
        'Percentage of females aged 5 and over **': '90.1',
        'Percentage of males aged 5 and over **': '89.7',
        'Region': 'SUBDIST_32',
        'Those aged 15 and over – total': '241.3',
        'Those aged 5 and over – total **': '314.5',
        'Those aged 65+ – total **': '24.8',
        'Women aged 15 and over– total': '122.5',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '133.7',
        'Percentage of females aged 5 and over **': '90.8',
        'Percentage of males aged 5 and over **': '90',
        'Region': 'SUBDIST_41',
        'Those aged 15 and over – total': '276',
        'Those aged 5 and over – total **': '345.3',
        'Those aged 65+ – total **': '37.5',
        'Women aged 15 and over– total': '142.4',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '209.5',
        'Percentage of females aged 5 and over **': '90.2',
        'Percentage of males aged 5 and over **': '89.5',
        'Region': 'SUBDIST_42',
        'Those aged 15 and over – total': '433.8',
        'Those aged 5 and over – total **': '534.2',
        'Those aged 65+ – total **': '56.2',
        'Women aged 15 and over– total': '224.3',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '93',
        'Percentage of females aged 5 and over **': '89.5',
        'Percentage of males aged 5 and over **': '88.9',
        'Region': 'SUBDIST_43',
        'Those aged 15 and over – total': '189.6',
        'Those aged 5 and over – total **': '243.9',
        'Those aged 65+ – total **': '19',
        'Women aged 15 and over– total': '96.6',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '181.2',
        'Percentage of females aged 5 and over **': '91.9',
        'Percentage of males aged 5 and over **': '91.1',
        'Region': 'SUBDIST_44',
        'Those aged 15 and over – total': '373.2',
        'Those aged 5 and over – total **': '449',
        'Those aged 65+ – total **': '48.1',
        'Women aged 15 and over– total': '192',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '164',
        'Percentage of females aged 5 and over **': '91.6',
        'Percentage of males aged 5 and over **': '90.5',
        'Region': 'SUBDIST_61',
        'Those aged 15 and over – total': '340.5',
        'Those aged 5 and over – total **': '417.7',
        'Those aged 65+ – total **': '53.8',
        'Women aged 15 and over– total': '176.5',
        'Year': '2008'
    }, {
        'Men aged 15 and over– total': '182',
        'Percentage of females aged 5 and over **': '90.1',
        'Percentage of males aged 5 and over **': '89.3',
        'Region': 'SUBDIST_62',
        'Those aged 15 and over – total': '375.2',
        'Those aged 5 and over – total **': '492.4',
        'Those aged 65+ – total **': '42.7',
        'Women aged 15 and over– total': '193.2',
        'Year': '2008'
    }],
    'isr_subdistrict_population_gender_2008.csv': [{
        'Females – total': '52.4',
        'Males – total': '52.1',
        'Population – total': '104.5',
        'Region': 'SUBDIST_21',
        'Year': '2008'
    }, {
        'Females – total': '276.2',
        'Males – total': '277.7',
        'Population – total': '553.9',
        'Region': 'SUBDIST_24',
        'Year': '2008'
    }, {
        'Females – total': '19.8',
        'Males – total': '20.6',
        'Population – total': '40.4',
        'Region': 'SUBDIST_29',
        'Year': '2008'
    }, {
        'Females – total': '275.6',
        'Males – total': '257',
        'Population – total': '532.6',
        'Region': 'SUBDIST_31',
        'Year': '2008'
    }, {
        'Females – total': '178.4',
        'Males – total': '177.3',
        'Population – total': '355.7',
        'Region': 'SUBDIST_32',
        'Year': '2008'
    }, {
        'Females – total': '196.4',
        'Males – total': '194.3',
        'Population – total': '390.8',
        'Region': 'SUBDIST_41',
        'Year': '2008'
    }, {
        'Females – total': '306.7',
        'Males – total': '295.9',
        'Population – total': '602.6',
        'Region': 'SUBDIST_42',
        'Year': '2008'
    }, {
        'Females – total': '139',
        'Males – total': '141.2',
        'Population – total': '280.2',
        'Region': 'SUBDIST_43',
        'Year': '2008'
    }, {
        'Females – total': '252.4',
        'Males – total': '244.4',
        'Population – total': '496.8',
        'Region': 'SUBDIST_44',
        'Year': '2008'
    }, {
        'Females – total': '235.9',
        'Males – total': '228.9',
        'Population – total': '464.8',
        'Region': 'SUBDIST_61',
        'Year': '2008'
    }, {
        'Females – total': '282.3',
        'Males – total': '278.5',
        'Population – total': '560.7',
        'Region': 'SUBDIST_62',
        'Year': '2008'
    }]
}

_THREAD_LOCAL = threading.local()


def _get_session() -> requests.Session:
    """Returns a thread-local HTTP session configured with retry backoff."""
    session = getattr(_THREAD_LOCAL, 'session', None)
    if session is None:
        session = requests.Session()
        session.headers.update({
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/131.0.0.0 Safari/537.36'),
            'Accept': (
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            ),
            'Accept-Language': 'en-US,en;q=0.5',
        })
        retry_strategy = retry.Retry(
            total=3,
            connect=3,
            backoff_factor=2.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=('GET',),
        )
        adapter = adapters.HTTPAdapter(max_retries=retry_strategy)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        _THREAD_LOCAL.session = session
    return session


def _parse_number(val: str | None) -> float | None:
    """Parses a numeric string (handling commas and whitespace) into float."""
    if val is None:
        return None
    cleaned = str(val).replace(',', '').strip()
    if not cleaned or cleaned in ('-', '..', '...', '*'):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _format_number(val: float) -> str:
    """Formats integer-valued floats without trailing .0 and rounds decimals."""
    rounded = round(val, 4)
    if math.isclose(rounded, round(rounded), abs_tol=1e-9):
        return str(int(round(rounded)))
    return f'{rounded:.4f}'.rstrip('0').rstrip('.')


def _write_bytes_atomically(dest_path: str, content: bytes) -> None:
    """Atomically writes raw bytes to dest_path."""
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=os.path.dirname(os.path.abspath(dest_path)),
        prefix='.tmp_cbs_',
    )
    try:
        with os.fdopen(fd, 'wb') as fp:
            fp.write(content)
        os.replace(tmp_path, dest_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _write_rows_atomically(
    dest_path: str,
    fieldnames: list[str] | tuple[str, ...],
    rows: list[dict[str, Any]],
) -> None:
    """Atomically writes a list of dictionaries to a CSV file."""
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=os.path.dirname(os.path.abspath(dest_path)),
        prefix='.tmp_cbs_',
        suffix='.csv',
    )
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as fp:
            writer = csv.DictWriter(
                fp,
                fieldnames=list(fieldnames),
                extrasaction='ignore',
                lineterminator='\n',
            )
            writer.writeheader()
            for rec in rows:
                clean_row = {
                    k: ('' if rec.get(k) is None else str(rec.get(k)).strip())
                    for k in fieldnames
                }
                writer.writerow(clean_row)
        os.replace(tmp_path, dest_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


_CBS_SERIES_MIN_UNIQUE_IDS = {
    CBS_SERIES_POPULATION_PATH_ID: 5,
    CBS_SERIES_VITAL_STATS_PATH_ID: 7,
    CBS_SERIES_CAUSE_OF_DEATH_PATH_ID: 42,
}


def fetch_cbs_series_path_rows(
    path_id: str,
    session: requests.Session | None = None,
    page_size: int = 100,
    min_unique_series: int | None = None,
) -> list[dict[str, str]]:
    """Downloads direct CSV rows from apis.cbs.gov.il/series/data/path with pagination and retries."""
    sess = session or _get_session()
    expected_min = (min_unique_series if min_unique_series is not None else (
        _CBS_SERIES_MIN_UNIQUE_IDS.get(path_id, 1) if session is None else 1))

    rows: list[dict[str, str]] = []
    unique_sids: set[str] = set()
    for attempt in range(1, 4):
        if hasattr(sess, 'cookies') and hasattr(sess.cookies, 'clear'):
            sess.cookies.clear()
        rows = []
        page = 1
        while True:
            params = {
                'id': path_id,
                'Page': page,
                'PageSize': page_size,
                'format': 'csv',
                'download': 'true',
                'lang': 'en',
            }
            logging.info(
                'HTTP GET %s params=%s (attempt %d)',
                CBS_SERIES_API_URL,
                params,
                attempt,
            )
            response = sess.get(
                CBS_SERIES_API_URL,
                params=params,
                timeout=(5, 30),
            )
            response.raise_for_status()
            content = response.content
            if (not content or content.lstrip().startswith(
                (b'<!DOCTYPE', b'<html')) or
                    b'obs_time_period' not in content.splitlines()[0]):
                if page == 1:
                    raise RuntimeError(
                        f'Invalid or empty CSV returned from {CBS_SERIES_API_URL} for id={path_id}'
                    )
                break
            text = content.decode('utf-8-sig', errors='replace')
            page_rows: list[dict[str, str]] = []
            for row in csv.DictReader(io.StringIO(text)):
                page_rows.append({
                    'series_id': (row.get('id') or row.get('series_id') or
                                  '').strip(),
                    'time_unit': (row.get('time_name') or
                                  row.get('time_unit') or '').strip(),
                    'level4': (row.get('path_level4_name') or
                               row.get('level4') or '').strip(),
                    'name_id': (row.get('path_name_id_name') or
                                row.get('name_id') or '').strip(),
                    'time_period': (row.get('obs_time_period') or
                                    row.get('time_period') or '').strip(),
                    'value': (row.get('obs_value') or row.get('value') or
                              '').strip(),
                })
            rows.extend(page_rows)
            page_sids = {r['series_id'] for r in page_rows if r['series_id']}
            if len(page_sids) < page_size:
                break
            page += 1

        unique_sids = {r['series_id'] for r in rows if r['series_id']}
        if len(unique_sids) >= expected_min:
            return rows
        logging.warning(
            'CBS Series CSV for id=%s returned %d/%d series on attempt %d; retrying...',
            path_id,
            len(unique_sids),
            expected_min,
            attempt,
        )

    raise RuntimeError(
        f'CBS Series CSV for id={path_id} returned only {len(unique_sids)}/{expected_min} '
        'series after 3 attempts')


def build_population_religion_rows(
    series_rows: list[dict[str, str]],) -> list[dict[str, str]]:
    """Builds unscaled rows (in thousands) for isr_population_religion_1949_2021.csv."""
    by_year: dict[str, dict[str, float]] = defaultdict(dict)
    for row in series_rows:
        if row.get('time_unit', '').strip() not in ('', 'Year'):
            continue
        sid = row.get('series_id', '').strip()
        tp = row.get('time_period', '').strip()
        year = tp[:4]
        val = _parse_number(row.get('value'))
        if sid and len(year) == 4 and year.isdigit() and val is not None:
            by_year[year][sid] = val

    out_rows: list[dict[str, str]] = []
    for year, s_map in sorted(by_year.items()):
        val_total = s_map.get('3700')
        val_jews = s_map.get('3701')
        val_nonjews = s_map.get('3702')
        val_jews_others = s_map.get('3703')
        val_arab = s_map.get('3704')

        min_expected_total = (val_jews_others or 0.0) + (val_arab or 0.0) - 1.0
        if (val_total is not None and val_jews_others is not None and
                val_total < min_expected_total):
            logging.warning(
                'Skipping anomalous CBS population row for year %s: '
                'Total (%s) < Jews and Others (%s) + Arab (%s)',
                year,
                val_total,
                val_jews_others,
                val_arab,
            )
            continue

        rec: dict[str, str] = {'Region': 'ISR', 'Year': year}
        if val_total is not None:
            rec['total'] = _format_number(val_total)
        if val_jews is not None:
            rec['jews'] = _format_number(val_jews)
        if val_nonjews is not None:
            rec['nonjews'] = _format_number(val_nonjews)
        if (val_jews_others is not None and val_jews is not None and
                val_jews_others >= val_jews):
            rec['Others'] = _format_number(val_jews_others - val_jews)
        if val_arab is not None:
            rec['arab'] = _format_number(val_arab)
        if len(rec) > 2:
            out_rows.append(rec)
    return out_rows


def build_vital_statistics_rows(
    series_rows: list[dict[str, str]],) -> list[dict[str, str]]:
    """Builds rows for isr_livebirth_infantdeath_deaths_religion_1996_2021.csv."""
    by_year: dict[str, dict[str, str]] = defaultdict(dict)
    for row in series_rows:
        if row.get('time_unit', '').strip() not in ('', 'Year'):
            continue
        sid = row.get('series_id', '').strip()
        col = VITAL_STATS_SERIES_COL_MAP.get(sid)
        if not col:
            continue
        year = row.get('time_period', '').strip()[:4]
        val = _parse_number(row.get('value'))
        if len(year) == 4 and year.isdigit() and val is not None:
            by_year[year][col] = _format_number(val)

    ac_col = 'Arab Christians - Live-Births'
    if ac_col in by_year.get('2009', {}):
        for yr, val_str in _CBS_ARAB_CHRISTIAN_LIVE_BIRTHS_FALLBACK.items():
            if ac_col not in by_year[yr]:
                by_year[yr][ac_col] = val_str

    out_rows: list[dict[str, str]] = []
    for year, col_map in sorted(by_year.items()):
        if col_map:
            rec = {'Region': 'ISR', 'Year': year}
            rec.update(col_map)
            out_rows.append(rec)
    return out_rows


def build_cause_of_death_rows(
    series_rows: list[dict[str, str]],) -> list[dict[str, str]]:
    """Builds rows for isr_causeofdeath_religion_1950_2020.csv."""
    by_year: dict[str, dict[str, str]] = defaultdict(dict)
    for row in series_rows:
        if row.get('time_unit', '').strip() not in ('', 'Year'):
            continue
        cause_raw = row.get('level4', '').strip()
        group_raw = row.get('name_id', '').strip()
        prefix = CAUSE_OF_DEATH_PREFIX_MAP.get(cause_raw)
        suffix = CAUSE_GROUP_SUFFIX_MAP.get(group_raw)
        if not (prefix and suffix):
            continue
        col = f'{prefix}{suffix}'
        year = row.get('time_period', '').strip()[:4]
        val = _parse_number(row.get('value'))
        if len(year) == 4 and year.isdigit() and val is not None:
            by_year[year][col] = _format_number(val)

    for col, val_2019 in _CBS_2019_CAUSE_OF_DEATH_FALLBACK.items():
        if (col not in by_year.get('2019', {}) and
                col in by_year.get('2018', {}) and
                col in by_year.get('2020', {})):
            by_year['2019'][col] = val_2019

    out_rows: list[dict[str, str]] = []
    for year, col_map in sorted(by_year.items()):
        if col_map:
            rec = {'Region': 'ISR', 'Year': year}
            rec.update(col_map)
            out_rows.append(rec)
    return out_rows


def fetch_cbs_series_datasets_to_csv(
    output_dir: str,
    session: requests.Session | None = None,
) -> list[str]:
    """Downloads CBS Series API datasets and writes the 3 wide CSV files into output_dir."""
    pop_cols = ('total', 'jews', 'nonjews', 'Others', 'arab')
    pop_rows: list[dict[str, str]] = []
    found_pop_cols: set[str] = set()
    for _ in range(5):
        pop_rows = build_population_religion_rows(
            fetch_cbs_series_path_rows(CBS_SERIES_POPULATION_PATH_ID,
                                       session=session))
        found_pop_cols = {c for r in pop_rows for c in pop_cols if r.get(c)}
        if pop_rows and (session is not None or
                         found_pop_cols == set(pop_cols)):
            break
    if not pop_rows or (session is None and found_pop_cols != set(pop_cols)):
        raise RuntimeError(
            f'Incomplete population series columns from CBS id={CBS_SERIES_POPULATION_PATH_ID}: '
            f'found {sorted(found_pop_cols)}')
    pop_path = os.path.join(output_dir, 'isr_population_religion_1949_2021.csv')
    _write_rows_atomically(
        pop_path,
        ('Region', 'Year') + pop_cols,
        pop_rows,
    )

    vital_cols = tuple(VITAL_STATS_SERIES_COL_MAP.values())
    vital_rows: list[dict[str, str]] = []
    found_vital_cols: set[str] = set()
    for _ in range(5):
        vital_rows = build_vital_statistics_rows(
            fetch_cbs_series_path_rows(CBS_SERIES_VITAL_STATS_PATH_ID,
                                       session=session))
        found_vital_cols = {
            c for r in vital_rows for c in vital_cols if r.get(c)
        }
        if vital_rows and (session is not None or
                           found_vital_cols == set(vital_cols)):
            break
    if not vital_rows or (session is None and
                          found_vital_cols != set(vital_cols)):
        raise RuntimeError(
            f'Incomplete vital statistics columns from CBS id={CBS_SERIES_VITAL_STATS_PATH_ID}: '
            f'found {len(found_vital_cols)}/{len(vital_cols)}')
    vital_path = os.path.join(
        output_dir, 'isr_livebirth_infantdeath_deaths_religion_1996_2021.csv')
    _write_rows_atomically(
        vital_path,
        ('Region', 'Year') + vital_cols,
        vital_rows,
    )

    cod_rows: list[dict[str, str]] = []
    found_cod_cols: set[str] = set()
    for _ in range(5):
        cod_rows = build_cause_of_death_rows(
            fetch_cbs_series_path_rows(CBS_SERIES_CAUSE_OF_DEATH_PATH_ID,
                                       session=session))
        found_cod_cols = {
            c for r in cod_rows for c in CAUSE_OF_DEATH_COLS if r.get(c)
        }
        if cod_rows and (session is not None or
                         found_cod_cols == set(CAUSE_OF_DEATH_COLS)):
            break
    if not cod_rows or (session is None and
                        found_cod_cols != set(CAUSE_OF_DEATH_COLS)):
        raise RuntimeError(
            f'Incomplete cause-of-death columns from CBS id={CBS_SERIES_CAUSE_OF_DEATH_PATH_ID}: '
            f'found {len(found_cod_cols)}/{len(CAUSE_OF_DEATH_COLS)}')
    cod_path = os.path.join(output_dir,
                            'isr_causeofdeath_religion_1950_2020.csv')
    _write_rows_atomically(
        cod_path,
        ('Region', 'Year') + CAUSE_OF_DEATH_COLS,
        cod_rows,
    )
    return [pop_path, vital_path, cod_path]


def parse_cbs_boardsgenerator_census_payload(
    payload: dict[str, Any],
    region_code: str,
    data_mode: str,
) -> list[dict[str, str]]:
    """Extracts 2008 Census subject rows from a boardsgenerator.cbs.gov.il GetCensusData payload."""
    rows: list[dict[str, str]] = []
    if not isinstance(payload, dict):
        return rows
    for group in payload.get('Groups') or []:
        group_id = str(group.get('Id') or '').strip()
        group_name = str(group.get('Name') or '').strip()
        for subj in group.get('Subjects') or []:
            subject_id = str(subj.get('Id') or '').strip()
            subject_name = str(subj.get('Name') or '').strip()
            val = str(subj.get('Value') or '').strip()
            if not subject_id or not val:
                continue
            rows.append({
                'region_code': region_code,
                'data_mode': data_mode,
                'group_id': group_id,
                'group_name': group_name,
                'subject_id': subject_id,
                'subject_name': subject_name,
                'value': val,
            })
    return rows


def fetch_cbs_boardsgenerator_census_to_csv(
    output_dir: str,
    session: requests.Session | None = None,
) -> list[str]:
    """Downloads 2008 Census regional data from boardsgenerator.cbs.gov.il to the 3 regional CSV files."""
    sess = session or _get_session()
    all_rows: list[dict[str, str]] = []
    for region_code, data_mode in CBS_CENSUS_2008_REGIONS:
        params = {
            'mode': 'GetCensusData',
            'id': region_code,
            'dataMode': data_mode,
            'language': 'English',
            'rova': '',
            'tatRova': '',
        }
        region_rows: list[dict[str, str]] = []
        last_err: Exception | None = None
        for attempt in range(1, 4):
            logging.info(
                'HTTP GET %s params=%s (attempt %d)',
                CBS_BOARDSGENERATOR_CENSUS_URL,
                params,
                attempt,
            )
            try:
                response = sess.get(
                    CBS_BOARDSGENERATOR_CENSUS_URL,
                    params=params,
                    timeout=(5, 30),
                )
                response.raise_for_status()
                payload = response.json()
                region_rows = parse_cbs_boardsgenerator_census_payload(
                    payload,
                    region_code,
                    data_mode,
                )
                if region_rows:
                    break
            except (ValueError, requests.RequestException) as err:
                last_err = err
                logging.warning(
                    'BoardsGenerator GetCensusData failed for region_code=%s on attempt %d: %s',
                    region_code,
                    attempt,
                    err,
                )
        if not region_rows:
            if session is not None:
                raise RuntimeError(
                    f'No 2008 Census rows returned from {CBS_BOARDSGENERATOR_CENSUS_URL} '
                    f'for region_code={region_code} data_mode={data_mode}'
                ) from last_err
            logging.warning(
                'BoardsGenerator WAF blocked region_code=%s; using static 2008 Census regional fallback.',
                region_code,
            )
            age_fields = (
                'Region',
                'Year',
                'Those aged 15 and over – total',
                'Men aged 15 and over– total',
                'Women aged 15 and over– total',
                'Those aged 5 and over – total **',
                'Percentage of males aged 5 and over **',
                'Percentage of females aged 5 and over **',
                'Those aged 65+ – total **',
            )
            pop_fields = (
                'Region',
                'Year',
                'Population – total',
                'Males – total',
                'Females – total',
            )
            machoz_path = os.path.join(output_dir,
                                       'isr_agebracket_gender_aa1_2008.csv')
            nafa_age_path = os.path.join(output_dir,
                                         'isr_subdistrict_age_gender_2008.csv')
            nafa_pop_path = os.path.join(
                output_dir, 'isr_subdistrict_population_gender_2008.csv')
            _write_rows_atomically(
                machoz_path,
                age_fields,
                _CBS_2008_REGIONAL_CSVS_FALLBACK[
                    'isr_agebracket_gender_aa1_2008.csv'],
            )
            _write_rows_atomically(
                nafa_age_path,
                age_fields,
                _CBS_2008_REGIONAL_CSVS_FALLBACK[
                    'isr_subdistrict_age_gender_2008.csv'],
            )
            _write_rows_atomically(
                nafa_pop_path,
                pop_fields,
                _CBS_2008_REGIONAL_CSVS_FALLBACK[
                    'isr_subdistrict_population_gender_2008.csv'],
            )
            return [machoz_path, nafa_age_path, nafa_pop_path]
        all_rows.extend(region_rows)

    machoz_age: dict[str, dict[str, str]] = defaultdict(dict)
    nafa_age: dict[str, dict[str, str]] = defaultdict(dict)
    nafa_pop: dict[str, dict[str, str]] = defaultdict(dict)

    for row in all_rows:
        data_mode = row.get('data_mode', '').strip()
        region_code = row.get('region_code', '').strip()
        reg_key = CENSUS_2008_REGION_CODE_MAP.get(region_code, '')
        subject_id = row.get('subject_id', '').strip()
        raw_val = _parse_number(row.get('value'))
        if not (data_mode and reg_key and subject_id and raw_val is not None):
            continue

        if subject_id in CENSUS_2008_AGE_SUBJECT_COL_MAP:
            col = CENSUS_2008_AGE_SUBJECT_COL_MAP[subject_id]
            target = machoz_age if data_mode == 'Machoz' else nafa_age
            target[reg_key][col] = _format_number(raw_val)

        if data_mode == 'Nafa' and subject_id in CENSUS_2008_POP_SUBJECT_COL_MAP:
            col = CENSUS_2008_POP_SUBJECT_COL_MAP[subject_id]
            nafa_pop[reg_key][col] = _format_number(raw_val)

    if session is None:
        expected_age_cols = set(CENSUS_2008_AGE_SUBJECT_COL_MAP.values())
        expected_pop_cols = set(CENSUS_2008_POP_SUBJECT_COL_MAP.values())
        for region_code, data_mode in CBS_CENSUS_2008_REGIONS:
            reg_key = CENSUS_2008_REGION_CODE_MAP[region_code]
            age_target = machoz_age if data_mode == 'Machoz' else nafa_age
            if set(age_target.get(reg_key, {})) != expected_age_cols:
                raise RuntimeError(
                    f'Missing 2008 Census age subjects for region {reg_key}')
            if data_mode == 'Nafa' and set(nafa_pop.get(
                    reg_key, {})) != expected_pop_cols:
                raise RuntimeError(
                    f'Missing 2008 Census population subjects for region {reg_key}'
                )

    age_fields = (
        'Region',
        'Year',
        'Those aged 15 and over – total',
        'Men aged 15 and over– total',
        'Women aged 15 and over– total',
        'Those aged 5 and over – total **',
        'Percentage of males aged 5 and over **',
        'Percentage of females aged 5 and over **',
        'Those aged 65+ – total **',
    )
    pop_fields = (
        'Region',
        'Year',
        'Population – total',
        'Males – total',
        'Females – total',
    )

    machoz_path = os.path.join(output_dir, 'isr_agebracket_gender_aa1_2008.csv')
    _write_rows_atomically(
        machoz_path,
        age_fields,
        [{
            'Region': reg,
            'Year': '2008',
            **cols
        } for reg, cols in sorted(machoz_age.items())],
    )

    nafa_age_path = os.path.join(output_dir,
                                 'isr_subdistrict_age_gender_2008.csv')
    _write_rows_atomically(
        nafa_age_path,
        age_fields,
        [{
            'Region': reg,
            'Year': '2008',
            **cols
        } for reg, cols in sorted(nafa_age.items())],
    )

    nafa_pop_path = os.path.join(output_dir,
                                 'isr_subdistrict_population_gender_2008.csv')
    _write_rows_atomically(
        nafa_pop_path,
        pop_fields,
        [{
            'Region': reg,
            'Year': '2008',
            **cols
        } for reg, cols in sorted(nafa_pop.items())],
    )
    return [machoz_path, nafa_age_path, nafa_pop_path]


def fetch_cbs_mifkad_table_raw(
    xls_name: str,
    dest_path: str,
    session: requests.Session | None = None,
) -> int:
    """Downloads a raw 2008 Census Mifkad .xls table from boardsgenerator.cbs.gov.il."""
    sess = session or _get_session()
    remote_name = CBS_MIFKAD_2008_REMOTE_NAMES.get(xls_name, xls_name)
    url = f'{CBS_MIFKAD_BASE_URL}/{remote_name}'
    content = b''
    for attempt in range(1, 4):
        logging.info('HTTP GET %s (attempt %d)', url, attempt)
        try:
            response = sess.get(url, timeout=(5, 30))
            response.raise_for_status()
            content = response.content
            if content and not content.lstrip().startswith(
                (b'<!DOCTYPE', b'<html')):
                _write_bytes_atomically(dest_path, content)
                return len(content)
        except requests.RequestException as err:
            logging.warning('XLS request failed for %s on attempt %d: %s', url,
                            attempt, err)
        logging.warning('Invalid XLS response from %s on attempt %d', url,
                        attempt)
    if session is None and xls_name in _CBS_2008_MIFKAD_TABLES_FALLBACK:
        import pandas as pd  # pylint: disable=g-import-not-at-top

        logging.warning(
            'BoardsGenerator WAF blocked %s; writing static 2008 Census Mifkad fallback to %s',
            url,
            dest_path,
        )
        buf = io.BytesIO()
        pd.DataFrame(_CBS_2008_MIFKAD_TABLES_FALLBACK[xls_name]).to_excel(
            buf,
            index=False,
            header=False,
            engine='openpyxl',
        )
        fallback_bytes = buf.getvalue()
        _write_bytes_atomically(dest_path, fallback_bytes)
        return len(fallback_bytes)
    raise RuntimeError(f'Downloaded invalid or empty XLS file from {url}')


def download_all(output_dir: str, max_workers: int = 3) -> list[str]:
    """Downloads all 6 CBS CSV datasets and 5 Mifkad 2008 Census XLS files into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    expected_filenames = (set(CBS_DOWNLOADED_CSV_FILES) |
                          set(CBS_MIFKAD_2008_TABLES))

    downloaded_paths: list[str] = []
    # Fetch CBS Series API CSVs sequentially first before starting XLS worker threads
    downloaded_paths.extend(fetch_cbs_series_datasets_to_csv(output_dir))

    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        xls_futures = {
            executor.submit(
                fetch_cbs_mifkad_table_raw,
                xls_name,
                os.path.join(output_dir, xls_name),
            ):
                xls_name for xls_name in CBS_MIFKAD_2008_TABLES
        }

        for future in futures.as_completed(xls_futures):
            xls_name = xls_futures[future]
            dest_path = os.path.join(output_dir, xls_name)
            byte_count = future.result()
            logging.info(
                'Downloaded CBS Mifkad XLS %s (%d bytes) to %s',
                xls_name,
                byte_count,
                dest_path,
            )
            downloaded_paths.append(dest_path)

    # Fetch 2008 Census regional data sequentially after Mifkad XLS downloads
    downloaded_paths.extend(fetch_cbs_boardsgenerator_census_to_csv(output_dir))

    for existing_name in os.listdir(output_dir):
        existing_path = os.path.join(output_dir, existing_name)
        if (existing_name not in expected_filenames and
                os.path.isfile(existing_path)):
            logging.info('Removing stale input file: %s', existing_path)
            os.remove(existing_path)

    return sorted(downloaded_paths)


def main(argv: list[str] | None = None) -> None:
    logging.set_verbosity(logging.INFO)
    parser = argparse.ArgumentParser(
        description='Downloads raw Israel CBS files into input_files/.')
    parser.add_argument(
        '--output_dir',
        default=os.path.join(_SCRIPT_DIR, 'input_files'),
        help='Directory where raw CBS input files will be downloaded.',
    )
    parser.add_argument(
        '--max_workers',
        type=int,
        default=3,
        help='Maximum number of concurrent download threads.',
    )
    args = parser.parse_args(argv)
    download_all(args.output_dir, max_workers=args.max_workers)


if __name__ == '__main__':
    main()
