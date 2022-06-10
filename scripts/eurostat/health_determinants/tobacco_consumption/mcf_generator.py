def smoking_tobaccoproducts_education_attainment_level() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Educational Attainment\n"
        "statType: dcs:measuredValue\n"
        "healthbehaviour: dcs:{healthbehaviour}\n"
        "{gender}{educationalAttainment}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for healthbehaviour in [
                'NonSmoker', 'DailySmoker', 'CurrentSmoker', 'OccasionalSmoker'
        ]:
            for educationalAttainment in [
                    'AllISCED2011Levels',
                    'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                    'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                    'TertiaryEducation'
            ]:
                Node = "Count_Person_" + educationalAttainment + "_" + gender + "_" + "SmokingTobaccoProducts" + "_" + healthbehaviour + "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_educationalAttainment = f"educationalAttainment: dcs:{educationalAttainment}\n"
                if educationalAttainment == "AllISCED2011Levels":
                    Node = Node.replace("_AllISCED2011Levels", "")
                    f_educationalAttainment = ""
                mcf += template_mcf.format(
                    Node=Node,
                    gender=f_gender,
                    healthbehaviour=healthbehaviour,
                    educationalAttainment=f_educationalAttainment)
    return mcf


def smoking_tobaccoproducts_income_quintile() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Income Quintile\n"
        "statType: dcs:measuredValue\n"
        "healthbehaviour: dcs:{healthbehaviour}\n"
        "{gender}{quant_inc}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for healthbehaviour in [
                'NonSmoker', 'DailySmoker', 'CurrentSmoker', 'OccasionalSmoker'
        ]:
            for quant_inc in [
                    'Total', 'FirstQuintile', 'SecondQuintile', 'ThirdQuintile',
                    'FourthQuintile', 'FifthQuintile'
            ]:
                Node = "Count_Person_" + quant_inc + "_" + gender + "_" + "SmokingTobaccoProducts" + "_" + healthbehaviour + "_AsAFractionOf_" + "Count_Person_" + quant_inc + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_quant_inc = f"quant_inc: dcs:{quant_inc}\n"
                if quant_inc == "Total":
                    Node = Node.replace("_Total", "")
                    f_quant_inc = ""
                mcf += template_mcf.format(Node=Node,
                                           gender=f_gender,
                                           healthbehaviour=healthbehaviour,
                                           quant_inc=f_quant_inc)
    return mcf


def smoking_tobaccoproducts_degree_of_urbanisation() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Degree of Urbanisation\n"
        "healthbehaviour: dcs:{healthbehaviour}\n"
        "{deg_urb}{gender}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for healthbehaviour in [
                'NonSmoker', 'DailySmoker', 'CurrentSmoker', 'OccasionalSmoker'
        ]:
            for deg_urb in ['Total', 'Cities', 'TownsAndSuburbs', 'RuralAreas']:
                Node = "Count_Person_" + deg_urb + "_" + gender + "_" + "SmokingTobaccoProducts" + "_" + healthbehaviour + "_AsAFractionOf_" + "Count_Person_" + deg_urb + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_deg_urb = f"deg_urb: dcs:{deg_urb}\n"
                if deg_urb == "Total":
                    Node = Node.replace("_Total", "")
                    f_deg_urb = ""
                mcf += template_mcf.format(Node=Node,
                                           gender=f_gender,
                                           healthbehaviour=healthbehaviour,
                                           deg_urb=f_deg_urb)
    return mcf


