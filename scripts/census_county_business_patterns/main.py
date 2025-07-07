# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import io
from absl import app
from absl import flags
from absl import logging
from google.cloud import storage 

# Import your MSAProcessor class
from cbp_co import CBPCOProcessor
from cbp_msa import CBPMSAProcessor
from zbp import ZBPTotalsProcessor
from zbp_detail import ZBPDetailProcessor
FLAGS = flags.FLAGS

# Define flags for paths and year
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_LOCAL_OUTPUT_PATH = os.path.join(_MODULE_DIR, 'output')

flags.DEFINE_string('output_dir', _LOCAL_OUTPUT_PATH,
                    'Base directory to place the local output files.')
flags.DEFINE_string(
        'gcs_folder_path',
        'gs://unresolved_mcf/CensusCountyBusinessPattern',
        'Input directory where config files downloaded.')
flags.DEFINE_string('year', '2022', 'YYYY to generate stats for.')
flags.DEFINE_bool('test', False, 'Run in test mode.')


def main(argv):
  
  _FLAGS = flags.FLAGS 
  config_file_path = _FLAGS.gcs_folder_path
  gcs_bucket_name =  config_file_path.split('/')[2]
  storage_client = storage.Client()
  bucket = storage_client.bucket(gcs_bucket_name)
  blob_name = '/'.join(config_file_path.split('/')[3:])
  blob = bucket.blob(blob_name)
  # To ensure it acts as a folder prefix
  if blob_name:
      blob_name += '/'

  logging.info('Attempting to list files in GCS folder: gs://%s/%s', gcs_bucket_name, blob_name)

  try:
    bucket = storage_client.bucket(gcs_bucket_name)
    blobs = bucket.list_blobs(prefix=blob_name, delimiter='/')

    found_files = False
    for blob in blobs:
      # Filter for files (not 'directory' placeholders if delimiter is used)
      # Check if the blob name actually starts with the prefix and is not just the prefix itself
      if blob.name.startswith(blob_name) and blob.name != blob_name:
          found_files = True
          filename = os.path.basename(blob.name)
          logging.info('Found file: %s in GCS folder. Attempting to download.', filename)

          # Download the file content as text
          gcs_file_content = blob.download_as_text()
          logging.info('Successfully downloaded %s from GCS.', blob.name)

          # Use io.StringIO to treat the string content as a file-like object           
          input_file_obj = io.StringIO(gcs_file_content)
          # --- Conditional Processing Logic ---
          if 'msa' in filename.lower() and filename.lower().endswith('.txt'): # Explicitly check for .txt extension
            logging.info('Detected CBPMSA .txt file: %s. Initiating CBP MSA processing.', filename)
            processor = CBPMSAProcessor(
                input_file_obj=input_file_obj,
                output_dir=FLAGS.output_dir,
                year=FLAGS.year,
                is_test_run=FLAGS.test
            )
            processor.process_cbp_data()
            logging.info("process completed for cbp msa import")
          elif 'co' in filename.lower() and filename.lower().endswith('.txt'): # Explicitly check for .txt extension
            logging.info('Detected CBP CO .txt file: %s. Initiating CBP CO processing.', filename)
            processor = CBPCOProcessor(
                input_file_obj=input_file_obj,
                output_dir=FLAGS.output_dir,
                year=FLAGS.year,
                is_test_run=FLAGS.test
            )
            processor.process_co_data()
            logging.info("process completed for co import")
          elif 'totals' in filename.lower() and filename.lower().endswith('.txt'): # Explicitly check for .txt extension
                logging.info('Detected ZPB TOTALS .txt file: %s. Initiating ZPB TOTALS processing.', filename)
                processor = ZBPTotalsProcessor(
                    input_file_obj=input_file_obj,
                    output_dir=FLAGS.output_dir,
                    year=FLAGS.year,
                    is_test_run=FLAGS.test
                )
                processor.process_zbp_data()
                logging.info("process completed for zbp  import")

          elif 'detail' in filename.lower() and filename.lower().endswith('.txt'): # Explicitly check for .txt extension
                logging.info('Detected ZBP DETAILS .txt file: %s. Initiating ZBP DETAILS processing.', filename)
                processor = ZBPDetailProcessor(
                    input_file_obj=input_file_obj,
                    output_dir=FLAGS.output_dir,
                    year=FLAGS.year,
                    is_test_run=FLAGS.test
                )
                processor.process_zbp_detail_data()
                logging.info("process completed for co import")



    if not found_files:
        logging.warning('No .txt files found in the specified GCS folder: gs://%s/%s', gcs_bucket_name, blob_name)

  except Exception as e:
    logging.fatal('An unexpected error occurred during GCS folder listing or file processing: %s', e)
    


if __name__ == '__main__':
  app.run(main)

