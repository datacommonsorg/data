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
Downloading and converting BLS CPI raw csv files to csv files of two columns:
"date" and "cpi", where "date" is of the form "YYYY-MM" and "cpi" is numeric.

Usage: python3 generate_csv.py
'''

import re
import io
import logging
import dataclasses
from typing import Set, Tuple

import requests
import frozendict
import pandas as pd

# From series types to lists of CSV URLs containing series of those types
SERIES_TYPES_TO_DATA_URLS = frozendict.frozendict({
    "cpi_u": (
        "https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems",
        "https://download.bls.gov/pub/time.series/cu/cu.data.11.USFoodBeverage",
        "https://download.bls.gov/pub/time.series/cu/cu.data.12.USHousing",
        "https://download.bls.gov/pub/time.series/cu/cu.data.13.USApparel",
        "https://download.bls.gov/pub/time.series/cu/cu.data.14.USTransportation",
        "https://download.bls.gov/pub/time.series/cu/cu.data.15.USMedical",
        "https://download.bls.gov/pub/time.series/cu/cu.data.16.USRecreation",
        "https://download.bls.gov/pub/time.series/cu/cu.data.17.USEducationAndCommunication",
        "https://download.bls.gov/pub/time.series/cu/cu.data.18.USOtherGoodsAndServices",
        "https://download.bls.gov/pub/time.series/cu/cu.data.20.USCommoditiesServicesSpecial"
    ),
    "cpi_w": (
        "https://download.bls.gov/pub/time.series/cw/cw.data.1.AllItems",
        "https://download.bls.gov/pub/time.series/cw/cw.data.11.USFoodBeverage",
        "https://download.bls.gov/pub/time.series/cw/cw.data.12.USHousing",
        "https://download.bls.gov/pub/time.series/cw/cw.data.13.USApparel",
        "https://download.bls.gov/pub/time.series/cw/cw.data.14.USTransportation",
        "https://download.bls.gov/pub/time.series/cw/cw.data.15.USMedical",
        "https://download.bls.gov/pub/time.series/cw/cw.data.16.USRecreation",
        "https://download.bls.gov/pub/time.series/cw/cw.data.17.USEducationAndCommunication",
        "https://download.bls.gov/pub/time.series/cw/cw.data.18.USOtherGoodsAndServices",
        "https://download.bls.gov/pub/time.series/cw/cw.data.20.USCommoditiesServicesSpecial"
    ),
    "c_cpi_u":
        ("https://download.bls.gov/pub/time.series/su/su.data.1.AllItems",)
})

SERIES_TYPES_TO_INFO_URLS = frozendict.frozendict({
    "cpi_u": "https://download.bls.gov/pub/time.series/cu/cu.series",
    "cpi_w": "https://download.bls.gov/pub/time.series/cw/cw.series",
    "c_cpi_u": "https://download.bls.gov/pub/time.series/su/su.series"
})

SERIES_TYPES_TO_EXPENDITURE_TYPES_URLS = frozendict.frozendict({
    "cpi_u": "https://download.bls.gov/pub/time.series/cu/cu.item",
    "cpi_w": "https://download.bls.gov/pub/time.series/cw/cw.item",
    "c_cpi_u": "https://download.bls.gov/pub/time.series/su/su.item"
})


@dataclasses.dataclass(frozen=True)
class SeriesInfo:
    survey_abbreviation: str
    seasonal_code: str
    periodicity_code: str
    area_code: str
    item_code: str
    series_id: str

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if (not self.series_id or len(self.series_id) < 11 or
                len(self.series_id) > 17):
            self._raise_validation_error("invalid series_id")
        if (not self.survey_abbreviation or
                self.survey_abbreviation not in ("SU", "CU", "CW")):
            self._raise_validation_error(
                f"nvalid survey_abbreviation: {self.survey_abbreviation}")
        if (not self.seasonal_code or self.seasonal_code not in ("S", "U")):
            self._raise_validation_error(
                f"invalid survey_abbreviation: {self.survey_abbreviation}")
        if (not self.periodicity_code or
                self.periodicity_code not in ("R", "S")):
            self._raise_validation_error(
                f"invalid periodicity_code: {self.periodicity_code}")
        if (not self.area_code or len(self.area_code) != 4):
            self._raise_validation_error(f"invalid area_code: {self.area_code}")

    def _raise_validation_error(self, message: str):
        raise ValueError(f"{self.series_id}: {message}")

    def is_us(self):
        return self.area_code == "0000"

    def is_monthly(self):
        return self.periodicity_code == "R"

    def get_mmethod(self) -> str:
        if self.survey_abbreviation == "SU":
            return "BLSChained"
        return "BLSUnchained"

    def get_pop_type(self) -> str:
        return f"BLS_{self.item_code}"

    def get_consumer(self) -> str:
        if self.survey_abbreviation == "CW":
            return "UrbanWageEarnerAndClericalWorker"
        return "UrbanConsumer"

    def get_mqual(self) -> str:
        if self.seasonal_code == "S":
            return "BLSSeasonallyAdjusted"
        return "BLSSeasonallyUnadjusted"

    def get_statvar(self) -> str:
        return ("ConsumerPriceIndex_"
                f"{self.get_pop_type()}_"
                f"{self.get_consumer()}_"
                f"{self.get_mqual()}")

    def get_unit(self, info_df: pd.DataFrame) -> Tuple[str, str]:
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
                f"InexPointBasePeriod{year_start}To{year_end}Equals100",
                f"The reference base is {year_start} to {year_end} equals 100.")
        year, _ = base.split("=")
        return (f"IndexPointBasePeriod{year}Equals100",
                f"The reference base is {year} equals 100.")


def parse_series_id(series_id):
    return SeriesInfo(survey_abbreviation=series_id[:2],
                      seasonal_code=series_id[2],
                      periodicity_code=series_id[3],
                      area_code=series_id[4:8],
                      item_code=series_id[8:],
                      series_id=series_id)


def generate_unit_enums(info_df, targets) -> Set[str]:
    generated = set()
    for series_id in targets:
        unit, desc = parse_series_id(series_id).get_unit(info_df)
        generated.add((f"Node: dcid:{unit}\n"
                       "typeOf: dcs:UnitOfMeasure\n"
                       f"description: \"{desc}\"\n"
                       "descriptionUrl: \"https://www.bls.gov/cpi/"
                       "technical-notes/home.htm\"\n\n"))
    return generated


def generate_pop_type_enums(url, targets) -> Set[str]:
    df = download_df(url, sep="\t", usecols=("item_code", "item_name"))
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
    generated.add("Node: dcid:BLSExpenditureTypeEnum\n"
                  "typeOf: dcs:Class\n"
                  "subClassOf: schema:Enumeration\n"
                  "description: "
                  "\"An enumeration of types of consumer expenditures.\"\n\n")

    for row in df.itertuples(index=False):
        generated.add((f"Node: dcid:BLS_{row.item_code}\n"
                       "typeOf: dcs:BLSExpenditureTypeEnum\n"
                       f"description: \"{row.item_name}\"\n\n"))
    return generated


def generate_csv(urls, dest, info_df, targets):
    result = pd.DataFrame()
    for url in urls:
        result = result.append(single(url, info_df, targets))
    result.to_csv(dest, index=False)
    return result


def download_df(url, sep="\t", usecols=None):
    response = requests.get(url)
    response.raise_for_status()
    return pd.read_csv(io.StringIO(response.text),
                       sep=sep,
                       dtype="str",
                       usecols=usecols).rename(columns=lambda col: col.strip())


def single(url: str, info_df: pd.DataFrame, targets: Set[str]) -> pd.DataFrame:
    df = download_df(url, sep=r"\s+")
    result = pd.DataFrame()
    for series_id, group_df in df.groupby(by="series_id"):
        if series_id not in targets:
            continue
        series_info = parse_series_id(series_id)
        # "period" is the months of the observations and is of the form "MM"
        # preceded by char 'M', e.g. "M05".
        # "M13" is annual averages.
        group_df = group_df[group_df["period"] != "M13"]
        # "year" is of the form "YYYY".
        group_df["date"] = (group_df["year"] + "-" +
                            group_df["period"].str[-2:])
        group_df["statvar"] = f"dcs:{series_info.get_statvar()}"
        group_df["unit"] = f"dcs:{series_info.get_unit(info_df)[0]}"
        # "value" is the CPI values.
        result = result.append(group_df[["value", "date", "statvar", "unit"]])
    return result


def generate_statvars(dest, targets):
    with open(dest, "w") as out:
        for series_id in targets:
            series_info = parse_series_id(series_id)
            out.write((f"Node: dcid:{series_info.get_statvar()}\n"
                       "typeOf: dcs:StatisticalVariable\n"
                       f"populationType: dcs:{series_info.get_pop_type()}\n"
                       f"measurementQualifier: dcs:{series_info.get_mqual()}\n"
                       "measuredProperty: dcs:consumerPriceIndex\n"
                       "statType: dcs:measuredValue\n"
                       f"consumer: dcs:{series_info.get_consumer()}\n"))
            out.write("\n")


def filter_series(info_df: pd.DataFrame) -> Set[str]:
    targets = set()
    for row in info_df.itertuples(index=False):
        series_info = parse_series_id(row.series_id)
        if series_info.is_us() and series_info.is_monthly():
            targets.add(row.series_id)
    return targets


def write_set(dest, to_write: Set[str]):
    with open(dest, "w") as out:
        for elem in to_write:
            out.write(elem)


def main():
    """Runs the script. See module docstring."""
    unit_enums = set()
    pop_type_enums = set()
    for series_type, urls in SERIES_TYPES_TO_DATA_URLS.items():
        info_df = download_df(SERIES_TYPES_TO_INFO_URLS[series_type],
                              sep=r"\s*\t")
        targets = filter_series(info_df)
        pop_type_enums.update(
            generate_pop_type_enums(
                SERIES_TYPES_TO_EXPENDITURE_TYPES_URLS[series_type], targets))
        unit_enums.update(generate_unit_enums(info_df, targets))
        generate_statvars(f"{series_type}.mcf", targets)
        generate_csv(SERIES_TYPES_TO_DATA_URLS[series_type],
                     f"{series_type}.csv", info_df, targets)
    write_set("unit_enums.mcf", unit_enums)
    write_set("pop_type_enums.mcf", pop_type_enums)


if __name__ == "__main__":
    main()
