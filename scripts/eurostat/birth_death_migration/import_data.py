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


def download_data():
    """Downloads raw data from Eurostat website and stores it in instance
    data frame.
    """
    raw_df = pd.read_table(DATA_LINK)
    return raw_df


def preprocess_data(raw_df):
    """Preprocesses instance raw_df and puts it into long format."""
    if raw_df is None:
        raise ValueError("Uninitialized value of raw data frame. Please "
                         "check you are calling download_data before "
                         "preprocess_data.")
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
    # Replace value column with extra space.
    preprocessed_df.value = preprocessed_df.value.str.replace(
        "([0-9:])$", lambda m: m.group(0) + ' ')
    statistical_variable = None
    # In case this returns only one element in the list.
    first_column_list = preprocessed_df.columns[0].rsplit(sep=",", maxsplit=1)
    if len(first_column_list) == 2:
        statistical_variable, geo = first_column_list
    else:
        geo = first_column_list[0]
    geo = geo.replace(r'\time', '')
    assert geo == "geo", "Expected the column header to end with 'geo'."

    if statistical_variable:
        split_df = preprocessed_df[preprocessed_df.columns[0]].str.rsplit(
            ",", n=1, expand=True)
        preprocessed_df['statistical_variable'] = split_df[0]
        preprocessed_df['geo'] = split_df[1]
        preprocessed_df.drop(columns=[preprocessed_df.columns[0]], inplace=True)

        preprocessed_df = (preprocessed_df.set_index(["geo", "time"]).pivot(
            columns="statistical_variable")['value'].reset_index().rename_axis(
                None, axis=1))
    # Fill missing 'geo' values with a colon.
    preprocessed_df.fillna(': ', inplace=True)

    # Split notes out of values.
    # Ex: "5598920 b" -> "5598920", "b".
    # Ex: "5665118" -> "5665118", ""
    # Ex: ": c" -> "", "c"
    # Append extra space for all values that do not come with a note.
    preprocessed_df[preprocessed_df.columns[2:]] = preprocessed_df[
        preprocessed_df.columns[2:]].replace("([0-9:])$",
                                             lambda m: m.group(0) + ' ')
    # replace comma in column names with a vertical bar so that we can save it in csv later
    new_column_names = []
    for column_name in preprocessed_df.columns:
        new_column_names.append(column_name.replace(',', '|'))
    preprocessed_df.columns = new_column_names
    for column_name in preprocessed_df.columns[2:]:
        preprocessed_df['{0}'.format(column_name)], preprocessed_df[
            '{0}|notes'.format(column_name)] = (zip(
                *preprocessed_df[column_name].apply(lambda x: x.split(' '))))
    return preprocessed_df


def clean_data(preprocessed_df):
    """Drops unnecessary columns that are not needed for data import and reformat column names."""
    if preprocessed_df is None:
        raise ValueError("Uninitialized value of processed data frame. "
                         "Please check you are calling preprocess_data "
                         "before clean_data.")
    # drop unused columns
    clean_df = preprocessed_df[preprocessed_df.columns[:len(
        preprocessed_df.columns
    ) // 2 + 1]]  # number of columns should be 2 + 2X, we want the first 2 + X
    # columns
    # replace colon with NaN.
    clean_df = clean_df.replace(':', '')
    clean_df.to_csv(FINAL_CSV_NAME, index=False)
    clean_df = pd.read_csv(FINAL_CSV_NAME)

    clean_df['geo'] = 'dcid:nuts/' + clean_df['geo']
    original_names = [
        'geo', 'time', 'DEATH', 'GBIRTHRT', 'GDEATHRT', 'GROW', 'GROWRT', 'JAN',
        'LBIRTH'
    ]
    new_names = [
        'geo', 'time', 'Count_MortalityEvent',
        'Count_BirthEvent_AsAFractionOfCount_Person',
        'Count_MortalityEvent_AsAFractionOfCount_Person',
        'IncrementalCount_Person', 'GrowthRate_Count_Person', 'Count_Person',
        'Count_BirthEvent'
    ]
    clean_df = clean_df[original_names]
    clean_df[['GBIRTHRT', 'GDEATHRT',
              'GROWRT']] /= 1000  # apply scaling factor of 1000
    clean_df.columns = new_names
    clean_df.to_csv(FINAL_CSV_NAME, index=False)


if __name__ == '__main__':
    DATA_LINK = "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/demo_r_gind3.tsv.gz"
    FINAL_CSV_NAME = 'demo_r_gind3_final_stage.csv'
    raw_df = download_data()
    preprocessed_df = preprocess_data(raw_df)
    clean_data(preprocessed_df)
