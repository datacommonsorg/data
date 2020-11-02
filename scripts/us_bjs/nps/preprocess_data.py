import pandas as pd
import argparse

STAT_VAR_NAMES = [
    "Count_Person_Female_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_Person_Female_Incarcerated_WhiteAlone_MeasuredBasedOnJurisdiction",
    "Count_Person_BlackOrAfricanAmericanAlone_Female_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_Person_Female_HispanicOrLatino_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_Person_AmericanIndianOrAlaskaNativeAlone_Female_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_Person_AsianAlone_Female_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_Person_Female_Incarcerated_NativeHawaiianOrOtherPacificIslanderAlone_MeasuredBasedOnJurisdiction",
    "Count_Person_Female_Incarcerated_TwoOrMoreRaces_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Female_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Female_Incarcerated_JudicialExecution_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Female_IllnessOrNaturalCause_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_AIDS_Female_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Female_Incarcerated_IntentionalSelf-Harm(Suicide)_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Accidents(UnintentionalInjuries)_Female_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_DeathDueToAnotherPerson_Female_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Assault(Homicide)_Female_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Female_Incarcerated_NPSOtherCauseOfDeath_MeasuredBasedOnJurisdiction",
    "Count_IncarcerationEvent_AdmittedToPrison_Female_Incarcerated_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction",
    "Count_IncarcerationEvent_Female_Incarcerated_MaxSentenceGreaterThan1Year_ReleasedFromPrison_Sentenced_MeasuredBasedOnJurisdiction",
    "Count_Person_Female_Incarcerated_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction",
    "Count_Person_Female_Incarcerated_MaxSentence1YearOrLess_Sentenced_MeasuredBasedOnJurisdiction",
    "Count_Person_Female_Incarcerated_Unsentenced_MeasuredBasedOnJurisdiction",
    "Count_Person_Female_Incarcerated_InState_PrivatelyOperated_MeasuredBasedOnJurisdiction",
    "Count_Person_Female_Incarcerated_OutOfState_PrivatelyOperated_MeasuredBasedOnJurisdiction",
    "Count_Person_Female_Incarcerated_Local_LocallyOperated_MeasuredBasedOnJurisdiction",
    "Count_Person_FederallyOperated_Female_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_Person_Female_Incarcerated_OutOfState_StateOperated_MeasuredBasedOnJurisdiction",
    "Count_Person_Female_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody",
    "Count_Person_Female_Incarcerated_MaxSentenceGreaterThan1Year_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody",
    "Count_Person_Female_Incarcerated_MaxSentence1YearOrLess_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody",
    "Count_Person_Female_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_Unsentenced_MeasuredBasedOnCustody",
    "Count_Person_Female_Incarcerated_Under18_MeasuredBasedOnCustody",
    "Count_Person_Incarcerated_Male_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_Male_WhiteAlone_MeasuredBasedOnJurisdiction",
    "Count_Person_BlackOrAfricanAmericanAlone_Incarcerated_Male_MeasuredBasedOnJurisdiction",
    "Count_Person_HispanicOrLatino_Incarcerated_Male_MeasuredBasedOnJurisdiction",
    "Count_Person_AmericanIndianOrAlaskaNativeAlone_Incarcerated_Male_MeasuredBasedOnJurisdiction",
    "Count_Person_AsianAlone_Incarcerated_Male_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_Male_NativeHawaiianOrOtherPacificIslanderAlone_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_Male_TwoOrMoreRaces_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Incarcerated_Male_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Incarcerated_JudicialExecution_Male_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_IllnessOrNaturalCause_Incarcerated_Male_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_AIDS_Incarcerated_Male_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Incarcerated_IntentionalSelf-Harm(Suicide)_Male_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Accidents(UnintentionalInjuries)_Incarcerated_Male_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_DeathDueToAnotherPerson_Incarcerated_Male_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Assault(Homicide)_Incarcerated_Male_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Incarcerated_Male_NPSOtherCauseOfDeath_MeasuredBasedOnJurisdiction",
    "Count_IncarcerationEvent_AdmittedToPrison_Incarcerated_Male_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction",
    "Count_IncarcerationEvent_Incarcerated_Male_MaxSentenceGreaterThan1Year_ReleasedFromPrison_Sentenced_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_Male_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_Male_MaxSentence1YearOrLess_Sentenced_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_Male_Unsentenced_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_InState_Male_PrivatelyOperated_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_Male_OutOfState_PrivatelyOperated_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_Local_LocallyOperated_Male_MeasuredBasedOnJurisdiction",
    "Count_Person_FederallyOperated_Incarcerated_Male_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_Male_OutOfState_StateOperated_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_Male_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody",
    "Count_Person_Incarcerated_Male_MaxSentenceGreaterThan1Year_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody",
    "Count_Person_Incarcerated_Male_MaxSentence1YearOrLess_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody",
    "Count_Person_Incarcerated_Male_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_Unsentenced_MeasuredBasedOnCustody",
    "Count_Person_Incarcerated_Male_Under18_MeasuredBasedOnCustody",
    "Count_Person_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_WhiteAlone_MeasuredBasedOnJurisdiction",
    "Count_Person_BlackOrAfricanAmericanAlone_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_Person_HispanicOrLatino_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_Person_AmericanIndianOrAlaskaNativeAlone_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_Person_AsianAlone_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_NativeHawaiianOrOtherPacificIslanderAlone_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_TwoOrMoreRaces_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Incarcerated_JudicialExecution_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_IllnessOrNaturalCause_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_AIDS_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Incarcerated_IntentionalSelf-Harm(Suicide)_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Accidents(UnintentionalInjuries)_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_DeathDueToAnotherPerson_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Assault(Homicide)_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_MortalityEvent_Incarcerated_NPSOtherCauseOfDeath_MeasuredBasedOnJurisdiction",
    "Count_IncarcerationEvent_AdmittedToPrison_Incarcerated_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction",
    "Count_IncarcerationEvent_Incarcerated_MaxSentenceGreaterThan1Year_ReleasedFromPrison_Sentenced_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_MaxSentence1YearOrLess_Sentenced_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_Unsentenced_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_InState_PrivatelyOperated_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_OutOfState_PrivatelyOperated_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_Local_LocallyOperated_MeasuredBasedOnJurisdiction",
    "Count_Person_FederallyOperated_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_OutOfState_StateOperated_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody",
    "Count_Person_Incarcerated_MaxSentenceGreaterThan1Year_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody",
    "Count_Person_Incarcerated_MaxSentence1YearOrLess_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody",
    "Count_Person_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_Unsentenced_MeasuredBasedOnCustody",
    "Count_Person_Incarcerated_Under18_MeasuredBasedOnCustody"
]

