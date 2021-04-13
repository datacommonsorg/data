# -*- coding: utf-8 -*-

import sys
sys.path.append("..")

import os
from base.data_cleaner import NHMDataLoaderBase
from base.readme_generator import ReadMeGen


# Mapping dictionary for data columns and StatVars
cols_to_nodes = {
    'State': 'State',
    'isoCode': 'isoCode',
    'Date': 'Date',
    'Estimated Number of Annual Pregnancies #': 'Count_PregnancyEvent',
    'Total number of pregnant women Registered for ANC': 'Count_PregnantWomen_RegisteredForAntenatalCare',
    'Number of Pregnant women registered within first trimester': 'Count_PregnantWomen_RegisteredForAntenatalCareWithinFirstTrimester',
    'Total reported deliveries': 'Count_ChildDeliveryEvent',
    'Institutional deliveries (Public Insts.+Pvt. Insts.)': 'Count_ChildDeliveryEvent_InAnInstitution',
    'Deliveries Conducted at Public Institutions': 'Count_ChildDeliveryEvent_InPublicInstitution',
    'Number of Home deliveries': 'Count_ChildDeliveryEvent_AtHome',
    'Number of home deliveries attended by SBA trained (Doctor/Nurse/ANM)': 'Count_ChildDeliveryEvent_AtHome_WithStandByAssist',
    '% Safe deliveries to Total Reported Deliveries': 'Count_DeliveryEvent_Safe_AsFractionOf_Count_DeliveryEvent'
    }


if __name__ == '__main__':
    dataset_name = "NHM_MaternalHealth"
    
    # Preprocess files; Generate CSV; Generate TMCF file
    loader = NHMDataLoaderBase(data_folder='../data/', dataset_name=dataset_name, 
                              cols_dict=cols_to_nodes)   
    loader.generate_csv()
    loader.create_tmcf()
    
    # Write README file
    readme_gen = ReadMeGen(dataset_name=dataset_name, dataset_description="Maternal Health Data",
                           data_level="State level", cols_dict=cols_to_nodes)
    readme_gen.gen_readme()