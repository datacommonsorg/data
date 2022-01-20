import os
import sys
import tabula
import numpy as np
import pandas as pd

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../..'))  # for utils
from us_epa.util.superfund_helper import write_tmcf
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../util/'))  # for statvar_dcid_generator
from statvar_dcid_generator import get_statvar_dcid

_UNIT_MAP = {
    "Cond.": "dcs:MicroseimensPerCentimeter",
    "pH": "",
    "Hardness": "dcs:MilligramsCaCO3PerLitre",
    "temp": "dcs:Celsius",
    "D.O.": "dcs:MilligramsPerLitre",
    "Sulfate": "dcs:MilligramsPerLitre",
    "Iron": "dcs:MilligramsPerLitre",
    "Lead": "dcs:MilligramsPerLitre",
    "Zinc": "dcs:MilligramsPerLitre",
    "Cadmium": "dcs:MilligramsPerLitre"
}

_BASE_SV_MAP = {
"Cond.": {
   "populationType": "SuperfundSite",
   "waterSource": "GroundWater",
   "measuredProperty": "electricalConductivity",
},
"pH": {
   "populationType": "SuperfundSite",
   "waterSource": "GroundWater",
   "measuredProperty": "potentialOfHydrogen"
},
"Hardness": {
   "populationType": "SuperfundSite",
   "waterSource": "GroundWater",
   "measuredProperty": "waterHardness"
},
"temp": {
   "populationType": "SuperfundSite",
   "waterSource": "GroundWater",
   "measuredProperty": "temperature"
},
"D.O.": {
   "populationType": "SuperfundSite",
   "waterSource": "GroundWater",
   "solute": "Oxygen",
   "solvent": "Water",
   "measuredProperty": "concentration"

},
"Sulfate": {
   "populationType": "SuperfundSite",
   "contaminatedThing": "GroundWater",
   "contaminant": "Sulfate",
   "measuredProperty": "concentration"
},
"Iron": {
   "populationType": "SuperfundSite",
   "contaminatedThing": "GroundWater",
   "contaminant": "Iron",
   "measuredProperty": "concentration"
},
"Lead": {
   "populationType": "SuperfundSite",
   "contaminatedThing": "GroundWater",
   "contaminant": "Lead",
   "measuredProperty": "concentration"
},
"Zinc": {
   "populationType": "SuperfundSite",
   "contaminatedThing": "GroundWater",
   "contaminant": "Zinc",
   "measuredProperty": "concentration"
},
"Cadmium":  {
   "populationType": "SuperfundSite",
   "contaminatedThing": "GroundWater",
   "contaminant": "Cadmium",
   "measuredProperty": "concentration"
}
}

_WELL_MAP = {
    'Picher #d - MW': 'epaSuperfundSiteWellId/OKD980629844/Pitcher_5MW',
    'Picher #5 - MW': 'epaSuperfundSiteWellId/OKD980629844/Pitcher_5MW',
    'Picher #7 - MW': 'epaSuperfundSiteWellId/OKD980629844/Pitcher_7MW',
    'Quapaw#4': 'epaSuperfundSiteWellId/OKD980629844/Quapaw_4',
    'Commerce#S': 'epaSuperfundSiteWellId/OKD980629844/Commerce_5'
}

def get_table_data_from_pdf(download_url:str, page_str:str)->list:
    try:
        return tabula.read_pdf(download_url, stream=True, guess=True, pages=page_str)
    except:
        return []

