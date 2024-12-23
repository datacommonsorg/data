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

Download the requirements.txt via pip and execute the file with Python 3.

Dataset being processed: https://download.bls.gov/pub/time.series/jt/
"""
import sys
import os
import textwrap
from absl import app
from absl import logging
from absl import flags
import time
import pandas as pd
import requests
from map_config import _dcid_map
import fileinput

_FLAGS = flags.FLAGS
flags.DEFINE_string('mode', '', 'Options: download or process')

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
    """Fetches and combines BLS Jolts data sources, with retry logic for file downloads.
    
    Downloads detailed series information from the entire JOLTS dataset.
    Each of the files is read, combined into a single dataframe, and processed.
    
    Returns:
        jolts_df: The 6 job data categories by industry, year, and adjustment, as a dataframe.
        schema_mapping: List of tuples that contains information for each dataset.
    """
    
    header = {'User-Agent': 'support@datacommons.org'}
    max_retry = 5
    
    def download_with_retries(url, retries=max_retry):
        """Download file with retry logic."""
        retry_count = 0
        while retry_count <= retries:
            try:
                data = pd.read_csv(url, storage_options=header, sep="\\s+")
                return data
            except Exception as e:
                logging.error(f"Error downloading {url}, retrying... ({retry_count + 1}/{retries})")
                time.sleep(5)
                retry_count += 1
                if retry_count > retries:
                    logging.fatal(f"Error downloading {url} after {retries} retries.")
                    raise e
    
    # Download and process series description
    try:
        series_desc = pd.read_csv(
            "https://download.bls.gov/pub/time.series/jt/jt.series",
            storage_options=header,
            converters={'industry_code': str},
            sep="\\t"
        )
        series_desc.columns = [
            'series_id', 'seasonal', 'industry_code', 'state_code', 'area_code',
            'sizeclass_code', 'dataelement_code', 'ratelevel_code',
            'footnote_codes', 'begin_year', 'begin_period', 'end_year', 'end_period'
        ]
        series_desc["series_id"] = series_desc["series_id"].apply(lambda x: x.strip())
        series_desc.to_csv("jolts_input_jt_series.csv")
        series_desc = series_desc.set_index("series_id")
    except Exception as e:
        logging.fatal(f"Failed to download series description: {e}")
        return
    
    # Download and process other datasets with retries
    try:
        job_openings = download_with_retries("https://download.bls.gov/pub/time.series/jt/jt.data.2.JobOpenings")
        job_openings.to_csv("jolts_input_jt_job_openings.csv")
    except Exception as e:
        logging.fatal(f"Failed to download job openings data: {e}")
        return

    try:
        job_hires = download_with_retries("https://download.bls.gov/pub/time.series/jt/jt.data.3.Hires")
        job_hires.to_csv("jolts_input_jt_job_hires.csv")
    except Exception as e:
        logging.fatal(f"Failed to download job hires data: {e}")
        return

    try:
        total_seps = download_with_retries("https://download.bls.gov/pub/time.series/jt/jt.data.4.TotalSeparations")
        total_seps.to_csv("jolts_input_jt_totlal_separations.csv")
    except Exception as e:
        logging.fatal(f"Failed to download total separations data: {e}")
        return

    try:
        total_quits = download_with_retries("https://download.bls.gov/pub/time.series/jt/jt.data.5.Quits")
        total_quits.to_csv("jolts_input_jt_total_quits.csv")
    except Exception as e:
        logging.fatal(f"Failed to download total quits data: {e}")
        return

    try:
        total_layoffs = download_with_retries("https://download.bls.gov/pub/time.series/jt/jt.data.6.LayoffsDischarges")
        total_layoffs.to_csv("jolts_input_jt_total_layoffs.csv")
    except Exception as e:
        logging.fatal(f"Failed to download total layoffs data: {e}")
        return

    try:
        total_other_seps = download_with_retries("https://download.bls.gov/pub/time.series/jt/jt.data.7.OtherSeparations")
        total_other_seps.to_csv("jolts_input_jt_total_other_separations.csv")
    except Exception as e:
        logging.fatal(f"Failed to download other separations data: {e}")
        return
    
    # Additional information about each dataframe.
    schema_mapping = [
        ("Count_JobPosting", "schema:JobPosting", "", job_openings),
        ("Count_Worker_Hire", "dcs:BLSWorker", "Hire", job_hires),
        ("Count_Worker_Separation", "dcs:BLSWorker", "Separation", total_seps),
        ("Count_Worker_VoluntarySeparation", "dcs:BLSWorker", "VoluntarySeparation", total_quits),
        ("Count_Worker_InvoluntarySeparation", "dcs:BLSWorker", "InvoluntarySeparation", total_layoffs),
        ("Count_Worker_OtherSeparation", "dcs:BLSWorker", "OtherSeparation", total_other_seps),
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
        jolts_df = jolts_df._append(df)

    # Drop non-monthly data and throw away slice.
    jolts_df = jolts_df.query("period != 'M13'").copy()

    # Change date to ISO format (YYYY-MM).
    def period_year_to_iso_8601(row):
        month = row['period'].lstrip("M")
        year = row['year']
        return f"{year}-{month}"

    jolts_df['Date'] = jolts_df.apply(period_year_to_iso_8601, axis=1)

    # Add relevant columns from series information.
    series_cols = [
        'industry_code', 'state_code', 'seasonal', 'ratelevel_code',
        'sizeclass_code'
    ]

    jolts_df = jolts_df.merge(series_desc[series_cols],
                              left_on=["series_id"],
                              right_index=True)
    jolts_df.to_csv("before_query.csv", index=False)

    # Drop rate data, preliminary data, and non-national data.
    jolts_df = jolts_df.query("ratelevel_code == 'L'")
    jolts_df = jolts_df.query("footnote_codes != 'P'")
    jolts_df = jolts_df.query("state_code == '00'")
    jolts_df = jolts_df.query('sizeclass_code == 0')
    jolts_df.to_csv("after_query.csv", index=False)

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
            f"dcs:{base_stat_var}_NAICS{industry_code}_{seasonal_adjustment}")

    # Build map to Statistical Variable.
    jolts_df['seasonal_adjustment'] = jolts_df['seasonal'].apply(
        lambda adj: "Adjusted" if adj == "S" else "Unadjusted")
    jolts_df['StatisticalVariable'] = jolts_df.apply(row_to_stat_var, axis=1)
    for old, new in _dcid_map.items():
        jolts_df['StatisticalVariable'] = jolts_df[
            'StatisticalVariable'].str.replace(old, new, regex=False)
    jolts_df['Value'] = jolts_df['value']

    return jolts_df, schema_mapping


def process(jolts_df, schema_mapping):
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
    Node: dcid:{STAT_CLASS}_NAICS{INDUSTRY}_{ADJUSTMENT}
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

    try:
        # Output the schema mapping to a new file.
        with open("BLSJolts_StatisticalVariables.mcf", "w+", newline="") as f_out:
            logging.info("Started writing statistical variable schemas to 'BLSJolts_StatisticalVariables.mcf'.")
            for schema_name, pop_type, job_change_event, _ in schema_mapping:
                for industry_code in list(jolts_df['industry_code'].unique()):
                    for adjusted_dcid_map, adjusted_schema in adjustment_types:
                        if adjusted_schema == "dcs:BLSSeasonallyAdjusted":
                            adjusted_schema = "dcs:Adjusted"
                        else:
                            adjusted_schema = "dcs:Unadjusted"

                        # Create new schema object.
                        stat_var_schema = textwrap.dedent(template_stat_var)

                        # Remove jobChangeEvent if not provided.
                        if job_change_event == "":
                            stat_var_schema = (stat_var_schema.replace(
                                "jobChangeEvent: dcs:{JOB_CHANGE_EVENT}\n", ""))

                        # Replace all placeholders with the actual values.
                        try:
                            f_out.write(
                                stat_var_schema.replace(
                                    "{STAT_CLASS}", schema_name).replace(
                                    "{INDUSTRY}", industry_code).replace(
                                    "{ADJUSTMENT}", adjusted_dcid_map).replace(
                                    "{BLS_ADJUSTMENT}", adjusted_schema).replace(
                                    "{POPULATION}", pop_type).replace(
                                    "{JOB_CHANGE_EVENT}", job_change_event)
                            )                            
                        except Exception as e:
                            logging.error(f"Error writing schema for {schema_name}, {industry_code}, {adjusted_dcid_map}: {e}")
                            continue  # Skip to the next item if writing fails

            logging.info("Finished writing all statistical variable schemas.")
    except Exception as e:
        logging.error(f"Error processing BLS Jolts data or writing to file: {e}")


def main(_):
    mode = _FLAGS.mode

    if mode == "download" or mode == "":
        logging.info("Downloading files...")
        generate_cleaned_dataframe()  # This function handles file download
        logging.info("Download completed!")

    if mode == "process" or mode == "":
        logging.info("Processing data...")
        jolts_df, schema_mapping = generate_cleaned_dataframe()
        # Process and output final cleaned CSV and MCF
        final_columns = ['Date', 'StatisticalVariable', 'Value']
        jolts_df.loc[:, final_columns].to_csv("BLSJolts.csv", index=False, encoding="utf-8")
        process(jolts_df, schema_mapping)
        logging.info("Process completed!")


if __name__ == '__main__':
    app.run(main)
