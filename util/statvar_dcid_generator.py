# Copyright 2021 Google LLC
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
"""A utility to generate dcid for statistical variables."""

import copy
import os
import re
import sys

# pylint: disable=wrong-import-position
# pylint: disable=import-error

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '.'))  # For soc_codes_names

from soc_codes_names import SOC_MAP
from naics_codes import NAICS_CODES
# pylint: enable=wrong-import-position
# pylint: enable=import-error

# Global constants
# Regex to match the quantity notations - [value quantity], [quantity value]
# Example matches: [2 Person], [Person 2]
_QUANTITY_REGEX_1 = re.compile(
    r'\[(?P<value>-|-?\d+(\.\d+)?) (?P<quantity>[A-Za-z_/\d]+)\]')
_QUANTITY_REGEX_2 = re.compile(
    r'\[(?P<quantity>[A-Za-z_/\d]+) (?P<value>-|-?\d+(\.\d+)?)\]')

# Regex to match the quantity range notations -
# [lower_limit upper_limit quantity], [quantity lower_limit upper_limit]
# Example matches: [10000 14999 USDollar], [USDollar 10000 14999]
_QUANTITY_RANGE_REGEX_1 = re.compile(r'\[(?P<lower_limit>-|-?\d+(\.\d+)?) '
                                     r'(?P<upper_limit>-|-?\d+(\.\d+)?) '
                                     r'(?P<quantity>[A-Za-z_/\d]+)\]')
_QUANTITY_RANGE_REGEX_2 = re.compile(r'\[(?P<quantity>[A-Za-z_/\d]+) '
                                     r'(?P<lower_limit>-|-?\d+(\.\d+)?) '
                                     r'(?P<upper_limit>-|-?\d+(\.\d+)?)\]')

# These are the default properties ignored during dcid generation
_DEFAULT_IGNORE_PROPS = (
    'unit',
    'Node',
    'memberOf',
    'typeOf',
    'constraintProperties',
    'name',
    'description',
    'descriptionUrl',
    'label',
    'url',
    'alternateName',
    'scalingFactor',
)

# Regex to match prefixes to be removed from constraints. The regex checks for
# specific prefixes followed by an upper case letter or underscore. This helps
# to avoid false positives like 'USCitizenBornInTheUnitedStates'.
_CONSTRAINT_PREFIX_REGEX = re.compile(
    r'(?P<prefix>^(USC|CDC|DAD|BLS|NCES|ACSED|UCR))(?P<ucase_uscore>[A-Z_])')

# Mutliple values can be assigned to a property by separating each value with
# '__' or '&'. To represent ParkOrPlayground for location of crime, we can have
# p=locationOfCrime and v=Park__Playground or v=Park&Playground.
# In the dcid, this will be represented as 'ParkOrPlayground'.
_MULTIPLE_VALUE_SEPARATOR_REGEX = re.compile(r'__|&')

# A mapping of NAICS codes to industry topics
# This map was generated using the code from the _create_naics_map function at
# https://github.com/datacommonsorg/tools/blob/master/stat_var_renaming/stat_var_renaming_constants.py

# Regex to match NAICS Codes. These codes could be a single code or a range
# Example matches: 53-56, 44
_NAICS_CODE_REGEX = re.compile(r'(\d+-\d+|\d+)')

# Regex to extract the lower and upper ranges in a range of NAICS codes
# Example matches: 53-56, 11-21
_NAICS_RANGE_REGEX = re.compile(r'(?P<lower_limit>\d+)-(?P<upper_limit>\d+)')

