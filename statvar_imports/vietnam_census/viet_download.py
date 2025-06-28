import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, WebDriverException, StaleElementReferenceException
import os
import csv # Import csv module for handling CSV files

# --- Helper function for robust element finding ---
def find_element_any_context(driver, wait, locator, timeout=20):
    """
    Attempts to find an element, first on the default content,
    then by switching to an iframe if not found on default content.
    Returns the element and a boolean indicating if it was found in an iframe.
    """
    found_in_iframe = False
    
    # Try finding on default content first
    try:
        driver.switch_to.default_content() # Always start from default
        element = wait.until(EC.presence_of_element_located(locator))
        return element, found_in_iframe
    except TimeoutException:
        print(f"Element {locator} not found on default content within {timeout}s. Checking for iframe.")
    except Exception as e:
        print(f"Error checking default content for {locator}: {e}. Checking for iframe.")

    # If not found on default, try switching to iframe and finding there
    try:
        # Use a shorter wait for iframe availability within this helper
        WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))
        print(f"Switched to iframe. Trying to find element {locator} in iframe.")
        element = wait.until(EC.presence_of_element_located(locator))
        found_in_iframe = True
        return element, found_in_iframe
    except TimeoutException:
        print(f"Element {locator} not found in iframe within 5s.")
        return None, False
    except Exception as e:
        print(f"Error checking iframe for {locator}: {e}.")
        return None, False

# --- Method to provide URLs (replaces config file) ---
def get_gso_urls():
    """
    Returns a list of GSO PX-Web URLs to download data from.
    """
    urls = [
             "https://www.gso.gov.vn/en/px-web/?pxid=E0234&theme=Population%20and%20Employment",
             "https://www.gso.gov.vn/en/px-web/?pxid=E0225&theme=Population%20and%20Employment",
             "https://www.gso.gov.vn/en/px-web/?pxid=E0203-07&theme=Population%20and%20Employment",
             "https://www.gso.gov.vn/en/px-web/?pxid=E0245&theme=Population%20and%20Employment",
             "https://www.nso.gov.vn/en/px-web/?pxid=E0237&theme=Population%20and%20Employment",
             "https://www.gso.gov.vn/en/px-web/?pxid=E0263&theme=Population%20and%20Employment",
             "https://www.nso.gov.vn/en/px-web/?pxid=E1302&theme=Education",
             "https://www.nso.gov.vn/en/px-web/?pxid=E1306&theme=Education",
             "https://www.nso.gov.vn/en/px-web/?pxid=E1305&theme=Education",
             "https://www.nso.gov.vn/en/px-web/?pxid=E1311&theme=Education",
             "https://www.nso.gov.vn/en/px-web/?pxid=E1308&theme=Education",
             "https://www.nso.gov.vn/en/px-web/?pxid=E1405&theme=Health%2C%20Culture%2C%20Sport%20and%20Living%20standard"
    ]
    return urls

