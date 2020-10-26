import pandas as pd
import argparse
from preprocess_data import preprocess_df
from nps_statvar_writer import write_sv

AGGREGATE_COLUMNS = ["Count_Jurisdiction_WhiteAlone","Count_Jurisdiction_BlackOrAfricanAmericanAlone", "Count_Jurisdiction_HispanicOrLatino",
"Count_Jurisdiction_AmericanIndianOrAlaskaNativeAlone", "Count_Jurisdiction_AsianAlone", "Count_Jurisdiction_NativeHawaiianOrOtherPacificIslanderAlone", "Count_Jurisdiction_TwoOrMoreRaces",
"Count_Jurisdiction_Death", "Count_Jurisdiction_DeathByJudicialExecution", "Count_Jurisdiction_DeathByIllnessOrNaturalCause", "Count_Jurisdiction_DeathByAIDS",
"Count_Jurisdiction_DeathByIntentionalSelf-Harm(Suicide)", "Count_Jurisdiction_DeathByAccidents(UnintentionalInjuries)", "Count_Jurisdiction_DeathByDeathDueToAnotherPerson",
"Count_Jurisdiction_DeathByAssault(Homicide)", "Count_Jurisdiction_DeathByNPSOtherCauseOfDeath", "Count_Jurisdiction_AdmittedToPrison",
"Count_Jurisdiction_ReleasedFromPrison", "Count_Jurisdiction_MaxSentenceGreaterThan1Year", "Count_Jurisdiction_MaxSentence1YearOrLess", "Count_Jurisdiction_Unsentenced",
"Count_Jurisdiction_PrivatelyOperatedInStateFacility", "Count_Jurisdiction_PrivatelyOperatedOutOfStateFacility", "Count_Jurisdiction_LocallyOperatedLocalFacility",
"Count_Jurisdiction_FederalFacility", "Count_Jurisdiction_StateOperatedOutOfStateFacility", "Count_Custody_NotAUSCitizen", "Count_Custody_NotAUSCitizen_MaxSentenceGreaterThan1Year",
"Count_Custody_NotAUSCitizen_MaxSentence1YearOrLess", "Count_Custody_NotAUSCitizen_Unsentenced", "Count_Custody_Under18", "Count_Jurisdiction_Female", "Count_Jurisdiction_Male", "Count_Jurisdiction"]
FILENAME = 'national_prison_stats'

def generate_tmcf(df):
    template_regular = """
    Node: E:{filename}->E{i}
    typeOf: dcs:StatVarObservation
    variableMeasured: dcs:{stat_var}
    measurementMethod: dcs:NationalPrisonerStatistics
    observationAbout: C:{filename}->GeoId
    observationDate: C:{filename}->YEAR
    value: C:{filename}->{stat_var}
    """
                        
    template_aggregate = """
    Node: E:{filename}->E{i}
    typeOf: dcs:StatVarObservation
    variableMeasured: dcs:{stat_var}
    measurementMethod: dcs:dcAggregate/NationalPrisonerStatistics
    observationAbout: C:{filename}->GeoId
    observationDate: C:{filename}->YEAR
    value: C:{filename}->{stat_var}
    """
    
    with open('national_prison_stats.tmcf', 'w') as tmcf_f:
        col_num = 0
        for col in list(df.columns):
            if not col == "GeoId" and not col == "YEAR":
                if col in AGGREGATE_COLUMNS:
                    tmcf_f.write(
                        template_aggregate.format_map({'i': col_num, 'stat_var': col, 'filename': FILENAME}))
                else:
                    tmcf_f.write(
                        template_regular.format_map({'i': col_num, 'stat_var': col, 'filename': FILENAME}))
            col_num += 1
    

def save_csv(df):
    df.to_csv(FILENAME + '.csv', index=False)
    
def main(args):
    filename = args.input_file
    df = pd.read_csv(filename, delimiter='\t')
    processed_df = preprocess_df(df)
    save_csv(processed_df)
    generate_tmcf(processed_df)
    f = open("nps_statvars.mcf","w+")
    write_sv(f)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="NPS Processing Script")
    parser.add_argument('-i',
                        dest='input_file',
                        default='NPS_1978-2018_Data.tsv')
    args = parser.parse_args()

    main(args)