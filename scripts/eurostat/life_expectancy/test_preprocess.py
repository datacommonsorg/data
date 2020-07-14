import unittest
from parameterized import parameterized
import generate_mcf

class PreprocessTest(unittest.TestCase):
    @parameterized.expand([('singlevalue', '80Years', '[Years 80]'), 
                           ('interval','40To50Years', '[Years 40 50]'),
                           ('upperlimit', 'Upto1Years', '[Years - 1]'),
                           ('lowerlimit', '85OrMoreYears', '[Years 85 -]')])
    def test_convert_range(self, name, str_in, expected):
        self.assertEqual(generate_mcf.convert_range(str_in), expected)

if __name__ == '__main__':
    unittest.main()