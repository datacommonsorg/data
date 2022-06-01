# Copyright 2022 Google LLC
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
"""A script to download, parse and process the Parent Company Info for Facilities tracked by EPA."""

import os.path
import pathlib
import sys

import csv
import datacommons
import json
import pandas as pd

from absl import app
from absl import flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))
from us_epa.util import facilities_helper as fh

FLAGS = flags.FLAGS

flags.DEFINE_string("input_download_path", "tmp_data", "Input directory")
flags.DEFINE_string("existing_facilities_file", "existing_facilities",
                    "Filename for existing facilities ids")
flags.DEFINE_string("output_base_path", "output",
                    "Output directory for processed data.")
flags.DEFINE_string("parent_co_output_path", "table",
                    "Output directory for company info.")
flags.DEFINE_string("ownership_output_path", "ownership",
                    "Output directory for ownership.")
flags.DEFINE_string("svobs_output_path", "svobs",
                    "Output directory for StatVarObs.")

_DC_API_URL = "https://api.datacommons.org/place/stat-vars"

# V_PARENT_COMPANY_INFO table
_TABLE_PREFIX = "D_GHG_B"
_TABLE = "V_PARENT_COMPANY_INFO"

_OUT_FILE_PREFIX = "EpaParentCompany"
_OUT_SVOBS_FILE_PREFIX = "SVObs"
_COUNTY_CANDIDATES_CACHE = {}

# Cleaned CSV Columns
# - "locatedIn" is a repeated list of refs to County and Census ZCTA
_DCID = "dcid"
_EPA_FACILITY_GHG_ID = "epaGhgrpFacilityId"
_NAME = "name"
_YEAR = "year"
_PERCENT_OWNERSHIP = "ownership"
_ADDRESS = "address"
_CIP = "locatedIn"

# The following are for the StatVarOvbservations.
_PARENT_COMPANY_DCID = 'parent_company_dcid'
_SV_MEASURED = "sv_measured"
_OBSERVATION_PERIOD = "obs_period"
_SVO_VAL = "value"
_OBSERVATION_DATE = "year"

_TABLE_CLEAN_CSV_HDR = (_DCID, _NAME, _ADDRESS, _CIP)
_OWNERSHIP_CLEAN_CSV_HDR = (_DCID, _EPA_FACILITY_GHG_ID, _YEAR,
                            _PERCENT_OWNERSHIP)
_SVOBS_CLEAN_CSV_HDR = (_PARENT_COMPANY_DCID, _SV_MEASURED, _OBSERVATION_PERIOD,
                        _SVO_VAL, _OBSERVATION_DATE)

_COUNTERS_COMPANIES = {
    "missing_zip": set(),
    "percent_ownership_not_found": set(),
    "facility_does_not_exist": set(),
    "company_name_not_found": set(),
    "year_does_not_exist": set(),
    "company_ids_replaced": set(),
}


def _gen_table_mcf():
    lines = [
        "Node: dcid:EpaParentCompany",
        "subClassOf: dcs:Organization",
        "name: EpaParentCompany",
        "typeOf: schema:Class",
        "\n",
        "Node: dcid:locatedIn",
        "typeOf: schema:Property",
        "domainIncludes: schema:Place",
        "rangeIncludes: schema:Place",
        "name: locatedIn",
    ]
    return "\n".join(lines)


def _gen_ownership_mcf():
    lines = [
        "Node: dcid:EpaOrganizationOwnership",
        "description: The ownership of an EPA Facility by an Organization in a given year.",
        "typeOf: dcs:StatisticalVariable",
        "populationType: dcs:EpaParentCompany",
        "measuredProperty: owns",
        "statType: measurementResult",
        "\n",
        "Node: dcid:ownershipPercentage",
        "typeOf: schema:Property",
        "domainIncludes: dcs:EpaParentCompany",
        "rangeIncludes: schema:Number",
        "name: ownershipPercentage",
    ]
    return "\n".join(lines)


