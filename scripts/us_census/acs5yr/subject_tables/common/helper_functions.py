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
Utilities to compile denominator section and related helper functions.
"""

from typing import Any
from absl import app
from absl import flags

from common_util import *

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'denominator_config', None,
    'Path of json file SHORT config for generating denominator section')
flags.DEFINE_string(
    'denominator_long_config', None,
    'Path of json file LONG config for generating denominator section')
flags.DEFINE_string('column_list_path', None,
                    'Path of json file containing list of all columns')
flags.DEFINE_boolean('get_ignore_columns', False,
                     'Path of json file containing list of all columns')


def find_columns_with_token(column_list: list,
                            token: str,
                            delimiter: str = '!!') -> list:
    """Filters out columns that contain the given token

    Args:
      column_list: List of column names to be searched.
      token: Token to be searched within the column name.
      delimiter: delimiter seperating tokens within single column name string.

    Returns:
      List of column names that contain the input token.
  """
    ret_list = []
    for cur_column in column_list:
        if token_in_list_ignore_case(token, cur_column.split(delimiter)):
            ret_list.append(cur_column)
    return list(set((ret_list)))


def replace_token_in_column(cur_column: str,
                            old_token: str,
                            new_token: str,
                            delimiter: str = '!!') -> str:
    return delimiter.join([
        new_token if x == old_token else x for x in cur_column.split(delimiter)
    ])


def replace_first_token_in_column(cur_column: str,
                                  old_token: str,
                                  new_token: str,
                                  delimiter: str = '!!') -> str:
    new_list = []
    temp_flag = True
    for x in cur_column.split(delimiter):
        if x == old_token and temp_flag:
            new_list.append(new_token)
            temp_flag = False
        else:
            new_list.append(x)

    return delimiter.join(new_list)


# replace token
def replace_token_in_column_list(column_list: list,
                                 old_token: str,
                                 new_token: str,
                                 delimiter: str = '!!') -> list:
    ret_list = []
    for cur_column in column_list:
        ret_list.append(
            replace_token_in_column(cur_column, old_token, new_token,
                                    delimiter))
    return ret_list


# combined replace list
def replace_token_list_in_column_list(column_list: list,
                                      old_token: str,
                                      new_token_list: list,
                                      delimiter: str = '!!') -> dict:
    """Replaces a token with an element from list of new tokens individually.
      Outputs a list of new column names with new token for each column name.

    Args:
      column_list: List of column names to replace tokens in.
      old_token: Token to be replaced.
      new_token_list: List of new tokens to be placed. Each token will have a output column name.
      delimiter: delimiter seperating tokens within single column name string.

    Returns:
      Dict object with original column name as key and list of replaced column names as value.
  """
    ret_dict = {}
    for cur_column in column_list:
        ret_dict[cur_column] = []
        for new_token in new_token_list:
            ret_dict[cur_column].append(
                replace_token_in_column(cur_column, old_token, new_token,
                                        delimiter))
    return ret_dict


# find columns sub token
def find_columns_with_token_partial_match(column_list: list,
                                          token_str: str,
                                          delimiter: str = '!!') -> list:
    ret_list = []
    for cur_column in column_list:
        for token in cur_column.split(delimiter):
            if token_str.lower() in token.lower():
                ret_list.append(cur_column)
    return list(set((ret_list)))


def get_columns_by_token_count(column_list: list,
                               delimiter: str = '!!') -> dict:
    ret_dict = {}
    for cur_column in column_list:
        token_list = cur_column.split(delimiter)
        if len(token_list) not in ret_dict:
            ret_dict[len(token_list)] = []
        ret_dict[len(token_list)].append(cur_column)
    return ret_dict


def get_columns_with_same_prefix(columns_by_length: dict,
                                 max_extra_token: int = 1,
                                 delimiter: str = '!!') -> dict:
    ret_dict = {}
    for column_length in columns_by_length:
        for cur_column in columns_by_length[column_length]:
            extra_length = 1
            while extra_length <= max_extra_token:
                if (column_length + extra_length) in columns_by_length:
                    for comapre_column in columns_by_length[column_length +
                                                            extra_length]:
                        if comapre_column.startswith(cur_column):
                            if cur_column not in ret_dict:
                                ret_dict[cur_column] = []
                            ret_dict[cur_column].append(comapre_column)
                extra_length += 1
    return ret_dict


def guess_total_columns_from_zip_file(zip_path: str, ignore_token_list: list,
                                      year_list: list) -> dict:
    """Find columns that might be totals based on their value(> 100).

    Args:
      zip_path: Path of the zip file with data.
      ignore_token_list: Tokens that indicate column needs to be ignored.
      year_list: List of years for which processing needs to be done.
    
    Returns:
      Dict with year as key value and list of column names that could be totals as value.
  """
    zip_path = os.path.expanduser(zip_path)

    ret_dict = {}

    with zipfile.ZipFile(zip_path) as zf:
        for filename in zf.namelist():
            if '_data_' in filename:
                # find year
                year = filename[:filename.index('.')]
                year = year[-4:]
                if year in year_list:
                    with zf.open(filename, 'r') as data_f:
                        csv_reader = csv.reader(
                            io.TextIOWrapper(data_f, 'utf-8'))
                        ret_dict[year] = total_columns_from_csvreader(
                            csv_reader, ignore_token_list)

    return ret_dict


def total_columns_from_csvreader(csv_reader: Any,
                                 ignore_token_list: list) -> list:
    total_columns = []
    for row in csv_reader:
        if csv_reader.line_num == 2:
            column_name_list = row.copy()
        elif csv_reader.line_num == 3:
            for i, val in enumerate(row):
                try:
                    ignore_cell = False
                    for tok in ignore_token_list:
                        if tok.lower() in column_name_list[i].lower():
                            ignore_cell = True
                    if 'Margin of Error' in column_name_list[i]:
                        ignore_cell = True
                    if not ignore_cell:
                        if float(val) > 100:
                            if column_name_list[i] not in total_columns:
                                total_columns.append(column_name_list[i])
                except ValueError:
                    pass
    return total_columns


def yearwise_columns_from_zip_file(zip_path: str,
                                   spec_dict: dict,
                                   year_list: list,
                                   delimiter: str = '!!') -> dict:
    zip_path = os.path.expanduser(zip_path)
    ret_dict = {}

    with zipfile.ZipFile(zip_path) as zf:
        for filename in zf.namelist():
            if '_data_' in filename:
                # find year
                year = filename[:filename.index('.')]
                year = year[-4:]
                if year in year_list:
                    with zf.open(filename, 'r') as data_f:
                        # TODO sort by variable ID to preserve sequence of appearance.
                        # Some older year files have lasst few columns in unsorted order,
                        # leading to wrong prefix association.
                        csv_reader = csv.reader(
                            io.TextIOWrapper(data_f, 'utf-8'))
                        temp_list = columns_from_CSVreader(csv_reader, False)
                        ret_dict[year] = []
                        for cur_column in temp_list:
                            if not column_to_be_ignored(cur_column, spec_dict,
                                                        delimiter):
                                ret_dict[year].append(cur_column)

    return ret_dict


def column_find_prefixed(column_name: str, prefix_list: list) -> str:
    """Filter out columns that are begin with one of the strings from a given prefix list.
      NOTE: Longest prefix would be used in case multiple matches occour.

    Args:
      column_name: Name of the column to be checked.
      prefix_list: List of possible prefix.
    
    Returns:
      The longest matching prefix or None if no match is found.
  """
    matched_prefix = None
    if column_name not in prefix_list:
        for cur_prefix in prefix_list:
            if len(cur_prefix) < len(column_name) and cur_prefix in column_name:
                if matched_prefix:
                    if len(cur_prefix) > len(matched_prefix):
                        matched_prefix = cur_prefix
                else:
                    matched_prefix = cur_prefix

    return matched_prefix


def get_census_column_token_index(census_columns: list,
                                  year_list: list,
                                  yearwise_columns: dict,
                                  delimiter: str = '!!') -> dict:
    """Finds the index of token representing the census UI column name.
      This index is used for adding MOE substring when necessary.

    Args:
      census_columns: List of column names in census UI.
      year_list: List of years for which processing is rerquired.
      yearwise_columns: Dict with list of columns names by year.
      delimiter: delimiter seperating tokens within single column name string.
    
    Returns:
      Dict with year as key value and the index of census UI column name token as value.
  """
    index_dict = {}
    ret_dict = {}
    for year in yearwise_columns:
        if year in year_list:
            index_dict[year] = {}
        for census_col in census_columns:
            if year in year_list:
                index_dict[year][census_col] = {}
                index_dict[year][census_col]['index'] = []

    for year in yearwise_columns:
        if year in year_list:
            # compile list of column token index, traversing each row
            for census_cell in yearwise_columns[year]:
                token_list = census_cell.split(delimiter)
                column_found = False
                for census_col in census_columns:
                    if census_col in token_list:  # or census_col+' MOE' in token_list:
                        column_found = True
                        # find the token index of column name for each year
                        col_i = token_list.index(census_col)
                        if col_i not in index_dict[year][census_col]['index']:
                            index_dict[year][census_col]['index'].append(col_i)
                    # MOE column names
                    if census_col + ' MOE' in token_list:  # or census_col+' MOE' in token_list:
                        column_found = True
                        # find the token index of column name for each year
                        col_i = token_list.index(census_col + ' MOE')
                        if col_i not in index_dict[year][census_col]['index']:
                            index_dict[year][census_col]['index'].append(col_i)
                if not column_found:
                    print('Warning: No column found for', census_cell)

            # find the census column token index for the year
            year_col_i = -1
            for census_col in census_columns:
                # keep the lowest of the found indices, if multiple found
                index_dict[year][census_col]['index'] = sorted(
                    index_dict[year][census_col]['index'])
                if year_col_i == -1:
                    year_col_i = index_dict[year][census_col]['index'][0]
                # check if it is consistent across columns
                if year_col_i != index_dict[year][census_col]['index'][0]:
                    print(
                        'Warning: found potential conflicts for column token index for year',
                        year)

            ret_dict[year] = year_col_i

    ## For debug
    # print(json.dumps(index_dict, indent=2))
    return ret_dict


def get_census_rows_by_column(census_columns: list,
                              year_list: list,
                              yearwise_columns: dict,
                              index_dict: dict,
                              delimiter: str = '!!') -> dict:
    """Organises column names so that census UI rows are associated with their UI columns.

    Args:
      census_columns: List of column names in census UI.
      year_list: List of years for which processing is rerquired.
      yearwise_columns: Dict with list of columns names by year.
      index_dict: Dict with census UI column token index for each year.
      delimiter: delimiter seperating tokens within single column name string.
    
    Returns:
      Dict with year, census column name as key value and the index of census UI column name token as value.
  """
    # store the rows according to their columns
    ret_dict = {}
    for year in yearwise_columns:
        if year in year_list:
            ret_dict[year] = {}
            for census_col in census_columns:
                ret_dict[year][census_col] = []
            for census_cell in yearwise_columns[year]:
                token_list = census_cell.split(delimiter)
                for census_col in census_columns:
                    if token_list[index_dict[year]] == census_col or token_list[
                            index_dict[year]] == census_col + ' MOE':
                        if census_cell not in ret_dict[year][census_col]:
                            ret_dict[year][census_col].append(census_cell)

    return ret_dict


def get_census_rows_by_column_by_type(rows_by_column: dict,
                                      delimiter: str = '!!') -> dict:
    # store the rows according to their columns and type
    ret_dict = {}
    for year in rows_by_column:
        ret_dict[year] = {}
        for census_col in rows_by_column[year]:
            ret_dict[year][census_col] = {'moe_cols': [], 'estimate_cols': []}
            for census_cell in rows_by_column[year][census_col]:
                token_list = census_cell.split(delimiter)
                if 'Margin of Error' in token_list:
                    ret_dict[year][census_col]['moe_cols'].append(census_cell)
                else:
                    ret_dict[year][census_col]['estimate_cols'].append(
                        census_cell)

    return ret_dict


def get_column_total_status(totals_by_column: dict,
                            rows_by_column_type: dict) -> dict:
    ret_dict = {}
    for year in totals_by_column:
        for census_col in totals_by_column[year]:
            if census_col not in ret_dict:
                ret_dict[census_col] = {}
            ret_dict[census_col][year] = {
                'only_percentage': False,
                'only_total': False,
            }
            # only percentages
            if len(totals_by_column[year][census_col]) == 0:
                ret_dict[census_col][year]['only_percentage'] = True

            # only totals
            if len(totals_by_column[year][census_col]) == len(
                    rows_by_column_type[year][census_col]['estimate_cols']):
                ret_dict[census_col][year]['only_total'] = True

    return ret_dict


def get_denominator_method_config(
    totals_status: dict, totals_by_column: dict,
    total_not_prefix: list = ()) -> dict:
    ret_dict = {}
    ret_dict['denominator_method'] = ''
    total_columns = []
    percent_columns = []

    for census_col in totals_status:
        col_is_total = 1
        col_is_percent = 1
        for year in totals_status[census_col]:
            if col_is_total == 1:
                col_is_total = totals_status[census_col][year]['only_total']
            if col_is_total != totals_status[census_col][year]['only_total']:
                col_is_total = 2
            if col_is_percent == 1:
                col_is_percent = totals_status[census_col][year][
                    'only_percentage']
            if col_is_percent != totals_status[census_col][year][
                    'only_percentage']:
                col_is_percent = 2

        if col_is_percent == 2:
            ret_dict['denominator_method'] = 'year_mismatch'
        elif col_is_percent:
            percent_columns.append(census_col)
        if col_is_total == 2:
            ret_dict['denominator_method'] = 'year_mismatch'
        elif col_is_total:
            total_columns.append(census_col)

    if len(percent_columns) > 0 and len(total_columns) > 0:
        ret_dict['denominator_method'] = 'token_replace'
        ret_dict['token_map'] = {}
        for tok in percent_columns:
            ret_dict['token_map'][tok] = total_columns[0]
        if len(total_columns) > 1:
            print(
                'Warning: The config might need fixing of token_map section because multiple total columns were found'
            )
    # prefix method
    else:
        ret_dict['denominator_method'] = 'prefix'
        temp_dict = {'col': '', 'len': 0}
        len_dict = {}
        # check if length of estimates is the same for all columns
        for year in totals_by_column:
            for census_col in totals_by_column[year]:
                # sanity checks
                if census_col not in len_dict:
                    len_dict[census_col] = len(
                        totals_by_column[year][census_col])
                elif len_dict[census_col] != len(
                        totals_by_column[year][census_col]):
                    print(
                        'Warning: number of totals for', census_col,
                        'changes across years, modify the long config if needed'
                    )

                # find longest list of totals to use, ideally should be same for all columns
                if len(totals_by_column[year][census_col]) > temp_dict['len']:
                    temp_dict['col'] = census_col
                    temp_dict['len'] = len(totals_by_column[year][census_col])
                    temp_dict['rows'] = totals_by_column[year][census_col]

        ret_dict['reference_column'] = temp_dict['col']
        ret_dict['totals'] = {}
        for year in totals_by_column:
            ret_dict['totals'][year] = totals_by_column[year][temp_dict['col']]

        # TODO discard column present total_not_prefix(should be a new section in the initial config)
        # useful when there are multiple totals followed by percentage using the 1st total
    return ret_dict


def rename_col(row_name: str, new_col: str, col_i: int, delimiter: str = '!!'):
    temp_list = row_name.split(delimiter)
    temp_list[col_i] = new_col
    temp_str = delimiter.join(temp_list)
    return temp_str


def col_add_moe(row_name: str, col_i: int, delimiter: str = '!!'):
    temp_list = row_name.split(delimiter)
    temp_list[col_i] = temp_list[col_i] + ' MOE'
    temp_str = delimiter.join(temp_list)
    return temp_str


# create config
def create_long_config(basic_config_path: str, delimiter: str = '!!') -> None:
    basic_config_path = os.path.expanduser(basic_config_path)
    config_dict = json.load(open(basic_config_path))

    spec_dict = get_spec_dict_from_path(config_dict['spec_path'])

    us_data_zip = os.path.expanduser(config_dict['us_data_zip'])

    year_list = config_dict['year_list']

    yearwise_columns = yearwise_columns_from_zip_file(us_data_zip, spec_dict,
                                                      year_list, delimiter)

    census_columns = config_dict['census_columns']
    used_columns = config_dict['used_columns']
    ignore_tokens = config_dict['ignore_tokens']

    for year in yearwise_columns:
        # remove median, mean
        temp_list = []
        for column_name in yearwise_columns[year]:
            tok_found = False
            for tok in ignore_tokens:
                if tok in column_name:
                    tok_found = True
            if not tok_found:
                temp_list.append(column_name)
        yearwise_columns[year] = temp_list

    yearwise_column_ind = get_census_column_token_index(census_columns,
                                                        year_list,
                                                        yearwise_columns,
                                                        delimiter)
    # yearwise col_token index store in config
    config_dict['column_tok_index'] = yearwise_column_ind

    # find set all rows of each column yearwise
    yearwise_rows_by_column = get_census_rows_by_column(census_columns,
                                                        year_list,
                                                        yearwise_columns,
                                                        yearwise_column_ind,
                                                        delimiter)
    yearwise_rows_by_column_type = get_census_rows_by_column_by_type(
        yearwise_rows_by_column)

    # find possible totals
    yearwise_total_columns = guess_total_columns_from_zip_file(
        us_data_zip, ignore_tokens, year_list)
    for year in yearwise_total_columns:
        # remove ignoreColumns
        yearwise_total_columns[year] = remove_columns_to_be_ignored(
            yearwise_total_columns[year], spec_dict)

    # group by column name
    yearwise_totals_by_column = get_census_rows_by_column(
        used_columns, year_list, yearwise_total_columns, yearwise_column_ind,
        delimiter)

    yearwise_totals_status = get_column_total_status(
        yearwise_totals_by_column, yearwise_rows_by_column_type)

    temp_config = get_denominator_method_config(yearwise_totals_status,
                                                yearwise_totals_by_column)
    config_dict.update(temp_config)

    new_config_path = basic_config_path.replace('.json', '_long.json')
    json.dump(config_dict, open(new_config_path, 'w'), indent=2)

    # store yearwise_rows_by_column_type
    columns_path = new_config_path.replace('.json', '_columns.json')
    json.dump(yearwise_rows_by_column_type, open(columns_path, 'w'), indent=2)

    print(json.dumps(config_dict, indent=2))


# TODO accept the path of _columns.json
def create_denominators_section(long_config_path: str,
                                delimiter: str = '!!') -> None:
    long_config_path = os.path.expanduser(long_config_path)
    config_dict = json.load(open(long_config_path))

    rows_by_column_type = json.load(
        open(long_config_path.replace('.json', '_columns.json')))
    denominators = {}
    no_prefix = []
    if config_dict['denominator_method'] == 'token_replace':
        for new_col in config_dict['token_map']:
            total_col = config_dict['token_map'][new_col]
            for year in rows_by_column_type:
                col_i = config_dict['column_tok_index'][year]
                for new_total in rows_by_column_type[year][total_col][
                        'estimate_cols']:
                    if new_total not in denominators:
                        denominators[new_total] = []
                    # replace new_col in new_total
                    temp_str = rename_col(new_total, new_col, col_i, delimiter)
                    # check and add
                    if temp_str in rows_by_column_type[year][new_col][
                            'estimate_cols']:
                        if temp_str not in denominators[new_total]:
                            denominators[new_total].append(temp_str)
                    else:
                        print('Warning: column expected but not found\n',
                              temp_str)

                    # replace new_col and Margin of Error in new_total
                    temp_str2 = replace_token_in_column(temp_str, 'Estimate',
                                                        'Margin of Error',
                                                        delimiter)
                    # check and add
                    moe_found = False
                    if temp_str2 in rows_by_column_type[year][new_col][
                            'moe_cols']:
                        if temp_str2 not in denominators[new_total]:
                            denominators[new_total].append(temp_str2)
                        moe_found = True

                    # replace new_col+ MOE and Margin of Error in new_total
                    temp_str3 = rename_col(new_total, new_col + ' MOE', col_i,
                                           delimiter)
                    temp_str3 = replace_token_in_column(temp_str3, 'Estimate',
                                                        'Margin of Error',
                                                        delimiter)
                    # check and add
                    if temp_str3 in rows_by_column_type[year][new_col][
                            'moe_cols']:
                        if temp_str3 not in denominators[new_total]:
                            denominators[new_total].append(temp_str3)
                        moe_found = True

                    if not moe_found:
                        print('Warning: column expected but not found\n',
                              temp_str2, '\nor\n', temp_str3)

    if config_dict['denominator_method'] == 'prefix':
        yearwise_totals_col = config_dict['totals']
        used_col = config_dict['used_columns']
        # create extended totals list
        total_prefixes = []
        for year in yearwise_totals_col:
            col_i = config_dict['column_tok_index'][year]
            for new_total in yearwise_totals_col[year]:
                if new_total not in total_prefixes:
                    total_prefixes.append(new_total)
                for new_col in used_col:
                    temp_str = rename_col(new_total, new_col, col_i, delimiter)
                    if temp_str not in total_prefixes:
                        total_prefixes.append(temp_str)

        # read columns by year
        for year in rows_by_column_type:
            print('year', year)
            col_i = config_dict['column_tok_index'][year]
            for census_col in rows_by_column_type[year]:
                for cur_i, new_row in enumerate(
                        rows_by_column_type[year][census_col]['estimate_cols']):
                    cur_prefix = column_find_prefixed(new_row, total_prefixes)
                    if cur_prefix:
                        if cur_prefix not in denominators:
                            denominators[cur_prefix] = []
                        if new_row not in denominators[cur_prefix]:
                            denominators[cur_prefix].append(new_row)
                        temp_str2 = replace_token_in_column(
                            new_row, 'Estimate', 'Margin of Error', delimiter)
                        temp_str3 = col_add_moe(temp_str2, col_i, delimiter)
                        moe_found = False
                        if temp_str2 in rows_by_column_type[year][census_col][
                                'moe_cols']:
                            if temp_str2 not in denominators[cur_prefix]:
                                denominators[cur_prefix].append(temp_str2)
                            moe_found = True
                        if temp_str3 in rows_by_column_type[year][census_col][
                                'moe_cols']:
                            if temp_str3 not in denominators[cur_prefix]:
                                denominators[cur_prefix].append(temp_str3)
                            moe_found = True
                        if not moe_found:
                            print('Warning: column expected but not found\n',
                                  temp_str2, '\nor\n', temp_str3)
                    # warn if no prefix found
                    elif new_row not in total_prefixes:
                        # print('Warning:', new_row, 'has no prefix and is not a total')
                        print(new_row)
                        new_total_i = -1
                        for total_i in range(cur_i):
                            if rows_by_column_type[year][census_col][
                                    'estimate_cols'][total_i] in total_prefixes:
                                new_total_i = total_i
                        new_total = rows_by_column_type[year][census_col][
                            'estimate_cols'][new_total_i]
                        if new_total not in denominators:
                            denominators[new_total] = []
                        if new_row not in denominators[new_total]:
                            denominators[new_total].append(new_row)
                        temp_str2 = replace_token_in_column(
                            new_row, 'Estimate', 'Margin of Error', delimiter)
                        temp_str3 = col_add_moe(temp_str2, col_i, delimiter)
                        moe_found = False
                        if temp_str2 in rows_by_column_type[year][census_col][
                                'moe_cols']:
                            if temp_str2 not in denominators[new_total]:
                                denominators[new_total].append(temp_str2)
                            moe_found = True
                        if temp_str3 in rows_by_column_type[year][census_col][
                                'moe_cols']:
                            if temp_str3 not in denominators[new_total]:
                                denominators[new_total].append(temp_str3)
                            moe_found = True
                        if not moe_found:
                            print('Warning: column expected but not found\n',
                                  temp_str2, '\nor\n', temp_str3)
                        print(new_total, '\n')
                        no_prefix.append({new_row: new_total})

    # print(json.dumps(denominators, indent=2))
    output_path = os.path.dirname(long_config_path)
    if no_prefix:
        json.dump(no_prefix,
                  open(os.path.join(output_path, 'rows_without_prefix.json'),
                       'w'),
                  indent=2)
    json.dump(denominators,
              open(os.path.join(output_path, 'denominators.json'), 'w'),
              indent=2)
    if config_dict['update_spec']:
        spec_dict = get_spec_dict_from_path(config_dict['spec_path'])
        spec_dict['denominators'] = denominators
        json.dump(spec_dict, open(config_dict['spec_path'], 'w'), indent=2)


def get_columns_stat_moe(column_list: list, delimiter: str = '!!') -> list:
    ret_list = []
    stat_tokens = ['Mean', 'Median', 'Average']
    moe_columns = find_columns_with_token(column_list, 'Margin of Error')
    for cur_token in stat_tokens:
        ret_list.extend(
            find_columns_with_token_partial_match(moe_columns, cur_token,
                                                  delimiter))

    return list(set(ret_list))


def main(argv):
    if FLAGS.denominator_config:
        create_long_config(FLAGS.denominator_config)
    if FLAGS.denominator_long_config:
        create_denominators_section(FLAGS.denominator_long_config)
    if FLAGS.get_ignore_columns:
        if not FLAGS.column_list_path:
            print('List of columns required to get ignore columns')
        else:
            columns_path = os.path.expanduser(FLAGS.column_list_path)
            column_list = json.load(open(columns_path))
            ignore_columns = get_columns_stat_moe(column_list, FLAGS.delimiter)
            print(json.dumps(ignore_columns, indent=2))


if __name__ == '__main__':
    app.run(main)