def daily_smokers_cigarettes_education_attainment_level() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Educational Attainment\n"
        "statType: dcs:measuredValue\n"
        "{gender}{educationalAttainment}{healthbehaviour}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for healthbehaviour in [
                'Total', 'LessThan20CigarettesPerDay',
                '20OrMoreCigarettesPerDay'
        ]:
            for educationalAttainment in [
                    'AllISCED2011Levels',
                    'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                    'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                    'TertiaryEducation'
            ]:
                Node = "Count_Person_" + educationalAttainment + "_" + gender + "_" + "DailySmokerCigarettes" + "_" + healthbehaviour + "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_educationalAttainment = f"educationalAttainment: dcs:{educationalAttainment}\n"
                if educationalAttainment == "AllISCED2011Levels":
                    Node = Node.replace("_AllISCED2011Levels", "")
                    f_educationalAttainment = ""

                f_healthbehaviour = f"healthbehaviour: dcs:{healthbehaviour}\n"
                if healthbehaviour == "Total":
                    Node = Node.replace("_Total", "")
                    f_healthbehaviour = ""
                mcf += template_mcf.format(
                    Node=Node,
                    gender=f_gender,
                    healthbehaviour=f_healthbehaviour,
                    educationalAttainment=f_educationalAttainment)
    return mcf


def daily_smokers_cigarettes_income_quintile() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Income Quintile\n"
        "statType: dcs:measuredValue\n"
        "{healthbehaviour}{gender}{quant_inc}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for healthbehaviour in [
                'Total', 'LessThan20CigarettesPerDay',
                '20OrMoreCigarettesPerDay'
        ]:
            for quant_inc in [
                    'Total', 'FirstQuintile', 'SecondQuintile', 'ThirdQuintile',
                    'FourthQuintile', 'FifthQuintile'
            ]:
                Node = "Count_Person_" + quant_inc + "_" + gender + "_" + "DailySmokerCigarettes" + "_" + healthbehaviour + "_AsAFractionOf_" + "Count_Person_" + quant_inc + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_quant_inc = f"quant_inc: dcs:{quant_inc}\n"
                if quant_inc == "Total":
                    Node = Node.replace("_Total", "")
                    f_quant_inc = ""

                f_healthbehaviour = f"healthbehaviour: dcs:{healthbehaviour}\n"
                if healthbehaviour == "Total":
                    Node = Node.replace("_Total", "")
                    f_healthbehaviour = ""
                mcf += template_mcf.format(Node=Node,
                                           gender=f_gender,
                                           healthbehaviour=f_healthbehaviour,
                                           quant_inc=f_quant_inc)

    return mcf


def daily_smokers_cigarettes_degree_of_urbanisation() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Degree of Urbanisation\n"
        "statType: dcs:measuredValue\n"
        "gender: dcs:{gender}\n"
        "healthbehaviour: dcs:{healthbehaviour}\n"
        "deg_urb: dcs:{deg_urb}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for healthbehaviour in [
                'Total', 'LessThan20CigarettesPerDay',
                '20OrMoreCigarettesPerDay'
        ]:
            for deg_urb in ['Total', 'Cities', 'TownsAndSuburbs', 'RuralAreas']:
                Node = "Count_Person_" + deg_urb + "_" + gender + "_" + "DailySmokerCigarettes" + "_" + healthbehaviour + "_AsAFractionOf_" + "Count_Person_" + deg_urb + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_healthbehaviour = f"healthbehaviour: dcs:{healthbehaviour}\n"
                if healthbehaviour == "Total":
                    Node = Node.replace("_Total", "")
                    f_healthbehaviour = ""

                f_deg_urb = f"deg_urb: dcs:{deg_urb}\n"
                if deg_urb == "Total":
                    Node = Node.replace("_Total", "")
                    f_deg_urb = ""
                mcf += template_mcf.format(Node=Node,
                                           gender=f_gender,
                                           healthbehaviour=f_healthbehaviour,
                                           deg_urb=f_deg_urb)

    return mcf


