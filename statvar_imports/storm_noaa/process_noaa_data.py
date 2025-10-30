import os
import re
import sys
import csv
from datetime import datetime
import pytz
import multiprocessing
from functools import partial
import glob
import json
import tempfile
import shutil

from absl import app
from absl import flags
from absl import logging

# Allows the following module imports to work when running as a script
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, _PROJECT_ROOT)
sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'util'))
from util import file_util
from util import latlng2place_mapsapi

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'gcs_api_key_path',
    'gs://unresolved_mcf/storms/latest/api_key.json',
    'Google Cloud Storage path for the API key JSON file.'
)
flags.DEFINE_string("input_dir", "sharded_noaa_data", "Directory containing sharded NOAA storm data.")
flags.DEFINE_string("output_csv", "noaa_storm_output/cleaned_storm_data.csv", "Path for the cleaned output CSV file.")
flags.DEFINE_string("temp_dir", "noaa_storm_output/temp", "Directory for temporary intermediate files.")

_WIND_SPEED_TYPES = {
    "EG": "WindEstimatedGust",
    "ES": "EstimatedSustainedWind",
    "MS": "MeasuredSustainedWind",
    "MG": "WindMeasuredGust"
}

_ZERO_MAP = {
    "H": 100, "K": 1000, "M": 1000000, "B": 1000000000, "T": 1000000000000
}

_TIMEZONE_MAP = {
    'AST': 'America/Puerto_Rico',
    'ADT': 'America/Halifax',
    'EST': 'America/New_York',
    'EDT': 'America/New_York',
    'CST': 'America/Chicago',
    'CDT': 'America/Chicago',
    'MST': 'America/Denver',
    'MDT': 'America/Denver',
    'PST': 'America/Los_Angeles',
    'PDT': 'America/Los_Angeles',
    'AKST': 'America/Anchorage',
    'AKDT': 'America/Anchorage',
    'HST': 'Pacific/Honolulu',
    'HDT': 'Pacific/Honolulu',
    'SST': 'Pacific/Pago_Pago',
    'SDT': 'Pacific/Pago_Pago',
    'CHST': 'Pacific/Guam',
}

def cost_to_int(cost_string):
    if not cost_string:
        return 0
    cost_string = cost_string.strip().upper()
    if not cost_string or cost_string == "0":
        return 0

    multiplier = 1
    last = cost_string[-1]
    if last in _ZERO_MAP:
        multiplier = _ZERO_MAP[last]
        cost_string = cost_string[:-1]

    try:
        return int(float(cost_string) * multiplier)
    except (ValueError, TypeError):
        return 0

def process_event_type(etype):
    return re.sub("[^A-Za-z]", "", etype.title())

def format_date(date_str, time_str, timezone_abbr):
    if not date_str or not time_str:
        return ""
    
    try:
        dt_str = f"{date_str} {time_str.zfill(4)}"
        dt_naive = datetime.strptime(dt_str, '%d-%b-%y %H%M')
        tz_name = _TIMEZONE_MAP.get(timezone_abbr)
        if not tz_name:
            return dt_naive.isoformat()
        tz = pytz.timezone(tz_name)
        dt_aware = tz.localize(dt_naive)
        return dt_aware.isoformat()
    except (ValueError, TypeError):
        return ""

def valid_lat(lat):
    if not lat: return False
    try:
        return -90 <= float(lat) <= 90
    except (ValueError, TypeError):
        return False

def valid_lng(lng):
    if not lng: return False
    try:
        return -180 <= float(lng) <= 180
    except (ValueError, TypeError):
        return False

