
def smoking_tobaccoproducts_education_attainment_level() -> str:
    template_mcf = (
        "Node: dcid:{node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "statType: dcs:measuredValue\n"
        "healthBehavior: dcs:{healthBehavior}\n"
        "substanceUsed: dcs:TobaccoProducts\n"
        "{substanceUsageFrequency}{gender}{educationalAttainment}\n")

    mcf = ''
    # for gender in ['Male', 'Female']:
    for gender in ['Male', 'Female','Total']:

        for healthBehavior in ['NonSmoker', 'Smoking']:
            if healthBehavior == 'NonSmoker':
                for educationalAttainment in [
                        'AllISCED2011Levels',
                        'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                        'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                        'TertiaryEducation'
                ]:
                    node = "Count_Person_" + educationalAttainment + "_" + gender + "_" + healthBehavior + "_TobaccoProducts" + "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
                    
                    denominator = "Count_Person_" + educationalAttainment + "_" + gender
                    f_gender = f"gender: dcs:{gender}\n"
                    if gender == "Total":
                        node = node.replace("_Total", "")
                        denominator = denominator.replace("_Total", "")
                        f_gender = ""

                    f_educationalAttainment = f"educationalAttainment: dcs:{educationalAttainment}\n"
                    f_educationalAttainment = f_educationalAttainment.replace("Or", "__")
                    
                    if educationalAttainment == "AllISCED2011Levels":
                        node = node.replace("_AllISCED2011Levels", "")
                        denominator = denominator.replace("_AllISCED2011Levels", "")
                        f_educationalAttainment = ""

                    mcf += template_mcf.format(
                        node=node,
                        denominator = denominator,
                        gender=f_gender,
                        healthBehavior=healthBehavior,
                        substanceUsageFrequency="",
                        educationalAttainment=f_educationalAttainment)

            elif healthBehavior == 'Smoking':
                for substanceUsageFrequency in ['DailyUsage' , 'OccasionalUsage']:
                    f_substanceUsageFrequency = f"substanceUsageFrequency: dcs:{substanceUsageFrequency}\n"
                    
                    for educationalAttainment in [
                            'AllISCED2011Levels',
                            'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                            'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                            'TertiaryEducation'
                    ]:
                        node = "Count_Person_" + educationalAttainment + "_" + gender + "_" + healthBehavior +"_"+ substanceUsageFrequency+"_TobaccoProducts"+"_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
                        
                        denominator = "Count_Person_" + educationalAttainment + "_" + gender
                        f_gender = f"gender: dcs:{gender}\n"
                        if gender == "Total":
                            node = node.replace("_Total", "")
                            denominator = denominator.replace("_Total", "")
                            f_gender = ""

                        f_educationalAttainment = f"educationalAttainment: dcs:{educationalAttainment}\n"
                        f_educationalAttainment = f_educationalAttainment.replace("Or", "__")
                        
                        if educationalAttainment == "AllISCED2011Levels":
                            node = node.replace("_AllISCED2011Levels", "")
                            denominator = denominator.replace("_AllISCED2011Levels", "")
                            f_educationalAttainment = ""

                        mcf += template_mcf.format(
                            node=node,
                            denominator = denominator,
                            gender=f_gender,
                            healthBehavior=healthBehavior,
                            substanceUsageFrequency=f_substanceUsageFrequency,
                            educationalAttainment=f_educationalAttainment)
    return mcf


