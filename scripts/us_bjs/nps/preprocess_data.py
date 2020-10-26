import pandas as pd
import argparse

STAT_VAR_NAMES = ["Count_Jurisdiction_WhiteAlone_Female", "Count_Jurisdiction_WhiteAlone_Male", "Count_Jurisdiction_WhiteAlone","Count_Jurisdiction_BlackOrAfricanAmericanAlone_Female",
"Count_Jurisdiction_BlackOrAfricanAmericanAlone_Male", "Count_Jurisdiction_BlackOrAfricanAmericanAlone", "Count_Jurisdiction_HispanicOrLatino_Female", "Count_Jurisdiction_HispanicOrLatino_Male",
"Count_Jurisdiction_HispanicOrLatino", "Count_Jurisdiction_AmericanIndianOrAlaskaNativeAlone_Female", "Count_Jurisdiction_AmericanIndianOrAlaskaNativeAlone_Male",
"Count_Jurisdiction_AmericanIndianOrAlaskaNativeAlone", "Count_Jurisdiction_AsianAlone_Female", "Count_Jurisdiction_AsianAlone_Male", "Count_Jurisdiction_AsianAlone",
"Count_Jurisdiction_NativeHawaiianOrOtherPacificIslanderAlone_Female", "Count_Jurisdiction_NativeHawaiianOrOtherPacificIslanderAlone_Male", "Count_Jurisdiction_NativeHawaiianOrOtherPacificIslanderAlone",
"Count_Jurisdiction_TwoOrMoreRaces_Female", "Count_Jurisdiction_TwoOrMoreRaces_Male", "Count_Jurisdiction_TwoOrMoreRaces", "Count_Jurisdiction_Death_Female", "Count_Jurisdiction_Death_Male", 
"Count_Jurisdiction_Death", "Count_Jurisdiction_DeathByJudicialExecution_Female", "Count_Jurisdiction_DeathByJudicialExecution_Male", "Count_Jurisdiction_DeathByJudicialExecution",
"Count_Jurisdiction_DeathByIllnessOrNaturalCause_Female", "Count_Jurisdiction_DeathByIllnessOrNaturalCause_Male", "Count_Jurisdiction_DeathByIllnessOrNaturalCause", "Count_Jurisdiction_DeathByAIDS_Female",
"Count_Jurisdiction_DeathByAIDS_Male", "Count_Jurisdiction_DeathByAIDS", "Count_Jurisdiction_DeathByIntentionalSelf-Harm(Suicide)_Female", "Count_Jurisdiction_DeathByIntentionalSelf-Harm(Suicide)_Male",
"Count_Jurisdiction_DeathByIntentionalSelf-Harm(Suicide)", "Count_Jurisdiction_DeathByAccidents(UnintentionalInjuries)_Female", "Count_Jurisdiction_DeathByAccidents(UnintentionalInjuries)_Male",
"Count_Jurisdiction_DeathByAccidents(UnintentionalInjuries)", "Count_Jurisdiction_DeathByDeathDueToAnotherPerson_Female", "Count_Jurisdiction_DeathByDeathDueToAnotherPerson_Male",
"Count_Jurisdiction_DeathByDeathDueToAnotherPerson", "Count_Jurisdiction_DeathByAssault(Homicide)_Female", "Count_Jurisdiction_DeathByAssault(Homicide)_Male", "Count_Jurisdiction_DeathByAssault(Homicide)",
"Count_Jurisdiction_DeathByNPSOtherCauseOfDeath_Female", "Count_Jurisdiction_DeathByNPSOtherCauseOfDeath_Male", "Count_Jurisdiction_DeathByNPSOtherCauseOfDeath", "Count_Jurisdiction_AdmittedToPrison_Female",
"Count_Jurisdiction_AdmittedToPrison_Male", "Count_Jurisdiction_AdmittedToPrison", "Count_Jurisdiction_ReleasedFromPrison_Female", "Count_Jurisdiction_ReleasedFromPrison_Male",
"Count_Jurisdiction_ReleasedFromPrison", "Count_Jurisdiction_MaxSentenceGreaterThan1Year_Female", "Count_Jurisdiction_MaxSentenceGreaterThan1Year_Male", "Count_Jurisdiction_MaxSentenceGreaterThan1Year",
"Count_Jurisdiction_MaxSentence1YearOrLess_Female", "Count_Jurisdiction_MaxSentence1YearOrLess_Male", "Count_Jurisdiction_MaxSentence1YearOrLess", "Count_Jurisdiction_Unsentenced_Female",
"Count_Jurisdiction_Unsentenced_Male", "Count_Jurisdiction_Unsentenced", "Count_Jurisdiction_PrivatelyOperatedInStateFacility_Female", "Count_Jurisdiction_PrivatelyOperatedInStateFacility_Male",
"Count_Jurisdiction_PrivatelyOperatedInStateFacility", "Count_Jurisdiction_PrivatelyOperatedOutOfStateFacility_Female", "Count_Jurisdiction_PrivatelyOperatedOutOfStateFacility_Male",
"Count_Jurisdiction_PrivatelyOperatedOutOfStateFacility", "Count_Jurisdiction_LocallyOperatedLocalFacility_Female", "Count_Jurisdiction_LocallyOperatedLocalFacility_Male",
"Count_Jurisdiction_LocallyOperatedLocalFacility", "Count_Jurisdiction_FederallyOperatedFacility_Female", "Count_Jurisdiction_FederallyOperatedFacility_Male", "Count_Jurisdiction_FederallyOperatedFacility",
"Count_Jurisdiction_StateOperatedOutOfStateFacility_Female", "Count_Jurisdiction_StateOperatedOutOfStateFacility_Male", "Count_Jurisdiction_StateOperatedOutOfStateFacility",
"Count_Custody_NotAUSCitizen_Female", "Count_Custody_NotAUSCitizen_Male", "Count_Custody_NotAUSCitizen", "Count_Custody_NotAUSCitizen_MaxSentenceGreaterThan1Year_Female",
"Count_Custody_NotAUSCitizen_MaxSentenceGreaterThan1Year_Male", "Count_Custody_NotAUSCitizen_MaxSentenceGreaterThan1Year", "Count_Custody_NotAUSCitizen_MaxSentence1YearOrLess_Female",
"Count_Custody_NotAUSCitizen_MaxSentence1YearOrLess_Male", "Count_Custody_NotAUSCitizen_MaxSentence1YearOrLess", "Count_Custody_NotAUSCitizen_Unsentenced_Female", "Count_Custody_NotAUSCitizen_Unsentenced_Male",
"Count_Custody_NotAUSCitizen_Unsentenced", "Count_Custody_Under18_Female", "Count_Custody_Under18_Male", "Count_Custody_Under18", "Count_Jurisdiction_Female", "Count_Jurisdiction_Male", "Count_Jurisdiction"]