def process_2020_report(skip_count:int=5)->list:
    download_url = "https://semspub.epa.gov/work/06/100021610.pdf"
    page_range = '83-86'
    df_list =  get_table_data_from_pdf(download_url, page_range)
    columns = ['observationAbout', 'observationDate', 'contaminantType', 'Cond.', 'D.O.', 'Hardness', 'temp', 'pH', 'Iron', 'Lead', 'Zinc', 'Cadmium', 'Sulfate']
    cleaned_dataset = [pd.DataFrame(columns=columns)]

    for idx in range(len(df_list)):
        df = df_list[idx].iloc[skip_count:] #skip the first k-rows
        extracted_well_name = df.iloc[0][0]
        df = df[1:] #skip the well name row
        if idx == 3:
            df['Unnamed: 0'] = df['Unnamed: 0'].replace({"/ ": "/", " /": "/", r'/ [^0-9]+': r'/[^0-9]+', 'Tota ls': 'Totals', 'Di sso lved': 'Dissolved', '200A': '2004', '19.E': '19.8'}, regex=True)
            df['Unnamed: 0'] = df['Unnamed: 0'].replace({'Dissolved': 'NaN Dissolved'})
            df['Zinc'] = df['Zinc'].replace({'O.Ql': '0.01'})
            df[['observationDate', 'contaminantType']] = df['Unnamed: 0'].str.split(n=1, expand=True)
            df['observationDate'] = pd.to_datetime(df['observationDate']).ffill()
            df['Temo. DH'] = df['Temo. DH'].replace({'19.E': '19.8'}, regex=True)
            df[['temp', 'pH']] = df['Temo. DH'].str.split(n=1, expand=True)
            df['Hardness Cadmium'].replace(to_replace=r'^<', value='- <', regex=True, inplace=True) #replace the entires with start with '<' since the after splitting the column associated with the data is wrong. 
            df[['Hardness', 'Cadmium']] = df['Hardness Cadmium'].str.split(n=1, expand=True)
            df.drop(columns=['Unnamed: 0', 'Unnamed: 1', 'Temo. DH', 'Hardness Cadmium'], inplace=True)
        if idx == 2:
            df['Unnamed: 0'] = df['Unnamed: 0'].replace({"/ ": "/", " /": "/", r'/ [^0-9]+': r'/[^0-9]+', 'To ta ls': 'Totals', 'Total s': 'Totals', 'Tota ls': 'Totals', 'Tot als':'Totals', 'Di ssolved': 'Dissolved', 'Di sso lved': 'Dissolved', '200A': '2004', '19.E': '19.8'}, regex=True)
            df['Unnamed: 0'] = df['Unnamed: 0'].replace({'Dissolved': 'NaN Dissolved'})
            df[['observationDate', 'contaminantType']] = df['Unnamed: 0'].str.split(n=1, expand=True)
            df['observationDate'] = pd.to_datetime(df['observationDate']).ffill()
            df[['temp', 'pH']] = df['Temp. pH'].str.split(n=1, expand=True)
            df.drop(columns=['Unnamed: 0', 'Unnamed: 1', 'Temp. pH'], inplace=True)
            df.rename(columns={'Su lfate': 'Sulfate'}, inplace=True)
        if idx == 1:
            df = df[~df['Unnamed: 0'].str.contains('Averages')]
            df['Unnamed: 0'] = df['Unnamed: 0'].replace({"/ ": "/", " /": "/", r'/ [^0-9]+': r'/[^0-9]+', 'To tals': 'Totals', 'To tal s': 'Totals', 'Total s': 'Totals', 'Tota ls': 'Totals', 'To ta ls': 'Totals','Disso lved': 'Dissolved', 'Di ssolved': 'Dissolved', 'Di sso lved': 'Dissolved', '200A': '2004', '19.E': '19.8'}, regex=True)
            df['Unnamed: 0'] = df['Unnamed: 0'].replace({'Dissolved': 'NaN Dissolved'})
            df[['observationDate', 'contaminantType']] = df['Unnamed: 0'].str.split(n=1, expand=True)
            df['observationDate'] = pd.to_datetime(df['observationDate']).ffill()
            df[['temp', 'pH']] = df['Temp. pH'].str.split(n=1, expand=True)
            df.drop(columns=['Unnamed: 0', 'Unnamed: 1', 'Temp. pH'], inplace=True)
            df.rename(columns={"0 .0 .": "D.O."}, inplace=True)
        if idx == 0:
            df['Unnamed: 0'] = df['Unnamed: 0'].replace({"/ ": "/", " /": "/", r'/ [^0-9]+': r'/[^0-9]+', 'To tals': 'Totals', 'To tal s': 'Totals', 'Total s': 'Totals', 'Tota ls': 'Totals', 'Disso lved': 'Dissolved', 'Di ssolved': 'Dissolved', 'Di sso lved': 'Dissolved', '200A': '2004', '19.E': '19.8'}, regex=True)
            df['Unnamed: 0'] = df['Unnamed: 0'].replace({'Dissolved': 'NaN Dissolved'})
            df[['observationDate', 'contaminantType']] = df['Unnamed: 0'].str.split(n=1, expand=True)
            df['observationDate'] = pd.to_datetime(df['observationDate']).ffill()
            df[['temp', 'pH']] = df['Temp. pH'].str.split(n=1, expand=True)
            df.drop(columns=['Unnamed: 0', 'Unnamed: 1', 'Temp. pH'], inplace=True)
        df['observationAbout'] = _WELL_MAP[extracted_well_name]
        df = df[columns]
        cleaned_dataset.append(df)
    
    cleaned_dataset = pd.concat(cleaned_dataset, ignore_index=True)
    cleaned_dataset.to_csv("tar_creek_2020.csv", index=False)
    return cleaned_dataset

