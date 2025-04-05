import os
import csv

def process_csv_files(input_folder, output_folder, lines_to_read=60):
    """
    Reads CSV files from an input folder, extracts the first 'lines_to_read' lines,
    and writes them to new CSV files in an output folder.

    Args:
        input_folder (str): Path to the folder containing the input CSV files.
        output_folder (str): Path to the folder where the output CSV files will be written.
        lines_to_read (int): Number of lines to extract from each input CSV file.
    """

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            input_filepath = os.path.join(input_folder, filename)
            output_filepath = os.path.join(output_folder, filename)

            try:
                with open(input_filepath, 'r', newline='', encoding='utf-8') as infile, \
                     open(output_filepath, 'w', newline='', encoding='utf-8') as outfile:

                    reader = csv.reader(infile)
                    writer = csv.writer(outfile)
                    count = 0

                    for row in reader:
                        if count < lines_to_read:
                            writer.writerow(row)
                            count += 1
                        else:
                            break  # Stop reading after the desired number of lines

                print(f"Processed {filename} and saved to {output_filepath}")

            except FileNotFoundError:
                print(f"Error: File not found - {input_filepath}")
            except Exception as e:
                print(f"An error occurred processing {filename}: {e}")

# Example Usage:
input_folder_path = "/usr/local/google/home/chharish/Downloads/input_rwanda"  # Replace with your input folder path
output_folder_path = "/usr/local/google/home/chharish/opendata_africa/data/statvar_imports/opendataforafrica/rwanda_census/test_data" # Replace with your output folder path
process_csv_files(input_folder_path, output_folder_path)