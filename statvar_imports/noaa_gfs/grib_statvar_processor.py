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
Processes GRIB2 weather data for Data Commons ingestion.
This script automates the end-to-end pipeline by utilizing the pygrib library: 
opening GRIB2 files, normalizing coordinates for GIS compatibility, mapping 
raw parameters to standardized DCIDs, handling complex vertical level logic, 
and generating high-precision, quote-free CSV outputs using PyArrow for 
optimal streaming performance.
"""

import time
import pygrib
import numpy as np
import pyarrow as pa
import pyarrow.csv as csv
import csv as py_csv
import re
from absl import app, flags, logging

logging.set_verbosity(logging.INFO)

# --- FLAG DEFINITIONS ---
FLAGS = flags.FLAGS
flags.DEFINE_string('input_file', None, 'Path to the input GRIB file.')
flags.DEFINE_string('output_file', None, 'Path to the output CSV file.')
flags.DEFINE_string('forecast_hour', '000', 'The forecast hour (e.g., 000, 003).')

# Set mandatory flags
flags.mark_flag_as_required('input_file')
flags.mark_flag_as_required('output_file')

# --- PARAMETER & LEVEL MAPPING ---
# Maps raw GRIB shortnames to standardized internal codes
NAME_MAP = {
    "prmsl": "PRMSL", "clwmr": "CLMR", "icmr": "ICMR", "rwmr": "RWMR",
    "snmr": "SNMR", "grle": "GRLE", "refd": "REFD", "refc": "REFC",
    "vis": "VIS", "u": "UGRD", "v": "VGRD", "vrate": "VRATE",
    "gust": "GUST", "gh": "HGT", "t": "TMP", "r": "RH",
    "q": "SPFH", "w": "VVEL", "wz": "DZDT", "absv": "ABSV",
    "o3mr": "O3MR", "tcc": "TCDC", "hindex": "HINDEX", "mslet": "MSLET",
    "sp": "PRES", "orog": "HGT", "st": "TSOIL", "soilw": "SOILW",
    "soill": "SOILL", "cnwat": "CNWAT", "sdwe": "WEASD", "sde": "SNOD",
    "sithick": "ICETK", "2t": "TMP", "2sh": "SPFH", "2d": "DPT",
    "2r": "RH", "aptmp": "APTMP", "10u": "UGRD", "10v": "VGRD",
    "cpofp": "CPOFP", "prate": "PRATE", "csnow": "CSNOW", "cicep": "CICEP",
    "cfrzr": "CFRZR", "crain": "CRAIN", "fsr": "SFCR", "fricv": "FRICV",
    "veg": "VEG", "slt": "SOTYP", "wilt": "WILT", "fldcp": "FLDCP",
    "sunsd": "SUNSD", "lftx": "LFTX", "cape": "CAPE", "cin": "CIN",
    "pwat": "PWAT", "cwat": "CWAT", "tozne": "TOZNE", "lcc": "LCDC",
    "mcc": "MCDC", "hcc": "HCDC", "hlcy": "HLCY", "ustm": "USTM",
    "vstm": "VSTM", "trpp": "PRES", "icaht": "ICAHT", "vwsh": "VWSH",
    "pres": "PRES", "100u": "UGRD", "100v": "VGRD", "4lftx": "4LFTX",
    "pt": "POT", "plpl": "PLPL", "lsm": "LAND", "ci": "ICEC", "sit": "ICETMP"
}

# Maps internal codes to Data Commons StatVar base names and Units
PARAM_MAP = {
    'PRMSL': ('Pressure_Place', 'Pascal'), 'MSLET': ('MSLPEtaReduction_Pressure_Atmosphere', 'Pascal'),
    'TMP': ('Temperature_Place', 'Kelvin'), 'DPT': ('DewPointTemperature_Atmosphere', 'Kelvin'),
    'APTMP': ('Apparent_Temperature_Place', 'Kelvin'), 'HGT': ('GeopotentialHeight_Place', 'GeopotentialMeters'),
    'RH': ('Humidity_Place', 'Percent'), 'SPFH': ('Humidity_Place', ''),
    'UGRD': ('WindSpeed_Place', 'MeterPerSecond'), 'VGRD': ('WindSpeed_Place', 'MeterPerSecond'),
    'VIS': ('Visibility_Place', 'Meter'), 'GUST': ('Max_WindSpeed_Place', 'MeterPerSecond'),
    'PRES': ('Pressure_Atmosphere', 'Pascal'), 'CLMR': ('MixingRatio_Cloud', ''),
    'ICMR': ('MixingRatio_Ice', ''), 'RWMR': ('MixingRatio_Rainwater', ''),
    'SNMR': ('MixingRatio_Snow', ''), 'GRLE': ('Count_Graupel', ''),
    'REFD': ('Reflectivity_Place', 'Decibel'), 'REFC': ('Max_CompositeReflectivity_Place', 'Decibel'),
    'VVEL': ('PressureVerticalVelocity_Velocity_Place', 'PascalPerSecond'),
    'DZDT': ('GeometricVerticalVelocity_Velocity_Place', 'MeterPerSecond'),
    'ABSV': ('AbsoluteVorticity_Place', 'InverseSecond'), 'O3MR': ('Ozone_MixingRatio_Atmosphere', ''),
    'VRATE': ('VentilationRate_Place', 'SquareMeterPerSecond'), 'TSOIL': ('Temperature_Soil', 'Kelvin'),
    'SOILW': ('VolumetricSoilMoisture_Soil', ''), 'SOILL': ('LiquidWaterContent_Soil', ''),
    'TCDC': ('CloudCover_Place', 'Percent'), 'HINDEX': ('HainesIndex_Place', ''),
    'CNWAT': ('CloudWaterContent_Atmosphere', 'KilogramPerMeterSquared'),
    'WEASD': ('SnowWaterEquivalent_Place', 'KilogramPerMeterSquared'), 'SNOD': ('Depth_Snow', 'Meter'),
    'ICETK': ('Thickness_Ice', 'Meter'), 'ICEG': ('GrowthRate_Count_Ice', 'MeterPerSecond'),
    'CPOFP': ('FrozenPrecipitation_Place', 'Percent'), 'PRATE': ('PrecipitationRate_Place', ''),
    'CSNOW': ('Occurrence_Place_SurfaceLevel_Snow', ''), 'CICEP': ('Occurrence_Place_SurfaceLevel_IcePellets', ''),
    'CFRZR': ('Occurrence_Place_SurfaceLevel_FreezingRain', ''), 'CRAIN': ('Occurrence_Place_SurfaceLevel_Rain', ''),
    'VEG': ('Area_Place_SurfaceLevel_Vegetation', 'Percent'), 'SFCR': ('SurfaceRoughness_Place', 'Meter'),
    'FRICV': ('FrictionalVelocity_Place', 'MeterPerSecond'), 'SOTYP': ('SoilType_Soil', ''),
    'WILT': ('WiltingPoint_Soil', ''), 'FLDCP': ('FieldCapacity_Soil', ''),
    'SUNSD': ('SunshineDuration_Place', 'Second'), 'LFTX': ('SurfaceLiftedIndex_Atmosphere', 'Kelvin'),
    '4LFTX': ('BestLiftedIndex_Atmosphere', 'Kelvin'), 'CAPE': ('ConvectiveAvailablePotentialEnergy_Atmosphere', 'JoulePerKilogram'),
    'CIN': ('ConvectiveInhibition_Atmosphere', 'JoulePerKilogram'), 'PWAT': ('PrecipitableWater_Place', 'KilogramPerMeterSquared'),
    'CWAT': ('CloudWater_Place', 'KilogramPerMeterSquared'), 'TOZNE': ('Concentration_Atmosphere_Ozone', ''),
    'LCDC': ('CloudCover_Place_LowCloudLayer', 'Percent'), 'MCDC': ('CloudCover_Place_MiddleCloudLayer', 'Percent'),
    'HCDC': ('CloudCover_Place_HighCloudLayer', 'Percent'), 'HLCY': ('StormRelativeHelicity_Atmosphere', 'MetersSquaredPerSecondSquared'),
    'USTM': ('StormMotion_Atmosphere', 'MeterPerSecond'), 'VSTM': ('StormMotion_Atmosphere', 'MeterPerSecond'),
    'ICAHT': ('ICAOStandardAtmosphere_Altitude_Atmosphere', 'Meter'), 'VWSH': ('WindShear_Atmosphere', 'InverseSecond'),
    'POT': ('PotentialTemperature_Atmosphere', 'Kelvin'), 'HPBL': ('PlanetaryBoundaryLayer_Altitude_Atmosphere', 'Meter'),
    'PLPL': ('LiftedParcelLevel_Pressure_Atmosphere', 'Pascal'), 'LAND': ('Area_LandCover', 'SquareDegree'),
    'ICEC': ('Area_IceCover', 'SquareDegree'), 'ICETMP': ('Temperature_SeaIce', 'Kelvin'),
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
    Standardizes raw GFS level strings into DCID standards.
    
    Args:
        level (str): The raw vertical level description (e.g., '2 m above ground').
        
    Returns:
        str: A cleaned, standardized string suitable for a Data Commons identifier.
    """
    l = str(level).lower().strip()

    # 1. Check for exact matches using the map
    if l in STATIC_LEVEL_MAP: return STATIC_LEVEL_MAP[l]

    # 2. Dynamic string parsing for non-static levels
    if "m above mean sea level" in l:
        val = l.split(" ")[0].replace("-", "To")
        return f"{val}MetersAboveMeanSeaLevel"
    
    if "entire atmosphere" in l: return ""

    if "low cloud layer" in l: return "LowCloudLayer"
    if "middle cloud layer" in l: return "MiddleCloudLayer"
    if "high cloud layer" in l: return "HighCloudLayer"
    
    if "hybrid level" in l:
        val = l.split(" ")[0]
        return "LowestHybridLevel" if val == "1" else f"{val}HybridLevel"
    
    if "m below ground" in l:
        match = re.search(r'([0-9.]+)-?([0-9.]*)', l)
        if match:
            start, end = match.group(1), match.group(2)
            return f"{start}To{end}Meter" if end else f"{start}Meter"
    
    if "m above ground" in l:
        val = l.split(" ")[0].replace("-", "To")
        return f"{val}Meter"
    
    if "mb" in l:
        val = l.split(" ")[0].replace("-", "To")
        return f"{val}Millibar"
    
    if "sigma" in l:
        val = l.split(" ")[0].replace("-", "To")
        suffix = "SigmaLayer" if "layer" in l else "SigmaLevel"
        return f"{val}{suffix}"
    
    if "pv=" in l:
        return "PotentialVorticityNeg2PVU" if ("neg" in l or "-2" in l) else "PotentialVorticity2PVU"
    
    return "".join(word.capitalize() for word in l.replace("-", " ").split() if word)

