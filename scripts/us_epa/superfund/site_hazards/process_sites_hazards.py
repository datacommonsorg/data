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
"""Exposure and risks of superfund sites to natural hazards

This dataset is associated with the following publication: Summers, K., A. Lamaper, and K. Buck. National Hazards Vulnerability and the Remediation, Restoration and Revitalization of Contaminated Sites – 1. Superfund. ENVIRONMENTAL MANAGEMENT. Springer-Verlag, New York, NY, USA, 14, (2021). 

This script proecsses the file:
- ./data/SF_CRSI_OLEM.xlsx
  The dataset lists all active and upcoming Superfund sites and their vulnerability to 12 natural hazards using a vulnerability score between 0 and 100. Additional risk/exposure metrices are also imported.
"""
import os
from absl import app, flags
import pandas as pd

FLAGS = flags.FLAGS
flags.DEFINE_string('site_hazard_input_path', './data',
                    'Path to the directory with input files')
flags.DEFINE_string(
    'site_hazard_output_path', './data/output',
    'Path to the directory where generated files are to be stored.')

_RISK_TEMPLATE_MCF = """Node: E:SuperfundSite->E0
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardRiskScore_SuperfundSite_HurricaneEvent
value: C:SuperfundSite->HURR_EXP

Node: E:SuperfundSite->E1
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardRiskScore_SuperfundSite_TornadoEvent
value: C:SuperfundSite->TORN_EXP

Node: E:SuperfundSite->E2
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardRiskScore_SuperfundSite_LandslideEvent
value: C:SuperfundSite->LSLD_EXP

Node: E:SuperfundSite->E3
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardRiskScore_SuperfundSite_ExtremeColdWindChillEvent
value: C:SuperfundSite->LTMP_EXP

Node: E:SuperfundSite->E4
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardRiskScore_SuperfundSite_ExcessiveHeatEvent
value: C:SuperfundSite->HTMP_EXP

Node: E:SuperfundSite->E5
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardRiskScore_SuperfundSite_HailEvent
value: C:SuperfundSite->HAIL_EXP

Node: E:SuperfundSite->E6
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardRiskScore_SuperfundSite_WildfireEvent
value: C:SuperfundSite->FIRE_EXP

Node: E:SuperfundSite->E7
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardRiskScore_SuperfundSite_EarthquakeEvent
value: C:SuperfundSite->EQ_EXP

Node: E:SuperfundSite->E8
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardRiskScore_SuperfundSite_DroughtEvent
value: C:SuperfundSite->DRGH_EXP

Node: E:SuperfundSite->E9
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardRiskScore_SuperfundSite_FloodEvent
value: C:SuperfundSite->IFLD_EXP

Node: E:SuperfundSite->E10
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardRiskScore_SuperfundSite_CoastalFloodEvent
value: C:SuperfundSite->CFLD_EXP

Node: E:SuperfundSite->E11
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardRiskScore_SuperfundSite_HighWindEvent
value: C:SuperfundSite->WIND_EXP

Node: E:SuperfundSite->E12
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardExposureScore_SuperfundSite
value: C:SuperfundSite->EXPOSURE_SCORE

Node: E:SuperfundSite->E13
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:NaturalHazardRiskScore_SuperfundSite
value: C:SuperfundSite->RISK_SCORE

Node: E:SuperfundSite->E14
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->Site_EPA_ID
observationDate: C:SuperfundSite->observationDate
variableMeasured: dcid:CrsiScore_SuperfundSite
value: C:SuperfundSite->CRSI_SCORE
"""

_DATASET_NAME = "./SF_CRSI_OLEM.xlsx"

_DATA_COLS = [
    'Site_EPA_ID', 'CFLD_EXP', 'IFLD_EXP', 'DRGH_EXP', 'EQ_EXP', 'FIRE_EXP',
    'HAIL_EXP', 'HTMP_EXP', 'LTMP_EXP', 'HURR_EXP', 'LSLD_EXP', 'TORN_EXP',
    'WIND_EXP', 'EXPOSURE_SCORE', 'RISK_SCORE', 'CRSI_SCORE'
]


def process_site_hazards(input_path: str, output_path: str) -> int:
    """
    Processes ./SF_CRSI_OLEM.xlsx to generate clean csv and tmcf files
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    risk_score = pd.read_excel(os.path.join(input_path, _DATASET_NAME),
                               usecols=_DATA_COLS)

    risk_score[
        'Site_EPA_ID'] = 'epaSuperfundSiteId/' + risk_score['Site_EPA_ID']
    risk_score['observationDate'] = 2021

    risk_score.to_csv(os.path.join(output_path, 'superfund_hazardExposure.csv'),
                      index=False)

    f = open(os.path.join(output_path, 'superfund_hazardExposure.tmcf'), 'w')
    f.write(_RISK_TEMPLATE_MCF)
    f.close()

    site_count = len(risk_score['Site_EPA_ID'].unique())
    return int(site_count)


def main(_) -> None:
    site_count = process_site_hazards(FLAGS.site_hazard_input_path,
                                      FLAGS.site_hazard_output_path)
    print(f"Processing of {site_count} superfund sites is complete.")


if __name__ == '__main__':
    app.run(main)
