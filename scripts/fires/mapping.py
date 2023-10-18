# Copyright 2022 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Mappings to create CSV for WFIGS data.
"""
CAUSE_DCID_MAP = {
    "Human":
        "FireCauseHuman",
    "Natural":
        "FireCauseNatural",
    "Unknown":
        "FireCauseUnknown",
    "Undetermined":
        "FireCauseUnknown",
    "CauseandOriginNotIdentified":
        "FireCauseUnknown",
    "DebrisBurning(FireUse)":
        "DebrisOrOpenBurning",
    "Debrisandopenburning":
        "DebrisOrOpenBurning",
    "Equipment":
        "EquipmentAndVehicleUse",
    "Equipmentandvehicleuse":
        "EquipmentAndVehicleUse",
    "Firearmsandexplosivesuse":
        "FirearmsAndExplosivesUse",
    "Lightning":
        "LightningEvent",
    "MiscOrOther":
        "FireCauseOther",
    "Incendiary":
        "IncendiaryMaterials",
    "Misuseoffirebyaminor":
        "MisuseOfFireByMinor",
    "Natural":
        "FireCauseNatural",
    "OtherHumanCause":
        "NIFC_OtherHumanFireCause",
    "OtherNaturalCause":
        "NIFC_OtherNaturalFireCause",
    "Othercauses":
        "FireCauseOther",
    "PowergenerationOrtransmissionOrdistribution":
        "PowerProduction",
    "Railroad":
        "Railroad",
    "Railroadoperationsandmaintenance":
        "RailroadOperationsAndMaintenance",
    "Undetermined(remarksrequired)":
        "FireCauseUndetermined",
    "Utilities":
        "FireCauseUtilities",
    "Aerialfireworks":
        "AerialFireworks",
    "Agricultural":
        "Agriculture",
    "Aircraft":
        "aircraft",
    "Arson-CrimeConcealment":
        "ArsonCrimeConcealment",
    "Arson-Excitement":
        "ArsonExcitement",
    "Arson-ExtremismOrTerrorism":
        "ArsonExtremismOrTerrorism",
    "Arson-Profit":
        "ArsonProfit",
    "Arson-Retaliation":
        "ArsonRetaliation",
    "Arson-Vandalism":
        "ArsonVandalism",
    "BarbequeOrsmoker":
        "BarbequeOrSmoker",
    "Barrel":
        "FireCauseBarrel",
    "BroadcastOrPrescribedBurn":
        "PrescribedFire",
    "BurnBarrel":
        "FireCauseBarrel",
    "Burningpersonalitems":
        "BurningPersonalItems",
    "ChainsawOrbrushsawOrweedtrimmer":
        "ChainsawOrBrushsawOrWeedtrimmer",
    "CigarOrcigaretteOrpipe":
        "CigarOrCigaretteOrPipe",
    "Cigarette":
        "Cigarettes",
    "Commercialtransportvehicle":
        "CommercialTransportVehicle",
    "Device":
        "device",
    "DumpBurning":
        "OpenBurningWaste",
    "E-cigarette":
        "ECigarettes",
    "ElectricmotorOrpowertoolsOrbattery":
        "ElectricMotorOrPowerToolsOrBattery",
    "ElectricaltransmissionOrdistributionsystems":
        "ElectricalTransmissionOrDistributionSystems",
    "Explodingtargetshooting":
        "ExplodingTargetShooting",
    "Fireworks(ConsumerorPersonalUse)":
        "FireworksConsumerOrPersonalUse",
    "Fireworks(DisplayorProfessionalUse)":
        "FireworksDisplayOrProfessionalUse",
    "FlaresOrfuses":
        "FlaresOrDuses",
    "GascookingOrwarmingOrlightingdevice":
        "GasCookingOrWarmingOrLightingdevice",
    "Heavyequipment&implements":
        "HeavyEquipmentAndImplements",
    "Hotwork:welderOrgrinderOrtorchOrcutter":
        "HotworkWelderOrGrinderOrTorchOrCutter",
    "Incendiarydevice":
        "IncendiaryDevice",
    "LighterOrmatches":
        "LighterOrMatches",
    "Match(s)":
        "Matches",
    "MachinepileOrslash":
        "MachinePileOrSlash",
    "MotorVehicles":
        "MotorVehicle",
    "Muzzle-loadingFirearms":
        "MuzzleLoadingFirearms",
    "OHVOrATVOrmotorcycle":
        "OhvOrAtvOrMotorcycle",
    "OilOrgasproductionOrtransportation":
        "OilOrGasProductionOrTransportation",
    "Opentrashburning":
        "OpenTrashBurning",
    "OriginandOrorcausenotidentified":
        "FireCauseUnknown",
    "Origindestroyed":
        "OriginDestroyed",
    "Other(remarksrequired)":
        "FireCauseOther",
    "Otherlandclearing":
        "OtherLandClearing",
    "Othersmallengineequipment":
        "OtherSmallEngineEquipment",
    "Other,Known":
        "FireCauseOtherKnown",
    "Other,Unknown":
        "FireCauseOtherUnknown",
    "PassengervehicleOrmotorizedRV":
        "PassengerVehicleOrMotorizedRV",
    "Right-of-Way":
        "RightOfWay",
    "Right-of-WayMaintenance":
        "RightOfWayMaintenance",
    "Spontaneouscombustion":
        "SpontaneousCombustion",
    "TractorsOrmowersOrbrushhogs":
        "TractorsOrMowersOrBrushhogs",
    "Trailer":
        "trailer",
    "Underinvestigation":
        "UnderInvestigation",
    "Unknown(remarksrequired)":
        "FireCauseUnknown",
    "Yarddebris":
        "YardDebris"
}

POOSTATE_GEOID_MAP = {
    "CA-BC": "dcid:wikidataId/Q1974",
    "CA-SK": "dcid:wikidataId/Q1989",
    "CA-YT": "dcid:wikidataId/Q2009",
    "MX-BCN": "dcid:wikidataId/Q58731",
    # BC and BCN are both Baja California
    "MX-BN": "dcid:wikidataId/Q58731",
    "MX-CA": "dcid:wikidataId/Q53079",
    "MX-CH": "dcid:wikidataId/Q53079",
    "MX-SO": "dcid:wikidataId/Q46422",
    "MX-SON": "dcid:wikidataId/Q46422",
    "MX-TAM": "dcid:wikidataId/Q80007",
    "US-AK": "dcid:geoId/02, dcid:country/USA",
    "US-AL": "dcid:geoId/01, dcid:country/USA",
    "US-AR": "dcid:geoId/04, dcid:country/USA",
    "US-AZ": "dcid:geoId/04, dcid:country/USA",
    "US-CA": "dcid:geoId/06, dcid:country/USA",
    "US-CO": "dcid:geoId/08, dcid:country/USA",
    "US-CT": "dcid:geoId/09, dcid:country/USA",
    "US-DC": "dcid:geoId/11, dcid:country/USA",
    "US-DE": "dcid:geoId/10, dcid:country/USA",
    "US-FL": "dcid:geoId/12, dcid:country/USA",
    "US-GA": "dcid:geoId/13, dcid:country/USA",
    "US-GU": "dcid:country/GUM",
    "US-HI": "dcid:geoId/15, dcid:country/USA",
    "US-IA": "dcid:geoId/19, dcid:country/USA",
    "US-ID": "dcid:geoId/16, dcid:country/USA",
    "US-IL": "dcid:geoId/17, dcid:country/USA",
    "US-IN": "dcid:geoId/18, dcid:country/USA",
    "US-KS": "dcid:geoId/20, dcid:country/USA",
    "US-KY": "dcid:geoId/21, dcid:country/USA",
    "US-LA": "dcid:geoId/22, dcid:country/USA",
    "US-MA": "dcid:geoId/25, dcid:country/USA",
    "US-MD": "dcid:geoId/24, dcid:country/USA",
    "US-ME": "dcid:geoId/23, dcid:country/USA",
    "US-MI": "dcid:geoId/26, dcid:country/USA",
    "US-MN": "dcid:geoId/27, dcid:country/USA",
    "US-MO": "dcid:geoId/29, dcid:country/USA",
    "US-MS": "dcid:geoId/28, dcid:country/USA",
    "US-MT": "dcid:geoId/30, dcid:country/USA",
    "US-NC": "dcid:geoId/37, dcid:country/USA",
    "US-ND": "dcid:geoId/38, dcid:country/USA",
    "US-NE": "dcid:geoId/31, dcid:country/USA",
    "US-NH": "dcid:geoId/33, dcid:country/USA",
    "US-NJ": "dcid:geoId/34, dcid:country/USA",
    "US-NM": "dcid:geoId/35, dcid:country/USA",
    "US-NV": "dcid:geoId/32, dcid:country/USA",
    "US-NY": "dcid:geoId/36, dcid:country/USA",
    "US-OH": "dcid:geoId/39, dcid:country/USA",
    "US-OK": "dcid:geoId/40, dcid:country/USA",
    "US-OR": "dcid:geoId/41, dcid:country/USA",
    "US-PA": "dcid:geoId/42, dcid:country/USA",
    "US-PR": "dcid:geoId/72, dcid:country/USA",
    "US-SC": "dcid:geoId/45, dcid:country/USA",
    "US-SD": "dcid:geoId/46, dcid:country/USA",
    "US-TN": "dcid:geoId/47, dcid:country/USA",
    "US-TX": "dcid:geoId/48, dcid:country/USA",
    "US-UT": "dcid:geoId/49, dcid:country/USA",
    "US-VA": "dcid:geoId/51, dcid:country/USA",
    "US-VT": "dcid:geoId/50, dcid:country/USA",
    "US-WA": "dcid:geoId/53, dcid:country/USA",
    "US-WI": "dcid:geoId/55, dcid:country/USA",
    "US-WV": "dcid:geoId/54, dcid:country/USA",
    "US-WY": "dcid:geoId/56, dcid:country/USA"
}