def _gen_ownership_tmcf():
    lines = [
        "Node: E:EpaParentCompanyOwnership->E0",
        "typeOf: dcs:StatVarObservation",
        "variableMeasured: dcid:EpaOrganizationOwnership",
        f"observationDate: C:EpaParentCompanyOwnership->{_YEAR}",
        f"observationAbout: C:EpaParentCompanyOwnership->{_DCID}",
        f"value: C:EpaParentCompanyOwnership->{_EPA_FACILITY_GHG_ID}",
        f"ownershipPercentage: C:EpaParentCompanyOwnership->{_PERCENT_OWNERSHIP}",
    ]
    return "\n".join(lines) + "\n"


def _gen_company_tmcf():
    lines = [
        "Node: E:EpaParentCompanyTable->E1",
        "typeOf: dcs:EpaParentCompany",
        f"{_DCID}: C:EpaParentCompanyTable->{_DCID}",
        f"{_NAME}: C:EpaParentCompanyTable->{_NAME}",
        f"{_ADDRESS}: C:EpaParentCompanyTable->{_ADDRESS}",
        f"{_CIP}: C:EpaParentCompanyTable->{_CIP}",
    ]
    return "\n".join(lines) + "\n"


def _gen_svobs_tmcf():
    lines = [
        "Node: E:EpaParentCompanyStatVarObs->E0",
        'typeOf: dcs:StatVarObservation',
        f'observationAbout: C:EpaParentCompanyStatVarObs->{_PARENT_COMPANY_DCID}',
        f'variableMeasured: C:EpaParentCompanyStatVarObs->{_SV_MEASURED}',
        f'observationPeriod: C:EpaParentCompanyStatVarObs->{_OBSERVATION_PERIOD}',
        'unit: dcs:MetricTonCO2e',
        'measurementMethod: dcs:dcAggregate/EPA_GHGRP',
        f'value: C:EpaParentCompanyStatVarObs->{_SVO_VAL}',
        f'observationDate: C:EpaParentCompanyStatVarObs->{_OBSERVATION_DATE}',
    ]
    return "\n".join(lines) + "\n"


def _str(v):
    if not v:
        return ''
    return '"' + v + '"'


def _get_county(company_id, zip, year):
    """Resolve the geo relations for the given Facility

    Returns resolved <county> which is the first county returned by the
    containedInPlace resolver OR the first county in the geoOverlaps resolver.
    containedInPlace is given precendence over geoOverlaps.

    county is an empty string if both the resolvers fail to return counties.
    This can happen for some zip codes which don't have a county associated in
    Data Commons, e.g. https://datacommons.org/browser/zip/31040 or the zip
    code itself does not exist in Data Commons, e.g.
    https://datacommons.org/browser/zip/00804.
    """
    if zip == "zip/00000" or zip == "":
        _COUNTERS_COMPANIES["missing_zip"].add((company_id, year))
        return ""

    county_candidates = fh.get_county_candidates(zip)
    if not county_candidates:
        _COUNTERS_COMPANIES["missing_zip"].add((company_id, year))
        return ""

    # Choose the first matching county. fh.get_county_candidates() returns a
    # two dimensional array corresponding to containedInPlace (at index 0)
    # and geoOverlaps (at index 1).
    county = ""
    if county_candidates[0]:
        county = county_candidates[0][0]
    elif county_candidates[1]:
        county = county_candidates[1][0]

    return county


# Returns a mapping from a key to value.
# key: (company_id, StatVar, Obs Period, Obs Date)
# value: a map of all elements in the Key and the observed Value multiplied by
#   the percentage ownership.
def _get_key_val_for_svobs(facility_id, stat_var, facility_comp_ownership,
                           svobs_series):
    key_val = {}
    for svo_dict in svobs_series:
        for dt, v in svo_dict['val'].items():
            if (facility_id, dt) in facility_comp_ownership:
                for company_id, percentage in facility_comp_ownership[(
                        facility_id, dt)].items():
                    key = (company_id, stat_var, svo_dict['observationPeriod'],
                           dt)
                    if key not in key_val:
                        key_val[key] = {}
                    key_val.update({
                        key: {
                            _PARENT_COMPANY_DCID: company_id,
                            _SV_MEASURED: stat_var,
                            _OBSERVATION_PERIOD: svo_dict['observationPeriod'],
                            _OBSERVATION_DATE: dt,
                            _SVO_VAL: v * float(percentage) / 100
                        }
                    })

    return key_val


