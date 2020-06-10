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

import pandas as pd
import urllib.request
OUTPUT_MCF_TO_CONSOLE = True

### Step 1) Data Download
# Dataset being processed: https://download.bls.gov/pub/time.series/jt/
# Data split across several white space separate files that may have incomplete rows
def web_to_pandas(url, sep):
  '''
    Helper to load incomplete whitespace separated data file into pandas
  '''
  df = None
  remote_web_page = urllib.request.urlopen(url)

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

  return df

# Download series descriptions (used for seasonally adjusted status and industry code)
series_desc = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.series", sep="\t")
series_desc = series_desc.set_index("series_id")

# Download various series datapoints -- find more info here https://download.bls.gov/pub/time.series/jt/jt.txt
job_openings = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.2.JobOpenings", sep="\t")
job_hires = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.3.Hires", sep="\t")
total_seps = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.4.TotalSeparations", sep="\t")
total_quits = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.5.Quits", sep="\t")
total_layoffs = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.6.LayoffsDischarges", sep="\t")
total_other_seps = web_to_pandas("https://download.bls.gov/pub/time.series/jt/jt.data.7.OtherSeparations", sep="\t")

# Validate that these all downloaded correctly
def columns_match(df):
	EXPECTED_COLS = ['series_id', 'year', 'period', 'value', 'footnote_codes']

	# This returns an array for each column so we need to iterate
	matches = df.columns == EXPECTED_COLS
	return False not in matches

assert columns_match(job_openings)
assert columns_match(job_hires)
assert columns_match(total_seps)
assert columns_match(total_quits)
assert columns_match(total_layoffs)
assert columns_match(total_other_seps)

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

jolts_df['Date'] = jolts_df.apply(period_year_to_iso_8601, axis=1)

# Add relevant columns from series information
jolts_df = jolts_df.merge(series_desc[['industry_code', 'region_code', 'seasonal', 'ratelevel_code']], left_on=["series_id"], right_index=True)

# Drop rate data
jolts_df = jolts_df.drop(jolts_df.query("ratelevel_code != 'L'").index)

# Drop non-national data
jolts_df = jolts_df.drop(jolts_df.query("region_code != '00'").index)

# Map industry and seasonal adjustment to statistical variable name
UNIQUE_INDUSTRIES = list(jolts_df['industry_code'].unique())
SEPARATION_TYPES = ["Adjusted", "Unadjusted"]

def mapRowToStatisticalVariable(row):
  base_stat_var = row['statistical_variable']
  industry_code = row['industry_code']
  seasonal_adjustment = SEPARATION_TYPES[0] if row['seasonal'] == "S" else SEPARATION_TYPES[1]

  return f"dcs:{base_stat_var}_NAICS{industry_code}_{seasonal_adjustment}"

# Build map to StatisticalVariable
jolts_df['StatisticalVariable'] = jolts_df.apply(mapRowToStatisticalVariable, axis=1)
jolts_df['Value'] = jolts_df['value']

# Output final cleaned CSV
FINAL_COLUMNS = ['Date', 'StatisticalVariable', 'Value']
output_csv = jolts_df.loc[:, FINAL_COLUMNS]
output_csv.to_csv("BLSJolts.csv", index=False, encoding="utf-8")

### Step 3) Create StatisticalVariables  (6 job variables * 28 industries * 2 adjustments)
SAMPLE_STAT_VAR = """
Node: dcid:{STAT_CLASS}/NAICS{INDUSTRY}/{ADJUSTMENT}
typeOf: StatisticalVariable
populationType: {POPULATION}
statType: dcs:measuredValue
measuredProperty: dcs:count
turnoverType: dcs:{TURNOVER_TYPE}
"""

# Output the schema mapping to a new file
with open("BLSJolts_StatisticalVariables.mcf", "w", newline="") as f_out:
  for schema_name, pop_type, sep_type, _ in schema_mapping:
    for industry_code in UNIQUE_INDUSTRIES:
      for separation_type in SEPARATION_TYPES:
        # Create new schema object
        stat_var_schema = SAMPLE_STAT_VAR

        # Remove separation type entry if not includes
        if sep_type == "":
          stat_var_schema = stat_var_schema.replace("turnoverType: dcs:{TURNOVER_TYPE}", "")

        # Replace all other fields
        stat_var_schema = stat_var_schema.replace("{STAT_CLASS}", schema_name)   \
                                         .replace("{INDUSTRY}", industry_code)   \
                                         .replace("{ADJUSTMENT}", separation_type)   \
                                         .replace("{POPULATION}", pop_type)      \
                                         .replace("{TURNOVER_TYPE}", sep_type)

        f_out.write(stat_var_schema)

        if OUTPUT_MCF_TO_CONSOLE:
          print(stat_var_schema)

### Step 4) Create Template MCF
BASE_MCFS = """
Node: E:BLSJolts->E0
typeOf: Country
dcid: country/USA
"""

SAMPLE_TEMPLATE_MCF = """
Node: E:BLSJolts->E1
typeOf: dcs:StatVarObservation
variableMeasured: C:BLSJolts->StatisticalVariable
observationDate: C:BLSJolts->Date
observationPeriod: P1M
observationAbout: E:BLSJolts->E0
value: C:BLSJolts->Value
"""

with open('BLSJolts.tmcf', 'w', newline='') as f_out:
  f_out.write(BASE_MCFS)
  f_out.write(SAMPLE_TEMPLATE_MCF)

  if OUTPUT_MCF_TO_CONSOLE:
    print(BASE_MCFS)
    print(SAMPLE_TEMPLATE_MCF)