# Certain properties have text prepended, appended or replaced in the dcid to
# improve readability. For example, p='householderRace', v='AsianAlone' is
# changed to v='HouseholderRaceAsianAlone'. The initial map was picked from
# https://github.com/datacommonsorg/tools/blob/master/stat_var_renaming/stat_var_renaming_functions.py
# In the map, the keys are properties, the value to the key is a dict which can
# have four keys. The 'prepend' and 'append' keys can be used to prepend and
# append to a property value.The value in 'replace' is replaced with the value
# in 'replacement'.
_PREPEND_APPEND_REPLACE_MAP = {
    'languageSpokenAtHome': {
        'append': 'SpokenAtHome'
    },
    'childSchoolEnrollment': {
        'prepend': 'Child'
    },
    'residenceType': {
        'prepend': 'ResidesIn'
    },
    'healthPrevented': {
        'prepend': 'Received'
    },
    'householderAge': {
        'prepend': 'HouseholderAge'
    },
    'householderRace': {
        'prepend': 'HouseholderRace'
    },
    'dateBuilt': {
        'append': 'Built'
    },
    'homeValue': {
        'prepend': 'HomeValue'
    },
    'numberOfRooms': {
        'prepend': 'WithTotal'
    },
    'isic': {
        'prepend': 'ISIC'
    },
    'establishmentOwnership': {
        'append': 'Establishment'
    },
    'householdSize': {
        'prepend': 'With'
    },
    'householdWorkerSize': {
        'prepend': 'With'
    },
    'numberOfVehicles': {
        'prepend': 'With'
    },
    'income': {
        'prepend': 'IncomeOf'
    },
    'grossRent': {
        'prepend': 'GrossRent'
    },
    'healthOutcome': {
        'prepend': 'With'
    },
    'healthPrevention': {
        'prepend': 'Received'
    },
    'propertyTax': {
        'prepend': 'YearlyTax'
    },
    'detailedLevelOfSchool': {
        'prepend': 'Detailed'
    },
    'medicalCondition': {
        'prepend': 'Condition'
    },
    'educationalAttainment': {
        'prepend': 'EducationalAttainment'
    },
    'householderEducationalAttainment': {
        'prepend': 'HouseholderEducationalAttainment'
    },
    'householderRelatedChildrenUnder18Years': {
        'prepend': 'Householder',
        'replace': 'Child',
        'replacement': 'RelatedChildren',
    },
    'householderOwnChildrenUnder18Years': {
        'prepend': 'Householder',
        'replace': 'Child',
        'replacement': 'OwnChildren',
    },
    'occupation': {
        'append': 'Occupation'
    },
    'usualHoursWorked': {
        'prepend': 'WorkPerWeek'
    },
    'workPeriod': {
        'prepend': 'WorkPerYear'
    },
    'dateOfEntry': {
        'prepend': 'DateOfEntry',
        'replace': 'Date',
        'replacement': '',
    },
    'placeOfBirth': {
        'prepend': 'PlaceOfBirth'
    },
    'dateMovedIn': {
        'prepend': 'MovedInDate',
        'replace': 'Date',
        'replacement': '',
    },
    'bachelorsDegreeMajor': {
        'prepend': 'BachelorOf'
    },
    'biasMotivation': {
        'prepend': 'BiasMotivation'
    },
    'offenderRace': {
        'prepend': 'OffenderRace'
    },
    'offenderEthnicity': {
        'prepend': 'OffenderEthnicity'
    },
    'locationOfCrime': {
        'prepend': 'LocationOfCrime'
    },
    'victimType': {
        'prepend': 'VictimType'
    },
    'mothersRace': {
        'prepend': 'Mother'
    },
    'mothersEthnicity': {
        'prepend': 'Mother'
    },
    'mothersNativity': {
        'prepend': 'Mother'
    },
    'mothersMaritalStatus': {
        'prepend': 'Mother'
    },
    'mothersAge': {
        'prepend': 'Mother'
    },
    'mothersEducation': {
        'prepend': 'Mother'
    },
    'importSource': {
        'prepend': 'ImportFrom',
    },
    'exportDestination': {
        'prepend': 'ExportTo',
    },
    'lendingEntity': {
        'prepend': 'Lender',
    },
    'fromCurrency': {
        'prepend': 'FromCurrency_',
    },
    'toCurrency': {
        'prepend': 'ToCurrency_',
    },
    'internetUsageLocation': {
        'prepend': 'InternetUsageAt',
    }
}