def daily_smokers_cigarettes_education_attainment_level() -> str:
    template_mcf = (
        "Node: dcid:{node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "statType: dcs:measuredValue\n"
        "substanceUsageFrequency: dcs:DailyUsage\n"
        "substanceUsed: dcs:Cigarettes\n"
        "healthBehavior: dcs:Smoking\n"
        "{gender}{educationalAttainment}{substanceUsageQuantity}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for substanceUsageQuantity in [
                'Total', 'LessThan20CigarettesPerDay',
                '20OrMoreCigarettesPerDay'
        ]:
            for educationalAttainment in [
                    'AllISCED2011Levels',
                    'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                    'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                    'TertiaryEducation'
            ]:
                node = "Count_Person_" + educationalAttainment + "_" + gender + "_" + "Smoking"+"_" + "DailyUsage"+"_"+"Cigarettes"+"_" + substanceUsageQuantity + "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
                denominator = "Count_Person_" + educationalAttainment + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    node = node.replace("_Total", "")
                    denominator = denominator.replace("_Total", "")
                    f_gender = ""

                f_substanceUsageQuantity = f"substanceUsageQuantity: dcs:{substanceUsageQuantity}\n"
                if substanceUsageQuantity == "Total":
                    node = node.replace("_Total", "")
                    denominator = denominator.replace("_Total", "")
                    f_substanceUsageQuantity = ""

                f_educationalAttainment = f"educationalAttainment: dcs:{educationalAttainment}\n"
                f_educationalAttainment = f_educationalAttainment.replace("Or", "__")
                if educationalAttainment == "AllISCED2011Levels":
                    node = node.replace("_AllISCED2011Levels", "")
                    denominator = denominator.replace("_AllISCED2011Levels", "")
                    f_educationalAttainment = ""

                mcf += template_mcf.format(
                    node=node,
                    gender=f_gender,
                    substanceUsageQuantity=f_substanceUsageQuantity,
                    educationalAttainment=f_educationalAttainment,
                    denominator = denominator)
    return mcf


def daily_exposure_tobacco_smoke_indoors_education_attainment_level() -> str:
    template_mcf = (
        "Node: dcid:{node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "statType: dcs:measuredValue\n"
        "healthBehavior: dcs:ExposureToTobaccoSmoke\n"
        "substanceExposureFrequency: dcs:{substanceExposureFrequency}\n"
        "{gender}{educationalAttainment}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for substanceExposureFrequency in [
                'AtLeast1HourEveryDay', 'LessThan1HourEveryDay',
                'LessThanOnceAWeek', 'AtLeastOnceAWeek', 'RarelyOrNever'
        ]:
            for educationalAttainment in [
                    'AllISCED2011Levels',
                    'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                    'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                    'TertiaryEducation'
            ]:
                node = "Count_Person_" + educationalAttainment + "_" + gender + "_"+ "ExposureToTobaccoSmoke" + "_" + substanceExposureFrequency + "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
                denominator = "Count_Person_" + educationalAttainment + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    node = node.replace("_Total", "")
                    denominator = denominator.replace("_Total", "")
                    f_gender = ""

                f_educationalAttainment = f"educationalAttainment: dcs:{educationalAttainment}\n"
                f_educationalAttainment = f_educationalAttainment.replace("Or", "__")
                if educationalAttainment == "AllISCED2011Levels":
                    node = node.replace("_AllISCED2011Levels", "")
                    denominator = denominator.replace("_AllISCED2011Levels", "")
                    f_educationalAttainment = ""
                mcf += template_mcf.format(
                    node=node,
                    denominator=denominator,
                    gender=f_gender,
                    substanceExposureFrequency=substanceExposureFrequency,
                    educationalAttainment=f_educationalAttainment)
    return mcf


def former_daily_tobacco_smoker_education_attainment_level() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "statType: dcs:measuredValue\n"
        "healthBehavior: dcs:FormerSmoker\n"
        "substanceUsed: dcs:TobaccoProducts\n"
        "substanceUsageFrequency: DailyUsage\n"
        "{gender}{educationalAttainment}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for educationalAttainment in [
                'AllISCED2011Levels',
                'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                'TertiaryEducation'
        ]:
            Node = "Count_Person_" + educationalAttainment + "_" + gender + "_" + "FormerSmoker"+"_"+"DailyUsage"+"TobaccoProducts"+ "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
            denominator = "Count_Person_" + educationalAttainment + "_" + gender
            f_gender = f"gender: dcs:{gender}\n"
            if gender == "Total":
                Node = Node.replace("_Total", "")
                denominator = denominator.replace("_Total", "")
                f_gender = ""

            f_educationalAttainment = f"educationalAttainment: dcs:{educationalAttainment}\n"
            f_educationalAttainment = f_educationalAttainment.replace("Or", "__")
            if educationalAttainment == "AllISCED2011Levels":
                Node = Node.replace("_AllISCED2011Levels", "")
                denominator = denominator.replace("_AllISCED2011Levels", "")
                f_educationalAttainment = ""
            mcf += template_mcf.format(
                Node=Node,
                denominator=denominator,
                gender=f_gender,
                educationalAttainment=f_educationalAttainment)
    return mcf


