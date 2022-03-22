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
from re import sub

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

# V_PARENT_COMPANY_INFO table
_TABLE_PREFIX = "D_GHG_B"
_TABLE = "V_PARENT_COMPANY_INFO"

_OUT_FILE_PREFIX = "EpaParentCompany"
_COUNTY_CANDIDATES_CACHE = {}

# Cleaned CSV Columns
# - "containedInPlace" is a repeated list of refs to County and Census ZCTA
_DCID = "dcid"
_EPA_FACILITY_GHG_ID = "epaGhgrpFacilityId"
_NAME = "parentCompanyName"
_OTHERNAME = "otherName"
_YEAR = "year"
_PERCENT_OWNERSHIP = "facilityPercentOwnership"
_ADDRESS = "address"
_CIP = "locatedIn"

_TABLE_CLEAN_CSV_HDR = (_DCID, _NAME, _ADDRESS, _CIP)
_OWNERSHIP_CLEAN_CSV_HDR = (_DCID, _EPA_FACILITY_GHG_ID, _YEAR,
                            _PERCENT_OWNERSHIP)

_COUNTERS = {
    "missing_zip": set(),
    "percent_ownership_not_found": set(),
    "facility_does_not_exist": set(),
    "company_name_not_found": set(),
    "year_does_not_exist": set(),
}


def _gen_mcf():
    lines = [
        "Node: dcid:EpaOrganizationOwnership",
        "description: The ownership of an EPA Facility by an Organization in a given year.",
        "typeOf: dcs:StatisticalVariable", "populationType: dcs:Organization",
        "measuredProperty: owns", "statType: measurementResult"
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
    return "\n".join(lines)


def _gen_company_tmcf():
    lines = [
        "Node: E:EpaParentCompanyTable->E1", "typeOf: dcs:Organization",
        f"{_DCID}: C:EpaParentCompanyTable->{_DCID}",
        f"{_NAME}: C:EpaParentCompanyTable->{_NAME}",
        f"{_ADDRESS}: C:EpaParentCompanyTable->{_ADDRESS}",
        f"{_CIP}: C:EpaParentCompanyTable->{_CIP}"
    ]
    return "\n".join(lines)


def _v(table, row, col):
    return row.get(_TABLE_PREFIX + "." + table + "." + col, "")


def _cv(table, row, col):
    return _v(table, row, col).strip().title()


def _get_name(table, row):
    name = _cv(table, row, "PARENT_COMPANY_NAME")
    return name.replace(" Llc", " LLC")


def _name_to_id(s):
    s = sub(r'\W+', '', s)
    s = s.replace(' Llc', ' LLC')
    return ''.join([s[0].upper(), s[1:]])


def _get_address(table, row):
    parts = []
    for k in ["PARENT_CO_STREET_ADDRESS", "PARENT_CO_CITY", "PARENT_CO_STATE"]:
        p = _cv(table, row, k)
        if p:
            parts.append(p)
    address = ", ".join(parts)
    p = _cv(table, row, "PARENT_CO_ZIP")
    if p:
        address += " - " + p
    return address


def _get_county(company_id, zip, year):
    """Resolve the geo relations for the given Facility

    Returns resolved <zip>, <county>
    """
    if zip == "zip/00000" or zip == "zip/":
        _COUNTERS["missing_zip"].add((company_id, year))
        return ""

    county_candidates = fh.get_county_candidates(zip)
    if not county_candidates:
        _COUNTERS["missing_zip"].add((company_id, year))
        return ""

    # Choose the first.
    try:
        # This could fail because county_candidates is of form [[], []]
        county = county_candidates[0][0]
    except:
        county = ""
    return county


def counters_string():
    result = []
    for k, v in _COUNTERS.items():
        result.append(k + " -> " + str(len(v)) + " - " + ", " + str(v))
    return "\n".join(result)


def process(input_table_path, existing_facilities_file, output_path_info,
            output_path_ownership):
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
                ghg_id = _v(_TABLE, in_row, "FACILITY_ID")
                assert ghg_id, str(in_row)
                ghg_id = _EPA_FACILITY_GHG_ID + "/" + ghg_id

                company_name = _get_name(_TABLE, in_row)
                if not company_name:
                    _COUNTERS["company_name_not_found"].add(ghg_id)
                    continue

                company_name = company_name.replace("\"", "").replace("'", "")

                company_id = "EpaParentCompany/" + _name_to_id(company_name)
                assert company_id, str(in_row)

                year = _v(_TABLE, in_row, "YEAR")
                if not year:
                    _COUNTERS["year_does_not_exist"].add((company_id, ghg_id))

                percent_own = _v(_TABLE, in_row, "PARENT_CO_PERCENT_OWN")
                # If the ownership percentage is not known, set it to 100.
                if not percent_own:
                    _COUNTERS["percent_ownership_not_found"].add(
                        (company_id, year))
                    percent_own = 100

                ownership_out_row = {
                    _DCID: "dcid:" + company_id,
                    _EPA_FACILITY_GHG_ID: ghg_id,
                    _PERCENT_OWNERSHIP: percent_own,
                    _YEAR: year
                }
                rows_written += 1
                if rows_written % 500 == 0:
                    print("**********************************")
                    print("processed %d rows" % rows_written)
                    print("Geo Resolution Stats: \n" + counters_string())

                # Only insert the ownership relationships where the facility exists in data commons.
                if ghg_id in facility_ids:
                    ownershipWriter.writerow(ownership_out_row)
                else:
                    _COUNTERS["facility_does_not_exist"].add(ghg_id)

                # If the company_id was previously seen, do not insert again.
                # This can happen when the name of the company is formatted differently. We only
                # need one version.
                if company_id.lower() not in processed_companies:
                    # zips have extension
                    zip_code = _v(_TABLE, in_row, "PARENT_CO_ZIP")[:5]
                    if not zip_code:
                        zip_code = ""
                    zip = "zip/" + zip_code
                    county = _get_county(company_id, zip, year)

                    table_out_row = {
                        _DCID: "dcid:" + company_id,
                        _NAME: company_name,
                        _ADDRESS: _get_address(_TABLE, in_row),
                        _CIP: ", ".join(fh.get_cip(zip, county)),
                    }
                    tableWriter.writerow(table_out_row)
                    processed_companies.add(company_id.lower())

        print("Produced " + str(rows_written) + " rows from " + _TABLE)
        print("Geo Resolution Stats: \n" + counters_string())

    # Write the MCF and TMCF files in their respective destination locations.
    with open(ownership_path + "Ownership.mcf", "w") as fp:
        fp.write(_gen_mcf())

    with open(ownership_path + "Ownership.tmcf", "w") as fp:
        fp.write(_gen_ownership_tmcf())

    with open(table_path + "Table.tmcf", "w") as fp:
        fp.write(_gen_company_tmcf())


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

    process(FLAGS.input_download_path, FLAGS.existing_facilities_file,
            output_path_info, output_path_ownership)


if __name__ == "__main__":
    app.run(main)