# This is a list of boolean properties
_BOOLEAN_PROPS = [
    'hasComputer',
    'hasFunctionalToilet',
    'isAccessibleForFree',
    'isEnergyStored',
    'isFDAReferenceStandard',
    'isFamilyFriendly',
    'isGenomeRepresentationFull',
    'isGift',
    'isInternetUser',
    'isLiquefiedNaturalGasStored',
    'isLiveBroadcast',
    'isNaturalGasStored',
    'isPharmacodynamicRelationship',
    'isPharmacokineticRelationship',
    'isRefSeqGenBankAssembliesIdentical',
    'isHateCrime',
]

# To map stat vars which do not follow the conventions of stat var dcid naming
# The key is the dcid generated by the get_statvar_dcid function. The value is
# the replacement dcid.
_LEGACY_MAP = {
    'Count_Person_WithDisability_NoHealthInsurance':
        ('Count_Person_NoHealthInsurance_WithDisability'),
    'Count_Person_NoDisability_NoHealthInsurance':
        ('Count_Person_NoHealthInsurance_NoDisability'),
}


def _capitalize_process(word: str) -> str:
    """Capitalizes, removes namespaces, measurement constraint prefixes and

  underscores from a word.

  Manual upper casing is preferred compared to the builtin function
  str.capitalize() because we want to change only the case of the first
  character and ignore the case of other characters. Firstly, all namespaces
  are removed from the string. Then, constraint prefixes and underscores
  are removed. Lastly, the first character is upper cased.

  Args:
      word: A string literal to capitalize and process.

  Returns:
      Returns a string that can be used in dcid generation.
      Returns None if the string is empty.
  """
    if word:
        # Removing namespaces
        word = word[word.find(':') + 1:]

        # Removing constraint prefixes and replacing __ or & with 'Or'
        word_list = _MULTIPLE_VALUE_SEPARATOR_REGEX.split(word)
        for idx, w in enumerate(word_list):
            word_list[idx] = _CONSTRAINT_PREFIX_REGEX.sub(
                r'\g<ucase_uscore>', w)
        word = 'Or'.join(word_list)

        # Removing all underscores
        word = word.replace('_', '')
        # Remove '/' or replace with '-' when used as number separator
        words = []
        for tok in word.split('/'):
            if tok:
                if tok[0].isdigit() and len(
                        words) > 0 and words[-1][-1].isdigit():
                    words.append('-')
            words.append(tok[0].upper() + tok[1:]),
        word = ''.join(words)

        # Upper casing the first character
        word = word[0].upper() + word[1:]
        return word
    return None


def _generate_quantity_range_name(match_dict: dict) -> str:
    """Generate a name for a quantity range.

  Args:
      match_dict: A dictionary containing quantity range regex groups. Expected
        syntax of match_dict is { 'lower_limit': <value>, 'upper_limit':
        <value>, 'quantity': <value> }

  Returns:
      A string representing the quantity range name to be used in the dcid.
      Returns None if any of the expected keys are not in the dictionary.
  """
    try:
        lower_limit = match_dict['lower_limit']
        upper_limit = match_dict['upper_limit']
        quantity = match_dict['quantity']
    except KeyError:
        return None

    # Joining word to be used when upper_limit or lower_limit is '-'
    ul_conjunction = 'More'
    ll_conjunction = 'Less'
    quantity = _capitalize_process(quantity)

    if quantity == 'Date':  # Special case
        ul_conjunction = 'Later'
        ll_conjunction = 'Earlier'

    if upper_limit == '-':
        return f'{lower_limit}Or{ul_conjunction}{quantity}'

    if lower_limit == '-':
        return f'{upper_limit}Or{ll_conjunction}{quantity}'

    return f'{lower_limit}To{upper_limit}{quantity}'


