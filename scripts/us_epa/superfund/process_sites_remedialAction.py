# Copyright 2021 Google LLC
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
"""Remedial action by contaminated thing dataset for superfund sites import

This import uses the dataset:
- ./data/401052.xlsx
    This file describes Remedy Component Data for Decision Documents by Media, FYs 1982-2017 (Final NPL, Deleted NPL, and Superfund Alternative Approach Sites). The data includes sites
    1) final or deleted on the National Priorities List (NPL); and 
    2) sites with a Superfund Alternative Approach (SAA) Agreement in place. The only sites included that are 1) not on the NPL; 2) proposed for NPL; or 3) removed from proposed NPL, are those with an SAA Agreement in place.
"""

from absl import app, flags
import os
import sys
import pandas as pd

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../'))  # for utils
from superfund.utils import write_tmcf

FLAGS = flags.FLAGS
flags.DEFINE_string('input_path', './',
                    'Path to the directory with input files')
flags.DEFINE_string(
    'output_path', './',
    'Path to the directory where generated files are to be stored.')

_TEMPALTE_MCF = """Node: E:SuperfundSite->E0
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->observationAbout
observationDate: C:SuperfundSite->observationDate
variableMeasured: C:SuperfundSite->variableMeasured
value: C:SuperfundSite->value
"""

