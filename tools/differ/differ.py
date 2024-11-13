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

from absl import app
from absl import flags
from absl import logging
import pandas as pd
import helper
import os

FLAGS = flags.FLAGS
flags.DEFINE_string("currentData", "", "Path to the current MCF data.")
flags.DEFINE_string("previousData", "", "Path to the previous MCF data.")
flags.DEFINE_string("outputLocation", "output", "Path to the output data.")

flags.DEFINE_string("groupbyColumns", "variableMeasured,observationAbout,observationDate",
  "Columns to group data for diff analysis in the order (var,place,time etc.).")
flags.DEFINE_string("valueColumns", "value,unit",
  "Columns with statvar value (unit etc.) for diff analysis.")

SAMPLE_COUNT=3

class DatasetDiffer:
  """
  This utility generates a diff (point and series analysis) 
  of two data files of the same dataset for import analysis. 

  Usage:
  $ python differ.py --currentData=<filepath> --previousData=<filepath>

  Summary output generated is of the form below showing counts of differences for each
  variable.  Detailed diff output is written to files for further analysis.

variableMeasured   added  deleted  modified  same  total
0   dcid:var1       1      0       0          0     1
1   dcid:var2       0      2       1          1     4
2   dcid:var3       0      0       1          0     1
3   dcid:var4       0      2       0          0     2

  """

  def __init__(self, groupby_columns, value_columns):
    self.groupby_columns = groupby_columns.split(",")
    self.value_columns = value_columns.split(",")
    self.variable_column  =  self.groupby_columns[0]
    self.place_column  =  self.groupby_columns[1]
    self.time_column  =  self.groupby_columns[2]
    self.diff_column = "_diff_result"

  def __cleanup_data(self, df: pd.DataFrame):
    for column in ["added", "deleted", "modified", "same"]:
      df[column] = df[column] if column in df.columns else 0
      df[column] = df[column].fillna(0).astype(int)

  # Pro-rocesses two dataset files to identify changes.
  def process_data(self, previous_df: pd.DataFrame, current_df: pd.DataFrame) -> pd.DataFrame:
    cur_df_columns = current_df.columns.values.tolist()
    self.groupby_columns = [i for i in self.groupby_columns if i in cur_df_columns]
    self.value_columns = [i for i in self.value_columns if i in cur_df_columns]
    df1 = previous_df.loc[:, self.groupby_columns + self.value_columns]
    df2 = current_df.loc[:, self.groupby_columns + self.value_columns]
    df1["_value_combined"] = df1[self.value_columns]\
      .apply(lambda row: "_".join(row.values.astype(str)), axis=1)
    df2["_value_combined"] = df2[self.value_columns]\
      .apply(lambda row: "_".join(row.values.astype(str)), axis=1)
    df1.drop(columns=self.value_columns, inplace=True)
    df2.drop(columns=self.value_columns, inplace=True)
    # Perform outer join operation to identify differences.
    result  = pd.merge(df1, df2, on = self.groupby_columns, how="outer", indicator=self.diff_column)
    result[self.diff_column] = result.apply(
      lambda row: "added" if row[self.diff_column] == "right_only" \
      else "deleted" if row[self.diff_column] == "left_only" \
      else "modified" if row["_value_combined_x"] != row["_value_combined_y"] \
      else "same", axis=1)
    return result

  # Performs point diff analysis to identify data point changes.
  def point_analysis(self, in_data: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
    column_list = [self.variable_column, self.place_column, self.time_column, self.diff_column]
    result = in_data.loc[:, column_list]
    # summary = summary.groupby([variable,"result"], observed=True, as_index=False).agg(["count"]).reset_index()
    result = result.groupby([self.variable_column, self.diff_column], observed=True, as_index=False)[[self.place_column, self.time_column]].agg(lambda x: x.tolist())
    result["size"] = result.apply(lambda row:len(row[self.place_column]), axis=1)
    result[self.place_column] = result.apply(lambda row: row[self.place_column][0:SAMPLE_COUNT], axis=1)
    result[self.time_column] = result.apply(lambda row: row[self.time_column][0:SAMPLE_COUNT], axis=1)
    # result = result.groupby(
    #   [self.variable_column, self.diff_column], observed=True, as_index=False).size()
    summary = result.pivot(
      index=self.variable_column, columns=self.diff_column, values="size")\
      .reset_index().rename_axis(None, axis=1)
    self.__cleanup_data(summary)
    summary["total"] = summary.apply(
      lambda row: row["added"] + row["deleted"] + row["modified"] + row["same"] , axis=1)
    return summary, result

  # Performs series diff analysis to identify time series changes.
  def series_analysis(self, in_data: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
    column_list = [self.variable_column, self.place_column, self.diff_column]
    result = in_data.loc[:, column_list]
    result = result.groupby(column_list, as_index=False).size()
    result = result.pivot(
      index=[self.variable_column, self.place_column], columns=self.diff_column, values="size")\
      .reset_index().rename_axis(None, axis=1)
    self.__cleanup_data(result)
    result[self.diff_column] = result.apply(lambda row: "added" if row["added"] > 0 \
      and row["deleted"] + row["modified"] + row["same"] == 0 \
      else "deleted" if row["deleted"] > 0 and row["added"] + row["modified"] + row["same"] == 0 \
      else "modified" if row["deleted"] > 0 or row["added"] > 0 or row["modified"] > 0 \
      else "same", axis=1)
    result = result[column_list]
    result = result.groupby([self.variable_column, self.diff_column], observed=True, as_index=False)[self.place_column].agg(lambda x: x.tolist())
    result["size"] = result.apply(lambda row:len(row[self.place_column]), axis=1)
    result[self.place_column] = result.apply(lambda row: row[self.place_column][0:SAMPLE_COUNT], axis=1)
    summary = result.pivot(
      index=self.variable_column, columns=self.diff_column, values="size")\
      .reset_index().rename_axis(None, axis=1)
    self.__cleanup_data(summary)
    summary["total"] = summary.apply(
      lambda row: row["added"] + row["deleted"] + row["modified"] + row["same"], axis=1)
    return summary, result

def main(_):
  """Runs the code."""
  differ = DatasetDiffer(
    FLAGS.groupbyColumns, FLAGS.valueColumns)

  if not os.path.exists(FLAGS.outputLocation):
    os.makedirs(FLAGS.outputLocation)
  logging.info("Loading data...")
  previous_df = helper.load_data(FLAGS.currentData, FLAGS.outputLocation)
  current_df = helper.load_data(FLAGS.previousData, FLAGS.outputLocation)

  logging.info("Processing data...")
  in_data = differ.process_data(previous_df, current_df)

  logging.info("Point analysis:")
  summary, result = differ.point_analysis(in_data)
  result.sort_values(by=[differ.diff_column, differ.variable_column], inplace=True)
  print(summary.head(10))
  print(result.head(10))
  helper.write_data(summary, FLAGS.outputLocation, "point-analysis-summary.csv")
  helper.write_data(result, FLAGS.outputLocation, "point-analysis-results.csv")

  logging.info("Series analysis:")
  summary, result = differ.series_analysis(in_data)
  result.sort_values(by=[differ.diff_column, differ.variable_column], inplace=True)
  print(summary.head(10))
  print(result.head(10))
  helper.write_data(summary, FLAGS.outputLocation, "series-analysis-summary.csv")
  helper.write_data(result, FLAGS.outputLocation, "series-analysis-results.csv")

  logging.info("Differ output written to %s", FLAGS.outputLocation)


if __name__ == "__main__":
  app.run(main)