# Read from the EpaParentCompanyOwnership.csv file generated while processing
# the parent company data.
# Retun a map of (facility ID, year) to a dictionary of
# {company_id: percentage ownership}.
def _facility_year_company_percentages(ownership_filepath):
    facility_company_ownership = {}
    with open(ownership_filepath, "r") as owfp:
        cr = csv.DictReader(owfp)
        for in_row in cr:
            key = (in_row[_EPA_FACILITY_GHG_ID], in_row[_YEAR])
            if key not in facility_company_ownership:
                facility_company_ownership[key] = {}
            facility_company_ownership[key].update(
                {in_row[_DCID]: in_row[_PERCENT_OWNERSHIP]})

    return facility_company_ownership


def counters_string(counter_dict):
    result = []
    for k, v in counter_dict.items():
        result.append(k + " -> " + str(len(v)) + " - " + ", " + str(v))
    return "\n".join(result)


def process_companies(input_table_path, existing_facilities_file,
                      output_path_info, output_path_ownership):

    company_ids_replaced_counter = 0
    # First retrieve the ID duplicate mappings.
    dupes = {}
    dupes_filepath = os.path.join(input_table_path, "DuplicateIdMappings.csv")
    with open(dupes_filepath, "r") as dfp:
        cr = csv.DictReader(dfp)
        for row in cr:
            dupes[row['Id']] = row['MappedTo']

    processed_companies = set()
    # Writing two CSVs: one for the CompanyInfo; the other for the Ownership StatVarObs.
    table_path = os.path.join(output_path_info, _OUT_FILE_PREFIX)
    ownership_path = os.path.join(output_path_ownership, _OUT_FILE_PREFIX)
    with \
        open(table_path + "Table.csv", "w") as twfp, \
        open(ownership_path + "Ownership.csv", "w") as owfp:
        # IMPORTANT: We want to escape double quote (\") if it is specified in the cell
        # value, rather than the default of using two double quotes ("")
        tableWriter = csv.DictWriter(twfp,
                                     _TABLE_CLEAN_CSV_HDR,
                                     doublequote=False,
                                     escapechar="\\")
        tableWriter.writeheader()

        ownershipWriter = csv.DictWriter(owfp,
                                         _OWNERSHIP_CLEAN_CSV_HDR,
                                         doublequote=False,
                                         escapechar="\\")
        ownershipWriter.writeheader()

        # Get the existing facility ids in a set.
        existing_facilities_path = os.path.join(
            input_table_path, existing_facilities_file + ".csv")

        facility_ids = set(
            pd.read_csv(existing_facilities_path)[_EPA_FACILITY_GHG_ID].values)
        input_table = os.path.join(input_table_path, _TABLE + ".csv")
        rows_written = 0
        with open(input_table, "r") as rfp:
            cr = csv.DictReader(rfp)
            for in_row in cr:
                ghg_id = fh.v(_TABLE,
                              in_row,
                              "FACILITY_ID",
                              table_prefix=_TABLE_PREFIX)
                assert ghg_id, str(in_row)
                ghg_id = _EPA_FACILITY_GHG_ID + "/" + ghg_id

                company_name = fh.get_name(_TABLE,
                                           in_row,
                                           "PARENT_COMPANY_NAME",
                                           table_prefix=_TABLE_PREFIX)
                if not company_name:
                    _COUNTERS_COMPANIES["company_name_not_found"].add(ghg_id)
                    continue

                company_name = company_name.replace("\"", "").replace("'", "")

                company_id = fh.name_to_id(company_name)
                assert company_id, str(in_row)

                # Replace the company_id with a duplicate mapping, if it exists.
                if company_id in dupes:
                    _COUNTERS_COMPANIES["company_ids_replaced"].add(company_id)
                    company_id = dupes[company_id]
                company_id = "EpaParentCompany/" + company_id

                year = fh.v(_TABLE, in_row, "YEAR", table_prefix=_TABLE_PREFIX)
                if not year:
                    _COUNTERS_COMPANIES["year_does_not_exist"].add(
                        (company_id, ghg_id))

                percent_own = fh.v(_TABLE,
                                   in_row,
                                   "PARENT_CO_PERCENT_OWN",
                                   table_prefix=_TABLE_PREFIX)
                # If the ownership percentage is not known, set it to 100.
                if not percent_own:
                    _COUNTERS_COMPANIES["percent_ownership_not_found"].add(
                        (company_id, year))
                    percent_own = 100

                ownership_out_row = {
                    _DCID: company_id,
                    _EPA_FACILITY_GHG_ID: ghg_id,
                    _PERCENT_OWNERSHIP: percent_own,
                    _YEAR: year
                }
                rows_written += 1
                if rows_written % 500 == 0:
                    print("**********************************")
                    print("processed %d rows" % rows_written)
                    print("Geo Resolution Stats: \n" +
                          counters_string(_COUNTERS_COMPANIES))

                # Only insert the ownership relationships where the facility exists in data commons.
                if ghg_id in facility_ids:
                    ownershipWriter.writerow(ownership_out_row)
                else:
                    _COUNTERS_COMPANIES["facility_does_not_exist"].add(ghg_id)

                # If the company_id was previously seen, do not insert again.
                # This can happen when the name of the company is formatted differently. We only
                # need one version.
                if company_id.lower() not in processed_companies:
                    # zips have extension
                    zip_code = fh.v(_TABLE,
                                    in_row,
                                    "PARENT_CO_ZIP",
                                    table_prefix=_TABLE_PREFIX)[:5]
                    zip = ""
                    if zip_code:
                        zip = "zip/" + zip_code
                    county = _get_county(company_id, zip, year)

                    table_out_row = {
                        _DCID:
                            company_id,
                        _NAME:
                            _str(company_name),
                        _ADDRESS:
                            _str(
                                fh.get_address(_TABLE,
                                               in_row,
                                               table_prefix=_TABLE_PREFIX)),
                        _CIP:
                            ", ".join(fh.get_cip(zip, county)),
                    }
                    tableWriter.writerow(table_out_row)
                    processed_companies.add(company_id.lower())

        print("Produced " + str(rows_written) + " rows from " + _TABLE)
        print("Geo Resolution Stats: \n" + counters_string(_COUNTERS_COMPANIES))

    print("Company ID duplicated replaced = ", company_ids_replaced_counter)

    # Write the MCF and TMCF files in their respective destination locations.
    with open(table_path + "Table.mcf", "w") as fp:
        fp.write(_gen_table_mcf())

    with open(ownership_path + "Ownership.mcf", "w") as fp:
        fp.write(_gen_ownership_mcf())

    with open(table_path + "Table.tmcf", "w") as fp:
        fp.write(_gen_company_tmcf())

    with open(ownership_path + "Ownership.tmcf", "w") as fp:
        fp.write(_gen_ownership_tmcf())


