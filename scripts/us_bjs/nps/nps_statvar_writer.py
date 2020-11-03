NO_GENDER = "Both"
POPULATIONTYPE_PERSON = "Person"
POPULATIONTYPE_DEATH = "MortalityEvent"
POPULATIONTYPE_INCARCERATION = "IncarcerationEvent"
GENDERS = ["Female", "Male", NO_GENDER]
RACES = [
    "WhiteAlone", "BlackOrAfricanAmericanAlone", "HispanicOrLatino",
    "AmericanIndianOrAlaskaNativeAlone", "AsianAlone",
    "NativeHawaiianOrOtherPacificIslanderAlone", "TwoOrMoreRaces"
]
CAUSES_OF_DEATH = [
    "JudicialExecution", "IllnessOrNaturalCause", "AIDS",
    "IntentionalSelf-Harm(Suicide)", "Accidents(UnintentionalInjuries)",
    "DeathDueToAnotherPerson", "Assault(Homicide)", "NPSOtherCauseOfDeath"
]
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
        props.append("gender: schema:" + gender)
    props.append("populationType: dcs:" + population_type)
    props.append("measurementQualifier: dcs:" + measurement_qualifier)
    props.append("typeOf: dcs:StatisticalVariable")
    props.append("institutionalization: dcs:Incarcerated")
    props.append("statType: dcs:measuredValue")
    props.append("measuredProperty: dcs:Count")
    props.append("")
    return props


def get_title(properties, pop_type, gender, mqualifier):
    template = """Node: dcid:Count_{pop_type}_{properties}_{mqualifier}"""
    props = []
    if not gender == NO_GENDER:
        props.append(gender)
    props.extend(properties)
    props.append("Incarcerated")
    props = sorted(props, key=str.lower)
    prop_string = '_'.join(props)
    return template.format_map({
        'pop_type': pop_type,
        'properties': prop_string,
        'mqualifier': mqualifier
    })


def get_sentencing_properties(sentence_type):
    props = []
    prop_values = []
    if (sentence_type == UNSENTENCED):
        props.append("prisonSentenceStatus: dcs:Unsentenced")
        prop_values.append("Unsentenced")
    elif (sentence_type == SENTENCED_OVER_1_YEAR):
        props.append("prisonSentenceStatus: dcs:Sentenced")
        props.append("maxPrisonSentence: [2 - Years]")
        prop_values.append("Sentenced")
        prop_values.append("MaxSentenceGreaterThan1Year")
    elif (sentence_type == SENTENCED_UNDER_1_YEAR):
        props.append("prisonSentenceStatus: dcs:Sentenced")
        props.append("maxPrisonSentence: [- 1 Years]")
        prop_values.append("Sentenced")
        prop_values.append("MaxSentence1YearOrLess")
    return props, prop_values


def get_jurisdiction_sv(gender):
    props = []
    props.append(get_title([], POPULATIONTYPE_PERSON, gender, JURISDICTION))
    props.extend(
        get_constant_properties(gender, POPULATIONTYPE_PERSON, JURISDICTION))
    for race in RACES:
        props.append(
            get_title([race], POPULATIONTYPE_PERSON, gender, JURISDICTION))
        props.append("race: dcs:" + race)
        props.extend(
            get_constant_properties(gender, POPULATIONTYPE_PERSON,
                                    JURISDICTION))
    return props


def get_death_sv(gender):
    props = []
    props.append(get_title([], POPULATIONTYPE_DEATH, gender, JURISDICTION))
    props.extend(
        get_constant_properties(gender, POPULATIONTYPE_DEATH, JURISDICTION))
    for cause in CAUSES_OF_DEATH:
        props.append(
            get_title([cause], POPULATIONTYPE_DEATH, gender, JURISDICTION))
        props.append("causeOfDeath: dcs:" + cause)
        props.extend(
            get_constant_properties(gender, POPULATIONTYPE_DEATH, JURISDICTION))
    return props


