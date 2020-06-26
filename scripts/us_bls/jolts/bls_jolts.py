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

"""Fetches, cleans, and downloads BLS Jolts data into Data Commons Knowledge Graph.

Data is fetched from various data sources within the BLS site then combined and cleaned.
StatisticalVariables are generated and cleaned CSV is output.

Download the requirements.txt via pip and execute the file with Python 3.
"""

from absl import app
import pandas as pd
import urllib.request

# JOLTS dataset contains a mix of NAICS industry codes and custom BLS jolts aggregations
# Existing NAICS Codes are mapped directly
# Custom JOLTS codes include a colon distinguishing their new name 
CODE_MAPPINGS = {
 '000000': '000000:Total nonfarm', # New Code
 '100000': '10', 
 '110099': '110099:Mining and logging', # New Code
 '230000': '23', 
 '300000': '300000:Manufacturing', # New Code
 '320000': '320000:Durable goods manufacturing', # New Code
 '340000': '340000:Nondurable goods manufacturing', # New Code
 '400000': '400000:Trade, transportation, and utilities', # New Code
 '420000': '42',
 '440000': '44',
 '480099': '480099:Transportation warehousing, and utilities', # New Code
 '510000': '51',
 '510099': '510099:Financial activities', # New Code
 '520000': '52',
 '530000': '53',
 '540099': '540099:Professional and business services', # New Code
 '600000': '600000:Education and health services', # New Code
 '610000': '61',
 '620000': '62',
 '700000': '700000:Leisure and hospitality', # New Code
 '710000': '71',
 '720000': '72',
 '810000': '81',
 '900000': '900000:Government', # New Code
 '910000': '910000:Federal', # New Code
 '920000': '92',
 '923000': '923000:State and local government education', # New Code
 '929000': '929000:State and local government excluding education'# New Code
}

STATISTICAL_VARIABLE_FILE = "BLSJolts_StatisticalVariables.mcf"

### Step 1) Data Download
# Dataset being processed: https://download.bls.gov/pub/time.series/jt/
# Data split across several white space separate files that may have incomplete rows
def web_to_pandas(url, sep, expected_cols):
  """ Helper to load incomplete whitespace separated data file into pandas.

  The BLS JOLTS data, while regular, uses whitespace to indicate breaks between columns and
  may leave trailing entries completely blank. Pandas default read tools fails to handle these
  partial rows so we need to process them manually.

  Args:
    url: The URL of the resource to fetch
    sep: The separator between columns 
    expected_cols: Fetched columns are validated against this list

  Raises:
    URLError or HTTPError if the data import request fails 
    Assert failure if columns of fetched CSVs are not as expected
  """
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