def process_svobs(svobs_path, facility_company_ownership, facility_svo_dict):
    # Create a map where key: (company_id, statVar, obsPeriod, year)
    # and value: the svobs value multiplied by the percentage ownership.
    # Note that the same key may appear more than once. This happens when the
    # company and year combination applies to multiple companies. Therefore, we
    # add the (value * percentage) across all the multiple facilities, for the
    # same key.
    company_svo_dict = {}
    for facility_id, sv_dict in facility_svo_dict.items():
        for sv, svobs in sv_dict.items():
            if not svobs:
                continue

            # Construct a key comprising the Company ID, SV, Year and
            # Obs Period. A company may own several facilities in a given year
            # and the same SV may be present for those facilities in the same
            # year. Therefore, we need to sum the values of the observations.
            key_val = _get_key_val_for_svobs(facility_id, sv,
                                             facility_company_ownership,
                                             svobs['sourceSeries'])
            for (k, v) in key_val.items():
                if k not in company_svo_dict:
                    company_svo_dict[k] = {
                        _PARENT_COMPANY_DCID: v[_PARENT_COMPANY_DCID],
                        _SV_MEASURED: v[_SV_MEASURED],
                        _OBSERVATION_PERIOD: v[_OBSERVATION_PERIOD],
                        _OBSERVATION_DATE: v[_OBSERVATION_DATE],
                        _SVO_VAL: 0
                    }
                company_svo_dict[k][_SVO_VAL] += v[_SVO_VAL]

    out_path = os.path.join(svobs_path, _OUT_SVOBS_FILE_PREFIX)
    with open(out_path + ".csv", "w") as svofp:
        writer = csv.DictWriter(svofp,
                                _SVOBS_CLEAN_CSV_HDR,
                                doublequote=False,
                                escapechar="\\")
        writer.writeheader()

        num_rows = 0
        for k, v in company_svo_dict.items():
            if num_rows % 1000 == 0:
                print("processed %d rows" % num_rows)
            out_row = {
                _PARENT_COMPANY_DCID: v[_PARENT_COMPANY_DCID],
                _SV_MEASURED: v[_SV_MEASURED],
                _OBSERVATION_PERIOD: v[_OBSERVATION_PERIOD],
                _SVO_VAL: v[_SVO_VAL],
                _OBSERVATION_DATE: v[_OBSERVATION_DATE]
            }
            writer.writerow(out_row)
            num_rows += 1

    with open(out_path + ".tmcf", "w") as fp:
        fp.write(_gen_svobs_tmcf())


