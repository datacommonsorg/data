# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
GRIB2 to Data Commons CSV Processor

This script extracts meteorological variables from GRIB2 files 
and maps them to standardized Data Commons identifiers (dcids).

Key Features:
1. Multi-processing: Uses a Pool of workers to process GRIB messages in parallel.
2. Coordinate Transformation: Converts 0-360 longitude to -180 to 180 range.
3. DCID Mapping: Dynamically constructs Data Commons IDs based on parameter type 
   and vertical levels (e.g., Isobaric, Height Above Ground).
4. Data Cleaning: Handles bitmaps, missing values, and unit conversions 
   (e.g., scaling land/ice cover).
"""

import time
import pygrib
import numpy as np
import csv as py_csv
import re
import os
import json
import io
from pathlib import Path
from multiprocessing import Pool, cpu_count
from absl import app, flags, logging
from google.cloud import storage
from google.api_core import exceptions

logging.set_verbosity(logging.INFO)

# --- FLAG DEFINITIONS ---
FLAGS = flags.FLAGS
flags.DEFINE_string('project_id', 'datcom', 'GCP Project ID.')
flags.DEFINE_string('bucket_name', 'datcom-prod-imports',
                    'GCS Bucket for state storage.')
flags.DEFINE_string('state_path',
                    'scripts/noaa_gfs/NOAA_GlobalForecastSystem/state.json',
                    'Path to state.json in GCS.')
flags.DEFINE_string('output_gcs_prefix',
                    'scripts/noaa_gfs/NOAA_GlobalForecastSystem/output/',
                    'GCS prefix for CSVs.')

flags.DEFINE_string('input', 'input_files',
                    'Directory containing input GRIB files.')
flags.DEFINE_string('forecast_hour', '000',
                    'The forecast hour (e.g., 000, 003).')
flags.DEFINE_integer('num_workers', cpu_count(),
                     'Number of parallel processes.')

# --- PARAMETER & LEVEL MAPPING ---
# Maps short GRIB names to standardized Data Commons variable names
NAME_MAP = {
    "prmsl": "PRMSL",
    "clwmr": "CLMR",
    "icmr": "ICMR",
    "rwmr": "RWMR",
    "snmr": "SNMR",
    "grle": "GRLE",
    "refd": "REFD",
    "refc": "REFC",
    "vis": "VIS",
    "u": "UGRD",
    "v": "VGRD",
    "vrate": "VRATE",
    "gust": "GUST",
    "gh": "HGT",
    "t": "TMP",
    "r": "RH",
    "q": "SPFH",
    "w": "VVEL",
    "wz": "DZDT",
    "absv": "ABSV",
    "o3mr": "O3MR",
    "tcc": "TCDC",
    "hindex": "HINDEX",
    "mslet": "MSLET",
    "sp": "PRES",
    "orog": "HGT",
    "st": "TSOIL",
    "soilw": "SOILW",
    "soill": "SOILL",
    "cnwat": "CNWAT",
    "sdwe": "WEASD",
    "sde": "SNOD",
    "sithick": "ICETK",
    "2t": "TMP",
    "2sh": "SPFH",
    "2d": "DPT",
    "2r": "RH",
    "aptmp": "APTMP",
    "10u": "UGRD",
    "10v": "VGRD",
    "cpofp": "CPOFP",
    "prate": "PRATE",
    "csnow": "CSNOW",
    "cicep": "CICEP",
    "cfrzr": "CFRZR",
    "crain": "CRAIN",
    "fsr": "SFCR",
    "fricv": "FRICV",
    "veg": "VEG",
    "slt": "SOTYP",
    "wilt": "WILT",
    "fldcp": "FLDCP",
    "sunsd": "SUNSD",
    "lftx": "LFTX",
    "cape": "CAPE",
    "cin": "CIN",
    "pwat": "PWAT",
    "cwat": "CWAT",
    "tozne": "TOZNE",
    "lcc": "LCDC",
    "mcc": "MCDC",
    "hcc": "HCDC",
    "hlcy": "HLCY",
    "ustm": "USTM",
    "vstm": "VSTM",
    "trpp": "PRES",
    "icaht": "ICAHT",
    "vwsh": "VWSH",
    "pres": "PRES",
    "100u": "UGRD",
    "100v": "VGRD",
    "4lftx": "4LFTX",
    "pt": "POT",
    "plpl": "PLPL",
    "lsm": "LAND",
    "ci": "ICEC",
    "sit": "ICETMP"
}

# Mapping for (Data Commons Base Property, Unit)
PARAM_MAP = {
    'PRMSL': ('Pressure_Place', 'Pascal'),
    'MSLET': ('MSLPEtaReduction_Pressure_Atmosphere', 'Pascal'),
    'TMP': ('Temperature_Place', 'Kelvin'),
    'DPT': ('DewPointTemperature_Atmosphere', 'Kelvin'),
    'APTMP': ('Apparent_Temperature_Place', 'Kelvin'),
    'HGT': ('GeopotentialHeight_Place', 'GeopotentialMeters'),
    'RH': ('Humidity_Place', 'Percent'),
    'SPFH': ('Humidity_Place', ''),
    'UGRD': ('WindSpeed_Place', 'MeterPerSecond'),
    'VGRD': ('WindSpeed_Place', 'MeterPerSecond'),
    'VIS': ('Visibility_Place', 'Meter'),
    'GUST': ('Max_WindSpeed_Place', 'MeterPerSecond'),
    'PRES': ('Pressure_Atmosphere', 'Pascal'),
    'CLMR': ('MixingRatio_Cloud', ''),
    'ICMR': ('MixingRatio_Ice', ''),
    'RWMR': ('MixingRatio_Rainwater', ''),
    'SNMR': ('MixingRatio_Snow', ''),
    'GRLE': ('Count_Graupel', ''),
    'REFD': ('Reflectivity_Place', 'Decibel'),
    'REFC': ('Max_CompositeReflectivity_Place', 'Decibel'),
    'VVEL': ('PressureVerticalVelocity_Velocity_Place', 'PascalPerSecond'),
    'DZDT': ('GeometricVerticalVelocity_Velocity_Place', 'MeterPerSecond'),
    'ABSV': ('AbsoluteVorticity_Place', 'InverseSecond'),
    'O3MR': ('Ozone_MixingRatio_Atmosphere', ''),
    'VRATE': ('VentilationRate_Place', 'SquareMeterPerSecond'),
    'TSOIL': ('Temperature_Soil', 'Kelvin'),
    'SOILW': ('VolumetricSoilMoisture_Soil', ''),
    'SOILL': ('LiquidWaterContent_Soil', ''),
    'TCDC': ('CloudCover_Place', 'Percent'),
    'HINDEX': ('HainesIndex_Place', ''),
    'CNWAT': ('CloudWaterContent_Atmosphere', 'KilogramPerMeterSquared'),
    'WEASD': ('SnowWaterEquivalent_Place', 'KilogramPerMeterSquared'),
    'SNOD': ('Depth_Snow', 'Meter'),
    'ICETK': ('Thickness_Ice', 'Meter'),
    'ICEG': ('GrowthRate_Count_Ice', 'MeterPerSecond'),
    'CPOFP': ('FrozenPrecipitation_Place', 'Percent'),
    'PRATE': ('PrecipitationRate_Place', ''),
    'CSNOW': ('Occurrence_Place_SurfaceLevel_Snow', ''),
    'CICEP': ('Occurrence_Place_SurfaceLevel_IcePellets', ''),
    'CFRZR': ('Occurrence_Place_SurfaceLevel_FreezingRain', ''),
    'CRAIN': ('Occurrence_Place_SurfaceLevel_Rain', ''),
    'VEG': ('Area_Place_SurfaceLevel_Vegetation', 'Percent'),
    'SFCR': ('SurfaceRoughness_Place', 'Meter'),
    'FRICV': ('FrictionalVelocity_Place', 'MeterPerSecond'),
    'SOTYP': ('SoilType_Soil', ''),
    'WILT': ('WiltingPoint_Soil', ''),
    'FLDCP': ('FieldCapacity_Soil', ''),
    'SUNSD': ('SunshineDuration_Place', 'Second'),
    'LFTX': ('SurfaceLiftedIndex_Atmosphere', 'Kelvin'),
    '4LFTX': ('BestLiftedIndex_Atmosphere', 'Kelvin'),
    'CAPE':
        ('ConvectiveAvailablePotentialEnergy_Atmosphere', 'JoulePerKilogram'),
    'CIN': ('ConvectiveInhibition_Atmosphere', 'JoulePerKilogram'),
    'PWAT': ('PrecipitableWater_Place', 'KilogramPerMeterSquared'),
    'CWAT': ('CloudWater_Place', 'KilogramPerMeterSquared'),
    'TOZNE': ('Concentration_Atmosphere_Ozone', ''),
    'LCDC': ('CloudCover_Place_LowCloudLayer', 'Percent'),
    'MCDC': ('CloudCover_Place_MiddleCloudLayer', 'Percent'),
    'HCDC': ('CloudCover_Place_HighCloudLayer', 'Percent'),
    'HLCY':
        ('StormRelativeHelicity_Atmosphere', 'MetersSquaredPerSecondSquared'),
    'USTM': ('StormMotion_Atmosphere', 'MeterPerSecond'),
    'VSTM': ('StormMotion_Atmosphere', 'MeterPerSecond'),
    'ICAHT': ('ICAOStandardAtmosphere_Altitude_Atmosphere', 'Meter'),
    'VWSH': ('WindShear_Atmosphere', 'InverseSecond'),
    'POT': ('PotentialTemperature_Atmosphere', 'Kelvin'),
    'HPBL': ('PlanetaryBoundaryLayer_Altitude_Atmosphere', 'Meter'),
    'PLPL': ('LiftedParcelLevel_Pressure_Atmosphere', 'Pascal'),
    'LAND': ('Area_LandCover', 'SquareDegree'),
    'ICEC': ('Area_IceCover', 'SquareDegree'),
    'ICETMP': ('Temperature_SeaIce', 'Kelvin'),
}

STATIC_LEVEL_MAP = {
    "mean sea level": "0MetersAboveMeanSeaLevel",
    "surface": "SurfaceLevel",
    "planetary boundary layer": "PlanetaryBoundaryLayer",
    "0c isotherm": "Isotherm0C",
    "highest tropospheric freezing level": "HighestTroposphericFreezingLevel"
}


# --- HELPER FUNCTIONS ---
def format_level_dcid(level):
    """
    Standardizes raw GFS level strings into Data Commons naming conventions.
    
    Example: '2 m above ground' -> '2Meter'
             '1000 mb' -> '1000Millibar'
    """
    l = str(level).lower().strip()
    if l in STATIC_LEVEL_MAP:
        return STATIC_LEVEL_MAP[l]

    # Handle vertical altitude (Above Mean Sea Level)
    if "m above mean sea level" in l:
        val = l.split(" ")[0].replace("-", "To")
        return f"{val}MetersAboveMeanSeaLevel"

    if "entire atmosphere" in l:
        return ""
    if "low cloud layer" in l:
        return "LowCloudLayer"
    if "middle cloud layer" in l:
        return "MiddleCloudLayer"
    if "high cloud layer" in l:
        return "HighCloudLayer"
    if "cloud ceiling" in l:
        return "CloudCeiling"

    # Handle hybrid vertical coordinates
    if "hybrid level" in l:
        val = l.split(" ")[0]
        return "LowestHybridLevel" if val == "1" else f"{val}HybridLevel"

    # Handle sub-surface depths
    if "m below ground" in l:
        match = re.search(r'([0-9.]+)-?([0-9.]*)', l)
        if match:
            start, end = match.group(1), match.group(2)
            return f"{start}To{end}Meter" if end else f"{start}Meter"

    # Handle standard height above ground
    if "m above ground" in l:
        val = l.split(" ")[0].replace("-", "To")
        return f"{val}Meter"

    # Handle pressure levels (Millibars)
    if "mb" in l:
        val = l.split(" ")[0].replace("-", "To")
        return f"{val}Millibar"

    # Handle sigma (pressure-normalized) levels
    if "sigma" in l:
        val = l.split(" ")[0].replace("-", "To")
        suffix = "SigmaLayer" if "layer" in l else "SigmaLevel"
        return f"{val}{suffix}"

    # Handle Potential Vorticity units (PVU)
    if "pv=" in l:
        return "PotentialVorticityNeg2PVU" if (
            "neg" in l or "-2" in l) else "PotentialVorticity2PVU"
    return "".join(
        word.capitalize() for word in l.replace("-", " ").split() if word)


def construct_dcid(param_raw, level_raw):
    """
    Orchestrates the creation of the final Data Commons Identifier.
    Combines the base property with level specifics and directional components (U/V).
    """
    param = str(param_raw).upper()
    level_clean = format_level_dcid(level_raw)
    mapping = PARAM_MAP.get(param)

    base = mapping[0] if mapping else param

    # Special case: Humidity (DCID has specific structure)
    if param == 'RH' and not level_clean:
        return "dcid:Humidity_RelativeHumidity"

    # Construct base DCID
    if level_clean and level_clean in base:
        dcid = f"dcid:{base}"
    elif not level_clean:
        dcid = f"dcid:{base}"
    else:
        dcid = f"dcid:{base}_{level_clean}"

    # Append Vector components (Wind/Storm motion)
    if param in ['UGRD', 'VGRD', 'USTM', 'VSTM']:
        suffix = "UComponent" if param in ['UGRD', 'USTM'] else "VComponent"
        # Standardize 10m wind speed identifier
        if param in ['UGRD', 'VGRD'] and level_clean == "10Meter":
            return f"dcid:WindSpeed_{suffix}_Height10Meters"
        return f"{dcid}_{suffix}"

    if param == 'RH':
        return f"{dcid}_RelativeHumidity"
    if param == 'SPFH':
        return f"{dcid}_SpecificHumidity"
    if param == 'REFC':
        return f"dcid:{base}"

    return dcid


def update_state_json(latest_date, latest_cycle):
    """Uploads the newest processed checkpoint to GCS."""
    try:
        client = storage.Client(project=FLAGS.project_id)
        bucket = client.bucket(FLAGS.bucket_name)
        blob = bucket.blob(FLAGS.state_path)

        # 1. Get existing state to preserve BigQuery progress
        state = {}
        if blob.exists():
            state = json.loads(blob.download_as_text())

        # 2. Update ONLY the top-level date/cycle (for the processor/downloader)
        state["date"] = latest_date
        state["cycle"] = latest_cycle
        state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # 3. Upload the merged dictionary
        blob.upload_from_string(json.dumps(state, indent=2),
                                content_type='application/json')
        logging.info(
            f"Successfully updated GCS state to: {latest_date} {latest_cycle}z")
    except Exception as e:
        logging.error(f"Failed to update state.json: {e}")


# --- WORKER FUNCTION ---
def worker_process(args):
    """
    The core loop executed by each CPU core.
    Processes a slice of GRIB messages and writes to a temporary partition file.
    """
    input_path, start_msg, end_msg, chunk_id, lats_flat, lons_flat, f_hour, output_path = args
    temp_path = f"{output_path}.part{chunk_id}"

    f_hour_int = int(f_hour)
    suffix_method = "GFS0Hour" if f_hour_int == 0 else f"GFS{f_hour_int}HourForecast"

    # Pre-calculate coordinate strings once per worker for efficiency
    lats_str = [str(int(x)) if x % 1 == 0 else f"{x:g}" for x in lats_flat]
    lons_str = [str(int(x)) if x % 1 == 0 else f"{x:g}" for x in lons_flat]
    place_names = [f"latLong/{la}_{lo}" for la, lo in zip(lats_str, lons_str)]

    grbs = pygrib.open(input_path)

    with open(temp_path, 'w', encoding='utf-8', newline='') as f_out:
        writer = py_csv.writer(f_out,
                               quoting=py_csv.QUOTE_MINIMAL,
                               lineterminator='\r\n')

        for i in range(start_msg, end_msg + 1):
            try:
                grb = grbs.message(i)
                raw_values = np.flipud(grb.values)
                data_flat = raw_values.flatten()

                raw_short = grb.shortName.lower()
                if raw_short == "unknown":
                    d, c, num = grb.discipline, grb.parameterCategory, grb.parameterNumber
                    if d == 0 and c == 3 and num == 196:
                        var_name = "HPBL"
                    elif d == 10 and c == 2 and num == 6:
                        var_name = "ICEG"
                    else:
                        var_name = f"VAR_{d}_{c}_{num}"
                else:
                    var_name = NAME_MAP.get(raw_short, raw_short.upper())

                # --- FILTERING LOGIC ---
                try:
                    has_bitmap = grb.bitmapPresent
                except:
                    has_bitmap = False

                valid_mask = np.ones(data_flat.shape, dtype=bool)
                if has_bitmap and hasattr(data_flat, 'mask'):
                    valid_mask &= ~data_flat.mask

                raw_data = data_flat.data if hasattr(data_flat,
                                                     'mask') else data_flat
                if var_name not in ["SUNSD", "CLMR"]:
                    try:
                        m_val = grb.missingValue
                        if m_val is not None:
                            valid_mask &= (raw_data != m_val)
                    except:
                        pass

                if not np.any(valid_mask):
                    continue

                data_subset = raw_data[valid_mask]
                mask_idx = np.where(valid_mask)[0]

                # --- LEVEL LOGIC ---
                l_type = grb.typeOfLevel
                LEVEL_TYPE_MAP_REF = {
                    "surface":
                        "surface",
                    "meanSea":
                        "mean sea level",
                    "atmosphere":
                        "entire atmosphere",
                    "atmosphereSingleLayer":
                        "entire atmosphere",
                    "planetaryBoundaryLayer":
                        "planetary boundary layer",
                    "lowCloudLayer":
                        "low cloud layer",
                    "middleCloudLayer":
                        "middle cloud layer",
                    "highCloudLayer":
                        "high cloud layer",
                    "cloudCeiling":
                        "cloud ceiling",
                    "isothermZero":
                        "0C isotherm",
                    "highestTroposphericFreezing":
                        "highest tropospheric freezing level",
                    "tropopause":
                        "tropopause",
                    "maxWind":
                        "max wind",
                    "heightAboveSea":
                        "m above mean sea level"
                }

                if l_type in LEVEL_TYPE_MAP_REF:
                    l_str = f"{grb.level} m above mean sea level" if l_type == "heightAboveSea" else LEVEL_TYPE_MAP_REF[
                        l_type]
                elif l_type == "isobaricInhPa":
                    l_str = f"{grb.level:g} mb"
                elif l_type == "isobaricInPa":
                    l_str = f"{grb.level / 100:g} mb"
                elif l_type == "heightAboveGround":
                    l_str = f"{grb.level} m above ground"
                elif l_type == "hybrid":
                    l_str = f"{grb.level} hybrid level"
                elif l_type == "potentialVorticity":
                    try:
                        s_val = grb['scaledValueOfFirstFixedSurface']
                        if s_val & (1 << 31):
                            s_val = -(s_val & ~(1 << 31))
                        pv_val = s_val * (
                            10**-grb['scaleFactorOfFirstFixedSurface'])
                        l_str = f"PV={pv_val:g} (Km^2/kg/s) surface"
                    except:
                        l_str = f"PV={grb.level*1e-9:g} (Km^2/kg/s) surface"
                elif l_type == "sigma":
                    try:
                        s_val = grb['scaledValueOfFirstFixedSurface'] * (
                            10**-grb['scaleFactorOfFirstFixedSurface'])
                        l_str = f"{s_val:g} sigma level"
                    except:
                        l_str = f"{grb.level} sigma level"
                elif l_type == "sigmaLayer":
                    try:
                        t = grb['scaledValueOfFirstFixedSurface'] * (
                            10**-grb['scaleFactorOfFirstFixedSurface'])
                        b = grb['scaledValueOfSecondFixedSurface'] * (
                            10**-grb['scaleFactorOfSecondFixedSurface'])
                        l_str = f"{t:g}-{b:g} sigma layer"
                    except:
                        l_str = f"{grb.level} sigma layer"
                elif l_type == "depthBelowLandLayer":
                    try:
                        t = grb['scaledValueOfFirstFixedSurface'] * (
                            10**-grb['scaleFactorOfFirstFixedSurface'])
                        b = grb['scaledValueOfSecondFixedSurface'] * (
                            10**-grb['scaleFactorOfSecondFixedSurface'])
                        l_str = f"{t:g}-{b:g} m below ground"
                    except:
                        l_str = f"{grb.level} m below ground"
                elif l_type in [
                        "pressureFromGroundLayer", "heightAboveGroundLayer"
                ]:
                    unit_l = "mb above ground" if "pressure" in l_type else "m above ground"
                    try:
                        l_str = f"{grb.topLevel/100 if 'pressure' in l_type else grb.topLevel:g}-{grb.bottomLevel/100 if 'pressure' in l_type else grb.bottomLevel:g} {unit_l}"
                    except:
                        l_str = f"{grb.level} {unit_l}"
                else:
                    l_str = f"{grb.level} {l_type}"

                l_low = l_str.lower()
                if "mb" in l_low or "mean sea level" in l_low:
                    final_m = suffix_method
                else:
                    base_m = "GroundLevel" if "ground" in l_low else ""
                    final_m = f"{base_m}_{suffix_method}" if base_m else suffix_method

                dcid = construct_dcid(var_name, l_str)
                obs_date = grb.validDate.strftime("%Y-%m-%dT%H:%M:%S")
                unit = PARAM_MAP.get(var_name, ('', ''))[1]

                if var_name in ['LAND', 'ICEC']:
                    data_subset = data_subset * 0.0625

                data_rounded = np.round(data_subset, 2)

                for j, val in enumerate(data_rounded):
                    idx = mask_idx[j]
                    if val == 0:
                        val_out = "-0" if np.signbit(val) else "0"
                    elif val % 1 == 0:
                        val_out = str(int(val))
                    else:
                        val_out = f"{val:.2f}".rstrip('0').rstrip('.')

                    writer.writerow([
                        obs_date, val_out, dcid, final_m, lats_str[idx],
                        lons_str[idx], place_names[idx], unit
                    ])
            except Exception as e:
                logging.error(f"Worker {chunk_id} skipped msg {i}: {e}")

    grbs.close()
    return temp_path


def grib_statvar_processor(input_path, gcs_blob_name):
    """
    Converts the specified GRIB file into a Data Commons compatible CSV format.
    """
    start_time = time.perf_counter()
    logging.info(f"Parallel process started: {input_path}")

    # Temporary local directory for worker partitions
    temp_dir = Path("temp_parts")
    temp_dir.mkdir(exist_ok=True)
    local_temp_base = temp_dir / input_path.name

    try:
        grbs = pygrib.open(str(input_path))
        total_messages = grbs.messages
        sample = grbs.message(1)
        lats, lons = sample.latlons()
        lats_flat = np.flipud(lats).flatten().astype(np.float32)
        lons_raw = np.flipud(lons).flatten()
        lons_flat = np.where(lons_raw > 180, lons_raw - 360,
                             lons_raw).astype(np.float32)
        grbs.close()

        num_workers = min(FLAGS.num_workers, total_messages)
        chunk_size = total_messages // num_workers
        tasks = []
        for i in range(num_workers):
            start = (i * chunk_size) + 1
            end = total_messages if i == num_workers - 1 else (i +
                                                               1) * chunk_size
            tasks.append((str(input_path), start, end, i, lats_flat, lons_flat,
                          FLAGS.forecast_hour, str(local_temp_base)))

        with Pool(num_workers) as pool:
            temp_files = pool.map(worker_process, tasks)

        # Merge and Stream to GCS
        client = storage.Client(project=FLAGS.project_id)
        bucket = client.bucket(FLAGS.bucket_name)
        blob = bucket.blob(gcs_blob_name)

        logging.info(
            f"Uploading merged results to gs://{FLAGS.bucket_name}/{gcs_blob_name}..."
        )
        final_local_csv = f"{local_temp_base}.final"
        with open(final_local_csv, 'wb') as f_final:
            header = "observationDate,value,variableMeasured,measurementMethod,latitude,longitude,placeName,unit\r\n"
            f_final.write(header.encode('utf-8'))

            for temp_path in temp_files:
                if os.path.exists(temp_path):
                    with open(temp_path, 'rb') as f_part:
                        f_final.write(f_part.read())
                    os.remove(temp_path)

        blob.upload_from_filename(final_local_csv, content_type='text/csv')

        duration = time.perf_counter() - start_time
        logging.info(f"Completed {input_path.name} in {duration:.2f}s")
        return True

    except Exception as e:
        logging.error(f"Failed to process {input_path}: {e}")
        return False


def main(argv):
    """Entry point for the GRIB processing script."""
    input_dir = Path(FLAGS.input)
    files_to_process = sorted(list(input_dir.rglob('gfs.t*')))

    if not files_to_process:
        logging.warning(f"No files found in {FLAGS.input}")
        return

    logging.info(f"Found {len(files_to_process)} files to process.")

    for input_path in files_to_process:
        path_str = str(input_path)
        # Extract metadata for filename: noaa_gfs_output_DATE_CYCLE_FHOUR.csv
        date_match = re.search(r'(\d{8})', path_str)
        cycle_match = re.search(r't(\d{2})z', path_str)

        if date_match and cycle_match:
            date_str = date_match.group(1)
            cycle_str = cycle_match.group(1)
            f_hour = FLAGS.forecast_hour

            gcs_filename = f"noaa_gfs_output_{date_str}_{cycle_str}_{f_hour}.csv"
            gcs_full_path = f"{FLAGS.output_gcs_prefix.strip('/')}/{gcs_filename}"

            if grib_statvar_processor(input_path, gcs_full_path):
                logging.info(
                    f"Successfully processed {date_str} {cycle_str}z. Updating state..."
                )
                update_state_json(date_str, cycle_str)
            else:
                logging.error(
                    f"Failed to process {path_str}. Stopping to maintain integrity."
                )
                break
        else:
            logging.warning(
                f"Could not extract date/cycle from {path_str}; skipping.")


if __name__ == "__main__":
    app.run(main)
