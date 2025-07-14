from absl import app
from absl import flags
from absl import logging
from google.cloud import bigquery
import pandas as pd

_FLAGS = flags.FLAGS

flags.DEFINE_string("out_file", "gender_income_inequality.csv",
                    "CSV output file name.")


def calculate_and_save_gender_inequality_locally():
    """
    Runs a BigQuery query to calculate gender income inequality and saves the
    results to a local CSV file.
    """
    client = bigquery.Client()

    # --- Configuration ---
    # Define a local file path for the output
    output_filename = _FLAGS.out_file

    # --- BigQuery SQL Query ---
    query = """
    WITH PivotedIncome AS (
      SELECT
        O.observation_about AS place_id,
        O.observation_date,
        MAX(IF(O.variable_measured = 'Median_Income_Person_15OrMoreYears_Male_WithIncome', SAFE_CAST(O.value AS FLOAT64), NULL)) AS male_income,
        MAX(IF(O.variable_measured = 'Median_Income_Person_15OrMoreYears_Female_WithIncome', SAFE_CAST(O.value AS FLOAT64), NULL)) AS female_income
      FROM
        `datcom-store.dc_kg_latest.StatVarObservation` AS O
      INNER JOIN
        `datcom-store.dc_kg_latest.Place` AS P ON O.observation_about = P.id
      WHERE
        O.measurement_method = 'CensusACS5yrSurvey'
        AND O.variable_measured IN (
          'Median_Income_Person_15OrMoreYears_Female_WithIncome',
          'Median_Income_Person_15OrMoreYears_Male_WithIncome'
        )
      GROUP BY
        place_id,
        observation_date
    )
    SELECT
      place_id,
      observation_date,
      (male_income - female_income) / (male_income + female_income) AS gender_income_inequality
    FROM
      PivotedIncome
    WHERE
      male_income IS NOT NULL
      AND female_income IS NOT NULL
      AND (male_income + female_income) > 0
    """

    logging.info("Submitting BigQuery query to fetch data...")
    # Execute the query and wait for the job to complete.
    query_job = client.query(query)

    logging.info(f"Job {query_job.job_id} is running. Waiting for results...")

    # Fetch results and convert to a Pandas DataFrame.
    results_df = query_job.to_dataframe()

    # Write the DataFrame to a local CSV file.
    results_df.to_csv(output_filename, index=False)
    logging.info(f"Success! Data written to local file: {output_filename}")


def main(_):
    calculate_and_save_gender_inequality_locally()


if __name__ == "__main__":
    app.run(main)
