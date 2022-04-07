# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A script which has the static company ID mappings for the EPA Parent Company import to correct."""

company_id_mappings = {
    # Data Commons import-tool validation check warnings reveal some of the
    # changes below.
    "AirLiquideUsaLLC":
        "AirLiquideLargeIndustriesUsLP",
    "AirLiquideAmericaLP":
        "AirLiquideLargeIndustriesUsLP",
    "AirLiquideUs":
        "AirLiquideLargeIndustriesUsLP",
    "AirLiquideUsaInc":
        "AirLiquideLargeIndustriesUsLP",
    "AkSteelHoldingCorp":
        "AkSteelCorp",
    "AlcoaCorp":
        "AlcoaInc",
    "CovantaEnergy":
        "CovantaHoldingCorp",
    "GreenPlainsRenewableEnergyInc":
        "GreenPlains",
    "HastingsUtilitiesCityOfHastingsNe":
        "CityOfHastingsNebraska",
    "IndianaMunicipalPowerAgencyImpa100OwnsGt2AndGt3":
        "IndianaMunicipalPowerAgency",
    "JointSolidWasteDisposalBoardCityAndCountOfPeoria":
        "JointSolidWasteDisposalBoardCityAndCountyOfPeoria",
    "MartinResourceManagementCorp":
        "MartinMidstreamPartnersLP",
    "MiamiDadePublicWorksAndWasteManagementDepartment":
        "MiamiDadeCountyDepartmentOfSolidWasteManagement",
    "MiamiDadeWaterAndSewer":
        "MiamiDadeCounty",
    "NrgEnergyInc":
        "NrgEnergy",
    "OneokInc":
        "OneokPartnersLP",
    "OptimEnergyLLCCOCompetitivePowerVentures":
        "OptimEnergyLLC",
    "PetrobrasUsa":
        "PetrobrasAmericaInc",
    "PioneerNaturalResourcesCo":
        "PioneerNaturalResourcesUsaInc",
    "PrinceWilliamCountyPublicWorksDepartmentSolidWasteDivision":
        "PrinceWilliamCountyPublicWorksDepartmentSolidWasteDiv",
    "SandridgeProductionAndExplorationLLC":
        "SandridgeExplorationAndProductionLLC",
    "ShellPetroleumIncShellChemicalLPNorcoLa":
        "ShellPetroleumInc",
    "SouthwesternEnergy":
        "SouthwesternEnergyCo",
    "SouthwesternEnergyCoInc":
        "SouthwesternEnergyCo",
    "TpfGencoCoInvestmentFundLP":
        "TpfIiALP",
    "UsgCorp":
        "USGypsumCorp",
    "USGypsumCo":
        "USGypsumCorp",
    "UsSteel":
        "UsSteelCorp",
    "USSteel":
        "UsSteelCorp",
    "VanguardNaturalResourcesLLC":
        "VanguardNaturalResourcesInc",
    "VanguardNaturalResourcesIncorporated":
        "VanguardNaturalResourcesInc",
    "WestrockCorp":
        "WestrockCo",
    "XcelEnergy":
        "XcelEnergyInc",

    # Special case: https://www.epa.gov/enforcement/equilon-enterprises-llc-doing-business-shell-oil-products-us-motiva-enterprises-llc-and
    "EquilonEnterprisesLLCDbaShellOilProductsUs":
        "EquilonEnterprisesLLC",
    "MotivaEnterprisesLLC":
        "EquilonEnterprisesLLC",
    "DeerParkRefiningLimitedPartnership":
        "EquilonEnterprisesLLC",
    "DeerParkRefiningLP":
        "EquilonEnterprisesLLC",
    "ShellOilProductsUs":
        "EquilonEnterprisesLLC",
    "ShellPetroleumIncorporated":
        "ShellPetroleumInc",
}
