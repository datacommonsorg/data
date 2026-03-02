import csv
import io
import re
import time
from google.cloud import storage

# --- CONFIGURATION ---
BUCKET_NAME = "unresolved_mcf"
INPUT_LOCAL = "../noa_gfs/input_files/gfs.t00z.pgrb2.0p25.f000.csv"
OUTPUT_BLOB_NAME = "noaa_gfs/noaa_gfs_output.csv"

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
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(OUTPUT_BLOB_NAME)
    blob.chunk_size = 64 * 1024 * 1024

    with open(INPUT_LOCAL, mode='r') as f_in:
        reader = csv.DictReader(f_in)
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
                
                l_low = level.lower()
                
                # Logic to determine measurementMethod
                # If it is Millibar or Mean Sea Level, it must be empty
                if "mb" in l_low or "mean sea level" in l_low:
                    method = ""
                else:
                    method = "GroundLevel" if "ground" in l_low else ""
                
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

if __name__ == "__main__":
    start_time = time.perf_counter()
    print(f"Process started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        process_and_upload_true_stream()
        print("Upload complete.")
    except Exception as e:
        print(f"Error: {e}")
    duration = time.perf_counter() - start_time
    mins, secs = divmod(duration, 60)
    print(f"Total Execution Time: {int(mins)}m {secs:.2f}s")