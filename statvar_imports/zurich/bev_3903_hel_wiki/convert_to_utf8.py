import argparse
import chardet
import os
import sys
import logging

# Configure logging
# By default, logs INFO and higher to the console (stderr).
# You can customize this (e.g., to write to a file) by changing basicConfig.
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def convert_csv_to_utf8(input_csv_path):
    """
    Converts a CSV file from its detected encoding to UTF-8.

    Args:
        input_csv_path (str): The path to the input CSV file.

    Returns:
        str: The path to the newly created UTF-8 encoded CSV file, or None if conversion fails.
    """
    if not input_csv_path.lower().endswith('.csv'):
        logging.error(f"Input file '{input_csv_path}' is not a CSV file. Skipping conversion.")
        return None
    if not os.path.exists(input_csv_path):
        logging.error(f"Input CSV file '{input_csv_path}' not found. Cannot proceed.")
        return None

    # Determine the output file path (adds _utf8 before the .csv extension)
    base, ext = os.path.splitext(input_csv_path)
    output_csv_path = f"{base}_utf8{ext}"

    logging.info(f"Attempting to convert '{input_csv_path}' to UTF-8...")

    try:
        # 1. Detect the original encoding of the input CSV
        with open(input_csv_path, 'rb') as f_raw:
            raw_data = f_raw.read(100000) # Read up to 100KB for detection
        detection = chardet.detect(raw_data)
        detected_encoding = detection['encoding']
        
        chosen_encoding = None
        read_errors_mode = 'strict'

        if detected_encoding is None or detection['confidence'] < 0.8:
            logging.info(f"Encoding detection for '{input_csv_path}' was unreliable (detected: {detected_encoding}, confidence: {detection['confidence']:.2f}). Trying common fallbacks.")
            possible_fallbacks = ['cp1252', 'latin-1', 'utf-8']
            for enc in possible_fallbacks:
                try:
                    with open(input_csv_path, 'r', encoding=enc) as test_f:
                        test_f.read() # Attempt to read the entire file
                    chosen_encoding = enc
                    logging.info(f"Successfully read with fallback encoding: '{chosen_encoding}'.")
                    break
                except UnicodeDecodeError:
                    continue # Try the next fallback
            if chosen_encoding is None:
                # If no strict encoding worked, force utf-8 with replacement for conversion
                chosen_encoding = detected_encoding if detected_encoding else 'utf-8'
                read_errors_mode = 'replace' # Allow character replacement if decoding fails
                logging.warning(f"No strict encoding found. Forcing '{chosen_encoding}' with 'errors=replace' mode. Some characters might be lost or replaced.")
        else:
            chosen_encoding = detected_encoding
            logging.info(f"Detected encoding for '{input_csv_path}': '{detected_encoding}' (confidence: {detection['confidence']:.2f}).")

        # 2. Read the input CSV with the determined encoding
        with open(input_csv_path, 'r', encoding=chosen_encoding, errors=read_errors_mode) as infile:
            content = infile.read()

        # 3. Write the content to a new file with UTF-8 encoding
        with open(output_csv_path, 'w', encoding='utf-8') as outfile:
            outfile.write(content)

        logging.info(f"Successfully converted '{input_csv_path}' (from '{chosen_encoding}') to UTF-8: '{output_csv_path}'")
        return output_csv_path

    except UnicodeDecodeError as e:
        logging.error(f"Failed to decode '{input_csv_path}' with '{chosen_encoding}'. Details: {e}")
        logging.error("Please verify the file's original encoding. You might need to adjust the script's fallbacks or manually convert it first.")
        return None
    except Exception as e:
        logging.critical(f"An unexpected fatal error occurred during conversion of '{input_csv_path}': {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a CSV file to UTF-8 encoding.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'input_csv_path',
        type=str,
        help='The full or relative path to the input CSV file.'
    )

    args = parser.parse_args()
    converted_file = convert_csv_to_utf8(args.input_csv_path)

    if not converted_file:
        sys.exit(1) # Indicate an error if conversion failed