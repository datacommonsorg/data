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
'''
Generates the CSVs, StatisticalVariable MCFs, and template MCFs for importing
US Burea of Labor Statistics CPI-U, CPI-W, and C-CPI-U series into Data Commons.
Only monthly series for the US as a whole and not for parts of the US are
generated. The semi-annually series overlap with the monthly series so they
are not generated.

The script replies heavily on the CSVs provided by BLS that contain information,
such as whether the series are seasonally adjusted, about series of a
particular type, e.g., https://download.bls.gov/pub/time.series/cu/cu.series.
The DataFrames loaded from these CSVs are often referred to as "info_df"
in the script.

Running the script generates these files:
- CSVs
    - cpi_u.csv
    - cpi_w.csv
    - c_cpi_u.csv
- Node MCFs
    - cpi_u.mcf
        - Contains StatisticalVariables for CPI-U series.
    - cpi_w.mcf
    - c_cpi_u.mcf
    - pop_type_enums.mcf
        - Contains populationType enums for all three types of series.
    - unit_enums.mcf
        - Contains unit enums for all three types of series.
- Template MCFs
    - cpi_u.tmcf
        - Contains the template MCF for CPI-U series.
    - cpi_w.tmcf
    - c_cpi_u.tmcf

The CSVs have these columns:
- value
    - Observation values for the series.
- date
    - Dates of the observations. For monthly series, the dates are of the form
      "YYYY-MM" For semi-annually series, the format is the same and the dates
      are the last months of the half years, i.e., June and December.
- duration
    - Observation periods of the series. The durations are "P1M" and "P6M" for
      monthly series and semi-annually series respectively.
- statvar
    - DCIDs of the StatisticalVariables meausred by the series.
- unit
    - DCIDs of the units of the observations.

Usage: python3 generate_csv_mcf.py
'''

import re
import io
import dataclasses
from typing import Set, List, Tuple, Iterable

import requests
import frozendict
import pandas as pd

_PREFIX = "https://download.bls.gov/pub/time.series/"

# From series types to lists of CSV URLs containing series of those types
SERIES_TYPES_TO_DATA_URLS = frozendict.frozendict({
    "cpi_u": (f"{_PREFIX}/cu/cu.data.1.AllItems",
              f"{_PREFIX}/cu/cu.data.11.USFoodBeverage",
              f"{_PREFIX}/cu/cu.data.12.USHousing",
              f"{_PREFIX}/cu/cu.data.13.USApparel",
              f"{_PREFIX}/cu/cu.data.14.USTransportation",
              f"{_PREFIX}/cu/cu.data.15.USMedical",
              f"{_PREFIX}/cu/cu.data.16.USRecreation",
              f"{_PREFIX}/cu/cu.data.17.USEducationAndCommunication",
              f"{_PREFIX}/cu/cu.data.18.USOtherGoodsAndServices",
              f"{_PREFIX}/cu/cu.data.20.USCommoditiesServicesSpecial"),
    "cpi_w": (f"{_PREFIX}/cw/cw.data.1.AllItems",
              f"{_PREFIX}/cw/cw.data.11.USFoodBeverage",
              f"{_PREFIX}/cw/cw.data.12.USHousing",
              f"{_PREFIX}/cw/cw.data.13.USApparel",
              f"{_PREFIX}/cw/cw.data.14.USTransportation",
              f"{_PREFIX}/cw/cw.data.15.USMedical",
              f"{_PREFIX}/cw/cw.data.16.USRecreation",
              f"{_PREFIX}/cw/cw.data.17.USEducationAndCommunication",
              f"{_PREFIX}/cw/cw.data.18.USOtherGoodsAndServices",
              f"{_PREFIX}/cw/cw.data.20.USCommoditiesServicesSpecial"),
    "c_cpi_u": (f"{_PREFIX}/su/su.data.1.AllItems",)
})

# From series types to URLs of CSVs describing the series
SERIES_TYPES_TO_INFO_URLS = frozendict.frozendict({
    "cpi_u": f"{_PREFIX}/cu/cu.series",
    "cpi_w": f"{_PREFIX}/cw/cw.series",
    "c_cpi_u": f"{_PREFIX}/su/su.series"
})