def generate_cleaned_dataframe():
  """ Fetches and combines BLS Jolts data sources.

  Downloads detailed series information from the entire JOLTS dataset.
  Each of the files is read, combined into a single dataframe, and post-processed.

  Returns:
    jolts_df: A dataframe representing the 6 job data categories by industry, year, and seasonal adjustment
    schema_mapping: A list of tuples that contains information for each data set 
  """
  
  # Download series descriptions (used for seasonally adjusted status and industry code)
  expected_series_columns = ['series_id','seasonal', 'industry_code', 'region_code', 'dataelement_code', 'ratelevel_code', 'footnote_codes','begin_year', 'begin_period', 'end_year', 'end_period']
  series_desc = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.series", sep="\t", expected_cols=expected_series_columns)
  series_desc = series_desc.set_index("series_id")

  # Download various series datapoints -- find more info here https://download.bls.gov/pub/time.series/jt/jt.txt
  expected_job_columns = ['series_id', 'year', 'period', 'value', 'footnote_codes']
  job_openings = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.2.JobOpenings", sep="\t", expected_cols=expected_job_columns)
  job_hires = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.3.Hires", sep="\t", expected_cols=expected_job_columns)
  total_seps = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.4.TotalSeparations", sep="\t", expected_cols=expected_job_columns)
  total_quits = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.5.Quits", sep="\t", expected_cols=expected_job_columns)
  total_layoffs = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.6.LayoffsDischarges", sep="\t", expected_cols=expected_job_columns)
  total_other_seps = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.7.OtherSeparations", sep="\t", expected_cols=expected_job_columns)

  # Additional information about each dataframe
  # Tuple Format: Statistical Variable name, Stat Var population, Stat Var Job Change Type If Relevant, Dataframe for Stat Var 
  schema_mapping = [
    ("NumJobOpening", "schema:JobPosting", "", job_openings),
    ("NumJobHire", "dcs:BLSWorker", "Hire", job_hires),
    ("NumSeparation", "dcs:BLSWorker", "Separation", total_seps),
    ("NumVoluntarySeparation", "dcs:BLSWorker", "VoluntarySeparation", total_quits),
    ("NumInvoluntarySeparation", "dcs:BLSWorker", "InvoluntarySeparation", total_layoffs),
    ("NumOtherSeparation", "dcs:BLSWorker", "OtherSeparation", total_other_seps),
  ]

  # Combine datasets into a single dataframe including origin of data
  jolts_df = pd.DataFrame()
  columns_to_keep = ['series_id', 'year', 'period', 'value']

  for schema_name, population_type, job_change_event, df in schema_mapping:
    df = df.loc[:, columns_to_keep]
    df['statistical_variable'] = schema_name
    df['job_change_event'] = job_change_event
    df['population_type'] = population_type
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
  jolts_df = jolts_df.query("ratelevel_code == 'L'")

  # Drop non-national data
  jolts_df = jolts_df.query("region_code == '00'")

  # Map industries
  def jolts_code_map(row):
    """ Maps industry code used by BLS Jolts to NAICS or BLS aggregation """
    industry_code = row['industry_code']
    assert industry_code in CODE_MAPPINGS

    mapped_code = CODE_MAPPINGS[industry_code]

    # New Jolts code
    if ":" in mapped_code:
      JOLTS_CODE = mapped_code.split(":")[0]
      row['industry_code'] = "JOLTS_" + JOLTS_CODE

    # NAICS
    else:
      row['industry_code'] = mapped_code
    
    return row

  jolts_df = jolts_df.apply(jolts_code_map, axis=1)

  def map_row_to_statistical_variable(row):
    """ Maps a row of the dataframe to the Statistical Variable that describes it """
    base_stat_var = row['statistical_variable']
    industry_code = row['industry_code']

    return f"dcs:{base_stat_var}_NAICS_{industry_code}"

  # Build map to Statistical Variable
  jolts_df['SeasonalAdjustment'] = jolts_df['seasonal'].apply(lambda adjustment: "Adjusted" if adjustment == "S" else "Unadjusted")
  jolts_df['StatisticalVariable'] = jolts_df.apply(map_row_to_statistical_variable, axis=1)
  jolts_df['Value'] = jolts_df['value']

  return jolts_df, schema_mapping


def create_bls_nodes():
  """ Creates a list of BLS_JOLTS MCFs for JOLTS aggregations.

  Downloads detailed series information from the entire JOLTS dataset.
  Each of the files is read, combined into a single dataframe, and post-processed.
  This method creates the statistical variables file and writes to it.
  """

  required_new_nodes = """
Node: dcid:jobChangeEvent
name: "jobChangeEvent"
typeOf: schema:Property
domain: schema:Person
range: dcs:JobChangeEventEnum

Node: dcid:JobChangeEventEnum
name: "JobChangeEventEnum"
description: "Describes different job change events that may happen to workers" 
typeOf: dcs:Class
subClassOf: Enumeration

Node: dcid:Hired
name: "Hired"
description: "Describes a worker that was hired to a company"
typeOf: dcid:JobChangeEventEnum

Node: dcid:Separated
name: "Separated"
description: "Describes a worker that was separated from a company"
typeOf: dcid:JobChangeEventEnum

Node: dcid:VoluntarySeparation
name: "VoluntarySeparation"
description: "Describes a worker that voluntarily separated from a company"
typeOf: dcid:JobChangeEventEnum
specializationOf: dcs:Separated

Node: dcid:InvoluntarySeparation
name: "InvoluntarySeparation"
description: "Describes a worker that involuntarily separated from a company"
typeOf: dcid:JobChangeEventEnum
specializationOf: dcs:Separated

Node: dcid:OtherSeparation
name: "OtherSeparation"
description: "Describes a worker that separated from a company for other reasons"
typeOf: dcid:JobChangeEventEnum
specializationOf: dcs:Separated
  """

  template_bls = """
Node: dcid:NAICS/JOLTS_{JOLTS_CODE}
typeOf: NAICSEnum
name: {JOLTS_NAME}
  """

  with open(STATISTICAL_VARIABLE_FILE, "w+", newline="") as f_out:
    f_out.write(required_new_nodes)

    for _, new_code in CODE_MAPPINGS.items():
      if ":" in new_code:
        jolts_code, jolts_name = new_code.split(":")
        f_out.write(template_bls.format_map({"JOLTS_CODE": jolts_code, "JOLTS_NAME": jolts_name}))

