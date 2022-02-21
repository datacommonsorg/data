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
"""Maps to respective schema dcids for pvs used in the superfund import."""

### Map for the different contaminated media to their respective dcids
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
