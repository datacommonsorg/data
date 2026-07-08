import datetime
import os
import csv
import sys
import pandas as pd
from absl import logging, flags, app
from collections import Counter

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
current_year = datetime.datetime.now().year
statvar_csv = os.path.join(_MODULE_DIR, 'statvars.csv')
_GCS_OUTPUT_DIR = os.path.join(_MODULE_DIR, 'gcs_output')
input_directory = os.path.join(_GCS_OUTPUT_DIR, 'input_files')
output = os.path.join(_GCS_OUTPUT_DIR, 'output')
output_file_path = os.path.join(output, 'transformed_data_for_all_final.csv')

places_csv = os.path.join(_MODULE_DIR, 'places.csv')
skip_places_csv = os.path.join(_MODULE_DIR, 'skip_places.csv')

_UTIL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_UTIL_DIR, '../../../util/'))
import file_util

MEASUREMENT_METHOD = "WorldBank_WDI_CSV"

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "gs_path",
    "gs://unresolved_mcf/world_bank/datasets/observations/historical_retained/",
    "historical file path")
flags.DEFINE_string("historical_file", "bq-results-20250423.csv",
                    "historical file name")
flags.DEFINE_string(
    'historical_gcs_path',
    'https://storage.mtls.cloud.google.com/unresolved_mcf/world_bank/datasets/deleted_historical_data_06_2026.csv',
    'GCS path to the deleted historical data CSV file')

DCID_MAP = {}
IGNORE_DCIDS = set()


def _load_place_mapping():
    try:
        with open(places_csv, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                DCID_MAP[row['country code'].strip()] = row['dcid'].strip()
    except FileNotFoundError:
        logging.fatal(f"File not found: {places_csv}")
    except csv.Error as e:
        logging.fatal(f"Error reading CSV {places_csv}: {e}")

    try:
        with open(skip_places_csv, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                IGNORE_DCIDS.add(row['country code'].strip())
    except FileNotFoundError:
        logging.fatal(f"File not found: {skip_places_csv}")
    except csv.Error as e:
        logging.fatal(f"Error reading CSV {skip_places_csv}: {e}")


def transform_worldbank_csv(input_filename,
                            writer,
                            data_start_row=5,
                            write_header=False):
    processed_rows = set()
    try:
        with open(input_filename, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)

            header = None
            indicator_code_column_index = None
            country_code_column_index = None
            year_columns_start_index = None

            for i, row in enumerate(reader):
                if i == data_start_row - 1:
                    header = [col.strip().lower() for col in row]
                    try:
                        indicator_code_column_index = header.index(
                            'indicator code')
                        country_code_column_index = header.index('country code')
                        for index, col in enumerate(header):
                            try:
                                year = int(col)
                                if 1960 <= year <= current_year:
                                    year_columns_start_index = index
                                    break
                            except ValueError:
                                pass
                    except ValueError:
                        logging.info(
                            f"Error: Could not find required columns in header of '{input_filename}'."
                        )
                        return
                    if write_header:
                        writer.writerow([
                            'indicatorcode', 'statvar', 'measurementmethod',
                            'observationabout', 'observationdate',
                            'observationvalue', 'unit'
                        ])
                elif i >= data_start_row:
                    if header and indicator_code_column_index is not None and \
                            country_code_column_index is not None and year_columns_start_index is not None:
                        indicator_code = row[indicator_code_column_index].strip(
                        )
                        code_from_csv = row[country_code_column_index]
                        raw_country_code = "country/" + code_from_csv

                        if code_from_csv in IGNORE_DCIDS:
                            continue
                        if code_from_csv in DCID_MAP:
                            country_code = DCID_MAP[code_from_csv]
                        else:
                            country_code = raw_country_code

                        stat_var = "worldBank/" + indicator_code.replace(
                            '.', '_')

                        unit_value = get_unit_by_indicator(indicator_code)
                        for j in range(year_columns_start_index, len(row)):
                            year = header[j]
                            value = row[j].strip()
                            if value:
                                duplicate_key = (indicator_code, stat_var,
                                                 MEASUREMENT_METHOD,
                                                 country_code, year, unit_value)
                                if duplicate_key not in processed_rows:
                                    writer.writerow([
                                        indicator_code, stat_var,
                                        MEASUREMENT_METHOD, country_code, year,
                                        value, unit_value
                                    ])
                                    processed_rows.add(duplicate_key)

    except FileNotFoundError:
        logging.fatal(f"Error: Input file '{input_filename}' not found.")
    except Exception as e:
        logging.fatal(f"An error occurred processing '{input_filename}': {e}")


def get_unit_by_indicator(target_indicator_code):
    try:
        with open(statvar_csv, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)

            if header:
                try:
                    indicator_code_index = header.index('seriescode')
                    unit_index = header.index('unit')
                except ValueError:
                    return ""

                for row in reader:
                    if len(row) > max(indicator_code_index, unit_index):
                        indicator = row[indicator_code_index].strip()
                        unit = row[unit_index].strip()
                        if indicator == target_indicator_code:
                            return unit
            return ""
    except FileNotFoundError:
        return ""
    except Exception as e:
        logging.warning(
            f"Error while reading unit for indicator {target_indicator_code}: {e}"
        )
        return ""


def main(_):
    _load_place_mapping()
    input_files = [
        os.path.join(input_directory, f)
        for f in os.listdir(input_directory)
        if f.endswith('.csv')
    ]
    try:
        os.makedirs(output, exist_ok=True)
        with open(output_file_path, 'w', newline='',
                  encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            first_file_processed = False

            for input_file in input_files:
                logging.info(f"Processing: {input_file}")
                transform_worldbank_csv(input_file,
                                        writer,
                                        write_header=not first_file_processed)
                first_file_processed = True

        logging.info(
            f"\nSuccessfully processed {len(input_files)} files. Combined output written to '{output_file_path}'"
        )

        # Read deleted historical data from GCS if it exists
        try:
            logging.info(
                f"Reading historical deleted data from GCS: {FLAGS.historical_gcs_path}"
            )
            final_df = pd.read_csv(output_file_path)
            with file_util.FileIO(FLAGS.historical_gcs_path, 'r') as f:
                deleted_df = pd.read_csv(f)

            # Combine dataframes. final_df is placed first so its versions are preferred.
            final_df = pd.concat([final_df, deleted_df], ignore_index=True)

            # Deduplicate based on composite keys, keeping the first occurrence (from final_df)
            composite_keys = [
                'indicatorcode', 'statvar', 'measurementmethod',
                'observationabout', 'observationdate', 'unit'
            ]
            final_df = final_df.drop_duplicates(subset=composite_keys,
                                                keep='first')
            final_df.to_csv(output_file_path, index=False)
            logging.info(
                "Successfully merged and de-duplicated deleted historical data."
            )
        except Exception as e:
            logging.warning(
                f"Could not read historical deleted data from GCS: {e}. Proceeding with fresh data only."
            )

        file_util.file_copy(f'{FLAGS.gs_path}{FLAGS.historical_file}',
                            f'{output}/{FLAGS.historical_file}')

        expected_output_files = [
            FLAGS.historical_file, 'transformed_data_for_all_final.csv'
        ]
        actual_files = os.listdir(output)
        if Counter(expected_output_files) != Counter(actual_files):
            logging.fatal("Actual otuput files are not equal to expected files")
        else:
            logging.info("Successfully processed")
    except Exception as e:
        logging.fatal(f"An error occurred in the main function: {e}")


if __name__ == "__main__":
    app.run(main)
