import pandas as pd
from absl import flags
from absl import app

FLAGS = flags.FLAGS
flags.DEFINE_string('preprocess_file',
                    'NPS_1978-2018_Data.tsv',
                    'file path to tsv file with data to proess',
                    short_name='p')


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
    df["Female_Total_Temp"] = df[["JURTOTF", "PVINF_Temp", "PVOTHF_Temp"
                                 ]].sum(axis=1).where(df["PVINCLF"] == 2,
                                                      df["JURTOTF"])
    df["Male_Total_Temp"] = df[["JURTOTM", "PVINM_Temp", "PVOTHM_Temp"
                               ]].sum(axis=1).where(df["PVINCLM"] == 2,
                                                    df["JURTOTM"])
    """calculation to include local facility numbers"""
    df["LFF_Temp"] = df["LFF"].apply(convert_nan_for_calculation)
    df["LFM_Temp"] = df["LFM"].apply(convert_nan_for_calculation)
    df["Female_Total_Temp"] = df[["Female_Total_Temp", "LFF_Temp"
                                 ]].sum(axis=1).where(df["LFINCLF"] == 2,
                                                      df["Female_Total_Temp"])
    df["Male_Total_Temp"] = df[["Male_Total_Temp", "LFM_Temp"
                               ]].sum(axis=1).where(df["LFINCLM"] == 2,
                                                    df["Male_Total_Temp"])
    """calculation to include numbers from local facilities solely to ease crowding"""
    df["LFCRSTF_Temp"] = df["LFCRSTF"].apply(convert_nan_for_calculation)
    df["LFCRSTM_Temp"] = df["LFCRSTM"].apply(convert_nan_for_calculation)
    df["Female_Total_Temp"] = df[["Female_Total_Temp", "LFCRSTF_Temp"
                                 ]].sum(axis=1).where(df["LFCRINCF"] == 2,
                                                      df["Female_Total_Temp"])
    df["Male_Total_Temp"] = df[["Male_Total_Temp", "LFCRSTM_Temp"
                               ]].sum(axis=1).where(df["LFCRINCM"] == 2,
                                                    df["Male_Total_Temp"])
    """calculation to include federal and other state facility numbers"""
    df["FEDF_Temp"] = df["FEDF"].apply(convert_nan_for_calculation)
    df["OTHSTF_Temp"] = df["OTHSTF"].apply(convert_nan_for_calculation)
    df["FEDM_Temp"] = df["FEDM"].apply(convert_nan_for_calculation)
    df["OTHSTM_Temp"] = df["OTHSTM"].apply(convert_nan_for_calculation)
    df["Female_Total_Temp"] = df[[
        "Female_Total_Temp", "FEDF_Temp", "OTHSTF_Temp"
    ]].sum(axis=1).where(df["FACINCLF"] == 2, df["Female_Total_Temp"])
    df["Male_Total_Temp"] = df[["Male_Total_Temp", "FEDM_Temp", "OTHSTM_Temp"
                               ]].sum(axis=1).where(df["FACINCLM"] == 2,
                                                    df["Male_Total_Temp"])


