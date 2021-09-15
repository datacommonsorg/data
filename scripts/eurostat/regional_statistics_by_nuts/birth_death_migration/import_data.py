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

import pandas as pd


def download_data(download_link):
    """Downloads raw data from Eurostat website and stores it in instance
    data frame.
    """
    raw_df = pd.read_table(download_link)
    return raw_df


def preprocess_data(raw_df):
    """Preprocesses instance raw_df and puts it into long format.

    Assume the head of the dataset at most looks something like this (a typical Eurostat dataset):
        indic_de,geo\time 2019    2018    2017  ...    2003    2002    2001    2000
    0       CNMIGRAT,AL    :  -15027  -14904  ...  -39807  -41292  -17640  -30000
    1      CNMIGRAT,AL0    :  -14938  -14798  ...       :       :       :       :
    2     CNMIGRAT,AL01    :   -8699  -10353  ...       :       :       :       :
    3    CNMIGRAT,AL011    :   -2680   -5396  ...       :       :       :       :
    4    CNMIGRAT,AL012    :    -512    3488  ...       :       :       :       :

        where the first column ends with geo\time and it should at least have two columns in order to have
        observation values. It handles cases where there is 0 or more statistical variable in the first column.
        In this case, we have one statistical variable called indic_de
    We first melt this to a long format
        geo  time  indic_de   value
    0  AL  2019  CNMIGRAT       :
    1  AL  2018  CNMIGRAT  -15027
    2  AL  2017  CNMIGRAT  -14904
    3  AL  2016  CNMIGRAT   -9346
    4  AL  2015  CNMIGRAT  -27007 e
        where the first and second column are 'geo' and 'time'. The third column contains all the statistical
        variables.
    After this, we pivot the table using 'geo' and 'time' to obtain our processed table
        geo  time CNMIGRAT  ... LBIRTH|notes NATGROW|notes NATGROWRT|notes
    0  AL  2000   -30000  ...            :             :               :
    1  AL  2001   -17640  ...            :             :               :
    2  AL  2002   -41292  ...            :             :               :
    3  AL  2003   -39807  ...            :             :               :
    4  AL  2004   -39870  ...            :             :               :
    It contains 2 + 2X columns where X is the number of statistical variables the first two columns are
    'geo' and 'time', followed by X columns of statistical variables values, followed by X columns of
    statistical variable notes.

    """
    assert len(raw_df.columns) > 1, "Data must have at least two columns."
    assert raw_df.columns.values[0].endswith(
        '\\time'), "Expected the first column header to end with '\\time'."

    # Convert from one-year per column (wide format) to one row per
    # data point (long format).
    preprocessed_df = raw_df.melt(id_vars=[raw_df.columns[0]])
    # Rename the variable column.
    preprocessed_df.columns.values[1] = 'time'

    # Split the index column into two.
    # Ex: 'unit,sex,age,geo\time' -> 'unit,sex,age' and 'geo'.
    # '\time' labels the other columns so it is confusing.

    # Append extra space for all cells in value column that do not come with a note, so that we can split them without error.
    preprocessed_df.value = preprocessed_df.value.str.replace(
        "([0-9:])$", lambda m: m.group(0) + ' ')

    first_column_list = preprocessed_df.columns[0].rsplit(sep=",", maxsplit=1)

    statistical_variable = None
    # In case this returns only one element in the list.
    if len(first_column_list) == 2:
        statistical_variable, geo = first_column_list
    else:
        geo = first_column_list[0]
    geo = geo.replace(r'\time', '')
    assert geo == "geo", "Column header should end with 'geo'."

    if statistical_variable:
        split_df = preprocessed_df[preprocessed_df.columns[0]].str.rsplit(
            ",", n=1, expand=True)
        preprocessed_df['statistical_variable'] = split_df[0]
        preprocessed_df['geo'] = split_df[1]
        preprocessed_df.drop(columns=[preprocessed_df.columns[0]],
                             inplace=True)

        preprocessed_df = (preprocessed_df.set_index(["geo", "time"]).pivot(
            columns="statistical_variable")['value'].reset_index().rename_axis(
                None, axis=1))
    # Fill missing 'geo' values with a colon.
    preprocessed_df.fillna(': ', inplace=True)

    # replace comma in column names with a vertical bar so that we can save it in csv later
    new_column_names = []
    for column_name in preprocessed_df.columns:
        new_column_names.append(column_name.replace(',', '|'))
    preprocessed_df.columns = new_column_names
    # split the statistical value and its note into two columns
    # split notes out of values.
    # ex: "5598920 b" -> "5598920", "b".
    # ex: "5665118" -> "5665118", ""
    # ex: ": c" -> "", "c"
    for column_name in preprocessed_df.columns[2:]:
        preprocessed_df['{0}'.format(column_name)], preprocessed_df[
            '{0}|notes'.format(column_name)] = (zip(
                *preprocessed_df[column_name].apply(lambda x: x.split(' '))))
    return preprocessed_df


def clean_data(preprocessed_df, output_path):
    """Drops unnecessary columns that are not needed for data import and reformat column names."""
    # number of columns should be 2 + 2X, we want the first 2 + X
    num_clean_columns = len(preprocessed_df.columns) // 2 + 1
    # drop unused columns
    clean_df = preprocessed_df.iloc[:, :num_clean_columns]

    # replace colon with NaN.
    clean_df = clean_df.replace(':', '')

    clean_df['geo'] = 'dcid:nuts/' + clean_df['geo']
    # trim the space in the time column i.e. '2020 ' -> '2020'
    clean_df['time'] = clean_df['time'].astype('int32')
    original_names = [
        'geo', 'time', 'DEATH', 'GBIRTHRT', 'GDEATHRT', 'GROW', 'GROWRT',
        'JAN', 'LBIRTH'
    ]
    new_names = [
        'geo', 'time', 'Count_Death',
        'Count_BirthEvent_AsAFractionOf_Count_Person',
        'Count_Death_AsAFractionOf_Count_Person', 'IncrementalCount_Person',
        'GrowthRate_Count_Person', 'Count_Person', 'Count_BirthEvent'
    ]
    clean_df = clean_df[original_names]
    clean_df[['GBIRTHRT', 'GDEATHRT',
              'GROWRT']] = clean_df[['GBIRTHRT', 'GDEATHRT',
                                     'GROWRT']].apply(pd.to_numeric)
    clean_df[['GBIRTHRT', 'GDEATHRT',
              'GROWRT']] /= 1000  # apply scaling factor of 1000
    clean_df.columns = new_names
    clean_df.to_csv(output_path, index=False)


if __name__ == '__main__':
    download_link = "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/demo_r_gind3.tsv.gz"
    output_path = 'EurostatNUTS3_BirthDeathMigration.csv'
    raw_df = download_data(download_link)
    preprocessed_df = preprocess_data(raw_df)
    clean_data(preprocessed_df, output_path)
