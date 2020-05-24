from random import random
import sys
sys.path.insert(1, '../../')
import util.county_to_dcid as county_to_dcid
import util.alpha2_to_dcid as alpha2_to_dcid
import util.name_to_alpha2 as name_to_alpha2


def skip_value(skip_pct) -> bool:
    """Given the amount of cells you skip in percent, will return whether to skip that specific one."""
    return random() <= skip_pct


class CovidMobility:
    """
    Converts a Google COVID-19 Mobility Report CSV file to MCF.
    :arg input_file: Google COVID-19 Mobility Report CSV file (11 rows in total).
    """

    def __init__(self, input_file: str, less_output: bool = False) -> None:
        self.input_csv: str = input_file
        self.less_output = less_output

        self.mobility_locations: dict = {}
        self.data: list = []
        self.output_file = open('./covid_mobility_output.mcf', 'w+')

        self.parse_data_from_input_csv()
        self.write_statistical_pop_node()
        self.write_observation_nodes()

        self.output_file.close()

    def parse_data_from_input_csv(self) -> None:
        """
        Given an input Google COVID-19 Mobility Report CSV file, read from it and generate a unique ID for each
        different location.
        """
        with open(self.input_csv, 'r+') as f:
            # Ignore the first row from csv, since it's the column titles.
            rows = f.read().split("\n")[1:]

            for row in rows:
                # If parameter less_output==True, then only output less than 1% of the data.
                if self.less_output and skip_value(skip_pct=0.99999):
                    continue

                row_as_list: list = row.split(',')

                # There must be 11 rows, otherwise skip that row.
                if len(row_as_list) != 11:
                    continue

                try:
                    row_data: dict = self.csv_row_to_dict(row_as_list)
                except KeyError:
                    print('Skipped: ' + str(row_as_list))
                    continue
                self.data.append(row_data)

                self.generate_node_id_for_row(row_data)

    def generate_node_id_for_row(self, row_data: dict) -> None:
        """
        Generates a new key->value on the mobility_locations containing: location_type, place_categories
        :arg row_data: the row data represented as a dictionary.
        """
        location_name: str = row_data['sub_region_2'] + row_data['sub_region_1'] + row_data['country']
        location_dcid: str = row_data['dcid']

        self.mobility_locations[location_dcid] = {}
        self.mobility_locations[location_dcid]["place_categories"] = {
            "RetailAndRecreation": f"{location_name}_RetailAndRecreation",
            "GroceryAndPharmacy": f"{location_name}_GroceryAndPharmacy",
            "Park": f"{location_name}_Park",
            "TransitStation": f"{location_name}_TransitStation",
            "Workplace": f"{location_name}_Workplace",
            "Residential": f"{location_name}_Residential"
        }

    @staticmethod
    def get_dcid_from_region(sub_region_2, sub_region_1, country_code) -> str:
        """
        Convert region to dcid.
        :param sub_region_2: Usually a US County.
        :param sub_region_1: State or Province
        :param country_code: Country Code as alpha
        :return location_dcid
        :except KeyError if any of the regions aren't hashable
        """

        # If key doesn't exist in the dictionary, it will throw an KeyError Exception.
        if sub_region_2:
            state_alpha_code: str = name_to_alpha2.USSTATE_MAP[sub_region_1]
            dcid: str = county_to_dcid.COUNTY_MAP[state_alpha_code][sub_region_2]
        elif sub_region_1:
            region_alpha_code: str = name_to_alpha2.USSTATE_MAP[sub_region_1]
            dcid: str = alpha2_to_dcid.USSTATE_MAP[region_alpha_code]
        else:
            dcid: str = alpha2_to_dcid.COUNTRY_MAP[country_code]
        return dcid

    def csv_row_to_dict(self, row: list) -> dict:
        """
        Given a row from an input file, generate a dictionary for it.
        :arg row: a list of strings separated by commas, where each index is a column.
        :returns data_as_dict: the row's data where each column is a key.
        :except KeyError if there is no dcid for given place.
        """

        country_code: str = row[0]
        country: str = row[1].replace(' ', '')
        sub_region_1: str = row[2].replace(' ', '')
        sub_region_2: str = row[3]
        dcid: str = self.get_dcid_from_region(sub_region_2, sub_region_1, country_code)

        return {
            'dcid': dcid,
            'country_code': country_code,
            'country': country,
            'sub_region_1': sub_region_1,
            'sub_region_2': sub_region_2,
            'date': row[4],
            'RetailAndRecreation': row[5],
            'GroceryAndPharmacy': row[6],
            'Park': row[7],
            'TransitStation': row[8],
            'Workplace': row[9],
            'Residential': row[10]
        }

    def write_statistical_pop_node(self) -> None:
        """
        Generates unique ID's for each location and generates a Statistical Population Node in MCF format.
        """
        for location_dcid in self.mobility_locations:
            location_data: dict = self.mobility_locations[location_dcid]
            place_categories: dict = location_data['place_categories']

            for category_name in place_categories:
                node_id: str = place_categories[category_name]
                statistical_pop_node: str = self.get_statistical_pop_nodes(local_id=node_id,
                                                                           location_dcid=f"{location_dcid}",
                                                                           place_category=category_name)
                self.output_file.write(statistical_pop_node + '\n\n')

    @staticmethod
    def get_statistical_pop_nodes(local_id: str, location_dcid: str, place_category: str) -> str:
        """
        Returns the MCF string representation of a statistical population node.
        :param local_id: unique local id for the node.
        :param location_dcid: the location's dcid.
        :param place_category: type of category (Pharmacy, Residence, Transit, etc...).
        :return: Statistical Population Node MCF String.
        """
        return (f"Node: {local_id}\n"
                "typeOf: schema:StatisticalPopulation\n"
                f"location: dcid:{location_dcid}\n"
                "populationType: dcs:PlaceVisitEvent\n"
                f"placeCategory: dcs:{place_category}")

    def write_observation_nodes(self) -> None:
        """
        For every data point, generate a new observation node with its corresponding information.
        Where observed_node is the statistical population node.
        """
        for row_data in self.data:
            location_dcid: str = row_data['dcid']

            place_categories: dict = self.mobility_locations[location_dcid]['place_categories']
            for category_name in place_categories:
                observation_node_id: str = place_categories[category_name]
                measured_value: str = row_data[category_name]

                # If the measured value is empty, skip it.
                if not measured_value:
                    continue

                observation_node: str = self.get_observation_node(observed_node=observation_node_id,
                                                                  date=row_data['date'],
                                                                  measured_value=measured_value)
                self.output_file.write(observation_node + '\n\n')

    @staticmethod
    def get_observation_node(observed_node: str, date: str, measured_value: str) -> str:
        """
        Returns the MCF string representation of an observation node.
        :param observed_node: The unique local ID of the reference node.
        :param date: Date of the observation.
        :param measured_value: Value of the observation.
        :return: Observation Node MCF String
        """
        # Remove any whitespace
        node_id: str = f"Node: {observed_node}_{date}_{measured_value}\n".replace(" ", "")

        return (f"{node_id}"
                "typeOf: schema:Observation\n"
                f"observedNode: l:{observed_node}\n"
                f'observationDate: "{date}"\n'
                "measuredProperty: dcs:covid19MobilityTrend\n"
                f"measuredValue: {measured_value}\n"
                "unit: dcs:Percent")


if __name__ == '__main__':
    CovidMobility('/Users/eduardomorales/Downloads/Global_Mobility_Report.csv', less_output=False)
