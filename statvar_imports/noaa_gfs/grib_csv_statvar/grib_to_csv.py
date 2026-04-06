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
This script processes GRIB2 meteorological data by utilizing the pygrib library.
It performs automated coordinate normalization, re-orienting data for GIS 
compatibility, and leverages PyArrow for high-performance CSV streaming.
"""

import time
import pygrib
import numpy as np
import pyarrow as pa
import pyarrow.csv as csv
from absl import app, flags, logging

logging.set_verbosity(logging.INFO)

# --- FLAG DEFINITIONS ---
FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'Path to the input GRIB file.')
flags.DEFINE_string('output_file', None, 'Path to the output CSV file.')

# Set mandatory flags
flags.mark_flag_as_required('input_file')
flags.mark_flag_as_required('output_file')

# --- CONSTANTS & MAPS ---
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

LEVEL_TYPE_MAP = {
    "surface": "surface", "meanSea": "mean sea level", "atmosphere": "entire atmosphere",
    "atmosphereSingleLayer": "entire atmosphere (considered as a single layer)",
    "planetaryBoundaryLayer": "planetary boundary layer", "lowCloudLayer": "low cloud layer",
    "middleCloudLayer": "middle cloud layer", "highCloudLayer": "high cloud layer",
    "cloudCeiling": "cloud ceiling", "isothermZero": "0C isotherm",
    "highestTroposphericFreezing": "highest tropospheric freezing level",
    "tropopause": "tropopause", "maxWind": "max wind", "heightAboveSea": "m above mean sea level"
}

def convert_grib_to_csv(input_path, output_path):
    """Processes GRIB data and writes to CSV using Arrow."""
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

    grbs.rewind()
    
    # --- 2. DATA PROCESSING LOOP ---
    with open(output_path, 'wb') as f:
        # Standard CSV options
        opts = csv.WriteOptions(include_header=False, quoting_style='needed')
        
        for grb in grbs:
            try:
                vals_flipped = np.flipud(grb.values)
                data_flat = vals_flipped.flatten()

                # Variable Name Resolution
                raw_short = grb.shortName.lower()
                if raw_short == "unknown":
                    d, c, num = grb.discipline, grb.parameterCategory, grb.parameterNumber
                    if d == 0 and c == 3 and num == 196: var_name = "HPBL"
                    elif d == 10 and c == 2 and num == 6: var_name = "ICEG"
                    else: var_name = f"VAR_{d}_{c}_{num}"
                else:
                    var_name = NAME_MAP.get(raw_short, raw_short.upper())

                # Filtering Logic (Missing Values / Bitmaps) ---
                try:
                    has_bitmap = grb.bitmapPresent
                except:
                    has_bitmap = False

                valid_mask = np.ones(data_flat.shape, dtype=bool)
                if has_bitmap and hasattr(data_flat, 'mask'):
                    valid_mask &= ~data_flat.mask
                
                # Filter out points matching the GRIB 'missingValue' metadata.
                if var_name not in ["SUNSD", "CLMR"]:
                    try:
                        m_val = grb.missingValue
                        if m_val is not None:
                            raw_data = data_flat.data if hasattr(data_flat, 'mask') else data_flat
                            valid_mask &= (raw_data != m_val)
                    except:
                        pass
                
                # Extract only the valid data points to reduce CSV file size.
                data_subset = data_flat.data[valid_mask] if hasattr(data_flat, 'mask') else data_flat[valid_mask]
                lons_subset = lons_flat[valid_mask]
                lats_subset = lats_flat[valid_mask]

                n = len(data_subset)
                if n == 0: 
                    continue
                
                # Vertical Level Logic
                l_type = grb.typeOfLevel
                if l_type == "potentialVorticity":
                    try:
                        s_factor = grb['scaleFactorOfFirstFixedSurface']
                        s_value = grb['scaledValueOfFirstFixedSurface']
                        # GRIB2 sign bit check (if bit 1 of s_value is 1, it's negative)
                        if s_value & (1 << 31):
                            s_value = -(s_value & ~(1 << 31))
                        pv_val = s_value * (10**-s_factor)
                        level_str = f"PV={pv_val:g} (Km^2/kg/s) surface"
                    except:
                        level_str = f"PV={grb.level*1e-9:g} (Km^2/kg/s) surface"
                elif l_type in LEVEL_TYPE_MAP:
                    level_str = f"{grb.level} {LEVEL_TYPE_MAP[l_type]}" if l_type == "heightAboveSea" else LEVEL_TYPE_MAP[l_type]
                elif l_type == "isobaricInhPa": level_str = f"{grb.level:g} mb"
                elif l_type == "isobaricInPa": level_str = f"{grb.level/100:g} mb"
                elif l_type == "heightAboveGround": level_str = f"{grb.level} m above ground"
                elif l_type == "hybrid": level_str = f"{grb.level} hybrid level"
                elif l_type == "sigma":
                    try:
                        s_val = grb['scaledValueOfFirstFixedSurface'] * (10**-grb['scaleFactorOfFirstFixedSurface'])
                        level_str = f"{s_val:g} sigma level"
                    except:
                        level_str = f"{grb.level} sigma level"
                elif l_type == "sigmaLayer":
                    try:
                        t = grb['scaledValueOfFirstFixedSurface'] * (10**-grb['scaleFactorOfFirstFixedSurface'])
                        b = grb['scaledValueOfSecondFixedSurface'] * (10**-grb['scaleFactorOfSecondFixedSurface'])
                        level_str = f"{t:g}-{b:g} sigma layer"
                    except:
                        level_str = f"{grb.level} sigma layer"
                elif l_type == "depthBelowLandLayer":
                    try:
                        t = grb['scaledValueOfFirstFixedSurface'] * (10**-grb['scaleFactorOfFirstFixedSurface'])
                        b = grb['scaledValueOfSecondFixedSurface'] * (10**-grb['scaleFactorOfSecondFixedSurface'])
                        level_str = f"{t:g}-{b:g} m below ground"
                    except:
                        level_str = f"{grb.topLevel/100:g}-{grb.bottomLevel/100:g} m below ground"
                elif l_type in ["pressureFromGroundLayer", "heightAboveGroundLayer"]:
                    unit = "mb above ground" if "pressure" in l_type else "m above ground"
                    level_str = f"{grb.topLevel/100 if 'pressure' in l_type else grb.topLevel:g}-{grb.bottomLevel/100 if 'pressure' in l_type else grb.bottomLevel:g} {unit}"
                else:
                    level_str = f"{grb.level} {l_type}"

                processed_vals = np.round(data_subset, 2)
                
                # CSV Export via Arrow
                table = pa.Table.from_arrays([
                    pa.array([grb.analDate.strftime("%Y-%m-%d %H:%M:%S")] * n),
                    pa.array([grb.validDate.strftime("%Y-%m-%d %H:%M:%S")] * n),
                    pa.array([var_name] * n),
                    pa.array([level_str] * n),
                    pa.array(lons_subset),
                    pa.array(lats_subset),
                    pa.array(processed_vals)
                ], names=['1','2','3','4','5','6','7'])

                csv.write_csv(table, f, write_options=opts)

            except Exception as e:
                logging.error(f"Error: {e}")

    grbs.close()

def main(argv):
    """Main execution entry point."""
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')

    start_time = time.perf_counter()
    logging.info(f"Conversion started for: {FLAGS.input_file}")

    try:
        convert_grib_to_csv(FLAGS.input_file, FLAGS.output_file)
        logging.info(f"Conversion complete. Output saved to: {FLAGS.output_file}")
    except Exception as e:
        logging.fatal(f"Process failed: {e}")
    
    duration = time.perf_counter() - start_time
    logging.info(f"Total Execution Time: {duration:.2f}s")

if __name__ == "__main__":
    app.run(main)