def daily_exposure_tobacco_smoke_indoors_education_attainment_level() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Educational Attainment\n"
        "statType: dcs:measuredValue\n"
        "frequency: dcs:{frequency}\n"
        "{gender}{educationalAttainment}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for frequency in [
                'AtLeast1HourEveryDay', 'LessThan1HourEveryDay',
                'LessThanOnceAWeek', 'AtLeastOnceAWeek', 'RarelyOrNever'
        ]:
            for educationalAttainment in [
                    'AllISCED2011Levels',
                    'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                    'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                    'TertiaryEducation'
            ]:
                Node = "Count_Person_" + educationalAttainment + "_" + gender + "_" + "DailyExposureTobaccoSmokeIndoors" + "_" + frequency + "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_educationalAttainment = f"educationalAttainment: dcs:{educationalAttainment}\n"
                if educationalAttainment == "AllISCED2011Levels":
                    Node = Node.replace("_AllISCED2011Levels", "")
                    f_educationalAttainment = ""
                mcf += template_mcf.format(
                    Node=Node,
                    gender=f_gender,
                    frequency=frequency,
                    educationalAttainment=f_educationalAttainment)
    return mcf


def daily_exposure_tobacco_smoke_indoors_degree_of_urbanisation() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Degree of Urbanisation\n"
        "statType: dcs:measuredValue\n"
        "{gender}{deg_urb}\n"
        "frequency: dcs:{frequency}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for frequency in [
                'AtLeast1HourEveryDay', 'LessThan1HourEveryDay',
                'LessThanOnceAWeek', 'AtLeastOnceAWeek', 'RarelyOrNever'
        ]:
            for deg_urb in ['Total', 'Cities', 'TownsAndSuburbs', 'RuralAreas']:
                Node = "Count_Person_" + deg_urb + "_" + gender + "_" + "DailyExposureTobaccoSmokeIndoors" + "_" + frequency + "_AsAFractionOf_" + "Count_Person_" + deg_urb + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_deg_urb = f"deg_urb: dcs:{deg_urb}\n"
                if deg_urb == "Total":
                    Node = Node.replace("_Total", "")
                    f_deg_urb = ""
                mcf += template_mcf.format(Node=Node,
                                           gender=f_gender,
                                           frequency=frequency,
                                           deg_urb=f_deg_urb)
    return mcf


def smoking_tobaccoproducts_county_of_birth() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Country of Birth\n"
        "statType: dcs:measuredValue\n"
        "{gender}{healthbehaviour}\n"
        "birth: dcs:{birth}\n")
    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for healthbehaviour in [
                'NonSmoker', 'DailySmoker', 'CurrentSmoker', 'OccasionalSmoker'
        ]:
            for birth in [
                    'CountryOfBirthEU28CountriesExceptReportingCountry',
                    'CountryOfBirthNonEU28CountriesNorReportingCountry',
                    'CountryOfBirthForeignCountry',
                    'CountryOfBirthReportingCountry'
            ]:
                Node = "Count_Person_" + birth + "_" + gender + "_" + "SmokingTobaccoProducts" + "_" + healthbehaviour + "_AsAFractionOf_" + "Count_Person_" + birth + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_healthbehaviour = f"healthbehaviour: dcs:{healthbehaviour}\n"
                if healthbehaviour == "Total":
                    Node = Node.replace("_Total", "")
                    f_healthbehaviour = ""
                mcf += template_mcf.format(Node=Node,
                                           gender=f_gender,
                                           healthbehaviour=f_healthbehaviour,
                                           birth=birth)

    return mcf


def smoking_tobaccoproducts_country_of_citizenship() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Country of Citizenhip\n"
        "statType: dcs:measuredValue\n"
        "{gender}{healthbehaviour}\n"
        "citizen: dcs:{citizen}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for healthbehaviour in [
                'NonSmoker', 'DailySmoker', 'CurrentSmoker', 'OccasionalSmoker'
        ]:
            for citizen in [
                    'CitizenshipEU28CountriesExceptReportingCountry',
                    'CitizenshipNonEU28CountriesNorReportingCountry',
                    'CitizenshipForeignCountry', 'CitizenshipReportingCountry'
            ]:
                Node = "Count_Person_" + citizen + "_" + gender + "_" + "SmokingTobaccoProducts" + "_" + healthbehaviour + "_AsAFractionOf_" + "Count_Person_" + citizen + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_healthbehaviour = f"healthbehaviour: dcs:{healthbehaviour}\n"
                if healthbehaviour == "Total":
                    Node = Node.replace("_Total", "")
                    f_healthbehaviour = ""
                mcf += template_mcf.format(Node=Node,
                                           gender=f_gender,
                                           healthbehaviour=f_healthbehaviour,
                                           citizen=citizen)

    return mcf


