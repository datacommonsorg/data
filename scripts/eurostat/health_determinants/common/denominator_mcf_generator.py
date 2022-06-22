"""
This Python Script generates
Denomiantor MCF
"""
import re
import os


#Return a list containing every occurrence of "ai":
def _generate_mcf(sv_list, mcf_file_path) -> None:
    """
    This method generates MCF file w.r.t
    dataframe headers and defined MCF template
    Arguments:
        df_cols (list) : List of DataFrame Columns
    Returns:
        None
    """
    # pylint: disable=R0914
    # pylint: disable=R0912
    # pylint: disable=R0915
    actual_mcf_template = ("Node: dcid:{}\n"
                           "typeOf: dcs:StatisticalVariable\n"
                           "populationType: dcs:Person{}{}{}{}{}{}{}{}{}{}{}\n"
                           "statType: dcs:measuredValue\n"
                           "measuredProperty: dcs:count\n")
    final_mcf_template = ""
    for sv in sv_list:
        if "Total" in sv:
            continue
        incomequin = ''
        gender = ''
        education = ''
        healthbehavior = ''
        exercise = ''
        residence = ''
        activity = ''
        duration = ''
        countryofbirth = ''
        citizenship = ''
        lev_limit = ''

        #sv_temp = sv.split("_AsAFractionOf_")
        #denominator = "\nmeasurementDenominator: dcs:" + sv_temp[1]
        sv_prop = sv.split("_")

        for prop in sv_prop:
            if prop in ["Count", "Person"]:
                continue
            if "PhysicalActivity" in prop:
                healthbehavior = "\nhealthBehavior: dcs:" + prop
            elif "Male" in prop or "Female" in prop:
                gender = "\ngender: dcs:" + prop
            elif "Aerobic" in prop or "MuscleStrengthening" in prop \
                or "Walking" in prop or "Cycling" in prop:
                exercise = "\nexerciseType: dcs:" + prop
            elif "Education" in prop:
                education = "\neducationalAttainment: dcs:" + \
                    prop.replace("EducationalAttainment","")\
                    .replace("Or","__")
            elif "Percentile" in prop:
                incomequin = "\nincome: ["+prop.replace("Percentile",\
                    "").replace("To"," ").replace("IncomeOf","")+" Percentile]"
            elif "Urban" in prop or "SemiUrban" in prop \
                or "Rural" in prop:
                residence = "\nplaceOfResidenceClassification: dcs:" + prop
            elif "Activity" in prop:
                activity = "\nphysicalActivityEffortLevel: dcs:" + prop
            elif "Minutes" in prop:
                if "OrMoreMinutes" in prop:
                    duration = "\nduration: [" + prop.replace\
                        ("OrMoreMinutes","") + " - Minutes]"
                elif "To" in prop:
                    duration = "\nduration: [" + prop.replace("Minutes",\
                            "").replace("To", " ") + " Minutes]"
                else:
                    duration = "\nduration: [Minutes " + prop.replace\
                        ("Minutes","") + "]"
            elif "ForeignBorn" in prop or "Native" in prop:
                countryofbirth = "\nnativity: dcs:" + \
                    prop.replace("CountryOfBirth","")
            elif "ForeignWithin" in prop or "ForeignOutside" in prop\
                or "Citizen" in prop:
                citizenship = "\ncitizenship: dcs:" + \
                    prop.replace("Citizenship","")
            elif "Moderate" in prop or "Severe" in prop \
                or "None" in prop:
                lev_limit = "\nglobalActivityLimitationindicator: dcs:"\
                    + prop
            elif "weight" in prop or "Normal" in prop \
                or "Obese" in prop or "Obesity" in prop:
                healthbehavior = "\nhealthBehavior: dcs:" + prop
        final_mcf_template += actual_mcf_template.format(
            sv, incomequin, education, healthbehavior, exercise, residence,
            activity, duration, gender, countryofbirth, citizenship,
            lev_limit) + "\n"

    # Writing Genereated MCF to local path.
    with open(mcf_file_path, 'w+', encoding='utf-8') as f_out:
        f_out.write(final_mcf_template.rstrip('\n'))


_MODULE_DIR = "/Users/chharish/datacommonsEU/data/scripts/"+\
    "eurostat/health_determinants/tobacco_consumption/"
_INPUT_MCF_FILE_PATH = os.path.join(
    _MODULE_DIR, "output", "eurostat_population_tobaccoconsumption.mcf")
_OUTPUT_MCF_FILE_PATH = os.path.join(
    _MODULE_DIR, "output", "eurostat_population_"+\
        "tobaccoconsumption_denominator.mcf")

# pylint: disable=W1514
with open(_INPUT_MCF_FILE_PATH, "r") as mcf_file:
    mcf = mcf_file.read()
    # pylint: disable=W1401
    deno_matched = re.findall("(measurementDenominator: dcs:)(\w+)", mcf)
    f_deno = []
    for deno in deno_matched:
        f_deno.append(deno[1])
    f_deno = list(set(f_deno))
    f_deno.sort()
    _generate_mcf(f_deno, _OUTPUT_MCF_FILE_PATH)
    # pylint: enable=W1401
    # pylint: enable=W1514