DESIRED_COLUMNS = ['GeoId', 'YEAR'] + STAT_VAR_NAMES

def convert_nan_for_calculation(value):
    if pd.isna(value):
        return 0
    else:
        return value

def total_jurisdiction_columns_helper(df):
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
   
    
def get_columns(df):
    total_jurisdiction_columns_helper(df)
    df["Count_Person_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df["Female_Total_Temp"]
    df["Count_Person_Female_Incarcerated_WhiteAlone_MeasuredBasedOnJurisdiction"] = df["WHITEF"]
    df["Count_Person_BlackOrAfricanAmericanAlone_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df["BLACKF"]
    df["Count_Person_Female_HispanicOrLatino_Incarcerated_MeasuredBasedOnJurisdiction"] = df["HISPF"]
    df["Count_Person_AmericanIndianOrAlaskaNativeAlone_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df["AIANF"]
    df["Count_Person_AsianAlone_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df["ASIANF"]
    df["Count_Person_Female_Incarcerated_NativeHawaiianOrOtherPacificIslanderAlone_MeasuredBasedOnJurisdiction"] = df["NHPIF"]
    df["Count_Person_Female_Incarcerated_TwoOrMoreRaces_MeasuredBasedOnJurisdiction"] = df["TWORACEF"]
    df["Count_MortalityEvent_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df["DTHTOTF"]
    df["Count_MortalityEvent_Female_Incarcerated_JudicialExecution_MeasuredBasedOnJurisdiction"] = df["DTHEXECF"]
    df["Count_MortalityEvent_Female_IllnessOrNaturalCause_Incarcerated_MeasuredBasedOnJurisdiction"] = df["DTHILLNF"]
    df["Count_MortalityEvent_AIDS_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df["DTHAIDSF"]
    df["Count_MortalityEvent_Female_Incarcerated_IntentionalSelf-Harm(Suicide)_MeasuredBasedOnJurisdiction"] = df["DTHSUICF"]
    df["Count_MortalityEvent_Accidents(UnintentionalInjuries)_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df["DTHACCF"]
    df["Count_MortalityEvent_DeathDueToAnotherPerson_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df["DTHPERSF"]
    df["Count_MortalityEvent_Assault(Homicide)_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df["DTHHOMIF"]
    df["Count_MortalityEvent_Female_Incarcerated_NPSOtherCauseOfDeath_MeasuredBasedOnJurisdiction"] = df["DTHOTHF"]
    df["Count_IncarcerationEvent_AdmittedToPrison_Female_Incarcerated_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction"] = df["ADTOTF"]
    df["Count_IncarcerationEvent_Female_Incarcerated_MaxSentenceGreaterThan1Year_ReleasedFromPrison_Sentenced_MeasuredBasedOnJurisdiction"] = df["RLTOTF"]
    df["Count_Person_Female_Incarcerated_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction"] = df["JURGT1F"]
    df["Count_Person_Female_Incarcerated_MaxSentence1YearOrLess_Sentenced_MeasuredBasedOnJurisdiction"] = df["JURLT1F"]
    df["Count_Person_Female_Incarcerated_Unsentenced_MeasuredBasedOnJurisdiction"] = df["JURUNSF"]
    df["Count_Person_Female_Incarcerated_InState_PrivatelyOperated_MeasuredBasedOnJurisdiction"] = df["PVINF"]
    df["Count_Person_Female_Incarcerated_OutOfState_PrivatelyOperated_MeasuredBasedOnJurisdiction"] = df["PVOTHF"]
    df["Count_Person_Female_Incarcerated_Local_LocallyOperated_MeasuredBasedOnJurisdiction"] = df["LFF"]
    df["Count_Person_FederallyOperated_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df["FEDF"]
    df["Count_Person_Female_Incarcerated_OutOfState_StateOperated_MeasuredBasedOnJurisdiction"] = df["OTHSTF"]
    df["Count_Person_Female_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df["NCITZTOTF"]
    df["Count_Person_Female_Incarcerated_MaxSentenceGreaterThan1Year_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df["NCITZGT1F"]
    df["Count_Person_Female_Incarcerated_MaxSentence1YearOrLess_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df["NCITZLE1F"]
    df["Count_Person_Female_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_Unsentenced_MeasuredBasedOnCustody"] = df["NCITZUNSF"]
    df["Count_Person_Female_Incarcerated_Under18_MeasuredBasedOnCustody"] = df["CUSLT18F"]
    df["Count_Person_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df["Male_Total_Temp"]
    df["Count_Person_Incarcerated_Male_WhiteAlone_MeasuredBasedOnJurisdiction"] = df["WHITEM"]
    df["Count_Person_BlackOrAfricanAmericanAlone_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df["BLACKM"]
    df["Count_Person_HispanicOrLatino_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df["HISPM"]
    df["Count_Person_AmericanIndianOrAlaskaNativeAlone_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df["AIANM"]
    df["Count_Person_AsianAlone_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df["ASIANM"]
    df["Count_Person_Incarcerated_Male_NativeHawaiianOrOtherPacificIslanderAlone_MeasuredBasedOnJurisdiction"] = df["NHPIM"]
    df["Count_Person_Incarcerated_Male_TwoOrMoreRaces_MeasuredBasedOnJurisdiction"] = df["TWORACEM"]
    df["Count_MortalityEvent_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df["DTHTOTM"]
    df["Count_MortalityEvent_Incarcerated_JudicialExecution_Male_MeasuredBasedOnJurisdiction"] = df["DTHEXECM"]
    df["Count_MortalityEvent_IllnessOrNaturalCause_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df["DTHILLNM"]
    df["Count_MortalityEvent_AIDS_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df["DTHAIDSM"]
    df["Count_MortalityEvent_Incarcerated_IntentionalSelf-Harm(Suicide)_Male_MeasuredBasedOnJurisdiction"] = df["DTHSUICM"]
    df["Count_MortalityEvent_Accidents(UnintentionalInjuries)_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df["DTHACCM"]
    df["Count_MortalityEvent_DeathDueToAnotherPerson_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df["DTHPERSM"]
    df["Count_MortalityEvent_Assault(Homicide)_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df["DTHHOMIM"]
    df["Count_MortalityEvent_Incarcerated_Male_NPSOtherCauseOfDeath_MeasuredBasedOnJurisdiction"] = df["DTHOTHM"]
    df["Count_IncarcerationEvent_AdmittedToPrison_Incarcerated_Male_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction"] = df["ADTOTM"]
    df["Count_IncarcerationEvent_Incarcerated_Male_MaxSentenceGreaterThan1Year_ReleasedFromPrison_Sentenced_MeasuredBasedOnJurisdiction"] = df["RLTOTM"]
    df["Count_Person_Incarcerated_Male_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction"] = df["JURGT1M"]
    df["Count_Person_Incarcerated_Male_MaxSentence1YearOrLess_Sentenced_MeasuredBasedOnJurisdiction"] = df["JURLT1M"]
    df["Count_Person_Incarcerated_Male_Unsentenced_MeasuredBasedOnJurisdiction"] = df["JURUNSM"]
    df["Count_Person_Incarcerated_InState_Male_PrivatelyOperated_MeasuredBasedOnJurisdiction"] = df["PVINM"]
    df["Count_Person_Incarcerated_Male_OutOfState_PrivatelyOperated_MeasuredBasedOnJurisdiction"] = df["PVOTHM"]
    df["Count_Person_Incarcerated_Local_LocallyOperated_Male_MeasuredBasedOnJurisdiction"] = df["LFM"]
    df["Count_Person_FederallyOperated_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df["FEDM"]
    df["Count_Person_Incarcerated_Male_OutOfState_StateOperated_MeasuredBasedOnJurisdiction"] = df["OTHSTM"]
    df["Count_Person_Incarcerated_Male_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df["NCITZTOTM"]
    df["Count_Person_Incarcerated_Male_MaxSentenceGreaterThan1Year_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df["NCITZGT1M"]
    df["Count_Person_Incarcerated_Male_MaxSentence1YearOrLess_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df["NCITZLE1M"]
    df["Count_Person_Incarcerated_Male_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_Unsentenced_MeasuredBasedOnCustody"] = df["NCITZUNSM"]
    df["Count_Person_Incarcerated_Male_Under18_MeasuredBasedOnCustody"] = df["CUSLT18M"]
    df["Count_Person_Incarcerated_MeasuredBasedOnJurisdiction"] = df["Female_Total_Temp"] + df["Male_Total_Temp"]
    df["Count_Person_Incarcerated_WhiteAlone_MeasuredBasedOnJurisdiction"] = df["WHITEF"] + df["WHITEM"]
    df["Count_Person_BlackOrAfricanAmericanAlone_Incarcerated_MeasuredBasedOnJurisdiction"] = df["BLACKF"] + df["BLACKM"]
    df["Count_Person_HispanicOrLatino_Incarcerated_MeasuredBasedOnJurisdiction"] = df["HISPF"] + df["HISPM"]
    df["Count_Person_AmericanIndianOrAlaskaNativeAlone_Incarcerated_MeasuredBasedOnJurisdiction"] = df["AIANF"] + df["AIANM"]
    df["Count_Person_AsianAlone_Incarcerated_MeasuredBasedOnJurisdiction"] = df["ASIANF"] + df["ASIANM"]
    df["Count_Person_Incarcerated_NativeHawaiianOrOtherPacificIslanderAlone_MeasuredBasedOnJurisdiction"] = df["NHPIF"] + df["NHPIM"]
    df["Count_Person_Incarcerated_TwoOrMoreRaces_MeasuredBasedOnJurisdiction"] = df["TWORACEF"] + df["TWORACEM"]
    df["Count_MortalityEvent_Incarcerated_MeasuredBasedOnJurisdiction"] = df["DTHTOTF"] + df["DTHTOTM"]
    df["Count_MortalityEvent_Incarcerated_JudicialExecution_MeasuredBasedOnJurisdiction"] = df["DTHEXECF"] + df["DTHEXECM"]
    df["Count_MortalityEvent_IllnessOrNaturalCause_Incarcerated_MeasuredBasedOnJurisdiction"] = df["DTHILLNF"] + df["DTHILLNM"]
    df["Count_MortalityEvent_AIDS_Incarcerated_MeasuredBasedOnJurisdiction"] = df["DTHAIDSF"] + df["DTHAIDSM"]
    df["Count_MortalityEvent_Incarcerated_IntentionalSelf-Harm(Suicide)_MeasuredBasedOnJurisdiction"] = df["DTHSUICF"] + df["DTHSUICM"]
    df["Count_MortalityEvent_Accidents(UnintentionalInjuries)_Incarcerated_MeasuredBasedOnJurisdiction"] = df["DTHACCF"] + df["DTHACCM"]
    df["Count_MortalityEvent_DeathDueToAnotherPerson_Incarcerated_MeasuredBasedOnJurisdiction"] = df["DTHPERSF"] + df["DTHPERSM"]
    df["Count_MortalityEvent_Assault(Homicide)_Incarcerated_MeasuredBasedOnJurisdiction"] = df["DTHHOMIF"] + df["DTHHOMIM"]
    df["Count_MortalityEvent_Incarcerated_NPSOtherCauseOfDeath_MeasuredBasedOnJurisdiction"] = df["DTHOTHF"] + df["DTHOTHM"]
    df["Count_IncarcerationEvent_AdmittedToPrison_Incarcerated_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction"] = df["ADTOTF"] + df["ADTOTM"]
    df["Count_IncarcerationEvent_Incarcerated_MaxSentenceGreaterThan1Year_ReleasedFromPrison_Sentenced_MeasuredBasedOnJurisdiction"] = df["RLTOTF"] + df["RLTOTM"]
    df["Count_Person_Incarcerated_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction"] = df["JURGT1F"] + df["JURGT1M"]
    df["Count_Person_Incarcerated_MaxSentence1YearOrLess_Sentenced_MeasuredBasedOnJurisdiction"] = df["JURLT1F"] + df["JURLT1M"]
    df["Count_Person_Incarcerated_Unsentenced_MeasuredBasedOnJurisdiction"] = df["JURUNSF"] + df["JURUNSM"]
    df["Count_Person_Incarcerated_InState_PrivatelyOperated_MeasuredBasedOnJurisdiction"] = df["PVINF"] + df["PVINM"]
    df["Count_Person_Incarcerated_OutOfState_PrivatelyOperated_MeasuredBasedOnJurisdiction"] = df["PVOTHF"] + df["PVOTHM"]
    df["Count_Person_Incarcerated_Local_LocallyOperated_MeasuredBasedOnJurisdiction"] = df["LFF"] + df["LFM"]
    df["Count_Person_FederallyOperated_Incarcerated_MeasuredBasedOnJurisdiction"] = df["FEDF"] + df["FEDM"]
    df["Count_Person_Incarcerated_OutOfState_StateOperated_MeasuredBasedOnJurisdiction"] = df["OTHSTF"] + df["OTHSTM"]
    df["Count_Person_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df["NCITZTOTF"] + df["NCITZTOTM"]
    df["Count_Person_Incarcerated_MaxSentenceGreaterThan1Year_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df["NCITZGT1F"] + df["NCITZGT1M"]
    df["Count_Person_Incarcerated_MaxSentence1YearOrLess_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df["NCITZLE1F"] + df["NCITZLE1M"]
    df["Count_Person_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_Unsentenced_MeasuredBasedOnCustody"] = df["NCITZUNSF"] + df["NCITZUNSM"]
    df["Count_Person_Incarcerated_Under18_MeasuredBasedOnCustody"] = df["CUSLT18F"] + df["CUSLT18M"]
    
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
    df['GeoId'] = df['STATEID'].apply(convert_geoId)
    
    # convert missing values to NaN for aggregation
    for column_name in list(df.columns):
        df[column_name] = df[column_name].apply(convert_missing_value_to_nan)
    
    #get columns matching stat var names and add aggregate columns
    get_columns(df)
    
    #convert NaN to empty cell
    for column_name in list(df.columns):
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