DESIRED_COLUMNS = ['GeoId', 'YEAR'] + STAT_VAR_NAMES

def convert_nan_for_calculation(value):
    if pd.isna(value):
        return 0
    else:
        return value

def get_total_jurisdiction_columns(df):
    """calculation to include private facility numbers"""
    df["PVINF_Temp"] = df["PVINF"].apply(convert_nan_for_calculation)
    df["PVOTHF_Temp"] = df["PVOTHF"].apply(convert_nan_for_calculation)
    df["PVINM_Temp"] = df["PVINM"].apply(convert_nan_for_calculation)
    df["PVOTHM_Temp"] = df["PVOTHM"].apply(convert_nan_for_calculation)
    df["Female_Total_Temp"] = df[["JURTOTF", "PVINF_Temp", "PVOTHF_Temp"]].sum(axis=1).where(df["PVINCLF"] == 2, df["JURTOTF"])
    df["Male_Total_Temp"] = df[["JURTOTM", "PVINM_Temp", "PVOTHM_Temp"]].sum(axis=1).where(df["PVINCLM"] == 2, df["JURTOTM"])
    """calculation to include local facility numbers"""
    df["LFF_Temp"] = df["LFF"].apply(convert_nan_for_calculation)
    df["LFM_Temp"] = df["LFM"].apply(convert_nan_for_calculation)
    df["Female_Total_Temp"] = df[["Female_Total_Temp", "LFF_Temp"]].sum(axis=1).where(df["LFINCLF"] == 2, df["Female_Total_Temp"])
    df["Male_Total_Temp"] = df[["Male_Total_Temp", "LFM_Temp"]].sum(axis=1).where(df["LFINCLM"] == 2, df["Male_Total_Temp"])
    """calculation to include numbers from local facilities solely to ease crowding"""
    df["LFCRSTF_Temp"] = df["LFCRSTF"].apply(convert_nan_for_calculation)
    df["LFCRSTM_Temp"] = df["LFCRSTM"].apply(convert_nan_for_calculation)
    df["Female_Total_Temp"] = df[["Female_Total_Temp", "LFCRSTF_Temp"]].sum(axis=1).where(df["LFCRINCF"] == 2, df["Female_Total_Temp"])
    df["Male_Total_Temp"] = df[["Male_Total_Temp", "LFCRSTM_Temp"]].sum(axis=1).where(df["LFCRINCM"] == 2, df["Male_Total_Temp"])
    """calculation to include federal and other state facility numbers"""
    df["FEDF_Temp"] = df["FEDF"].apply(convert_nan_for_calculation)
    df["OTHSTF_Temp"] = df["OTHSTF"].apply(convert_nan_for_calculation)
    df["FEDM_Temp"] = df["FEDM"].apply(convert_nan_for_calculation)
    df["OTHSTM_Temp"] = df["OTHSTM"].apply(convert_nan_for_calculation)
    df["Female_Total_Temp"] = df[["Female_Total_Temp", "FEDF_Temp", "OTHSTF_Temp"]].sum(axis=1).where(df["FACINCLF"] == 2, df["Female_Total_Temp"])
    df["Male_Total_Temp"] = df[["Male_Total_Temp", "FEDM_Temp", "OTHSTM_Temp"]].sum(axis=1).where(df["FACINCLM"] == 2, df["Male_Total_Temp"])
    """make jurisdiction total columns"""
    df["Count_Jurisdiction_Female"] = df["Female_Total_Temp"]
    df["Count_Jurisdiction_Male"] = df["Male_Total_Temp"]
    df["Count_Jurisdiction"] = df["Female_Total_Temp"] + df["Male_Total_Temp"]
    
