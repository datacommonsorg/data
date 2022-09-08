sourcegroups = {
    'FuelCombustionElectricUtility': 'StationaryFuelCombustion',
    'FuelCombustionIndustrial': 'StationaryFuelCombustion',
    'EPA_FuelCombustionOther': 'StationaryFuelCombustion',
    'ChemicalAndAlliedProductManufacturing': 'IndustrialAndOtherProcesses',
    'MetalsProcessing': 'IndustrialAndOtherProcesses',
    'PetroleumAndRelatedIndustries': 'IndustrialAndOtherProcesses',
    'EPA_OtherIndustrialProcesses': 'IndustrialAndOtherProcesses',
    'SolventUtilization': 'IndustrialAndOtherProcesses',
    'StorageAndTransport': 'IndustrialAndOtherProcesses',
    'WasteDisposalAndRecycling': 'IndustrialAndOtherProcesses',
    'OnRoadVehicles': 'Transportation',
    'NonRoadEnginesAndVehicles': 'Transportation'
}
sourcepollutantmetadata = {
    'CO': 'CarbonMonoxide',
    'NOX': 'OxidesOfNitrogen',
    'PM10Primary': 'PM10',
    'PM25Primary': 'PM2.5',
    'PM10-PRI': 'PM10',
    'PM25-PRI': 'PM2.5',
    'SO2': 'SulfurDioxide',
    'VOC': 'VolatileOrganicCompound',
    'NH3': 'Ammonia',
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
    'PRESCRIBED FIRES': 'PrescribedFire'
}

sheets_national = [
    'CO', 'NOX', 'PM10Primary', 'PM25Primary', 'SO2', 'VOC', 'NH3'
]
skiphead_ammonia_national = 6
skiphead_others_national = 5
skipfoot_pm_national = 0
skipfoot_others_national = 5

sheet_state = 'State_Trends'
