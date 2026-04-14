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
flags.DEFINE_string('project_id', 'datcom-external', 'GCP Project ID.')
flags.DEFINE_string('bucket_name', 'datcom-prod-imports', 'GCS Bucket containing the CSVs.')
flags.DEFINE_string('gcs_prefix', 'scripts/noaa_gfs/NOAA_GlobalForecastSystem/output/', 'GCS prefix (folder path).')
flags.DEFINE_string('dataset_id', 'data_commons_noaa_gfs', 'BigQuery Dataset ID.')
flags.DEFINE_string('table_id', 'Observation', 'BigQuery Table ID.')
flags.DEFINE_string('staging_table_id', 'Observation_Staging', 'Temporary Staging Table ID.')

def run_mapping_query(bq_client):
    """
    Executes the SQL transformation to map data from Staging to Final table.
    """
    final_table = f"{FLAGS.project_id}.{FLAGS.dataset_id}.{FLAGS.table_id}"
    staging_table = f"{FLAGS.project_id}.{FLAGS.dataset_id}.{FLAGS.staging_table_id}"

    query = f"""
    INSERT INTO `{final_table}` (
        observation_about,
        variable_measured,
        value,
        observation_date,
        measurement_method,
        unit,
        prov_id
    )
    SELECT 
        placeName,
        variableMeasured,
        CAST(value AS STRING),
        CAST(observationDate AS STRING),
        measurementMethod,
        unit,
        'dc/base/NOAA_GlobalForecastSystem'
    FROM `{staging_table}`;
    """
    
    try:
        logging.info("Starting transformation query...")
        query_job = bq_client.query(query)
        query_job.result() # Wait for completion
        
        # Optional: Truncate staging table after successful migration
        bq_client.query(f"TRUNCATE TABLE `{staging_table}`").result()
        logging.info("Transformation complete and staging table cleared.")
        return True
    except Exception as e:
        logging.error(f"Mapping query failed: {e}")
        return False

def upload_gcs_to_staging(bq_client, gcs_uri):
    """
    Loads raw CSV data into the Staging table.
    """
    table_ref = f"{FLAGS.project_id}.{FLAGS.dataset_id}.{FLAGS.staging_table_id}"
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        # WRITE_APPEND used here to collect all CSVs before the final SQL transformation
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    try:
        logging.info(f"Loading to staging: {gcs_uri}")
        load_job = bq_client.load_table_from_uri(gcs_uri, table_ref, job_config=job_config)
        load_job.result() 
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

    # Step 1: Bulk Load everything into Staging
    success_count = 0
    for uri in csv_uris:
        if upload_gcs_to_staging(bq_client, uri):
            success_count += 1

    logging.info(f"Ingestion batch complete. {success_count}/{len(csv_uris)} URIs processed.")

    # Step 2: Run Mapping SQL if at least some files loaded
    if success_count > 0:
        run_mapping_query(bq_client)

if __name__ == "__main__":
    app.run(main)
