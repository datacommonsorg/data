"""This file contains mappings required to get Climate Trace stat-vars.

It is used by the preproccess_data.py file to find stat-vars for sectors and
sub-sectors.
"""
GASES = {
    "co2": "CarbonDioxide",
    "ch4": "Methane",
    "n20": "NitrousOxide",
    "co2100": "CarbonDioxideEquivalent100YearGlobalWarmingPotential",
    "co220": "CarbonDioxideEquivalent20YearGlobalWarmingPotential"
}

SECTORS = {
    "fossil-fuel-operations": "FossilFuelOperations",
    "power": "Power",
    "waste": "WasteManagement",
    "agriculture": "Agriculture",
    "mineral-extraction": "MineralExtraction",
    "fluorinated-gases": "FluorinatedGases",
    "forestry-and-land-use": "ForestryAndLandUse",
    "manufacturing": "Manufacturing",
    "buildings": "FuelCombustionInBuildings",
    "transportation": "Transportation"
}

SUBSECTORS = {
    "electricity-generation":
        "ElectricityGeneration",
    "other-energy-use":
        "ClimateTrace_OtherEnergyUse",
    "domestic-aviation":
        "FuelCombustionForDomesticAviation",
    "international-aviation":
        "FuelCombustionForInternationalAviation",
    "road-transportation":
        "FuelCombustionForRoadVehicles",
    "railways":
        "FuelCombustionForRailways",
    "shipping":
        "MaritimeShipping",
    "other-transport":
        "ClimateTrace_OtherTransportation",
    "residential-and-commercial-onsite-fuel-usage":
        "FuelCombustionForResidentialCommercialOnsiteHeating",
    "other-onsite-fuel-usage":
        "ClimateTrace_OtherOnsiteFuelUsage",
    "coal-mining":
        "CoalMining",
    "solid-fuel-transformation":
        "SolidFuelTransformation",
    "oil-and-gas-production-and-transport":
        "OilAndGasProduction",
    "oil-and-gas-refining":
        "OilAndGasRefining",
    "other-fossil-fuel-operations":
        "ClimateTrace_OtherFossilFuelOperations",
    "cement":
        "CementProduction",
    "chemicals":
        "ChemicalPetrochemicalIndustry",
    "steel":
        "SteelManufacturing",
    "aluminum":
        "AluminumProduction",
    "pulp-and-paper":
        "PulpAndPaperManufacturing",
    "other-manufacturing":
        "ClimateTrace_OtherManufacturing",
    "bauxite-mining":
        "BauxiteMining",
    "copper-mining":
        "CopperMining",
    "iron-mining":
        "IronMining",
    "rock-quarrying":
        "RockQuarry",
    "sand-quarrying":
        "SandQuarry",
    "other-mineral-extraction":
        "ClimateTrace_OtherMineralExtraction",
    "enteric-fermentation":
        "EntericFermentation",
    "manure-management":
        "ManureManagement",
    "rice-cultivation":
        "RiceCultivation",
    "synthetic-fertilizer-application":
        "SyntheticFertilizerApplication",
    "cropland-fires":
        "CroplandFire",
    "other-agricultural-soil-emissions":
        "ClimateTrace_OtherAgriculturalSoilEmissions",
    "other-agriculture":
        "ClimateTrace_OtherAgriculture",
    "solid-waste-disposal":
        "SolidWasteDisposal",
    "biological-treatment-of-solid-waste-&-biogenic":
        "BiologicalTreatmentOfSolidWasteAndBiogenic",
    "incineration-and-open-burning-of-waste":
        "OpenBurningWaste",
    "wastewater-treatment-and-discharge":
        "WastewaterTreatmentAndDischarge",
    "forest-clearing":
        "ForestClearing",
    "forest-land-sink":
        "ForestLandSink",
    "forest-land-sources":
        "ForestLandSources",
    "grassland-sink":
        "GrasslandSink",
    "wetland-sources":
        "WetlandSources",
    "wetland-sink":
        "WetlandSink",
    "other-land-sources":
        "ClimateTract_OtherLandSources",
    "other-land-sink":
        "ClimateTract_OtherLandSink",
    "net-forest-emissions":
        "NetForestEmissions",
    "forest-fires":
        "ForestFire",
    "savannas-fires":
        "SavannaFire",
    "scrubland-fires":
        "ShrublandFire",
    "peatland-fires":
        "PeatlandFire",
    "forest-grassland-wetland-sink":
        "ForestGrasslandWetlandSink",
    "forest-land-clearing":
        "ForestLandClearing",
    "forest-land-degradation":
        "ForestLandDegredation",
    "forest-land-fires":
        "ForestLandFire",
    "grassland-fires":
        "GrasslandFire",
    "net-grassland-emissions":
        "NetGrasslandEmissions",
    "net-wetland-emissions":
        "NetWetlandEmissions",
    "wetland-fires":
        "WetlandFire"
}
