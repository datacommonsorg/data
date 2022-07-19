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
"""
This Python Script Load the datasets, cleans it
and generates cleaned CSV, MCF, TMCF file.
"""

import os
import sys
from sre_constants import IN
from absl import app, flags
import pandas as pd
import numpy as np

FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

_MCF_TEMPLATE = ("Node: dcid:{pv1}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Emissions\n"
                 "measurementQualifier: dcs:Annual{pv2}{pv3}{pv4}\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:amount\n")

_TMCF_TEMPLATE = ("Node: E:national_emission_onroad->E0\n"
                  "typeOf: dcs:StatVarObservation\n"
                  "variableMeasured: C:national_emission_onroad->SV\n"
                  "measurementMethod: C:national_emission_onroad->"
                  "Measurement_Method\n"
                  "observationAbout: C:national_emission_onroad->geo_Id\n"
                  "observationDate: C:national_emission_onroad->year\n"
                  "unit: C:national_emission_onroad->unit\n"
                  "value: C:national_emission_onroad->observation\n")


def _replace_pollutant_code(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'pollutant code': {
            '100414': 'EthylBenzene',
            '123386': 'Propanal',
            'N2O': 'NitrousOxide',
            'NH3': 'Ammonia',
            '18540299': 'Chromium_6',
            '1330207': '1_3_Xylene',
            '208968': 'Acenaphthylene',
            '53703': 'Naphtho_1_2_B_Phenanthrene',
            '75070': 'Acetaldehyde',
            'DIESEL-PM10': 'DieselPM10',
            'PM10-PRI': 'PM10',
            'PMFINE': 'PMFINE',
            '129000': 'Pyrene',
            '205992': 'Benzo_B_Fluoranthene',
            '207089': 'Benzo_K_Fluoranthene',
            '7440382': 'Arsenic',
            '86737': 'Fluorene',
            '50000': 'Formaldehyde',
            '83329': 'Acenaphthene',
            'SO4': 'Sulfate',
            '107028': 'Acrolein',
            '206440': 'Fluoranthene',
            '108883': 'Toluene',
            'CH4': 'Methane',
            '218019': 'Chrysene',
            '7439976': 'Mercury',
            'VOC': 'VolatileOrganicCompound',
            '191242': 'Benzo_GHI_Perylene',
            'PM25-PRI': 'PM2.5',
            'EC': 'ElementalCarbon',
            'OC': 'OrganicCarbon',
            '110543': 'Hexane',
            'NOX': 'OxidesOfNitrogen',
            'SO2': 'SulfurDioxide',
            '120127': 'Anthracene',
            '50328': 'Benzo_A_Pyrene',
            '540841': '2_2_4_Trimethylpentane',
            '7440020': 'Nickel',
            'CO': 'CarbonMonoxide',
            '100425': 'Styrene',
            '56553': 'Benzo_A_Anthracene',
            '7439965': 'Manganese',
            '193395': 'Indeno_1_2_3_C_D_Pyrene',
            'CO2': 'CarbonDioxide',
            'NO3': 'Nitrate',
            '71432': 'Benzene',
            '85018': 'Phenanthrene',
            '91203': 'Naphthalene',
            'DIESEL-PM25': 'DieselPM2.5',
            '106990': 'Buta_1_3_Diene',
            '55673897': '1_2_3_4_7_8_9_Heptachlorodibenzofuran',
            '60851345': '2_3_4_6_7_8_Hexachlorodibenzofuran',
            '3268879': '1_2_3_4_6_7_8_9_Octachlorodibenzo_P_Dioxin',
            '57117416': '1_2_3_7_8_Pentachlorodibenzofuran',
            '40321764': '1_2_3_7_8_Pentachlorodibenzo_P_Dioxin',
            '72918219': '1_2_3_7_8_9_Hexachlorodibenzofuran',
            '67562394': '1_2_3_4_6_7_8_Heptachlorodibenzofuran',
            '51207319': '2_3_7_8_Tetrachlorodibenzofuran',
            '57117449': '1_2_3_6_7_8_Hexachlorodibenzofuran',
            '19408743': '1_2_3_7_8_9_Hexachlorodibenzo_P_Dioxin',
            '35822469': '1_2_3_4_6_7_8_Heptachlorodibenzo_P_Dioxin',
            '57117314': '2_3_4_7_8_Pentachlorodibenzofuran',
            '39001020': '1_2_3_4_6_7_8_9_Octachlorodibenzofuran',
            '70648269': '1_2_3_4_7_8_Hexachlorodibenzofuran',
            '57653857': '1_2_3_6_7_8_Hexachlorodibenzo_P_Dioxin',
            'DIESEL-PM2': 'DieselPM2.5',
            '39227286': '1_2_3_4_7_8_Hexachlorodibenzo_P_Dioxin',
            '1746016': '2_3_7_8_Tetrachlorodibenzo_P_Dioxin',
            'DIESEL-PM1': 'DieselPM10',
            '95476': '1_2_Xylene',
            '106423': '1_4_Xylene',
            '7440439': 'Cadmium',
            '7440484': 'Cobalt',
            '98828': 'Cumene',
            '7439921': 'Lead',
            '7782505': 'Chlorine',
            '7782492': 'Selenium',
            '7723140': 'Phosphorus',
            '7440360': 'Antimony',
            '67561': 'Methanol',
            '16065831': 'Oxo_Oxochromiooxy_Chromium',
            '108383': '1_3_Xylene',
            '130498292': 'PAH_Total',
            '1634044': '2_Methoxy_2_Methylpropane',
            '91576': '2_Methylnaphthalene'
        }
    })
    return df