# Helper function which retrieves the list of all facilities, the ownership
# relationships and then queries the DC API to get all relevant StatVars and
# StatVar Observations associated with each facility.
# It calls the process_svobs() function which writes the tmcf and csv files.
def generate_svobs_helper(ownership_relationships_filepath, svobs_path_info):
    # First get the facility, year to company, percentage mappings.
    facility_company_ownership = _facility_year_company_percentages(
        ownership_relationships_filepath)

    facilities = set()
    for (facility_id, year) in facility_company_ownership:
        facilities.add(facility_id)

    facilities = list(facilities)

    statVars = fh.get_all_statvars(_DC_API_URL, facilities)
    facility_svo_dict = fh.get_all_svobs(facilities, statVars)
    print("# SVs : %d" % len(statVars))
    print("# Facilities : %d" % len(facility_svo_dict))

    process_svobs(svobs_path_info, facility_company_ownership,
                  facility_svo_dict)


def main(_):
    # Validate inputs.
    assert FLAGS.output_base_path
    assert FLAGS.parent_co_output_path
    assert FLAGS.ownership_output_path
    assert FLAGS.input_download_path
    assert FLAGS.existing_facilities_file
    assert os.path.exists(
        os.path.join(FLAGS.input_download_path,
                     FLAGS.existing_facilities_file + ".csv"))
    assert os.path.exists(
        os.path.join(FLAGS.input_download_path, _TABLE + ".csv"))

    output_path_info = os.path.join(FLAGS.output_base_path,
                                    FLAGS.parent_co_output_path)
    output_path_ownership = os.path.join(FLAGS.output_base_path,
                                         FLAGS.ownership_output_path)

    pathlib.Path(FLAGS.output_base_path).mkdir(exist_ok=True)
    pathlib.Path(output_path_info).mkdir(exist_ok=True)
    pathlib.Path(output_path_ownership).mkdir(exist_ok=True)

    # First process companies.
    process_companies(FLAGS.input_download_path, FLAGS.existing_facilities_file,
                      output_path_info, output_path_ownership)

    # Now process the StatVarObs.
    # First check that the output csv from process_companies() exists.
    ownership_path = os.path.join(output_path_ownership, _OUT_FILE_PREFIX)
    ownership_relationships_filepath = ownership_path + "Ownership.csv"
    assert os.path.exists(ownership_relationships_filepath)

    svobs_path_info = os.path.join(FLAGS.output_base_path,
                                   FLAGS.svobs_output_path)
    pathlib.Path(svobs_path_info).mkdir(exist_ok=True)

    # Generate the new SVOs.
    generate_svobs_helper(ownership_relationships_filepath, svobs_path_info)


if __name__ == "__main__":
    app.run(main)
