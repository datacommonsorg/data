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


### Step 2) Create Statistical Variable Schemas
SAMPLE_STAT_VAR = """
Node: dcid:{STAT_CLASS}
typeOf: StatisticalVariable
populationType: {POPULATION}
statType: dcs:measuredValue
measuredProperty: dcs:count
turnoverType: dcs:{TURNOVER_TYPE}
"""

# StatVarName, PopulationType, TurnoverType (if present), corresponding dataframe
schema_mapping = [
  ("NumJobOpening", "JobPosting", "", job_openings),
  ("NumJobHire", "JobHire", "", job_hires),
  ("Turnover", "LaborTurnover", "", total_seps),
  ("NumVoluntarySeparation", "LaborTurnover", "VoluntarySeparation", total_quits),
  ("NumLayoff", "LaborTurnover", "Layoff", total_layoffs),
  ("NumOtherSeparation", "LaborTurnover", "OtherSeparation", total_other_seps),
]

# Output the schema mapping to a new file
with open("BLSJolts_StatisticalVariables.mcf", "w", newline="") as f_out:
  for schema_name, pop_type, sep_type, _ in schema_mapping:
    # Create new schema object
    stat_var_schema = SAMPLE_STAT_VAR

    # Remove separation type entry if not includes
    if sep_type == "":
      stat_var_schema = stat_var_schema.replace("turnoverType: dcs:{TURNOVER_TYPE}", "")

    # Replace all other fields
    stat_var_schema = stat_var_schema.replace("{STAT_CLASS}", schema_name)   \
                                    .replace("{POPULATION}", pop_type)      \
                                    .replace("{TURNOVER_TYPE}", sep_type)

    f_out.write(stat_var_schema)

    if OUTPUT_MCF_TO_CONSOLE:
      print(stat_var_schema)


### Step 3) Assemble cleaned csv
jolts_df = pd.DataFrame()

# Replace generic 'value' column in each dataset to match StatisticalVariable naming
for schema_name, _, _, df in schema_mapping:
  # Rename generic df to match StatisticalVariable 
  df[schema_name] = df['value']
  df = df.drop('value', axis=1)

  jolts_df = jolts_df.append(df)

# Drop non-monthly data
jolts_df = jolts_df.drop(jolts_df.query("period == 'M13'").index)

# Change data to ISO Format (YYYY-MM)
def period_year_to_iso_8601(row):
  month = row['period'].lstrip("M")
  year = row['year']
  return f"{year}-{month}"

jolts_df['Date'] = jolts_df.apply(period_year_to_iso_8601, axis=1)

# Add relevant columns from series information
jolts_df = jolts_df.merge(series_desc[['industry_code', 'region_code', 'seasonal', 'ratelevel_code']], left_on=["series_id"], right_index=True)

# Refactor industry
jolts_df['Industry'] = jolts_df['industry_code'].apply(lambda code: f"NAICS/{code}")

# Drop non-national data
jolts_df = jolts_df.drop(jolts_df.query("region_code != '00'").index)

# Now we need to combine the 6 rows for each data entry into a single row for the same data
columns_to_drop = ['series_id', 'year', 'period', 'industry_code', 'region_code', 'seasonal', 'ratelevel_code', 'footnote_codes']
adj_seasonal_df = jolts_df.query("seasonal == 'S' and ratelevel_code == 'L'").drop(columns_to_drop, axis=1)
unadj_seasonal_df = jolts_df.query("seasonal == 'U' and ratelevel_code == 'L'").drop(columns_to_drop, axis=1)

# Squash into single row 
adj_seasonal_df = adj_seasonal_df.groupby(['Date', 'Industry']).first().reset_index()
unadj_seasonal_df = unadj_seasonal_df.groupby(['Date', 'Industry']).first().reset_index()

# Recombine
adj_seasonal_df['seasonalAdjustment'] = 'BLSSeasonallyAdjusted'
unadj_seasonal_df['seasonalAdjustment'] = 'BLSSeasonallyUnadjusted'
jolts_df = pd.concat([adj_seasonal_df, unadj_seasonal_df], axis=0)

# Export as CSV
jolts_df.to_csv("BLSJolts.csv", index=False, encoding="utf-8")

### Step 3) Create Template MCF
BASE_MCFS = """
Node: E:BLSJolts->E0
typeOf: Country
dcid: country/USA

Node: E:BLSJolts->E1
typeOf: NAICSEnum
dcid: C:BLSJolts->Industry
"""

SAMPLE_TEMPLATE_MCF = """
Node: E:BLSJolts->E{NUM}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{STATVARMEASURED}
observationDate: C:BLSJolts->Date
observationPeriod: P1M
observationAbout: E:BLSJolts->E0
measurementMethod: C:BLSJolts->seasonalAdjustment
industry: E:BLSJolts->E1
value: C:BLSJolts->{STATVARMEASURED}
"""

with open('BLSJolts.tmcf', 'w', newline='') as f_out:
  f_out.write(BASE_MCFS)

  if OUTPUT_MCF_TO_CONSOLE:
    print(BASE_MCFS)

  for index, var in enumerate(schema_mapping):
    stat_var_name, _, _, _ = var
    updated_schema = SAMPLE_TEMPLATE_MCF
    updated_schema = updated_schema.replace("{NUM}", str(index+2)).replace("{STATVARMEASURED}", stat_var_name)
    f_out.write(updated_schema)

    if OUTPUT_MCF_TO_CONSOLE:
      print(updated_schema)