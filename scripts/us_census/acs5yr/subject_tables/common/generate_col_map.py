"""
Module to generate StatVar nodes from column maps
"""
import os
import io
import sys
import logging
import json
import re
import csv
from zipfile import ZipFile
from collections import OrderedDict

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(
    _SCRIPT_PATH, '../../../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_stat_var_dcid

# intitalize the logger
logging.basicConfig(
    filename='make_column_map.log',
    format="{asctime} {processName:<12} {message} ({filename}:{lineno})",
    style="{",
    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# list of properties that every statistical variable should contain
_MANDATORY_PROPS = ['measuredProperty', 'populationType', 'statType']

# list of keys expected in the JSON spec, if they are not defined, we set as an
# empty dictionary
_JSON_KEYS = [
    'populationType', 'measurement', 'pvs', 'inferredSpec',
    'enumSpecializations', 'pvs', 'universePVs', 'ignoreColumns',
    'overwrite_dcids', 'preprocess', 'find_and_replace'
]


def process_zip_file(zip_file_path,
                     spec_path,
                     write_output=True,
                     output_dir_path='./',
                     delimiter='!!',
                     header_row=1):
    """Given a zip file of datasets in csv format, the function builds a column map for each year
  Args:
    zip_file_path: input zip file with data files in csv format, file naming expected to be consistent with data.census.gov
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

    with ZipFile(zip_file_path) as zf:
        for filename in zf.namelist():
            if 'data_with_overlays' in filename:
                with io.TextIOWrapper(zf.open(filename, 'r')) as csv_file:
                    csv_reader = csv.reader(csv_file)
                    for index, line in enumerate(csv_reader):
                        if index == header_row:
                            year = filename.split(f'ACSST5Y')[1][:4]
                            column_map[year] = generate_stat_var_map(
                                spec_dict, line, delimiter)
                            break
                        continue
    ## save the column_map
    if write_output:
        f = open(f'{output_dir_path}/column_map.json', 'w')
        json.dump(column_map, f, indent=4)
        f.close()
    return column_map


def generate_stat_var_map(spec_dict, column_list, delimiter='!!'):
    """Wrapper function for generateColMapBase class to generate column map.

  Args:
    specDict: A dictionary containing specifications for the different properties of the statistical variable.
    columnList: A list of column names for which the column map needs to be generated. This is typically the column header in the dataset.

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
                                     delimiter=delimiter)
    return col_map_obj._generate_stat_vars_from_spec()


class GenerateColMapBase:
    """module to generate a column map given a list of columns of the dataset and a JSON Spec

  Attributes:
    specDict: A dictionary containing specifications for the different properties of the statistical variable.
    columnList: A list of column names for which the column map needs to be generated. This is typically the column header in the dataset.
    delimiter: The delimiting string that is used for tokenising the column name
  """

    def __init__(self, spec_dict={}, column_list=[], delimiter='!!'):
        """module init"""
        self.features = spec_dict
        self.column_list = column_list
        self.column_map = {}
        self.delimiter = delimiter
        #TODO: Add a dictionary of counters withsummary stats of number of
        # columns, number of statvars generated, statvars of differnt population
        # types, errors or warnings,

        # fill missing keys in JSON spec with empty values
        for key in _JSON_KEYS:
            if key not in self.features:
                if key == 'ignoreColumns':
                    self.features[key] = []
                else:
                    self.features[key] = {}
        # if columns names need to be normalized
        self.column_list = self._find_and_replace_column_names(self.column_list)

    def _find_and_replace_column_names(self, df_column_list):
        """
        if spec has find_and_replace defined, this function updates column name
        """
        if 'preprocess' in self.features:
            if 'find_and_replace' in self.features['preprocess']:
                for col_idx, column in enumerate(df_column_list):
                    part_list = column.split(self.delimiter)
                    for idx, part in enumerate(part_list):
                        if part in self.features['preprocess'][
                                'find_and_replace']:
                            part_list[idx] = self.features['preprocess'][
                                'find_and_replace'][part]
                            df_column_list[col_idx] = self.delimiter.join(
                                part_list)
        return df_column_list

    def _generate_stat_vars_from_spec(self):
        """generates stat_var nodes for each column in column list and returns
        a dictionary of columns with their respective stat_var nodes
            Example output: {
          "Total Civilian population": {
            "populationType": "Person",
            "statType": "measuredValue",
            "measuredProperty": "Count Person"
            "armedForceStatus": "Civilian"
          },
          "<column-name-2>": {}, .....
        }
        """
        # for each column generate the definition of their respective
        # statistical variable node
        for col in self.column_list:
            ignore_token_count = 0
            for part in col.split(self.delimiter):
                for token in self.features['ignoreColumns']:
                    if part == token:
                        ignore_token_count = 1
                    if token == col:
                        ignore_token_count = 1

            # if no tokens of the columns are in ignoreColumns of the spec
            if ignore_token_count == 0:
                self.column_map[col] = self._column_to_statvar(col)
                try:
                    self.column_map[col] = self._column_to_statvar(col)
                except Exception as e:
                    exec_type, exec_obj, exec_tb = sys.exc_info()
                    logger.error(
                        f"""Exeception: {exec_type} occured in
                        generate_col_map.py at line {exec_tb.tb_lineno}"""
                    )
            continue
        # Drop stat_vars based on enumSpecializations mentioned in spec
        self._keep_only_enum_specializations()
        #TODO: Enable validating the generate columnMap.
        # Dependent implementation _isvalid_column_map
        return self.column_map

    def _column_to_statvar(self, column):
        """
        generates a dictionary statistical variable with all properties
        specified in the JSON spec for a single column"""
        measurement_assigned = False
        stat_var = {}
        # part_list contains a list of tokens of the column name after splitting
        # the column name based on the '!!' delimiter
        part_list = column.split(self.delimiter)

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

        # associate pvs to stat_var
        for part in part_list:
            ##  p = property and k = dictionary of column tokens mapped to a propertyValue
            for p, k in self.features['pvs'].items():
                ## check if the current key of dict matches with tokens of a column name
                for c, v in k.items():
                    # check if column substring matches with a column token
                    # the check is done by ignoring the case
                    if part.lower() == c.lower():
                        if p in stat_var:
                            logger.warning(
                                f"""For column: {column} | Property {p} has an
                                existing value {stat_var[p]} which is modified
                                to value {p}"""
                            )
                        stat_var[p] = v

        ## add Universe PVs based on the populationType of StatVar
        dependent_properties = None
        for elem in self.features['universePVs']:
            if stat_var['populationType'] == elem['populationType']:
                # check if all constraints of this populationType is in stat_var
                if (set(elem['constraintProperties']).issubset(
                        set(list(stat_var.keys())))):
                    try:
                        ## if the dependentPVs are not in statVar add them
                        if not set(list(elem['dependentPVs'].keys())).issubset(
                                set(list(stat_var.keys()))):
                            stat_var.update(elem['dependentPVs'])
                        ## add the depedent keys to a list
                        dependent_properties = list(elem['dependentPVs'].keys())
                    except KeyError:
                        # Skip, when dependentPVs are not specified in spec
                        continue
                # if constraintProperties is empty, then add the defaultPVs to
                # the stat_var node
                if len(elem['constraintProperties']) == 0:
                    stat_var.update(elem['dependentPVs'])

        # add inferred propoerties if applicable
        for p in list(stat_var):
            if p in self.features['inferredSpec']:
                stat_var.update(self.features['inferredSpec'][p])

        # generating dcid using the utils/statvar_dcid_generator.py
        stat_var_dcid = get_stat_var_dcid(stat_var,
                                          ignore_props=dependent_properties)

        ## overwrite stat_var_dcids from the spec (for existing dcids)
        if stat_var_dcid in self.features['overwrite_dcids']:
            stat_var_dcid = self.features['overwrite_dcids'][stat_var_dcid]
        stat_var['Node'] = 'dcid:' + stat_var_dcid

        #Move the dcid to begining of the dict, uses OrderedDict
        stat_var = OrderedDict(stat_var)
        stat_var.move_to_end('Node', last=False)
        stat_var = json.loads(json.dumps(stat_var))

        #prefix the values if they are not QuantityRanges with dcs:
        stat_var = self._format_stat_var_node(stat_var)

        #check if the stat_var dict has the mandatory properties
        if self._isvalid_stat_var(stat_var):
            return stat_var
        else:
            try:
                raise ValueError
            except ValueError:
                logger.error(
                    f"""One or more mandatory properties of the stat_var is missing.
                    \nDump of the stat_var:: {stat_var}"""
                )

    def _keep_only_enum_specializations(self):
        """
      removes the stat var nodes for columns that are defined as generalizations.

      Example: if the enumSpecicalization is defined as
      {
        "Under 6 years": "Under 19 years, Under 18 years",
        "6 to 18 years": "Under 19 years",
      }
      It means that "Under 6 years" and "6 to 18 years" are specializations of
      Under 19 years. Hence, we do not add a stat var for "Under 19 Years".
      If the enumSpecialisation field is empty this will not be done.
      """
        column_map = self.column_map.copy()
        for column_name, stat_var in column_map.items():
            part_list = column_name.split(self.delimiter)
            ## The assumption of using the last token of the column as the
            ##specialization holds for ACS Subject tables.
            ## TODO: Check if this assumption hold for non-subject tables
            last_column_token = part_list[-1]
            if last_column_token in self.features['enumSpecializations']:
                base_class = self.features['enumSpecializations'][
                    last_column_token]
                for base in base_class.split(', '):
                    if base in part_list:
                        col_name = self.delimiter.join(part_list[:-1])
                        try:
                            del self.column_map[col_name]
                            logger.info(
                                f"""Removing the base class column: {col_name}
                                from the column map based on enumSpecialization
                                of the spec"""
                            )
                        except KeyError:
                            logger.info(
                                f"""Attempted removal of base class column:
                                {col_name} failed. It might be already removed."""
                            )

    def _isvalid_stat_var(self, stat_var):
        """
        method validates if stat_var has mandatory properties, specified in
        _MANDATORY_PROPS
        """
        if set(_MANDATORY_PROPS).issubset(set(list(stat_var.keys()))):
            return True
        else:
            return False

    def _format_stat_var_node(self, stat_var):
        """
        utility to format the stat_var dict values to ensure they conform to
        the specifications of StatVar
        """
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
        ##TODO: defintion of different rules which are used to validate a generated column map
        ## Rule ideas:
        ## 1. condition to handle case when 2 columns have same SV DCID
        ## 2. condition to handle case when 2 SV nodes have same SV DCID
        ## 3. condition to check if column map excludes tokens that are to be skipped per enumSpecializations
        ## 4. check if column map matches with the spec
        pass

    def _get_population_type(self, part_list):
        """
        From tokenized column name, find the most relevant populationType from
        the JSON Spec
        """
        # if 'populationType' in self.features:
        for k, v in self.features['populationType'].items():
            for part in part_list:
                if k in part:
                    return v
        # If populationType not in column name, take the default from the spec
        try:
            return self.features['populationType']['_DEFAULT']
        except KeyError:
            ## The default populationType if populationType is not specified in
            ## the spec, is Person. Since most of the ACS Subject Tables
            ## describe different qualitative and quantitative characteristics
            ## of individuals
            return 'Person'
