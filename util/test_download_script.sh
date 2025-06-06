#!/bin/bash
# Define the path to your Python script
PYTHON_SCRIPT="download_util_script.py"

# --- Test Case 1: Successful Download (mandatory flags provided) ---
echo "--- Running Test Case 1: Successful Download ---"
TEST_URL="https://www.stats.govt.nz/assets/Topics/Population/Summary-figures-for-the-NZ-population-1991-2023.xlsx"
TEST_OUTPUT_FOLDER="./test_downloads/case1"


python3 "${PYTHON_SCRIPT}" \
  --url="${TEST_URL}" \
  --output_folder="${TEST_OUTPUT_FOLDER}" \

if [ $? -eq 0 ]; then
  echo "Test Case 1: PASSED - Script exited with success."
else
  echo "Test Case 1: FAILED - Script exited with error."
fi
echo ""

# --- Test Case 2: Missing URL (mandatory flag not provided) ---
echo "--- Running Test Case 2: Missing URL (should fail) ---"
# We expect this to fail because --url is marked as required
TEST_OUTPUT_FOLDER_2="./test_downloads/case2"

python3 "${PYTHON_SCRIPT}" \
  --output_folder="${TEST_OUTPUT_FOLDER_2}" \
  --unzip=False

if [ $? -ne 0 ]; then
  echo "Test Case 2: PASSED - Script exited with expected error (missing --url)."
else
  echo "Test Case 2: FAILED - Script did NOT exit with expected error."
fi
echo ""

# --- Test Case 3: Missing Output Folder (mandatory flag not provided) ---
echo "--- Running Test Case 3: Missing Output Folder (should fail) ---"
# We expect this to fail because --output_folder is marked as required
TEST_URL_3="http://example.com/some_file.zip" # Using a generic URL as it won't be downloaded

python3 "${PYTHON_SCRIPT}" \
  --url="${TEST_URL_3}" \
  --unzip=True

if [ $? -ne 0 ]; then
  echo "Test Case 3: PASSED - Script exited with expected error (missing --output_folder)."
else
  echo "Test Case 3: FAILED - Script did NOT exit with expected error."
fi
echo ""

# --- Test Case 4: Download and Unzip a mock file (optional flag true) ---
echo "--- Running Test Case 4: Download and Unzip (mocking for test) ---"

TEST_URL_4="https://www.stats.govt.nz/assets/Uploads/Employment-indicators/Employment-indicators-December-2024/Download-data/employment-indicators-december-2024.zip" # Assuming this is a valid zip
TEST_OUTPUT_FOLDER_4="./test_downloads/case4"

python3 "${PYTHON_SCRIPT}" \
  --url="${TEST_URL_4}" \
  --output_folder="${TEST_OUTPUT_FOLDER_4}" \
  --unzip=True

if [ $? -eq 0 ]; then
  echo "Test Case 4: PASSED - Script exited with success (assuming unzipping worked)."
  # Optional: Verify folder exists (and potentially content if you know what's in the zip)
  if [ -d "${TEST_OUTPUT_FOLDER_4}" ]; then
    echo "       Output folder '${TEST_OUTPUT_FOLDER_4}' created."
  else
    echo "       Output folder '${TEST_OUTPUT_FOLDER_4}' NOT created."
  fi
else
  echo "Test Case 4: FAILED - Script exited with error."
fi
echo ""


echo "Cleanup complete."