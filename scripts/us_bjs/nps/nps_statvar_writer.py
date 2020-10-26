NO_GENDER = "Both"
POPULATIONTYPE_PERSON = "Person"
POPULATIONTYPE_DEATH = "MortalityEvent"
POPULATIONTYPE_INCARCERATION = "IncarcerationEvent"
GENDERS = ["Female", "Male", "Both"]
RACES = ["WhiteAlone", "BlackOrAfricanAmericanAlone", "HispanicOrLatino", "AmericanIndianOrAlaskaNativeAlone", "AsianAlone","NativeHawaiianOrOtherPacificIslanderAlone", "TwoOrMoreRaces"]
CAUSES_OF_DEATH = ["JudicialExecution", "IllnessOrNaturalCause", "AIDS", "IntentionalSelf-Harm(Suicide)", "Accidents(UnintentionalInjuries)", "DeathDueToAnotherPerson", "Assault(Homicide)", "NPSOtherCauseOfDeath"]
INCARCERATION_EVENTS = ["AdmittedToPrison", "ReleasedFromPrison"]
SENTENCED_OVER_1_YEAR = "MaxSentenceGreaterThan1Year"
SENTENCED_UNDER_1_YEAR = "MaxSentence1YearOrLess"
UNSENTENCED = "Unsentenced"
SENTENCE_AMOUNTS = [SENTENCED_OVER_1_YEAR, SENTENCED_UNDER_1_YEAR, UNSENTENCED]
JURISDICTION = "MeasuredBasedOnJurisdiction"
CUSTODY = "MeasuredBasedOnCustody"
    
def get_constant_properties(gender, population_type, measurement_qualifier):
    """gets list of properties needed for all stat vars

    Args:
        gender: gender of stat var as string
        population_type: population type of stat var as string
        measurement_qualifier: measurement qualifier of stat var as string
    
    Returns:
        list of strings where each string is an individual property
    """
    props = []
    if not gender == NO_GENDER:
        props.append("gender: schema:" + gender + "\n")
    props.append("populationType: dcs:" + population_type + "\n")
    props.append("measurementQualifier: dcs:" + measurement_qualifier + "\n")
    props.append("typeOf: dcs:StatisticalVariable\n")
    props.append("institutionalization: dcs:Incarcerated\n")
    props.append("statType: dcs:measuredValue\n")
    props.append("measuredProperty: dcs:Count\n")
    props.append("\n")
    return props

def get_title(sv_title, gender):
    if gender == NO_GENDER:
        return "Node: dcid:" + sv_title + "\n"
    else:
        return "Node: dcid:" + sv_title + "_" + gender + "\n"

def get_sentencing_properties(sentence_type):
    props = []
    if (sentence_type == UNSENTENCED):
        props.append("prisonSentenceStatus: dcs:Unsentenced\n")
    elif (sentence_type == SENTENCED_OVER_1_YEAR):
        props.append("prisonSentenceStatus: dcs:Sentenced\n")
        props.append("maxPrisonSentence: [2 - Years]\n")
    elif (sentence_type == SENTENCED_UNDER_1_YEAR):
        props.append("prisonSentenceStatus: dcs:Sentenced\n")
        props.append("maxPrisonSentence: [- 1 Years]\n")
    return props

def get_jurisdiction_sv(gender):
    props = []
    props.append(get_title("Count_Jurisdiction", gender))
    props.extend(get_constant_properties(gender, POPULATIONTYPE_PERSON, JURISDICTION))
    for race in RACES:
        props.append(get_title("Count_Jurisdiction_" + race, gender))
        props.append("race: dcs:" + race + "\n")
        props.extend(get_constant_properties(gender, POPULATIONTYPE_PERSON, JURISDICTION))
    return props

def get_death_sv(gender):
    props = []
    props.append(get_title("Count_Jurisdiction_Death", gender))
    props.extend(get_constant_properties(gender, POPULATIONTYPE_DEATH, JURISDICTION))
    for cause in CAUSES_OF_DEATH:
        props.append(get_title("Count_Jurisdiction_DeathBy" + cause, gender))
        props.append("causeOfDeath: dcs:" + cause + "\n")
        props.extend(get_constant_properties(gender, POPULATIONTYPE_DEATH, JURISDICTION))
    return props
    
def get_incarceration_events_sv(gender):
    props = []
    for event in INCARCERATION_EVENTS:
        props.append(get_title("Count_Jurisdiction_" + event, gender))
        props.append("eventType: dcs:" + event + "\n")
        props.extend(get_sentencing_properties(SENTENCED_OVER_1_YEAR))
        props.extend(get_constant_properties(gender, POPULATIONTYPE_INCARCERATION, JURISDICTION))
    return props

def get_sentencing_sv(gender):
    props = []
    for sentence in SENTENCE_AMOUNTS:
        props.append(get_title("Count_Jurisdiction_" + sentence, gender))
        props.extend(get_sentencing_properties(sentence))
        props.extend(get_constant_properties(gender, POPULATIONTYPE_PERSON, JURISDICTION))
    return props

def get_correctional_facility_sv(gender, operator, location):
    props = []
    props.append(get_title("Count_Jurisdiction_" + operator + location + "Facility", gender))
    if not operator is "":
        props.append("correctionalFacilityOperator: dcs:" + operator + "\n")
    if not location is "":
        props.append("correctionalFacilityLocation: dcs:" + location + "\n")
    props.extend(get_constant_properties(gender, POPULATIONTYPE_PERSON, JURISDICTION))
    return props

def non_us_citizen_constant_props(gender):
    props = []
    props.append("citizenship: dcs:NotAUSCitizen\n")
    props.append("correctionalFacilityOperator: dcs:StateOperated&FederallyOperated&PrivatelyOperated\n")
    props.extend(get_constant_properties(gender, POPULATIONTYPE_PERSON, CUSTODY))
    return props
    
def get_non_us_citizen_sv(gender):
    props = []
    props.append(get_title("Count_Custody_NotAUSCitizen", gender))
    props.extend(non_us_citizen_constant_props(gender))
    for sentence in SENTENCE_AMOUNTS:
        props.append(get_title("Count_Custody_NotAUSCitizen_" + sentence, gender))
        props.extend(get_sentencing_properties(sentence))
        props.extend(non_us_citizen_constant_props(gender))
    return props

def get_under_18_sv(gender):
    props = []
    props.append(get_title("Count_Custody_Under18", gender))
    props.append("age: [0 17 Years]\n")
    props.extend(get_constant_properties(gender, POPULATIONTYPE_PERSON, CUSTODY))
    return props

def write_sv(f):
    """writes stat vars to file

    Args:
        f: file to write to
    """
    result = []
    for gender in GENDERS:
        result.extend(get_jurisdiction_sv(gender))
        result.extend(get_death_sv(gender))
        result.extend(get_incarceration_events_sv(gender))
        result.extend(get_sentencing_sv(gender))
        result.extend(get_correctional_facility_sv(gender, "PrivatelyOperated", "InState"))
        result.extend(get_correctional_facility_sv(gender, "PrivatelyOperated", "OutOfState"))
        result.extend(get_correctional_facility_sv(gender, "LocallyOperated", "Local"))
        result.extend(get_correctional_facility_sv(gender, "FederallyOperated", ""))
        result.extend(get_correctional_facility_sv(gender, "StateOperated", "OutOfState"))
        result.extend(get_non_us_citizen_sv(gender))
        """under 18"""
        result.extend(get_under_18_sv(gender))
    result = ''.join(result)
    f.write(result)
        
def main():
    f = open("nps_statvars.mcf","w+")
    write_sv(f)

if __name__ == '__main__':
    main()
