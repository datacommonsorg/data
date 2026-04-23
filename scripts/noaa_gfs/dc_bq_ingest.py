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

import json
import re
from datetime import datetime, timezone
from absl import app, flags, logging
from google.cloud import bigquery
from google.cloud import storage
from google.api_core import exceptions

# --- FLAG DEFINITIONS ---
FLAGS = flags.FLAGS
flags.DEFINE_string('project_id', 'datcom-external', 'GCP Project ID.')
flags.DEFINE_string('bucket_name', 'datcom-prod-imports',
                    'GCS Bucket containing the CSVs.')
flags.DEFINE_string('gcs_prefix',
                    'scripts/noaa_gfs/NOAA_GlobalForecastSystem/output/',
                    'GCS prefix (folder path).')
flags.DEFINE_string('state_path',
                    'scripts/noaa_gfs/NOAA_GlobalForecastSystem/state.json',
                    'Path to state.json in GCS.')
flags.DEFINE_string('dataset_id', 'NOAA_GFS_data_commons',
                    'BigQuery Dataset ID.')
flags.DEFINE_string('staging_dataset_id', 'NOAA_GFS_Staging',
                    'BigQuery Staging Dataset ID.')
flags.DEFINE_string('table_id', 'Observation', 'BigQuery Table ID.')
flags.DEFINE_string('staging_table_id', 'Observation_Staging',
                    'Temporary Staging Table ID.')


def get_gcs_client():
    """Initializes the GCS client with a specific Project ID."""
    return storage.Client(project=FLAGS.project_id)


def load_state():
    """Reads state from GCS. Returns default if file doesn't exist."""
    client = get_gcs_client()
    bucket = client.bucket(FLAGS.bucket_name)
    blob = bucket.blob(FLAGS.state_path)

    try:
        state_data = blob.download_as_text()
        data = json.loads(state_data)
        logging.info(
            f"Successfully loaded state: {data.get('bq_ingest')} from gs://{FLAGS.bucket_name}/{FLAGS.state_path}"
        )
        return data
    except exceptions.NotFound:
        logging.warning("State file not found in GCS. Starting from scratch.")
        return {}


def update_bq_state(latest_date, latest_cycle):
    """Updates the bq_ingest key in the state.json ."""
    try:
        client = get_gcs_client()
        bucket = client.bucket(FLAGS.bucket_name)
        blob = bucket.blob(FLAGS.state_path)

        # Download existing to preserve 'date' and 'cycle' from grib_statvar_processor.py
        state = {}
        if blob.exists():
            state = json.loads(blob.download_as_text())

        state['bq_ingest'] = {
            "date":
                latest_date,
            "cycle":
                latest_cycle,
            "updated_at":
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }

        blob.upload_from_string(json.dumps(state, indent=2),
                                content_type='application/json')
        logging.info(
            f"Successfully updated BQ state to: {latest_date} {latest_cycle}z")
    except Exception as e:
        logging.error(f"Failed to update state.json: {e}")


def run_mapping_query(bq_client):
    """
    Executes the SQL transformation to map data from Staging to Final table.
    """
    final_table = f"{FLAGS.project_id}.{FLAGS.dataset_id}.{FLAGS.table_id}"
    staging_table = f"{FLAGS.project_id}.{FLAGS.staging_dataset_id}.{FLAGS.staging_table_id}"
    variable_table = f"{FLAGS.project_id}.{FLAGS.dataset_id}.Variable"
    place_table = f"{FLAGS.project_id}.{FLAGS.dataset_id}.Place"

    query = f"""
    INSERT INTO `{final_table}` (
        observation_about,
        variable_measured,
        variable_name,
        value,
        observation_date,
        measurement_method,
        unit,
        prov_id,
        provenance_name,
        geo_coordinates,
        place_name
    )
    SELECT 
        st.placeName,
        REGEXP_REPLACE(st.variableMeasured, r'^dcid:', '') AS variable_measured,
        v.name,
        CAST(st.value AS STRING),
        CAST(st.observationDate AS STRING),
        st.measurementMethod,
        st.unit,
        'dc/base/NOAA_GlobalForecastSystem',
        'NOAA_GlobalForecastSystem',
        ST_GEOGPOINT(st.longitude, st.latitude),
        p.name
    FROM `{staging_table}` AS st
    LEFT JOIN `{variable_table}` AS v
        ON REGEXP_REPLACE(st.variableMeasured, r'^dcid:', '') = v.id
    LEFT JOIN `{place_table}` AS p
        ON st.placeName = p.id;
    """

    try:
        # Run Ingestion
        logging.info("Starting transformation query...")
        query_job = bq_client.query(query)
        query_job.result()  # Wait for completion

        # Truncate staging table after successful migration
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
    table_ref = f"{FLAGS.project_id}.{FLAGS.staging_dataset_id}.{FLAGS.staging_table_id}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    try:
        logging.info(f"Loading to staging: {gcs_uri}")
        load_job = bq_client.load_table_from_uri(gcs_uri,
                                                 table_ref,
                                                 job_config=job_config)
        load_job.result()
        return True
    except Exception as e:
        logging.error(f"Failed to load {gcs_uri}: {e}")
        return False


def main(argv):
    """Entry point for the GCS-to-BigQuery ingestion script."""
    # Initialize Clients
    bq_client = bigquery.Client(project=FLAGS.project_id)
    storage_client = get_gcs_client()

    # 1. Load progress
    state = load_state()
    bq_progress = state.get('bq_ingest', {"date": "00000000", "cycle": "00"})
    last_key = f"{bq_progress['date']}_{bq_progress['cycle']}"

    # 2. Filter GCS CSVs
    bucket = storage_client.bucket(FLAGS.bucket_name)
    blobs = bucket.list_blobs(prefix=FLAGS.gcs_prefix)

    to_ingest = []
    for blob in blobs:
        if not blob.name.endswith('.csv'):
            continue

        # Match YYYYMMDD and HH cycle from filename
        filename = blob.name.split('/')[-1]
        match = re.fullmatch(r'noaa_gfs_output_(\d{8})_(\d{2})_\d{3}\.csv',
                             filename)
        if match:
            f_date, f_cycle = match.groups()
            if f"{f_date}_{f_cycle}" > last_key:
                to_ingest.append(
                    (f"gs://{FLAGS.bucket_name}/{blob.name}", f_date, f_cycle))

    if not to_ingest:
        logging.info("Everything is up to date in BigQuery.")
        return

    to_ingest.sort(key=lambda x: x[0])  # Chronological order

    # 3. Process Batch
    # Ensure staging is clean before starting a new batch
    staging_table = f"{FLAGS.project_id}.{FLAGS.staging_dataset_id}.{FLAGS.staging_table_id}"
    bq_client.query(f"TRUNCATE TABLE `{staging_table}`").result()

    success_count = 0
    current_max_date, current_max_cycle = bq_progress['date'], bq_progress[
        'cycle']

    for uri, f_date, f_cycle in to_ingest:
        if upload_gcs_to_staging(bq_client, uri):
            success_count += 1
            if f"{f_date}_{f_cycle}" > f"{current_max_date}_{current_max_cycle}":
                current_max_date, current_max_cycle = f_date, f_cycle

    logging.info(
        f"Ingestion batch complete. {success_count}/{len(to_ingest)} URIs processed."
    )

    # 4. Finalize
    if success_count > 0:
        if run_mapping_query(bq_client):
            update_bq_state(current_max_date, current_max_cycle)


if __name__ == "__main__":
    app.run(main)
