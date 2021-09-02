"""Module to generate a column map to their corresponding statistical variable defintions."""

import os
import json

import pandas as pd

#TODO:Remove this import and make it from ~/data/utils/ directory when it is available
os.system(
    'curl https://raw.githubusercontent.com/Abilityguy/data/dcid_gen/util/statvar_dcid_generator.py -LO statvar_dcid_generator.py'
)
from statvar_dcid_generator import get_stat_var_dcid



def generate(specDict: dict, columnList: list) -> dict:
    """Wrapper function for generateColMapBase class to generate column map.

  Args:
    specDict:
      A dictionary containing specifications for the different properties of the statistical variable.
    columnList:
      A list of column names for which the column map needs to be generated. This is typically the column header in the dataset.

  Returns:
    A dict mapping each column to their respective stat_var node definitions.
  """
    col_map_obj = GenerateColMapBase(specDict=specDict, columnList=columnList)
    return col_map_obj._generate_stat_vars_from_spec()


class GenerateColMapBase:
    """module to generate a column map given a list of columns of the dataset and a JSON Spec

  Attributes:
    specDict: A dictionary containing specifications for the different properties of the statistical variable.
    columnList: A list of column names for which the column map needs to be generated. This is typically the column header in the dataset.
  """

    def __init__(self, specDict=None, columnList=None):
        """module init """
        self.features = specDict
        self.column_list = columnList
        self.column_map = {}

    def _generate_stat_vars_from_spec(self):
        """generates stat_var nodes for each column in column list and returns a dictionary of columns with their respective stat_var nodes"""
        # for each column generate the definition of their respective statistical variable node
        for col in self.column_list:
            if 'ignoreColumns' in self.features and col not in self.features[
                    'ignoreColumns']:
                self.column_map[col] = self._column_to_statvar(col)
        #TODO: Enable validating the generate columnMap: _valid_col_map():
        return self.column_map

    def _column_to_statvar(self, column):
        """generates a dictionary statistical variable with all properties specified in the JSON spec for a single column"""
        measurement_assigned = False
        stat_var = {}
        # part_list contains a list of tokens of the column name after splitting the
        # column name based on the '!!' delimiter
        part_list = column.split('!!')

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
            if not measurement_assigned and 'measurement' in self.features.keys(
            ):
                if part in self.features['measurement'].keys():
                    stat_var.update(self.features['measurement'][part])
                    measurement_assigned = True

        # set the default statVar definition
        if not measurement_assigned and 'measurement' in self.features.keys(
        ) and '_DEFAULT' in self.features['measurement'].keys():
            stat_var.update(self.features['measurement']['_DEFAULT'])

        # set the populationType attribute
        stat_var['populationType'] = self._get_population_type(part_list)

        # associate pvs to stat_var
        if val_prop_col not in self.features['measurement'].keys():
            if 'pvs' in self.features.keys():
                #p = property, k = dictionary of substrings in column that points to a propertyValue
                for p, k in self.features['pvs'].items():
                    for c, v in k.items():
                        ## check if the current key of dict matches with any substring from the tokens of a column name
                        for part in part_list:
                            if c in part:
                                stat_var[p] = v
                                # add inferred properties from property 'p' to the stat_var
                                if 'inferredSpec' in self.features.keys(
                                ) and p in self.features['inferredSpec'].keys():
                                    stat_var.update(
                                        self.features['inferredSpec'][p])

        #TODO: If quantityRanges occurs as values in multiple properties, find the property that relates to the column
        #TODO: Add units and scalingFactor

        # if the column is Margin of Error, update statType key
        if 'Margin of Error' in part_list:
            stat_var['statType'] = 'marginOfError'

        ## add Universe PVs based on the populationType of StatVar
        dependent_properties = None
        if 'universePVs' in self.features.keys():
            for elem in self.features['universePVs']:
                if stat_var['populationType'] == elem['populationType']:
                    # check if all constraints of this populationType is in stat_var
                    if (set(elem['constraintProperties']).issubset(
                            set(list(stat_var.keys())))):
                        dependent_properties = list(elem['dependentPVs'].keys())

        # generating dcid using the utils/statvar_dcid_generator.py
        stat_var['dcid'] = get_stat_var_dcid(
            stat_var, ignore_props=dependent_properties)
        return stat_var

    def _get_population_type(self, part_list):
        """From tokenized column name, find the most relevant populationType from the JSON Spec """
        if 'populationType' in self.features.keys():
            for part in part_list:
                for k, v in self.features['populationType'].items():
                    if k in part:
                        return self.features['populationType'][k]
            # If populationType not in column name, take the default from the spec
            return self.features['populationType']['_DEFAULT']
        else:
            ## The default populationType if populationType is not specified in the spec, is Person.
            ## Since most of the ACS Subject Tables describe different qualitative and quantitative characteristics of individuals
            return 'Person'