def _replace_pollutant_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'pollutant type(s)': {
            'HAP': 'HazardousAirPollutants',
            'GHG': 'GreenhouseGas',
            'CAP': 'CriteriaAirPollutants'
        }
    })
    return df


def _replace_tribe_fips(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'fips code': {
            'Kootenai Tribe of Idaho':
                88183,
            'Nez Perce Tribe of Idaho':
                88182,
            'Shoshone-Bannock Tribes of the Fort Hall Reservation of Idaho':
                88180,
            'Coeur dAlene Tribe of the Coeur dAlene Reservation, Idaho':
                88181,
            'Northern Cheyenne Tribe of the Northern Cheyenne Indian Reservation, Montana':
                88207,
            'Morongo Band of Cahuilla Mission Indians of the Morongo Reservation, California':
                88582
        }
    })
    return df


def _replace_unit(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({'unit': {'TON': 'Ton', 'LB': 'Pound'}})
    return df


def _replace_scc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'scc': {
            2205320080:
                'SCC/MobileLightCommercialTruckE85',
            2202410080:
                'SCC/MobileIntercityBusDiesel',
            2201110080:
                'SCC/MobileMotorcycleGas',
            2202430080:
                'SCC/MobileSchoolBusDiesel',
            2202420080:
                'SCC/MobileTransitBusDiesel',
            2202540080:
                'SCC/MobileMotorHomeDiesel',
            2202320080:
                'SCC/MobileLightCommercialTruckDiesel',
            2202530080:
                'SCC/MobileSingleUnitLonghaulTruckDiesel',
            2201520080:
                'SCC/MobileSingleUnitShorthaulTruckGas',
            2201510080:
                'SCC/MobileRefuseTruckGas',
            2202510080:
                'SCC/MobileRefuseTruckDiesel',
            2205310080:
                'SCC/MobilePassengerTruckE85',
            2205210080:
                'SCC/MobilePassengerCarE85',
            2201310080:
                'SCC/MobilePassengerTruckGas',
            2201430080:
                'SCC/MobileSchoolBusGas',
            2201000062:
                'SCC/MobileRefuelingGas',
            2201530080:
                'SCC/MobileSingleUnitLonghaulTruckGas',
            2202310080:
                'SCC/MobilePassengerTruckDiesel',
            2201210080:
                'SCC/MobilePassengerCarGas',
            2201610080:
                'SCC/MobileCombinationShorthaulTruckGas',
            2202210080:
                'SCC/MobilePassengerCarDiesel',
            2202620080:
                'SCC/MobileCombinationLonghaulTruckDiesel',
            2202520080:
                'SCC/MobileSingleUnitShorthaulTruckDiesel',
            2202610080:
                'SCC/MobileCombinationShorthaulTruckDiesel',
            2202000062:
                'SCC/MobileRefuelingDiesel',
            2201540080:
                'SCC/MobileMotorHomeGas',
            2201420080:
                'SCC/MobileTransitBusGas',
            2205000062:
                'SCC/MobileRefuelingEthanol',
            2201320080:
                'SCC/MobileLightCommercialTruckGas',
            2203420080:
                'SCC/MobileTransitBusCNG',
            2209310080:
                'SCC/MobilePassengerTruckElectric',
            2209210080:
                'SCC/MobilePassengerCarElectric',
            2201001110:
                "SCC/MobileLDGVGasRuralInterstate",
            2201001130:
                "SCC/MobileLDGVGasRuralOtherPrincipalArterial",
            2201001150:
                "SCC/MobileLDGVGasRuralMinorArterial",
            2201001170:
                "SCC/MobileLDGVGasRuralMajorCollector",
            2201001190:
                "SCC/MobileLDGVGasRuralMinorCollector",
            2201001210:
                "SCC/MobileLDGVGasRuralLocal",
            2201001230:
                "SCC/MobileLDGVGasUrbanInterstate",
            2201001250:
                "SCC/MobileLDGVGasUrbanOtherFreewaysandExpressways",
            2201001270:
                "SCC/MobileLDGVGasUrbanOtherPrincipalArterial",
            2201001290:
                "SCC/MobileLDGVGasUrbanMinorArterial",
            2201001310:
                "SCC/MobileLDGVGasUrbanCollector",
            2201001330:
                "SCC/MobileLDGVGasUrbanLocal",
            2201001390:
                "SCC/MobileLDGVGasParkingArea",
            2201020110:
                "SCC/MobileLDGT1GasRuralInterstate",
            2201020130:
                "SCC/MobileLDGT1GasRuralOtherPrincipalArterial",
            2201020150:
                "SCC/MobileLDGT1GasRuralMinorArterial",
            2201020170:
                "SCC/MobileLDGT1GasRuralMajorCollector",
            2201020190:
                "SCC/MobileLDGT1GasRuralMinorCollector",
            2201020210:
                "SCC/MobileLDGT1GasRuralLocal",
            2201020230:
                "SCC/MobileLDGT1GasUrbanInterstate",
            2201020250:
                "SCC/MobileLDGT1GasUrbanOtherFreewaysandExpressways",
            2201020270:
                "SCC/MobileLDGT1GasUrbanOtherPrincipalArterial",
            2201020290:
                "SCC/MobileLDGT1GasUrbanMinorArterial",
            2201020310:
                "SCC/MobileLDGT1GasUrbanCollector",
            2201020330:
                "SCC/MobileLDGT1GasUrbanLocal",
            2201020390:
                "SCC/MobileLDGT1GasParkingArea",
            2201040110:
                "SCC/MobileLDGT2GasRuralInterstate",
            2201040130:
                "SCC/MobileLDGT2GasRuralOtherPrincipalArterial",
            2201040150:
                "SCC/MobileLDGT2GasRuralMinorArterial",
            2201040170:
                "SCC/MobileLDGT2GasRuralMajorCollector",
            2201040190:
                "SCC/MobileLDGT2GasRuralMinorCollector",
            2201040210:
                "SCC/MobileLDGT2GasRuralLocal",
            2201040230:
                "SCC/MobileLDGT2GasUrbanInterstate",
            2201040250:
                "SCC/MobileLDGT2GasUrbanOtherFreewaysandExpressways",
            2201040270:
                "SCC/MobileLDGT2GasUrbanOtherPrincipalArterial",
            2201040290:
                "SCC/MobileLDGT2GasUrbanMinorArterial",
            2201040310:
                "SCC/MobileLDGT2GasUrbanCollector",
            2201040330:
                "SCC/MobileLDGT2GasUrbanLocal",
            2201040390:
                "SCC/MobileLDGT2GasParkingArea",
            2201070110:
                "SCC/MobileHDGVGasRuralInterstate",
            2201070130:
                "SCC/MobileHDGVGasRuralOtherPrincipalArterial",
            2201070150:
                "SCC/MobileHDGVGasRuralMinorArterial",
            2201070170:
                "SCC/MobileHDGVGasRuralMajorCollector",
            2201070190:
                "SCC/MobileHDGVGasRuralMinorCollector",
            2201070210:
                "SCC/MobileHDGVGasRuralLocal",
            2201070230:
                "SCC/MobileHDGVGasUrbanInterstate",
            2201070250:
                "SCC/MobileHDGVGasUrbanOtherFreewaysandExpressways",
            2201070270:
                "SCC/MobileHDGVGasUrbanOtherPrincipalArterial",
            2201070290:
                "SCC/MobileHDGVGasUrbanMinorArterial",
            2201070310:
                "SCC/MobileHDGVGasUrbanCollector",
            2201070330:
                "SCC/MobileHDGVGasUrbanLocal",
            2201070390:
                "SCC/MobileHDGVGasParkingArea",
            2201080110:
                "SCC/MobileMotocycleGasRuralInterstate",
            2201080130:
                "SCC/MobileMotocycleGasRuralOtherPrincipalArterial",
            2201080150:
                "SCC/MobileMotocycleGasRuralMinorArterial",
            2201080170:
                "SCC/MobileMotocycleGasRuralMajorCollector",
            2201080190:
                "SCC/MobileMotocycleGasRuralMinorCollector",
            2201080210:
                "SCC/MobileMotocycleGasRuralLocal",
            2201080230:
                "SCC/MobileMotocycleGasUrbanInterstate",
            2201080250:
                "SCC/MobileMotocycleGasUrbanOtherFreewaysandExpressways",
            2201080270:
                "SCC/MobileMotocycleGasUrbanOtherPrincipalArterial",
            2201080290:
                "SCC/MobileMotocycleGasUrbanMinorArterial",
            2201080310:
                "SCC/MobileMotocycleGasUrbanCollector",
            2201080330:
                "SCC/MobileMotocycleGasUrbanLocal",
            2201080390:
                "SCC/MobileMotocycleGasParkingArea",
            2230001110:
                "SCC/MobileLDDVDieselRuralInterstate",
            2230001130:
                "SCC/MobileLDDVDieselRuralOtherPrincipalArterial",
            2230001150:
                "SCC/MobileLDDVDieselRuralMinorArterial",
            2230001170:
                "SCC/MobileLDDVDieselRuralMajorCollector",
            2230001190:
                "SCC/MobileLDDVDieselRuralMinorCollector",
            2230001210:
                "SCC/MobileLDDVDieselRuralLocal",
            2230001230:
                "SCC/MobileLDDVDieselUrbanInterstate",
            2230001250:
                "SCC/MobileLDDVDieselUrbanOtherFreewaysandExpressways",
            2230001270:
                "SCC/MobileLDDVDieselUrbanOtherPrincipalArterial",
            2230001290:
                "SCC/MobileLDDVDieselUrbanMinorArterial",
            2230001310:
                "SCC/MobileLDDVDieselUrbanCollector",
            2230001330:
                "SCC/MobileLDDVDieselUrbanLocal",
            2230001390:
                "SCC/MobileLDDVDieselParkingArea",
            2230060110:
                "SCC/MobileLDDTDieselRuralInterstate",
            2230060130:
                "SCC/MobileLDDTDieselRuralOtherPrincipalArterial",
            2230060150:
                "SCC/MobileLDDTDieselRuralMinorArterial",
            2230060170:
                "SCC/MobileLDDTDieselRuralMajorCollector",
            2230060190:
                "SCC/MobileLDDTDieselRuralMinorCollector",
            2230060210:
                "SCC/MobileLDDTDieselRuralLocal",
            2230060230:
                "SCC/MobileLDDTDieselUrbanInterstate",
            2230060250:
                "SCC/MobileLDDTDieselUrbanOtherFreewaysandExpressways",
            2230060270:
                "SCC/MobileLDDTDieselUrbanOtherPrincipalArterial",
            2230060290:
                "SCC/MobileLDDTDieselUrbanMinorArterial",
            2230060310:
                "SCC/MobileLDDTDieselUrbanCollector",
            2230060330:
                "SCC/MobileLDDTDieselUrbanLocal",
            2230060390:
                "SCC/MobileLDDTDieselParkingArea",
            2230071110:
                "SCC/MobileHDDV2BDieselRuralInterstate",
            2230071130:
                "SCC/MobileHDDV2BDieselRuralOtherPrincipalArterial",
            2230071150:
                "SCC/MobileHDDV2BDieselRuralMinorArterial",
            2230071170:
                "SCC/MobileHDDV2BDieselRuralMajorCollector",
            2230071190:
                "SCC/MobileHDDV2BDieselRuralMinorCollector",
            2230071210:
                "SCC/MobileHDDV2BDieselRuralLocal",
            2230071230:
                "SCC/MobileHDDV2BDieselUrbanInterstate",
            2230071250:
                "SCC/MobileHDDV2BDieselUrbanOtherFreewaysandExpressways",
            2230071270:
                "SCC/MobileHDDV2BDieselUrbanOtherPrincipalArterial",
            2230071290:
                "SCC/MobileHDDV2BDieselUrbanMinorArterial",
            2230071310:
                "SCC/MobileHDDV2BDieselUrbanCollector",
            2230071330:
                "SCC/MobileHDDV2BDieselUrbanLocal",
            2230071390:
                "SCC/MobileHDDV2BDieselParkingArea",
            2230072110:
                "SCC/MobileHDDV345DieselRuralInterstate",
            2230072130:
                "SCC/MobileHDDV345DieselRuralOtherPrincipalArterial",
            2230072150:
                "SCC/MobileHDDV345DieselRuralMinorArterial",
            2230072170:
                "SCC/MobileHDDV345DieselRuralMajorCollector",
            2230072190:
                "SCC/MobileHDDV345DieselRuralMinorCollector",
            2230072210:
                "SCC/MobileHDDV345DieselRuralLocal",
            2230072230:
                "SCC/MobileHDDV345DieselUrbanInterstate",
            2230072250:
                "SCC/MobileHDDV345DieselUrbanOtherFreewaysandExpressways",
            2230072270:
                "SCC/MobileHDDV345DieselUrbanOtherPrincipalArterial",
            2230072290:
                "SCC/MobileHDDV345DieselUrbanMinorArterial",
            2230072310:
                "SCC/MobileHDDV345DieselUrbanCollector",
            2230072330:
                "SCC/MobileHDDV345DieselUrbanLocal",
            2230072390:
                "SCC/MobileHDDV345DieselParkingArea",
            2230073110:
                "SCC/MobileHDDV67DieselRuralInterstate",
            2230073130:
                "SCC/MobileHDDV67DieselRuralOtherPrincipalArterial",
            2230073150:
                "SCC/MobileHDDV67DieselRuralMinorArterial",
            2230073170:
                "SCC/MobileHDDV67DieselRuralMajorCollector",
            2230073190:
                "SCC/MobileHDDV67DieselRuralMinorCollector",
            2230073210:
                "SCC/MobileHDDV67DieselRuralLocal",
            2230073230:
                "SCC/MobileHDDV67DieselUrbanInterstate",
            2230073250:
                "SCC/MobileHDDV67DieselUrbanOtherFreewaysandExpressways",
            2230073270:
                "SCC/MobileHDDV67DieselUrbanOtherPrincipalArterial",
            2230073290:
                "SCC/MobileHDDV67DieselUrbanMinorArterial",
            2230073310:
                "SCC/MobileHDDV67DieselUrbanCollector",
            2230073330:
                "SCC/MobileHDDV67DieselUrbanLocal",
            2230073390:
                "SCC/MobileHDDV67DieselParkingArea",
            2230074110:
                "SCC/MobileHDDV8DieselRuralInterstate",
            2230074130:
                "SCC/MobileHDDV8DieselRuralOtherPrincipalArterial",
            2230074150:
                "SCC/MobileHDDV8DieselRuralMinorArterial",
            2230074170:
                "SCC/MobileHDDV8DieselRuralMajorCollector",
            2230074190:
                "SCC/MobileHDDV8DieselRuralMinorCollector",
            2230074210:
                "SCC/MobileHDDV8DieselRuralLocal",
            2230074230:
                "SCC/MobileHDDV8DieselUrbanInterstate",
            2230074250:
                "SCC/MobileHDDV8DieselUrbanOtherFreewaysandExpressways",
            2230074270:
                "SCC/MobileHDDV8DieselUrbanOtherPrincipalArterial",
            2230074290:
                "SCC/MobileHDDV8DieselUrbanMinorArterial",
            2230074310:
                "SCC/MobileHDDV8DieselUrbanCollector",
            2230074330:
                "SCC/MobileHDDV8DieselUrbanLocal",
            2230074390:
                "SCC/MobileHDDV8DieselParkingArea",
            2230075110:
                "SCC/MobileBusDieselRuralInterstate",
            2230075130:
                "SCC/MobileBusDieselRuralOtherPrincipalArterial",
            2230075150:
                "SCC/MobileBusDieselRuralMinorArterial",
            2230075170:
                "SCC/MobileBusDieselRuralMajorCollector",
            2230075190:
                "SCC/MobileBusDieselRuralMinorCollector",
            2230075210:
                "SCC/MobileBusDieselRuralLocal",
            2230075230:
                "SCC/MobileBusDieselUrbanInterstate",
            2230075250:
                "SCC/MobileBusDieselUrbanOtherFreewaysandExpressways",
            2230075270:
                "SCC/MobileBusDieselUrbanOtherPrincipalArterial",
            2230075290:
                "SCC/MobileBusDieselUrbanMinorArterial",
            2230075310:
                "SCC/MobileBusDieselUrbanCollector",
            2230075330:
                "SCC/MobileBusDieselUrbanLocal",
            2230075390:
                "SCC/MobileBusDieselParkingArea"
        }
    })
    return df