def get_columns(df):
    get_total_jurisdiction_columns(df)
    df["Count_Jurisdiction_WhiteAlone_Female"] = df["WHITEF"]
    df["Count_Jurisdiction_WhiteAlone_Male"] = df["WHITEM"]
    df["Count_Jurisdiction_WhiteAlone"] = df["WHITEF"] + df["WHITEM"]
    df["Count_Jurisdiction_BlackOrAfricanAmericanAlone_Female"] = df["BLACKF"]
    df["Count_Jurisdiction_BlackOrAfricanAmericanAlone_Male"] = df["BLACKM"]
    df["Count_Jurisdiction_BlackOrAfricanAmericanAlone"] = df["BLACKF"] + df["BLACKM"]
    df["Count_Jurisdiction_HispanicOrLatino_Female"] = df["HISPF"]
    df["Count_Jurisdiction_HispanicOrLatino_Male"] = df["HISPM"]
    df["Count_Jurisdiction_HispanicOrLatino"] = df["HISPF"] + df["HISPM"]
    df["Count_Jurisdiction_AmericanIndianOrAlaskaNativeAlone_Female"] = df["AIANF"]
    df["Count_Jurisdiction_AmericanIndianOrAlaskaNativeAlone_Male"] = df["AIANM"]
    df["Count_Jurisdiction_AmericanIndianOrAlaskaNativeAlone"] = df["AIANF"] + df["AIANM"]
    df["Count_Jurisdiction_AsianAlone_Female"] = df["ASIANF"]
    df["Count_Jurisdiction_AsianAlone_Male"] = df["ASIANM"]
    df["Count_Jurisdiction_AsianAlone"] = df["ASIANF"] + df["ASIANM"]
    df["Count_Jurisdiction_NativeHawaiianOrOtherPacificIslanderAlone_Female"] = df["NHPIF"]
    df["Count_Jurisdiction_NativeHawaiianOrOtherPacificIslanderAlone_Male"] = df["NHPIM"]
    df["Count_Jurisdiction_NativeHawaiianOrOtherPacificIslanderAlone"] = df["NHPIF"] + df["NHPIM"]
    df["Count_Jurisdiction_TwoOrMoreRaces_Female"] = df["TWORACEF"]
    df["Count_Jurisdiction_TwoOrMoreRaces_Male"] = df["TWORACEM"]
    df["Count_Jurisdiction_TwoOrMoreRaces"] = df["TWORACEF"] + df["TWORACEM"]
    df["Count_Jurisdiction_Death_Female"] = df["DTHTOTF"]
    df["Count_Jurisdiction_Death_Male"] = df["DTHTOTM"]
    df["Count_Jurisdiction_Death"] = df["DTHTOTF"] + df["DTHTOTM"]
    df["Count_Jurisdiction_DeathByJudicialExecution_Female"] = df["DTHEXECF"]
    df["Count_Jurisdiction_DeathByJudicialExecution_Male"] = df["DTHEXECM"]
    df["Count_Jurisdiction_DeathByJudicialExecution"] = df["DTHEXECF"] + df["DTHEXECM"]
    df["Count_Jurisdiction_DeathByIllnessOrNaturalCause_Female"] = df["DTHILLNF"]
    df["Count_Jurisdiction_DeathByIllnessOrNaturalCause_Male"] = df["DTHILLNM"]
    df["Count_Jurisdiction_DeathByIllnessOrNaturalCause"] = df["DTHILLNF"] + df["DTHILLNM"]
    df["Count_Jurisdiction_DeathByAIDS_Female"] = df["DTHAIDSF"]
    df["Count_Jurisdiction_DeathByAIDS_Male"] = df["DTHAIDSM"]
    df["Count_Jurisdiction_DeathByAIDS"] = df["DTHAIDSF"] + df["DTHAIDSM"]
    df["Count_Jurisdiction_DeathByIntentionalSelf-Harm(Suicide)_Female"] = df["DTHSUICF"]
    df["Count_Jurisdiction_DeathByIntentionalSelf-Harm(Suicide)_Male"] = df["DTHSUICM"]
    df["Count_Jurisdiction_DeathByIntentionalSelf-Harm(Suicide)"] = df["DTHSUICF"] + df["DTHSUICM"]
    df["Count_Jurisdiction_DeathByAccidents(UnintentionalInjuries)_Female"] = df["DTHACCF"]
    df["Count_Jurisdiction_DeathByAccidents(UnintentionalInjuries)_Male"] = df["DTHACCM"]
    df["Count_Jurisdiction_DeathByAccidents(UnintentionalInjuries)"] = df["DTHACCF"] + df["DTHACCM"]
    df["Count_Jurisdiction_DeathByDeathDueToAnotherPerson_Female"] = df["DTHPERSF"]
    df["Count_Jurisdiction_DeathByDeathDueToAnotherPerson_Male"] = df["DTHPERSM"]
    df["Count_Jurisdiction_DeathByDeathDueToAnotherPerson"] = df["DTHPERSF"] + df["DTHPERSM"]
    df["Count_Jurisdiction_DeathByAssault(Homicide)_Female"] = df["DTHHOMIF"]
    df["Count_Jurisdiction_DeathByAssault(Homicide)_Male"] = df["DTHHOMIM"]
    df["Count_Jurisdiction_DeathByAssault(Homicide)"] = df["DTHHOMIF"] + df["DTHHOMIM"]
    df["Count_Jurisdiction_DeathByNPSOtherCauseOfDeath_Female"] = df["DTHOTHF"]
    df["Count_Jurisdiction_DeathByNPSOtherCauseOfDeath_Male"] = df["DTHOTHM"]
    df["Count_Jurisdiction_DeathByNPSOtherCauseOfDeath"] = df["DTHOTHF"] + df["DTHOTHM"]
    df["Count_Jurisdiction_AdmittedToPrison_Female"] = df["ADTOTF"]
    df["Count_Jurisdiction_AdmittedToPrison_Male"] = df["ADTOTM"]
    df["Count_Jurisdiction_AdmittedToPrison"] = df["ADTOTF"] + df["ADTOTM"]
    df["Count_Jurisdiction_ReleasedFromPrison_Female"] = df["RLTOTF"]
    df["Count_Jurisdiction_ReleasedFromPrison_Male"] = df["RLTOTM"]
    df["Count_Jurisdiction_ReleasedFromPrison"] = df["RLTOTF"] + df["RLTOTM"]
    df["Count_Jurisdiction_MaxSentenceGreaterThan1Year_Female"] = df["JURGT1F"]
    df["Count_Jurisdiction_MaxSentenceGreaterThan1Year_Male"] = df["JURGT1M"]
    df["Count_Jurisdiction_MaxSentenceGreaterThan1Year"] = df["JURGT1F"] + df["JURGT1M"]
    df["Count_Jurisdiction_MaxSentence1YearOrLess_Female"] = df["JURLT1F"]
    df["Count_Jurisdiction_MaxSentence1YearOrLess_Male"] = df["JURLT1M"]
    df["Count_Jurisdiction_MaxSentence1YearOrLess"] = df["JURLT1F"] + df["JURLT1M"]
    df["Count_Jurisdiction_Unsentenced_Female"] = df["JURUNSF"]
    df["Count_Jurisdiction_Unsentenced_Male"] = df["JURUNSM"]
    df["Count_Jurisdiction_Unsentenced"] = df["JURUNSF"] + df["JURUNSM"]
    df["Count_Jurisdiction_PrivatelyOperatedInStateFacility_Female"] = df["PVINF"]
    df["Count_Jurisdiction_PrivatelyOperatedInStateFacility_Male"] = df["PVINM"]
    df["Count_Jurisdiction_PrivatelyOperatedInStateFacility"] = df["PVINF"] + df["PVINM"]
    df["Count_Jurisdiction_PrivatelyOperatedOutOfStateFacility_Female"] = df["PVOTHF"]
    df["Count_Jurisdiction_PrivatelyOperatedOutOfStateFacility_Male"] = df["PVOTHM"]
    df["Count_Jurisdiction_PrivatelyOperatedOutOfStateFacility"] = df["PVOTHF"] + df["PVOTHM"]
    df["Count_Jurisdiction_LocallyOperatedLocalFacility_Female"] = df["LFF"]
    df["Count_Jurisdiction_LocallyOperatedLocalFacility_Male"] = df["LFM"]
    df["Count_Jurisdiction_LocallyOperatedLocalFacility"] = df["LFF"] + df["LFM"]
    df["Count_Jurisdiction_FederallyOperatedFacility_Female"] = df["FEDF"]
    df["Count_Jurisdiction_FederallyOperatedFacility_Male"] = df["FEDM"]
    df["Count_Jurisdiction_FederallyOperatedFacility"] = df["FEDF"] + df["FEDM"]
    df["Count_Jurisdiction_StateOperatedOutOfStateFacility_Female"] = df["OTHSTF"]
    df["Count_Jurisdiction_StateOperatedOutOfStateFacility_Male"] = df["OTHSTM"]
    df["Count_Jurisdiction_StateOperatedOutOfStateFacility"] = df["OTHSTF"] + df["OTHSTM"]
    df["Count_Custody_NotAUSCitizen_Female"] = df["NCITZTOTF"]
    df["Count_Custody_NotAUSCitizen_Male"] = df["NCITZTOTM"]
    df["Count_Custody_NotAUSCitizen"] = df["NCITZTOTF"] + df["NCITZTOTM"]
    df["Count_Custody_NotAUSCitizen_MaxSentenceGreaterThan1Year_Female"] = df["NCITZGT1F"]
    df["Count_Custody_NotAUSCitizen_MaxSentenceGreaterThan1Year_Male"] = df["NCITZGT1M"]
    df["Count_Custody_NotAUSCitizen_MaxSentenceGreaterThan1Year"] = df["NCITZGT1F"] + df["NCITZGT1M"]
    df["Count_Custody_NotAUSCitizen_MaxSentence1YearOrLess_Female"] = df["NCITZLE1F"]
    df["Count_Custody_NotAUSCitizen_MaxSentence1YearOrLess_Male"] = df["NCITZLE1M"]
    df["Count_Custody_NotAUSCitizen_MaxSentence1YearOrLess"] = df["NCITZLE1F"] + df["NCITZLE1M"]
    df["Count_Custody_NotAUSCitizen_Unsentenced_Female"] = df["NCITZUNSF"]
    df["Count_Custody_NotAUSCitizen_Unsentenced_Male"] = df["NCITZUNSM"]
    df["Count_Custody_NotAUSCitizen_Unsentenced"] = df["NCITZUNSF"] + df["NCITZUNSM"]
    df["Count_Custody_Under18_Female"] = df["CUSLT18F"]
    df["Count_Custody_Under18_Male"] = df["CUSLT18M"]
    df["Count_Custody_Under18"] = df["CUSLT18F"] + df["CUSLT18M"]
    get_total_jurisdiction_columns(df)
    
