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
from absl import app, flags, logging
from google.cloud import bigquery
from google.cloud import storage

# --- FLAG DEFINITIONS ---
FLAGS = flags.FLAGS
flags.DEFINE_string('project_id', 'datcom', 'GCP Project ID.')
flags.DEFINE_string('bucket_name', 'datcom-prod-imports', 'GCS Bucket containing the CSVs.')
flags.DEFINE_string('gcs_prefix', 'scripts/noaa_gfs/NOAA_GlobalForecastSystem/output/', 'GCS prefix (folder path).')
flags.DEFINE_string('dataset_id', 'noaa_gfs', 'BigQuery Dataset ID.')
flags.DEFINE_string('table_id', 'observations', 'BigQuery Table ID.')

def upload_gcs_to_bq(bq_client, gcs_uri):
    """
    Triggers a BigQuery load job directly from a GCS URI.
    """
    table_ref = f"{FLAGS.project_id}.{FLAGS.dataset_id}.{FLAGS.table_id}"
    
    # Configure the load job
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,      # Skip the header row
        autodetect=True,          # Automatically infer types
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    try:
        logging.info(f"Starting load job for: {gcs_uri}")
        # Direct URI load
        load_job = bq_client.load_table_from_uri(
            gcs_uri, 
            table_ref, 
            job_config=job_config
        )
        
        # Wait for the job to complete
        load_job.result() 
            
        logging.info(f"Successfully loaded rows from {gcs_uri}. Job ID: {load_job.job_id}")
        return True
    except Exception as e:
        logging.error(f"Failed to load {gcs_uri}: {e}")
        return False

def main(argv):
    """Entry point for the GCS-to-BigQuery ingestion script."""
    # Initialize Clients
    bq_client = bigquery.Client(project=FLAGS.project_id)
    storage_client = storage.Client(project=FLAGS.project_id)
    
    # Get reference to the bucket and list blobs
    bucket = storage_client.bucket(FLAGS.bucket_name)
    blobs = bucket.list_blobs(prefix=FLAGS.gcs_prefix)
    
    # Filter for CSV files
    csv_uris = [f"gs://{FLAGS.bucket_name}/{blob.name}" for blob in blobs if blob.name.endswith('.csv')]
    
    if not csv_uris:
        logging.warning(f"No CSV files found at gs://{FLAGS.bucket_name}/{FLAGS.gcs_prefix}")
        return

    logging.info(f"Found {len(csv_uris)} files in GCS for ingestion.")

    # Loop and Trigger Load Jobs
    success_count = 0
    for uri in csv_uris:
        if upload_gcs_to_bq(bq_client, uri):
            success_count += 1

    logging.info(f"Ingestion batch complete. {success_count}/{len(csv_uris)} URIs processed.")

if __name__ == "__main__":
    app.run(main)
