import csv
import os
import re
import shutil

try:
    from absl import logging
    logging.set_verbosity(logging.INFO)
except ImportError:
    import logging as std_logging

    class _CompatLogger:
        def __init__(self):
            self._logger = std_logging.getLogger(__name__)
            self._logger.setLevel(std_logging.INFO)
            if not self._logger.handlers:
                handler = std_logging.StreamHandler()
                handler.setFormatter(
                    std_logging.Formatter('%(levelname)s:%(message)s'))
                self._logger.addHandler(handler)

        def set_verbosity(self, level):
            self._logger.setLevel(level)

        def info(self, msg, *args, **kwargs):
            self._logger.info(msg, *args, **kwargs)

        def warning(self, msg, *args, **kwargs):
            self._logger.warning(msg, *args, **kwargs)

        def error(self, msg, *args, **kwargs):
            self._logger.error(msg, *args, **kwargs)

    logging = _CompatLogger()
    logging.set_verbosity(std_logging.INFO)


def preprocess(base_path='.'):
    folder_name = 'gcs_output/source_files'
    target_folder = os.path.join(base_path, folder_name)
    counters_folder = os.path.join(base_path, 'counters')
    os.makedirs(counters_folder, exist_ok=True)
    output_folder = os.path.join(base_path, 'output')
    os.makedirs(output_folder, exist_ok=True)

    custom_schema_file = os.path.join(
        base_path, 'oecd_regional_education_custom_schema.mcf')
    if os.path.isfile(custom_schema_file):
        shutil.copyfile(
            custom_schema_file,
            os.path.join(output_folder, 'oecd_regional_education_custom_schema.mcf'))
        logging.info(f"Copied custom schema to {output_folder}")

    places_resolved_file = os.path.join(
        base_path, 'oecd_regional_education_places_resolved.csv')
    valid_places = set()
    if os.path.isfile(places_resolved_file):
        with open(places_resolved_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('dcid', '').strip():
                    valid_places.add(row['place_name'].strip())
        logging.info(f"Loaded {len(valid_places)} valid places from {places_resolved_file}")
    else:
        logging.warning(f"Places resolved file not found: {places_resolved_file}")

    if not os.path.isdir(target_folder):
        logging.error(f"Folder '{folder_name}' not found in '{base_path}'")
        return

    pattern = re.compile(r'^A.*$', re.IGNORECASE)
    raw_file = None
    for filename in os.listdir(target_folder):
        if pattern.match(filename):
            raw_file = filename
            break

    target_csv = os.path.join(target_folder, 'oecd_regional_education_data.csv')

    if raw_file:
        src_path = os.path.join(target_folder, raw_file)
        tmp_path = os.path.join(target_folder, 'filtered_tmp.csv')
        logging.info(f"Filtering '{raw_file}' into 'oecd_regional_education_data.csv'...")
        _filter_csv(src_path, tmp_path, valid_places)
        if os.path.exists(target_csv):
            os.remove(target_csv)
        os.rename(tmp_path, target_csv)
        if src_path != target_csv and os.path.exists(src_path):
            os.remove(src_path)
        logging.info("Preprocessing and filtering completed successfully.")
    elif os.path.isfile(target_csv) and valid_places:
        tmp_path = os.path.join(target_folder, 'filtered_tmp.csv')
        logging.info(f"Checking and filtering existing '{target_csv}'...")
        _filter_csv(target_csv, tmp_path, valid_places)
        os.replace(tmp_path, target_csv)
        logging.info("Filtering completed successfully.")
    else:
        logging.info("No matching source data file found to process.")


def _filter_csv(src_path: str, dst_path: str, valid_places: set):
    with open(src_path, 'r', encoding='utf-8', errors='replace') as fin, \
         open(dst_path, 'w', encoding='utf-8', newline='') as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)

        header = next(reader, None)
        if not header:
            return
        writer.writerow(header)

        ref_area_idx = header.index('REF_AREA') if 'REF_AREA' in header else None
        if ref_area_idx is None:
            logging.warning("REF_AREA column not found in header, copying all rows.")
            for row in reader:
                writer.writerow(row)
            return

        kept = 0
        dropped = 0
        for row in reader:
            if len(row) > ref_area_idx and row[ref_area_idx].strip() in valid_places:
                writer.writerow(row)
                kept += 1
            else:
                dropped += 1

        logging.info(f"Filtered source data: {kept} rows kept, {dropped} rows with unresolved places dropped.")


if __name__ == '__main__':
    preprocess()