_REMEDIAL_ACTION_DCID_MAP = {
    "Acid Extraction (exsitu)":
        "AcidExtractionExsitu",
    "Active Gas Venting System":
        "ActiveGasVentingSystem",
    "Active Soil Pressurization (for VI mitigation)":
        "ActiveSoilPressurizationForVIMitigation",
    "Aeration":
        "Aeration",
    "Aeration (exsitu)":
        "AerationExsitu",
    "Aeration (insitu)":
        "AerationInsitu",
    "Aeration Basin (P&T, exsitu)":
        "AerationBasinPTExsitu",
    "Air Sparging (physical treatment, insitu)":
        "AirSpargingPhysicalTreatmentInsitu",
    "Air Stripping (P&T, exsitu)":
        "AirStrippingPTExsitu",
    "Amendments (insitu)":
        "AmendmentsInsitu",
    "Biopile (exsitu)":
        "BiopileExsitu",
    "Bioreactive Wall (insitu)":
        "BioreactiveWallInsitu",
    "Bioremediation":
        "Bioremediation",
    "Bioremediation (P&T, other, NOS, exsitu)":
        "BioremediationPTOtherNOSExsitu",
    "Bioremediation (aerobic, insitu)":
        "BioremediationAerobicInsitu",
    "Bioremediation (anaerobic, insitu)":
        "BioremediationAnaerobicInsitu",
    "Bioremediation (bioaugmentation, insitu)":
        "BioremediationBioaugmentationInsitu",
    "Bioremediation (cometabolic treatment, insitu)":
        "BioremediationCometabolicTreatmentInsitu",
    "Bioremediation (composting, exsitu)":
        "BioremediationCompostingExsitu",
    "Bioremediation (landfarming, aerobic, exsitu)":
        "BioremediationLandfarmingAerobicExsitu",
    "Bioremediation (other, NOS, exsitu)":
        "BioremediationOtherNOSExsitu",
    "Bioremediation (other, NOS, insitu)":
        "BioremediationOtherNOSInsitu",
    "Bioremediation (slurry phase, exsitu)":
        "BioremediationSlurryPhaseExsitu",
    "Bioventing":
        "Bioventing",
    "Bioventing (insitu)":
        "BioventingInsitu",
    "Bottom Liner":
        "BottomLiner",
    "Building Sealant":
        "BuildingSealant",
    "COC Only":
        "COC",
    "Cap":
        "Cap",
    "Cap (amended, insitu)":
        "CapAmendedInsitu",
    "Cap (engineered cap)":
        "CapEngineeredCap",
    "Cap (exsitu)":
        "CapExsitu",
    "Cap (insitu)":
        "CapInsitu",
    "Cap (sand, subaqueous with sediment)":
        "CapSandSubaqueousWithSediment",
    "Carbon Adsorption":
        "CarbonAdsorption",
    "Carbon Adsorption (liquid phase, P&T, exsitu)":
        "CarbonAdsorptionLiquidPhasePtExsitu",
    "Carbon Adsorption (vapor phase)":
        "CarbonAdsorptionVaporPhase",
    "Centralized Waste Treatment Facility (onsite)":
        "CentralizedWasteTreatmentFacilityOnsite",
    "Chemical Oxidation":
        "ChemicalOxidation",
    "Chemical Oxidation (P&T, exsitu)":
        "ChemicalOxidationPTExsitu",
    "Chemical Oxidation (exsitu)":
        "ChemicalOxidationExsitu",
    "Chemical Oxidation (insitu)":
        "ChemicalOxidationInsitu",
    "Chemical Oxidation/Reduction (P&T, exsitu)":
        "ChemicalOxidationReductionPTExsitu",
    "Chemical Oxidation/Reduction (exsitu)":
        "ChemicalOxidationReductionExsitu",
    "Chemical Oxidation/Reduction (insitu)":
        "ChemicalOxidationReductionInsitu",
    "Chemical Reduction":
        "ChemicalReduction",
    "Chemical Reduction (P&T, exsitu)":
        "ChemicalReductionPTExsitu",
    "Chemical Reduction (exsitu)":
        "ChemicalReductionExsitu",
    "Chemical Reduction (insitu)":
        "ChemicalReductionInsitu",
    "Chemical Treatment":
        "ChemicalTreatment",
    "Chemical Treatment (dehalogenation, exsitu)":
        "ChemicalTreatmentDehalogenationExsitu",
    "Chemical Treatment (other, NOS, insitu)":
        "ChemicalTreatmentOtherNOSInsitu",
    "Chemical Treatment (solvent extraction, exsitu)":
        "ChemicalTreatmentSolventExtractionExsitu",
    "Clarification (sedimentation, P&T, exsitu)":
        "ClarificationSedimentationPTExsitu",
    "Coagulation/Flocculation (P&T, exsitu)":
        "CoagulationflocculationPTExsitu",
    "Consolidate (onsite)":
        "ConsolidateOnsite",
    "Containment":
        "Containment",
    "Containment (deep well injection)":
        "ContainmentDeepWellInjection",
    "Containment (encapsulation)":
        "ContainmentEncapsulation",
    "Containment (other, NOS, onsite)":
        "ContainmentOtherNOSOnsite",
    "Containment (overpacking)":
        "ContainmentOverpacking",
    "Containment Cell (subaqeous, confined aquatic disposal [CAD])":
        "ContainmentCellSubaqeousConfinedAquaticDisposal",
    "Containment Cell (upland/adjacent)":
        "ContainmentCellUplandAdjacent",
    "Cover (evapotranspiration)":
        "CoverEvapotranspiration",
    "Cover (soil)":
        "CoverSoil",
    "Decontamination":
        "Decontamination",
    "Demolition":
        "Demolition",
    "Dewatering":
        "Dewatering",
    "Directional Wells (for insitu applications)":
        "DirectionalWellsForInsituApplications",
    "Discharge":
        "Discharge",
    "Discharge (POTW)":
        "DischargePOTW",
    "Discharge (infiltration basin/trench)":
        "DischargeInfiltrationBasinTrench",
    "Discharge (other, NOS)":
        "DischargeOtherNOS",
    "Discharge (reuse as drinking water)":
        "DischargeReuseAsDrinkingWater",
    "Discharge (reuse as irrigation water)":
        "DischargeReuseAsIrrigationWater",
    "Discharge (reuse as process water)":
        "DischargeReuseAsProcessWater",
    "Discharge (reuse not specified)":
        "DischargeReuseNotSpecified",
    "Discharge (surface drain reinjection)":
        "DischargeSurfaceDrainReinjection",
    "Discharge (surface water/NPDES discharge)":
        "DischargeSurfaceWaterNPDESDischarge",
    "Discharge (vertical well reinjection to contaminated aquifer)":
        "DischargeVerticalWellReinjectionToContaminatedAquifer",
    "Disposal":
        "Disposal",
    "Disposal (offsite)":
        "DisposalOffsite",
    "Drainage/Erosion Control":
        "DrainageErosionControl",
    "Drainage/Erosion Control (dike/berm/levee)":
        "DrainageErosionControlDikeBermLevee",
    "Drainage/Erosion Control (ditch)":
        "DrainageErosionControlDitch",
    "Drainage/Erosion Control (other, NOS)":
        "DrainageErosionControlOtherNOS",
    "Dredging or Excavation":
        "DredgingOrExcavation",
    "Dredging":
        "Dredging",
    "Dust Suppression":
        "DustSuppression",
    "ESD - Electro Static Discharge":
        "ESD",
    "ESD - Nonfundamental Change (other)":
        "ESDNonfundamentalChangeOther",
    "ESD/Amd - ARAR(s) Change":
        "ESDAmdARARChange",
    "ESD/Amd - COC(s) Change":
        "ESDAmdCocChange",
    "ESD/Amd - Cleanup/Performance Standard Change":
        "ESDAmdCleanupPerformanceStandardChange",
    "ESD/Amd - ICs - Implement or Change":
        "ESDAmdICImplementOrChange",
    "ESD/Amd - ICs/Five-Year Reviews Removal":
        "ESDAmdICFiveyearReviewsRemoval",
    "ESD/Amd - RAO(s) Change":
        "ESDAmdRAOChange",
    "ESD/Amd - ROD Error Correction":
        "ESDAmdRODErrorCorrection",
    "ESD/Amd - Remedy Change - Other":
        "ESDAmdRemedyChangeOther",
    "ESD/Amd - Remedy Component Removal":
        "ESDAmdRemedyComponentRemoval",
    "ESD/Amd - Remedy Element Addition/Modification":
        "ESDAmdRemedyElementAdditionModification",
    "ESD/Amd - Significant Cleanup Time Change":
        "ESDAmdSignificantCleanupTimeChange",
    "ESD/Amd - Significant Cost Change":
        "ESDAmdSignificantCostChange",
    "ESD/Amd - Significant Volume Change":
        "ESDAmdSignificantVolumeChange",
    "ESD/Amd - Study/Assessment Initiation or Documentation":
        "ESDAmdStudyAssessmentInitiationOrDocumentation",
    "ESD/Amd - TI Waiver Clarification/Change":
        "ESDAmdTIWaiverClarificationChange",
    "ESD/Amd - Treatment Area Change":
        "ESDAmdTreatmentAreaChange",
    "ESD/Amd - Treatment/Disposal Location Change":
        "ESDAmdTreatmentDisposalLocationChange",
    "Electrical separation (electrokinetic separation)":
        "ElectricalSeparation",
    "Electrokinetics (insitu)":
        "ElectrokineticsInsitu",
    "Engineering Control (other, NOS)":
        "EngineeringControlOtherNOS",
    "Enhanced Interior Ventilation (for VI mitigation)":
        "EnhancedInteriorVentilationForVIMitigation",
    "Enhanced Monitored Natural Recovery":
        "EnhancedMonitoredNaturalRecovery",
    "Equalization (P&T, exsitu)":
        "EqualizationPTExsitu",
    "Evaporation (P&T, exsitu)":
        "EvaporationPTExsitu",
    "Excavation":
        "Excavation",
    "Explosive/Unexplosive Ordnance Screening/Removal":
        "ExplosiveunexplosiveOrdnanceScreeningremoval",
    "Extraction (collection drain)":
        "ExtractionCollectionDrain",
    "Extraction (recovery trench/subsurface collection drain)":
        "ExtractionRecoveryTrenchSubsurfaceCollectionDrain",
    "Extraction (recovery/vertical well)":
        "ExtractionRecoveryVerticalWell",
    "Filtration (P&T, exsitu)":
        "FiltrationPTExsitu",
    "Flame Flare (enclosed, open, other, NOS)":
        "FlameFlareEnclosedOpenOtherNOS",
    "Flushing (insitu)":
        "FlushingInsitu",
    "Fracturing (pneumatic/hydraulic)":
        "FracturingPneumaticHydraulic",
    "Free Product Recovery (active or passive, excluding MPE and bioslurping)":
        "FreeProductRecoveryActiveOrPassiveExcludingMPEAndBioslurping",
    "Free Product Recovery (bioslurping)":
        "FreeProductRecoveryBioslurping",
    "Gas Collection":
        "GasCollection",
    "Gas Collection System (active)":
        "GasCollectionSystemActive",
    "Gas Collection System (other, NOS)":
        "GasCollectionSystemOtherNOS",
    "Gas Collection System (passive)":
        "GasCollectionSystemPassive",
    "Gas Collection/Treatment":
        "GasCollectionTreatment",
    "Gas Pressure Controls":
        "GasPressureControls",
    "Habitat Restoration":
        "HabitatRestoration",
    "Hydraulic Control (containment)":
        "HydraulicControlContainment",
    "Hydraulic Control (for water table adjustment)":
        "HydraulicControlForWaterTableAdjustment",
    "Impermeable Barrier":
        "ImpermeableBarrier",
    "In Situ Decommissioning":
        "InSituDecommissioning",
    "In-well Air Stripping":
        "InwellAirStripping",
    "Incineration":
        "Incineration",
    "Incineration (offsite)":
        "IncinerationOffsite",
    "Incineration (onsite)":
        "IncinerationOnsite",
    "Institutional Controls":
        "InstitutionalControls",
    "Ion Exchange (P&T, exsitu)":
        "IonExchangePTExsitu",
    "Landfill Gas Collection/Treatment":
        "LandfillGasCollectionTreatment",
    "Leachate Control":
        "LeachateControl",
    "Membrane Filtration (reverse osmosis, P&T, exsitu)":
        "MembraneFiltrationReverseOsmosisPTExsitu",
    "Monitored Natural Attenuation":
        "MonitoredNaturalAttenuation",
    "Monitored Natural Recovery":
        "MonitoredNaturalRecovery",
    "Monitoring":
        "Monitoring",
    "Monitoring (NAPL)":
        "MonitoringNapl",
    "Monitoring (ambient air)":
        "MonitoringAmbientAir",
    "Monitoring (buildings/structures)":
        "MonitoringBuildingsstructures",
    "Monitoring (fish tissue)":
        "MonitoringFishTissue",
    "Monitoring (groundwater)":
        "MonitoringGroundwater",
    "Monitoring (indoor air)":
        "MonitoringIndoorAir",
    "Monitoring (landfill gas)":
        "MonitoringLandfillGas",
    "Monitoring (leachate)":
        "MonitoringLeachate",
    "Monitoring (sediment)":
        "MonitoringSediment",
    "Monitoring (soil gas)":
        "MonitoringSoilGas",
    "Monitoring (soil)":
        "MonitoringSoil",
    "Monitoring (solid waste)":
        "MonitoringSolidWaste",
    "Monitoring (surface water)":
        "MonitoringSurfaceWater",
    "Monitoring Site Reuse":
        "MonitoringSiteReuse",
    "Multi-phase Extraction (insitu)":
        "MultiphaseExtractionInsitu",
    "Neutralization (P&T, exsitu)":
        "NeutralizationPTExsitu",
    "Neutralization (exsitu)":
        "NeutralizationExsitu",
    "Neutralization (insitu)":
        "NeutralizationInsitu",
    "No Action":
        "NoAction",
    "No Further Action":
        "NoFurtherAction",
    "Noncombustion Energy Recovery Technology (NOS)":
        "NoncombustionEnergyRecoveryTechnologyNOS",
    "Off-gas Treatment (other, NOS)":
        "OffgasTreatmentOtherNOS",
    "Oil Water Separation (P&T, exsitu)":
        "OilWaterSeparationPTExsitu",
    "Open Burn/Open Detonation":
        "OpenBurnOpenDetonation",
    "Operations & Maintenance (O&M)":
        "OperationsMaintenance",
    "Other (NOS)":
        "OtherNOS",
    "Passive Ventilation System":
        "PassiveVentilationSystem",
    "Permeable Reactive Barrier (chemical reactive wall, passive treatment wall, etc.)":
        "PermeableReactiveBarrier",
    "Physical Separation (exsitu)":
        "PhysicalSeparationExsitu",
    "Physical Separation (exsitu, onsite)":
        "PhysicalSeparationExsituOnsite",
    "Phytoremediation (for hydraulic control)":
        "PhytoremediationForHydraulicControl",
    "Phytoremediation (for treatment insitu)":
        "PhytoremediationForTreatmentInsitu",
    "Population Relocation (other, NOS)":
        "PopulationRelocationOtherNOS",
    "Population Relocation (permanent)":
        "PopulationRelocationPermanent",
    "Population Relocation (temporary)":
        "PopulationRelocationTemporary",
    "Positive Building Pressurization (HVAC System Adjustment) (for VI mitigation)":
        "PositiveBuildingPressurizationHAVCSystemAdjustmentForVIMitigation",
    "Precipitation (P&T, exsitu)":
        "PrecipitationPTExsitu",
    "Pumping":
        "Pumping",
    "Radon Mitigation":
        "RadonMitigation",
    "Recovery Wells":
        "RecoveryWells",
    "Recycling":
        "Recycling",
    "Recycling (offsite)":
        "RecyclingOffsite",
    "Recycling (onsite)":
        "RecyclingOnsite",
    "Repair (pipe/sewer/tank repair)":
        "RepairPipeSewerTankRepair",
    "Repair (pipe/sewer/tank/structure repair)":
        "RepairPipeSewerTankStructureRepair",
    "Residential Topsoil Replacement":
        "ResidentialTopsoilReplacement",
    "Residuals Discharge":
        "ResidualsDischarge",
    "Residuals Disposal":
        "ResidualsDisposal",
    "Residuals Treatment/Disposal (offsite)":
        "ResidualsTreatmentDisposalOffsite",
    "Residuals Treatment/Disposal (onsite)":
        "ResidualsTreatmentDisposalOnsite",
    "Residuals Treatment/Disposal (other, NOS)":
        "ResidualsTreatmentDisposalOtherNOS",
    "Revegetation":
        "Revegetation",
    "Sampling":
        "Sampling",
    "Sealing (seal cracks in foundations, etc.) (for VI mitigation)":
        "SealingForVIMitigation",
    "Shoreline Stabilization":
        "ShorelineStabilization",
    "Slope Stabilization":
        "SlopeStabilization",
    "Soil Amendments":
        "SoilAmendments",
    "Soil Vapor Extraction (exsitu)":
        "SoilVaporExtractionExsitu",
    "Soil Vapor Extraction (insitu)":
        "SoilVaporExtractionInsitu",
    "Soil Washing (exsitu)":
        "SoilWashingExsitu",
    "Solidification/Stabilization (exsitu, offsite)":
        "SolidificationStabilizationExsituOffsite",
    "Solidification/Stabilization (exsitu, onsite)":
        "SolidificationStabilizationExsituOnsite",
    "Solidification/Stabilization (insitu)":
        "SolidificationStabilizationInsitu",
    "Storage (temporary, onsite)":
        "StorageTemporaryOnsite",
    "Stream Realignment":
        "StreamRealignment",
    "Streambed/bank Rehabilitation":
        "StreambedBankRehabilitation",
    "Sub-Membrane Depressurization (SMD) (for VI mitigation)":
        "SubmembraneDepressurizationForVIMitigation",
    "Sub-Slab Depressurization (SSD) (for VI mitigation)":
        "SubslabDepressurizationForVIMitigation",
    "Sub-Slab Ventilation (passive, for VI mitigation)":
        "SubslabVentilationPassiveForVIMitigation",
    "Thermal Desorption (exsitu, offsite)":
        "ThermalDesorptionExsituOffsite",
    "Thermal Desorption (exsitu, onsite)":
        "ThermalDesorptionExsituOnsite",
    "Thermal Treatment (insitu)":
        "ThermalTreatmentInsitu",
    "Thermal Treatment (other, NOS)":
        "ThermalTreatmentOtherNOS",
    "Thermal Treatment (other, NOS, exsitu, onsite)":
        "ThermalTreatmentOtherNOSExsituOnsite",
    "Thermal Treatment (other, NOS, offsite)":
        "ThermalTreatmentOtherNOSOffsite",
    "Treatment (other, NOS)":
        "TreatmentOtherNOS",
    "Treatment (other, NOS, exsitu)":
        "TreatmentOtherNOSExsitu",
    "Treatment (other, NOS, exsitu) ":
        "TreatmentOtherNOSExsitu",
    "Treatment (other, NOS, exsitu, onsite)":
        "TreatmentOtherNOSExsituOnsite",
    "Treatment (other, NOS, insitu)":
        "TreatmentOtherNOSInsitu",
    "Treatment (other, NOS, offsite)":
        "TreatmentOtherNOSOffsite",
    "Treatment (other, NOS, offsite) ":
        "TreatmentOtherNOSOffsite",
    "Treatment (other, NOS, onsite)":
        "TreatmentOtherNOSOnsite",
    "Ultraviolet (UV) Oxidation (P&T, exsitu)":
        "UVOxidationPTExsitu",
    "Vapor Barrier (passive barrier) (for VI mitigation)":
        "VaporBarrierPassiveBarrierForVIMitigation",
    "Vapor Extraction (insitu)":
        "VaporExtractionInsitu",
    "Vapor Intrusion Mitigation (other, NOS)":
        "VaporIntrusionMitigationOtherNos",
    "Vertical Engineered Barrier (deep soil mixing)":
        "VerticalEngineeredBarrierDeepSoilMixing",
    "Vertical Engineered Barrier (other)":
        "VerticalEngineeredBarrierOther",
    "Vertical Engineered Barrier (slurry wall)":
        "VerticalEngineeredBarrierSlurryWall",
    "Vitrification (exsitu, onsite)":
        "VitrificationExsituOnsite",
    "Vitrification (insitu)":
        "VitrificationInsitu",
    "Water Supply":
        "WaterSupply",
    "Water Supply (abandon water supply well)":
        "WaterSupplyAbandonWaterSupplyWell",
    "Water Supply (connect to municipal water supply system)":
        "WaterSupplyConnectToMunicipalWaterSupplySystem",
    "Water Supply (install new municipal wells)":
        "WaterSupplyInstallNewMunicipalWells",
    "Water Supply (install new private domestic wells)":
        "WaterSupplyInstallNewPrivateDomesticWells",
    "Water Supply (permanent replacement, other, NOS)":
        "WaterSupplyPermanentReplacementOtherNOS",
    "Water Supply (permanent wellhead treatment)":
        "WaterSupplyPermanentWellheadTreatment",
    "Water Supply (point-of-use/point-of-entry treatment)":
        "WaterSupplyPointofusePointofentryTreatment",
    "Water Supply (temporary replacement, other, NOS)":
        "WaterSupplyTemporaryReplacementOtherNOS",
    "Water Supply (temporary wellhead treatment)":
        "WaterSupplyTemporaryWellheadTreatment",
    "Water Supply (water supply line replacement)":
        "WaterSupplyWaterSupplyLineReplacement",
    "Wetland for Treatment":
        "WetlandForTreatment",
    "Wetland for Treatment (constructed engineered wetland)":
        "WetlandForTreatmentConstructedEngineeredWetland",
    "Wetland for Treatment (constructed engineered wetland, exsitu)":
        "WetlandForTreatmentConstructedEngineeredWetlandExsitu",
    "Wetland for Treatment (constructed engineered wetland, insitu)":
        "WetlandForTreatmentConstructedEngineeredWetlandInsitu",
    "Wetlands Replacement":
        "WetlandsReplacement",
    "Wetlands Restoration":
        "WetlandsRestoration"
}