def construct_dcid(param_raw, level_raw):
    """
    Constructs a full Data Commons Identifier (DCID) based on parameters and levels.
    
    Args:
        param_raw (str): The meteorological parameter code (e.g., 'TMP').
        level_raw (str): The raw vertical level description.
        
    Returns:
        str: The complete DCID string formatted with 'dcid:' prefix.
    """
    param = str(param_raw).upper()
    level_clean = format_level_dcid(level_raw)
    mapping = PARAM_MAP.get(param)
    base = mapping[0] if mapping else param

    if param == 'RH' and not level_clean: 
        return "dcid:Humidity_RelativeHumidity"
    
    if level_clean and level_clean in base: 
        dcid = f"dcid:{base}"
    elif not level_clean: 
        dcid = f"dcid:{base}"
    else: 
        dcid = f"dcid:{base}_{level_clean}"
    
    # Handle component-specific wind and motion vectors
    if param in ['UGRD', 'VGRD', 'USTM', 'VSTM']:
        suffix = "UComponent" if param in ['UGRD', 'USTM'] else "VComponent"
        if param in ['UGRD', 'VGRD'] and level_clean == "10Meter": 
            return f"dcid:WindSpeed_{suffix}_Height10Meters"
        return f"{dcid}_{suffix}"
    
    if param == 'RH': return f"{dcid}_RelativeHumidity"
    if param == 'SPFH': return f"{dcid}_SpecificHumidity"
    if param == 'REFC': return f"dcid:{base}"

    return dcid