def former_daily_tobacco_smoker_income_quintile() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Income Quintile\n"
        "statType: dcs:measuredValue\n"
        "{gender}{quant_inc}")
    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for quant_inc in [
                'Total', 'FirstQuintile', 'SecondQuintile', 'ThirdQuintile',
                'FourthQuintile', 'FifthQuintile'
        ]:
            Node = "Count_Person_" + quant_inc + "_" + gender + "_" + "FormerDailTobaccoSmoker" + "_AsAFractionOf_" + "Count_Person_" + quant_inc + "_" + gender
            f_gender = f"gender: dcs:{gender}\n"
            if gender == "Total":
                Node = Node.replace("_Total", "")
                f_gender = ""

            f_quant_inc = f"quant_inc: dcs:{quant_inc}\n"
            if quant_inc == "Total":
                Node = Node.replace("_Total", "")
                f_quant_inc = ""
            mcf += template_mcf.format(Node=Node,
                                       gender=f_gender,
                                       quant_inc=f_quant_inc)

    return mcf


def former_daily_tobacco_smoker_education_attainment_level() -> str:
    template_mcf = (
        " Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Educational Attainment\n"
        "statType: dcs:measuredValue\n"
        "{gender}{educationalAttainment}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for educationalAttainment in [
                'AllISCED2011Levels',
                'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                'TertiaryEducation'
        ]:
            Node = "Count_Person_" + educationalAttainment + "_" + gender + "_" + "FormerDailTobaccoSmoker" + "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
            f_gender = f"gender: dcs:{gender}\n"
            if gender == "Total":
                Node = Node.replace("_Total", "")
                f_gender = ""

            f_educationalAttainment = f"educationalAttainment: dcs:{educationalAttainment}\n"
            if educationalAttainment == "AllISCED2011Levels":
                Node = Node.replace("_AllISCED2011Levels", "")
                f_educationalAttainment = ""
            mcf += template_mcf.format(
                Node=Node,
                gender=f_gender,
                educationalAttainment=f_educationalAttainment)
    return mcf


def duration_daily_tobacco_smoking_education_attainment_level() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Educational Attainment\n"
        "statType: dcs:measuredValue\n"
        "{gender}{educationalAttainment}\n"
        "duration: dcs:{duration}\n")
    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for educationalAttainment in [
                'AllISCED2011Levels',
                'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                'TertiaryEducation'
        ]:
            for duration in [
                    'LessThan1Year', 'From1To5Years', 'From5To10Years',
                    '10YearsOrOver'
            ]:
                Node = "Count_Person_" + educationalAttainment + "_" + gender + "_" + "DurationOfDailyTobaccoSmoking" + "_" + duration + "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_educationalAttainment = f"educationalAttainment: dcs:{educationalAttainment}\n"
                if educationalAttainment == "AllISCED2011Levels":
                    Node = Node.replace("_AllISCED2011Levels", "")
                    f_educationalAttainment = ""
                mcf += template_mcf.format(
                    Node=Node,
                    gender=f_gender,
                    educationalAttainment=f_educationalAttainment,
                    duration=duration)
    return mcf


def electronic_cigarettes_similar_electronic_devices_education_attainment_level(
) -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Educational Attainment\n"
        "statType: dcs:measuredValue\n"
        "{gender}{educationalAttainment}\n"
        "frequency: dcs:{frequency}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for educationalAttainment in [
                'AllISCED2011Levels',
                'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                'TertiaryEducation'
        ]:
            for frequency in ['EveryDay', 'Formerly', 'Occasionally', 'Never']:
                Node = "Count_Person_" + educationalAttainment + "_" + gender + "_" + "ElectronicCigarettesSimilarElectronicDevices" + "_" + frequency + "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_educationalAttainment = f"educationalAttainment: dcs:{educationalAttainment}\n"
                if educationalAttainment == "AllISCED2011Levels":
                    Node = Node.replace("_AllISCED2011Levels", "")
                    f_educationalAttainment = ""
                mcf += template_mcf.format(
                    Node=Node,
                    gender=f_gender,
                    educationalAttainment=f_educationalAttainment,
                    frequency=frequency)
    return mcf


