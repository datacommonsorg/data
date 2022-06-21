import re
import os

_MCF_TEMPLATE = """Node: dcid:{dcid}
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
statType: dcs:measuredValue
measuredProperty: dcs:count
{xtra_pvs}
"""

_INCOME_QUINTILE_VALUES = {
    "IncomeOf0To20Percentile": "[0 20 Percentile]",
    "IncomeOf20To40Percentile": "[20 40 Percentile]",
    "IncomeOf40To60Percentile": "[40 60 Percentile]",
    "IncomeOf60To80Percentile": "[60 80 Percentile]",
    "IncomeOf80To100Percentile": "[80 100 Percentile]",
}


def _replace_prop(sv: str):
    return sv.replace("CountryOfBirth", "")\
             .replace("Citizenship", "")\
             .replace("In_", "")\
             .replace("Count_", "")\
             .replace("Person_", "")\
             .replace("Percent_", "")


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
    mcf_nodes = []
    for sv in sv_list:
        pvs = []
        dcid = sv
        sv = _replace_prop(sv)
        sv_prop = [prop for prop in sv.split("_") if sv.strip()]
        for prop in sv_prop:
            if "Male" in prop or "Female" in prop:
                pvs.append(f"gender: dcs:{prop}")
            elif "Education" in prop:
                pvs.append(
                    f"educationalAttainment: dcs:{prop.replace('Or', '__')}")
            elif "Percentile" in prop:
                income_quin = _INCOME_QUINTILE_VALUES[prop]
                pvs.append(f"income: {income_quin}")
            elif "Urban" in prop or "SemiUrban" in prop \
                or "Rural" in prop:
                pvs.append(f"placeOfResidenceClassification: dcs:{prop}")
            elif "ForeignBorn" in prop or "Native" in prop:
                pvs.append(f"nativity: dcs:{prop}")
            elif "ForeignWithin" in prop or "ForeignOutside" in prop\
                or "Citizen" in prop:
                pvs.append(f"citizenship: dcs:{prop}")
            elif "Activity" in prop:
                pvs.append(f"globalActivityLimitationindicator: dcs:{prop}")
            elif "weight" in prop \
                or "Obese" in prop or "Obesity" in prop:
                pvs.append(f"healthBehavior: dcs:{prop}")
        node = _MCF_TEMPLATE.format(dcid=dcid, xtra_pvs='\n'.join(pvs))
        mcf_nodes.append(node)
    mcf = '\n'.join(mcf_nodes)
    # Writing Genereated MCF to local path.
    with open(mcf_file_path, 'w+', encoding='utf-8') as f_out:
        f_out.write(mcf.rstrip('\n'))


_MODULE_DIR = os.path.dirname(__file__)
# _INPUT_MCF_FILE_PATH=os.path.join(_MODULE_DIR, "output_files", "eurostat_population_bmi.mcf")
# _OUTPUT_MCF_FILE_PATH=os.path.join(_MODULE_DIR, "output_files", "eurostat_population_bmi_deno.mcf")
_INPUT_MCF_FILE_PATH = "/Users/chharish/datacommonsEU/data/scripts/eurostat/health_determinants/tobacco_consumption/output/eurostat_population_tobaccoconsumption.mcf"
_OUTPUT_MCF_FILE_PATH = "/Users/chharish/datacommonsEU/data/scripts/eurostat/health_determinants/tobacco_consumption/output/eurostat_population_tobaccoconsumption_denominator.mcf"

with open(_INPUT_MCF_FILE_PATH, "r") as mcf_file:
    mcf = mcf_file.read()
    #print(mcf)
    deno_matched = re.findall("(measurementDenominator: dcs:)(\w+)", mcf)
    f_deno = []
    for deno in deno_matched:
        f_deno.append(deno[1])
    f_deno = list(set(f_deno))
    f_deno.sort()
    _generate_mcf(f_deno, _OUTPUT_MCF_FILE_PATH)
