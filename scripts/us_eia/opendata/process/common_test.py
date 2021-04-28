
import common
import os
import tempfile
import unittest

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestProcess(unittest.TestCase):

    def test_process(self):
        _TEST_CASES = [
            ('elec.txt', 'elec.csv', 'elec.mcf', 'elec.tmcf'),
        ]
        for (in_file, csv, mcf, tmcf) in _TEST_CASES:
          with tempfile.TemporaryDirectory() as tmp_dir:
            in_file = os.path.join(module_dir_, 'test_data', in_file)

            act_csv = os.path.join(tmp_dir, csv)
            act_mcf = os.path.join(tmp_dir, mcf)
            act_tmcf = os.path.join(tmp_dir, tmcf)
            common.process(in_file, act_csv, act_mcf, act_tmcf)

            with open(os.path.join(module_dir_, 'test_data', csv)) as f:
              exp_csv_data = f.read()
            with open(os.path.join(module_dir_, 'test_data', mcf)) as f:
              exp_mcf_data = f.read()
            with open(os.path.join(module_dir_, 'test_data', tmcf)) as f:
              exp_tmcf_data = f.read()
            with open(act_csv) as f:
              act_csv_data = f.read()
            with open(act_mcf) as f:
              act_mcf_data = f.read()
            with open(act_tmcf) as f:
              act_tmcf_data = f.read()

            os.remove(act_csv)
            os.remove(act_mcf)
            os.remove(act_tmcf)

          self.assertEqual(exp_csv_data, act_csv_data)
          self.assertEqual(exp_mcf_data, act_mcf_data)
          self.assertEqual(exp_tmcf_data, act_tmcf_data)


if __name__ == '__main__':
    unittest.main()