def make_stat_var_dict(contaminant_type:list, column_list:list):
    ignore_columns = ['observationAbout', 'observationDate', 'contaminantType']
    sv_dict = {}
    sv_column_map = {}

    for contaminant_state in contaminant_type:
        for column in column_list:
            if column not in ignore_columns:
                base_sv = {}

                # add pvs
                base_sv.update(_BASE_SV_MAP[column])
               
                if contaminant_state == 'Dissolved':
                    base_sv['contaminantStatus'] = 'Dissolved'

                key =  'Node: dcid:' + get_statvar_dcid(base_sv)
                base_sv['typeOf'] = 'StatisticalVariable'
                base_sv['statType'] = 'measuredValue'

                if key not in sv_dict.keys():
                    sv_dict[key] = base_sv
                    sv_column_map[column + '_' + contaminant_state] = get_statvar_dcid(base_sv)
    return sv_dict, sv_column_map

def write_sv_mcf(output_path, sv_dict):
    f = open(output_path, 'w')
    for k, pvs in sv_dict.items():
        fstr = k + "\n"
        for p, v in pvs.items():
            if v.startswith('dcs:'):
                fstr += f"{p}: {v}\n"
            else:
                fstr += f"{p}: dcs:{v}\n"
        fstr += "\n"
        f.write(fstr)
    f.close()

_CLEAN_CSV_FRAMES = []



def clean_dataset(row, column_list, sv_map):
    clean_csv = pd.DataFrame(columns=['observationAbout', 'observationDate', 'variableMeasured', 'value', 'units'])

    ignore_list = ['-', ' - ', 'NaN', 'n.a.', np.nan]
    ignore_columns = ['observationAbout', 'observationDate', 'contaminantType']

    for column in column_list:
        if column not in ignore_columns:
            if row[column] not in ignore_list:
                sv_key = column + '_' +row['contaminantType']

                ## add data to clean csv
                clean_csv = clean_csv.append({
                    'observationAbout': row['observationAbout'],
                    'observationDate': row['observationDate'],
                    'variableMeasured': 'dcid:' + sv_map[sv_key],
                    'value': row[column],
                    'units': _UNIT_MAP[column]
                }, ignore_index=True)

    _CLEAN_CSV_FRAMES.append(clean_csv)

_TEMPLATE_MCF = """
Node: E:EPASuperfundTarCreek->E0
typeOf: dcs:StatVarObservation
observationAbout: C:EPASuperfundTarCreek->observationAbout
observationDate: C:EPASuperfundTarCreek->observationDate
variableMeasured: C:EPASuperfundTarCreek->variableMeasured
value: C:EPASuperfundTarCreek->value
unit: C:EPASuperfundTarCreek->units
"""

df = pd.read_csv("tar_creek_2020.csv")
df.replace(to_replace=r'^<', value='', regex=True, inplace=True) #remove < from SVObs values
contaminant_list = df['contaminantType'].unique().tolist()
sv_dict, sv_column_map = make_stat_var_dict(contaminant_list, df.columns.tolist())
write_sv_mcf('superfund_sites_tarcreek.mcf', sv_dict)

print(sv_column_map)
df.apply(clean_dataset,args=(df.columns.tolist(), sv_column_map,),axis=1)

clean_csv = pd.concat(_CLEAN_CSV_FRAMES, ignore_index=True)
write_sv_mcf("./superfund_sites_tarcreek.mcf", sv_dict)
write_tmcf(_TEMPLATE_MCF, "./superfund_sites_tarcreek.tmcf")
clean_csv.to_csv("./superfund_sites_tarcreek.csv", index=False)
