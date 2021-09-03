"""Module to generate a column map to their corresponding statistical variable defintions."""
import os
import sys
import logging
import json
import re

import pandas as pd

#TODO:Remove this import and make it from ~/data/utils/ directory when it is available
os.system(
    'curl https://raw.githubusercontent.com/Abilityguy/data/dcid_gen/util/statvar_dcid_generator.py -LO statvar_dcid_generator.py'
)
from statvar_dcid_generator import get_stat_var_dcid

# intitalize the logger
logging.basicConfig(
    filename='column_map_generatetion_task.log',
    format="{asctime} {processName:<12} {message} ({filename}:{lineno})",
    style="{",
    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# regex for the definition of QuantityRanges
# From: utils/statvar_dcid_generator.py
_QUANTITY_RANGE_REGEX = (r"\[(?P<lower_limit>-|-?\d+(\.\d+)?) "
                         r"(?P<upper_limit>-|-?\d+(\.\d+)?) "
                         r"(?P<quantity>[A-Za-z]+)\]")

# list of properties that every statistical variable should contain
_MANDATORY_PROPS = ['measuredProperty', 'populationType', 'statType']

# common properties and their associated populationTypes
# TODO: Establish if this map generalizes across the different subject tables
_DISAMBIGUATING_POP_TYPE = {'income': 'Household', 'earnings': 'Person'}

# list of keys expected in the JSON spec, if they are not defined, we set as an
# empty dictionary
_JSON_KEYS = [
    'populationType', 'measurement', 'pvs', 'inferredSpec',
    'enumSpecializations', 'pvs', 'universePVs'
]


def generate_stat_var_map(spec_dict: dict, column_list: list) -> dict:
    """Wrapper function for generateColMapBase class to generate column map.

  Args:
    specDict:
      A dictionary containing specifications for the different properties of the statistical variable.
    columnList:
      A list of column names for which the column map needs to be generated. This is typically the column header in the dataset.

  Returns:
    A dict mapping each column to their respective stat_var node definitions.
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
    col_map_obj = GenerateColMapBase(spec_dict=spec_dict,
                                     column_list=column_list)
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

        # fill missing keys in JSON spec with empty values
        for key in self.features:
            try:
                self.features[key]
            except KeyError:
                self.features[key] = {}

    def _generate_stat_vars_from_spec(self):
        """generates stat_var nodes for each column in column list and returns a dictionary of columns with their respective stat_var nodes
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
            if 'ignoreColumns' in self.features and col not in self.features[
                    'ignoreColumns']:
                try:
                    self.column_map[col] = self._column_to_statvar(col)
                except Exception as e:
                    exec_type, exec_obj, exec_tb = sys.exc_info()
                    logger.error(
                        f"Exeception: {exec_type} occured in generate_col_map.py at line {exec_tb.tb_lineno}"
                    )
                    continue

        #TODO: Enable validating the generate columnMap. Dependent implementation _isvalid_column_map
        return self.column_map

    def _column_to_statvar(self, column):
        """generates a dictionary statistical variable with all properties specified in the JSON spec for a single column"""
        measurement_assigned = False
        stat_var = {}
        # part_list contains a list of tokens of the column name after splitting the
        # column name based on the '!!' delimiter
        part_list = column.split(self.delimiter)

        # part_list[-1], the last element of part_list describes the property value.
        # This element points to the 'v' in 'pv' -> and we map it to the
        # corresponding property 'p'
        # Eg:
        # 'Estimate!!Total!!Total civilian noninstitutionalized
        # population!!SEX!!Male' is the name of the column and the value you we want
        # is the gender 'Male'. This pattern repeats for all columns
        # To verify this assumption for specific census tables, please check the
        # table shells at: https://www2.census.gov/programs-surveys/acs/tech_docs/table_shells/2019/
        val_prop_col = part_list[-1]

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
        #p = property, k = dictionary of substrings in column that points to a propertyValue
        for p, k in self.features['pvs'].items():
            for c, v in k.items():
                ## check if the current key of dict matches with any substring from the tokens of a column name
                for part in part_list:
                    # check if column substring matches with a column token
                    # the check is done by ignoring the case
                    if c.lower() in part.lower():
                        if p in stat_var:
                            logger.warning(
                                f"For column: {column} | Property {p} has an existing value {stat_var[p]} which is modified to value {p}"
                            )
                        stat_var[p] = v
        # If quantityRanges occurs as values in multiple properties, we pick the related property based on
        # populationType using _DISAMBIGUATING_POP_TYPE for pvs. Example: In
        # subject table S2702,  income (for Households) and earnings(for Person)
        # appears based on the values and needs to be disambiguated.
        # TODO: Fix this logic for Margin Of Error where this part did not work
        for k in stat_var:
            if k in _DISAMBIGUATING_POP_TYPE:
                if stat_var['populationType'] != _DISAMBIGUATING_POP_TYPE[k]:
                    del stat_var[k]
                    break

        ## add Universe PVs based on the populationType of StatVar
        dependent_properties = None
        for elem in self.features['universePVs']:
            if stat_var['populationType'] == elem['populationType']:
                # check if all constraints of this populationType is in stat_var
                if (set(elem['constraintProperties']).issubset(
                        set(list(stat_var.keys())))):
                    dependent_properties = list(elem['dependentPVs'].keys())
                # if dependent PVs are not present, add them to stat_var
                else:
                    #TODO: Can be improved?
                    stat_var.update(elem['dependentPVs'])

        # add inferred propoerties if applicable
        for p in stat_var:
            if stat_var[p] in self.features['inferredSpec']:
                stat_var.update(self.features['inferredSpec'][p])

        # generating dcid using the utils/statvar_dcid_generator.py
        stat_var['Node'] = 'dcid:' + get_stat_var_dcid(
            stat_var, ignore_props=dependent_properties)

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
                    f'One or more mandatory properties of the stat_var is missing. \n Dump of the stat_var:: {stat_var}'
                )

    def _keep_only_enum_specializations(self):
        """removes the stat var nodes for columns that are defined as generalizations of a group.
      Example: if the enumSpecicalization is defined as
      {
        "Under 6 years": "Under 19 years",
        "6 to 18 years": "Under 19 years",
      }
      It means that "Under 6 years" and "6 to 18 years" are specializations of Under 19 years.
      And hence we do not add a stat var for "Under 19 Years". 
      If the enumSpecialisation field is empty this will not be done.
      """
        # iterate over the column_names, since the column_names are descriptive in
        # the census tables
        # TODO: Improve this implementation
        for column_name in self.column_map:
            for k, v in self.features['enumSpecializations']:
                if k in column_name and v in column_name:
                    del self.column_map[column_name]
                    break

    def _isvalid_stat_var(self, stat_var):
        """method validates if stat_var has mandatory properties, specified in _MANDATORY_PROPS"""
        if set(_MANDATORY_PROPS).issubset(set(list(stat_var.keys()))):
            return True
        else:
            return False

    def _format_stat_var_node(self, stat_var):
        """utility to format the stat_var dict values to ensure they conform to the specifications of StatVar"""
        # add typeOf property to the node if undefined
        if 'typeOf' not in stat_var:
            stat_var['typeOf'] = 'dcs:StatisticalVariable'

        # check if all values that are not quantity ranges are prefixed
        for k, v in stat_var.items():
            # if value is not a bracketed quantity range
            if re.match(_QUANTITY_RANGE_REGEX, v):
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
        ##TODO[sharadshriram]: Needs to be implemented
        ## same stat_var dcid occurs for multiple columns -- #TODO
        pass

    def _get_population_type(self, part_list):
        """From tokenized column name, find the most relevant populationType from the JSON Spec """
        # if 'populationType' in self.features:
        try:
            for part in part_list:
                for k, v in self.features['populationType'].items():
                    if k in part:
                        return self.features['populationType'][k]
        # If populationType not in column name, take the default from the spec
        except:
            return self.features['populationType']['_DEFAULT']
        else:
            ## The default populationType if populationType is not specified in the spec, is Person.
            ## Since most of the ACS Subject Tables describe different qualitative and quantitative characteristics of individuals
            return 'Person'