def _regularize_columns(df: pd.DataFrame, file_path: str) -> pd.DataFrame:
    """
    Reads the file for national emissions data and cleans it for concatenation
    in Final CSV.

    Args:
        df (pd.DataFrame): provides the df as input
        file_path (str): path to excel file as the input

    Returns:
        df (pd.DataFrame): provides the regularized df as output
    """
    if '2008' in file_path or '2011' in file_path:
        df.rename(columns={
            'state_and_county_fips_code': 'fips code',
            'data_set_short_name': 'data set',
            'pollutant_cd': 'pollutant code',
            'uom': 'emissions uom',
            'total_emissions': 'total emissions'
        },
                  inplace=True)
        df = df.drop(columns=[
            'tribal_name', 'st_usps_cd', 'county_name', 'data_category_cd',
            'description', 'emissions_type_code', 'aircraft_engine_type_cd',
            'emissions_op_type_code'
        ])
        df['pollutant type(s)'] = 'nan'
    elif '2017' in file_path:
        df = df.drop(columns=[
            'epa region code', 'state', 'fips state code', 'county',
            'emissions type code', 'aetc', 'reporting period',
            'emissions operating type', 'sector', 'tribal name',
            'pollutant desc', 'data category'
        ])
    elif 'tribes' in file_path:
        df.rename(columns={'tribal name': 'fips code'}, inplace=True)
        df = df.drop(columns=[
            'state', 'fips state code', 'data category', 'reporting period',
            'emissions operating type', 'emissions type code', 'pollutant desc'
        ])
        df = _replace_tribe_fips(df)
        df['pollutant type(s)'] = 'nan'
    else:
        df.rename(columns={
            'state_and_county_fips_code': 'fips code',
            'data_set': 'data set',
            'pollutant_cd': 'pollutant code',
            'uom': 'emissions uom',
            'total_emissions': 'total emissions'
        },
                  inplace=True)
        df = df.drop(columns=[
            'tribal_name', 'fips_state_code', 'st_usps_cd', 'county_name',
            'data_category', 'emission_operating_type', 'pollutant_desc',
            'emissions_type_code', 'emissions_operating_type'
        ])
        df['pollutant type(s)'] = 'nan'
    return df


