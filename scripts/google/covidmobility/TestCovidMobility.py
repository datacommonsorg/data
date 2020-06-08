import unittest
from covidmobility import CovidMobility


# NOTE: More testing will be added soon.


class TestStringMethods(unittest.TestCase):
    def test1_output(self):
        # Get the output file.
        CovidMobility('./test1.csv')
        # Get the content of the expected output.
        actual_f = open('./covid_mobility_output.mcf', 'r')
        actual = actual_f.read().replace('\n', '')
        actual_f.close()
        # Get the content of the written output.
        expected_f = open('./test1expectedoutput.mcf', 'r')
        expected = expected_f.read().replace('\n', '')
        expected_f.close()
        self.assertEqual(actual, expected)

    def test_csv_row_to_dict(self):
        row = ["AE", "United Arab Emirates", "", "", "2/26/20", "-2", "1", "-3", "-2", "3", "1"]
        covidmobility = CovidMobility('./test1.csv', less_output=False)
        output = covidmobility.csv_row_to_dict(row)
        self.assertEqual(output, {'dcid': 'country/ARE', 'country_code': 'AE', 'country': 'UnitedArabEmirates',
                                  'sub_region_1': '', 'sub_region_2': '', 'date': '2/26/20',
                                  'RetailAndRecreation': '-2', 'GroceryAndPharmacy': '1', 'Park': '-3',
                                  'TransitStation': '-2', 'Workplace': '3', 'Residential': '1'})

    def test_non_US_subregion_raises_exception(self):
        row = ["ES", "Spain", "Barcelona", "", "2/26/20", "0", "1", "2", "3", "4", "5"]
        with self.assertRaises(KeyError):
            self.covidmobility.csv_row_to_dict(row)


if __name__ == '__main__':
    unittest.main()