def process_shard(shard_file, api_key):
    """Processes a single shard file and writes its output to a temporary CSV file."""
    shard_name = os.path.basename(shard_file)
    logging.info(f"Starting processing for shard: {shard_name}")
    
    ll2p = latlng2place_mapsapi.Resolver(api_key=api_key)
    processed_rows = set()
    
    temp_output_file = os.path.join(FLAGS.temp_dir, f"processed_{shard_name}")

    with open(temp_output_file, "w", newline="") as f_out:
        writer = csv.writer(f_out, quoting=csv.QUOTE_ALL)
        with file_util.FileIO(shard_file, "r") as f_in:
            reader = csv.DictReader(f_in)
            for row in reader:
                try:
                    if not row.get("BEGIN_LAT") or not row.get("BEGIN_LON"):
                        continue
                    
                    geoids = ll2p.resolve(row["BEGIN_LAT"], row["BEGIN_LON"])
                    if not geoids:
                        logging.warning(f"Could not resolve geoid for lat/lng: {row['BEGIN_LAT']},{row['BEGIN_LON']} in {shard_name}")
                        continue
                    
                    observation_about = geoids[0]
                    date = f"{row['BEGIN_YEARMONTH'][:4]}-{row['BEGIN_YEARMONTH'][4:]}-{row['BEGIN_DAY'].zfill(2)}"
                    event_type = process_event_type(row["EVENT_TYPE"])

                    begin_date_str = datetime.strptime(f"{row['BEGIN_YEARMONTH']}{row['BEGIN_DAY']}", '%Y%m%d').strftime('%d-%b-%y') if row.get('BEGIN_YEARMONTH') and row.get('BEGIN_DAY') else ''
                    end_date_str = datetime.strptime(f"{row['END_YEARMONTH']}{row['END_DAY']}", '%Y%m%d').strftime('%d-%b-%y') if row.get('END_YEARMONTH') and row.get('END_DAY') else ''

                    start_date = format_date(begin_date_str, row.get("BEGIN_TIME"), row.get("CZ_TIMEZONE"))
                    end_date = format_date(end_date_str or begin_date_str, row.get("END_TIME"), row.get("CZ_TIMEZONE"))

                    event_id = row.get("EVENT_ID")
                    episode_id = row.get("EPISODE_ID")

                    storm_event = f"stormEvent/nws{event_id}" if event_id else ""
                    storm_episode = f"stormEpisode/nws{episode_id}" if episode_id else ""
                    storm_episode_name = f"Storm Episode NWS {episode_id}" if episode_id else ""

                    begin_lat, begin_lon = row.get("BEGIN_LAT"), row.get("BEGIN_LON")
                    end_lat, end_lon = row.get("END_LAT"), row.get("END_LON")

                    start_loc_str = f"[LatLong {begin_lat} {begin_lon}]" if valid_lat(begin_lat) and valid_lng(begin_lon) else ""
                    end_loc_str = f"[LatLong {end_lat} {end_lon}]" if valid_lat(end_lat) and valid_lng(end_lon) else ""

                    location, startLocation, endLocation = "", "", ""
                    if start_loc_str and (start_loc_str == end_loc_str or not end_loc_str):
                        location = start_loc_str
                    elif end_loc_str and not start_loc_str:
                        location = end_loc_str
                    elif start_loc_str and end_loc_str:
                        startLocation, endLocation = start_loc_str, end_loc_str

                    property_damage = cost_to_int(row.get("DAMAGE_PROPERTY", "0"))
                    crop_damage = cost_to_int(row.get("DAMAGE_CROPS", "0")),
                    property_damage_value = f"[USDollar {property_damage}]" if property_damage else ""
                    crop_damage_value = f"[USDollar {crop_damage}]" if crop_damage else ""

                    unit = "MilesPerHour" if row.get("MAGNitude_TYPE") else "Inch"
                    precipitation_accumulation, precipitation_type = (f"[{unit} {row.get('MAGNITUDE')}]", "dcs:Hail") if unit == "Inch" and row.get("MAGNITUDE") else ( "", "")
                    wind_speed, wind_speed_type = (f"[{unit} {row.get('MAGNITUDE')}]", f"dcs:{_WIND_SPEED_TYPES[row.get('MAGNITUDE_TYPE')]}") if row.get("MAGNITUDE_TYPE") in _WIND_SPEED_TYPES and row.get("MAGNITUDE") else ( "", "")
                    cause = "dcs:" + row.get("FLOOD_CAUSE").replace("/", "Or").replace(" ", "") if row.get("FLOOD_CAUSE") else ""
                    
                    max_classification, length_traveled, width = "", "", ""
                    if row.get("EVENT_TYPE", "").lower() == "tornado":
                        if row.get("TOR_F_SCALE"): max_classification = f"dcs:TornadoIntensity{row.get('TOR_F_SCALE')}"
                        if row.get("TOR_LENGTH"): length_traveled = f"[Mile {row.get('TOR_LENGTH')}]"
                        if row.get("TOR_WIDTH"): width = f"[Foot {row.get('TOR_WIDTH')}]"
                    
                    description = row.get("EVENT_NARRATIVE", "").replace("\"", "&quot;").replace("\\", "&sol;")

                    output_row = [
                        storm_event, storm_episode, storm_episode_name, observation_about, date, event_type,
                        row.get("INJURIES_DIRECT", 0), row.get("INJURIES_INDIRECT", 0), row.get("DEATHS_DIRECT", 0), row.get("DEATHS_INDIRECT", 0),
                        property_damage, crop_damage, property_damage_value, crop_damage_value, start_date, end_date,
                        location, startLocation, endLocation, begin_lat, begin_lon, end_lat, end_lon,
                        unit, wind_speed, wind_speed_type, cause, description, precipitation_accumulation, precipitation_type,
                        max_classification, length_traveled, width,
                        row.get("EPISODE_ID", ""), row.get("EVENT_ID", ""), row.get("STATE", ""), row.get("STATE_FIPS", ""), row.get("YEAR", ""),
                        row.get("MONTH_NAME", ""), row.get("CZ_TYPE", ""), row.get("CZ_FIPS", ""), row.get("CZ_NAME", ""), row.get("WFO", ""),
                        row.get("BEGIN_DATE_TIME", ""), row.get("CZ_TIMEZONE", ""), row.get("END_DATE_TIME", ""), row.get("SOURCE", ""),
                        row.get("MAGNITUDE_TYPE", ""), row.get("FLOOD_CAUSE", ""), row.get("CATEGORY", ""), row.get("TOR_OTHER_WFO", ""),
                        row.get("TOR_OTHER_CZ_STATE", ""), row.get("TOR_OTHER_CZ_FIPS", ""), row.get("TOR_OTHER_CZ_NAME", ""),
                        row.get("BEGIN_RANGE", ""), row.get("BEGIN_AZIMUTH", ""), row.get("BEGIN_LOCATION", ""), row.get("END_RANGE", ""),
                        row.get("END_AZIMUTH", ""), row.get("END_LOCATION", ""), row.get("EPISODE_NARRATIVE", ""),
                        row.get("EVENT_NARRATIVE", ""), row.get("DATA_SOURCE", ""),
                    ]
                    row_tuple = tuple(output_row)
                    if row_tuple not in processed_rows:
                        processed_rows.add(row_tuple)
                        writer.writerow(output_row)
                except Exception as e:
                    logging.error(f"Error processing row in {shard_name}: {row}\n{e}")
    
    logging.info(f"Finished processing for shard: {shard_name}")
    return temp_output_file