def convert_geoId(fips_code):
    """Creates geoId column"""
    return 'geoId/' + str(fips_code).zfill(2)

def convert_missing_value_to_nan(value):
    """codes for missing values are always negative and actual data is always >= 0"""
    if isinstance(value, int) and value < 0:
        return float("nan")
    else:
        return value
        
def convert_nan_to_empty_cell(value):
    if pd.isna(value):
        return ''
    else:
        return value
    
def preprocess_df(raw_df):
    """cleans raw_df

    Args:
        raw_data: raw data frame to be used as starting point for cleaning
    """
    df = raw_df.copy()
    column_names = list(df.columns)
    df['GeoId'] = df['STATEID'].apply(convert_geoId)
    
    # convert missing values to NaN for aggregation
    for column_name in column_names:
        df[column_name] = df[column_name].apply(convert_missing_value_to_nan)
    
    #get columns matching stat var names and add aggregate columns
    get_columns(df)
    
    #convert NaN to empty cell
    for column_name in column_names:
        df[column_name] = df[column_name].apply(convert_nan_to_empty_cell)
        
    #filter out unnecessary columns
    return df[DESIRED_COLUMNS]

def main(args):
        filename = args.input_file
        print('Processing {0}'.format(filename))
        df = pd.read_csv(filename, delimiter='\t')
        processed_df = preprocess_df(df)
        processed_df.to_csv(args.input_file.replace('.tsv', '_processed.csv'),
                            index=False)
        print('Done processing {0}'.format(args.input_file))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="NPS Processing Script")
    parser.add_argument('-i',
                        dest='input_file',
                        default='NPS_1978-2018_Data.tsv')
    args = parser.parse_args()

    main(args)
