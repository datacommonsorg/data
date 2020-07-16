# Copyright 2020 Google LLC
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
Defines functions to preprocess Eurostat data and put it in long-form CSV format.
Author:

    Usage:

    python3 preprocess_data.py (--input_file) (--output_file) (--sep)
"""
import pandas as pd
import argparse
import gzip
import shutil


def unzip_single(filename_in):
    filename_out = filename_in[:-3]  # to trim the .gz
    with gzip.open(filename_in, 'rb') as f_in:
        with open(filename_out, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    return filename_out


def first_stage_processing(df, separation_symbol):
    time_invariant_var = 'geo'
    header = list(df.columns)
    variable_column = header[0]
    variable_column = variable_column.replace('\\', ',')
    variable_column = variable_column.split(',')
    assert variable_column[-1] == 'time'  # have this constraint for now
    assert time_invariant_var in variable_column
    time_invariant_var_index = variable_column.index(time_invariant_var)
    time_columns = header[1:]
    # just strip the space in the time column
    for i in range(len(time_columns)):
        time_columns[i] = time_columns[i].strip()
    df.columns = [header[0]] + time_columns
    combined_variable_name = ''
    for v in variable_column:
        if v != 'time' and v != time_invariant_var:
            combined_variable_name = combined_variable_name + v + separation_symbol
    combined_variable_name = combined_variable_name[:-len(separation_symbol)]  # remove last underscore
    # insert a dummy variable for two dimensional dataset. Note most of the time this should not happen
    if combined_variable_name == '':
        combined_variable_name = 'dummy_var_column'
    total_record_count = len(df)*len(time_columns)
    all_records = []
    for i in range(len(df)):
        row_values = list(df.iloc[i])
        variable_value_list = row_values[0].split(',')
        time_invariant_var_value = variable_value_list[time_invariant_var_index]
        del variable_value_list[time_invariant_var_index]
        current_combined_variable_value = separation_symbol.join(variable_value_list)
        # insert a dummy variable for two dimensional dataset. Note most of the time this should not happen
        if combined_variable_name == 'dummy_var_column' and current_combined_variable_value == '':
            current_combined_variable_value = 'dummy_var'
        for j in range(len(time_columns)):
            raw_value = row_values[j + 1].strip()
            value_with_note = raw_value.split(' ')  # want to distinguish between the ones with notes and without
            if len(value_with_note) == 2:
                value = value_with_note[0]
                note = value_with_note[1]
            elif len(value_with_note) == 1:
                value = value_with_note[0]
                note = ':'
            else:
                print(value_with_note)
                raise NotImplementedError
            all_records.append([time_invariant_var_value, time_columns[j], current_combined_variable_value, value, note])
    new_df = pd.DataFrame(all_records, columns=[time_invariant_var, 'time', combined_variable_name, 'value', 'note'])
    assert len(new_df) == total_record_count
    return new_df


def second_stage_processing(df, separation_symbol):
    combined_variable_name = list(df.columns)[2]

    combined_variable_values_list = sorted(list(df[combined_variable_name].unique()))
    combined_variables_values_set = set(combined_variable_values_list)
    notes_list = []
    units_list = []
    unit_values = []
    for v in combined_variable_values_list:
        notes_list.append(v + separation_symbol + 'notes')
    if 'unit' in combined_variable_name:
        unit_index = combined_variable_name.split(separation_symbol).index('unit')
        for v in combined_variable_values_list:
            units_list.append(v + separation_symbol + 'unit')
            unit_values.append(v.split(separation_symbol)[unit_index])
    grouped_df = df.groupby(['geo', 'time'])
    all_records = []
    for name, group in grouped_df:
        keys = list(name)
        variable_list = list(group[combined_variable_name])
        value_list = list(group['value'])
        note_list = list(group['note'])
        missing_variable_list = list(combined_variables_values_set - set(variable_list))
        variable_list.extend(missing_variable_list)
        value_list.extend([':']*len(missing_variable_list))
        note_list.extend([':']*len(missing_variable_list))
        variable_value_note = zip(variable_list, value_list, note_list)
        variable_value_note_sorted = sorted(variable_value_note)
        variable_list_sorted = [variable for variable, value, note in variable_value_note_sorted]
        assert variable_list_sorted == combined_variable_values_list
        value_list_sorted = [value for variable, value, note in variable_value_note_sorted]
        note_list_sorted = [note for variable, value, note in variable_value_note_sorted]
        if len(units_list) > 0:
            unit_list_sorted = unit_values
            all_records.append(keys + value_list_sorted + note_list_sorted + unit_list_sorted)
        else:
            all_records.append(keys + value_list_sorted + note_list_sorted)
    if len(units_list) > 0:
        new_df = pd.DataFrame(all_records, columns=['geo', 'time'] + combined_variable_values_list + notes_list + units_list)
    else:
        new_df = pd.DataFrame(all_records, columns=['geo', 'time'] + combined_variable_values_list + notes_list)
    return new_df

def preprocess_df(df, sep='|'):
    """Combines first_stage_processing and second_stage_processing into an
    end-to-end processing of a raw dataframe.
    """
    first_stage_df = first_stage_processing(df, sep)
    return second_stage_processing(first_stage_df, sep)

def main(args):
    print('Processing {0}'.format(args.input_file))
    tsv_filename = unzip_single(PREFIX + args.input_file)
    df = pd.read_csv(tsv_filename, delimiter='\t')
    first_stage_df = first_stage_processing(df, args.sep)
    second_stage_df = second_stage_processing(first_stage_df, args.sep)
    if args.output_file is None:
        second_stage_df.to_csv(args.input_file.replace('.tsv.gz', '_processed.csv'), index=False)
    else:
        second_stage_df.to_csv(args.output_file, index=False)
    print('Done processing {0}'.format(args.input_file))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="EuroStat Processing Script")
    parser.add_argument('-i', dest='input_file', default='demo_r_pjangrp3.tsv.gz')
    parser.add_argument('-o', dest='output_file', default=None)
    parser.add_argument('-s', dest='sep', type=str, default='|')  # dataset dependent
    args = parser.parse_args()

    main(args)
