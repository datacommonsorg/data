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
"""Exposure and risks of superfund sites to natural hazards

This dataset is associated with the following publication: Summers, K., A. Lamaper, and K. Buck. National Hazards Vulnerability and the Remediation, Restoration and Revitalization of Contaminated Sites – 1. Superfund. ENVIRONMENTAL MANAGEMENT. Springer-Verlag, New York, NY, USA, 14, (2021). 

This script proecsses the file:
- ./data/SF_CRSI_OLEM.xlsx
  The dataset lists all active and upcoming Superfund sites and their vulnerability to 12 natural hazards using a vulnerability score between 0 and 100. Additional risk/exposure metrices are also imported.
"""
import os
import sys
from absl import app, flags
from utils import write_tmcf
import pandas as pd

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../'))  # for utils
from superfund.utils import write_tmcf

FLAGS = flags.FLAGS
flags.DEFINE_string(
  'input_path', './', 'Path to the directory with input files'
)
flags.DEFINE_string(
  'output_path', './', 'Path to the directory where generated files are to be stored.'
)

_RISK_TEMPLATE_MCF="""Node: E:SuperfundSite->E0
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:RiskScore_SuperfundSite_HurricaneEvent
value: C:SuperfundSite->HURR_EXP

Node: E:SuperfundSite->E1
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:RiskScore_SuperfundSite_TornadoEvent
value: C:SuperfundSite->TORN_EXP

Node: E:SuperfundSite->E2
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:RiskScore_SuperfundSite_LandslideEvent
value: C:SuperfundSite->LSLD_EXP

Node: E:SuperfundSite->E3
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:RiskScore_SuperfundSite_ExtremeColdWindChillEvent
value: C:SuperfundSite->LTMP_EXP

Node: E:SuperfundSite->E4
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:RiskScore_SuperfundSite_ExcessiveHeatEvent
value: C:SuperfundSite->HTMP_EXP

Node: E:SuperfundSite->E5
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:RiskScore_SuperfundSite_HailEvent
value: C:SuperfundSite->HAIL_EXP

Node: E:SuperfundSite->E6
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:RiskScore_SuperfundSite_WildfireEvent
value: C:SuperfundSite->FIRE_EXP

Node: E:SuperfundSite->E7
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:RiskScore_SuperfundSite_EarthquakeEvent
value: C:SuperfundSite->EQ_EXP

Node: E:SuperfundSite->E8
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:RiskScore_SuperfundSite_DroughtEvent
value: C:SuperfundSite->DRGH_EXP

Node: E:SuperfundSite->E9
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:RiskScore_SuperfundSite_FloodEvent
value: C:SuperfundSite->IFLD_EXP

Node: E:SuperfundSite->E10
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:RiskScore_SuperfundSite_CoastalFloodEvent
value: C:SuperfundSite->CFLD_EXP

Node: E:SuperfundSite->E11
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:RiskScore_SuperfundSite_HighWindEvent
value: C:SuperfundSite->WIND_EXP

Node: E:SuperfundSite->E12
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:ExposureScore_SuperfundSite
value: C:SuperfundSite->EXPOSURE_SCORE

Node: E:SuperfundSite->E13
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:RiskScore_SuperfundSite
value: C:SuperfundSite->RISK_SCORE

Node: E:SuperfundSite->E14
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:CRSIScore_SuperfundSite
value: C:SuperfundSite->CRSI_SCORE
"""

def process_site_hazards(input_path:str, output_path:str) -> int:
  """
  Processes ./data/SF_CRSI_OLEM.xlsx to generate clean csv and tmcf files
  """
  risk_score = pd.read_excel(os.path.join(input_path, "./data/SF_CRSI_OLEM.xlsx"), usecols=['Site_EPA_ID', 'CFLD_EXP', 'IFLD_EXP',
        'DRGH_EXP', 'EQ_EXP', 'FIRE_EXP', 'HAIL_EXP', 'HTMP_EXP', 'LTMP_EXP',
        'HURR_EXP', 'LSLD_EXP', 'TORN_EXP', 'WIND_EXP', 'EXPOSURE_SCORE',
        'RISK_SCORE', 'CRSI_SCORE'])

  risk_score['Site_EPA_ID'] = 'dcid:epaSuperfundSiteId/' + risk_score['Site_EPA_ID']
  risk_score['observationDate'] = '2019'

  if output_path:
    risk_score.to_csv(os.path.join(output_path, 'superfund_hazardExposure.csv'), index=False)
    write_tmcf(_RISK_TEMPLATE_MCF, os.path.join(output_path, 'superfund_hazardExposure.tmcf'))
  site_count = len(risk_score['Site_EPA_ID'].unique())
  return int(site_count)

def main(_) -> None:
  site_count = process_site_hazards(FLAGS.input_path, FLAGS.output_path)
  print(f"Processing of {site_count} superfund sites is complete.")

if __name__ == '__main__':
  app.run(main)