# From series types to URLs of CSVs containing mappings from
# item code to item name
SERIES_TYPES_TO_EXPENDITURE_TYPES_URLS = frozendict.frozendict({
    "cpi_u": f"{_PREFIX}/cu/cu.item",
    "cpi_w": f"{_PREFIX}/cw/cw.item",
    "c_cpi_u": f"{_PREFIX}/su/su.item"
})


@dataclasses.dataclass(frozen=True)
class SeriesInfo:
    """Information about a series. For descriptions of the fields, see
    Section 4 of {_PREFIX}/cu/cu.txt.
    """
    survey_abbreviation: str
    seasonal_code: str
    periodicity_code: str
    area_code: str
    item_code: str
    series_id: str

    def __post_init__(self):
        """Validates the fields after init."""
        self._validate()

    def _validate(self) -> None:
        """Validates the fields.

        Raises:
            ValueError: Some field(s) is invalid.
        """
        if (not self.series_id or len(self.series_id) < 11 or
                len(self.series_id) > 17):
            self._raise_validation_error("invalid series_id")
        if self.survey_abbreviation not in ("SU", "CU", "CW"):
            self._raise_validation_error(
                f"nvalid survey_abbreviation: {self.survey_abbreviation}")
        if self.seasonal_code not in ("S", "U"):
            self._raise_validation_error(
                f"invalid survey_abbreviation: {self.survey_abbreviation}")
        if self.periodicity_code not in ("R", "S"):
            self._raise_validation_error(
                f"invalid periodicity_code: {self.periodicity_code}")
        if (not self.area_code or len(self.area_code) != 4):
            self._raise_validation_error(f"invalid area_code: {self.area_code}")

    def _raise_validation_error(self, message: str) -> None:
        raise ValueError(f"{self.series_id}: {message}")

    def is_us(self) -> bool:
        """Returns if the series is for US as a whole and
        not for parts of US."""
        return self.area_code == "0000"

    def is_monthly(self) -> bool:
        """Returns if the series is monthly."""
        return self.periodicity_code == "R"

    def is_semiannually(self) -> bool:
        """Returns if the series is semi-annually."""
        return self.periodicity_code == "S"

    def get_mmethod(self) -> str:
        """Returns the DCID of the measurement method for this series."""
        if self.survey_abbreviation == "SU":
            return "BLSChained"
        return "BLSUnchained"

    def get_pop_type(self) -> str:
        """Returns the DCID of the population type for this series."""
        return f"BLSItem/{self.item_code}"

    def get_consumer(self) -> str:
        """Returns the DCID of the consumer for this series."""
        if self.survey_abbreviation == "CW":
            return "UrbanWageEarnerAndClericalWorker"
        return "UrbanConsumer"

    def get_mqual(self) -> str:
        """Returns the DCID of the measurement qualifier for this series."""
        if self.seasonal_code == "S":
            return "BLSSeasonallyAdjusted"
        return "BLSSeasonallyUnadjusted"

    def get_statvar(self) -> str:
        """Returns the DCID of the statistical variable for this series."""
        return ("ConsumerPriceIndex_"
                f"{self.get_pop_type()}_"
                f"{self.get_consumer()}_"
                f"{self.get_mqual()}")

    def get_unit(self, info_df: pd.DataFrame) -> Tuple[str, str]:
        """Returns the DCID of the unit for this series and a description
        of the unit.

        Args:
            info_df: DataFrame containing information about the series.

        Raises:
            ValueError: The base period obtained from the dataframe is invalid.
        """
        row = info_df[info_df["series_id"] == self.series_id]
        num_rows = row.shape[0]
        if num_rows != 1:
            self._raise_validation_error(f"found {num_rows} in info_df")
        base = row["base_period"].iloc[0]

        # base is described in one of three ways:
        # "YYYY=100", e.g., "1967=100",
        # "YYYY-YY=100", e.g., "1982-84=100", or
        # "MONTH YYYY=100", e.g., "DECEMBER 2009=100"
        if not re.fullmatch(r"\d{4}=100|\d{4}-\d{2}=100|[A-Z]+ \d{4}=100",
                            base):
            self._raise_validation_error(f"invalid base_period: {base}")
        if " " in base:
            month, year, _ = re.split(r"[ =]", base)
            month = month.lower().title()
            return (f"IndexPointBasePeriod{month}{year}Equals100",
                    f"The reference base is {month} {year} equals 100.")
        elif "-" in base:
            year_start, year_end, _ = re.split(r"[-=]", base)
            year_end = year_start[:2] + year_end
            return (
                f"IndexPointBasePeriod{year_start}To{year_end}Equals100",
                f"The reference base is {year_start} to {year_end} equals 100.")
        year, _ = base.split("=")
        return (f"IndexPointBasePeriod{year}Equals100",
                f"The reference base is {year} equals 100.")