# --- MAIN PROCESSING LOGIC ---
def process_grib_dcid(input_path, output_path):
    """
    Processes GRIB data and writes directly to standardized CSV using Arrow.
    Includes coordinate normalization, parameter mapping, and DCID resolution.
    """
    try:
        grbs = pygrib.open(input_path)
    except Exception as e:
        logging.error(f"Failed to open GRIB file: {e}")
        return

    # --- 1. STATIC GRID INITIALIZATION ---
    sample = grbs.readline()
    lats, lons = sample.latlons()

    # Flip and flatten coordinates
    lats_flat = np.flipud(lats).flatten().astype(np.float32)
    lons_raw = np.flipud(lons).flatten()
    lons_flat = np.where(lons_raw > 180, lons_raw - 360, lons_raw).astype(np.float32)
    
    # Match precision of the second script (simple string conversion)
    lats_str = [str(int(x)) if x % 1 == 0 else f"{x:g}" for x in lats_flat]
    lons_str = [str(int(x)) if x % 1 == 0 else f"{x:g}" for x in lons_flat]
    place_names = [f"latLong/{la}_{lo}" for la, lo in zip(lats_str, lons_str)]
    
    grbs.rewind()

    f_hour_int = int(FLAGS.forecast_hour)
    suffix_method = "GFS0Hour" if f_hour_int == 0 else f"GFS{f_hour_int}HourForecast"

    # --- 2. DATA PROCESSING LOOP ---
    with open(output_path, 'w', encoding='utf-8', newline='') as f_out:
        writer = py_csv.writer(f_out, quoting=py_csv.QUOTE_MINIMAL)
        writer.writerow(['observationDate', 'value', 'variableMeasured', 'measurementMethod', 'latitude', 'longitude', 'placeName', 'unit'])

        for grb in grbs:
            try:
                data_flat = np.flipud(grb.values).flatten()
                raw_short = grb.shortName.lower()
                
                # Parameter mapping
                if raw_short == "unknown":
                    d, c, num = grb.discipline, grb.parameterCategory, grb.parameterNumber
                    if d == 0 and c == 3 and num == 196: var_name = "HPBL"
                    elif d == 10 and c == 2 and num == 6: var_name = "ICEG"
                    else: var_name = f"VAR_{d}_{c}_{num}"
                else:
                    var_name = NAME_MAP.get(raw_short, raw_short.upper())

                valid_mask = np.ones(data_flat.shape, dtype=bool)
                if hasattr(data_flat, 'mask'): valid_mask &= ~data_flat.mask
                
                if not np.any(valid_mask): continue
                
                data_subset = data_flat[valid_mask]
                mask_idx = np.where(valid_mask)[0]
                
                # Resolve Level and Method
                l_type = grb.typeOfLevel
                if l_type == "meanSea": l_str = "mean sea level"
                elif l_type == "surface": l_str = "surface"
                elif l_type == "isobaricInhPa": l_str = f"{grb.level:g} mb"
                elif l_type == "isobaricInPa": l_str = f"{grb.level / 100:g} mb"
                elif l_type == "heightAboveGround": l_str = f"{grb.level} m above ground"
                elif l_type == "depthBelowLandLayer": 
                    try:
                        top = grb['scaledValueOfFirstFixedSurface'] * (10**-grb['scaleFactorOfFirstFixedSurface'])
                        bottom = grb['scaledValueOfSecondFixedSurface'] * (10**-grb['scaleFactorOfSecondFixedSurface'])
                        l_str = f"{top:g}-{bottom:g} m below ground"
                    except:
                        l_str = f"{grb.level} m below ground"
                elif l_type == "hybrid": l_str = "1 hybrid level" if grb.level == 1 else f"{grb.level} hybrid level"
                elif l_type == "planetaryBoundaryLayer": l_str = "planetary boundary layer"
                else: l_str = f"{grb.level} {l_type}"

                l_low = l_str.lower()
                if "mb" in l_low or "mean sea level" in l_low:
                    final_m = suffix_method
                else:
                    base_m = "GroundLevel" if "ground" in l_low else ""
                    final_m = f"{base_m}_{suffix_method}" if base_m else suffix_method

                dcid = construct_dcid(var_name, l_str)
                obs_date = grb.validDate.strftime("%Y-%m-%dT%H:%M:%S")
                unit = PARAM_MAP.get(var_name, ('', ''))[1]

                data_rounded = np.round(data_subset, 2)

                # --- WRITING ROWS ---
                for i, val in enumerate(data_rounded):
                    idx = mask_idx[i]
                    if val == 0:
                        val_out = "-0" if np.signbit(val) else "0"
                    elif val % 1 == 0:
                        val_out = str(int(val))
                    else:
                        val_out = f"{val:.2f}".rstrip('0').rstrip('.')
                    writer.writerow([
                        obs_date,
                        val_out,
                        dcid,
                        final_m,
                        lats_str[idx],
                        lons_str[idx],
                        place_names[idx],
                        unit
                    ])

            except Exception as e:
                logging.error(f"Skip message: {e}")

    grbs.close()

def main(argv):
    """Main execution entry point."""
    if len(argv) > 1: raise app.UsageError('Too many arguments.')

    start_time = time.perf_counter()
    logging.info(f"Process started: {FLAGS.input_file}")

    try:
        process_grib_dcid(FLAGS.input_file, FLAGS.output_file)
        logging.info(f"Conversion complete. Output saved to: {FLAGS.output_file}")
    except Exception as e:
        logging.fatal(f"Process failed: {e}")
    
    duration = time.perf_counter() - start_time
    logging.info(f"Total processing time: {duration:.2f} seconds")

if __name__ == "__main__":
    app.run(main)
