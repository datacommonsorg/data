# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

POLLUTANT = {
    'CO': 'CarbonMonoxide',
    'NOX': 'OxidesOfNitrogen',
    'PM10Primary': 'PM10',
    'PM25Primary': 'PM2.5',
    'PM10-PRI': 'PM10',
    'PM25-PRI': 'PM2.5',
    'SO2': 'SulfurDioxide',
    'VOC': 'VolatileOrganicCompound',
    'NH3': 'Ammonia',
    'BLACK CARBON': 'BlackCarbon',
    'ORGANIC CARBON': 'OrganicCarbon'
}

SOURCE = {
    'FUEL COMB. ELEC. UTIL.': 'FuelCombustionElectricUtility',
    'FUEL COMB. INDUSTRIAL': 'FuelCombustionIndustrial',
    'FUEL COMB. OTHER': 'EPA_FuelCombustionOther',
    'CHEMICAL & ALLIED PRODUCT MFG': 'ChemicalAndAlliedProductManufacturing',
    'METALS PROCESSING': 'MetalsProcessing',
    'PETROLEUM & RELATED INDUSTRIES': 'PetroleumAndRelatedIndustries',
    'OTHER INDUSTRIAL PROCESSES': 'EPA_OtherIndustrialProcesses',
    'SOLVENT UTILIZATION': 'SolventUtilization',
    'STORAGE & TRANSPORT': 'StorageAndTransport',
    'WASTE DISPOSAL & RECYCLING': 'WasteDisposalAndRecycling',
    'HIGHWAY VEHICLES': 'OnRoadVehicles',
    'OFF-HIGHWAY': 'NonRoadEnginesAndVehicles',
    'MISCELLANEOUS': 'EPA_MiscellaneousEmissionSource',
    'Wildfires': 'Wildfire',
    'WILDFIRES': 'Wildfire',
    'PRESCRIBED FIRES': 'PrescribedFire',
    'Stationary fuel combustion': 'StationaryFuelCombustion',
    'Industrial and other processes': 'IndustrialAndOtherProcesses',
    'Transportation': 'Transportation'
}

SHEETS_NATIONAL = [
    'CO', 'NOX', 'PM10Primary', 'PM25Primary', 'SO2', 'VOC', 'NH3'
]

SKIPHEAD_AMMONIA_NATIONAL = 6
SKIPHEAD_OTHERS_NATIONAL = 5
# SKIPFOOT_PM_NATIONAL = 0
# SKIPFOOT_OTHERS_NATIONAL = 5

SHEET_STATE = 'State Trends'
