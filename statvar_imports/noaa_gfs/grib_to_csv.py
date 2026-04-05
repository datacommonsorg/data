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
This script processes GRIB2 meteorological data by utilizing the pygrib library to 
decode binary records into NumPy arrays for vectorized grid transformations. 
It performs automated coordinate normalization (converting 0-360° to -180-180°), 
re-orienting data for standard GIS compatibility, and resolving complex 
vertical level definitions (including Potential Vorticity, Sigma, and Hybrid layers). 
The pipeline maps raw NCEP shortnames to standardized identifiers, applies 
variable-specific precision rounding, and leverages PyArrow for high-performance 
flattening and CSV streaming of the resulting observations.
"""

import pygrib
import numpy as np
import pyarrow as pa
import pyarrow.csv as csv
import sys
import time

def convert(input_file, output_file):
    """
    Converts GRIB weather data to a filtered, flattened CSV format.
    Uses PyArrow for high-performance I/O and NumPy for vectorised data manipulation.
    """
    start_total = time.time()
    
    try:
        grbs = pygrib.open(input_file)
    except Exception as e:
        print(f"Error: {e}")
        return

    # --- 1. STATIC GRID INITIALIZATION ---
    # We extract the lat/lon grid once from the first record to avoid redundant 
    # heavy calculations, assuming the grid is consistent across the GRIB file.
    sample = grbs.readline()
    lats, lons = sample.latlons()

    # GRIB data is often stored top-to-bottom; flipud ensures standard orientation.
    lats_flat = np.flipud(lats).flatten().astype(np.float32)
    lons_raw = np.flipud(lons).flatten()

    # Normalize longitudes from [0, 360] to [-180, 180] for standard GIS compatibility.
    lons_flat = np.where(lons_raw > 180, lons_raw - 360, lons_raw).astype(np.float32)
    grbs.rewind()
    
    # --- 2. TRANSLATION MAPS ---
    # Maps internal GRIB shortnames to standardized NOAA/NCEP abbreviations.
    name_map = {
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

    # Human-readable strings for vertical levels (e.g., 'surface', 'tropopause').
    level_type_map = {
        "surface": "surface", "meanSea": "mean sea level", "atmosphere": "entire atmosphere",
        "atmosphereSingleLayer": "entire atmosphere (considered as a single layer)",
        "planetaryBoundaryLayer": "planetary boundary layer", "lowCloudLayer": "low cloud layer",
        "middleCloudLayer": "middle cloud layer", "highCloudLayer": "high cloud layer",
        "cloudCeiling": "cloud ceiling", "isothermZero": "0C isotherm",
        "highestTroposphericFreezing": "highest tropospheric freezing level",
        "tropopause": "tropopause", "maxWind": "max wind", "heightAboveSea": "m above mean sea level"
    }

    # --- 3. DATA PROCESSING LOOP ---
    with open(output_file, 'wb') as f:
        # include_header=False is used because we append rows record-by-record.
        opts = csv.WriteOptions(include_header=False, quoting_style='needed')
        
        for grb in grbs:
            try:
                # Align data values with our flipped lat/lon grid.
                vals_flipped = np.flipud(grb.values)
                data_flat = vals_flipped.flatten()

                # --- Variable Name Resolution ---
                # Handles "Unknown" GRIB parameters by looking at Discipline/Category/Number.
                raw_short = grb.shortName.lower()
                if raw_short == "unknown":
                    d, c, num = grb.discipline, grb.parameterCategory, grb.parameterNumber
                    if d == 0 and c == 3 and num == 196: var_name = "HPBL"
                    elif d == 10 and c == 2 and num == 6: var_name = "ICEG"
                    else: var_name = f"VAR_{d}_{c}_{num}"
                else:
                    var_name = name_map.get(raw_short, raw_short.upper())

                # --- Filtering Logic (Missing Values / Bitmaps) ---
                # Identifies which grid points actually contain data.
                try:
                    has_bitmap = grb.bitmapPresent
                except:
                    has_bitmap = False

                valid_mask = np.ones(data_flat.shape, dtype=bool)

                # Apply mask if the GRIB record uses a bitmap (e.g., land-only data).
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
                if n == 0: continue
                
                # --- Vertical Level Logic ---
                # Complex logic to interpret different height/pressure/sigma types.
                l_type = grb.typeOfLevel
                
                if l_type == "potentialVorticity":
                    # Manually parsing GRIB2 sign bits for PV units (Km^2/kg/s).
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

                # (Standard level parsing: mb for pressure, m for height, etc.)
                elif l_type in level_type_map:
                    level_str = f"{grb.level} {level_type_map[l_type]}" if l_type == "heightAboveSea" else level_type_map[l_type]
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

                # --- Precision & Rounding ---
                # Variables like Pressure/Height are rounded to integers.
                # Wind components (UGRD/VGRD) keep high precision.
                if var_name in ["PRMSL", "PRES", "HGT", "MSLET"]:
                    processed_vals = (np.floor(np.abs(data_subset) + 0.499999999) * np.sign(data_subset)).astype(np.int32)
                elif var_name in ["UGRD", "VGRD", "ICEG", "HPBL", "VWSH"]:
                    # VWSH added to high precision to match wgrib2 evidence
                    processed_vals = np.round(data_subset, 9) if var_name == "VWSH" else np.round(data_subset, 5)
                else:
                    processed_vals = np.round(data_subset, 3)
                
                # --- CSV Export via Arrow ---
                # We wrap the data in PyArrow arrays for the fastest possible conversion to CSV.
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
                print(f"Error: {e}")

    grbs.close()
    print(f"Total Time taken for GRIB to CSV conversion: {time.time() - start_total:.2f}s")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <input_grib> <output_csv>")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
