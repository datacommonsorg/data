import pandas as pd
from preprocess_data import preprocess_df
from nps_statvar_writer import write_sv
from absl import flags
from absl import app

FLAGS = flags.FLAGS
flags.DEFINE_string('input_file',
                    'NPS_1978-2018_Data.tsv',
                    'file path to tsv file with import data',
                    short_name='i')

AGGREGATE_COLUMNS = [
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
    "Count_Person_Female_Incarcerated_MeasuredBasedOnJurisdiction",
    "Count_Person_Incarcerated_Male_MeasuredBasedOnJurisdiction"
]
FILENAME = 'national_prison_stats'


def generate_tmcf(df):
    template = """
    Node: E:{filename}->E{i}
    typeOf: dcs:StatVarObservation
    variableMeasured: dcs:{stat_var}
    measurementMethod: dcs:{mmethod}
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
                        template.format_map({
                            'i': col_num,
                            'stat_var': col,
                            'filename': FILENAME,
                            'mmethod': 'dcAggregate/NationalPrisonerStatistics'
                        }))
                else:
                    tmcf_f.write(
                        template.format_map({
                            'i': col_num,
                            'stat_var': col,
                            'filename': FILENAME,
                            'mmethod': 'NationalPrisonerStatistics'
                        }))
            col_num += 1


def save_csv(df, filename):
    df.to_csv(filename + '.csv', index=False)


def main(args):
    df = pd.read_csv(FLAGS.input_file, delimiter='\t')
    processed_df = preprocess_df(df)
    save_csv(processed_df, FILENAME)
    generate_tmcf(processed_df)
    f = open("nps_statvars.mcf", "w+")
    write_sv(f)


if __name__ == '__main__':
    app.run(main)