def duration_daily_tobacco_smoking_education_attainment_level() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "statType: dcs:measuredValue\n"
        "healthBehavior: dcs:Smoking\n"
        "substanceUsed: dcs:TobaccoProducts\n"
        "substanceUsageFrequency: DailyUsage\n"
        "substanceUsageHistory: dcs:{substanceUsageHistory}\n"
        "{gender}{educationalAttainment}\n")
    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for educationalAttainment in [
                'AllISCED2011Levels',
                'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                'TertiaryEducation'
        ]:
            for substanceUsageHistory in [
                    'LessThan1Year', 'From1To5Years', 'From5To10Years',
                    '10YearsOrOver'
            ]:
                Node = "Count_Person_" + educationalAttainment + "_" + gender + "_" + "Smoking" + "_" +"DailyUsage"+"_"+ substanceUsageHistory +"_"+"TobaccoProducts"+ "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
                denominator = "Count_Person_" + educationalAttainment + "_" + gender
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    denominator = denominator.replace("_Total", "")
                    f_gender = ""

                f_educationalAttainment = f"educationalAttainment: dcs:{educationalAttainment}\n"
                f_educationalAttainment = f_educationalAttainment.replace("Or", "__")
                if educationalAttainment == "AllISCED2011Levels":
                    Node = Node.replace("_AllISCED2011Levels", "")
                    denominator = denominator.replace("_AllISCED2011Levels", "")
                    f_educationalAttainment = ""
                mcf += template_mcf.format(
                    Node=Node,
                    denominator=denominator,
                    gender=f_gender,
                    educationalAttainment=f_educationalAttainment,
                    substanceUsageHistory=substanceUsageHistory)
    return mcf


def electronic_cigarettes_similar_electronic_devices_education_attainment_level(
) -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "statType: dcs:measuredValue\n"
        "substanceUsed: dcs:Ecigarettes\n"
        "healthBehavior: dcs:{healthBehavior}\n"
        "substanceUsageFrequency: dcs:{substanceUsageFrequency}\n"
        "{gender}{educationalAttainment}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for educationalAttainment in [
                'AllISCED2011Levels',
                'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
                'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
                'TertiaryEducation'
        ]:
            for healthBehavior in ['Smoking','FormerSmoker']:
                for substanceUsageFrequency in ['DailyUsage', 'OccasionalUsage', 'NeverUsed']:
                    Node = "Count_Person_" + educationalAttainment + "_" + gender + "_" +healthBehavior+ substanceUsageFrequency + "_" + "Ecigarettes" + "_AsAFractionOf_" + "Count_Person_" + educationalAttainment + "_" + gender
                    denominator = "Count_Person_" + educationalAttainment + "_" + gender
                    f_gender = f"gender: dcs:{gender}\n"
                    if gender == "Total":
                        Node = Node.replace("_Total", "")
                        denominator = denominator.replace("_Total", "")
                        f_gender = ""

                    f_educationalAttainment = f"educationalAttainment: dcs:{educationalAttainment}\n"
                    f_educationalAttainment = f_educationalAttainment.replace("Or", "__")
                    if educationalAttainment == "AllISCED2011Levels":
                        Node = Node.replace("_AllISCED2011Levels", "")
                        denominator = denominator.replace("_AllISCED2011Levels", "")
                    f_educationalAttainment = ""
                    mcf += template_mcf.format(
                        Node=Node,
                        healthBehavior=healthBehavior,
                        denominator=denominator,
                        gender=f_gender,
                        educationalAttainment=f_educationalAttainment,
                        substanceUsageFrequency=substanceUsageFrequency)
    return mcf



