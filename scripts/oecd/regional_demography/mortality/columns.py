import pandas as pd
import sys

sys.path.append('../')
from utils import multi_index_to_single_index

VAR_to_statsvars = {
    'DEATH_RAT':
        'Count_Death_AsAFractionOf_Count_Person',
    'DEATH_RAM':
        'Count_Death_Male_AsAFractionOf_Count_Person_Male',
    'DEATH_RAF':
        'Count_Death_Female_AsAFractionOf_Count_Person_Female',
    'STD_MORTT':
        'Count_Death_AgeAdjusted_AsAFractionOf_Count_Person',
    'STD_MORTM':
        'Count_Death_Male_AgeAdjusted_AsAFractionOf_Count_Person_Male',
    'STD_MORTF':
        'Count_Death_Female_AgeAdjusted_AsAFractionOf_Count_Person_Female',
    'YOU_DEATH_RAT':
        'Count_Death_Upto14Years_AsAFractionOf_Count_Person_Upto14Years',
    'YOU_DEATH_RAM':
        'Count_Death_Upto14Years_Male_AsAFractionOf_Count_Person_Upto14Years_Male',
    'YOU_DEATH_RAF':
        'Count_Death_Upto14Years_Female_AsAFractionOf_Count_Person_Upto14Years_Female',
    'INF_MORTT':
        'Count_Death_LessThan1Year_AsAFractionOf_Count_BirthEvent',
    'INF_MORTM':
        'Count_Death_LessThan1Year_Male_AsAFractionOf_Count_BirthEvent_Male',
    'INF_MORTF':
        'Count_Death_LessThan1Year_Female_AsAFractionOf_Count_BirthEvent_Female'
}

reindex_column = [
    'Region', 'Year', 'Count_Death_Male_AsAFractionOf_Count_Person_Male',
    'Count_Death_Female_AsAFractionOf_Count_Person_Female',
    'Count_Death_AgeAdjusted_AsAFractionOf_Count_Person',
    'Count_Death_Male_AgeAdjusted_AsAFractionOf_Count_Person_Male',
    'Count_Death_Female_AgeAdjusted_AsAFractionOf_Count_Person_Female',
    'Count_Death_Upto14Years_AsAFractionOf_Count_Person_Upto14Years',
    'Count_Death_Upto14Years_Male_AsAFractionOf_Count_Person_Upto14Years_Male',
    'Count_Death_Upto14Years_Female_AsAFractionOf_Count_Person_Upto14Years_Female',
    'Count_Death_LessThan1Year_AsAFractionOf_Count_BirthEvent',
    'Count_Death_LessThan1Year_Male_AsAFractionOf_Count_BirthEvent_Male',
    'Count_Death_LessThan1Year_Female_AsAFractionOf_Count_BirthEvent_Female',
    'Count_Death_AsAFractionOf_Count_Person',
    'Count_Death_AsAFractionOfCount_Person'
]

df_raw = pd.read_csv(
    "/usr/local/google/home/chharish/oecd_refresh/data/scripts/oecd/regional_demography/mortality/OECD_OLD_life_mort_cleaned.csv"
)

df_cleaned = df_raw.reindex(columns=reindex_column)

df_cleaned.to_csv("OECD_mortality_retained.csv", index=False)
