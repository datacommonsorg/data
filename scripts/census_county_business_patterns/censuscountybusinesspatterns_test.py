import os
import sys
import logging, unittest
from absl import flags, app
import shutil
import io
from cbp_co import CBPCOProcessor
# from main import main, _LOCAL_OUTPUT_PATH, FLAGS # Import main and the path variable
FLAGS = flags.FLAGS
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_OUTPUT_DIR = os.path.join(_MODULE_DIR, 'test_data')
if not os.path.exists(_OUTPUT_DIR):
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
flags.DEFINE_bool('test', False, 'Run in test mode.')
flags.DEFINE_string('output_dir', _OUTPUT_DIR,
                    'Base directory to place the local output files.')


class TestCriteriaGasesTest(unittest.TestCase):

    def test_run(self):

        input_local_path = os.path.join(_MODULE_DIR, 'test_data')
        full_local_path = os.path.join(input_local_path, 'cbp16co.txt')
        with open(full_local_path, 'r', encoding='latin-1') as f:
            local_file_content = f.read()

        # Use io.StringIO to treat the string content as a file-like object
        # This maintains compatibility with your existing processor classes
        input_file_obj = io.StringIO(local_file_content)
        processing_year = 2016
        processor = CBPCOProcessor(input_file_obj=input_file_obj,
                                   output_dir=FLAGS.output_dir,
                                   year=processing_year,
                                   is_test_run=FLAGS.test)
        processor.process_co_data()
        logging.info("process completed for cbp co import")
        test_csv = os.path.join(_OUTPUT_DIR, 'cbp_2016_co.csv')
        expected_csv = os.path.join(_OUTPUT_DIR, 'expected_output.csv')
        with open(test_csv, 'r') as test:
            test_str: str = test.read().strip()
            with open(expected_csv, 'r') as expected:
                expected_str: str = expected.read().strip()
                self.assertEqual(test_str, expected_str)
        os.remove(test_csv)


if __name__ == '__main__':
    FLAGS(sys.argv)
    unittest.main()
