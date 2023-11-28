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
"""Fetches and cleans BLS Jolts data into Data Commons Knowledge Graph.

Data is fetched from various data sources within the BLS site
then combined and cleaned.

Statistical Variables are generated and cleaned CSV is output.

Download the requirements_all.txt via pip and execute the file with Python 3.

Dataset being processed: https://download.bls.gov/pub/time.series/jt/
"""
import textwrap
from absl import app
import pandas as pd

# JOLTS dataset contains both NAICS industry codes and BLS jolts aggregations.
# Existing NAICS Codes are mapped directly while
# custom JOLTS codes include a colon distinguishing their new name.
_CODE_MAPPINGS = {
    '000000': '000000:Total nonfarm',  # New Code
    '100000': '10',
    '110099': '110099:Mining and logging',  # New Code
    '230000': '23',
    '300000': '300000:Manufacturing',  # New Code
    '320000': '320000:Durable goods manufacturing',  # New Code
    '340000': '340000:Nondurable goods manufacturing',  # New Code
    '400000': '400000:Trade, transportation, and utilities',  # New Code
    '420000': '42',
    '440000': '44',
    '480099': '480099:Transportation warehousing, and utilities',  # New Code
    '510000': '51',
    '510099': '510099:Financial activities',  # New Code
    '520000': '52',
    '530000': '53',
    '540099': '540099:Professional and business services',  # New Code
    '600000': '600000:Education and health services',  # New Code
    '610000': '61',
    '620000': '62',
    '700000': '700000:Leisure and hospitality',  # New Code
    '710000': '71',
    '720000': '72',
    '810000': '81',
    '900000': '900000:Government',  # New Code
    '910000': '910000:Federal',  # New Code
    '920000': '92',
    '923000': '923000:State and local government education',  # New Code
    '929000':
        '929000:State and local government excluding education'  # New Code
}


def generate_cleaned_dataframe():
    """Fetches and combines BLS Jolts data sources.

  Downloads detailed series information from the entire JOLTS dataset.
  Each of the files is read, combined into a single dataframe, and processed.

  Returns:
    jolts_df: The 6 job data categories by industry, year, and adjustment,
        as a data frame.
    schema_mapping: List of tuples that contains information for each dataset.
  """
    # Series descriptions are used for adjustment status and industry code.
    exp_series_columns = [
        'series_id', 'seasonal', 'industry_code', 'region_code',
        'dataelement_code', 'ratelevel_code', 'footnote_codes', 'begin_year',
        'begin_period', 'end_year', 'end_period'
    ]

    series_desc = pd.read_csv(
        "https://download.bls.gov/pub/time.series/jt/jt.series",
        converters={'industry_code': str},
        sep="\\s+")
    assert len(series_desc.columns) == len(exp_series_columns)
    assert (series_desc.columns == exp_series_columns).all()
    series_desc = series_desc.set_index("series_id")

    # Download various series datapoints
    job_openings = pd.read_csv(
        "https://download.bls.gov/pub/time.series/jt/jt.data.2.JobOpenings",
        sep="\\s+")
    job_hires = pd.read_csv(
        "https://download.bls.gov/pub/time.series/jt/jt.data.3.Hires",
        sep="\\s+")
    total_seps = pd.read_csv(
        "https://download.bls.gov/pub/time.series/jt/jt.data.4.TotalSeparations",  # pylint: disable=line-too-long
        sep="\\s+")
    total_quits = pd.read_csv(
        "https://download.bls.gov/pub/time.series/jt/jt.data.5.Quits",
        sep="\\s+")
    total_layoffs = pd.read_csv(
        "https://download.bls.gov/pub/time.series/jt/jt.data.6.LayoffsDischarges",  # pylint: disable=line-too-long
        sep="\\s+")
    total_other_seps = pd.read_csv(
        "https://download.bls.gov/pub/time.series/jt/jt.data.7.OtherSeparations",  # pylint: disable=line-too-long
        sep="\\s+")
    # Additional information about each dataframe.
    # Tuple Format: Statistical Variable name, Stat Var population,
    #   Stat Var Job Change Type If Relevant, Dataframe for Stat Var.
    schema_mapping = [
        ("NumJobOpening", "schema:JobPosting", "", job_openings),
        ("NumJobHire", "dcs:BLSWorker", "Hire", job_hires),
        ("NumSeparation", "dcs:BLSWorker", "Separation", total_seps),
        ("NumVoluntarySeparation", "dcs:BLSWorker", "VoluntarySeparation",
         total_quits),
        ("NumInvoluntarySeparation", "dcs:BLSWorker", "InvoluntarySeparation",
         total_layoffs),
        ("NumOtherSeparation", "dcs:BLSWorker", "OtherSeparation",
         total_other_seps),
    ]
    # Combine datasets into a single dataframe including origin of data.
    jolts_df = pd.DataFrame()
    job_columns = ['series_id', 'year', 'period', 'value', 'footnote_codes']

    for schema_name, population_type, job_change_event, df in schema_mapping:
        # Assert columns are as expected.
        assert len(df.columns) == len(job_columns)
        assert (df.columns == job_columns).all()

        # Add to general dataframe.
        df = df.loc[:, job_columns]
        df.loc[:, 'statistical_variable'] = schema_name
        df.loc[:, 'job_change_event'] = job_change_event
        df.loc[:, 'population_type'] = population_type
        jolts_df = jolts_df.append(df)

    # Drop non-monthly data and throw away slice.
    jolts_df = jolts_df.query("period != 'M13'").copy()

    # Change date to ISO format (YYYY-MM).
    def period_year_to_iso_8601(row):
        month = row['period'].lstrip("M")
        year = row['year']
        return f"{year}-{month}"

    jolts_df['Date'] = jolts_df.apply(period_year_to_iso_8601, axis=1)

    # Add relevant columns from series information.
    series_cols = ['industry_code', 'region_code', 'seasonal', 'ratelevel_code']
    jolts_df = jolts_df.merge(series_desc[series_cols],
                              left_on=["series_id"],
                              right_index=True)

    # Drop rate data, preliminary data, and non-national data.
    jolts_df = jolts_df.query("ratelevel_code == 'L'")
    jolts_df = jolts_df.query("footnote_codes != 'P'")
    jolts_df = jolts_df.query("region_code == '00'")

    # Map industries.
    def jolts_code_map(row):
        """Maps industry code used by BLS Jolts to NAICS or BLS aggregation."""
        industry_code = row['industry_code']
        assert industry_code in _CODE_MAPPINGS, f"{industry_code} not mapped!"
        mapped_code = _CODE_MAPPINGS[industry_code]

        if ":" in mapped_code:
            # New Jolts code have a prepended JOLTS id.
            row['industry_code'] = "JOLTS_" + mapped_code.split(":")[0]
        else:
            # Just map original NAICS codes directly.
            row['industry_code'] = mapped_code

        return row

    jolts_df = jolts_df.apply(jolts_code_map, axis=1)

    def row_to_stat_var(row):
        """Maps a row of df to the Statistical Variable that describes it."""
        base_stat_var = row['statistical_variable']
        industry_code = row['industry_code']
        seasonal_adjustment = row['seasonal_adjustment']

        return (
            f"dcs:{base_stat_var}_NAICS_{industry_code}_{seasonal_adjustment}")

    # Build map to Statistical Variable.
    jolts_df['seasonal_adjustment'] = jolts_df['seasonal'].apply(
        lambda adj: "Adjusted" if adj == "S" else "Unadjusted")
    jolts_df['StatisticalVariable'] = jolts_df.apply(row_to_stat_var, axis=1)
    jolts_df['Value'] = jolts_df['value']

    return jolts_df, schema_mapping


