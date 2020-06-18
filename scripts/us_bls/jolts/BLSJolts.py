"""Fetches, cleans, and downloads BLS Jolts data into Data Commons Knowledge Graph.

Data is fetched from various data sources within the BLS site then combined and cleaned.
StatisticalVariables are generated and cleaned CSV is output.

Simply download the requirements and execute the file with Python3
"""

# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from absl import app
import pandas as pd
import urllib.request

# JOLTS Mappings
# JOLTS dataset contains a mix of NAICS codes
CODE_MAPPINGS = {'000000': '00:Total nonfarm', # new code
 '100000': '10', 
 '110099': '110099:Mining and logging', # new code
 '230000': '23', 
 '300000': '300000:Manufacturing',# New Code
 '320000': '320000:Durable goods manufacturing',# New Code
 '340000': '340000:Nondurable goods manufacturing', # New Code
 '400000': '400000:Trade, transportation, and utilities',# New Code
 '420000': '42',
 '440000': '44',
 '480099': '480099:Transportation, warehousing, and utilities', # New Code
 '510000': '51',
 '510099': '510099:Financial activities', # New Code
 '520000': '52',
 '530000': '53',
 '540099': '540099:Professional and business services',# New Code
 '600000': '600000:Education and health services',# New Code
 '610000': '61',
 '620000': '62',
 '700000': '700000:Leisure and hospitality',# New Code
 '710000': '71',
 '720000': '72',
 '810000': '81',
 '900000': '900000:Government',# New Code
 '910000': '910000:Federal', # New Code
 '920000': '92',
 '923000': '923000:State and local government education', # New Code
 '929000': '929000:State and local government, excluding education'# New Code
 }

### Step 1) Data Download
# Dataset being processed: https://download.bls.gov/pub/time.series/jt/
# Data split across several white space separate files that may have incomplete rows
def web_to_pandas(url, sep, expected_cols):
  '''
    Helper to load incomplete whitespace separated data file into pandas
  '''
  df = None
  remote_web_page = urllib.request.urlopen(url)
  assert remote_web_page.getcode() == 200

  for line in remote_web_page:
    # Split out columns
    line_text = line.decode("utf-8")
    line_text = line_text.replace('\r', '')
    line_text = line_text.replace('\n', '')
    cols_in_line = [col.strip() for col in line_text.split(sep)]

    # Initialize dataframe with first row
    if df is None:
      df = pd.DataFrame(columns = cols_in_line)

    # Otherwise add a new row
    else:
      # If a row is missing a trailing column then pad it 
      cols_in_line.extend((df.shape[1] - len(cols_in_line)) * [""])
      df = df.append(pd.DataFrame([cols_in_line], columns=df.columns), ignore_index=True)

  assert len(df.columns) == len(expected_cols) and (False not in (df.columns == expected_cols))
  return df

def generateCleanedDataframe():
  # Download series descriptions (used for seasonally adjusted status and industry code)
  EXPECTED_SERIES_COLUMNS = ['series_id','seasonal', 'industry_code', 'region_code', 'dataelement_code', 'ratelevel_code', 'footnote_codes','begin_year', 'begin_period', 'end_year', 'end_period']
  series_desc = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.series", sep="\t", expected_cols=EXPECTED_SERIES_COLUMNS)
  series_desc = series_desc.set_index("series_id")

  # Download various series datapoints -- find more info here https://download.bls.gov/pub/time.series/jt/jt.txt
  EXPECTED_JOB_COLUMNS = ['series_id', 'year', 'period', 'value', 'footnote_codes']
  job_openings = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.2.JobOpenings", sep="\t", expected_cols=EXPECTED_JOB_COLUMNS)
  job_hires = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.3.Hires", sep="\t", expected_cols=EXPECTED_JOB_COLUMNS)
  total_seps = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.4.TotalSeparations", sep="\t", expected_cols=EXPECTED_JOB_COLUMNS)
  total_quits = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.5.Quits", sep="\t", expected_cols=EXPECTED_JOB_COLUMNS)
  total_layoffs = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.6.LayoffsDischarges", sep="\t", expected_cols=EXPECTED_JOB_COLUMNS)
  total_other_seps = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.7.OtherSeparations", sep="\t", expected_cols=EXPECTED_JOB_COLUMNS)


  ### Step 2) Combine and clean dataset
  # Additional information about each dataframe
  schema_mapping = [
    ("NumJobOpening", "JobPosting", "", job_openings),
    ("NumJobHire", "JobHire", "", job_hires),
    ("Turnover", "LaborTurnover", "", total_seps),
    ("NumVoluntarySeparation", "LaborTurnover", "VoluntarySeparation", total_quits),
    ("NumLayoff", "LaborTurnover", "Layoff", total_layoffs),
    ("NumOtherSeparation", "LaborTurnover", "OtherSeparation", total_other_seps),
  ]

  # Combine datasets into a single dataframe including origin of data
  jolts_df = pd.DataFrame()
  COLUMNS_TO_KEEP = ['series_id', 'year', 'period', 'value']

  for schema_name, population_type, separation_type, df in schema_mapping:
    df = df.loc[:, COLUMNS_TO_KEEP]
    df['statistical_variable'] = schema_name
    df['population_type'] = population_type
    df['separation_type'] = separation_type
    jolts_df = jolts_df.append(df)

  # Drop non-monthly data
  jolts_df = jolts_df.drop(jolts_df.query("period == 'M13'").index)

  # Change date to ISO Format (YYYY-MM)
  def period_year_to_iso_8601(row):
    month = row['period'].lstrip("M")
    year = row['year']
    return f"{year}-{month}"

  jolts_df.loc[:, 'Date'] = jolts_df.apply(period_year_to_iso_8601, axis=1)

  # Add relevant columns from series information
  jolts_df = jolts_df.merge(series_desc[['industry_code', 'region_code', 'seasonal', 'ratelevel_code']], left_on=["series_id"], right_index=True)

  # Drop rate data
  jolts_df = jolts_df.drop(jolts_df.query("ratelevel_code != 'L'").index)

  # Drop non-national data
  jolts_df = jolts_df.drop(jolts_df.query("region_code != '00'").index)

  # Map Industries
  def joltsCodesMap(row):
    mapped_code = CODE_MAPPINGS[row['industry_code']]

    # New Jolts Code
    if ":" in mapped_code:
      JOLTS_CODE = mapped_code.split(":")[0]
      row['code_type'] = "BLS_JOLTS"
      row['industry_code'] = JOLTS_CODE

    # NAICS
    else:
      row['code_type'] = "NAICS"
      row['industry_code'] = mapped_code
    
    return row

  jolts_df = jolts_df.apply(joltsCodesMap, axis=1)

  def mapRowToStatisticalVariable(row):
    base_stat_var = row['statistical_variable']
    code_type = row['code_type']
    industry_code = row['industry_code']

    return f"dcs:{base_stat_var}_{code_type}{industry_code}"

  # Build map to StatisticalVariable
  jolts_df['SeasonalAdjustment'] = jolts_df['seasonal'].apply(lambda adjustment: "Adjusted" if adjustment == "S" else "Unadjusted")
  jolts_df['StatisticalVariable'] = jolts_df.apply(mapRowToStatisticalVariable, axis=1)
  jolts_df['Value'] = jolts_df['value']

  return jolts_df, schema_mapping


