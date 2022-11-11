# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
This file takes the generated MCF file and makes a new MCF file which would have
Stat Vars for the measurement denominator property values.
"""
import re
import os
import sys
from absl import flags

# pylint: disable = wrong-import-position
_COMMON_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(1, _COMMON_PATH)
from dcid_existence import check_dcid_existence
# pylint: enable = wrong-import-position

_FLAGS = flags.FLAGS
import_name = [
    "social_environment", "bmi", "alcohol_consumption", "tobacco_consumption",
    "physical_activity", "fruits_vegetables"
]
flags.DEFINE_list("import_name", import_name, "Import Data File's List")
_FLAGS(sys.argv)
for _import in _FLAGS.import_name:
    if _import == "social_environment":
        _MODULE_DIR = os.path.join(_COMMON_PATH, "..", _import)

        _INPUT_MCF_FILE_PATH = os.path.join(
            _MODULE_DIR, "output_files",
            "eurostat_population_social_environment.mcf")
        _OUTPUT_MCF_FILE_PATH = os.path.join(
            _MODULE_DIR, "output_files",
            "eurostat_population_social_environment_deno.mcf")
    elif _import == "bmi":
        _MODULE_DIR = os.path.join(_COMMON_PATH, "..", _import)

        _INPUT_MCF_FILE_PATH = os.path.join(_MODULE_DIR, "output_files",
                                            "eurostat_population_bmi.mcf")
        _OUTPUT_MCF_FILE_PATH = os.path.join(
            _MODULE_DIR, "output_files", "eurostat_population_bmi_deno.mcf")
    elif _import == "alcohol_consumption":
        _MODULE_DIR = os.path.join(_COMMON_PATH, "..", _import)

        _INPUT_MCF_FILE_PATH = os.path.join(
            _MODULE_DIR, "output_files",
            "eurostat_population_alcoholconsumption.mcf")
        _OUTPUT_MCF_FILE_PATH = os.path.join(
            _MODULE_DIR, "output_files",
            "eurostat_population_alcoholconsumption_deno.mcf")
    elif _import == "tobacco_consumption":
        _MODULE_DIR = os.path.join(_COMMON_PATH, "..", _import)

        _INPUT_MCF_FILE_PATH = os.path.join(
            _MODULE_DIR, "output_files",
            "eurostat_population_tobaccoconsumption.mcf")
        _OUTPUT_MCF_FILE_PATH = os.path.join(
            _MODULE_DIR, "output_files",
            "eurostat_population_tobaccoconsumption_deno.mcf")
    elif _import == "physical_activity":
        _MODULE_DIR = os.path.join(_COMMON_PATH, "..", _import)

        _INPUT_MCF_FILE_PATH = os.path.join(
            _MODULE_DIR, "output_files",
            "eurostat_population_physicalactivity.mcf")
        _OUTPUT_MCF_FILE_PATH = os.path.join(
            _MODULE_DIR, "output_files",
            "eurostat_population_physicalactivity_deno.mcf")
    elif _import == "fruits_vegetables":
        _MODULE_DIR = os.path.join(_COMMON_PATH, "..", _import)

        _INPUT_MCF_FILE_PATH = os.path.join(
            _MODULE_DIR, "output_files",
            "eurostat_population_fruits_vegetables.mcf")
        _OUTPUT_MCF_FILE_PATH = os.path.join(
            _MODULE_DIR, "output_files",
            "eurostat_population_fruits_vegetables_deno.mcf")

_INCOME_QUINTILE_VALUES = {
    "IncomeOf0To20Percentile": "[0 20 Percentile]",
    "IncomeOf20To40Percentile": "[20 40 Percentile]",
    "IncomeOf40To60Percentile": "[40 60 Percentile]",
    "IncomeOf60To80Percentile": "[60 80 Percentile]",
    "IncomeOf80To100Percentile": "[80 100 Percentile]",
}

_N_PORTION_VALUES = {
    "0Portion": "[Portion 0]",
    "From1To4Portion": "[1 4 Portion]",
    "5PortionOrMore": "[5 - Portion]",
}

_NAME_PROP_REPLACEMENTS = {
    ", Among": " Among",
    "Population:,": "Population:",
    "Percentage,": "Percentage",
    "Among,": "Among",
    "ACitizen": "A Citizen",
    "To": "To ",
    "Of": "Of ",
    "To299": "To 299",
    "To149": "To 149",
    "Least30": "Least 30",
    "Normalweight": "Normal Weight"
}

_ADDITIONAL_NAME_PROP_REPLACEMENTS = {' Among': ''}


def _update_name_property(name_prop: str) -> str:
    """
    Updates the name property.

    Args:
        name_prop (str): name property

    Returns:
        str: updated name property
    """

    name_prop = name_prop.rstrip(', ')
    name_prop = name_prop.rstrip('with')
    # Adding spaces before every capital letter,
    # to make SV look more like a name.
    name_prop = re.sub(r"(\w)([A-Z])", r"\1 \2", name_prop)
    name_prop = "name: \"" + name_prop + "\""
    for key, value in _NAME_PROP_REPLACEMENTS.items():
        name_prop = name_prop.replace(key, value)
    if name_prop.strip().endswith('Among"'):
        for key, value in _ADDITIONAL_NAME_PROP_REPLACEMENTS.items():
            name_prop = name_prop.replace(key, value)
    return name_prop


# pylint: disable = too-many-return-statements
# pylint: disable = too-many-branches
def _generate_pv_node(prop: str) -> str:
    """
    Returns the PV for the sv property.

    Args:
        prop (str): property

    Returns:
        str: property-value
    """

    if prop in ["Count"]:
        return "continue"
    if "PhysicalActivity" in prop:
        return f"healthBehavior: dcs:{prop}"
    if "Male" in prop or "Female" in prop:
        return f"gender: dcs:{prop}"
    if "Aerobic" in prop or "MuscleStrengthening" in prop \
        or "Walking" in prop or "Cycling" in prop:
        return f"exerciseType: dcs:{prop}"
    if "Education" in prop:
        return f"educationalAttainment: dcs:{prop.replace('Or', '__')}"
    if "Percentile" in prop:
        income_quin = _INCOME_QUINTILE_VALUES[prop]
        return f"income: {income_quin}"
    if "Portions" in prop:
        n_portion = _N_PORTION_VALUES[prop]
        return f"consumptionQuantity {n_portion}"
    if "Strong" in prop or "Intermediate" in prop or "Poor" in prop:
        return f"\nsocialSupportLevel: dcs:{prop}"
    if "Relatives" in prop:
        return f"\nsocialSupportBeneficiaryType: dcs:{prop}"
    if "InformalCare" in prop:
        return f"\nsocialSupportType: dcs:{prop}"
    if "AtLeastOnceAWeek" in prop:
        return f"\nactivityFrequency: dcs:{prop}"
    if "Urban" in prop or "Rural" in prop:
        return f"placeOfResidenceClassification: dcs:{prop}"
    if "Limitation" in prop:
        return f"globalActivityLimitationindicator: dcs:{prop}"
    if "ModerateActivity" in prop or "HeavyActivity" in prop\
        or "NoActivity" in prop:
        prop = prop.replace('ModerateActivityOrHeavyActivity', \
                         'ModerateActivityLevel__HeavyActivity')
        return f"physicalActivityEffortLevel: dcs:{prop}Level"
    if "AtLeast30MinutesPerDay" in prop:
        return f"activityFrequency: dcs{prop}"
    if "Minutes" in prop:
        if "OrMoreMinutes" in prop:
            return f"duration: [{prop.replace('OrMoreMinutes','')} - Minutes]"
        if "To" in prop:
            prop = prop.replace('Minutes', '').replace('To', ' ')
            return f"duration: [{prop} Minutes]"
        return f"duration: [Minutes {prop.replace('Minutes','')}]"
    if "ForeignBorn" in prop or "Native" in prop:
        return f"nativity: dcs:{prop.replace('CountryOfBirth','')}"
    if "ForeignWithin" in prop or "ForeignOutside" in prop\
        or "Citizen" in prop:
        return f"citizenship: dcs:{prop.replace('Citizenship','')}"
    if "weight" in prop \
      or "Obese" in prop or "Obesity" in prop:
        return f"healthBehavior: dcs:{prop}"
    return None


# pylint: enable = too-many-return-statements
# pylint: enable = too-many-branches


def generate_mcf_template(stat_var: str, mcf_template: str,
                          xtra_pvs: list) -> str:
    """
    This method generates MCF String w.r.t
    dataframe headers and defined MCF template.

    Args:
        stat_var (str): StatVar Name
        mcf_template (str): Input MCF Template
        xtra_pvs (list): List of additional property values

    Returns:
        str: String of Generated MCF
    """
    mcf_nodes = []
    pvs = xtra_pvs
    dcid = stat_var
    sv_name = ""
    sv_prop = [prop for prop in stat_var.split("_") if stat_var.strip()]
    for prop in sv_prop:
        prop_updated = _generate_pv_node(prop)
        if prop_updated == "continue":
            continue
        if prop in ["Person"]:
            sv_name = "Population: " + sv_name
        elif prop == "Percent":
            sv_name = sv_name + "Percentage"
        elif prop == "In":
            sv_name = sv_name + "Among"
        else:
            sv_name = sv_name + prop + ", "
            pvs.append(prop_updated)
    sv_name = _update_name_property(sv_name)
    pvs.append(sv_name)
    mcf_nodes.append(mcf_template.format(dcid=dcid, xtra_pvs='\n'.join(pvs)))
    mcf = '\n'.join(mcf_nodes)
    return mcf


def write_to_mcf_path(final_mcf_nodes: list, mcf_path: str) -> None:
    final_mcf = '\n'.join(final_mcf_nodes)
    # Writing Genereated MCF to local path.
    with open(mcf_path, 'w+', encoding='utf-8') as f_out:
        f_out.write(final_mcf.rstrip('\n'))


if __name__ == '__main__':
    actual_mcf_template = ("Node: dcid:{dcid}\n"
                           "typeOf: dcs:StatisticalVariable\n"
                           "populationType: dcs:Person\n"
                           "statType: dcs:measuredValue\n"
                           "measuredProperty: dcs:count\n"
                           "{xtra_pvs}\n")
    with open(_INPUT_MCF_FILE_PATH, "r", encoding="UTF-8") as mcf_file:
        sv_mcf = mcf_file.read()
        deno_matched = re.findall(r"(measurementDenominator: dcs:)(\w+)", \
                                  sv_mcf)
        f_deno = []
        for deno in deno_matched:
            f_deno.append(deno[1])
        f_deno = list(set(f_deno))
        node_status = check_dcid_existence(f_deno)
        f_deno = []
        for node, status in node_status.items():
            if not status:
                f_deno.append(node)
        f_deno.sort()
        sv_mcf_nodes = []
        for deno in f_deno:
            sv_mcf = generate_mcf_template(deno, actual_mcf_template, [])
            sv_mcf_nodes.append(sv_mcf)
        write_to_mcf_path(sv_mcf_nodes, _OUTPUT_MCF_FILE_PATH)