def create_statistical_variables(jolts_df, schema_mapping):
    """Creates Statistical Variable nodes.

    A new statistical industry is needed for each of the 6 job variables
    and for every industry.
    The industry codes may be either NAICS or BLS_JOLTS aggregations.
    The schema_mapping is used for additional information for
    each of the 6 job variables. These new variables are written
    to the statistical variables mcf file.

    Args:
      jolts_df: The df of BLS Jolts data created by generate_cleaned_dataframe.
      schema_mapping: The schema mapping created by generate_cleaned_dataframe.
  """
    template_stat_var = """
  Node: dcid:{STAT_CLASS}_NAICS_{INDUSTRY}_{ADJUSTMENT}
  typeOf: dcs:StatisticalVariable
  populationType: {POPULATION}
  jobChangeEvent: dcs:{JOB_CHANGE_EVENT}
  statType: dcs:measuredValue
  measuredProperty: dcs:count
  measurementQualifier: {BLS_ADJUSTMENT}
  naics: dcid:NAICS/{INDUSTRY}
  """
    # Map industry and seasonal adjustment to statistical variable name.
    adjustment_types = [("Adjusted", "dcs:BLSSeasonallyAdjusted"),
                        ("Unadjusted", "dcs:BLSSeasonallyUnadjusted")]

    # Output the schema mapping to a new file.
    with open("BLSJolts_StatisticalVariables.mcf", "w+", newline="") as f_out:
        for schema_name, pop_type, job_change_event, _ in schema_mapping:
            for industry_code in list(jolts_df['industry_code'].unique()):
                for adjusted_dcid_map, adjusted_schema in adjustment_types:
                    # Create new schema object.
                    stat_var_schema = textwrap.dedent(template_stat_var)

                    # Remove separation type entry if not includes.
                    if job_change_event == "":
                        stat_var_schema = (stat_var_schema.replace(
                            "jobChangeEvent: dcs:{JOB_CHANGE_EVENT}\n", ""))

                    # Replace all other fields.
                    f_out.write(
                        stat_var_schema.replace(
                            "{STAT_CLASS}", schema_name).replace(
                                "{INDUSTRY}", industry_code).replace(
                                    "{ADJUSTMENT}", adjusted_dcid_map).replace(
                                        "{BLS_ADJUSTMENT}",
                                        adjusted_schema).replace(
                                            "{POPULATION}", pop_type).replace(
                                                "{JOB_CHANGE_EVENT}",
                                                job_change_event))


def main(_):
    """ Executes the downloading, preprocessing, and outputting of
  required MCF and CSV for JOLTS data.
  """
    # Download and clean data.
    jolts_df, schema_mapping = generate_cleaned_dataframe()

    # Output final cleaned CSV.
    final_columns = ['Date', 'StatisticalVariable', 'Value']
    jolts_df.loc[:, final_columns].to_csv("BLSJolts.csv",
                                          index=False,
                                          encoding="utf-8")

    # Create and output Statistical Variables.
    create_statistical_variables(jolts_df, schema_mapping)


if __name__ == '__main__':
    app.run(main)
