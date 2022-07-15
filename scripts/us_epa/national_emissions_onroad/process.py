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

_TMCF_TEMPLATE = (
    "Node: E:national_emission_onroad->E0\n"
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
            '100414' : 'EthylBenzene',
            '123386' : 'Propanal',
            'N2O' : 'NitrousOxide',
            'NH3' : 'Ammonia',
            '18540299' : 'Chromium(6+)',
            '1330207' : '1_3_Xylene',
            '208968' : 'Acenaphthylene',
            '53703'	: 'Naphtho_1_2_b_Phenanthrene',
            '75070'	: 'Acetaldehyde',
            'DIESEL-PM10' : 'DieselPM10',
            'PM10-PRI' :'PM10',
            'PMFINE' : 'PMFINE',
            '129000' : 'Pyrene',
            '205992' : 'Benzo_b_Fluoranthene',
            '207089' : 'Benzo_k_Fluoranthene',
            '7440382' : 'Arsenic',
            '86737'	: 'Fluorene',
            '50000'	: 'Formaldehyde',
            '83329' : 'Acenaphthene',
            'SO4' : 'Sulfate',
            '107028' : 'Acrolein',
            '206440' : 'Fluoranthene',
            '108883' : 'Toluene',
            'CH4' : 'Methane',
            '218019' : 'Chrysene',
            '7439976' : 'Mercury',
            'VOC' : 'VolatileOrganicCompound',
            '191242' : 'Benzo_Ghi_Perylene',
            'PM25-PRI' : 'PM2.5',
            'EC' : 'ElementalCarbon',
            'OC' : 'OrganicCarbon',
            '110543' : 'Hexane',
            'NOX' : 'OxidesOfNitrogen',
            'SO2' : 'SulfurDioxide',
            '120127' : 'Anthracene',
            '50328'	: 'Benzo_a_Pyrene',
            '540841' : '2_2_4_Trimethylpentane',
            '7440020' : 'Nickel',
            'CO' : 'CarbonMonoxide',
            '100425' : 'Styrene',
            '56553'	: 'Benzo_a_Anthracene',
            '7439965' : 'Manganese',
            '193395' : 'Indeno_1_2_3_c_d_Pyrene',
            'CO2' : 'CarbonDioxide',
            'NO3' : 'Nitrate',
            '71432'	: 'Benzene',
            '85018'	: 'Phenanthrene',
            '91203' : 'Naphthalene',
            'DIESEL-PM25' : 'DieselPM2.5',
            '106990' : 'Buta_1_3_Diene',
            '55673897' : '1_2_3_4_7_8_9_Heptachlorodibenzofuran',
            '60851345' : '2_3_4_6_7_8_Hexachlorodibenzofuran',
            '3268879' : '1_2_3_4_6_7_8_9_Octachlorodibenzo_p_Dioxin',
            '57117416'	:'1_2_3_7_8_Pentachlorodibenzofuran',
            '40321764'	:'1_2_3_7_8_Pentachlorodibenzo_p_Dioxin',
            '72918219'	:'1_2_3_7_8_9_Hexachlorodibenzofuran',
            '67562394'	:'1_2_3_4_6_7_8_Heptachlorodibenzofuran',
            '51207319'	:'2_3_7_8_Tetrachlorodibenzofuran',
            '57117449'	:'1_2_3_6_7_8_Hexachlorodibenzofuran',
            '19408743'	:'1_2_3_7_8_9_Hexachlorodibenzo_p_Dioxin',
            '35822469'	:'1_2_3_4_6_7_8_Heptachlorodibenzo_p_Dioxin',
            '57117314'	:'2_3_4_7_8_Pentachlorodibenzofuran',
            '39001020'	:'1_2_3_4_6_7_8_9_octachlorodibenzofuran',
            '70648269'	:'1_2_3_4_7_8_Hexachlorodibenzofuran',
            '57653857'	:'1_2_3_6_7_8_Hexachlorodibenzo_p_Dioxin',
            'DIESEL-PM2'	: 'DieselPM2.5',
            '39227286'	:'1_2_3_4_7_8_Hexachlorodibenzo_p_Dioxin',
            '1746016'	:'2_3_7_8_Tetrachlorodibenzo_p_Dioxin',
            'DIESEL-PM1'	: 'DieselPM10',
            '95476'	:'1_2_Xylene',
            '106423'	:'1_4_Xylene',
            '7440439'	:'Cadmium',
            '7440484'	:'Cobalt',
            '98828'	:'Cumene',
            '7439921':	'Lead',
            '7782505':	'Chlorine',
            '7782492':	'Selenium',
            '7723140':	'Phosphorus',
            '7440360':	'Antimony',
            '67561'	:'Methanol',
            '16065831'	:'Oxo_Oxochromiooxy_Chromium',
            '108383'	:'1_3_Xylene',
            '130498292'	:'PAH_Total',
            '1634044'	:'2_Methoxy_2_Methylpropane',
            '91576'	:'2_Methylnaphthalene'
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
            'HAP' : 'HazardousAirPollutants',
            'GHG' : 'GreenhouseGas',
            'CAP' : 'CriteriaAirPollutants'
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
            'Kootenai Tribe of Idaho':88183,
            'Nez Perce Tribe of Idaho':88182,
            'Shoshone-Bannock Tribes of the Fort Hall Reservation of Idaho':88180,
            'Coeur dAlene Tribe of the Coeur dAlene Reservation, Idaho':88181,
            'Northern Cheyenne Tribe of the Northern Cheyenne Indian Reservation, Montana':88207,
            'Morongo Band of Cahuilla Mission Indians of the Morongo Reservation, California':00000
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
    df = df.replace({
        'unit': {
            'TON': 'Ton',
            'LB': 'Pound'
        }
    })
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
            2205320080:	'SCC_MobileLightCommercialTruckE85',
            2202410080:	'SCC_MobileIntercityBusDiesel',
            2201110080:	'SCC_MobileMotorcycleGas',
            2202430080:	'SCC_MobileSchoolBusDiesel',
            2202420080:	'SCC_MobileTransitBusDiesel',
            2202540080:	'SCC_MobileMotorHomeDiesel',
            2202320080:	'SCC_MobileLightCommercialTruckDiesel',
            2202530080:	'SCC_MobileSingleUnitLonghaulTruckDiesel',
            2201520080:	'SCC_MobileSingleUnitShorthaulTruckGas',
            2201510080:	'SCC_MobileRefuseTruckGas',
            2202510080:	'SCC_MobileRefuseTruckDiesel',
            2205310080:	'SCC_MobilePassengerTruckE85',
            2205210080:	'SCC_MobilePassengerCarE85',
            2201310080:	'SCC_MobilePassengerTruckGas',
            2201430080:	'SCC_MobileSchoolBusGas',
            2201000062:	'SCC_MobileRefuelingGas',
            2201530080:	'SCC_MobileSingleUnitLonghaulTruckGas',
            2202310080:	'SCC_MobilePassengerTruckDiesel',
            2201210080:	'SCC_MobilePassengerCarGas',
            2201610080:	'SCC_MobileCombinationShorthaulTruckGas',
            2202210080:	'SCC_MobilePassengerCarDiesel',
            2202620080:	'SCC_MobileCombinationLonghaulTruckDiesel',
            2202520080:	'SCC_MobileSingleUnitShorthaulTruckDiesel',
            2202610080:	'SCC_MobileCombinationShorthaulTruckDiesel',
            2202000062:	'SCC_MobileRefuelingDiesel',
            2201540080:	'SCC_MobileMotorHomeGas',
            2201420080:	'SCC_MobileTransitBusGas',
            2205000062:	'SCC_MobileRefuelingEthanol',
            2201320080:	'SCC_MobileLightCommercialTruckGas',
            2203420080:	'SCC_MobileTransitBusCNG',
            2209310080:	'SCC_MobilePassengerTruckElectric',
            2209210080:	'SCC_MobilePassengerCarElectric'
        }
    })
    return df