def get_incarceration_events_sv(gender):
    props = []
    for event in INCARCERATION_EVENTS:
        sentencing_props, prop_values = get_sentencing_properties(
            SENTENCED_OVER_1_YEAR)
        prop_values.append(event)
        props.append(
            get_title(prop_values, POPULATIONTYPE_INCARCERATION, gender,
                      JURISDICTION))
        props.append("eventType: dcs:" + event)
        props.extend(sentencing_props)
        props.extend(
            get_constant_properties(gender, POPULATIONTYPE_INCARCERATION,
                                    JURISDICTION))
    return props


def get_sentencing_sv(gender):
    props = []
    for sentence in SENTENCE_AMOUNTS:
        sentencing_props, prop_values = get_sentencing_properties(sentence)
        props.append(
            get_title(prop_values, POPULATIONTYPE_PERSON, gender, JURISDICTION))
        props.extend(sentencing_props)
        props.extend(
            get_constant_properties(gender, POPULATIONTYPE_PERSON,
                                    JURISDICTION))
    return props


def get_correctional_facility_sv(gender, operator, location):
    props = []
    prop_values = []
    if operator is not None:
        props.append("correctionalFacilityOperator: dcs:" + operator)
        prop_values.append(operator)
    if location is not None:
        props.append("correctionalFacilityLocation: dcs:" + location)
        prop_values.append(location)
    props.extend(
        get_constant_properties(gender, POPULATIONTYPE_PERSON, JURISDICTION))
    result = [
        get_title(prop_values, POPULATIONTYPE_PERSON, gender, JURISDICTION)
    ]
    result.extend(props)
    return result


def non_us_citizen_constant_props(gender):
    props = []
    prop_values = []
    props.append("citizenship: dcs:NotAUSCitizen")
    prop_values.append("NotAUSCitizen")
    props.append(
        "correctionalFacilityOperator: dcs:StateOperated&FederallyOperated&PrivatelyOperated"
    )
    prop_values.append("StateOperated&FederallyOperated&PrivatelyOperated")
    props.extend(get_constant_properties(gender, POPULATIONTYPE_PERSON,
                                         CUSTODY))
    return props, prop_values


def get_non_us_citizen_sv(gender):
    props = []
    non_us_citizen_props, prop_values = non_us_citizen_constant_props(gender)
    props.append(get_title(prop_values, POPULATIONTYPE_PERSON, gender, CUSTODY))
    props.extend(non_us_citizen_props)
    for sentence in SENTENCE_AMOUNTS:
        sentencing_props, sentencing_prop_values = get_sentencing_properties(
            sentence)
        temp_prop_vals = []
        temp_prop_vals.extend(prop_values)
        temp_prop_vals.extend(sentencing_prop_values)
        props.append(
            get_title(temp_prop_vals, POPULATIONTYPE_PERSON, gender, CUSTODY))
        props.extend(sentencing_props)
        props.extend(non_us_citizen_props)
    return props


def get_under_18_sv(gender):
    props = []
    props.append(get_title(["Under18"], POPULATIONTYPE_PERSON, gender, CUSTODY))
    props.append("age: [0 17 Years]")
    props.extend(get_constant_properties(gender, POPULATIONTYPE_PERSON,
                                         CUSTODY))
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
        result.extend(
            get_correctional_facility_sv(gender, "PrivatelyOperated",
                                         "InState"))
        result.extend(
            get_correctional_facility_sv(gender, "PrivatelyOperated",
                                         "OutOfState"))
        result.extend(
            get_correctional_facility_sv(gender, "LocallyOperated", "Local"))
        result.extend(
            get_correctional_facility_sv(gender, "FederallyOperated", None))
        result.extend(
            get_correctional_facility_sv(gender, "StateOperated", "OutOfState"))
        result.extend(get_non_us_citizen_sv(gender))
        """under 18"""
        result.extend(get_under_18_sv(gender))
    result = "\n".join(result)
    f.write(result)


def main():
    f = open("nps_statvars.mcf", "w+")
    write_sv(f)


if __name__ == '__main__':
    main()