def get_api_key_from_gcs():
    """
    Retrieves the Google Maps API key from a JSON file in a GCS bucket.
    """
    logging.info("--- Starting GCS File Transfer for API key ---")
    local_temp_dir = tempfile.mkdtemp()
    api_key = None
    try:
        gcs_source_path = FLAGS.gcs_api_key_path
        local_filepath = os.path.join(local_temp_dir, 'api_key.json')

        file_util.file_copy(gcs_source_path, local_filepath)
        logging.info(f"Copied '{gcs_source_path}' to '{local_filepath}'.")

        with open(local_filepath, 'r') as f:
            api_keys_data = json.load(f)

        api_key = api_keys_data.get("api-key")
        if not api_key:
            logging.fatal("'api-key' not found in the JSON file.")
            raise RuntimeError("API key not found in JSON.")

        return api_key

    except Exception as e:
        logging.fatal(
            f"An unexpected error occurred during API key retrieval: {e}.")
        raise RuntimeError("Unexpected error during API key retrieval.") from e

    finally:
        shutil.rmtree(local_temp_dir, ignore_errors=True)
        logging.info("Temporary directory cleaned up.")

def main(argv):
    logging.set_verbosity(logging.INFO)
    
    api_key = get_api_key_from_gcs()

    # Setup directories
    output_dir = os.path.dirname(FLAGS.output_csv)
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    if not os.path.exists(FLAGS.temp_dir): os.makedirs(FLAGS.temp_dir)

    shard_files = glob.glob(os.path.join(FLAGS.input_dir, "fips_*.csv"))
    if not shard_files:
        logging.error(f"No shard files found in {FLAGS.input_dir}. Did you run shard_noaa_data.py first?")
        return

    # Use multiprocessing to process shards in parallel
    num_processes = multiprocessing.cpu_count()
    logging.info(f"Starting parallel processing with {num_processes} workers for {len(shard_files)} shards.")
    
    with multiprocessing.Pool(processes=num_processes) as pool:
        worker_func = partial(process_shard, api_key=api_key)
        temp_files = pool.map(worker_func, shard_files)

    # Combine results from temporary files
    logging.info("Combining results from all processed shards.")
    header = [
        "stormEvent", "stormEpisode", "stromEpisodeName", "observationAbout", "observationDate", "eventType", "directInjuries",
        "indirectInjuries", "directDeaths", "indirectDeaths", "propertyDamage", "cropDamage", "propertyDamageValue", "cropDamageValue",
        "startDate", "endDate", "location", "startLocation", "endLocation", "BEGIN_LAT", "BEGIN_LON", "END_LAT", "END_LON",
        "unit", "windSpeed", "windSpeedType", "cause", "description", "precipitationAccumulation", "precipitationType",
        "maxClassification", "lengthTraveled", "width", "EPISODE_ID", "EVENT_ID", "STATE", "STATE_FIPS", "YEAR", "MONTH_NAME",
        "CZ_TYPE", "CZ_FIPS", "CZ_NAME", "WFO", "BEGIN_DATE_TIME", "CZ_TIMEZONE", "END_DATE_TIME", "SOURCE", "MAGNITUDE_TYPE",
        "FLOOD_CAUSE", "CATEGORY", "TOR_OTHER_WFO", "TOR_OTHER_CZ_STATE", "TOR_OTHER_CZ_FIPS", "TOR_OTHER_CZ_NAME",
        "BEGIN_RANGE", "BEGIN_AZIMUTH", "BEGIN_LOCATION", "END_RANGE", "END_AZIMUTH", "END_LOCATION",
        "EPISODE_NARRATIVE", "EVENT_NARRATIVE", "DATA_SOURCE"
    ]
    
    with open(FLAGS.output_csv, "w", newline="") as f_out:
        writer = csv.writer(f_out, quoting=csv.QUOTE_ALL)
        writer.writerow(header)
        for temp_file in filter(None, temp_files):
            with open(temp_file, "r") as f_in:
                reader = csv.reader(f_in)
                for row in reader:
                    writer.writerow(row)
            try:
                os.remove(temp_file)
            except OSError as e:
                logging.error(f"Error removing temporary file {temp_file}: {e}")

    logging.info(f"Successfully created cleaned data file at {FLAGS.output_csv}")
    try:
        # Check if temp dir is empty before trying to remove it
        if not os.listdir(FLAGS.temp_dir):
            os.rmdir(FLAGS.temp_dir)
            logging.info(f"Successfully removed temporary directory {FLAGS.temp_dir}")
    except OSError as e:
        logging.error(f"Error removing temporary directory {FLAGS.temp_dir}: {e}")

if __name__ == "__main__":
    app.run(main)