_CONTAMINATED_THING_DCID_MAP = {
    'Groundwater': "GroundWater",
    'Soil': "Soil",
    'Sediment': "Sediment",
    'Solid Waste': "SolidWaste",
    'Surface Water': "SurfaceWater",
    'Debris': "Debris",
    'Buildings/Structures': "BuildingOrStructures",
    'Leachate': "Leachate",
    'Sludge': "Sludge",
    'Free-phase NAPL': "FreePhaseNAPL",
    'Liquid Waste': "LiquidWaste",
    'Soil Gas': "SoilGas",
    'Other': "EPA_OtherContaminatedThing",
    'Landfill Gas': "LandfillGas",
    'Air': "Atmosphere",
    'Fish Tissue': "FishTissue",
    'Residuals': "Residuals"
}


def write_sv_to_file(row, file_obj):
    if type(row['Remedy Component']) != float:
        remedial_action = _REMEDIAL_ACTION_DCID_MAP[row['Remedy Component']]
        contaminated_thing = _CONTAMINATED_THING_DCID_MAP[row['Media']]

        node_str = f"Node: dcid:RemedialAction_{remedial_action}_Contaminanted{contaminated_thing}\n"
        node_str += "typeOf: dcs:StatisticalVariable\n"
        node_str += "populationType: dcs:Thing\n"
        node_str += "statType: dcs:measurementResult\n"
        node_str += f"contaminatedThing: dcid:{contaminated_thing}\n"
        node_str += "measuredProperty: dcs:remedialAction\n"
        node_str += f"remedialAction: dcid:{remedial_action}\n\n"
        file_obj.write(node_str)

        dcid = f"dcid:RemedialAction_{remedial_action}_Contaminanted{contaminated_thing}"
        row['dcid'] = dcid
        row['Remedy Component'] = remedial_action
        return row