def daily_smokers_cigarettes_history_education_attainment_level() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Educational Attainment\n"
        "statType: dcs:measuredValue\n"
        "{gender}{educationalAttainment}\n")
    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for educationalAttainment in [
                'AllISCED1997Levels',
                'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                'TertiaryEducationStageOneOrTertiaryEducationStageTwo'
        ]:
            Node = "Count_Person_" + educationalAttainment + "_" + gender + "_" + "DailySmokersCigarettesHistory" + "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
            mcf += template_mcf.format(
                Node=Node,
                gender=gender,
                educationalAttainment=educationalAttainment)
    return mcf


def daily_smokers_cigarettes_history_income_quintile() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Income Quintile\n"
        "statType: dcs:measuredValue\n"
        "{gender}{quant_inc}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for quant_inc in [
                'Total', 'FirstQuintile', 'SecondQuintile', 'ThirdQuintile',
                'FourthQuintile', 'FifthQuintile', 'Unknown'
        ]:
            Node = "Count_Person_" + quant_inc + "_" + gender + "_" + "DailySmokersCigarettesHistory" + "_AsAFractionOf_" + "Count_Person_" + quant_inc + "_" + gender
            mcf += template_mcf.format(Node=Node,
                                       gender=gender,
                                       quant_inc=quant_inc)
    return mcf


def daily_smokers_number_of_cigarettes_history_education_attainment_level(
) -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:Count Person by Sex, Age & Educational Attainment\n"
        "statType: dcs:measuredValue\n"
        "healthbehaviour: dcs:{healthbehaviour}\n"
        "{gender}{educationalAttainment}\n")
    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for healthbehaviour in [
                'DailyCigaretteSmoker20OrMorePerDay',
                'DailyCigaretteSmokerLessThan20PerDay'
        ]:
            for educationalAttainment in [
                    'AllISCED1997Levels',
                    'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                    'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                    'TertiaryEducationStageOneOrTertiaryEducationStageTwo'
            ]:
                Node = "Count_Person_" + educationalAttainment + "_" + gender + "_" + "DailySmokersNumberOFCigarettesHistory" + "_" + healthbehaviour + "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender

                mcf += template_mcf.format(
                    Node=Node,
                    gender=gender,
                    educationalAttainment=educationalAttainment,
                    healthbehaviour=healthbehaviour)
    return mcf


def generate_mcf():
    mcf = ''
    for f in [
            smoking_tobaccoproducts_education_attainment_level,
            smoking_tobaccoproducts_income_quintile,
            smoking_tobaccoproducts_degree_of_urbanisation,
            daily_smokers_cigarettes_education_attainment_level,
            daily_smokers_cigarettes_income_quintile,
            daily_smokers_cigarettes_degree_of_urbanisation,
            daily_exposure_tobacco_smoke_indoors_education_attainment_level,
            daily_exposure_tobacco_smoke_indoors_degree_of_urbanisation,
            smoking_tobaccoproducts_county_of_birth,
            smoking_tobaccoproducts_country_of_citizenship,
            former_daily_tobacco_smoker_income_quintile,
            former_daily_tobacco_smoker_education_attainment_level,
            duration_daily_tobacco_smoking_education_attainment_level,
            electronic_cigarettes_similar_electronic_devices_education_attainment_level,
            daily_smokers_cigarettes_history_education_attainment_level
    ]:
        #     daily_smokers_cigarettes_history_income_quintile,
        #      daily_smokers_number_of_cigarettes_history_education_attainment_level]:
        mcf += f()

    return mcf


if __name__ == "__main__":
    generate_mcf()
