# Copyright 2019 Google LLC
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
'''
Generates cleaned CSV and template MCF files for the EPA AirData.

Usage: python3 air_quality.py <end_year>
'''
import csv, os, sys, re, requests, io, zipfile
from urllib3.util import Retry

from absl import app
from absl import flags
from absl import logging
from datetime import datetime

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_FLAGS = flags.FLAGS

flags.DEFINE_integer(
    'data_start_year', int(os.getenv('START_YEAR', '1980')),
    'Process data starting from this year.')
flags.DEFINE_integer(
    'data_end_year',
    int(os.getenv('END_YEAR', 0)),
    'Process data upto this year. Defaults to the previous calendar year.')

# AQS parameter codes: https://aqs.epa.gov/aqsweb/documents/codetables/parameters.html
POLLUTANTS = {
    '44201': 'Ozone',
    '42401': 'SO2',
    '42101': 'CO',
    '42602': 'NO2',
    '88101': 'PM2.5',
    '81102': 'PM10',
}

UNIT_MAP = {
    'micrograms/cubic meter (lc)': 'MicrogramsPerCubicMeter_lc',
    'micrograms/cubic meter (25 c)': 'MicrogramsPerCubicMeter_25C',
    'parts per million': 'PartsPerMillion',
    'parts per billion': 'PartsPerBillion',
}

CSV_COLUMNS = [
    'Date', 'Site_Number', 'Site_Name', 'Site_Location', 'County', 'Units',
    'Method', 'POC', 'Mean', 'Max', 'AQI', 'Mean_SV', 'Max_SV', 'AQI_SV'
]

# Template MCF for StatVarObservation
TEMPLATE_MCF = '''
Node: E:EPA_AirQuality->E1
typeOf: dcs:StatVarObservation
variableMeasured: C:EPA_AirQuality->Mean_SV
measurementMethod: C:EPA_AirQuality->Method
observationDate: C:EPA_AirQuality->Date
observationAbout: E:EPA_AirQuality->E0
observationPeriod: "P1D"
value: C:EPA_AirQuality->Mean
unit: C:EPA_AirQuality->Units
airQualitySiteMonitor: C:EPA_AirQuality->POC

Node: E:EPA_AirQuality->E2
typeOf: dcs:StatVarObservation
variableMeasured: C:EPA_AirQuality->Max_SV
measurementMethod: C:EPA_AirQuality->Method
observationDate: C:EPA_AirQuality->Date
observationAbout: E:EPA_AirQuality->E0
observationPeriod: "P1D"
value: C:EPA_AirQuality->Max
unit: C:EPA_AirQuality->Units
airQualitySiteMonitor: C:EPA_AirQuality->POC

Node: E:EPA_AirQuality->E3
typeOf: dcs:StatVarObservation
variableMeasured: C:EPA_AirQuality->AQI_SV
measurementMethod: C:EPA_AirQuality->Method
observationDate: C:EPA_AirQuality->Date
observationAbout: E:EPA_AirQuality->E0
observationPeriod: "P1D"
value: C:EPA_AirQuality->AQI
airQualitySiteMonitor: C:EPA_AirQuality->POC
'''

# Template MCF for Air Quality Site
TEMPLATE_MCF_AIR_QUALITY_SITE = '''
Node: E:EPA_AirQuality->E0
typeOf: dcs:AirQualitySite
dcid: C:EPA_AirQuality->Site_Number
name: C:EPA_AirQuality->Site_Name
location: C:EPA_AirQuality->Site_Location
containedInPlace: C:EPA_AirQuality->County
'''


# Convert to CamelCase (splitting on non-alphanumeric characters)
# Example: Parts per million -> PartsPerMillion
def get_camel_case(s):
    if not s or s.strip() in ('', '-', '-'):
        return ''
    parts = re.split(r'[^a-zA-Z0-9]+', s)
    return ''.join(p.capitalize() for p in parts if p)


# Example: Ozone 8-hour 2015 -> Ozone_8hour_2015
def get_pollutant_standard(s):
    return s.replace(' ', '_').replace('-', '')


def create_csv(csv_file_path):
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=CSV_COLUMNS,
                                lineterminator='\n')
        writer.writeheader()


def create_sites_mcf(sites_mcf_file_path):
    with open(sites_mcf_file_path, 'w', encoding='utf-8') as f_out:
        pass