def parse_series_id(series_id: str) -> SeriesInfo:
    """Parses a series ID to a SeriesInfo. See Section 4 of
    {_PREFIX}/cu/cu.txt
    for a breakdown of series IDs."""
    return SeriesInfo(survey_abbreviation=series_id[:2],
                      seasonal_code=series_id[2],
                      periodicity_code=series_id[3],
                      area_code=series_id[4:8],
                      item_code=series_id[8:],
                      series_id=series_id)


def generate_unit_enums(info_df: pd.DataFrame, targets: Set[str]) -> Set[str]:
    """Returns a list of enum definitions for the units required by the series
    identified by their IDs in "targets".

    Args:
        info_df: DataFrame containing information about
            all the series in targets.
        targets: Set of series IDs to generate unit enums for.
    """
    generated = set()
    for series_id in targets:
        unit, desc = parse_series_id(series_id).get_unit(info_df)
        generated.add((f"Node: dcid:{unit}\n"
                       "typeOf: dcs:UnitOfMeasure\n"
                       f"description: \"{desc}\"\n"
                       "descriptionUrl: \"https://www.bls.gov/cpi/"
                       "technical-notes/home.htm\"\n\n"))
    return generated


def generate_pop_type_enums(url: str, targets: Set[str]) -> Set[str]:
    """Returns a list of enum definitions for the population types required
    by the series identified by their IDs in "targets".

    Args:
        url: URL to the CSV containing the mappings from item codes to item
            names needed by the type of the series in "targets".
        targets: Set of series IDs to generate population
            type enums for.

    Raises:
        ValueError: Some series(s) does not have an item code mapping.
    """
    df = _download_df(url, sep="\t", usecols=("item_code", "item_name"))
    if "item_code" not in df.columns or "item_name" not in df.columns:
        raise ValueError("item_code or/and item_name columns missing")

    # Make sure every series of interest has an item_code mapping, i.e., has
    # an enum defined for pop type
    df = df[["item_code", "item_name"]]
    codes = set(df["item_code"])
    for series_id in targets:
        series_info = parse_series_id(series_id)
        if series_info.item_code not in codes:
            raise ValueError(
                f"{series_info} does not have an item_code mapping")

    generated = set()
    for row in df.itertuples(index=False):
        generated.add((f"Node: dcid:BLSItem/{row.item_code}\n"
                       "typeOf: dcs:EconomicProductEnum\n"
                       f"name: \"{row.item_name}\"\n\n"))
    return generated


def write_csv(urls: Iterable[str], dest: str, info_df: pd.DataFrame,
              targets: Set[str]) -> None:
    """Writes out the CSV containing series of a particular type, e.g., CPI-U.

    Args:
        urls: URLs to the CSVs containing the series.
        dest: Path to the output CSV.
        info_df: DataFrame containing information about the series.
        targets: Series to include in the output CSV.
    """
    result = pd.DataFrame()
    for url in urls:
        result = result.append(_generate_csv(url, info_df, targets))
    result.to_csv(dest, index=False)
    return result


def _download_df(url: str,
                 sep: str = "\t",
                 usecols: Tuple[str] = None) -> pd.DataFrame:
    """Downloads a CSV from a URL and loads it into a DataFrame,

    Args:
        url: URL to the CSV.
        sep: Separators used by the CSV. Can be a regex pattern.
        usecols: Columns to keep.
    """
    response = requests.get(url)
    response.raise_for_status()
    return pd.read_csv(io.StringIO(response.text),
                       sep=sep,
                       dtype="str",
                       usecols=usecols).rename(columns=lambda col: col.strip())


