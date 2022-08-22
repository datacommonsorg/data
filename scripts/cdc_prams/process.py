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
The Python script loads the datasets, 
cleans them and generates the cleaned CSV, MCF and TMCF file.
"""
import os
import sys
import re
from copy import deepcopy
import pandas as pd
import numpy as np
from absl import app, flags
# from util.alpha2_to_dcid import COUNTRY_MAP
import tabula as tb

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, _CODEDIR)

sys.path.insert(1, os.path.join(_CODEDIR, '../../util/'))
from statvar_dcid_generator import get_statvar_dcid
from state_division_to_dcid import _PLACE_MAP

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))

from statvar import statvar_col
# pylint: enable=wrong-import-pos

from constants import (_MCF_TEMPLATE, _TMCF_TEMPLATE, DEFAULT_SV_PROP,_PROP,
                        _TIME,_INSURANCE,_PROP4,_PV_PROP,_YEAR)

_FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

# for index df:

def prams(input_url: list, statvar_col:dict) -> pd.DataFrame:
    final_df = pd.DataFrame()
    df_all = pd.DataFrame([])
    sv_names = []
    for file in input_url:
        flag = "States"
        if "All-Sites" in file:
            flag = "National"
        data = tb.read_pdf(file, pages = 'all')
        df = pd.concat(data)
        file_name = os.path.basename(file)
        df['Geo'] = file_name.replace('-PRAMS-MCH-Indicators-508.pdf','').\
        replace('-',' ').replace('District Columbia','District of Columbia')\
        .replace('New York City','geoId/3651000').replace('All Sites','country/USA')
        print(file_name.replace('-PRAMS-MCH-Indicators-508.pdf',''))
        df.reset_index(drop=True, inplace=True)
        if flag == "States":
            df = df.drop(['Unnamed: 0','Unnamed: 1','Unnamed: 2','Unnamed: 3','Unnamed: 4'], 1)
            df.columns = ['statVar', '2016_CI', '2017_sampleSize', '2017_CI', 
            '2018_sampleSize', '2018_CI', '2019_sampleSize', '2019_CI', 
            '2020_sampleSize', '2020_CI', 'Overall_2020_CI','Geo']
        elif flag=="National":
            # print(df.columns)
            df.columns = ['statVar', '2016_CI', '2017_sampleSize','2017_Nan', 
            '2017_CI', '2018_sampleSize','2018_Nan', '2018_CI',
            '2019_sampleSize','2019_Nan', '2019_CI', '2020_sampleSize',
            '2020_Nan', '2020_CI','Geo']
            df.drop(['2017_Nan','2018_Nan','2019_Nan','2020_Nan'], 1, inplace=True)
        df.insert(1,'2016_sampleSize', np.NaN)   
        final_df = df.copy()
        final_df['statVar'] = final_df['statVar'].str.replace('• ', '')

        multiline = ['Multivitamin use ≥4 times a week during the month before', 
        'Heavy drinking (≥8 drinks a week) during the 3 months before', 
        'Experienced IPV during pregnancy by a husband or partner'
        ]
        df1 = final_df.copy()
        for line in multiline:
            for i in range(len(df1)):
                if df1.loc[i, 'statVar'] == line:
                    df1.loc[i, 'statVar'] = '{}{}{}'.format(df1.loc[i, 'statVar'], ' ', df1.loc[i+2, 'statVar'])
                    df1.loc[i, '2016_sampleSize'] = df1.loc[i+1, 'statVar']
                    df1.loc[i, '2016_CI'] = df1.loc[i+1, '2016_CI']
                    df1.loc[i, '2017_sampleSize'] = df1.loc[i+1, '2017_sampleSize']
                    df1.loc[i, '2017_CI'] = df1.loc[i+1, '2017_CI']
                    df1.loc[i, '2018_sampleSize'] = df1.loc[i+1, '2018_sampleSize']
                    df1.loc[i, '2018_CI'] = df1.loc[i+1, '2018_CI']
                    df1.loc[i, '2019_sampleSize'] = df1.loc[i+1, '2019_sampleSize']
                    df1.loc[i, '2019_CI'] = df1.loc[i+1, '2019_CI']
                    df1.loc[i, '2020_sampleSize'] = df1.loc[i+1, '2020_sampleSize']
                    df1.loc[i, '2020_CI'] = df1.loc[i+1, '2020_CI']
                    if flag=="States":
                        df1.loc[i, 'Overall_2020_CI'] = df1.loc[i+1, 'Overall_2020_CI']
                    df1.drop([i+1, i+2], inplace=True)
                    df1.reset_index(drop=True, inplace=True)
                    break

        for i in range(len(df1)):
            if df1.loc[i, 'statVar'][-4:].strip().strip('§').isnumeric():
                if flag=="States":
                    df1.loc[i, '2016_sampleSize'] = df1.loc[i, 'statVar'][-4:].strip().strip('§')
                elif flag=="National":
                    df1.loc[i, '2016_sampleSize'] = df1.loc[i, 'statVar'][-5:].strip().strip('§')
                l1 = len(df1.loc[i, 'statVar'])
                l2 = len(df1.loc[i, '2016_sampleSize'])
                df1.loc[i, 'statVar'] = df1.loc[i, 'statVar'][:l1-l2].strip()
            if re.match(r'^\d{1}\.\d{1} \(\d{1}.\d{1}-\d{1}\.\d{1}\)', df1.loc[i, 'statVar']):
                df1.loc[i, 'Overall_2020_CI'] = df1.loc[i, 'statVar'][:12]
                df1.loc[i, 'statVar'] = df1.loc[i, 'statVar'][13:]

        for i in range(len(df1)):
            if df1.loc[i, 'statVar'] == 'Experienced IPV during the 12 months before pregnancy by a':
                if flag=="National":
                    df1.loc[i, 'statVar'] = df1.loc[i, 'statVar'].replace('a2.5 ','a')
                    df1.loc[i+1, '2020_CI'] = 2.5
                df1.loc[i+1, 'statVar'] = df1.loc[i, 'statVar'] + df1.loc[i+1, 'statVar']
                df1.drop([i], inplace=True)
                df1.reset_index(drop=True, inplace=True)
                break

        if flag=="National":
            for i in range(len(df1)):
                if df1.loc[i, 'statVar'] == 'Teeth cleaned during pregnancy by a dentist or dental':
                    df1.loc[i+1, 'statVar'] = df1.loc[i+1, 'statVar'].replace('40.0 ','')
                    df1.loc[i+1, '2020_CI'] = 40.0
                    df1.loc[i+1, 'statVar'] = df1.loc[i, 'statVar'] + df1.loc[i+1, 'statVar']
                    df1.drop([i], inplace=True)
                    df1.reset_index(drop=True, inplace=True)
                    break
        df2 = df1.copy()
        main_header = ['Nutrition',
        'Pre-pregnancy Weight',
        'Substance Use',
        'Intimate Partner Violence (IPV)¥',
        'Depression',
        'Health Care Services',
        'Pregnancy Intention',
        'Postpartum†† Family Planning',
        'Oral Health',
        'Health Insurance Status One Month Before Pregnancy¶',
        'Health Insurance Status One Month Before Pregnancy¶¶',
        'Health Insurance Status for Prenatal Care¶¶',
        'Health Insurance Status Postpartum††¶¶',
        'Infant Sleep Practices',
        'Breastfeeding Practices']

        sub_header = ['Any cigarette smoking',
        'Any e-cigarette use',
        'Highly effective contraceptive methods']

        df2['main_header'] = np.where(
        df2['statVar'].isin(main_header),
        df2['statVar'], pd.NA)
        df2['main_header_delete_flag'] = df2['main_header']
        df2['main_header_delete_flag'] = df2['main_header_delete_flag'].fillna("")
        df2['main_header'] = df2['main_header'].fillna(method='ffill')

        df2['sub_header'] = np.where(
                df2['statVar'].isin(sub_header),
                df2['statVar'], pd.NA)
        df2['sub_header_delete_flag'] = df2['sub_header']
        df2['sub_header_delete_flag'] = df2['sub_header_delete_flag'].fillna("")
        df2['sub_header'] = df2['sub_header'].fillna(method='ffill', limit=2)
        index = df2[df2['statVar']=='Postpartum'].index.values[0]
        df2.loc[index,'sub_header'] = "Any cigarette smoking"
        df2['sub_header'] = df2['sub_header'].fillna("")

        df2['newStatVar'] = df2['main_header']+"_"+df2['sub_header']+"_"+df2['statVar']
        df2 = df2.loc[(df2['main_header_delete_flag']=='')]
        df2 = df2.loc[(df2['sub_header_delete_flag']=='')]
        df2 = df2.drop(columns=['statVar','main_header_delete_flag','sub_header'
        ,'main_header','sub_header_delete_flag'])
        df2['SV'] = df2['newStatVar']
        df2 = df2.replace({'SV': statvar_col})
        df2.to_csv("SV1.csv")
        df2 = df2.replace({'Geo': _PLACE_MAP})
        df2 = df2.reset_index(drop=True)

        if flag=="States":
            split_col = ['2016_CI','2017_CI','2018_CI','2019_CI','2020_CI']
            for i in split_col:
                df2[i] = df2[i].fillna(pd.NA)
                temp_df = df2[i].str.split(r"\s+|-", expand=True)
                siz = temp_df.shape[1]
                if siz==1:
                    temp_df = temp_df.rename(columns={temp_df.columns[0]: i+'_PERCENT'})
                    temp_df[i+'_LOWER'] = ""
                    temp_df[i+'_UPPER'] = ""
                elif siz==3:
                    temp_df = temp_df.rename(columns={temp_df.columns[0]: i+'_PERCENT',temp_df.columns[1]: i+'_LOWER',temp_df.columns[2]: i+'_UPPER'})
                    temp_df[i+'_LOWER'] = temp_df[i+'_LOWER'].str.replace('(','')
                    temp_df[i+'_UPPER'] = temp_df[i+'_UPPER'].str.replace(')','')
                df2 = pd.concat([df2,temp_df],axis=1)
            df2 = df2.drop(columns=['newStatVar','2016_CI','2017_CI','2018_CI','2019_CI','2020_CI','Overall_2020_CI'])
       
        if flag=="National":
            df2 = df2[['Geo','SV', '2016_sampleSize','2016_CI',
            '2017_sampleSize','2017_CI','2018_sampleSize','2018_CI',
            '2019_sampleSize','2019_CI','2020_sampleSize','2020_CI']]
        elif flag=="States":   
            df2 = df2[['Geo', 'SV','2016_sampleSize', '2017_sampleSize', '2018_sampleSize',
        '2019_sampleSize', '2020_sampleSize',  '2016_CI_PERCENT',
        '2016_CI_LOWER', '2016_CI_UPPER', '2017_CI_PERCENT', '2017_CI_LOWER',
        '2017_CI_UPPER', '2018_CI_PERCENT', '2018_CI_LOWER', '2018_CI_UPPER',
        '2019_CI_PERCENT', '2019_CI_LOWER', '2019_CI_UPPER', '2020_CI_PERCENT',
        '2020_CI_LOWER', '2020_CI_UPPER']]
            df2['2018_CI_UPPER'] = df2['2018_CI_UPPER'].replace('.','0.0')
            df2['2018_CI_LOWER'] = df2['2018_CI_LOWER'].replace('.','0.0')
        
        sv_melt = ['sample_size','percent_sv','lower_level','upper_level']

        for i1 in sv_melt:
            temp_df = df2.copy()
            if i1=="sample_size":
                temp_df['SV'] = 'SampleSize_Count'+df2['SV']
                if flag=="National":
                    temp_df = temp_df.drop(columns=['2016_CI','2017_CI','2018_CI','2019_CI','2020_CI'])
                elif flag=="States":
                    temp_df = temp_df.drop(columns=['2016_CI_PERCENT','2017_CI_PERCENT',
                    '2019_CI_PERCENT','2020_CI_PERCENT',
                    '2018_CI_PERCENT','2016_CI_LOWER','2016_CI_UPPER','2017_CI_LOWER',
                    '2017_CI_UPPER','2018_CI_LOWER','2018_CI_UPPER','2019_CI_LOWER',
                    '2019_CI_UPPER','2020_CI_LOWER','2020_CI_UPPER'])
                temp_df = temp_df.melt(id_vars=['Geo','SV'], var_name='Year'\
                        ,value_name='Observation')
            elif i1=="percent_sv":
                temp_df['SV'] = 'Percent'+df2['SV']
                if flag=="National":
                    temp_df = temp_df.drop(columns=['2016_sampleSize',
                    '2017_sampleSize','2018_sampleSize','2019_sampleSize',
                    '2020_sampleSize'])
                elif flag=="States":
                    temp_df = temp_df.drop(columns=['2016_sampleSize','2017_sampleSize',
                    '2018_sampleSize','2019_sampleSize','2020_sampleSize',
                    '2016_CI_LOWER','2016_CI_UPPER','2017_CI_LOWER','2017_CI_UPPER',
                    '2018_CI_LOWER','2018_CI_UPPER','2019_CI_LOWER','2019_CI_UPPER',
                    '2020_CI_LOWER','2020_CI_UPPER'])
                temp_df = temp_df.melt(id_vars=['Geo','SV'], var_name='Year'\
                        ,value_name='Observation')
            elif i1=="lower_level" and flag=="States":
                temp_df['SV'] = 'ConfidenceIntervalLowerLimit_Count'+df2['SV']
                temp_df = temp_df.drop(columns=['2016_sampleSize','2017_sampleSize',
                '2018_sampleSize','2019_sampleSize','2020_sampleSize',
                '2016_CI_UPPER','2017_CI_UPPER','2018_CI_UPPER','2019_CI_UPPER',
                '2020_CI_UPPER','2016_CI_PERCENT',
                '2017_CI_PERCENT','2019_CI_PERCENT','2020_CI_PERCENT',
                '2018_CI_PERCENT'])
                temp_df = temp_df.melt(id_vars=['Geo','SV'], var_name='Year'\
                        ,value_name='Observation')
            elif i1=="upper_level" and flag=="States":
                temp_df['SV'] = 'ConfidenceIntervalUpperLimit_Count'+df2['SV']
                temp_df = temp_df.drop(columns=['2016_sampleSize','2017_sampleSize',
                '2018_sampleSize','2019_sampleSize','2020_sampleSize',
                '2016_CI_LOWER','2017_CI_LOWER','2018_CI_LOWER','2019_CI_LOWER',
                '2020_CI_LOWER','2016_CI_PERCENT',
                '2017_CI_PERCENT','2019_CI_PERCENT','2020_CI_PERCENT',
                '2018_CI_PERCENT'])
                temp_df = temp_df.melt(id_vars=['Geo','SV'], var_name='Year'\
                        ,value_name='Observation')
            else:
                continue
            
            df_all = pd.concat([df_all,temp_df],axis=0)
        # Replacing Year column with the correct Values.
        for old,new in _YEAR.items():
            df_all['Year'] = df_all['Year'].replace(old,new)
        df_all.reset_index(drop=True, inplace=True)
        df_all = df_all.sort_values(by=['Geo'], kind="stable")
    return df_all    

class US_Prams:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    def __init__(self, input_files: list, csv_file_path: str, 
    mcf_file_path: str,tmcf_file_path: str) -> None:
        self.input_files = input_files
        self.cleaned_csv_file_path = csv_file_path
        self.mcf_file_path = mcf_file_path
        self.tmcf_file_path = tmcf_file_path

    def _generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.
        Arguments:
            None
        Returns:
            None
        """
        # Writing Genereated TMCF to local path.
        with open(self.tmcf_file_path, 'w+', encoding="UTF-8") as f_out:
            f_out.write(_TMCF_TEMPLATE.rstrip('\n'))

    def _generate_mcf(self, sv_names: list, mcf_file_path: str)-> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Args:
            sv_names (list): List of Statistical Variables
            mcf_file_path (str): Output MCF File Path
        """
        mcf_nodes = []
        dcid_nodes = {}
        for sv in sv_names:
            pvs = []
            dcid = sv
            sv_prop = [prop.strip() for prop in sv.split(" ")]
            sv_pvs = deepcopy(DEFAULT_SV_PROP)

            for prop in sv_prop:
                prop1 = deepcopy(prop)
                prop3 = deepcopy(prop)
                prop2 = deepcopy(prop)
                prop4 = deepcopy(prop)
                prop5 = deepcopy(prop)
                for old,new in _PROP.items():
                    prop1 = prop1.replace(old,new)
                for old,new in _TIME.items():
                    prop3 = prop3.replace(old,new)
                for old,new in _INSURANCE.items():
                    prop2 = prop2.replace(old,new)
                for old,new in _PROP4.items():
                    prop4 = prop4.replace(old,new)
                for old,new in _PV_PROP.items():
                    prop5 = prop5.replace(old,new)

                if "SampleSize" in prop :
                    sv_pvs["measuredProperty"] = f"dcs:count"
                    pvs.append(f"measuredProperty: dcs:count")
                    pvs.append(f"statType: dcs:sampleSize")
                    sv_pvs["statType"] = f"dcs:sampleSize"

                if "Percent" in prop:
                    sv_pvs["measuredProperty"] = f"dcs:percent"
                    pvs.append(f"measuredProperty: dcs:percent")
                    pvs.append(f"statType: dcs:measuredValue")
                    sv_pvs["statType"] = f"dcs:measuredValue"

                if "ConfidenceIntervalLowerLimit" in prop:
                    sv_pvs["measuredProperty"] = f"dcs:percent"
                    pvs.append(f"measuredProperty: dcs:percent")
                    pvs.append(f"statType: dcs:confidenceIntervalLowerLimit")
                    sv_pvs["statType"] = f"dcs:confidenceIntervalLowerLimit"

                if "ConfidenceIntervalUpperLimit" in prop:
                    sv_pvs["measuredProperty"] = f"dcs:percent"
                    pvs.append(f"measuredProperty: dcs:percent")
                    pvs.append(f"statType: dcs:confidenceIntervalUpperLimit")
                    sv_pvs["statType"] = f"dcs:confidenceIntervalUpperLimit"

                if "MultivitaminUseMoreThan4TimesAWeek" in prop:
                    prop = prop[0].lower() + prop[1:]
                    pvs.append(f"mothersHealthPrevention: dcs:{prop1}")
                    sv_pvs["mothersHealthPrevention"] = f"dcs:{prop1}"
                    sv_pvs["healthPreventionActionFrequency"] = f"dcs:{prop3}"
                    pvs.append(f"healthPreventionActionFrequency: dcs:{prop3}")

                if "Underweight" in prop or "Overweight" in prop or\
                    "Obese" in prop:
                    pvs.append(f"mothersHealthBehavior: dcs:{prop1}")
                    sv_pvs["mothersHealthBehavior"] = f"dcs:{prop1}"

                if "HealthCareVisit12MonthsBeforePregnancy"in prop or\
                        "PrenatalCareInFirstTrimester" in prop or\
                        "FluShot12MonthsBeforePregnancy"in prop or\
                        "MaternalCheckupPostpartum" in prop or\
                        "TeethCleanedByDentistOrHygienist" in prop:
                    prop = prop[0].lower() + prop[1:]
                    pvs.append(f"mothersHealthPrevention: dcs:{prop1}")
                    sv_pvs["mothersHealthPrevention"] = f"dcs:{prop1}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"dcs:{prop3}"
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{prop3}")
                
                elif "CigaretteSmoking3MonthsBeforePregnancy" in prop or\
                    "CigaretteSmokingLast3MonthsOfPregnancy"in prop or \
                    "CigaretteSmokingPostpartum" in prop or\
                    "ECigaretteSmoking3MonthsBeforePregnancy" in prop or\
                    "ECigaretteSmokingLast3MonthsOfPregnancy" in prop:
                    pvs.append(f"tobaccoUsageType: dcs:{prop4}")
                    sv_pvs["tobaccoUsageType"] = f"dcs:{prop4}"
                    pvs.append(f"mothersHealthBehavior: dcs:{prop1}")
                    sv_pvs["mothersHealthBehavior"] = f"dcs:{prop1}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"{prop3}"
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{prop3}")

                elif "HookahInLast2Years" in prop or "HeavyDrinking3MonthsBeforePregnancy" in prop:
                    pvs.append(f"mothersHealthBehavior: dcs:{prop1}")
                    sv_pvs["mothersHealthBehavior"] = f"dcs:{prop1}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"{prop3}"
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{prop3}")

                elif "IntimatePartnerViolenceByCurrentOrExPartnerOrCurrentOrExHusband" in prop:
                    pvs.append(f"intimatePartnerViolence: dcs:{prop1}")
                    sv_pvs["intimatePartnerViolence"] = f"dcs:{prop1}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"{prop3}"
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{prop3}")

                elif "MistimedPregnancy" in prop or "UnwantedPregnancy" in prop or\
                    "UnsureIfWantedPregnancy" in prop or "IntendedPregnancy" in prop :
                    pvs.append(f"pregnancyIntention: dcs:{prop4}")
                    sv_pvs["pregnancyIntention"] = f"dcs:{prop4}"

                elif "AnyPostpartumFamilyPlanning"in prop or\
                    "MaleOrFemaleSterilization"in prop or\
                    "LongActingReversibleContraceptiveMethods" in prop or\
                    "ModeratelyEffectiveContraceptiveMethods"in prop or\
                    "LeastEffectiveContraceptiveMethods"in prop:
                    pvs.append(f"postpartumFamilyPlanning: dcs:{prop4}")
                    sv_pvs["postpartumFamilyPlanning"] = f"dcs:{prop4}"

                elif "CDC_SelfReportedDepression3MonthsBeforePregnancy" in prop or\
                    "CDC_SelfReportedDepressionDuringPregnancy" in prop or\
                    "CDC_SelfReportedDepressionPostpartum" in prop:
                    pvs.append(f"mothersHealthCondition: dcs:{prop1}")
                    sv_pvs["mothersHealthCondition"] = f"dcs:{prop1}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"dcs:{prop3}"
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{prop3}")

                elif "healthInsuranceStatusOneMonthBeforePregnancyprivateinsurance"in prop or\
                    "healthInsuranceStatusOneMonthBeforePregnancyMedicaid" in prop or\
                    "healthInsuranceStatusOneMonthBeforePregnancyNoInsurance" in prop :
                    pvs.append(f"healthInsuranceStatusOneMonthBeforePregnancy: dcs:{prop1}")
                    sv_pvs["healthInsuranceStatusOneMonthBeforePregnancy"] = f"dcs:{prop1}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"dcs:{prop3}"
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{prop3}")

                elif "healthInsuranceStatusForPrenatalCareprivateinsurance"in prop or\
                    "healthInsuranceStatusForPrenatalCareMedicaid" in prop or\
                        "healthInsuranceStatusForPrenatalCareNoInsurance" in prop:
                    pvs.append(f"healthInsuranceStatusForPrenatalCare: dcs:{prop1}")
                    sv_pvs["healthInsuranceStatusForPrenatalCare"] = f"dcs:{prop1}"

                elif "healthInsuranceStatusPostpartumprivateinsurance" in prop or\
                    "healthInsuranceStatusPostpartumMedicaid" in prop or\
                        "healthInsuranceStatusPostpartumNoInsurance" in prop:
                    pvs.append(f"healthInsuranceStatusPostpartum: dcs:{prop2}")
                    sv_pvs["healthInsuranceStatusPostpartum"] = f"dcs:{prop2}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"dcs:{prop3}"
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{prop3}")

                elif "BabyMostOftenLaidOnBackToSleep" in prop :
                    pvs.append(f"infantSleepPractice: dcs:{prop4}")
                    sv_pvs["infantSleepPractice"] = f"dcs:{prop4}"

                elif "EverBreastfed"in prop or "AnyBreastfeedingAt8Weeks" in prop:
                    pvs.append(f"breastFeedingPractice: dcs:{prop4}")
                    sv_pvs["breastFeedingPractice"] = f"dcs:{prop4}"
                
            resolved_dcid = get_statvar_dcid(sv_pvs)
            dcid_nodes[dcid] = resolved_dcid
            mcf_nodes.append(
                _MCF_TEMPLATE.format(dcid=resolved_dcid, xtra_pvs='\n'.join(pvs)))
        mcf = '\n'.join(mcf_nodes)
        # Writing Genereated MCF to local path.
        with open(mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(mcf.rstrip('\n'))
        return dcid_nodes

    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.
        Arguments: None
        Returns: None
        """
        sv_names = []
        df_all = prams(self.input_files,statvar_col)
        sv_names += df_all["SV"].to_list()
        sv_names = list(set(sv_names))
        # Creating Output Directory
        output_path = os.path.dirname(self.cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_names.sort()
        updated_sv = self._generate_mcf(sv_names, self.mcf_file_path)
        df_all["SV"] = df_all["SV"].map(updated_sv)    
        self._generate_tmcf()
        df_all.to_csv(self.cleaned_csv_file_path, index=False)

def main(_):
    input_path = _FLAGS.input_path
    # input_path = "/Users/chharish/us_prams/data/scripts/cdc_prams/test_data/datasets"
    ip_files = os.listdir(input_path)
    ip_files = [os.path.join(input_path, file) for file in ip_files]
    # Defining Output Files
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output")
    csv_name = "PRAMS.csv"
    mcf_name = "PRAMS.mcf"
    tmcf_name = "PRAMS.tmcf"
    tmcf_path = os.path.join(data_file_path, tmcf_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    loader = US_Prams(ip_files, cleaned_csv_path,mcf_path,tmcf_path)
    loader.process()

if __name__ == "__main__":
    app.run(main)