def write_sites_mcf(sites_mcf_file_path, sites_dict):
    """Writes AirQualitySite MCF nodes to file, sorted by site DCID."""
    with open(sites_mcf_file_path, 'w', encoding='utf-8') as f_out:
        for site_number in sorted(sites_dict.keys()):
            site_info = sites_dict[site_number]
            site_name = site_info.get('name', '')
            lat = site_info.get('lat', '')
            lon = site_info.get('lon', '')
            site_county = site_info.get('county', '')
            location_prop = (f'location: [latLong {lat} {lon}]\n'
                             if lat and lon else '')
            f_out.write(f'Node: dcid:{site_number}\n'
                        f'typeOf: dcs:AirQualitySite\n'
                        f'name: "{site_name}"\n'
                        f'{location_prop}'
                        f'containedInPlace: {site_county}\n\n')


def write_csv(csv_file_path,
              reader,
              sites_mcf_file_path='EPA_AirQuality_sites.mcf',
              seen_sites=None,
              sites_dict=None):
    if sites_mcf_file_path == 'EPA_AirQuality_sites.mcf':
        csv_dir = os.path.dirname(csv_file_path)
        if csv_dir:
            sites_mcf_file_path = os.path.join(csv_dir,
                                               'EPA_AirQuality_sites.mcf')
        else:
            sites_mcf_file_path = os.path.join(_SCRIPT_DIR,
                                               'EPA_AirQuality_sites.mcf')

    existing_file_sites = set()
    if sites_mcf_file_path and os.path.exists(sites_mcf_file_path):
        with open(sites_mcf_file_path, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                stripped = line.strip()
                if stripped.startswith('Node: dcid:'):
                    site_id = stripped.split('Node: dcid:', 1)[1].strip()
                    existing_file_sites.add(site_id)
                    if seen_sites is not None and isinstance(seen_sites, set):
                        seen_sites.add(site_id)

    local_sites = {} if sites_dict is None else sites_dict

    with open(csv_file_path, 'a', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=CSV_COLUMNS,
                                lineterminator='\n')
        monitors = {}
        keys = set()
        for observation in reader:
            state_code = str(
                observation.get('State Code', '')).strip().upper().zfill(2)
            # Skip cross-border monitors outside US (80 = Mexico, CC = Canada)
            if state_code in ('80', 'CC'):
                continue
            county_code = str(
                observation.get('County Code', '')).strip().zfill(3)
            site_num = str(
                observation.get('Site Num', '')).strip().zfill(4)
            site_number = f'epa/{state_code}{county_code}{site_num}'
            lat = str(observation.get('Latitude', '') or '').strip()
            lon = str(observation.get('Longitude', '') or '').strip()
            site_county = f'dcid:geoId/{state_code}{county_code}'
            site_name = (observation.get('Local Site Name') or '').replace(
                '\r', ' ').replace('\n', ' ').strip().replace('"', r'\"')

            if site_number not in local_sites:
                local_sites[site_number] = {
                    'name': site_name,
                    'lat': lat,
                    'lon': lon,
                    'county': site_county,
                }
            else:
                if not local_sites[site_number]['lat'] and lat:
                    local_sites[site_number]['lat'] = lat
                    local_sites[site_number]['lon'] = lon
                if not local_sites[site_number]['name'] and site_name:
                    local_sites[site_number]['name'] = site_name
            if seen_sites is not None and isinstance(seen_sites, set):
                seen_sites.add(site_number)

            # For a given site and pollutant standard, select the same monitor
            monitor_key = (
                state_code,
                county_code,
                site_num,
                get_pollutant_standard(observation['Pollutant Standard']),
            )
            if monitor_key not in monitors:
                monitors[monitor_key] = observation['POC']
            elif monitors[monitor_key] != observation['POC']:
                continue
            key = (
                observation['Date Local'],
                state_code,
                county_code,
                site_num,
                get_pollutant_standard(observation['Pollutant Standard']),
            )
            if key in keys:
                continue
            keys.add(key)
            suffix = POLLUTANTS[observation["Parameter Code"]]
            county = f'dcid:geoId/{state_code}{county_code}'
            raw_unit_str = observation.get('Units of Measure', '')
            unit = UNIT_MAP.get(
                raw_unit_str.strip().lower()) if raw_unit_str else ''
            if not unit and raw_unit_str:
                unit = get_camel_case(raw_unit_str)
            new_row = {
                'Date':
                    observation['Date Local'],
                'Site_Number':
                    site_number,
                'Site_Name':
                    observation['Local Site Name'],
                'Site_Location':
                    f'[latLong {lat} {lon}]' if lat and lon else '',
                'County':
                    county,
                'POC':
                    observation['POC'],
                'Units':
                    unit,
                'Method':
                    get_pollutant_standard(
                        observation['Pollutant Standard']),
                'Mean':
                    observation['Arithmetic Mean'],
                'Max':
                    observation['1st Max Value'],
                'AQI':
                    observation['AQI'],
                'Mean_SV':
                    f'dcs:Mean_Concentration_AirPollutant_{suffix}',
                'Max_SV':
                    f'dcs:Max_Concentration_AirPollutant_{suffix}',
                'AQI_SV':
                    f'dcs:AirQualityIndex_AirPollutant_{suffix}',
            }
            writer.writerow(new_row)

    if sites_mcf_file_path:
        with open(sites_mcf_file_path, 'a', encoding='utf-8') as f_sites:
            for site_number, site_info in local_sites.items():
                if site_number not in existing_file_sites:
                    s_name = site_info.get('name', '')
                    s_lat = site_info.get('lat', '')
                    s_lon = site_info.get('lon', '')
                    s_county = site_info.get('county', '')
                    location_prop = (f'location: [latLong {s_lat} {s_lon}]\n'
                                     if s_lat and s_lon else '')
                    f_sites.write(f'Node: dcid:{site_number}\n'
                                  f'typeOf: dcs:AirQualitySite\n'
                                  f'name: "{s_name}"\n'
                                  f'{location_prop}'
                                  f'containedInPlace: {s_county}\n\n')
                    existing_file_sites.add(site_number)


def write_tmcf(tmcf_file_path):
    with open(tmcf_file_path, 'w', encoding='utf-8') as f_out:
        f_out.write(TEMPLATE_MCF_AIR_QUALITY_SITE)
        f_out.write(TEMPLATE_MCF)


def main(argv):
    if len(argv) > 1:
        raise app.UsageError(f'Too many command-line arguments: {argv[1:]}')

    start_year = _FLAGS.data_start_year
    end_year = _FLAGS.data_end_year or (datetime.now().year - 1)
    logging.info(f'Processing from {start_year} upto {end_year}')

    csv_file = os.path.join(_SCRIPT_DIR, 'EPA_AirQuality.csv')
    sites_mcf_file = os.path.join(_SCRIPT_DIR, 'EPA_AirQuality_sites.mcf')
    tmcf_file = os.path.join(_SCRIPT_DIR, 'EPA_AirQuality.tmcf')

    csv_tmp_file = f'{csv_file}.tmp'
    sites_mcf_tmp_file = f'{sites_mcf_file}.tmp'

    create_csv(csv_tmp_file)
    create_sites_mcf(sites_mcf_tmp_file)
    sites_dict = {}
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=Retry(
        total=10,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    ))
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    success = False
    try:
        for pollutant in POLLUTANTS:
            for year in range(start_year, int(end_year) + 1):
                filename = f'daily_{pollutant}_{year}'
                url = f'https://aqs.epa.gov/aqsweb/airdata/{filename}.zip'
                logging.info(f'Processing {filename} from {url}')
                try:
                    response = session.get(url, timeout=120)
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    if e.response is not None and e.response.status_code == 404:
                        logging.warning(
                            f'Archive not found for {filename} (404), skipping: {e}'
                        )
                        continue
                    raise
                with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                    with zf.open(f'{filename}.csv', 'r') as infile:
                        reader = csv.DictReader(
                            io.TextIOWrapper(infile, 'utf-8'))
                        write_csv(csv_tmp_file, reader, sites_dict=sites_dict)
        write_sites_mcf(sites_mcf_tmp_file, sites_dict)
        os.replace(csv_tmp_file, csv_file)
        os.replace(sites_mcf_tmp_file, sites_mcf_file)
        write_tmcf(tmcf_file)
        success = True
    finally:
        if not success:
            if os.path.exists(csv_tmp_file):
                os.remove(csv_tmp_file)
            if os.path.exists(sites_mcf_tmp_file):
                os.remove(sites_mcf_tmp_file)


if __name__ == '__main__':
    app.run(main)