def _naics_code_to_name(naics_val: str) -> str:
    """Converts NAICS codes to their industry using the _NAICS_MAP.

  Args:
      naics_val: A NAICS string literal to process. Expected syntax of naics_val
        - NAICS/{codes} '-' can be used to denote range of codes that may or may
        not belong to the same industry. For eg, 44-45 will be mapped to
        'RetailTrade'. '_' can be used to represent multiple industries. For eg,
        51_52 will be mapped to 'InformationFinanceInsurance'. A combination of
        '-' and '_' is acceptable.

  Returns:
      A string with all NAICS codes changed to their respective industry.
      This string can be used in dcid generation. Returns None if the string
      is empty or if the string does not follow the expected syntax.
  """

    # Helper function to process NAICS ranges
    def _process_naics_range(range_str: str) -> str:
        industry_str = ''
        match = _NAICS_RANGE_REGEX.search(range_str)
        m_dict = match.groupdict()
        lower_limit = int(m_dict['lower_limit'])
        upper_limit = int(m_dict['upper_limit'])

        prev_str = None  # To ensure the same industry is not added twice
        for code in range(lower_limit, upper_limit + 1):
            code_str = str(code)
            if code_str in NAICS_CODES and prev_str != NAICS_CODES[code_str]:
                industry_str = industry_str + NAICS_CODES[code_str]
                prev_str = NAICS_CODES[code_str]
            else:
                continue

        return industry_str

    if naics_val:
        processed_str = 'NAICS'

        # Remove namespaces
        naics_val = naics_val[naics_val.find(':') + 1:]

        # Strip NAICS/
        naics_val = naics_val.replace('NAICS/', '')

        matches = _NAICS_CODE_REGEX.findall(naics_val)
        if not matches:
            return None

        for match_str in matches:
            if match_str.find('-') != -1:  # Range
                industry_str = _process_naics_range(match_str)
            else:
                industry_str = NAICS_CODES.get(match_str)
                if not industry_str:
                    return None
            processed_str = processed_str + industry_str
        return processed_str
    return None


def _soc_code_to_name(soc_val: str) -> str:
    """Converts SOCv2018 codes to their industry using the SOC_MAP from

  soc_codes_names.py

  Args:
      soc_val: A SOCv2018 string literal to process. Expected syntax of soc_val
        - SOCv2018/{code}

  Returns:
      A string with SOC code changed to it's occupation.
      This string can be used in dcid generation. Returns the original string
      if the code is not in the SOC_MAP. Returns None if the string is empty.
  """
    if soc_val:
        processed_str = soc_val

        # Remove namespaces
        soc_val_ns_removed = soc_val[soc_val.find(':') + 1:]

        # Strip SOCv2018/ to get the code
        soc_code = soc_val_ns_removed.replace('SOCv2018/', '')

        if soc_code in SOC_MAP:
            processed_str = 'SOC' + SOC_MAP[soc_code]
        return processed_str
    return None


def _prepend_append_replace(word,
                            prepend='',
                            append='',
                            replace='',
                            replacement=''):
    """Prepends, appends and replaces text in a word.

  Args:
      word: A string literal to prepend, append or replace on.
      prepend: A string literal to prepend to word.
      append: A string literal to append to word.
      replace: A string literal that repersents a substring in word to be
        replaced.
      replacement: A string literal. In word, all occurances of replace will be
        changed to replacement.

  Returns:
      A string after appending, prepending and replacing to word.
  """
    if replace:
        word = word.replace(replace, replacement)
    if prepend and not word.lower().startswith(prepend.lower()):
        word = prepend + word
    if append:
        word = word + append
    return word


def _generate_quantity_name(match_dict: dict) -> str:
    """Generate a name for a quantity.

  Args:
      match_dict: A dictionary containing quantity regex groups. Expected syntax
        of match_dict { 'value': <value>, 'quantity': <value> }

  Returns:
      A string representing the quantity name to be used in the dcid.
      Returns None if any of the expected keys are not in the dictionary.
  """
    try:
        value = match_dict['value']
        quantity = match_dict['quantity']
    except KeyError:
        return None

    quantity = _capitalize_process(quantity)
    return f'{value}{quantity}'


