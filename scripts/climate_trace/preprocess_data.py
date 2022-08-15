"""This script processes climate trace data for ingestion into data commons.

It imports data from climate trace URLs, merges forest and non forest data,
extracts year from the dates and creates stat-vars for each sub-sector. It also
calculates values for the whole sector and appends them to the data set with
a stat-var representing the sector. The processed file is placed in the
output_files directory.
"""
from absl import app
from datetime import datetime
import numpy as np
import pandas as pd
import statvar_mapping


def _ImportDataFromURL(url):
    return pd.read_csv(url)


def _ExtractDate(dt_str):
    return datetime.strptime(dt_str, "%Y-%m-%d")


def MergeAndProcessData(forest_df, other_data_df):
    """Merge the two data frames and output processed data frames for country and sectors."""
    base_df = pd.concat([other_data_df, forest_df], ignore_index=True)
    column_list = [
        "country", "year", "statvar", "measurement_method", "Tonnes Co2e"
    ]
    # drop all rows with missing or zero values
    base_df["Tonnes Co2e"].replace('', np.nan, inplace=True)
    base_df.dropna(subset=["Tonnes Co2e"], inplace=True)
    base_df = base_df[base_df["Tonnes Co2e"] != 0]

    base_df["year"] = base_df["start"].apply(_ExtractDate).apply(
        lambda x: x.year)

    # Get per sector aggregates
    sector_df = base_df.groupby(["country", "year",
                                 "sector"])["Tonnes Co2e"].sum().reset_index()
    sector_df["statvar"] = (
        statvar_mapping.STATVAR_PREFIX +
        sector_df["sector"].apply(statvar_mapping.SECTOR_VAR_MAP.get))
    sector_df["measurement_method"] = statvar_mapping.MEASUREMENT_METHOD_SECTORS
    sector_df = sector_df[column_list]

    sub_sector_df = base_df
    sub_sector_df["statvar"] = (
        statvar_mapping.STATVAR_PREFIX +
        base_df["subsector"].apply(statvar_mapping.SUBSECTOR_VAR_MAP.get))
    sub_sector_df[
        "measurement_method"] = statvar_mapping.MEASUREMENT_METHOD_SECTORS
    sub_sector_df = sub_sector_df[column_list]

    # Get per country aggregates
    country_df = base_df.groupby(["country",
                                  "year"])["Tonnes Co2e"].sum().reset_index()
    country_df["statvar"] = statvar_mapping.STATVAR_COUNTRY_METRICS
    country_df[
        "measurement_method"] = statvar_mapping.MEASUREMENT_METHOD_COUNTRIES
    country_df = country_df[column_list]

    return pd.concat([sector_df, sub_sector_df, country_df], ignore_index=True)


def main(_):
    url = "https://api.climatetrace.org/emissions_by_subsector_timeseries?interval=year&since=2015&to=2020&download=csv"
    df = _ImportDataFromURL(url)
    # Climate trace import URL has a bug wherein it skips the forest category.
    # So adding and concatenating it separately
    forest_url = "https://api.climatetrace.org/emissions_by_subsector_timeseries?sector=forests&since=2015&to=2020&interval=year&download=csv"
    forest_df = _ImportDataFromURL(forest_url)
    final_df = MergeAndProcessData(forest_df, df)
    final_df.to_csv("./output_files/processed_data.csv", index=False)


if __name__ == "__main__":
    app.run(main)
