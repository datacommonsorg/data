import unittest
from covidmobility import covid_mobility, csv_row_to_obj


# NOTE: More testing will be added soon.


class TestStringMethods(unittest.TestCase):
    def test1_output(self):
        # Get the output file.
        covid_mobility('./test1.csv')
        # Get the content of the expected output.
        actual_f = open('./output/covid_mobility_output.mcf', 'r')
        actual = actual_f.read().replace('\n', '')
        actual_f.close()
        # Get the content of the written output.
        expected_f = open('./test1expectedoutput.mcf', 'r')
        expected = expected_f.read().replace('\n', '')
        expected_f.close()
        self.assertEqual(actual, expected)

    def test_csv_row_to_dict(self):
        row = ["AE", "United Arab Emirates", "", "", "2/26/20", "-2", "1", "-3", "-2", "3", "1"]
        covidmobility = covid_mobility('./test1.csv')
        output = csv_row_to_obj(row)
        self.assertEqual(output, {'dcid': 'country/ARE', 'country_code': 'AE', 'country': 'UnitedArabEmirates',
                                  'sub_region_1': '', 'sub_region_2': '', 'date': '2/26/20',
                                  'LocalBusiness': '-2', 'GroceryStore&Pharmacy': '1', 'Park': '-3',
                                  'TransportHub': '-2', 'Workplace': '3', 'Residence': '1'})

    def test_non_US_subregion_raises_exception(self):
        row = ["ES", "Spain", "Barcelona", "", "2/26/20", "0", "1", "2", "3", "4", "5"]
        with self.assertRaises(KeyError):
            csv_row_to_obj(row)


if __name__ == '__main__':
    unittest.main()
