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
This script processes GFS (Global Forecast System) weather data. 
It maps raw meteorological parameters and atmospheric levels to standardized 
Data Commons Identifiers (DCIDs), cleans and flattens the observations, and 
streams the resulting dataset directly to the unresolved_mcf bucket.
"""

import csv
import io
import re
import time
from absl import app, flags, logging
from google.cloud import storage

logging.set_verbosity(logging.INFO)

# --- FLAG DEFINITIONS ---
FLAGS = flags.FLAGS

flags.DEFINE_string('bucket_name', 'unresolved_mcf', 'GCS unresolved_mcf bucket.')
flags.DEFINE_string('input_local', './test_data/noaa_gfs_2025_12_24_0.csv', 'Path to the local input CSV file.')
flags.DEFINE_string('output_blob_name', 'noaa_gfs/auto/noaa_gfs_output.csv', 'Destination path in unresolved_mcf bucket.')
flags.DEFINE_string('forecast_hour', '000', 'The forecast hour (e.g., 000, 003).')

# 1. Parameter Mapping (Original)
param_map = {
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
    'CAPE': ('ConvectiveAvailablePotentialEnergy_Atmosphere', 'JoulePerKilogram'),
    'CIN': ('ConvectiveInhibition_Atmosphere', 'JoulePerKilogram'),
    'PWAT': ('PrecipitableWater_Place', 'KilogramPerMeterSquared'),
    'CWAT': ('CloudWater_Place', 'KilogramPerMeterSquared'),
    'TOZNE': ('Concentration_Atmosphere_Ozone', ''),
    'LCDC': ('CloudCover_Place_LowCloudLayer', 'Percent'),
    'MCDC': ('CloudCover_Place_MiddleCloudLayer', 'Percent'),
    'HCDC': ('CloudCover_Place_HighCloudLayer', 'Percent'),
    'HLCY': ('StormRelativeHelicity_Atmosphere', 'MetersSquaredPerSecondSquared'),
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

# 2. Helper Function to Clean Level for DCID
def format_level_dcid(level):
    """
    Standardizes raw GFS level strings into DCID standards.
    
    Args:
        level (str): The raw vertical level description (e.g., '2 m above ground').
        
    Returns:
        str: A cleaned, standardized string suitable for a Data Commons identifier.
    """
    l = str(level).lower().strip()
    
    if l == "mean sea level": 
        return "0MetersAboveMeanSeaLevel"
    if "m above mean sea level" in l:
        val = l.split(" ")[0].replace("-", "To")
        return f"{val}MetersAboveMeanSeaLevel"

    if l == "surface": return "SurfaceLevel"
    if "entire atmosphere" in l: return ""
    if l == "planetary boundary layer": return "PlanetaryBoundaryLayer"
    if "low cloud layer" in l: return "LowCloudLayer"
    if "middle cloud layer" in l: return "MiddleCloudLayer"
    if "high cloud layer" in l: return "HighCloudLayer"
    if l == "0c isotherm": return "Isotherm0C"
    if l == "highest tropospheric freezing level": return "HighestTroposphericFreezingLevel"
    
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
        # Extracts values from "30-0 mb" -> "30To0Millibar"
        # Prevents "GroundLevel" from being attached to Millibar layers later
        val = l.split(" ")[0].replace("-", "To")
        return f"{val}Millibar"

    if "sigma" in l:
        val = l.split(" ")[0].replace("-", "To")
        suffix = "SigmaLayer" if "layer" in l else "SigmaLevel"
        return f"{val}{suffix}"

    if "pv=" in l:
        return "PotentialVorticityNeg2PVU" if ("neg" in l or "-2" in l) else "PotentialVorticity2PVU"

    return "".join(word.capitalize() for word in l.replace("-", " ").split() if word)

# 3. DCID Constructor Logic
def construct_dcid(param_raw, level_raw):
    """
    Constructs a full Data Commons Identifier (DCID) based on GFS parameters and levels.
    
    Args:
        param_raw (str): The raw meteorological parameter code (e.g., 'TMP').
        level_raw (str): The raw vertical level description.
        
    Returns:
        str: The complete DCID string formatted with 'dcid:' prefix.
    """
    param = str(param_raw).upper()
    level_clean = format_level_dcid(level_raw)
    
    mapping = param_map.get(param)
    base = mapping[0] if mapping else param

    if param == 'RH' and not level_clean:
        return "dcid:Humidity_RelativeHumidity"
    
    if level_clean and level_clean in base:
        dcid = f"dcid:{base}"
    elif not level_clean:
        dcid = f"dcid:{base}"
    else:
        dcid = f"dcid:{base}_{level_clean}"

    if param in ['UGRD', 'VGRD', 'USTM', 'VSTM']:
        suffix = "UComponent" if param in ['UGRD', 'USTM'] else "VComponent"
        if param in ['UGRD', 'VGRD'] and level_clean == "10Meter":
            return f"dcid:WindSpeed_{suffix}_Height10Meters"
        return f"{dcid}_{suffix}"
    
    if param == 'RH': return f"{dcid}_RelativeHumidity"
    if param == 'SPFH': return f"{dcid}_SpecificHumidity"
    if param == 'REFC': return f"dcid:{base}"
    
    return dcid

def process_and_upload_true_stream():
    """
    Reads weather data and streams the transformed rows to GCS.
    
    The function flattens the data, determines measurement methods, resolves DCIDs,
    and writes to Cloud Storage using an internal buffer to manage write frequency.
    """
    client = storage.Client()
    bucket = client.bucket(FLAGS.bucket_name)
    blob = bucket.blob(FLAGS.output_blob_name)
    blob.chunk_size = 64 * 1024 * 1024

    # Define the standard wgrib2 CSV columns
    WGRIB2_COLUMNS = [
        'Reference_Time', 'Valid_Time', 'Parameter', 'Level', 
        'Longitude', 'Latitude', 'Value'
    ]

    with open(FLAGS.input_local, mode='r') as f_in:
        reader = csv.DictReader(f_in, fieldnames=WGRIB2_COLUMNS)
        output_buffer = io.StringIO()
        writer = csv.writer(output_buffer)
        writer.writerow(['observationDate', 'value', 'variableMeasured', 'measurementMethod', 'latitude', 'longitude', 'placeName', 'unit'])

        with blob.open("w", content_type='text/csv') as cloud_file:
            cloud_file.write(output_buffer.getvalue())
            output_buffer.seek(0); output_buffer.truncate(0)

            for i, row in enumerate(reader):
                param = row['Parameter']
                level = row['Level']
                obs_date = row['Valid_Time'].replace(' ', 'T')
                dcid = construct_dcid(param, level)

                # Apply multiplier for specific parameters
                try:
                    value = float(row['Value'])
                    if param in ['LAND', 'ICEC']:
                        value = value * 0.0625
                except (ValueError, TypeError):
                    value = row['Value']
                
                l_low = level.lower()
                
                # Logic to determine measurementMethod
                # If it is Millibar or Mean Sea Level, it must be empty
                if "mb" in l_low or "mean sea level" in l_low:
                    method = ""
                else:
                    method = "GroundLevel" if "ground" in l_low else ""
                
                # Suffixing logic based on Forecast Hour
                f_hour_int = int(FLAGS.forecast_hour)
                if f_hour_int == 0:
                    suffix = "GFS0Hour"
                else:
                    suffix = f"GFS{f_hour_int}HourForecast"
                
                if method:
                    method = f"{method}_{suffix}"
                else:
                    method = suffix

                writer.writerow([
                    obs_date,
                    row['Value'],
                    dcid,
                    method,
                    row['Latitude'],
                    row['Longitude'],
                    f"latLong/{row['Latitude']}_{row['Longitude']}",
                    param_map.get(param.upper(), ('', ''))[1]
                ])
                
                if i % 1000 == 0:
                    cloud_file.write(output_buffer.getvalue())
                    output_buffer.seek(0); output_buffer.truncate(0)
            
            cloud_file.write(output_buffer.getvalue())

def main(argv):
    """
    Main entry point for the script. Parses flags, tracks execution time, and triggers processing.
    """
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')

    start_time = time.perf_counter()
    logging.info(f"Process started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        process_and_upload_true_stream()
        logging.info("Upload complete.")
    except Exception as e:
        logging.fatal(f"Error: {e}")
    
    duration = time.perf_counter() - start_time
    mins, secs = divmod(duration, 60)
    logging.info(f"Total Execution Time: {int(mins)}m {secs:.2f}s")

if __name__ == "__main__":
    app.run(main)