def create_statistical_variables(jolts_df, schema_mapping):
  """ Creates Statistical Variable nodes.

    A new statistical industry is needed for each of the 6 job variables and for every industry
    The industry codes may be either NAICS or BLS_JOLTS aggregations. The schema_mapping is used 
    for additional information for each of the 6 job variables. These new variables are written
    to the statistical variables mcf file.

    Args:
      jolts_df: The dataframe of BLS Jolts data created by generate_cleaned_dataframe
      schema_mapping: The schema mapping created by generate_cleaned_dataframe
  """

  template_stat_var = """
  Node: dcid:{STAT_CLASS}_NAICS_{INDUSTRY}
  typeOf: StatisticalVariable
  populationType: {POPULATION}
  jobChangeEvent: dcs:{JOB_CHANGE_EVENT}
  statType: dcs:measuredValue
  measuredProperty: dcs:count
  naics: dcid:NAICS/{INDUSTRY}
  """

  # Map industry and seasonal adjustment to statistical variable name
  adjustment_types = [("Adjusted", "BLSSeasonallyAdjusted"), ("Unadjusted", "BLSSeasonallyUnadjusted")]

  # Output the schema mapping to a new file
  with open(STATISTICAL_VARIABLE_FILE, "a+", newline="") as f_out:
    for schema_name, pop_type, job_change_event, _ in schema_mapping:

        unique_industries = list(jolts_df['industry_code'].unique())

        for industry_code in unique_industries:
          for adjusted_dcid_map, adjusted_schema in adjustment_types:
            # Create new schema object
            stat_var_schema = template_stat_var

            # Remove separation type entry if not includes
            if job_change_event == "":
              stat_var_schema = stat_var_schema.replace("jobChangeEvent: dcs:{JOB_CHANGE_EVENT}\n", "")

            # Replace all other fields
            stat_var_schema = stat_var_schema.replace("{STAT_CLASS}", schema_name)   \
                                            .replace("{INDUSTRY}", industry_code)   \
                                            .replace("{ADJUSTMENT}", adjusted_dcid_map)   \
                                            .replace("{BLS_ADJUSTMENT}", adjusted_schema)   \
                                            .replace("{POPULATION}", pop_type)      \
                                            .replace("{JOB_CHANGE_EVENT}", job_change_event)  

          f_out.write(stat_var_schema)

def main(argv):
  """ Executes the downloading, preprocessing, and outputting of required MCF and CSV for JOLTS data.

    Args
      argv: Not used. Required by absl run.
  """

  # Download and clean data
  jolts_df, schema_mapping = generate_cleaned_dataframe()

  # Output final cleaned CSV
  final_columns = ['Date', 'StatisticalVariable', 'SeasonalAdjustment', 'Value']
  output_csv = jolts_df.loc[:, final_columns]
  output_csv.to_csv("BLSJolts.csv", index=False, encoding="utf-8")

  # Create new JOLTS nodes
  create_bls_nodes()

  # Create and output Statistical Variables
  create_statistical_variables(jolts_df, schema_mapping)

if __name__ == '__main__':
  app.run(main)