def smoking_tobaccoproducts_income_quintile() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "statType: dcs:measuredValue\n"
        "healthBehavior: dcs:{healthBehavior}\n"
        "substanceUsed: dcs:TobaccoProducts\n"
        "{gender}{substanceUsageFrequency}{income}\n")

    mcf = ''
    for gender in ['Male', 'Female','Total']:
        for healthBehavior in [
                'NonSmoker', 'Smoking'
        ]:
            for substanceUsageFrequency in ['DailyUsage','OccasionalUsage']:
                f_substanceUsageFrequency = f"substanceUsageFrequency: dcs:{substanceUsageFrequency}\n"
                for income in ['Total', 'IncomeOf0To20Percentile', 'IncomeOf20To40Percentile', 'IncomeOf40To60Percentile','IncomeOf60To80Percentile', 'IncomeOf80To100Percentile']:
                    Node = "Count_Person_"  + gender +"_"+ healthBehavior+"_"+income+ "_"+ substanceUsageFrequency +"_"+"TobaccoProducts"+ "_AsAFractionOf_" + "Count_Person_" + gender +"_"+income
                    denominator = "Count_Person_" + gender +"_"+income
                    f_gender = f"gender: dcs:{gender}\n"
                    if gender == "Total":
                        Node = Node.replace("_Total", "")
                        denominator = denominator.replace("_Total", "")
                        f_gender = ""

                    f_income = f"income: dcs:{income}\n"
                    f_income = f_income.replace("IncomeOf","[").replace("To"," ").replace("Percentile"," Percentile]")
                    if income == "Total":
                        Node = Node.replace("_Total", "")
                        denominator = denominator.replace("_Total", "")
                        f_income = ""

                    if healthBehavior == "NonSmoker":
                        Node = Node.replace("_DailyUsage", "").replace("_OccasionalUsage","")
                        f_substanceUsageFrequency = ""
                    mcf += template_mcf.format(Node=Node,
                                            gender=f_gender,
                                            substanceUsageFrequency=f_substanceUsageFrequency,
                                            denominator=denominator,
                                            healthBehavior=healthBehavior,
                                            income=f_income)
    return mcf

def daily_smokers_cigarettes_income_quintile() -> str:
    template_mcf = (
         "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "statType: dcs:measuredValue\n"
        "substanceUsageFrequency: DailyUsage\n"
        "substanceUsed: dcs:Cigarettes\n"
        "healthBehavior: dcs:Smoking\n"
        "{gender}{substanceUsageQuantity}{income}\n")

    mcf = ''
    for gender in ['Male', 'Female','Total']:
        for substanceUsageQuantity in [
                'Total', 'LessThan20CigarettesPerDay',
                '20OrMoreCigarettesPerDay'
        ]:
            for income in ['Total', 'IncomeOf0To20Percentile', 'IncomeOf20To40Percentile', 'IncomeOf40To60Percentile','IncomeOf60To80Percentile', 'IncomeOf80To100Percentile']:
                Node = "Count_Person_"  + gender +"_"+ "Smoking"+"_"+income+ "_"+ "DailyUsage" +substanceUsageQuantity+ "Cigarettes"+"_AsAFractionOf_" + "Count_Person_" + gender +"_"+income
                denominator = "Count_Person_" + gender +"_"+income
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_income = f"income: dcs:{income}\n"
                f_income = f_income.replace("IncomeOf","[").replace("To"," ").replace("Percentile"," Percentile]")
                if income == "Total":
                    Node = Node.replace("_Total", "")
                    denominator = denominator.replace("_Total", "") 
                    f_income = ""

                f_substanceUsageQuantity = f"substanceUsageFrequency: dcs:{substanceUsageQuantity}\n"
                if substanceUsageQuantity == "Total":
                    Node = Node.replace("_Total", "")
                    denominator = denominator.replace("_Total", "")
                    f_substanceUsageQuantity = ""
                mcf += template_mcf.format(Node=Node,
                                           gender=f_gender,
                                           denominator=denominator,
                                           substanceUsageQuantity=f_substanceUsageQuantity,
                                           income=f_income)

    return mcf        

