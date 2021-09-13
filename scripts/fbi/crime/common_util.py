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

import os
import sys

# For import util.alpha2_to_dcid
_CODEDIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(_CODEDIR, '../../../'))

import csv
import io
import ssl
import urllib.request
import sys
import requests
import re
import os

import pandas as pd
import logging
import util.alpha2_to_dcid as alpha2_to_dcid

# Automate Template MCF generation since there are many Statitical Variables.
TEMPLATE_MCF_TEMPLATE = """
Node: E:FBI_Crime->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
observationAbout: C:FBI_Crime->GeoId
observationDate: C:FBI_Crime->Year
observationPeriod: "P1Y"
value: C:FBI_Crime->{stat_var}
"""

# From 2013-2016, the FBI reported statistics for two different definitions of rape before fully transitioning to the current definition in 2017.
YEARS_WITH_TWO_RAPE_COLUMNS = {'2013', '2014', '2015', '2016'}


def remove_extra_chars(c):
    # Remove commas and quotes from string c, and any trailing whitespace.
    # Return the cleaned_string
    return re.sub(r'[,"]', '', c).strip()


def remove_digits(c):
    # Remove digits from string c
    # Return the cleaned string
    return re.sub(r'[\d]', '', c)


def is_digit(x):
    try:
        float(x)
        return True
    except ValueError:
        return False


def int_from_field(f):
    # Convert a field to int value. If field is empty or non-convertible, return 0.
    # Numeric number was read in as string with ".0" suffix, eg: "12.0". First convert to float, then to int.
    try:
        f = float(f)
        f = int(f)
        return f
    except ValueError as err:
        return 0
