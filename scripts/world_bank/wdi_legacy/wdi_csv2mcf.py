"""Script to convert WDI CSV to MCF."""

import csv
import os
import sys

from absl import app
from absl import flags
from absl import logging

import constants as cons

# Allows the local imports from repo root dir
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_REPO_DIR = _SCRIPT_DIR.split('/scripts/', 1)[0]
sys.path.append(os.path.join(_DATA_REPO_DIR, 'util'))

import download_util
import file_util
from counters import Counters


flags.DEFINE_string(
    'input_file', 'input_files/WDICSV.csv',
    'Path of input file downloaded from https://datacatalog.worldbank.org/search/dataset/0037712.'
)
flags.DEFINE_string('output_dir', 'output', 'Directory to write MCF output.')
flags.DEFINE_string('pops_file_name', 'wdi_pops.mcf',
                    'CNS file name to write population statistics nodes.')

_FLAGS = flags.FLAGS

_out_file = {}


def process_line(l, start_year: int, end_year: int, country_codes: dict,
                 counters: Counters):
    """Process line of WDI data."""
    indicator = l[cons.INDICATOR_NAME]
    if indicator in cons.INDICATOR_TEMP_MAP:
        # Skip country code not following ISO 3166 standard.
        if len(l[cons.COUNTRY_CODE]) != 3 or l[
                cons.COUNTRY_CODE] not in country_codes:
            counters.add_counter('input-rows-dropped-invalid-country', 1)
            return
        place_dcid = 'Earth' if l[
            cons.COUNTRY_CODE] == 'WLD' else 'country/' + l[cons.COUNTRY_CODE]
        process_pop(l, indicator, place_dcid, counters)
        for year in range(start_year, end_year + 1):
            year_str = str(year)
            process_obs(l, indicator, year_str, place_dcid, counters)


def process_pop(l, indicator, place_dcid, counters):
    """Store the pop node into population statistics MCF file."""
    try:
        node = cons.INDICATOR_TEMP_MAP[indicator][0].substitute(
            location=place_dcid, location_abbr=l[cons.COUNTRY_CODE])
        _out_file[cons.POPS_FILE].write(node + '\n')
        counters.add_counter(f'output-pop', 1)
    except:
        counters.add_counter('error-pop', 1)
        raise app.UsageError('Unable to write Pop for line=%s', l)


def process_obs(l, indicator, year_str, place_dcid, counters):
    """Store the obs node into the MCF file of the year if it has measure."""
    if l[year_str]:
        try:
            node = cons.INDICATOR_TEMP_MAP[indicator][1].substitute(
                location=place_dcid,
                location_abbr=l[cons.COUNTRY_CODE],
                underscore='_',
                observation_date=year_str,
                measured_value=l[year_str])
            _out_file[year_str].write(node + '\n')
            counters.add_counter(f'output-obs', 1)
            counters.add_counter(f'output-obs-{year_str}', 1)
        except:
            counters.add_counter('error-obs', 1)
            raise app.UsageError(
                'Unable to write Obs for %s country %s year %s : mVal=%s',
                indicator, l[cons.COUNTRY_CODE], year_str, l)


def process_file(input_file: str, output_dir: str, pops_file_name: str):
    """Process the input CSV and writes the MCF."""
    global _out_file
    counters = Counters()

    # Load list of existing countries
    country_codes = file_util.file_load_csv_dict(os.path.join(
        os.path.dirname(_SCRIPT_DIR), 'wdi', 'WorldBankCountries.csv'),
                                                 key_column='ISO3166Alpha3',
                                                 value_column='CountryName')
    # Create output file
    _out_file[cons.POPS_FILE] = file_util.FileIO(
        os.path.join(output_dir, pops_file_name), 'w')

    counters.add_counter('total', file_util.file_estimate_num_rows(input_file))
    with file_util.FileIO(input_file, 'r') as f_in:
        dict_reader = csv.DictReader(f_in)
        columns = dict_reader.fieldnames
        start_year = int(columns[cons.START_YEAR_COLUMN])
        end_year = int(columns[-1])

        # Create per-year output files
        for yr in range(start_year, end_year + 1):
            year_str = str(yr)
            if year_str not in _out_file:
                _out_file[year_str] = file_util.FileIO(
                    os.path.join(output_dir, 'wdi' + year_str + '.mcf'), 'w')

        for l in dict_reader:
            process_line(l, start_year, end_year, country_codes, counters)
            counters.add_counter('processed', 1)


def main(argv):
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')
    process_file(_FLAGS.input_file, _FLAGS.output_dir, _FLAGS.pops_file_name)


if __name__ == '__main__':
    app.run(main)