def former_daily_tobacco_smoker_income_quintile() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "statType: dcs:measuredValue\n"
        "healthBehavior: dcs:FormerSmoker\n"
        "substanceUsed: dcs:TobaccoProducts\n"
        "substanceUsageFrequency: dcs:DailyUsage\n"
        "{gender}{income}\n")
    mcf = ''
    for gender in ['Male', 'Female','Total']:
        for income in ['Total', 'IncomeOf0To20Percentile', 'IncomeOf20To40Percentile', 'IncomeOf40To60Percentile','IncomeOf60To80Percentile', 'IncomeOf80To100Percentile']:
            Node = "Count_Person_"  + gender +"_"+ "FormerSmoker"+"_"+income+ "_"+ "DailyUsage"+"_" +"TobaccoProducts"+"_"+ "Cigarettes"+"_AsAFractionOf_" + "Count_Person_" + gender +"_"+income
            denominator = "Count_Person_" + gender +"_"+income
            f_gender = f"gender: dcs:{gender}\n"
            if gender == "Total":
                Node = Node.replace("_Total", "")
                f_gender = ""

            f_income = f"income: dcs:{[income]}\n"
            f_income = f_income.replace("IncomeOf","").replace("To"," ").replace("Percentile"," Percentile")
            if income == "Total":
                Node = Node.replace("_Total", "")
                denominator = denominator.replace("_Total", "")
                f_income = ""
            mcf += template_mcf.format(Node=Node,
                                    denominator=denominator,
                                       gender=f_gender,
                                       income=f_income)

    return mcf

def smoking_tobaccoproducts_degree_of_urbanisation() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "healthBehavior: dcs:{healthBehavior}\n"
        "substanceUsed: dcs:TobaccoProducts\n"
        "{gender}{placeOfResidenceClassification}{substanceUsageFrequency}\n")

    mcf = ''
    for gender in ['Male', 'Female','Total']:
        for healthBehavior in [
                'NonSmoker', 'Smoking'
        ]:
            for substanceUsageFrequency in ['DailyUsage','OccasionalUsage']:
                f_substanceUsageFrequency = f"substanceUsageFrequency: dcs:{substanceUsageFrequency}\n"
                for placeOfResidenceClassification in ['Total', 'Urban', 'SemiUrban', 'Rural']:
                    Node = "Count_Person_" + gender+ "_"+healthBehavior+ "_"+ placeOfResidenceClassification+ "_"+substanceUsageFrequency+ "_" + "TobaccoProducts"+ "_AsAFractionOf_" + "Count_Person_" +gender+"_" + placeOfResidenceClassification
                    denominator = "Count_Person_"+gender+"_" + placeOfResidenceClassification
                    f_gender = f"gender: dcs:{gender}\n"
                    if gender == "Total":
                        Node = Node.replace("_Total", "")
                        f_gender = ""

                    f_placeOfResidenceClassification = f"placeOfResidenceClassification: dcs:{placeOfResidenceClassification}\n"
                    if placeOfResidenceClassification == "Total":
                        Node = Node.replace("_Total", "")
                        denominator = denominator = denominator.replace("_Total", "")
                        f_placeOfResidenceClassification = ""

                    if healthBehavior == "NonSmoker":
                        Node = Node.replace("_DailyUsage", "").replace("_OccasionalUsage","")
                        f_substanceUsageFrequency = ""
                    mcf += template_mcf.format(Node=Node,
                                            gender=f_gender,
                                            denominator=denominator,
                                            substanceUsageFrequency=f_substanceUsageFrequency,
                                            healthBehavior=healthBehavior,
                                            placeOfResidenceClassification=f_placeOfResidenceClassification)
    return mcf

