"""This file contains mappings required to get climate trace stat-vars.

It is used by the preproccess_data.py file to find stat-vars for sectors and
sub-sectors.
"""
MEASUREMENT_METHOD_SECTORS = "ClimateTraceEstimate"

MEASUREMENT_METHOD_COUNTRIES = "dcAggregate/ClimateTraceEstimate"

STATVAR_PREFIX = "Annual_Emissions_GreenhouseGas_"

STATVAR_COUNTRY_METRICS = "Annual_Emissions_GreenhouseGas"

# Sub-sector mapping
SUBSECTOR_VAR_MAP = {
    "wastewater treatment and discharge":
        "WastewaterTreatmentAndDischarge",
    "solid waste disposal":
        "SolidWasteDisposal",
    "open burning waste":
        "OpenBurningWaste",
    "biological treatment of solid waste and biogenic":
        "BiologicalTreatmentOfSolidWasteAndBiogenic",
    "copper mining":
        "CopperMining",
    "sand quarry":
        "SandQuarry",
    "rock quarry":
        "RockQuarry",
    "iron mining":
        "IronMining",
    "coal mining":
        "CoalMining",
    "aluminum":
        "AluminumProduction",
    "fluorchemical production":
        "FluorchemicalProduction",
    "cement production":
        "CementProduction",
    "food processing beverages tobbaco":
        "FoodProcessingBeveragesTobbacoProduction",
    "glass production":
        "GlassProduction",
    "steel":
        "SteelManufacturing",
    "pulp paper":
        "PulpAndPaperManufacturing",
    "petrochemicals":
        "PetrochemicalProduction",
    "nitric acid production":
        "NitricAcidProduction",
    "lime production":
        "LimeProduction",
    "other manufacturing":
        "ClimateTrace_OtherManufacturing",
    # shrubland subsector is misspelled as scrubland in the data
    "scrubland fires":
        "ShrublandFire",
    "savannas fires":
        "SavannaFire",
    "forest fires":
        "ForestFire",
    "forest clearing":
        "ForestClearing",
    "residential commercial onsite heating":
        "FuelCombustionForResidentialCommercialOnsiteHeating",
    "refrigeration air conditioning":
        "FuelCombustionForRefrigerationAirConditioning",
    "cooking":
        "FuelCombustionForCooking",
    "rice cultivation":
        "RiceCultivation",
    "manure management":
        "ManureManagement",
    "managed soils":
        "ManagedSoils",
    "enteric fermentation":
        "EntericFermentation",
    "cropland fires":
        "CroplandFire",
    "solid fuel transformation":
        "SolidFuelTransformation",
    "oil refining":
        "PetroleumRefining",
    "oil and gas production":
        "OilAndGasProduction",
    "roads":
        "FuelCombustionForRoadVehicles",
    "railways":
        "FuelCombustionForRailways",
    "aviation":
        "FuelCombustionForAviation",
    "other transportation":
        "ClimateTrace_OtherTransportation",
    "electricity generation":
        "ElectricityGenerationFromThermalPowerPlant",
    "other energy use":
        "ClimateTrace_OtherEnergyUse",
    "shipping":
        "MaritimeShipping",
    "bauxite mining":
        "BauxiteMining"
}

# Sector mapping
SECTOR_VAR_MAP = {
    "agriculture": "Agriculture",
    "buildings": "FuelCombustionInBuildings",
    "extraction": "MineralExtraction",
    "forests": "ForestryAndLandUse",
    "manufacturing": "Manufacturing",
    "maritime": "MaritimeTransport",
    "oil and gas": "OilAndGas",
    "power": "ElectricityGeneration",
    "transport": "Transportation",
    "waste": "WasteManagement"
}
