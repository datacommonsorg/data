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
"""
Module to generate a column map to their corresponding statistical variable defintions.
"""
import os
import io
import sys
import logging
import json
import re
import csv
import pandas as pd
from zipfile import ZipFile
from collections import OrderedDict

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(
    _SCRIPT_PATH, '../../../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_statvar_dcid

# intitalize the logger
logging.basicConfig(
    level=logging.ERROR,
    filename=os.path.join(_SCRIPT_PATH, 'make_column_map.log'),
    format="{asctime} {processName:<12} {message} ({filename}:{lineno})",
    style="{",
    filemode='w')
logging.StreamHandler(stream=None)
logger = logging.getLogger(__file__)
logger.setLevel(logging.CRITICAL)

# list of properties that every statistical variable should contain
_MANDATORY_PROPS = ['measuredProperty', 'populationType', 'statType']

# list of keys expected in the JSON spec, if they are not defined, we set as an
# empty dictionary
_JSON_KEYS = [
    'populationType', 'measurement', 'pvs', 'inferredSpec',
    'enumSpecializations', 'universePVs', 'ignoreColumns', 'overwrite_dcids',
    'preprocess'
]


def process_csv_file(csv_file_path: str,
                     spec_path: str,
                     write_output: bool = True,
                     output_dir_path: str = './',
                     delimiter: str = '!!',
                     header_row: int = 1) -> dict:
    """
    Given a csv census data file, the function builds a column map for each year
    
      Args:
        csv_file_path: input zip file with data files in csv format, file naming expected to be consistent with data.census.gov
        spec_path: File path where the JSON specification to be used for generating the column map is present
        write_output: Boolean to allow saving the generated column map to an out_dir_path. (default = False)
        output_dir_path: File path to the directory where column map is to be saved (default=./)
        delimiter: specify the string delimiter used in the column names. (default=!!, for subject tables)
        header: specify the index of the row where the column names are found in the csv files (default=1, for subject tables)

      Returns:
        A dictionary mapping each year with the corresponding column_map from generate_stat_var_map()
        Example:
          "2016": {
            "Total Civilian population": {
              "populationType": "Person",
              "statType": "measuredValue",
              "measuredProperty": "Count Person"
              "armedForceStatus": "Civilian"
            },
            "<column-name-2>": {}, .....,
          }
    """
    f = open(spec_path, 'r')
    spec_dict = json.load(f)
    f.close()

    column_map = {}
    counter_dict = {}
    filename = csv_file_path

    if 'data_with_overlays' in filename:
        df = pd.read_csv(filename, header=header_row, low_memory=False)
        year = filename.split(f'ACSST5Y')[1][:4]
        column_map[year] = generate_stat_var_map(spec_dict, df.columns.tolist(),
                                                 delimiter)

    ## save the column_map
    if write_output:
        f = open(f'{output_dir_path}/column_map.json', 'w')
        json.dump(column_map, f, indent=4)
        f.close()
    return column_map


def process_input_directory(input_path: str,
                            spec_path: str,
                            write_output: bool = True,
                            output_dir_path: str = './',
                            delimiter: str = '!!',
                            header_row: int = 1,
                            replace_inplace: bool = False) -> dict:
    """
    Given a directory of input files, the function builds a column map for each year
  
    Args:
        input_path: input zip file with data files in csv format, file naming expected to be consistent with data.census.gov
        spec_path: File path where the JSON specification to be used for generating the column map is present
        write_output: Boolean to allow saving the generated column map to an out_dir_path. (default = False)
        output_dir_path: File path to the directory where column map is to be saved (default=./)
        delimiter: specify the string delimiter used in the column names. (default=!!, for subject tables)
        header: specify the index of the row where the column names are found in the csv files (default=1, for subject tables)
        replace_inplace: Boolean flag to allow overwritng pvs with values in inferredSpec or dependent PVs. Disable with `Fa
        lse` by default

      Returns:
        A dictionary mapping each year with the corresponding column_map from generate_stat_var_map()
        Example:
          "2016": {
            "Total Civilian population": {
              "populationType": "Person",
              "statType": "measuredValue",
              "measuredProperty": "Count Person"
              "armedForceStatus": "Civilian"
            },
            "<column-name-2>": {}, .....,
          }
    """
    f = open(spec_path, 'r')
    spec_dict = json.load(f)
    f.close()

    column_map = {}
    counter_dict = {}
    for filename in sorted(os.listdir(input_path)):
        if 'data_with_overlays' in filename:
            df = pd.read_csv(filename, header=header_row, low_memory=False)
            year = filename.split(f'ACSST5Y')[1][:4]
            column_map[year] = generate_stat_var_map(spec_dict,
                                                     df.columns.tolist(),
                                                     delimiter, replace_inplace)

    ## save the column_map
    if write_output:
        f = open(f'{output_dir_path}/column_map.json', 'w')
        json.dump(column_map, f, indent=4)
        f.close()
    return column_map


def process_zip_file(zip_file_path: str,
                     spec_path: str,
                     write_output: bool = True,
                     output_dir_path: str = './',
                     delimiter: str = '!!',
                     header_row: int = 1,
                     replace_inplace: bool = False) -> dict:
    """Given a zip file of datasets in csv format, the function builds a column map for each year
      Args:
        zip_file_path: input zip file with data files in csv format, file naming expected to be consistent with data.census.gov
        spec_path: File path where the JSON specification to be used for generating the column map is present
        write_output: Boolean to allow saving the generated column map to an out_dir_path. (default = False)
        output_dir_path: File path to the directory where column map is to be saved (default=./)
        delimiter: specify the string delimiter used in the column names. (default=!!, for subject tables)
        header: specify the index of the row where the column names are found in the csv files (default=1, for subject tables)
        replace_inplace: Boolean flag to allow overwritng pvs with values in inferredSpec or dependent PVs. Disable with `Fa
        lse` by default

      Returns:
        A dictionary mapping each year with the corresponding column_map from generate_stat_var_map()
        Example:
          "2016": {
            "Total Civilian population": {
              "populationType": "Person",
              "statType": "measuredValue",
              "measuredProperty": "Count Person"
              "armedForceStatus": "Civilian"
            },
            "<column-name-2>": {}, .....,
          }
    """
    f = open(spec_path, 'r')
    spec_dict = json.load(f)
    f.close()

    column_map = {}
    counter_dict = {}
    zf = ZipFile(zip_file_path)
    for filename in sorted(zf.namelist()):
        if 'data_with_overlays' in filename:
            df = pd.read_csv(zf.open(filename, 'r'),
                             header=header_row,
                             low_memory=False)
            year = filename.split(f'ACSST5Y')[1][:4]
            column_map[year] = generate_stat_var_map(spec_dict,
                                                     df.columns.tolist(),
                                                     delimiter, replace_inplace)

    ## save the column_map
    if write_output:
        f = open(f'{output_dir_path}/column_map.json', 'w')
        json.dump(column_map, f, indent=4)
        f.close()
    return column_map


def generate_stat_var_map(spec_dict: dict,
                          column_list: list[str],
                          delimiter: str = '!!',
                          replace_inplace: bool = False) -> dict:
    """
    Wrapper function for generateColMapBase class to generate column map.

    Args:
        specdict: A dictionary containing specifications for the different properties of the statistical variable.
        columnList: A list of column names for which the column map needs to be generated. This is typically the column header in the dataset.
        replace_inplace: Boolean flag to allow overwritng pvs with values in inferredSpec or dependent PVs. Disable with `Fa
        lse` by default

    Returns:
        A dictionary mapping each column to their respective stat_var node definitions.
        Example: {
          "Total Civilian population": {
            "populationType": "Person",
            "statType": "measuredValue",
            "measuredProperty": "Count Person"
            "armedForceStatus": "Civilian"
          },
          "<column-name-2>": {}, .....,
        }
    """
    col_map_obj = GenerateColMapBase(spec_dict=spec_dict,
                                     column_list=column_list,
                                     delimiter=delimiter,
                                     replace_inplace=replace_inplace)
    return col_map_obj._generate_stat_vars_from_spec()


class GenerateColMapBase:
    """
    module to generate a column map given a list of columns of the dataset and a JSON Spec

      Attributes:
        specdict: A dictionary containing specifications for the different properties of the statistical variable.
        columnList: A list of column names for which the column map needs to be generated. This is typically the column header in the dataset.
        delimiter: The delimiting string that is used for tokenising the column name
        replace_inplace: Boolean flag to allow overwritng pvs with values in inferredSpec or dependent PVs. Disable with `False` by default
    """

    def __init__(self,
                 spec_dict: dict = {},
                 column_list: list = [],
                 delimiter: str = '!!',
                 replace_inplace: bool = False):
        """module init"""
        self.features = spec_dict
        self.column_list = column_list
        self.column_map = {}
        self.delimiter = delimiter
        self.replace_inplace = replace_inplace
        # TODO: Add a dictionary of counters with summary stats of number of
        # columns, number of statvars generated, statvars of differnt population
        # types, errors or warnings,
        #
        # fill missing keys in JSON spec with empty values
        for key in _JSON_KEYS:
            if key not in self.features:
                if key == 'ignoreColumns' or key == 'universePVs':
                    self.features[key] = []
                else:
                    self.features[key] = {}

    def _find_and_replace_column_names(self, column: str):
        """
        if spec has find_and_replace defined, this function updates column names
        """
        if 'find_and_replace' in self.features['preprocess']:
            find_and_replace_dict = self.features['preprocess'][
                'find_and_replace']
            # replace entire column name
            if column in find_and_replace_dict:
                return find_and_replace_dict[column]
            # replace a token in the column name
            else:
                part_list = column.split(self.delimiter)
                for key, val in find_and_replace_dict.items():
                    # check if one or more token is a subset of the column
                    if set(key.split(self.delimiter)).issubset(set(part_list)):
                        # we find the elements that contains the tokens to replace
                        # and update the part_list (tokenized column name) with the
                        # replacement token
                        for change in key.split(self.delimiter):
                            idx = part_list.index(change)
                            part_list[idx] = val
                        return self.delimiter.join(part_list)
        return column

    def _generate_stat_vars_from_spec(self):
        """generates stat_var nodes for each column in column list and
        returns a dictionary of columns with their respective stat_var nodes

            Example output: {
          "Total Civilian population": {
            "populationType": "Person",
            "statType": "measuredValue",
            "measuredProperty": "Count Person"
            "armedForceStatus": "Civilian"
          },
          "<column-name-2>": {}, .....
        }"""
        # for each column generate the definition of their respective statistical variable node
        for col in self.column_list:
            ignore_token_flag = False
            # if ignoreColumn token is a single token in the column name or the
            # entire column name, set ignore_token_flag
            if col in self.features['ignoreColumns'] or len(
                    set(self.features['ignoreColumns']) &
                    set(col.split(self.delimiter))) > 0:
                ignore_token_flag = True
            # set ignore_token_flag when multiple tokens of a column name
            # appears not in order
            if not ignore_token_flag:
                for token in self.features['ignoreColumns']:
                    if set(token.split(self.delimiter)).issubset(
                            set(col.split(self.delimiter))):
                        ignore_token_flag = True

            # if no tokens of the columns are in ignoreColumns of the spec
            if not ignore_token_flag:
                renamed_col = self._find_and_replace_column_names(col)
                # TODO: Should we generate an error _column_to_statvar() returns an empty statvar?
                self.column_map[col] = self._column_to_statvar(renamed_col)

        # TODO: Before returning the column map, call self._isvalid_column_map()
        # where we check of the same statvar is generated for more than one column?
        # Should that be considered an error for subject tables?
        return self.column_map

    def _keep_only_specializations(self, part_list: list):
        """
      While generating the stat-var node for the column Estimate!!Total Uninsured!!Total civilian noninstitutionalized population!!AGE!!Under 19 years!!Under 6 years will rename the column to keep only the specialization, which will mean the stat-var node generated will be for the column Estimate!!Total Uninsured!!Total civilian noninstitutionalized population!!AGE!!Under 6 years.

      There can also be a case where the specialization appears with more than one base class. For instance "Under 6 years" occurs with both "Under 18 years" and "Under 19 years". In this case, the base classes are comma-space separated (since that makes the JSON more humnan-readable)
      """
        for specialization, base_classes in self.features[
                'enumSpecializations'].items():
            for base in base_class.split(", "):
                part_list.remove(
                    base)  #removes the base class from the column tokens
        return part_list

    def _column_to_statvar(self, column: str):
        """generates a dictionary statistical variable with all properties specified in the JSON spec for a single column"""
        measurement_assigned = False
        stat_var = {}
        # part_list contains a list of tokens of the column name after splitting the
        # column name based on the '!!' delimiter
        part_list = column.split(self.delimiter)

        # check if the column contains tokens bath the base and specialization
        # of a particular enum. This check uses the enumSpecialization section
        # of the spec.
        part_list = self._keep_only_specializations(part_list)

        ## set the measurement for special cases: Median, Mean, etc.
        ## Pass 1: Check if the entire column is present in spec
        if not measurement_assigned and column in self.features['measurement']:
            stat_var.update(self.features['measurement'][column])
            measurement_assigned = True

        ## Pass 2: Check if a token of the column is present in spec
        for part in part_list:
            # set the base for special cases like median, etc.
            if not measurement_assigned and part in self.features['measurement']:
                stat_var.update(self.features['measurement'][part])
                measurement_assigned = True

        # set the default statVar definition
        if not measurement_assigned and '_DEFAULT' in self.features[
                'measurement']:
            stat_var.update(self.features['measurement']['_DEFAULT'])

        # set the populationType attribute
        if 'populationType' not in stat_var:
            stat_var['populationType'] = self._get_population_type(part_list)

        # TODO: To check if there are edge-cases with values not being full columns
        # associate pvs to stat_var
        for part in part_list:
            ##  p = property and k = dictionary of substrings in column that points to a propertyValue
            for p, k in self.features['pvs'].items():
                ## check if the current key of dict matches with any substring from the tokens of a column name
                for c, v in k.items():
                    # check if column substring matches with a column token
                    # the check is done by ignoring the case
                    if part.lower() == c.lower():
                        if p in stat_var:
                            logger.warning(
                                f"For column: {column} | Property {p} has an existing value {stat_var[p]} which is modified to value {p}"
                            )
                        stat_var[p] = v

        ## add Universe PVs based on the populationType of StatVar
        # replace_inplace is a boolean to flag if existing pvs get overwritten
        # with incoming values from the spec. By default, this is set to False,
        # as in no overwriting of existing pvs.
        replace_inplace = self.replace_inplace
        dependent_properties = None
        for elem in self.features['universePVs']:
            if stat_var['populationType'] == elem['populationType']:
                # check if all constraints of this populationType is in stat_var
                if (set(elem['constraintProperties']).issubset(
                        set(list(stat_var.keys())))):
                    try:
                        ## if the dependentPVs are not in statVar add them if replace_inplace is True
                        if replace_inplace and set(
                                list(elem['dependentPVs'].keys())).issubset(
                                    set(list(stat_var.keys()))):
                            stat_var.update(elem['dependentPVs'])

                        ## add the keys of dependentPVs to dependent_properties
                        dependent_properties = list(elem['dependentPVs'].keys())
                    except KeyError:
                        continue  #when dependentPVs are not specified in spec, skip
                # if constraintProperties is empty, then add the defaultPVs to the
                # stat_var node
                if len(elem['constraintProperties']) == 0:
                    stat_var.update(elem['dependentPVs'])

        # add inferred properties if applicable
        # overwritting pvs depends on replace_inplace value. Default behavior is
        # to disable overwritten
        for p in list(stat_var):
            if p in self.features['inferredSpec']:
                if replace_inplace and set(
                        list(self.features['inferredSpec'][p])).issubset(
                            set(list(stat_var.keys()))):
                    stat_var.update(self.features['inferredSpec'][p])

        # generating dcid using the utils/statvar_dcid_generator.py
        stat_var_dcid = get_statvar_dcid(stat_var,
                                         ignore_props=dependent_properties)

        ## overwrite stat_var_dcids from the spec (for existing dcids)
        if stat_var_dcid in self.features['overwrite_dcids']:
            stat_var_dcid = self.features['overwrite_dcids'][stat_var_dcid]
        stat_var['Node'] = 'dcid:' + stat_var_dcid

        #Move the dcid to begining of the dict, uses OrderedDict
        try:
            stat_var = OrderedDict(stat_var)
            stat_var.move_to_end('Node', last=False)
            stat_var = json.loads(json.dumps(stat_var))
        except:
            logger.warning(
                f"The 'Node' is not found for that statvar node generated with dcid={stat_var_dcid}"
            )
        #prefix the values if they are not QuantityRanges with dcs:
        stat_var = self._format_stat_var_node(stat_var)

        #check if the stat_var dict has the mandatory properties
        if self._isvalid_stat_var(stat_var):
            return stat_var
        else:
            try:
                raise ValueError
            except ValueError:
                logger.critical(
                    f'One or more mandatory properties of the stat_var is missing. \n Dump of the stat_var:: {stat_var}'
                )

    def _isvalid_stat_var(self, stat_var: dict):
        """method validates if stat_var has mandatory properties, specified in _MANDATORY_PROPS"""
        if set(_MANDATORY_PROPS).issubset(set(list(stat_var.keys()))):
            return True
        else:
            return False

    def _format_stat_var_node(self, stat_var: dict):
        """utility to format the stat_var dict values to ensure they conform to the specifications of StatVar"""
        # add typeOf property to the node if undefined
        if 'typeOf' not in stat_var:
            stat_var['typeOf'] = 'dcs:StatisticalVariable'

        # check if all values that are not quantity ranges are prefixed
        for k, v in stat_var.items():
            # if value is not a bracketed quantity range
            if v[0] == '[' and v[-1] == ']':
                continue
            # do not prefix units or scalingFactors
            if k in ['unit', 'units', 'scalingFactor']:
                continue
            # if value is not prefixed apriori with dcs: or schema:
            elif 'schema:' in v or 'dcs:' in v or 'dcid:' in v:
                continue
            # add dcid: prefix to the value
            else:
                stat_var[k] = 'dcid:' + v
        return stat_var

    def _isvalid_column_map(self):
        """check the generated column_map against a set of validation rules"""
        # TODO: defintion of different rules which are used to validate a generated column map
        ## Rule ideas:
        ## 1. condition to handle case when 2 columns have same SV DCID
        ## 2. condition to handle case when 2 SV nodes have same SV DCID
        ## 3. condition to check if column map excludes tokens that are to be skipped per enumSpecializations
        ## 4. check if column map matches with the spec
        pass

    def _get_population_type(self, part_list: list):
        """From tokenized column name, find the most relevant populationType from the JSON Spec """
        # if 'populationType' in self.features:
        for k, v in self.features['populationType'].items():
            for part in part_list:
                if k in part:
                    return v
        # If populationType not in column name, take the default from the spec
        try:
            return self.features['populationType']['_DEFAULT']
        except KeyError:
            ## The default populationType if populationType is not specified in the spec, is Person.
            ## Since most of the ACS Subject Tables describe different qualitative and quantitative characteristics of individuals
            return 'Person'