def daily_smokers_cigarettes_degree_of_urbanisation() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "statType: dcs:measuredValue\n"
        "substanceUsageFrequency :dcs:DailyUsage\n"
        "healthBehavior: dcs:Smoking\n"
        "substanceUsed: dcs:Cigarettes\n"
        "{gender}{substanceUsageQuantity}{placeOfResidenceClassification}\n")
        

    mcf = ''
    for gender in ['Male', 'Female','Total']:
        for substanceUsageQuantity in [
                'Total', 'LessThan20CigarettesPerDay',
                '20OrMoreCigarettesPerDay'
        ]:
            for placeOfResidenceClassification in ['Total', 'Urban', 'SemiUrban', 'Rural']:
                Node = "Count_Person_"+ gender+"_"+"Smoking"+"_" +placeOfResidenceClassification + "_"+"DailyUsage"+"_" + substanceUsageQuantity +"_"+"Cigarettes"+ "_AsAFractionOf_" + "Count_Person_" + gender + placeOfResidenceClassification
                denominator =  "Count_Person_" + gender + placeOfResidenceClassification
                f_gender = f"gender: dcs:{gender}\n"
                if gender == "Total":
                    Node = Node.replace("_Total", "")
                    f_gender = ""

                f_substanceUsageQuantity = f"substanceUsageFrequency: dcs:{substanceUsageQuantity}\n"
                if substanceUsageQuantity == "Total":
                    Node = Node.replace("_Total", "")
                    denominator = denominator.replace("_Total", "")
                    f_substanceUsageQuantity = ""

                f_placeOfResidenceClassification = f"placeOfResidenceClassification: dcs:{placeOfResidenceClassification}\n"
                if placeOfResidenceClassification == "Total":
                    Node = Node.replace("_Total", "")
                    denominator = denominator = denominator.replace("_Total", "")
                    f_placeOfResidenceClassification = ""
                mcf += template_mcf.format(Node=Node,
                                           gender=f_gender,
                                           denominator=denominator,
                                           substanceUsageQuantity=f_substanceUsageQuantity,
                                           placeOfResidenceClassification=f_placeOfResidenceClassification)

    return mcf

def daily_exposure_tobacco_smoke_indoors_degree_of_urbanisation() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "statType: dcs:measuredValue\n"
        "healthBehavior: dcs:ExposureToTobaccoSmoke\n"
        "substanceExposureFrequency: dcs:{substanceExposureFrequency}\n"
        "{gender}{placeOfResidenceClassification}\n")

    mcf = ''
    for gender in ['Male', 'Female','Total']:
            for substanceExposureFrequency in [
                    'AtLeast1HourEveryDay', 'LessThan1HourEveryDay',
                    'LessThanOnceAWeek', 'AtLeastOnceAWeek', 'RarelyOrNever'
            ]:
                for placeOfResidenceClassification in ['Total', 'Urban', 'SemiUrban', 'Rural']:
                    Node = "Count_Person_"+ gender+"_"+"ExposureToTobaccoSmoke"+"_" +placeOfResidenceClassification + "_"+substanceExposureFrequency +"_"+"Cigarettes"+ "_AsAFractionOf_" + "Count_Person_" + gender + placeOfResidenceClassification
                    denominator =  "Count_Person_" + gender + placeOfResidenceClassification
                    f_gender = f"gender: dcs:{gender}\n"
                    if gender == "Total":
                        Node = Node.replace("_Total", "")
                        f_gender = ""

                    f_placeOfResidenceClassification = f"placeOfResidenceClassification: dcs:{placeOfResidenceClassification}\n"
                    if placeOfResidenceClassification == "Total":
                        Node = Node.replace("_Total", "")
                        denominator = denominator = denominator.replace("_Total", "")
                        f_placeOfResidenceClassification = ""
                    mcf += template_mcf.format(Node=Node,
                                            gender=f_gender,
                                            denominator=denominator,
                                            substanceExposureFrequency=substanceExposureFrequency,
                                            placeOfResidenceClassification=f_placeOfResidenceClassification)
    return mcf

