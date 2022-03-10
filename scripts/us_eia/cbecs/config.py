# Copyright 2022 Google LLC
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
'''
Configs for processing CBECS data files.
'''

# Map form strings in data source to proverty-values.
PROPERTY_MAP = {
    # Column properties
    'NumberOfBuildings': {
        'Scale': 1000,
        'populationType': 'CommercialBuilding',
        'measuredProperty': 'count'
    },
    'TotalFloorspace': {
        'measuredProperty': 'floorSize',
        'populationType': 'CommercialBuilding',
    },
    'TotalWorkers': {
        'measuredProperty': 'Workers',
        'populationType': 'CommercialBuilding',
    },
    'MeanSquareFeetPerBuilding': {
        #'measuredProperty': 'floorSize',
        #'Per': 'Building',
        'measuredProperty': 'floorSizePerBuilding',
        'populationType': 'CommercialBuilding',
        'statType': 'meanValue',
        'unit': 'SquareFoot',
    },
    'MeanSquareFeetPerWorker1': {
        #'measuredProperty': 'floorSize',
        #'Per': 'Worker',
        'measuredProperty': 'floorSizePerWorker',
        'populationType': 'CommercialBuilding',
        'statType': 'meanValue',
        'unit': 'SquareFoot',
    },
    'MeanOperatingHoursPerWeek': {
        #'measuredProperty': 'workHours',
        #'Per': 'Week',
        'measuredProperty': 'workHoursPerWeek',
        'populationType': 'CommercialBuilding',
        'statType': 'meanValue',
        'unit': 'SquareFoot',
    },
    'MedianSquareFeetPerBuilding': {
        #'measuredProperty': 'floorSize',
        #'Per': 'Building',
        'measuredProperty': 'floorSizePerBuilding',
        'populationType': 'CommercialBuilding',
        'statType': 'medianValue',
        'unit': 'SquareFoot',
    },
    'MedianSquareFeetPerWorker1': {
        #'measuredProperty': 'floorSize',
        #'Per': 'Worker',
        'measuredProperty': 'floorSizePerWorker',
        'populationType': 'CommercialBuilding',
        'statType': 'medianValue',
        'unit': 'SquareFoot',
    },
    'MedianOperatingHoursPerWeek': {
        #'measuredProperty': 'workHours',
        #'Per': 'Week',
        'measuredProperty': 'workHoursPerWeek',
        'populationType': 'CommercialBuilding',
        'statType': 'medianValue',
        'unit': 'SquareFoot',
    },
    'MedianAgeOfBuildings': {
        'measuredProperty': 'age',
        'populationType': 'CommercialBuilding',
        'statType': 'medianValue',
        'unit': 'Year',
    },
    'EnergySourcesUsed': {
        'usingEnergySource': '@VALUE',
    },
    'AllBuildings': {
        'populationType': 'CommercialBuilding',
    },
    'BuildingsUsingAnyEnergySource': {
        'energySource': 'Any',
    },
    'Electricity': {
        '@VALUE': 'Electricity',
    },
    'NaturalGas': {
        '@VALUE': 'NaturalGas',
    },
    'FuelOil': {
        '@VALUE': 'FuelOil',
    },
    'DistrictHeat': {
        '@VALUE': 'DistrictHeat',
    },  # new
    'DistrictChilledWater': {
        '@VALUE': 'DistrictChilledWater',
    },  # new
    'Propane': {
        '@VALUE': 'Propane',
    },  # new
    'Solar': {
        '@VALUE': 'Solar',
    },
    'WoodCoalAndOther': {
        '@VALUE': 'WoodCoalAndOther',
    },  # new

    # Row properties
    'BuildingFloorspace': {
        'floorSize': '[{@VALUE} {@UNIT}]',
    },
    'YearConstructed': {
        'dateBuilt': '[@VALUE Year]'
    },
    'NumberOfWorkers': {
        'NumberWorkers': '[{@VALUE} Worker]'
    },
    'WeeklyOperatingHours': {
        'workHours': '[{@VALUE} Hour]'
    },
    'OpenContinuously': {
        'workHours': '[168 Hour]'
    },
    'Ownership and occupancy': {
        #'establishmentOwnership': '@VALUE'
    },
    'NongovernmentOwned': {
        'establishmentOwnership': 'NonGovernmentOwned'
    },
    'GovernmentOwned': {
        'establishmentOwnership': 'GovernmentOwned'
    },
    'Local': {
        'establishmentOwnership': 'LocalGovernmentOwned'
    },
    'State': {
        'establishmentOwnership': 'StateGovernmentOwned'
    },
    'Federal': {
        'establishmentOwnership': 'FederalGovernmentOwned'
    },
    'OwnerOccupied': {
        'occupancyTenure': 'dcs:OwnerOccupied'
    },
    'Leased Tenant': {
        'occupancyTenure': 'dcs:RenterOccupied'
    },
    'Unoccupied': {
        'occupancyTenure': 'dcs:Vacant'
    },
    'OwnerOccupiedAndLeased': {
        'occupancyTenure': 'dcs:OwnerOccupied_RenterOccupied'
    },
    'EnergySources': {
        'HasEnergySource': '@VALUE'
    },
    'EnergyEndUses': {
        'usedFor': '@VALUE'
    },
    'BuildingsWithSpaceHeating': {
        '@VALUE': 'SpaceHeating',
        'amenityFeature': 'SpaceHeating',
    },
    'BuildingsWithCooling': {
        '@VALUE': 'Cooling',
        'amenityFeature': 'Cooling',
    },
    'BuildingsWithWaterHeating': {
        '@VALUE': 'WaterHeating',
        'amenityFeature': 'WaterHeating',
    },
    'BuildingsWithCooking': {
        '@VALUE': 'Cooking',
        'amenityFeature': 'Cooking',
    },
    'BuildingsWithManufacturing': {
        '@VALUE': 'Manufacturing',
        'amenityFeature': 'Manufacturing',
    },
    'BuildingsWithElectricityGeneration': {
        '@VALUE': 'ElectricityGeneration',
        'amenityFeature': 'ElectricityGeneration',
    },
    'SpaceHeating': {
        'usedFor': 'SpaceHeating'
    },
    'Cooling': {
        'usedFor': 'Cooling'
    },
    'WaterHeating': {
        'usedFor': 'WaterHeating'
    },
    'Cooking': {
        'usedFor': 'Cooking'
    },
    'ManuFacturing': {
        'usedFor': 'Manufacturing'
    },
    'Manufacturing': {
        'usedFor': 'Manufacturing'
    },
    'ElectricityGenerAtion': {
        'usedFor': 'ElectricityGeneration'
    },
    'ElectricityGeneration': {
        'usedFor': 'ElectricityGeneration'
    },
    'FoodPreparatoinOrServingAreasInNonFoodServiceBuildings': {
        'foodEstablishment': '@VALUE'
    },
    'FastFoodSmallRestaurant': {
        'foodEstablishment': 'FastFoodRestaurant'
    },
    'CafeteriaLargeRestaurant': {
        'foodEstablishment': 'Restaurant'
    },
    'CommercialKitchenFoodPreparationArea': {
        'foodEstablishment': 'CommercialKitchen'
    },
    'SmallKitchenArea': {
        'foodEstablishment': 'SmallKitchen'
    },
    'NumberOfFloors': {
        'NumberOfFloors': '@VALUE',
        '@UNIT': 'Floor'
    },
    'NumberOfElevators': {
        'NumberOfElevators': '@VALUE',
        '@UNIT': 'Elevator'
    },
    'NumberOfEstablishments': {
        'NumberOfEstablishments': '@VALUE',
        '@UNIT': 'Establishment'
    },
    'PercentLitDuringOffHours': {
        'AmountLitDuringOffHours': '@VALUE',
        '@UNIT': 'Percent'
    },
    'PercentLitWhenOpen': {
        'AmountLitWhenOpen': '@VALUE',
        '@UNIT': 'Percent'
    },
    'PercentOfFloorspaceCooled': {
        'PercentOfFloorspaceCooled': '@VALUE',
        '@UNIT': 'Percent'
    },
    'PercentOfFloorspaceHeated': {
        'PercentOfFloorspaceHeated': '@VALUE',
        '@UNIT': 'Percent'
    },
    'PercentLitDuringOffHours': {
        'AmountLitDuringOffHours': '@VALUE',
        '@UNIT': 'Percent'
    },
    'PercentageLitWhenOpen': {
        'AmountLitWhenOpen': '@VALUE',
        '@UNIT': 'Percent'
    },
    'PercentageOfFloorspaceCooled': {
        'PercentageOfFloorspaceCooled': '@VALUE',
        '@UNIT': 'Percent'
    },
    'PercentageOfFloorspaceHeated': {
        'PercentageOfFloorspaceHeated': '@VALUE',
        '@UNIT': 'Percent'
    },
    'One': {
        '@VALUE': '[1 @UNIT]'
    },
    'Two': {
        '@VALUE': '[2 @UNIT]'
    },
    'Three': {
        '@VALUE': '[3 @UNIT]'
    },
    'Four': {
        '@VALUE': '[4 @UNIT]'
    },
    'Five': {
        '@VALUE': '[5 @UNIT]'
    },
    'Six': {
        '@VALUE': '[6 @UNIT]'
    },
    'Seven': {
        '@VALUE': '[7 @UNIT]'
    },
    'Eight': {
        '@VALUE': '[8 @UNIT]'
    },
    'Nine': {
        '@VALUE': '[9 @UNIT]'
    },
    'Two Five': {
        '@VALUE': '[2 5 @UNIT]'
    },
    'Four Nine': {
        '@VALUE': '[4 9 @UNIT]'
    },
    'Six -': {
        '@VALUE': '[6 - @UNIT]'
    },
    'OneFloor': {
        '@VALUE': '[1 Floor]'
    },
    'TwoFloors': {
        '@VALUE': '[2 Floor]'
    },
    'ThreeFloors': {
        '@VALUE': '[3 Floor]'
    },
    'FourFloors': {
        '@VALUE': '[4 Floor]'
    },
    'FiveFloors': {
        '@VALUE': '[5 Floor]'
    },
    'SixFloors': {
        '@VALUE': '[6 Floor]'
    },
    'SevenFloors': {
        '@VALUE': '[7 Floor]'
    },
    'EightFloors': {
        '@VALUE': '[8 Floor]'
    },
    'NineFloors': {
        '@VALUE': '[9 Floor]'
    },
    'Two FiveFloors': {
        '@VALUE': '[2 5 Floor]'
    },
    'Four NineFloors': {
        '@VALUE': '[4 9 Floor]'
    },
    'Six - Floors': {
        '@VALUE': '[6 - Floor]'
    },
    '1 5': {
        '@VALUE': '[1 50 @UNIT]'
    },
    '1 to 50': {
        '@VALUE': '[1 50 @UNIT]'
    },
    '2 5': {
        '@VALUE': '[2 5 @UNIT]'
    },
    '6 10': {
        '@VALUE': '[6 10 @UNIT]'
    },
    '11 20': {
        '@VALUE': '[11 20 @UNIT]'
    },
    '51 100': {
        '@VALUE': '[51 100 @UNIT]'
    },
    '51 99': {
        '@VALUE': '[51 99 @UNIT]'
    },
    '100': {
        '@VALUE': '[100 @UNIT]'
    },
    'NotHeated' : { 'PercentageOfFloorspaceHeated': '0' },
    '1 50PercentHeated': { 'PercentageOfFloorspaceHeated': '[1 50]' },
    '51 99PercentHeated': { 'PercentageOfFloorspaceHeated': '[51 99]' },
    '100PercentHeated': { 'PercentageOfFloorspaceHeated': '100' },
    # Units
    'SquareFeet': {
        'unit': 'SquareFoot',
        '@UNIT': 'SquareFoot',
    },
    'MillionSquareFeet': {
        'unit': 'SquareFoot',
        'Scale': 1000000,
    },
    'Thousand': {
        'Scale': 1000
    },

    # Places
    'CensusRegionAndDivision': {
        'observationAbout': '@VALUE'
    },
    'CensusRegion': {
        'observationAbout': '@VALUE'
    },
    'Northeast': {
        'observationAbout': 'USNortheastRegion'
    },
    'NewEngland': {
        'observationAbout': 'USNewEnglandDivision'
    },
    'MiddleAtlantic': {
        'observationAbout': 'USMiddleAtlanticDivision'
    },
    'Midwest': {
        'observationAbout': 'USMidwestRegion'
    },
    'EastNorthCentral': {
        'observationAbout': 'USEastNorthCentralDivision'
    },
    'WestNorthCentral': {
        'observationAbout': 'USWestNorthCentralDivision'
    },
    'South': {
        'observationAbout': 'USSouthRegion'
    },
    'SouthAtlantic': {
        'observationAbout': 'USSouthAtlanticDivision'
    },
    'EastSouthCentral': {
        'observationAbout': 'USEastSouthCentralDivision'
    },
    'WestSouthCentral': {
        'observationAbout': 'USWestSouthCentralDivision'
    },
    'West': {
        'observationAbout': 'USWestRegion'
    },
    'Mountain': {
        'observationAbout': 'USMountainDivision'
    },
    'Pacific': {
        'observationAbout': 'USPacificDivision'
    },
}