def _generate_boolean_value_name(prop: str, value: str) -> str:
    """Generates a name given a boolean property and value.

  Args:
      prop: A string literal representing the boolean property name.
      value: A string literal representing the boolean property value.

  Returns:
      A string that can be used in dcid generation
  """
    if value in ('True', 'False'):
        constraint_value = value == 'True'
        pop = None
        prefix = None
        if prop.startswith('has'):
            pop = prop[3:]
            prefix = 'Has' if constraint_value else 'No'
        elif prop.startswith('is'):
            pop = prop[2:]
            prefix = 'Is' if constraint_value else 'Not'
        else:
            assert False, f'Unhandled prefix {prop}'
        return prefix + pop
    return None


def _process_constraint_property(prop: str, value: str) -> str:
    """Processes constraint property, value and returns a name that can be used

  in dcid generation.
  Args:
      prop: A string literal representing the constraint property name.
      value: A string literal representing the constraint property value.

  Returns:
      A string that can be used in dcid generation.
  """
    if 'NAICS' in value:
        name = _naics_code_to_name(value)
    elif 'SOCv2018/' in value:
        name = _soc_code_to_name(value)
    elif prop in _BOOLEAN_PROPS:
        name = _generate_boolean_value_name(prop, value)
    else:
        match1 = _QUANTITY_RANGE_REGEX_1.match(value)
        match2 = _QUANTITY_RANGE_REGEX_2.match(value)

        if match1 or match2:  # Quantity Range
            m_dict = match1.groupdict() if match1 else match2.groupdict()
            name = _generate_quantity_range_name(m_dict)
        else:
            match1 = _QUANTITY_REGEX_1.match(value)
            match2 = _QUANTITY_REGEX_2.match(value)
            if match1 or match2:  # Quantity
                m_dict = match1.groupdict() if match1 else match2.groupdict()
                name = _generate_quantity_name(m_dict)
            else:
                name = _capitalize_process(value)

    if prop in _PREPEND_APPEND_REPLACE_MAP:
        name = _prepend_append_replace(name,
                                       **_PREPEND_APPEND_REPLACE_MAP[prop])

    return name