def _generate_csv(url: str, info_df: pd.DataFrame,
                  targets: List[str]) -> pd.DataFrame:
    """Returns a DataFrame containing series obtained from "url" and specified
    by "targets".

    Args:
        url: URL to a CSV containing some of the series in "targets".
        info_df: DataFrame containing informatino about the series.
        targets: Series to include in the return DataFrame.

    Returns:
        A DataFrame of five columns: "value", "date", "duration", "statvar",
        and "unit". See module docstring for what the columns are.
    """
    df = _download_df(url, sep=r"\s+")
    result = pd.DataFrame()
    for series_id, group_df in df.groupby(by="series_id"):
        if series_id not in targets:
            continue
        series_info = parse_series_id(series_id)
        # "period" is the months of the observations and is of the form "MM"
        # preceded by char 'M', e.g. "M05".
        # "M13" and "S03" are annual averages.
        group_df = group_df[~group_df["period"].isin(("M13", "S03"))]
        # "year" is of the form "YYYY".
        if series_info.is_monthly():
            group_df.loc[:, "date"] = (group_df["year"] + "-" +
                                       group_df["period"].str[-2:])
            group_df.loc[:, "duration"] = "P1M"
        else:
            group_df.loc[:, "date"] = group_df["year"] + "-" + group_df[
                "period"].map(lambda period: "06" if period == "S01" else "12")
            group_df.loc[:, "duration"] = "P6M"
        group_df.loc[:, "statvar"] = f"dcs:{series_info.get_statvar()}"
        group_df.loc[:, "unit"] = f"dcs:{series_info.get_unit(info_df)[0]}"
        # "value" is the CPI values.
        result = result.append(
            group_df[["value", "date", "duration", "statvar", "unit"]])
    return result


def _generate_statvar(series_id: str) -> str:
    """Returns the statvar definition for a series."""
    series_info = parse_series_id(series_id)
    return (f"Node: dcid:{series_info.get_statvar()}\n"
            "typeOf: dcs:StatisticalVariable\n"
            f"populationType: dcs:ConsumerGoodsAndServices\n"
            f"consumedThing: dcs:{series_info.get_pop_type()}\n"
            f"measurementQualifier: dcs:{series_info.get_mqual()}\n"
            "measuredProperty: dcs:consumerPriceIndex\n"
            "statType: dcs:measuredValue\n"
            f"consumer: dcs:{series_info.get_consumer()}\n"
            f"description: \"The series ID is {series_id}.\"\n")


def write_statvars(dest: str, targets: Set[str]) -> None:
    """Writes out the statistical variable definitions required by the
    series in "targets" after sorting for output determinism."""
    with open(dest, "w") as out:
        for series_id in sorted(targets):
            out.write(_generate_statvar(series_id))
            out.write("\n")


def filter_series(info_df: pd.DataFrame) -> Set[str]:
    """Filters all series provided by BLS and returns only monthly series for
    the US as a whole and not parts of US."""
    targets = set()
    # Prioritize monthly series
    for row in info_df.itertuples(index=False):
        series_info = parse_series_id(row.series_id)
        if not series_info.is_us() or not series_info.is_monthly():
            continue
        targets.add(row.series_id)
    return targets


def write_set(dest: str, to_write: List[str]) -> None:
    """Writes out a set of strings after sorting for output determinism."""
    with open(dest, "w") as out:
        for elem in sorted(to_write):
            out.write(elem)


def main() -> None:
    """Runs the script. See module docstring."""
    unit_enums = set()
    pop_type_enums = set()
    for series_type, urls in SERIES_TYPES_TO_DATA_URLS.items():
        info_df = _download_df(SERIES_TYPES_TO_INFO_URLS[series_type],
                               sep=r"\s*\t")
        targets = filter_series(info_df)
        pop_type_enums.update(
            generate_pop_type_enums(
                SERIES_TYPES_TO_EXPENDITURE_TYPES_URLS[series_type], targets))
        unit_enums.update(generate_unit_enums(info_df, targets))
        write_statvars(f"{series_type}.mcf", targets)
        write_csv(urls, f"{series_type}.csv", info_df, targets)
    write_set("unit_enums.mcf", unit_enums)
    write_set("pop_type_enums.mcf", pop_type_enums)


if __name__ == "__main__":
    main()
