from absl import app
from absl import flags
from absl import logging
import chardet
import os
import sys

# Define flags using flags
FLAGS = flags.FLAGS
flags.DEFINE_string(
    'input_csv_path', None,
    'The full or relative path to the input CSV file.'
)

def convert_csv_to_utf8(input_csv_path):
    """
    Converts a CSV file from its detected encoding to UTF-8.

    Args:
        input_csv_path (str): The path to the input CSV file.

    Returns:
        str: The path to the newly created UTF-8 encoded CSV file, or None if conversion fails.
    """
    if not input_csv_path.lower().endswith('.csv'):
        logging.error("Input file '%s' is not a CSV file. Skipping conversion.", input_csv_path)
        return None
    if not os.path.exists(input_csv_path):
        logging.error("Input CSV file '%s' not found. Cannot proceed.", input_csv_path)
        return None

    # Determine the output file path (adds _utf8 before the .csv extension)
    base, ext = os.path.splitext(input_csv_path)
    output_csv_path = f"{base}_utf8{ext}"

    logging.info("Attempting to convert '%s' to UTF-8...", input_csv_path)

    try:
        # 1. Detect the original encoding of the input CSV
        with open(input_csv_path, 'rb') as f_raw:
            raw_data = f_raw.read(100000) # Read up to 100KB for detection
        detection = chardet.detect(raw_data)
        detected_encoding = detection['encoding']
        
        chosen_encoding = None
        read_errors_mode = 'strict'

        if detected_encoding is None or detection['confidence'] < 0.8:
            logging.info(
                "Encoding detection for '%s' was unreliable (detected: %s, confidence: %.2f). Trying common fallbacks.",
                input_csv_path, detected_encoding, detection['confidence']
            )
            possible_fallbacks = ['cp1252', 'latin-1', 'utf-8']
            for enc in possible_fallbacks:
                try:
                    with open(input_csv_path, 'r', encoding=enc) as test_f:
                        test_f.read() # Attempt to read the entire file
                    chosen_encoding = enc
                    logging.info("Successfully read with fallback encoding: '%s'.", chosen_encoding)
                    break
                except UnicodeDecodeError:
                    continue # Try the next fallback
            if chosen_encoding is None:
                # If no strict encoding worked, force utf-8 with replacement for conversion
                chosen_encoding = detected_encoding if detected_encoding else 'utf-8'
                read_errors_mode = 'replace' # Allow character replacement if decoding fails
                logging.warning(
                    "No strict encoding found. Forcing '%s' with 'errors=replace' mode. Some characters might be lost or replaced.",
                    chosen_encoding
                )
        else:
            chosen_encoding = detected_encoding
            logging.info(
                "Detected encoding for '%s': '%s' (confidence: %.2f).",
                input_csv_path, detected_encoding, detection['confidence']
            )

        # 2. Read the input CSV with the determined encoding
        with open(input_csv_path, 'r', encoding=chosen_encoding, errors=read_errors_mode) as infile:
            content = infile.read()

        # 3. Write the content to a new file with UTF-8 encoding
        with open(output_csv_path, 'w', encoding='utf-8') as outfile:
            outfile.write(content)

        logging.info(
            "Successfully converted '%s' (from '%s') to UTF-8: '%s'",
            input_csv_path, chosen_encoding, output_csv_path
        )
        return output_csv_path

    except UnicodeDecodeError as e:
        logging.error(
            "Failed to decode '%s' with '%s'. Details: %s",
            input_csv_path, chosen_encoding, e
        )
        logging.error(
            "Please verify the file's original encoding. You might need to adjust the script's fallbacks or manually convert it first."
        )
        return None
    except Exception as e:
        logging.critical(
            "An unexpected fatal error occurred during conversion of '%s': %s",
            input_csv_path, e
        )
        return None

def main(argv):
    """
    Main function to parse arguments and initiate CSV conversion.
    """
    del argv  # Unused.
    
    if FLAGS.input_csv_path is None:
        logging.error("The '--input_csv_path' flag is required.")
        sys.exit(1)

    converted_file = convert_csv_to_utf8(FLAGS.input_csv_path)

    if not converted_file:
        sys.exit(1) # Indicate an error if conversion failed

if __name__ == '__main__':
    app.run(main)