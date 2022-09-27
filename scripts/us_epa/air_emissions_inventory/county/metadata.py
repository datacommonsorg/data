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
SOURCE_POLLUTANT = {
    'Carbon Monoxide': 'CarbonMonoxide',
    'Nitrogen Oxides': 'OxidesOfNitrogen',
    'PM10 Primary (Filt + Cond)': 'PM10',
    'PM2.5 Primary (Filt + Cond)': 'PM2.5',
    'Sulfur Dioxide': 'SulfurDioxide',
    'Volatile Organic Compounds': 'VolatileOrganicCompound',
    'Ammonia': 'Ammonia'
}

SOURCE_CATEGORY = {
    'Fuel Comb. Elec. Util.': 'FuelCombustionElectricUtility',
    'Fuel Comb. Industrial': 'FuelCombustionIndustrial',
    'Fuel Comb. Other': 'EPA_FuelCombustionOther',
    'Chemical & Allied Product Mfg': 'ChemicalAndAlliedProductManufacturing',
    'Metals Processing': 'MetalsProcessing',
    'Petroleum & Related Industries': 'PetroleumAndRelatedIndustries',
    'Other Industrial Processes': 'EPA_OtherIndustrialProcesses',
    'Solvent Utilization': 'SolventUtilization',
    'Storage & Transport': 'StorageAndTransport',
    'Waste Disposal & Recycling': 'WasteDisposalAndRecycling',
    'Highway Vehicles': 'OnRoadVehicles',
    'Off-Highway': 'NonRoadEnginesAndVehicles',
    'Miscellaneous': 'EPA_MiscellaneousEmissionSource',
    'Natural Resources': 'NaturalResources'
}