# --- Main download logic ---
def download_data_from_gso(url, download_path):
    """
    Automates the download of data in CSV format from GSO PX-Web.
    """
    options = webdriver.ChromeOptions()
    
    # Configure Chrome to automatically download files to the specified path
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False, 
        "download.directory_upgrade": True,
        "safeBrowse.enabled": False, # Changed to False for automated tests to prevent interference
        "plugins.always_open_pdf_externally": True 
    }
    options.add_experimental_option("prefs", prefs)

    # Browser arguments for stable execution
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    
    options.add_argument("--headless") # Run in headless mode

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30) # Global wait object for elements

    # Flag to track if the 'Save As' dropdown was found in an iframe in Step 4
    found_next_page_in_iframe = False 

    try:
        print(f"\n--- Navigating to {url} ---")
        driver.get(url)

        # --- STEP 1: Handle potential iframe for initial elements (Select All buttons) ---
        initial_iframe_found = False
        print("Checking for initial iframes and attempting to switch...")
        try:
            iframe_locator = (By.TAG_NAME, "iframe") 
            wait.until(EC.frame_to_be_available_and_switch_to_it(iframe_locator))
            print(f"SUCCESS: Switched to initial iframe. Current URL in iframe: {driver.current_url}")
            initial_iframe_found = True
            time.sleep(2) # Allow content within iframe to load
        except TimeoutException:
            print("INFO: No initial iframe found or loaded within 30 seconds. Assuming elements are on the main page.")
        except Exception as e:
            print(f"ERROR during initial iframe switch attempt: {e}. Assuming elements are on the main page.")

        # --- STEP 2: Click all "Select all" buttons ---
        select_all_buttons_locator = (By.XPATH, "//input[@type='image' and @title='Select all']")

        print(f"Attempting to find and click 'Select all' buttons...")
        try:
            wait.until(EC.element_to_be_clickable(select_all_buttons_locator))
            select_all_buttons = driver.find_elements(*select_all_buttons_locator)

            if not select_all_buttons:
                print("WARNING: No 'Select all' buttons found after initial wait.")
            else:
                print(f"Found {len(select_all_buttons)} 'Select all' buttons. Clicking them...")
                for i, button in enumerate(select_all_buttons):
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        driver.execute_script("arguments[0].click();", button) 
                        print(f"Clicked 'Select all' button {i+1}: {button.get_attribute('id') or button.get_attribute('name')}")
                        time.sleep(0.5) 
                    except Exception as e:
                        print(f"ERROR clicking 'Select all' button {i+1}: {e}")
            
            print("Waiting for page to stabilize after 'Select all' clicks (5 seconds)...")
            time.sleep(5) 

        except TimeoutException:
            print("FAILED: No 'Select all' buttons found/clickable. Exiting.")
            driver.save_screenshot(os.path.join(download_path, "ERROR_NO_SELECT_ALL_BUTTONS.png"))
            if initial_iframe_found: driver.switch_to.default_content()
            return
        except Exception as e:
            print(f"An error occurred during 'Select all' clicks: {e}. Exiting.")
            driver.save_screenshot(os.path.join(download_path, "ERROR_SELECT_ALL_EXCEPTION.png"))
            if initial_iframe_found: driver.switch_to.default_content()
            return

        # --- STEP 3: Prepare for "Continue" button context by re-evaluating iframe ---
        # Always switch to default content first to ensure we are on the main page
        print("Ensuring we are on default content before processing 'Continue' button.")
        driver.switch_to.default_content()
        time.sleep(2) # Give a brief moment for the main page to settle

        # Now, re-check for iframes before interacting with 'Continue' button
        continue_button_in_iframe = False
        print("Re-checking for iframes for 'Continue' button context...")
        try:
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe"))
            )
            print("SUCCESS: Switched to iframe for 'Continue' button context.")
            continue_button_in_iframe = True
            time.sleep(2) # Allow iframe content to load
        except TimeoutException:
            print("INFO: No iframe found for 'Continue' button context. Assuming it's on the default content.")
        except Exception as e:
            print(f"ERROR re-checking for iframe for 'Continue' button: {e}. Assuming it's on the default content.")


        # --- STEP 4: Click the "Continue" Button and WAIT for next page's elements flexibly ---
        continue_button_locator = (By.ID, "ctl00_ContentPlaceHolderMain_VariableSelector1_VariableSelector1_ButtonViewTable")
        # Locator for an element expected on the *next* page (the "Save as" dropdown)
        next_page_element_locator = (By.ID, "ctl00_ctl00_ContentPlaceHolderMain_CommandBar1_CommandBar1_SaveAsDropDownList")

        print("Attempting to click 'Continue' button and verify navigation...")
        try:
            # First, find the continue button in its proper context (from previous step's iframe check)
            continue_button = wait.until(EC.element_to_be_clickable(continue_button_locator))
            print("SUCCESS: 'Continue' button found and is clickable. Attempting click.")
            
            try:
                continue_button.click()
                print("SUCCESS: Clicked 'Continue' button using standard click.")
            except ElementClickInterceptedException:
                print("Click intercepted. Trying JavaScript click for 'Continue' button.")
                driver.execute_script("arguments[0].click();", continue_button)
                print("SUCCESS: Clicked 'Continue' button using JavaScript.")
            except Exception as e: 
                print(f"ERROR: Could not click 'Continue' button with standard method ({e}). Trying JavaScript click as last resort.")
                driver.execute_script("arguments[0].click();", continue_button)
                print("SUCCESS: Clicked 'Continue' button using JavaScript as last resort.")
            
            # After clicking 'Continue', if we were in an iframe, switch back to default content
            if continue_button_in_iframe:
                print("Switching back to default content after 'Continue' click.")
                driver.switch_to.default_content()
                time.sleep(1) # Small pause after switching

            # Allow a short moment for page transition to start, even if not fully loaded yet.
            print("Allowing 3 seconds for page transition to start...")
            time.sleep(3) 
            
            print("Attempting to find 'Save As' dropdown (next page element) flexibly...")
            # Use the new helper function to find the next page element (Save As dropdown)
            save_as_dropdown_element, found_next_page_in_iframe = find_element_any_context(driver, wait, next_page_element_locator, timeout=20)
            
            if save_as_dropdown_element:
                print("SUCCESS: Next page loaded and 'Save As' dropdown is present.")
                if found_next_page_in_iframe:
                    print("INFO: 'Save As' dropdown was found inside an iframe.")
                time.sleep(3) # Give extra time for the page to fully render
            else:
                raise TimeoutException("Next page element ('Save As' dropdown) did not appear in default content or any iframe.")

        except TimeoutException as e:
            print(f"ERROR: Page did not advance as expected after 'Continue' button click: {e}")
            driver.save_screenshot(os.path.join(download_path, "ERROR_CONTINUE_NAVIGATION_FAILURE.png"))
            return
        except Exception as e:
            print(f"An unexpected error occurred while handling 'Continue' button navigation: {e}")
            driver.save_screenshot(os.path.join(download_path, "ERROR_CONTINUE_NAVIGATION_GENERAL_FAILURE.png"))
            return
        finally:
            # Ensure we switch back to default content if we entered an iframe just for the next page element check
            # This is handled here for the 'found_next_page_in_iframe' flag
            if found_next_page_in_iframe: # This flag tracks if the Save As dropdown was found in an iframe
                print("Switching back to default content after finding next page element in iframe (if applicable).")
                driver.switch_to.default_content()
                time.sleep(1)

        # --- STEP 5: Check for and close Footnotes (if present) ---
        print("Checking for footnotes panel (max 5s)...")
        # Ensure we are on default content before checking for footnotes initially
        driver.switch_to.default_content()
        time.sleep(1) # brief pause

        close_footnote_button = None
        footnote_found_in_iframe = False # Flag to track if footnote was found in an iframe

        try:
            # Try finding on default content first
            close_footnote_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='image' and @title='Close']"))
            )
            print("Footnotes panel detected on default content.")
        except TimeoutException:
            print("INFO: No footnotes panel on default content within 5s. Checking for iframe.")
            # If not found on default, try switching to iframe
            try:
                # Use a shorter wait for iframe availability for footnote
                WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))
                print("Switched to iframe for footnote. Checking for 'Close' button within iframe.")
                close_footnote_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@type='image' and @title='Close']"))
                )
                footnote_found_in_iframe = True
                print("Footnotes panel detected in iframe.")
            except TimeoutException:
                print("INFO: No footnotes panel found even in iframe.")
            except Exception as e:
                print(f"ERROR checking/closing footnotes in iframe: {e}")
        except Exception as e:
            print(f"ERROR: General error handling footnotes on default content: {e}")
        
        if close_footnote_button:
            print("Attempting to close footnotes panel...")
            driver.save_screenshot(os.path.join(download_path, "DIAGNOSTIC_FOOTNOTE_DETECTED_BEFORE_CLOSE.png"))
            print(f"DIAGNOSTIC: Screenshot of detected footnote saved to {os.path.join(download_path, 'DIAGNOSTIC_FOOTNOTE_DETECTED_BEFORE_CLOSE.png')}")
            try:
                close_footnote_button.click()
                print("Footnotes panel closed (standard click).")
                time.sleep(1)
            except ElementClickInterceptedException:
                print("Footnote close click intercepted. Trying JavaScript click.")
                driver.execute_script("arguments[0].click();", close_footnote_button)
                print("Footnotes panel closed (JavaScript click).")
                time.sleep(1)
            except Exception as e:
                print(f"ERROR clicking footnote close button: {e}")
                driver.save_screenshot(os.path.join(download_path, "DIAGNOSTIC_FOOTNOTE_CLICK_FAILED.png"))
                print(f"DIAGNOSTIC: Screenshot if footnote click fails saved to {os.path.join(download_path, 'DIAGNOSTIC_FOOTNOTE_CLICK_FAILED.png')}")
        
        # Ensure we switch back to default content if we entered an iframe for footnotes
        if footnote_found_in_iframe:
            print("Switching back to default content after footnote check/close.")
            driver.switch_to.default_content()
            time.sleep(1)

        # --- STEP 6: Select "Comma-separated values (.csv)" from "Save as" dropdown and initiate download ---
        save_as_dropdown_id = "ctl00_ctl00_ContentPlaceHolderMain_CommandBar1_CommandBar1_SaveAsDropDownList"
        download_file_link_id = "ctl00_ctl00_ContentPlaceHolderMain_CommandBar1_CommandBar1_commandbarDownloadFileLink"

        print("Attempting to select 'Comma-separated values (.csv)' from dropdown and initiate download...")
        current_files_in_dir = os.listdir(download_path) 

        try:
            save_as_dropdown_element = wait.until(EC.element_to_be_clickable((By.ID, save_as_dropdown_id)))
            print("Found 'Save as' dropdown. Attempting to select CSV option...")
            save_as_dropdown = Select(save_as_dropdown_element)

            try:
                save_as_dropdown.select_by_visible_text("Comma-separated values (.csv)")
                print("Selected 'Comma-separated values (.csv)' by visible text.")
            except NoSuchElementException:
                print("Could not select 'Comma-separated values (.csv)' by visible text. Trying by partial value 'FileTypeCsv'.")
                # This find_element will also operate in the current context
                csv_option = driver.find_element(By.XPATH, f"//select[@id='{save_as_dropdown_id}']//option[contains(@value, 'FileTypeCsv')]")
                csv_option_value = csv_option.get_attribute("value")
                save_as_dropdown.select_by_value(csv_option_value)
                print(f"Selected 'Comma-separated values (.csv)' by value: {csv_option_value}.")
            
            time.sleep(2) 

            save_file_link = wait.until(EC.element_to_be_clickable((By.ID, download_file_link_id)))
            print("Found 'Save file' link. Clicking to initiate download...")
            save_file_link.click()
            
            print("Download should initiate automatically. Waiting for file to appear in directory (max 30s)...")
            download_success = False
            downloaded_filename = None # To store the name of the downloaded file
            for _ in range(30): 
                downloaded_files_now = os.listdir(download_path)
                new_files = [f for f in downloaded_files_now if not f.endswith(('.tmp', '.crdownload', '.part', '.download')) and f not in current_files_in_dir]
                if new_files:
                    downloaded_filename = new_files[0] # Assuming one file per download
                    print(f"SUCCESS: New file(s) downloaded to {download_path}: {downloaded_filename}")
                    download_success = True
                    break
                time.sleep(1) 
            
            if not download_success:
                print("WARNING: No *new completed* files detected in download directory after waiting.")
                print("Please check the download folder manually and inspect browser downloads.")
                driver.save_screenshot(os.path.join(download_path, "WARNING_NO_NEW_DOWNLOADED_FILE.png"))
            else:
                # Immediately rename the downloaded CSV file
                rename_csv_files_by_a1_content(download_path, downloaded_filename)

        except TimeoutException:
            print("ERROR: Timeout waiting for 'Save as' dropdown or 'Save file' link during download step.")
            driver.save_screenshot(os.path.join(download_path, "ERROR_DOWNLOAD_ELEMENTS_TIMEOUT.png"))
        except NoSuchElementException:
            print("ERROR: Could not find 'Save as' dropdown, CSV option, or 'Save file' link. Page structure might have changed.")
            driver.save_screenshot(os.path.join(download_path, "ERROR_DOWNLOAD_ELEMENTS_MISSING.png"))
        except Exception as e:
            print(f"ERROR: General error during 'Save as' and download step: {e}")
            driver.save_screenshot(os.path.join(download_path, "ERROR_DOWNLOAD_STEP_FAILURE.png"))
        finally:
            pass # Cleanup handled in main try-except's finally block
    
    except Exception as e:
        print(f"An UNEXPECTED TOP-LEVEL ERROR occurred for {url}: {e}")
    finally:
        print(f"--- Finished processing {url} ---")
        try:
            driver.switch_to.default_content()
            if found_next_page_in_iframe:
                print("Final switch back to default content after overall processing.")
        except Exception as e:
            print(f"WARNING: Could not switch back to default content in final cleanup: {e}")
        driver.quit()

