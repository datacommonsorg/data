"""A script to clean Decennial Census Redistricting data from FTP site. """

import csv
import glob
import io
import os
import zipfile

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'raw_data_path', 'scratch', 'Path to the equivalent of '
    'https://www2.census.gov/programs-surveys/decennial/')
flags.DEFINE_string('output_path', 'output', 'Output directory')
flags.DEFINE_boolean('verbose', False, 'Print debug info')

_YEARS = ['2010', '2020']
_DIR_PREFIX = 'data/01-Redistricting_File--PL_94-171'

# NOTE: Almost all screenshots below are from the documentation PDFs mentioned
# in the README.md:
# * 2010: https://www.census.gov/prod/cen2010/doc/pl94-171.pdf
# * 2020: https://www2.census.gov/programs-surveys/decennial/2020/technical-documentation/complete-tech-docs/summary-file/2020Census_PL94_171Redistricting_NationalTechDoc.pdf

#
# Mappings for 2020 Geo File.
#
# - https://user-images.githubusercontent.com/4375037/130695847-b0955d19-9b8b-4021-b195-86357cfb03ec.png
#

# Summary level in geo file.
_GEOF_2020_SUMLEV_COL = 2
# Logical Record Number in geofile.
_GEOF_2020_LOGRECNO_COL = 7

# summary-level -> [column1, column2, ...] (from 0) which form parts of DCID
#
# Relevant summary levels: https://user-images.githubusercontent.com/4375037/130695894-365a96b6-8bec-4a98-ab91-fe90ea3c2e57.png
_GEOF_2020_DCID_MAP = {
    # State
    '040': [12],
    # County
    '050': [12, 14],
    # CouSub
    '060': [12, 14, 17],
    # Tract
    '140': [12, 14, 32],
    # BlockGroup
    '150': [12, 14, 32, 33],
    # Place
    '160': [12, 29],
}

#
# Mappings for 2010 Geo File. These are not really delimited. Rather, they have
# start-position and length for the fields.
#
# - https://user-images.githubusercontent.com/4375037/130695985-6996cd98-66c9-4a59-87c7-48b9e389e2bc.png
#
_GEOF_2010_SUMLEV = (9, 3)
_GEOF_2010_LOGRECNO = (19, 7)

# summary-level -> [(start1, length1), (start2, length2), ...]
#
# Relevant summary levels: https://user-images.githubusercontent.com/4375037/130695894-365a96b6-8bec-4a98-ab91-fe90ea3c2e57.png
_GEOF_2010_DCID_MAP = {
    # State
    '040': [(28, 2)],
    # County
    '050': [(28, 2), (30, 3)],
    # CouSub
    '060': [(28, 2), (30, 3), (37, 5)],
    # Tract
    '140': [(28, 2), (30, 3), (55, 6)],
    # BlockGroup
    '150': [(28, 2), (30, 3), (55, 6), (61, 1)],
    # Place
    '160': [(28, 2), (46, 5)],
}

# US Summary level.
_US_SUMLEV = '010'

# Logical Record Number in datafile is same across years.
# 2020 - https://user-images.githubusercontent.com/4375037/130696087-14199c77-58f7-40cb-8010-3355356d7275.png
# 2010 - https://user-images.githubusercontent.com/4375037/130696096-a40d7306-1707-4359-92af-a7bd391e2623.png
_DATAF_LOGRECNO_COL = 4

# Delimiter for data file varies across years.
_DATAF_DELIM_CHAR = {
    '2010': ',',
    '2020': '|',
}

# Table name as it appears in Data Dictionary Reference:
# https://user-images.githubusercontent.com/4375037/130696166-da194721-c8e1-484e-8722-09202d3fe5c3.png
#
# The column offsets are the same across years:
# 2020 - https://user-images.githubusercontent.com/4375037/130696087-14199c77-58f7-40cb-8010-3355356d7275.png
# 2010 - https://user-images.githubusercontent.com/4375037/130696096-a40d7306-1707-4359-92af-a7bd391e2623.png
_TABLE_COLOFFSET_MAP = {
    'P001': 5,
    'P002': 5 + 71,
    'P003': 5,
    'P004': 5 + 71,
    'H001': 5 + 71 + 73,
}

# The column that stores the file shard number. Same across years.
_DATAF_CIFSN_COL = 3

# CIFSN value -> Variable Name -> stat-var DCID
_DATAF_STATVAR_MAP = {
    # https://user-images.githubusercontent.com/4375037/130696166-da194721-c8e1-484e-8722-09202d3fe5c3.png
    '01': {
        'P0010001': 'Count_Person',
        'P0010003': 'Count_Person_WhiteAlone',
        'P0010004': 'Count_Person_BlackOrAfricanAmericanAlone',
        'P0010005': 'Count_Person_AmericanIndianAndAlaskaNativeAlone',
        'P0010006': 'Count_Person_AsianAlone',
        'P0010007': 'Count_Person_NativeHawaiianAndOtherPacificIslanderAlone',
        'P0010008': 'Count_Person_SomeOtherRaceAlone',
        'P0020002': 'Count_Person_HispanicOrLatino',
    },
    # https://user-images.githubusercontent.com/4375037/130696328-34c79c4d-69f2-4c9a-892a-7bf26602160f.png
    '02': {
        'H0010001': 'Count_HousingUnit',
        'H0010002': 'Count_HousingUnit_OccupiedHousingUnit',
        'H0010003': 'Count_HousingUnit_VacantHousingUnit',
    },
}

_CSV_COLUMNS = [
    'observationAbout', 'variableMeasured', 'value', 'observationDate'
]


