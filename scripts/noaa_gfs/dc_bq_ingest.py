# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Automates ingestion of processed NOAA GFS meteorological data into BigQuery.
"""

import os
from pathlib import Path
from absl import app, flags, logging
from google.cloud import bigquery

# --- FLAG DEFINITIONS ---
FLAGS = flags.FLAGS
flags.DEFINE_string('project_id', 'datcom', 'GCP Project ID.')
flags.DEFINE_string('dataset_id', 'noaa_gfs', 'BigQuery Dataset ID.')
flags.DEFINE_string('table_id', 'observations', 'BigQuery Table ID.')
flags.DEFINE_string('output_dir', 'output', 'Directory containing CSV files to upload.')

def upload_csv_to_bq(client, file_path):
    """
    Loads a single CSV file into the BigQuery table.
    """
    # Construct the full table reference: project.dataset.table
    table_ref = f"{FLAGS.project_id}.{FLAGS.dataset_id}.{FLAGS.table_id}"
    
    # Configure the load job
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,      # Skip the header row
        autodetect=True,          # Automatically infer types (Date, Float, String)
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND, # Append to existing data
    )

    try:
        with open(file_path, "rb") as source_file:
            logging.info(f"Uploading {file_path.name} to {table_ref}...")
            load_job = client.load_table_from_file(
                source_file, 
                table_ref, 
                job_config=job_config
            )
            
            # Wait for the job to complete
            load_job.result() 
            
        logging.info(f"Successfully loaded {load_job.output_rows} rows.")
        return True
    except Exception as e:
        logging.error(f"Failed to load {file_path.name}: {e}")
        return False

def main(argv):
    """Entry point for the script."""
    # Initialize BigQuery Client
    bq_client = bigquery.Client(project=FLAGS.project_id)
    
    output_path = Path(FLAGS.output_dir)
    
    # 1. Find all CSV files recursively
    csv_files = list(output_path.rglob('*.csv'))
    
    if not csv_files:
        logging.warning(f"No CSV files found in {FLAGS.output_dir}")
        return

    logging.info(f"Found {len(csv_files)} files for ingestion.")

    # 2. Loop and Upload
    success_count = 0
    for csv_file in csv_files:
        if upload_csv_to_bq(bq_client, csv_file):
            success_count += 1

    logging.info(f"Ingestion batch complete. {success_count}/{len(csv_files)} files uploaded.")

if __name__ == "__main__":
    app.run(main)
