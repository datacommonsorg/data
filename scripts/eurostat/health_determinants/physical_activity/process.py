import os, sys
import re

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
from common.EuroStat import EuroStat

_MCF_TEMPLATE = ("Node: dcid:{pv1}\n"
                 "{pv14}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Person{pv2}{pv3}{pv4}{pv5}"
                 "{pv6}{pv7}{pv8}{pv9}{pv10}{pv11}{pv12}{pv13}{pv15}\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:count\n")


class EuroStatPhysicalActivity(EuroStat):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    def generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Args:
            df_cols (list) : List of DataFrame Columns

        Returns:
            None
        """
        # pylint: disable=R0914
        # pylint: disable=R0912
        # pylint: disable=R0915
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            incomequin = gender = education = healthbehavior = exercise = ''
            residence = activity = duration = countryofbirth = citizenship = ''
            lev_limit = bmi = sv_name = frequency = ''

            sv_temp = sv.split("_In_")
            denominator = "\nmeasurementDenominator: dcs:" + sv_temp[1]
            sv_property = sv.split("_")
            for prop in sv_property:
                if prop == "Percent":
                    sv_name = sv_name + "Percentage "
                elif prop == "In":
                    sv_name = sv_name + "Among "
                elif prop == "Count":
                    continue
                elif prop == "Person":
                    continue
                if "PhysicalActivity" in prop:
                    healthbehavior = "\nhealthBehavior: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Male" in prop or "Female" in prop:
                    gender = "\ngender: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Aerobic" in prop or "MuscleStrengthening" in prop \
                    or "Walking" in prop or "Cycling" in prop:
                    exercise = "\nexerciseType: dcs:" + prop.replace("Or", "__")
                    sv_name = sv_name + prop + ", "
                elif "Education" in prop:
                    education = "\neducationalAttainment: dcs:" + \
                        prop.replace("EducationalAttainment","")\
                        .replace("Or","__")
                    sv_name = sv_name + prop + ", "
                elif "Percentile" in prop:
                    incomequin = "\nincome: ["+prop.replace("IncomeOf","")\
                        .replace("To"," ").replace("Percentile"," Percentile")\
                        +"]"
                    sv_name = sv_name + prop.replace("Of","Of ")\
                        .replace("To"," To ") + ", "
                elif "Urban" in prop or "Rural" in prop:
                    residence = "\nplaceOfResidenceClassification: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Limitation" in prop:
                    lev_limit = "\nglobalActivityLimitationindicator: dcs:"\
                        + prop
                    sv_name = sv_name + prop + ", "
                elif "ModerateActivity" in prop or "HeavyActivity" in prop\
                    or "NoActivity" in prop:
                    activity = "\nphysicalActivityEffortLevel: dcs:"\
                    + prop.replace("ModerateActivityOrHeavyActivity",
                        "ModerateActivityLevel__HeavyActivity")+"Level"
                    sv_name = sv_name + prop + ", "
                elif "AtLeast30MinutesPerDay" in prop:
                    frequency = "\nactivityFrequency: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Minutes" in prop:
                    sv_name = sv_name + prop + ", "
                    if "OrMoreMinutes" in prop:
                        duration = "\nactivityDuration: [" + prop.replace\
                            ("OrMoreMinutes","") + " - Minute]"
                    elif "To" in prop:
                        duration = "\nactivityDuration: [" + prop.replace\
                            ("Minutes", "").replace("To", " ") + " Minute]"
                    else:
                        duration = "\nactivityDuration: [Minute " +\
                            prop.replace("Minutes","") + "]"
                elif "ForeignBorn" in prop or "Native" in prop:
                    countryofbirth = "\nnativity: dcs:" + \
                        prop.replace("CountryOfBirth","")
                    sv_name = sv_name + prop + ", "
                elif "Citizen" in prop:
                    citizenship = "\ncitizenship: dcs:" + \
                        prop.replace("Citizenship","")
                    sv_name = sv_name + prop + ", "
                elif "weight" in prop or "Normal" in prop \
                    or "Obese" in prop or "Obesity" in prop:
                    bmi = "__" + prop
                    healthbehavior = healthbehavior + bmi
                    sv_name = sv_name + prop + ", "
            # Making the changes to the SV Name,
            # Removing any extra commas, with keyword and
            # adding Population in the end
            sv_name = sv_name.replace(", Among", " Among")
            sv_name = sv_name.rstrip(', ')
            # Adding spaces before every capital letter,
            # to make SV look more like a name.
            sv_name = re.sub(r"(\w)([A-Z])", r"\1 \2", sv_name)
            sv_name = "name: \"" + sv_name + " Population\""
            sv_name = sv_name.replace("To299", "To 299").replace(
                "To149",
                "To 149").replace("ACitizen",
                                  "A Citizen").replace("Least30", "Least 30")

            final_mcf_template += _MCF_TEMPLATE.format(pv1=sv,
                                                       pv14=sv_name,
                                                       pv2=denominator,
                                                       pv3=incomequin,
                                                       pv4=education,
                                                       pv5=healthbehavior,
                                                       pv6=exercise,
                                                       pv7=residence,
                                                       pv8=activity,
                                                       pv9=duration,
                                                       pv10=gender,
                                                       pv11=countryofbirth,
                                                       pv12=citizenship,
                                                       pv13=lev_limit,
                                                       pv15=frequency) + "\n"

        # Writing Genereated MCF to local path.
        with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
        # pylint: enable=R0914
        # pylint: enable=R0912
        # pylint: enable=R0915


if __name__ == '__main__':
    input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "input_files")
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    # Defining Output Files
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output")

    csv_name = "eurostat_population_physicalactivity.csv"
    mcf_name = "eurostat_population_physicalactivity.mcf"
    tmcf_name = "eurostat_population_physicalactivity.tmcf"

    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)

    loader = EuroStat(ip_files, cleaned_csv_path, mcf_path, tmcf_path,
                      "physical_activity")
    sv_list = loader.process()

    loader.generate_mcf(sv_list)
    loader.generate_tmcf()