def process_site_remedialAction(input_path: str, output_path: str) -> int:
    remedial_action_path = os.path.join(input_path, "./data/401052.xlsx")
    remedial_action = pd.read_excel(remedial_action_path,
                                    header=1,
                                    usecols=[
                                        'EPA ID', 'Actual Completion Date',
                                        'Media', 'Remedy Component'
                                    ])
    remedial_action = remedial_action.drop_duplicates()
    remedial_action = remedial_action.dropna()

    # convert dates to appropriate format
    remedial_action['Actual Completion Date'] = pd.to_datetime(
        remedial_action['Actual Completion Date']).dt.strftime('%Y-%m-%d')

    remedial_action[
        'EPA ID'] = 'dcid:epaSuperfundSiteId/' + remedial_action['EPA ID']

    sv_df = remedial_action[['Media', 'Remedy Component']].drop_duplicates()
    sv_df = sv_df.dropna()
    f = open("remedial_action_statvars.mcf", "w")
    sv_df = sv_df.apply(write_sv_to_file, args=(f,), axis=1)
    f.close()

    remedial_action = pd.merge(remedial_action,
                               sv_df,
                               on=['Media', 'Remedy Component'],
                               how="inner")
    remedial_action.drop(columns=['Media'], inplace=True)
    remedial_action.columns = [
        'observationAbout', 'observationDate', 'value', 'variableMeasured'
    ]
    if output_path:
        remedial_action.to_csv(os.path.join(output_path,
                                            "superfund_remedialAction.csv"),
                               index=False)
        write_tmcf(_TEMPALTE_MCF,
                   os.path.join(output_path, "superfund_remedialAction.tmcf"))
    site_count = len(remedial_action['observationAbout'].unique())
    return int(site_count)


def main(_) -> None:
    site_count = process_site_remedialAction(FLAGS.input_path,
                                             FLAGS.output_path)
    print(f"Processing of {site_count} superfund sites is complete.")


if __name__ == '__main__':
    app.run(main)