def _onroad(file_path: str) -> pd.DataFrame:
    """
    Reads the file for national emissions data and cleans it for concatenation
    in Final CSV.

    Args:
        file_path (str): path to excel file as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    df = pd.read_csv(file_path, header=0, low_memory=False)
    df = _regularize_columns(df, file_path)
    df['pollutant code'] = df['pollutant code'].astype(str)
    df['geo_Id'] = [f'{x:05}' for x in df['fips code']]
    df['geo_Id'] = 'geoId/' + df['geo_Id']
    df.rename(columns={
        'emissions uom': 'unit',
        'total emissions': 'observation',
        'data set': 'year'
    },
              inplace=True)
    df['year'] = df['year'].str[:4]
    df = _replace_unit(df)
    df = _replace_scc(df)
    df = _replace_pollutant_code(df)
    df = _replace_pollutant_type(df)
    df['SV'] = ('Amount_Annual_Emissions_' + df['scc'].astype(str) + '_' +
                df['pollutant type(s)'].astype(str) + '_' +
                df['pollutant code'].astype(str))
    df['SV'] = df['SV'].str.replace('_nan', '')
    df = df.drop(
        columns=['scc', 'pollutant code', 'pollutant type(s)', 'fips code'])

    return df


class USAirEmissionTrends:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    def __init__(self, input_files: list, csv_file_path: str,
                 mcf_file_path: str, tmcf_file_path: str) -> None:
        self._input_files = input_files
        self._cleaned_csv_file_path = csv_file_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path

    def _generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.
        Args:
            None
        Returns:
            None
        """
        # Writing Genereated TMCF to local path.
        with open(self._tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(_TMCF_TEMPLATE.rstrip('\n'))

    def _generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Args:
            df_cols (list) : List of DataFrame Columns

        Returns:
            None
        """

        final_mcf_template = ""
        for sv in sv_list:
            emission_type = pollutant = ''
            sv_property = sv.split("_")
            source = '\nemissionSource: dcs:' + sv_property[3]
            if 'AirPollutants' in sv_property[4] or 'Greenhouse' in sv_property[
                    4]:
                emission_type = '\nemissionType: dcs:' + sv_property[4]
                for i in sv_property[5:]:
                    pollutant = pollutant + i + '_'
            else:
                for i in sv_property[4:]:
                    pollutant = pollutant + i + '_'
            pollutant = '\nemittedThing: dcs:' + pollutant.rstrip('_')
            final_mcf_template += _MCF_TEMPLATE.format(
                pv1=sv, pv2=source, pv3=pollutant, pv4=emission_type) + "\n"

        # Writing Genereated MCF to local path.
        with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))

    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.
        """

        final_df = pd.DataFrame(
            columns=['geo_Id', 'year', 'SV', 'observation', 'unit'])
        # Creating Output Directory
        output_path = os.path.dirname(self._cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []

        for file_path in self._input_files:
            # Taking the File name out of the complete file address
            # Used -1 to pickup the last part which is file name
            # Read till -4 inorder to remove the .csv extension
            file_name = file_path.split("/")[-1][:-4]
            file_name = file_name.split("_")[0]
            df = _onroad(file_path)
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()

        final_df = final_df.sort_values(
            by=['geo_Id', 'year', 'SV', 'observation'])
        final_df['observation'].replace('', np.nan, inplace=True)
        final_df.dropna(subset=['observation'], inplace=True)
        final_df.to_csv(self._cleaned_csv_file_path, index=False)
        sv_list = list(set(sv_list))
        sv_list.sort()
        self._generate_mcf(sv_list)
        self._generate_tmcf()


def main(_):
    input_path = FLAGS.input_path
    try:
        ip_files = os.listdir(input_path)
    except:
        print("Run the download script first.\n")
        sys.exit(1)
    ip_files = [input_path + os.sep + file for file in ip_files]
    output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "output")
    # Defining Output Files
    csv_name = "national_emission_onroad.csv"
    mcf_name = "national_emission_onroad.mcf"
    tmcf_name = "national_emission_onroad.tmcf"
    cleaned_csv_path = os.path.join(output_file_path, csv_name)
    mcf_path = os.path.join(output_file_path, mcf_name)
    tmcf_path = os.path.join(output_file_path, tmcf_name)
    loader = USAirEmissionTrends(ip_files, cleaned_csv_path, mcf_path,\
        tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)
