import os, sys
import re

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
from common.EuroStat import EuroStat

_MCF_TEMPLATE = ("Node: dcid:{pv1}\n"
                 "{pv11}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Person{pv2}{pv3}{pv4}{pv5}"
                 "{pv6}{pv7}{pv8}{pv9}{pv10}\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:count\n")


class EuroStatTobaccoConsumption(EuroStat):

    def generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template
        Args:
            df_columns (list) : List of DataFrame Columns
        Returns:
            None
        """
        # pylint: disable=R0914
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            incomequin = gender = education = frequenc_tobacco = activity =\
            residence = countryofbirth = citizenship = substance\
            = quantity = history = sv_name = ''

            sv_temp = sv.split("_In_")
            denominator = "\nmeasurementDenominator: dcs:" + sv_temp[1]
            sv_prop = sv_temp[0].split("_")
            sv_prop1 = sv_temp[1].split("_")
            for prop in sv_prop:
                if prop in ["Percent"]:
                    sv_name = sv_name + "Percentage"
                elif  "TobaccoSmoking" in prop or "NonSmoker" in prop or\
                    "ExposureToTobaccoSmoke" in prop or "FormerSmoker" in prop:
                    activity = "\nhealthBehavior: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Daily" in prop or "Occasional" in prop\
                     or "AtLeastOneHourPerDay" in prop or \
                    "LessThanOneHourPerDay" in prop:
                    frequenc_tobacco = "\nactivityFrequency: dcs:" + prop.replace(
                        "Or", "__")
                    sv_name = sv_name + prop + ", "
                elif "LessThanOnceAWeek" in prop or "AtLeastOnceAWeek" in\
                    prop or "RarelyOrNever" in prop :
                    frequenc_tobacco = "\nactivityFrequency: dcs:" + prop.replace(
                        "Or", "__")
                    sv_name = sv_name + prop + ", "
                elif "LessThan20CigarettesPerDay"in prop or \
                    "20OrMoreCigarettesPerDay" in prop \
                    or "DailyCigaretteSmoker20OrMorePerDay" in prop or \
                    "DailyCigaretteSmokerLessThan20PerDay" in prop:
                    quantity = "\nconsumptionQuantity: "+prop.replace\
                    ("LessThan20CigarettesPerDay","[- 20 Cigarettes]")\
                    .replace("20OrMoreCigarettesPerDay","[20 - Cigarettes]")\
                    .replace("DailyCigaretteSmoker20OrMorePerDay",\
                    "[20 - Cigarettes]").replace\
                    ("DailyCigaretteSmokerLessThan20PerDay","[- 20 Cigarettes]")
                    sv_name = sv_name + prop + ", "
                elif "Cigarette" in prop or "ECigarettes" in prop:
                    substance = "\ntobaccoUsageType: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif 'LessThan1Year' in prop or 'From1To5Years' in prop or \
                    'From5To10Years' in prop or '10YearsOrOver' in prop:
                    history = "\nactivityDuration: " + prop.replace\
                    ("LessThan1Year","[- 1 Year]").replace\
                    ("From1To5Years","[Years 1 5]")\
                    .replace("From5To10Years","[Years 5 10]").\
                    replace("10YearsOrOver","[10 - Years]")
                    sv_name = sv_name + prop.replace("From","From ").\
                        replace("To"," To ").replace("Years"," Years").\
                            replace("Than","Than ")+ ", "

            sv_name = sv_name + "Among"
            for prop in sv_prop1:
                if prop in ["Count", "Person"]:
                    continue
                if "Male" in prop or "Female" in prop:
                    gender = "\ngender: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Education" in prop:
                    education = "\neducationalAttainment: dcs:" + \
                        prop.replace("Or","__")
                    sv_name = sv_name + prop + ", "
                elif "Percentile" in prop:
                    incomequin = "\nincome: ["+prop.replace("Percentile",
                        "").replace("IncomeOf","").replace("To"," ")+\
                            " Percentile]"
                    sv_name = sv_name + prop.replace("Of","Of ")\
                        .replace("To"," To ") + ", "
                elif "Urban" in prop or "SemiUrban" in prop \
                    or "Rural" in prop:
                    residence = "\nplaceOfResidenceClassification: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "ForeignBorn" in prop or "Native" in prop:
                    countryofbirth = "\nnativity: dcs:" + \
                        prop.replace("CountryOfBirth","")
                    sv_name = sv_name + prop + ", "
                elif "WithinEU28AndNotACitizen" in prop or \
                    "CitizenOutsideEU28" in prop\
                    or "Citizen" in prop or "NotACitizen" in prop:
                    citizenship = "\ncitizenship: dcs:"+\
                    prop.replace("Citizenship","")
                    sv_name = sv_name + prop + ", "

            sv_name = sv_name.replace(", Among", " Among")
            sv_name = sv_name.rstrip(', ')
            sv_name = sv_name.rstrip('with')
            # Adding spaces before every capital letter,
            # to make SV look more like a name.
            sv_name = re.sub(r"(\w)([A-Z])", r"\1 \2", sv_name)
            sv_name = "name: \"" + sv_name + " Population\""
            sv_name = sv_name.replace("AWeek","A Week")\
            .replace("Than20","Than 20").replace("ACitizen","A Citizen")
            final_mcf_template += _MCF_TEMPLATE.format(pv1=sv,
                                                       pv14=sv_name,
                                                       pv2=denominator,
                                                       pv3=frequenc_tobacco,
                                                       pv4=gender,
                                                       pv5=activity,
                                                       pv6=education,
                                                       pv7=incomequin,
                                                       pv8=residence,
                                                       pv9=countryofbirth,
                                                       pv10=citizenship,
                                                       pv11=substance,
                                                       pv12=quantity,
                                                       pv13=history) + "\n"

        # Writing Genereated MCF to local path.
        with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
        # pylint: enable=R0914


if __name__ == '__main__':
    input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "input_files")
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    # Defining Output Files
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output")

    csv_name = "eurostat_population_tobaccoconsumption.csv"
    mcf_name = "eurostat_population_tobaccoconsumption.mcf"
    tmcf_name = "eurostat_population_tobaccoconsumption.tmcf"

    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)

    loader = EuroStatTobaccoConsumption(ip_files, cleaned_csv_path, mcf_path,
                                        tmcf_path, "tobacco_consumption")
    sv_list = loader.process()

    loader.generate_mcf(sv_list)
    loader.generate_tmcf()