def get_statvar_dcid(stat_var_dict: dict, ignore_props: list = None) -> str:
    """Generates the dcid given a statistical variable.

  The generated dcid will follow the pattern
  <statType>_<measuredProp>_<populationType>_<constraintVal1>_<constraintVal2>

  1. measurementQualifier is added as a prefix to the dcid.
  2. statType is included when it is not measuredValue.
  3. measurementDenominator is added as a suffix to the dcid.
  4. Constraints are sorted alphabetically based on the prop and values are
       added to the dcid.
  5. Existing dcids may not follow the above conventions. The _LEGACY_MAP maps
       generated dcids to their existing dcid.
  6. NAICS and SOC codes are replaced with their industry and occupation names
       respectively. See _NAICS_MAP and util/soc_codes_names.py for the
       mapping.
  7. Boolean constraints are replaced by their populations. For example,
       p=isInternetUser and v=True/False becomes v=isInternetUser/
       notInternetUser. See _BOOLEAN_PROPS for the properties that are
       considered for this renaming.
  8. Quantities and Quantity Ranges are changed into a name to be used in the
       dcid. For example p=age and v=[10 20 Years] becomes v=10To20Years.
  9. Certain variables have text prepended or appended to their constraints to
       improve readability. See _PREPEND_APPEND_REPLACE_MAP for more details.

  Args:
      stat_var_dict: A dictionary with property: value of the statistical
        variable as key-value pairs.
      ignore_props: A list of properties to ignore from stat_var_dict when
        generating the dcid. This list of ignore_props will be added to the
        default set of properties that are ignored. The ignore_props can be used
        to account for dependent properties to ignore when generating the dcid.
        For example in the following statVar, {
          populationType: Person
          measuredProperty: count
          statType: measuredValue
          healthInsurance: NoHealthInsurance
          armedForceStatus: Civilian
          institutionalization: USC_NonInstitutionalized } since the
            healthInsurance property indicates they are Civilian and
            USC_NonInstitutionalized, ignore_props can be the list
            ['armedForceStatus', 'institutionalization']. During the dcid
            generation process, these properties will not be considered.

  Returns:
      A string representing the dcid of the statistical variable.

  Caveats:
      1. Currently, there is no support for renaming ICD10 cause of death
           values and DEA drug names.
      2. MeasuredProp=InsuredUnemploymentRate is not changed to
           Rate_InsuredUnemployment.
      3. The generated dcids can get too long due to the large number of
           constraint props. In such cases, manual generation or the
           ignore_props arg can be used to exclude a few props from the
           generation process. It is recommended to limit the length of
           statvar dcids to 80 characters or less.
      4. This function does not differentiate between property names and only
           uses the values to generate the dcid. Two props having the same
           value, say p1=fuel, v1=Coal and p2=energy, v2=Coal will result in
           the same dcid. The _PREPEND_APPEND_REPLACE_MAP can be modified to
           disambiguate in this case.
  """

    # TODO: Renaming cause of death properties
    # TODO: Renaming DEA drug names
    # TODO: InsuredUmemploymentRate should become Rate_Insured_Unemployment

    # Helper function to add a property to the dcid list.
    def add_prop_to_list(prop: str, svd: dict, dcid_list: list):
        if prop in svd:
            token = _capitalize_process(svd[prop])
            if token is not None:
                dcid_list.append(token)
            svd.pop(prop, None)

    dcid_list = []
    denominator_suffix = ''
    svd = copy.deepcopy(stat_var_dict)

    if ignore_props is None:
        ig_p = _DEFAULT_IGNORE_PROPS
    else:
        ig_p = copy.deepcopy(ignore_props)
        ig_p.extend(_DEFAULT_IGNORE_PROPS)

    for prop in ig_p:
        svd.pop(prop, None)

    # measurementQualifier is added as a prefix
    add_prop_to_list('measurementQualifier', svd, dcid_list)

    # Add statType if statType is not measuredValue
    if ('statType' in svd) and (svd['statType'].find('measuredValue') == -1):
        svd['statType'] = svd['statType'].replace('Value', '')
        add_prop_to_list('statType', svd, dcid_list)
    svd.pop('statType', None)

    # Adding measuredProperty and populationType
    add_prop_to_list('measuredProperty', svd, dcid_list)
    add_prop_to_list('populationType', svd, dcid_list)

    # measurementDenominator is added as a suffix
    if 'measurementDenominator' in svd:
        md = svd['measurementDenominator']
        md = md[md.find(':') + 1:]  # Removing namespaces
        # Special case: PerCapita is directly appended.
        if md == 'PerCapita':
            denominator_suffix = 'PerCapita'
        # MD that are properties (camelCase) are added as Per(MD)
        # An example would be the property 'area' in Count_Person_PerArea
        elif md[0].islower():
            denominator_suffix = 'Per' + _capitalize_process(md)
        # Everything else is AsAFractionOf
        else:
            denominator_suffix = 'AsAFractionOf_' + md
        svd.pop('measurementDenominator', None)

    # Adding constraint properties in alphabetical order
    constraint_props = sorted(svd.keys(), key=str.casefold)
    for prop in constraint_props:
        name = _process_constraint_property(prop, svd[prop])
        dcid_list.append(name)

    if denominator_suffix:
        dcid_list.append(denominator_suffix)
    dcid = '_'.join(dcid_list)
    dcid = _LEGACY_MAP.get(dcid, dcid)
    return dcid
