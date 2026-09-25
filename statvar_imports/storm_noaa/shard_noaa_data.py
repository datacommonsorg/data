import csv
import os
import sys
from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string("input_dir", "noaa_storm_data", "Directory containing raw NOAA storm data files.")
flags.DEFINE_string("output_dir", "sharded_noaa_data", "Directory to store the sharded output files.")

def main(argv):
    logging.set_verbosity(logging.INFO)

    if not os.path.exists(FLAGS.input_dir):
        logging.error(f"Input directory '{FLAGS.input_dir}' not found.")
        sys.exit(1)

    if not os.path.exists(FLAGS.output_dir):
        os.makedirs(FLAGS.output_dir)
        logging.info(f"Created output directory: {FLAGS.output_dir}")
    else:
        logging.info(f"Output directory '{FLAGS.output_dir}' already exists.")

    shard_files = {}
    header = None
    total_lines_processed = 0

    logging.info("Finding all raw data files...")
    all_files = [os.path.join(path, name) for path, subdirs, files in os.walk(FLAGS.input_dir) for name in files if name.startswith("StormEvents_details") and name.endswith(".csv")]
    logging.info(f"Found {len(all_files)} files to process.")

    for input_file in all_files:
        logging.info(f"Processing file: {input_file}")
        with open(input_file, 'r', newline='', errors='ignore') as infile:
            reader = csv.reader(infile)
            
            current_header = next(reader)
            if header is None:
                header = current_header
                try:
                    # Find the index of the STATE_FIPS column
                    fips_index = header.index("STATE_FIPS")
                except ValueError:
                    logging.error("'STATE_FIPS' column not found in header. Cannot proceed.")
                    sys.exit(1)

            for row in reader:
                total_lines_processed += 1

                if len(row) <= fips_index:
                    logging.warning(f"Skipping malformed row {total_lines_processed + 1} in {input_file}: {row}")
                    continue

                fips_code = row[fips_index].strip()
                if not fips_code:
                    logging.warning(f"Skipping row with missing STATE_FIPS {total_lines_processed + 1} in {input_file}: {row}")
                    continue
                
                shard_key = fips_code
                out_filename = f"fips_{shard_key}.csv"
                out_path = os.path.join(FLAGS.output_dir, out_filename)

                if shard_key not in shard_files:
                    shard_files[shard_key] = open(out_path, 'w', newline='')
                    writer = csv.writer(shard_files[shard_key])
                    writer.writerow(header)
                    shard_files[shard_key].writer = writer # Attach writer to file handle
                    logging.info(f"Created shard file: {out_path}")
                
                shard_files[shard_key].writer.writerow(row)

                if total_lines_processed % 500000 == 0:
                    logging.info(f"Processed {total_lines_processed:,} total lines...")

    # Close all shard files
    for f in shard_files.values():
        f.close()

    logging.info(f"Sharding complete. Total lines processed: {total_lines_processed:,}")
    logging.info(f"Total shard files created: {len(shard_files)} in '{FLAGS.output_dir}/'")

if __name__ == "__main__":
    app.run(main)