def get_columns(df):
    df_out = {}
    total_jurisdiction_columns_helper(df)
    df_out["GeoId"] = df["GeoId"]
    df_out["YEAR"] = df["YEAR"]
    df_out["Count_Person_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
        "Female_Total_Temp"]
    df_out[
        "Count_Person_Female_Incarcerated_WhiteAlone_MeasuredBasedOnJurisdiction"] = df[
            "WHITEF"]
    df_out[
        "Count_Person_BlackOrAfricanAmericanAlone_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "BLACKF"]
    df_out[
        "Count_Person_Female_HispanicOrLatino_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "HISPF"]
    df_out[
        "Count_Person_AmericanIndianOrAlaskaNativeAlone_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "AIANF"]
    df_out[
        "Count_Person_AsianAlone_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "ASIANF"]
    df_out[
        "Count_Person_Female_Incarcerated_NativeHawaiianOrOtherPacificIslanderAlone_MeasuredBasedOnJurisdiction"] = df[
            "NHPIF"]
    df_out[
        "Count_Person_Female_Incarcerated_TwoOrMoreRaces_MeasuredBasedOnJurisdiction"] = df[
            "TWORACEF"]
    df_out[
        "Count_MortalityEvent_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "DTHTOTF"]
    df_out[
        "Count_MortalityEvent_Female_Incarcerated_JudicialExecution_MeasuredBasedOnJurisdiction"] = df[
            "DTHEXECF"]
    df_out[
        "Count_MortalityEvent_Female_IllnessOrNaturalCause_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "DTHILLNF"]
    df_out[
        "Count_MortalityEvent_AIDS_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "DTHAIDSF"]
    df_out[
        "Count_MortalityEvent_Female_Incarcerated_IntentionalSelf-Harm(Suicide)_MeasuredBasedOnJurisdiction"] = df[
            "DTHSUICF"]
    df_out[
        "Count_MortalityEvent_Accidents(UnintentionalInjuries)_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "DTHACCF"]
    df_out[
        "Count_MortalityEvent_DeathDueToAnotherPerson_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "DTHPERSF"]
    df_out[
        "Count_MortalityEvent_Assault(Homicide)_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "DTHHOMIF"]
    df_out[
        "Count_MortalityEvent_Female_Incarcerated_NPSOtherCauseOfDeath_MeasuredBasedOnJurisdiction"] = df[
            "DTHOTHF"]
    df_out[
        "Count_IncarcerationEvent_AdmittedToPrison_Female_Incarcerated_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction"] = df[
            "ADTOTF"]
    df_out[
        "Count_IncarcerationEvent_Female_Incarcerated_MaxSentenceGreaterThan2Year_ReleasedFromPrison_Sentenced_MeasuredBasedOnJurisdiction"] = df[
            "RLTOTF"]
    df_out[
        "Count_Person_Female_Incarcerated_MaxSentenceGreaterThan2Year_Sentenced_MeasuredBasedOnJurisdiction"] = df[
            "JURGT1F"]
    df_out[
        "Count_Person_Female_Incarcerated_MaxSentence1YearOrLess_Sentenced_MeasuredBasedOnJurisdiction"] = df[
            "JURLT1F"]
    df_out[
        "Count_Person_Female_Incarcerated_Unsentenced_MeasuredBasedOnJurisdiction"] = df[
            "JURUNSF"]
    df_out[
        "Count_Person_Female_Incarcerated_InState_PrivatelyOperated_MeasuredBasedOnJurisdiction"] = df[
            "PVINF"]
    df_out[
        "Count_Person_Female_Incarcerated_OutOfState_PrivatelyOperated_MeasuredBasedOnJurisdiction"] = df[
            "PVOTHF"]
    df_out[
        "Count_Person_Female_Incarcerated_Local_LocallyOperated_MeasuredBasedOnJurisdiction"] = df[
            "LFF"]
    df_out[
        "Count_Person_FederallyOperated_Female_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "FEDF"]
    df_out[
        "Count_Person_Female_Incarcerated_OutOfState_StateOperated_MeasuredBasedOnJurisdiction"] = df[
            "OTHSTF"]
    df_out[
        "Count_Person_Female_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df[
            "NCITZTOTF"]
    df_out[
        "Count_Person_Female_Incarcerated_MaxSentenceGreaterThan2Year_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df[
            "NCITZGT1F"]
    df_out[
        "Count_Person_Female_Incarcerated_MaxSentence1YearOrLess_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df[
            "NCITZLE1F"]
    df_out[
        "Count_Person_Female_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_Unsentenced_MeasuredBasedOnCustody"] = df[
            "NCITZUNSF"]
    df_out[
        "Count_Person_Female_Incarcerated_Under18_MeasuredBasedOnCustody"] = df[
            "CUSLT18F"]
    df_out["Count_Person_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df[
        "Male_Total_Temp"]
    df_out[
        "Count_Person_Incarcerated_Male_WhiteAlone_MeasuredBasedOnJurisdiction"] = df[
            "WHITEM"]
    df_out[
        "Count_Person_BlackOrAfricanAmericanAlone_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df[
            "BLACKM"]
    df_out[
        "Count_Person_HispanicOrLatino_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df[
            "HISPM"]
    df_out[
        "Count_Person_AmericanIndianOrAlaskaNativeAlone_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df[
            "AIANM"]
    df_out[
        "Count_Person_AsianAlone_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df[
            "ASIANM"]
    df_out[
        "Count_Person_Incarcerated_Male_NativeHawaiianOrOtherPacificIslanderAlone_MeasuredBasedOnJurisdiction"] = df[
            "NHPIM"]
    df_out[
        "Count_Person_Incarcerated_Male_TwoOrMoreRaces_MeasuredBasedOnJurisdiction"] = df[
            "TWORACEM"]
    df_out[
        "Count_MortalityEvent_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df[
            "DTHTOTM"]
    df_out[
        "Count_MortalityEvent_Incarcerated_JudicialExecution_Male_MeasuredBasedOnJurisdiction"] = df[
            "DTHEXECM"]
    df_out[
        "Count_MortalityEvent_IllnessOrNaturalCause_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df[
            "DTHILLNM"]
    df_out[
        "Count_MortalityEvent_AIDS_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df[
            "DTHAIDSM"]
    df_out[
        "Count_MortalityEvent_Incarcerated_IntentionalSelf-Harm(Suicide)_Male_MeasuredBasedOnJurisdiction"] = df[
            "DTHSUICM"]
    df_out[
        "Count_MortalityEvent_Accidents(UnintentionalInjuries)_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df[
            "DTHACCM"]
    df_out[
        "Count_MortalityEvent_DeathDueToAnotherPerson_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df[
            "DTHPERSM"]
    df_out[
        "Count_MortalityEvent_Assault(Homicide)_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df[
            "DTHHOMIM"]
    df_out[
        "Count_MortalityEvent_Incarcerated_Male_NPSOtherCauseOfDeath_MeasuredBasedOnJurisdiction"] = df[
            "DTHOTHM"]
    df_out[
        "Count_IncarcerationEvent_AdmittedToPrison_Incarcerated_Male_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction"] = df[
            "ADTOTM"]
    df_out[
        "Count_IncarcerationEvent_Incarcerated_Male_MaxSentenceGreaterThan2Year_ReleasedFromPrison_Sentenced_MeasuredBasedOnJurisdiction"] = df[
            "RLTOTM"]
    df_out[
        "Count_Person_Incarcerated_Male_MaxSentenceGreaterThan2Year_Sentenced_MeasuredBasedOnJurisdiction"] = df[
            "JURGT1M"]
    df_out[
        "Count_Person_Incarcerated_Male_MaxSentence1YearOrLess_Sentenced_MeasuredBasedOnJurisdiction"] = df[
            "JURLT1M"]
    df_out[
        "Count_Person_Incarcerated_Male_Unsentenced_MeasuredBasedOnJurisdiction"] = df[
            "JURUNSM"]
    df_out[
        "Count_Person_Incarcerated_InState_Male_PrivatelyOperated_MeasuredBasedOnJurisdiction"] = df[
            "PVINM"]
    df_out[
        "Count_Person_Incarcerated_Male_OutOfState_PrivatelyOperated_MeasuredBasedOnJurisdiction"] = df[
            "PVOTHM"]
    df_out[
        "Count_Person_Incarcerated_Local_LocallyOperated_Male_MeasuredBasedOnJurisdiction"] = df[
            "LFM"]
    df_out[
        "Count_Person_FederallyOperated_Incarcerated_Male_MeasuredBasedOnJurisdiction"] = df[
            "FEDM"]
    df_out[
        "Count_Person_Incarcerated_Male_OutOfState_StateOperated_MeasuredBasedOnJurisdiction"] = df[
            "OTHSTM"]
    df_out[
        "Count_Person_Incarcerated_Male_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df[
            "NCITZTOTM"]
    df_out[
        "Count_Person_Incarcerated_Male_MaxSentenceGreaterThan2Year_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df[
            "NCITZGT1M"]
    df_out[
        "Count_Person_Incarcerated_Male_MaxSentence1YearOrLess_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df[
            "NCITZLE1M"]
    df_out[
        "Count_Person_Incarcerated_Male_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_Unsentenced_MeasuredBasedOnCustody"] = df[
            "NCITZUNSM"]
    df_out[
        "Count_Person_Incarcerated_Male_Under18_MeasuredBasedOnCustody"] = df[
            "CUSLT18M"]
    df_out["Count_Person_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
        "Female_Total_Temp"] + df["Male_Total_Temp"]
    df_out[
        "Count_Person_Incarcerated_WhiteAlone_MeasuredBasedOnJurisdiction"] = df[
            "WHITEF"] + df["WHITEM"]
    df_out[
        "Count_Person_BlackOrAfricanAmericanAlone_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "BLACKF"] + df["BLACKM"]
    df_out[
        "Count_Person_HispanicOrLatino_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "HISPF"] + df["HISPM"]
    df_out[
        "Count_Person_AmericanIndianOrAlaskaNativeAlone_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "AIANF"] + df["AIANM"]
    df_out[
        "Count_Person_AsianAlone_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "ASIANF"] + df["ASIANM"]
    df_out[
        "Count_Person_Incarcerated_NativeHawaiianOrOtherPacificIslanderAlone_MeasuredBasedOnJurisdiction"] = df[
            "NHPIF"] + df["NHPIM"]
    df_out[
        "Count_Person_Incarcerated_TwoOrMoreRaces_MeasuredBasedOnJurisdiction"] = df[
            "TWORACEF"] + df["TWORACEM"]
    df_out[
        "Count_MortalityEvent_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "DTHTOTF"] + df["DTHTOTM"]
    df_out[
        "Count_MortalityEvent_Incarcerated_JudicialExecution_MeasuredBasedOnJurisdiction"] = df[
            "DTHEXECF"] + df["DTHEXECM"]
    df_out[
        "Count_MortalityEvent_IllnessOrNaturalCause_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "DTHILLNF"] + df["DTHILLNM"]
    df_out[
        "Count_MortalityEvent_AIDS_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "DTHAIDSF"] + df["DTHAIDSM"]
    df_out[
        "Count_MortalityEvent_Incarcerated_IntentionalSelf-Harm(Suicide)_MeasuredBasedOnJurisdiction"] = df[
            "DTHSUICF"] + df["DTHSUICM"]
    df_out[
        "Count_MortalityEvent_Accidents(UnintentionalInjuries)_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "DTHACCF"] + df["DTHACCM"]
    df_out[
        "Count_MortalityEvent_DeathDueToAnotherPerson_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "DTHPERSF"] + df["DTHPERSM"]
    df_out[
        "Count_MortalityEvent_Assault(Homicide)_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "DTHHOMIF"] + df["DTHHOMIM"]
    df_out[
        "Count_MortalityEvent_Incarcerated_NPSOtherCauseOfDeath_MeasuredBasedOnJurisdiction"] = df[
            "DTHOTHF"] + df["DTHOTHM"]
    df_out[
        "Count_IncarcerationEvent_AdmittedToPrison_Incarcerated_MaxSentenceGreaterThan2Year_Sentenced_MeasuredBasedOnJurisdiction"] = df[
            "ADTOTF"] + df["ADTOTM"]
    df_out[
        "Count_IncarcerationEvent_Incarcerated_MaxSentenceGreaterThan1Year_ReleasedFromPrison_Sentenced_MeasuredBasedOnJurisdiction"] = df[
            "RLTOTF"] + df["RLTOTM"]
    df_out[
        "Count_Person_Incarcerated_MaxSentenceGreaterThan2Year_Sentenced_MeasuredBasedOnJurisdiction"] = df[
            "JURGT1F"] + df["JURGT1M"]
    df_out[
        "Count_Person_Incarcerated_MaxSentence1YearOrLess_Sentenced_MeasuredBasedOnJurisdiction"] = df[
            "JURLT1F"] + df["JURLT1M"]
    df_out[
        "Count_Person_Incarcerated_Unsentenced_MeasuredBasedOnJurisdiction"] = df[
            "JURUNSF"] + df["JURUNSM"]
    df_out[
        "Count_Person_Incarcerated_InState_PrivatelyOperated_MeasuredBasedOnJurisdiction"] = df[
            "PVINF"] + df["PVINM"]
    df_out[
        "Count_Person_Incarcerated_OutOfState_PrivatelyOperated_MeasuredBasedOnJurisdiction"] = df[
            "PVOTHF"] + df["PVOTHM"]
    df_out[
        "Count_Person_Incarcerated_Local_LocallyOperated_MeasuredBasedOnJurisdiction"] = df[
            "LFF"] + df["LFM"]
    df_out[
        "Count_Person_FederallyOperated_Incarcerated_MeasuredBasedOnJurisdiction"] = df[
            "FEDF"] + df["FEDM"]
    df_out[
        "Count_Person_Incarcerated_OutOfState_StateOperated_MeasuredBasedOnJurisdiction"] = df[
            "OTHSTF"] + df["OTHSTM"]
    df_out[
        "Count_Person_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df[
            "NCITZTOTF"] + df["NCITZTOTM"]
    df_out[
        "Count_Person_Incarcerated_MaxSentenceGreaterThan2Year_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df[
            "NCITZGT1F"] + df["NCITZGT1M"]
    df_out[
        "Count_Person_Incarcerated_MaxSentence1YearOrLess_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody"] = df[
            "NCITZLE1F"] + df["NCITZLE1M"]
    df_out[
        "Count_Person_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_Unsentenced_MeasuredBasedOnCustody"] = df[
            "NCITZUNSF"] + df["NCITZUNSM"]
    df_out["Count_Person_Incarcerated_Under18_MeasuredBasedOnCustody"] = df[
        "CUSLT18F"] + df["CUSLT18M"]
    return df_out


def rename_columns_to_dcid(df_out):
    df_out = df_out.rename(
        columns={
            'Count_Person_Female_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/lnp5g90fwpct8',
            'Count_Person_Female_Incarcerated_WhiteAlone_MeasuredBasedOnJurisdiction':
                'dc/7g8v95ycwgwgg',
            'Count_Person_BlackOrAfricanAmericanAlone_Female_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/n11nnhnf54h78',
            'Count_Person_Female_HispanicOrLatino_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/4jqzmk4jtzwnb',
            'Count_Person_AmericanIndianOrAlaskaNativeAlone_Female_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/2487zfwx2423d',
            'Count_Person_AsianAlone_Female_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/xefh58ckxwk7b',
            'Count_Person_Female_Incarcerated_NativeHawaiianOrOtherPacificIslanderAlone_MeasuredBasedOnJurisdiction':
                'dc/6xg0t3qjdtqn5',
            'Count_Person_Female_Incarcerated_TwoOrMoreRaces_MeasuredBasedOnJurisdiction':
                'dc/4x1jbp34f4085',
            'Count_MortalityEvent_Female_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/gb0b3cwxyfsh9',
            'Count_MortalityEvent_Female_Incarcerated_JudicialExecution_MeasuredBasedOnJurisdiction':
                'dc/jh0nks36n1jc1',
            'Count_MortalityEvent_Female_IllnessOrNaturalCause_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/mjqlm4q2efmvh',
            'Count_MortalityEvent_AIDS_Female_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/qnnbzwrjn50jh',
            'Count_MortalityEvent_Female_Incarcerated_IntentionalSelf-Harm(Suicide)_MeasuredBasedOnJurisdiction':
                'dc/shgj6xwg96pp3',
            'Count_MortalityEvent_Accidents(UnintentionalInjuries)_Female_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/6dqm6n76jg2gc',
            'Count_MortalityEvent_DeathDueToAnotherPerson_Female_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/59k03h1hvxp89',
            'Count_MortalityEvent_Assault(Homicide)_Female_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/q2pgyz35p79l4',
            'Count_MortalityEvent_Female_Incarcerated_NPSOtherCauseOfDeath_MeasuredBasedOnJurisdiction':
                'dc/pwpgqvlz3zxtc',
            'Count_IncarcerationEvent_AdmittedToPrison_Female_Incarcerated_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction':
                'dc/36d93ckypx3bb',
            'Count_IncarcerationEvent_Female_Incarcerated_MaxSentenceGreaterThan2Year_ReleasedFromPrison_Sentenced_MeasuredBasedOnJurisdiction':
                'dc/4lq5grhwyrle2',
            'Count_Person_Female_Incarcerated_MaxSentenceGreaterThan2Year_Sentenced_MeasuredBasedOnJurisdiction':
                'dc/ylynnzg5215wf',
            'Count_Person_Female_Incarcerated_MaxSentence1YearOrLess_Sentenced_MeasuredBasedOnJurisdiction':
                'dc/7j909grsehbn1',
            'Count_Person_Female_Incarcerated_Unsentenced_MeasuredBasedOnJurisdiction':
                'dc/m5ltqeg1src',
            'Count_Person_Female_Incarcerated_InState_PrivatelyOperated_MeasuredBasedOnJurisdiction':
                'dc/5s1ytn01dxpn4',
            'Count_Person_Female_Incarcerated_OutOfState_PrivatelyOperated_MeasuredBasedOnJurisdiction':
                'dc/wcl0fysjk3cdf',
            'Count_Person_Female_Incarcerated_Local_LocallyOperated_MeasuredBasedOnJurisdiction':
                'dc/dd1ngpwxrfq8c',
            'Count_Person_FederallyOperated_Female_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/10d542rs75l3g',
            'Count_Person_Female_Incarcerated_OutOfState_StateOperated_MeasuredBasedOnJurisdiction':
                'dc/y7jvz4e4ln1w5',
            'Count_Person_Female_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody':
                'dc/nwmssnmerhgq2',
            'Count_Person_Female_Incarcerated_MaxSentenceGreaterThan2Year_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody':
                'dc/z4ej4lkyk7kg3',
            'Count_Person_Female_Incarcerated_MaxSentence1YearOrLess_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody':
                'dc/vhl29th29q708',
            'Count_Person_Female_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_Unsentenced_MeasuredBasedOnCustody':
                'dc/07rw0lsvkv1ld',
            'Count_Person_Female_Incarcerated_Under18_MeasuredBasedOnCustody':
                'dc/c17kzp0zrfkq9',
            'Count_Person_Incarcerated_Male_MeasuredBasedOnJurisdiction':
                'dc/03l0q0wyqrk39',
            'Count_Person_Incarcerated_Male_WhiteAlone_MeasuredBasedOnJurisdiction':
                'dc/yneg81m4e49z6',
            'Count_Person_BlackOrAfricanAmericanAlone_Incarcerated_Male_MeasuredBasedOnJurisdiction':
                'dc/ptp31y11913b6',
            'Count_Person_HispanicOrLatino_Incarcerated_Male_MeasuredBasedOnJurisdiction':
                'dc/ck1emtds61j27',
            'Count_Person_AmericanIndianOrAlaskaNativeAlone_Incarcerated_Male_MeasuredBasedOnJurisdiction':
                'dc/dxq7vxxwvp7pg',
            'Count_Person_AsianAlone_Incarcerated_Male_MeasuredBasedOnJurisdiction':
                'dc/2s9jqlpe84dk',
            'Count_Person_Incarcerated_Male_NativeHawaiianOrOtherPacificIslanderAlone_MeasuredBasedOnJurisdiction':
                'dc/03ewbkyh6zey2',
            'Count_Person_Incarcerated_Male_TwoOrMoreRaces_MeasuredBasedOnJurisdiction':
                'dc/lk9fd4v63ke94',
            'Count_MortalityEvent_Incarcerated_Male_MeasuredBasedOnJurisdiction':
                'dc/6xlk95n27cn23',
            'Count_MortalityEvent_Incarcerated_JudicialExecution_Male_MeasuredBasedOnJurisdiction':
                'dc/28nfbs113meqb',
            'Count_MortalityEvent_IllnessOrNaturalCause_Incarcerated_Male_MeasuredBasedOnJurisdiction':
                'dc/88znpts47dszb',
            'Count_MortalityEvent_AIDS_Incarcerated_Male_MeasuredBasedOnJurisdiction':
                'dc/zgct0hgv0l8zf',
            'Count_MortalityEvent_Incarcerated_IntentionalSelf-Harm(Suicide)_Male_MeasuredBasedOnJurisdiction':
                'dc/ep052e5d1p2t4',
            'Count_MortalityEvent_Accidents(UnintentionalInjuries)_Incarcerated_Male_MeasuredBasedOnJurisdiction':
                'dc/b0npgpvp37mvf',
            'Count_MortalityEvent_DeathDueToAnotherPerson_Incarcerated_Male_MeasuredBasedOnJurisdiction':
                'dc/3zy5zptr0tsmg',
            'Count_MortalityEvent_Assault(Homicide)_Incarcerated_Male_MeasuredBasedOnJurisdiction':
                'dc/z29z7w7ldnwl4',
            'Count_MortalityEvent_Incarcerated_Male_NPSOtherCauseOfDeath_MeasuredBasedOnJurisdiction':
                'dc/92sfrvdv82jh9',
            'Count_IncarcerationEvent_AdmittedToPrison_Incarcerated_Male_MaxSentenceGreaterThan1Year_Sentenced_MeasuredBasedOnJurisdiction':
                'dc/ttms13r578hq9',
            'Count_IncarcerationEvent_Incarcerated_Male_MaxSentenceGreaterThan2Year_ReleasedFromPrison_Sentenced_MeasuredBasedOnJurisdiction':
                'dc/31mgfjs08le08',
            'Count_Person_Incarcerated_Male_MaxSentenceGreaterThan2Year_Sentenced_MeasuredBasedOnJurisdiction':
                'dc/xph62e8xwqzl2',
            'Count_Person_Incarcerated_Male_MaxSentence1YearOrLess_Sentenced_MeasuredBasedOnJurisdiction':
                'dc/hjfp0fkfn6ps1',
            'Count_Person_Incarcerated_Male_Unsentenced_MeasuredBasedOnJurisdiction':
                'dc/cb1jtf8j55xx9',
            'Count_Person_Incarcerated_InState_Male_PrivatelyOperated_MeasuredBasedOnJurisdiction':
                'dc/3bz5n6t83nqv1',
            'Count_Person_Incarcerated_Male_OutOfState_PrivatelyOperated_MeasuredBasedOnJurisdiction':
                'dc/yvzmwphpsbbgf',
            'Count_Person_Incarcerated_Local_LocallyOperated_Male_MeasuredBasedOnJurisdiction':
                'dc/zh1v0wmmnxzjg',
            'Count_Person_FederallyOperated_Incarcerated_Male_MeasuredBasedOnJurisdiction':
                'dc/e718gzyclkcq8',
            'Count_Person_Incarcerated_Male_OutOfState_StateOperated_MeasuredBasedOnJurisdiction':
                'dc/y0brw153k6b48',
            'Count_Person_Incarcerated_Male_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody':
                'dc/shejk69d4k3fh',
            'Count_Person_Incarcerated_Male_MaxSentenceGreaterThan2Year_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody':
                'dc/7kgw0qhgglyz1',
            'Count_Person_Incarcerated_Male_MaxSentence1YearOrLess_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody':
                'dc/yrtlkk1jxj286',
            'Count_Person_Incarcerated_Male_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_Unsentenced_MeasuredBasedOnCustody':
                'dc/g7yg16710b0x8',
            'Count_Person_Incarcerated_Male_Under18_MeasuredBasedOnCustody':
                'dc/t14epl3f66wn',
            'Count_Person_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/hxsdmw575en24',
            'Count_Person_Incarcerated_WhiteAlone_MeasuredBasedOnJurisdiction':
                'dc/wp843855b1r4c',
            'Count_Person_BlackOrAfricanAmericanAlone_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/0tn58fc77r0z6',
            'Count_Person_HispanicOrLatino_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/zdb0f7sj2419d',
            'Count_Person_AmericanIndianOrAlaskaNativeAlone_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/fs27m9j4vpvc7',
            'Count_Person_AsianAlone_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/yksgwhwsbtv9c',
            'Count_Person_Incarcerated_NativeHawaiianOrOtherPacificIslanderAlone_MeasuredBasedOnJurisdiction':
                'dc/510pv6eq2vtw7',
            'Count_Person_Incarcerated_TwoOrMoreRaces_MeasuredBasedOnJurisdiction':
                'dc/rmwl11tzy7vkh',
            'Count_MortalityEvent_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/67ttwfn9dswch',
            'Count_MortalityEvent_Incarcerated_JudicialExecution_MeasuredBasedOnJurisdiction':
                'dc/xewq6n5r3nzch',
            'Count_MortalityEvent_IllnessOrNaturalCause_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/3s7lndm5j3wp4',
            'Count_MortalityEvent_AIDS_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/tn5kxlgy0shl4',
            'Count_MortalityEvent_Incarcerated_IntentionalSelf-Harm(Suicide)_MeasuredBasedOnJurisdiction':
                'dc/jte92xq8qsgtd',
            'Count_MortalityEvent_Accidents(UnintentionalInjuries)_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/80wsxnfj3secc',
            'Count_MortalityEvent_DeathDueToAnotherPerson_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/nz8kmke5yqvn',
            'Count_MortalityEvent_Assault(Homicide)_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/jtf63bh66k41g',
            'Count_MortalityEvent_Incarcerated_NPSOtherCauseOfDeath_MeasuredBasedOnJurisdiction':
                'dc/3kk4xws30zxlb',
            'Count_IncarcerationEvent_AdmittedToPrison_Incarcerated_MaxSentenceGreaterThan2Year_Sentenced_MeasuredBasedOnJurisdiction':
                'dc/62pg70d2beyh9',
            'Count_IncarcerationEvent_Incarcerated_MaxSentenceGreaterThan1Year_ReleasedFromPrison_Sentenced_MeasuredBasedOnJurisdiction':
                'dc/ljrjkp31x9ny2',
            'Count_Person_Incarcerated_MaxSentenceGreaterThan2Year_Sentenced_MeasuredBasedOnJurisdiction':
                'dc/g68w8e5hk1w2b',
            'Count_Person_Incarcerated_MaxSentence1YearOrLess_Sentenced_MeasuredBasedOnJurisdiction':
                'dc/y01295f7b38n1',
            'Count_Person_Incarcerated_Unsentenced_MeasuredBasedOnJurisdiction':
                'dc/e3jblh1b616b5',
            'Count_Person_Incarcerated_InState_PrivatelyOperated_MeasuredBasedOnJurisdiction':
                'dc/n92hgh8ned7k5',
            'Count_Person_Incarcerated_OutOfState_PrivatelyOperated_MeasuredBasedOnJurisdiction':
                'dc/qgv9d3frn35qc',
            'Count_Person_Incarcerated_Local_LocallyOperated_MeasuredBasedOnJurisdiction':
                'dc/r5ebll5x2zxfg',
            'Count_Person_FederallyOperated_Incarcerated_MeasuredBasedOnJurisdiction':
                'dc/0mz1rg7mm3y66',
            'Count_Person_Incarcerated_OutOfState_StateOperated_MeasuredBasedOnJurisdiction':
                'dc/91vy0sf20wlg9',
            'Count_Person_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody':
                'dc/b3jgznxenlrm2',
            'Count_Person_Incarcerated_MaxSentenceGreaterThan2Year_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody':
                'dc/ryhy4qxqv6hg6',
            'Count_Person_Incarcerated_MaxSentence1YearOrLess_NotAUSCitizen_Sentenced_StateOperated&FederallyOperated&PrivatelyOperated_MeasuredBasedOnCustody':
                'dc/x0l8799rm6xg4',
            'Count_Person_Incarcerated_NotAUSCitizen_StateOperated&FederallyOperated&PrivatelyOperated_Unsentenced_MeasuredBasedOnCustody':
                'dc/eergc1rzgq61b',
            'Count_Person_Incarcerated_Under18_MeasuredBasedOnCustody':
                'dc/z6w4rxbxb4eg8'
        })
    return df_out


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
    df_out = pd.DataFrame(get_columns(df))

    #get dcid for the stat var names
    df_out = pd.DataFrame(rename_columns_to_dcid(df_out))

    #convert NaN to empty cell
    for column_name in list(df_out.columns):
        df_out[column_name] = df_out[column_name].apply(
            convert_nan_to_empty_cell)

    return df_out


def main(args):
    filename = FLAGS.preprocess_file
    print('Processing {0}'.format(filename))
    df = pd.read_csv(filename, delimiter='\t')
    processed_df = preprocess_df(df)
    processed_df.to_csv(filename.replace('.tsv', '_processed.csv'), index=False)
    print('Done processing {0}'.format(filename))


if __name__ == '__main__':
    app.run(main)