def _regularize_columns(df: pd.DataFrame,file_path: str) -> pd.DataFrame:
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
        df.rename(columns = {'state_and_county_fips_code':'fips code', 
                        'data_set_short_name':'data set',
                        'pollutant_cd':'pollutant code',
                        'uom':'emissions uom',
                        'total_emissions':'total emissions'}, inplace = True)
        df = df.drop(columns=['tribal_name', 'st_usps_cd', 'county_name', 
                        'data_category_cd','description','emissions_type_code',
                        'aircraft_engine_type_cd','emissions_op_type_code'])
        df['pollutant type(s)'] = 'nan'
    elif '2017' in file_path:
        df = df.drop(columns=['epa region code','state','fips state code','county',
                        'emissions type code','aetc','reporting period',
                        'emissions operating type','sector',
                        'tribal name','pollutant desc','data category'])
    elif 'tribes' in file_path:
        df.rename(columns = {'tribal name':'fips code'}, inplace = True)
        df = df.drop(columns=['state','fips state code','data category',
                    'reporting period','emissions operating type',
                    'emissions type code','pollutant desc'])
        df = _replace_tribe_fips(df)
        df['pollutant type(s)'] = 'nan'
    else:
        df.rename(columns = {'state_and_county_fips_code':'fips code', 
                        'data_set':'data set',
                        'pollutant_cd':'pollutant code',
                        'uom':'emissions uom',
                        'total_emissions':'total emissions'}, inplace = True)
        df = df.drop(columns=['tribal_name','fips_state_code','st_usps_cd',
                    'county_name','data_category','emission_operating_type',
                    'pollutant_desc','emissions_type_code',
                    'emissions_operating_type'])
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
    print(file_path)
    df = pd.read_csv(file_path,header=0,low_memory=False)
    df = _regularize_columns(df,file_path)
    print(df)
    df['geo_Id'] = [f'{x:05}' for x in df['fips code']]
    df['geo_Id'] = 'geoId/' + df['geo_Id']
    df.rename(columns = {'emissions uom':'unit', 'total emissions':'observation'
                        ,'data set':'year'}, inplace = True)
    df['year'] = df['year'].str[:4]
    df = _replace_unit(df)
    df = _replace_scc(df)
    df = _replace_pollutant_code(df)
    df = _replace_pollutant_type(df)
    df['SV'] = ('Amount_Annual_Emissions_' + df['scc'].astype(str) + '_' +
            df['pollutant type(s)'].astype(str) +
            '_' + df['pollutant code'].astype(str))
    df['SV'] = df['SV'].str.replace('_nan','')
    df = df.drop(columns=['scc','pollutant code','pollutant type(s)','fips code'])
    
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
            source = '\nemissionSource: dcs:' + sv_property[3] + '_' + sv_property[4]
            if 'AirPollutants' in sv_property[5] or 'Greenhouse' in sv_property[5]:
                emission_type = '\nemissionType: dcs:' + sv_property[5]
                for i in sv_property[6:]:
                    pollutant = pollutant + i + '_'
            else:
                for i in sv_property[5:]:
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

        final_df = pd.DataFrame(columns=['geo_Id', 'year', 'SV', 'observation','unit'])
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