def smoking_tobaccoproducts_county_of_birth() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "statType: dcs:measuredValue\n"
        "nativity: dcs:{nativity}\n"
        "healthBehavior: dcs:{healthBehavior}\n"
        "substanceUsed: dcs:TobaccoProducts\n"
        "{substanceUsageFrequency}{gender}\n")
    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for healthBehavior in [
                'NonSmoker', 'Smoking'
        ]:
            for substanceUsageFrequency in ['DailyUsage','OccasionalUsage']:
                f_substanceUsageFrequency = f"substanceUsageFrequency: dcs:{substanceUsageFrequency}\n"
                for nativity in [
                        'CountryOfBirthEU28CountriesExceptReportingCountry',
                        'CountryOfBirthNonEU28CountriesNorReportingCountry',
                        'CountryOfBirthForeignCountry',
                        'CountryOfBirthReportingCountry'
                ]:
                    Node = "Count_Person_"+ gender + "_" +healthBehavior+"_"+nativity+"_"+substanceUsageFrequency+"_"+"TobaccoProducts"+"_AsAFractionOf_" + "Count_Person_" + gender+"_" + nativity
                    denominator =  "Count_Person_" + gender+"_" + nativity
                    f_gender = f"gender: dcs:{gender}\n"
                    if gender == "Total":
                        Node = Node.replace("_Total", "")
                        denominator = denominator = denominator.replace("_Total", "")
                        f_gender = ""

                    if healthBehavior == "NonSmoker":
                        Node = Node.replace("_DailyUsage", "").replace("_OccasionalUsage","")
                        f_substanceUsageFrequency = ""
                    mcf += template_mcf.format(Node=Node,
                                            gender=f_gender,
                                            denominator=denominator,
                                            substanceUsageFrequency=f_substanceUsageFrequency,
                                            healthBehavior=healthBehavior,
                                            nativity=nativity)

    return mcf

def smoking_tobaccoproducts_country_of_citizenship() -> str:
    template_mcf = (
        "Node: dcid:{Node}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Person\n"
        "measuredProperty: dcs:count\n"
        "measurementDenominator: dcs:{denominator}\n"
        "statType: dcs:measuredValue\n"
        "healthBehavior: dcs:{healthBehavior}\n"
        "substanceUsed: dcs:TobaccoProducts\n"
        "citizenship: dcs:{citizen}\n"
        "{gender}{substanceUsageFrequency}\n")

    mcf = ''
    for gender in ['Male', 'Female', 'Total']:
        for healthBehavior in [
                'NonSmoker', 'Smoking'
        ]:
            for substanceUsageFrequency in ['DailyUsage','OccasionalUsage']:
                f_substanceUsageFrequency = f"substanceUsageFrequency: dcs:{substanceUsageFrequency}\n"
                for citizenship in [
                        'CitizenshipEU28CountriesExceptReportingCountry',
                        'CitizenshipNonEU28CountriesNorReportingCountry',
                        'CitizenshipForeignCountry', 'CitizenshipReportingCountry'
                ]:
                    Node = "Count_Person_" + citizenship + "_" + gender + "_" + healthBehavior +"_"+substanceUsageFrequency+"_"+"TobaccoProducts"+ "_AsAFractionOf_" + "Count_Person_" + citizenship + "_" + gender
                    denominator = "Count_Person_" + citizenship + "_" + gender
                    f_gender = f"gender: dcs:{gender}\n"
                    if gender == "Total":
                        Node = Node.replace("_Total", "")
                        denominator = denominator = denominator.replace("_Total", "")
                        f_gender = ""

                    if healthBehavior == "NonSmoker":
                        Node = Node.replace("_DailyUsage", "").replace("_OccasionalUsage","")
                        f_substanceUsageFrequency = ""
                    mcf += template_mcf.format(Node=Node,
                                            gender=f_gender,
                                            substanceUsageFrequency=f_substanceUsageFrequency,
                                            denominator=denominator,
                                            healthBehavior=healthBehavior,
                                            citizen=citizenship)

    return mcf


def generate_mcf():
    mcf = ''
    for f in [smoking_tobaccoproducts_education_attainment_level,
            # daily_smokers_cigarettes_education_attainment_level,
            # daily_exposure_tobacco_smoke_indoors_education_attainment_level,
            # former_daily_tobacco_smoker_education_attainment_level,
            # duration_daily_tobacco_smoking_education_attainment_level,
            # electronic_cigarettes_similar_electronic_devices_education_attainment_level,

            # smoking_tobaccoproducts_income_quintile,
            # daily_smokers_cigarettes_income_quintile,
            # former_daily_tobacco_smoker_income_quintile,

            # smoking_tobaccoproducts_degree_of_urbanisation,
            # daily_smokers_cigarettes_degree_of_urbanisation,
            # daily_exposure_tobacco_smoke_indoors_degree_of_urbanisation,

            # smoking_tobaccoproducts_county_of_birth,
            # smoking_tobaccoproducts_country_of_citizenship
            ]:
        mcf += f()

    return mcf


if __name__ == "__main__":
    generate_mcf()