# --- Renaming function for CSV files ---
def rename_csv_files_by_a1_content(folder_path, filename):
    """
    Reads the A1 cell (first cell of the first row) of a .csv file
    and renames the file based on predefined mappings, removing spaces from target names.

    Args:
        folder_path (str): The path to the folder containing the .csv file.
        filename (str): The name of the downloaded .csv file.
    """

    rename_rules = {
        "Number of deaths was registered by province by Cities, provinces": "Death.csv",
        "Life expectancy at birth by province by Cities,": "Lifeexpectancy.csv", # Spaces removed
        "Average population by province,": "Population.csv",
        "Number of employed persons": "Employment.csv",
        "Labour force at 15 years of age and abov": "LabourForce.csv", # Spaces removed
        "Unemployment rate of labour force at": "UnemploymentRate.csv", # Spaces removed
        "Number of schools, classes, teachers and children of kindergarten": "EducationData.csv", # Spaces removed
        "Number of classes of general education as of 30 September": "NumberOfClasses.csv", # Spaces removed
        "Number of school of general education as of 30 September": "NumberOfSchool.csv", # Spaces removed
        "Number of pupils of general education as of 30 September": "NumberOfStudent.csv", # Spaces removed
        "Number of direct teaching teachers of general education as of 30 September": "NumberOfTeacher.csv", # Spaces removed
        "Number of health establishments under provincial departments of health": "Health.csv"
    }

    file_path = os.path.join(folder_path, filename)
    if not filename.endswith(".csv"):
        print(f"Skipping '{filename}': not a CSV file.")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Read the first row and get the first cell (A1 equivalent)
            first_row = next(reader, None) # Get first row, None if file is empty
            a1_value = first_row[0] if first_row else None

        if a1_value and isinstance(a1_value, str):
            a1_value = a1_value.strip() # Remove leading/trailing whitespace

            new_name = None
            for key, value in rename_rules.items():
                if a1_value.startswith(key): # Use startswith for partial matches
                    new_name = value
                    break

            if new_name:
                new_file_path = os.path.join(folder_path, new_name)
                if file_path != new_file_path: # Avoid renaming to itself
                    try:
                        os.rename(file_path, new_file_path)
                        print(f"Renamed '{filename}' to '{new_name}'")
                    except OSError as e:
                        print(f"Error renaming '{filename}' to '{new_name}': {e}")
                else:
                    print(f"File '{filename}' already has the correct name.")
            else:
                print(f"No rename rule found for '{filename}' with A1 content: '{a1_value}'")
        else:
            print(f"A1 cell of '{filename}' is empty or not a string.")

    except Exception as e:
        print(f"Could not process '{filename}': {e}")


# --- Main execution block ---
if __name__ == "__main__":
    gso_urls = get_gso_urls() # Get URLs from the new method

    # Save files in a new sub-directory named 'input_files'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    download_folder = os.path.join(script_dir, "input_files")

    # Create the directory if it doesn't exist
    os.makedirs(download_folder, exist_ok=True)
    print(f"Download directory: {download_folder}")

    if not gso_urls:
        print("WARNING: No URLs found in `get_gso_urls()` method. Exiting.")
        exit()

    for url in gso_urls:
        download_data_from_gso(url, download_folder)
        time.sleep(5) # Add a small delay between URLs to prevent overwhelming the server.

    print("\n--- All URLs processed. Check your current script folder for downloads. ---")