def _get_geo_file(zf):
    for f in zf.namelist():
        if 'geo' in f:
            return f
    return ''


def _slice(line, pair):
    return line[pair[0] - 1:pair[0] - 1 + pair[1]]


def _build_2010_geomap(geof, is_national):
    """Builds a map from logical-record-number to DCID for 2010."""
    geomap = {}
    for line in geof:
        line = line.strip()

        logrecno = _slice(line, _GEOF_2010_LOGRECNO)
        sumlev = _slice(line, _GEOF_2010_SUMLEV)

        if is_national:
            if sumlev == _US_SUMLEV:
                geomap[logrecno] = 'country/USA'
            continue

        if sumlev not in _GEOF_2010_DCID_MAP:
            # Not an interesting summary-level
            continue

        dcid_parts = ['geoId/']
        for c in _GEOF_2010_DCID_MAP[sumlev]:
            dcid_parts.append(_slice(line, c))

        geomap[logrecno] = ''.join(dcid_parts)

    return geomap


def _build_2020_geomap(geof, is_national):
    """Builds a map from logical-record-number to DCID for 2020."""
    geomap = {}
    for line in geof:
        parts = line.strip().split('|')

        logrecno = parts[_GEOF_2020_LOGRECNO_COL]
        sumlev = parts[_GEOF_2020_SUMLEV_COL]

        if is_national:
            # This is national file. Extract only US geo
            if sumlev == _US_SUMLEV:
                geomap[logrecno] = 'country/USA'
            continue

        if sumlev not in _GEOF_2020_DCID_MAP:
            # Not an interesting summary-level
            continue

        # Combine the values in the columns.
        dcid_parts = ['geoId/']
        for c in _GEOF_2020_DCID_MAP[sumlev]:
            dcid_parts.append(parts[c])

        geomap[logrecno] = ''.join(dcid_parts)

    return geomap


def _build_geomap(year, geof, is_national):
    """Builds a map from logical-record-number to DCID."""
    if year == '2010':
        return _build_2010_geomap(geof, is_national)
    else:
        assert year == '2020'
        return _build_2020_geomap(geof, is_national)


def _generate_csv(year, dataf, csvw, geomap, verbose):
    """Reads the data from 'dataf' for 'year' and writes cleaned-csv to 'csvw'."""
    for line in dataf:
        parts = line.strip().split(_DATAF_DELIM_CHAR[year])

        cifsn = parts[_DATAF_CIFSN_COL]
        if cifsn not in _DATAF_STATVAR_MAP:
            # This file does not have any StatVars!
            return

        logrecno = parts[_DATAF_LOGRECNO_COL]
        if logrecno not in geomap:
            # This geo is not in our map.
            continue

        place_dcid = geomap[logrecno]

        # This is a legit file and geo.  Select the interesting StatVar columns.
        for var, sv in _DATAF_STATVAR_MAP[cifsn].items():
            # var looks like P0010001.
            tab = var[:4]
            idx = int(var[4:])

            # _TABLE_COLOFFSET_MAP for P001 contains 5, which is where P0010001 starts
            val_col = _TABLE_COLOFFSET_MAP[tab] + idx - 1

            if verbose:
                print('Emitting: ', place_dcid, ' : ', sv, ' : ',
                      parts[val_col])
            csvw.writerow(
                ['dcid:' + place_dcid, 'dcid:' + sv, parts[val_col], year])


def _process_geodir(year, geodir, output_dir, verbose):
    """Processes a directory for a state or US national and produces CSV."""

    is_national = os.path.basename(geodir) == 'National'
    csv_fname = os.path.join(output_dir, os.path.basename(geodir) + '.csv')
    print('Processing ', geodir, ' -> ', csv_fname)

    with open(csv_fname, 'w') as csvf:
        csvw = csv.writer(csvf)
        csvw.writerow(_CSV_COLUMNS)

        # For every zip-file in the directory. We only hope to find one.
        for zip_fname in glob.glob(os.path.join(geodir, '*.zip')):
            with zipfile.ZipFile(zip_fname) as zipf:

                # Build map out of geofile
                geo_fname = _get_geo_file(zipf)
                assert geo_fname, 'Did not find geo file in ' + zip_fname
                with io.TextIOWrapper(zipf.open(geo_fname, 'r'),
                                      encoding='ISO-8859-1') as geof:
                    geomap = _build_geomap(year, geof, is_national)
                    if verbose:
                        print('Geo Map:')
                        for k, v in geomap.items():
                            print('\t', k, ' -> ', v)

                # Build CSV out of datafiles
                for data_fname in zipf.namelist():
                    if data_fname == geo_fname:
                        continue
                    if not data_fname.endswith('pl'):
                        # 2010 directories have a .txt file, skip it
                        continue
                    with io.TextIOWrapper(zipf.open(data_fname, 'r'),
                                          encoding='ISO-8859-1') as dataf:
                        _generate_csv(year, dataf, csvw, geomap, verbose)


def process(raw_data_path, output_path, verbose):
    """Processes decennial census zip-files and produces CSV files."""
    for year in _YEARS:
        print('Processing year ' + year)

        year_output_dir = os.path.join(output_path, year)
        os.makedirs(year_output_dir, exist_ok=True)

        # Path that contains states
        parent_dir = os.path.join(raw_data_path, year, _DIR_PREFIX, '*')
        for geodir in glob.glob(parent_dir):
            if os.path.isdir(geodir):
                _process_geodir(year, geodir, year_output_dir, verbose)


def main(_):
    process(FLAGS.raw_data_path, FLAGS.output_path, FLAGS.verbose)


if __name__ == '__main__':
    app.run(main)