def createBLSNodes():
  BLS_JOLTS_ENUM = """
  Node: dcid:BLS_JOLTSEnum
  typeOf: Class
  subClassOf: Enumeration
  description: Combinations of NAICS codes used by BLS JOLTs.
  name: BLS_JOLTSEnum
  """

  TEMPLATE_BLS = """
  Node: dcid:BLS_JOLTS/{JOLTS_CODE}
  typeOf: BLS_JOLTSEnum
  name: {JOLTS_NAME}
  """

  with open("BLSJolts_StatisticalVariables.mcf", "w+", newline="") as f_out:
    f_out.write(BLS_JOLTS_ENUM)

    for _, new_code in CODE_MAPPINGS.items():
      if ":" in new_code:
        jolts_code, jolts_name = new_code.split(":")
        f_out.write(TEMPLATE_BLS.format_map({"JOLTS_CODE": jolts_code, "JOLTS_NAME": jolts_name}))

### Step 3) Create StatisticalVariables  (6 job variables * 28 industries * 2 adjustments)
def createStatisticalVariables(jolts_df, schema_mapping):
  TEMPLATE_STAT_VAR = """
  Node: dcid:{STAT_CLASS}_{CODE_TYPE}{INDUSTRY}
  typeOf: StatisticalVariable
  populationType: {POPULATION}
  statType: dcs:measuredValue
  measuredProperty: dcs:count
  naics: dcid:{CODE_TYPE}/{INDUSTRY}
  turnoverType: dcs:{TURNOVER_TYPE}
  """

  # Map industry and seasonal adjustment to statistical variable name
  INDUSTRY_CODE_TYPES = ["NAICS", "BLS_JOLTS"]
  ADJUSTED_TYPES = [("Adjusted", "BLSSeasonallyAdjusted"), ("Unadjusted", "BLSSeasonallyUnadjusted")]

  # Output the schema mapping to a new file
  with open("BLSJolts_StatisticalVariables.mcf", "a+", newline="") as f_out:
    for schema_name, pop_type, sep_type, _ in schema_mapping:

      for industry_code_type in INDUSTRY_CODE_TYPES:
        unique_industries = list(jolts_df.query(f"code_type == '{industry_code_type}'")['industry_code'].unique())

        for industry_code in unique_industries:
          for adjusted_dcid_map, adjusted_schema in ADJUSTED_TYPES:
            # Create new schema object
            stat_var_schema = TEMPLATE_STAT_VAR

            # Remove separation type entry if not includes
            if sep_type == "":
              stat_var_schema = stat_var_schema.replace("turnoverType: dcs:{TURNOVER_TYPE}", "")

            # Replace all other fields
            stat_var_schema = stat_var_schema.replace("{STAT_CLASS}", schema_name)   \
                                            .replace("{INDUSTRY}", industry_code)   \
                                            .replace("{CODE_TYPE}", industry_code_type)   \
                                            .replace("{ADJUSTMENT}", adjusted_dcid_map)   \
                                            .replace("{BLS_ADJUSTMENT}", adjusted_schema)   \
                                            .replace("{POPULATION}", pop_type)      \
                                            .replace("{TURNOVER_TYPE}", sep_type)

          f_out.write(stat_var_schema)

def main(argv):
  # Download and clean data
  jolts_df, schema_mapping = generateCleanedDataframe()

  # Output final cleaned CSV
  FINAL_COLUMNS = ['Date', 'StatisticalVariable', 'SeasonalAdjustment', 'Value']
  output_csv = jolts_df.loc[:, FINAL_COLUMNS]
  output_csv.to_csv("BLSJolts.csv", index=False, encoding="utf-8")

  # Create new JOLTS Nodes
  createBLSNodes()

  # Create and output Statistical Variables
  createStatisticalVariables(jolts_df, schema_mapping)

if __name__ == '__main__':
  app.run(main)