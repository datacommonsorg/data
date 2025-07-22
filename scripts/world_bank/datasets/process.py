import datetime
import os
import csv
import sys
from absl import logging, flags, app
from collections import Counter

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
current_year = datetime.datetime.now().year
statvar_csv = os.path.join(_MODULE_DIR, 'statvars.csv')
_GCS_OUTPUT_DIR = os.path.join(_MODULE_DIR, 'gcs_output')
input_directory = os.path.join(_GCS_OUTPUT_DIR, 'input_files')
output = os.path.join(_GCS_OUTPUT_DIR, 'output')
output_file_path = os.path.join(output, 'transformed_data_for_all_final.csv')

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
                            """Ignoring ValueError: expecting integer for year column identification."""
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
                        country_code = "country/" + row[
                            country_code_column_index].strip()
                        stat_var = "worldBank/" + indicator_code.replace(
                            '.', '_')

                        unit_value = get_unit_by_indicator(indicator_code)
                        for j in range(year_columns_start_index, len(row)):
                            year = header[j]
                            value = row[j].strip()
                            if value:
                                """Keeping the first occurrence and removing subsequent duplicates. Verified with source and production; the initial value from the source now is matching with the production data(checked for 4-5 samples) ."""
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
        return ""


def main(_):
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
        # historical_file = "bq-results-20250423.csv"
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
