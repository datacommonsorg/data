import os, sys , re

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
from common.Eurostat import EuroStat

_MCF_TEMPLATE = ("Node: dcid:{pv1}\n"
                "{pv2}\n"
                "typeOf: dcs:StatisticalVariable\n"
                "populationType: dcs:Person{pv3}{pv4}{pv5}"
                "{pv6}{pv7}{pv8}{pv9}{pv10}{pv11}{pv12}{pv13}\n"
                "statType: dcs:measuredValue\n"
                "measuredProperty: dcs:count\n")

class EuroStatFruitsVegetables(EuroStat):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    def generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template.
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
            gender = education = portion = frequency = residence = ''
            countryofbirth = citizenship = lev_limit = sv_name = incomequin = ''
            coicop = ''
            sv_temp = sv.split("_In_")
            denominator = "\nmeasurementDenominator: dcs:" + sv_temp[1]
            sv_property = sv.split("_")
            for prop in sv_property:
                if prop == "Percent":
                    sv_name = sv_name + "Percentage "
                elif "Portions" in prop:
                    #                   sv_name = sv_name + prop + ", "
                    if "PortionsOrMore" in prop:
                        portion = "\nconsumptionQuantity: [" + prop.replace\
                            ("PortionsOrMore","") + " - Portions]"
                    elif "To" in prop:
                        portion = "\nconsumptionQuantity: [" + prop.replace\
                            ("Portions", "").replace("To", " ").replace\
                                ("From","") + " Portions]"
                    else:
                        portion = "\nconsumptionQuantity: [Portions " +\
                            prop.replace("Portions","") + "]"
                    sv_name = sv_name + prop + ", "
                elif prop == "In":
                    sv_name = sv_name + "Among "
                elif prop == "Count":
                    continue
                elif prop == "Person":
                    continue
                if "Male" in prop or "Female" in prop:
                    gender = "\ngender: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "ConsumptionOfPureFruitOrVegetableJuice" in prop:
                    coicop = "\nhealthBehavior: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "ConsumptionOfFruits" in prop or "ConsumptionOfVegetables"\
                    in prop or "SugarSweetenedSoftDrinks" in prop :
                    coicop = "\nhealthBehavior: dcs:" + prop.replace("Or", "__")
                    sv_name = sv_name + prop + ", "
                elif "UnderWeight" in prop or "Normal" in prop or "OverWeight"\
                        in prop or "PreObese" in prop or "Obesity" in prop:
                    sv_name = sv_name + prop + ", "
                    coicop = coicop + "__" + prop
                elif "Education" in prop:
                    education = "\neducationalAttainment: dcs:" + \
                        prop.replace("EducationalAttainment","")\
                        .replace("Or","__")
                    sv_name = sv_name + prop + ", "
                elif "Urban" in prop or "Rural" in prop or "SemiUrban" in prop:
                    residence = "\nplaceOfResidenceClassification: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Limitation" in prop:
                    lev_limit = "\nglobalActivityLimitationindicator: dcs:"\
                        + prop
                    sv_name = sv_name + prop + ", "
                elif "ForeignBorn" in prop or "Native" in prop:
                    countryofbirth = "\nnativity: dcs:" + \
                        prop.replace("CountryOfBirth","")
                    sv_name = sv_name + prop + ", "
                elif "Citizen" in prop:
                    citizenship = "\ncitizenship: dcs:" + \
                        prop.replace("Citizenship","")
                    sv_name = sv_name + prop + ", "
                elif "Percentile" in prop:
                    incomequin = "\nincome: ["+prop.replace("IncomeOf","")\
                        .replace("To"," ").replace("Percentile"," Percentile")\
                        +"]"
                    sv_name = sv_name + prop.replace("Of","Of ")\
                        .replace("To"," To ") + ", "
                elif "OnceADay" in prop or "AtLeastOnceADay" in prop or\
                        "AtleastTwiceADay" in prop or "LessThanOnceAWeek" \
                    in prop:
                    frequency = "\nactivityFrequency: dcs:" + prop\
                            .replace("Or","__")
                    sv_name = sv_name + prop + ", "
                elif "From1To3TimesAWeek" in prop or \
                    "From4To6TimesAWeek" in prop or "Never" \
                    in prop or "NeverOrOccasionally" in prop or "Daily" \
                    in prop:                   
                    frequency = "\nactivityFrequency: dcs:" + prop\
                            .replace("Or","__")
                    sv_name = sv_name + prop + ", "
    
            # Making the changes to the SV Name,
            # Removing any extra commas, with keyword and
            # adding Population in the end
            sv_name = sv_name.replace(", Among", " Among")
            sv_name = sv_name.rstrip(', ')
            sv_name = sv_name.rstrip('with')
            # Adding spaces before every capital letter,
            # to make SV look more like a name.
            sv_name = re.sub(r"(\w)([A-Z])", r"\1 \2", sv_name)
            sv_name = "name: \"Population: " + sv_name + "\""
            sv_name = sv_name.replace('AWeek', 'A Week')
            sv_name = sv_name.replace('From1', 'From 1')
            sv_name = sv_name.replace('To4', 'To 4')
            sv_name = sv_name.replace('To3', 'To 3')
            sv_name = sv_name.replace('ADay', 'A Day')
            sv_name = sv_name.replace('From4', 'From 4')
            sv_name = sv_name.replace('To6', 'To 6')
            sv_name = sv_name.replace('ACitizen', 'A Citizen')
            sv_name = sv_name.replace('Weig ', 'Weight ')
            sv_name = sv_name.replace('Normalweight', 'Normal Weight')
    
            final_mcf_template += _MCF_TEMPLATE.format(pv1=sv,
                                                        pv2=sv_name,
                                                        pv3=denominator,
                                                        pv4=education,
                                                        pv5=residence,
                                                        pv6=portion,
                                                        pv7=gender,
                                                        pv8=countryofbirth,
                                                        pv9=citizenship,
                                                        pv10=lev_limit,
                                                        pv11=coicop,
                                                        pv12=frequency,
                                                        pv13=incomequin) + "\n"
    
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
                                  "output_files")

    csv_name = "eurostat_population_fruitsvegetables.csv"
    mcf_name = "eurostat_population_fruitsvegetables.mcf"
    tmcf_name = "eurostat_population_fruitsvegetables.tmcf"

    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)

    loader = EuroStatFruitsVegetables(ip_files, cleaned_csv_path, mcf_path, tmcf_path,
                      "fruits_vegetables")
    sv_list = loader.process()

    # loader.generate_mcf(sv_list)
    # loader.generate_tmcf()