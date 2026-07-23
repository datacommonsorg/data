# Lint as: python3
r"""Scrape CDC Wonder data and store it locally.

Pre-requisite:
  Get chromedriver following the steps at
  https://sites.google.com/corp/chromium.org/driver/downloads/version-selection
  and put it in /usr/local/bin/chromedriver

Example command to get the chromedriver:

  curl -o /tmp/chromedriver_linux64.zip \
  https://chromedriver.storage.googleapis.com/78.0.3904.70/chromedriver_linux64.zip

  sudo unzip /tmp/chromedriver_linux64.zip -d /usr/local/bin/

Example command to scrape state level rate data.

  blaze run scrape_cdc_wonder -- \
  --alsologtostderr --download_path=/tmp/cdc/natality/state/ \
  --website=https://wonder.cdc.gov/natality-current.html \
  --config_path=natality_config.json --parallel_download=0 --headless \
  --calculate_combinations --show_totals --include_zeroes

"""
import functools
import itertools
import json
import multiprocessing
import os
import pathlib
import time

from absl import app
from absl import flags

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

flags.DEFINE_string('download_path', '', 'The local path to download the files')
flags.DEFINE_string('website', '', 'The website to download files from')
flags.DEFINE_string(
    'config_path', '', 'Path to config file. Use absolute path'
    'if running with blaze.')
flags.DEFINE_integer(
    'parallel_download', 0,
    'The number of concurrent download. 0 if do not parallel.')
flags.DEFINE_bool(
    'headless', False,
    'Run the web driver in headless mode. Default behavious is to not run in'
    'headless mode.')
flags.DEFINE_bool(
    'calculate_combinations', False,
    'Download all possible combinations of options in the select tags. When'
    'false, it downloads only single options without any combinations.')
flags.DEFINE_bool('show_totals', False, 'Whether to show totals across yrs.')
flags.DEFINE_bool('include_suppressed', False, 'Whether to get suppressed'
                  'results.')
flags.DEFINE_bool(
    'include_zeroes', False,
    'Whether to rows containing zero counts.')  # 0-9 autosuppressed for counts
flags.DEFINE_bool('test', False, 'Whether to run test instead of full scrape')

FLAGS = flags.FLAGS

CHROME_DRIVER_PATH = '/usr/local/bin/chromedriver-linux64/chromedriver'

CONFIG_MAP = dict()


def retry(f):
    """Define a decorator to retry a function."""

    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        while True:
            try:
                return f(*args, **kwargs)
            except:
                pass

    return wrapped


class Scraper(object):
    """Scraper class."""

    def __init__(self, driver):
        self._driver = driver
        if not FLAGS.headless:
            self._driver.maximize_window()

    def agree(self):
        """Click on the agree button."""
        agree_button = WebDriverWait(self._driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'action-I Agree')))
        agree_button.click()

    def send(self):
        """Click on the send button."""
        send_button = WebDriverWait(self._driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'action-Send')))
        send_button.click()

    def choose_group_by(self):
        """Choose group by based on config."""
        for s_id, option_value in CONFIG_MAP['group_by'].items():
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.ID, s_id)))
            group_by_select = Select(self._driver.find_element(By.ID, s_id))
            group_by_select.select_by_value(option_value)

    def get_options(self):
        """Get all options from select tags."""
        all_options = {}
        for s_id, s_values in CONFIG_MAP['select'].items():
            if s_values.get('radio', ''):
                radio_check = WebDriverWait(self._driver, 10).until(
                    EC.presence_of_element_located((By.ID, s_values['radio'])))
                radio_check.click()
                continue

            code_select = Select(self._driver.find_element(By.ID, s_id))
            code_select_values = [
                o.get_attribute('value') for o in code_select.options
            ]
            if 'exclude_options' in s_values:
                for value in s_values['exclude_options']:
                    code_select_values.remove(value)
            all_options[s_id] = code_select_values

        return all_options

    def check_radio(self):
        """Selects radio button based on config."""
        for s_values in CONFIG_MAP['select'].values():
            if s_values.get('radio', ''):
                radio_check = WebDriverWait(self._driver, 10).until(
                    EC.presence_of_element_located((By.ID, s_values['radio'])))
                radio_check.click()

    def check_measures(self):
        """Check measures."""
        for m_id in CONFIG_MAP.get('measure', []):
            m_check = WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.ID, m_id)))
            m_check.click()
        if not FLAGS.show_totals:  # default checked
            show_totals_check = WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.ID, 'CO_show_totals')))
            show_totals_check.click()
        if FLAGS.include_zeroes:
            zero_check = WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.ID, 'CO_show_zeros')))
            zero_check.click()
        if FLAGS.include_suppressed:
            suppressed_check = WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.ID, 'CO_show_suppressed')))
            suppressed_check.click()
        export_check = WebDriverWait(self._driver, 10).until(
            EC.presence_of_element_located((By.ID, 'export-option')))
        export_check.click()

    def check_all_years(self):
        """Select the 'All' option for year."""
        year_id = CONFIG_MAP.get('year', '')
        if year_id:
            code_select = Select(self._driver.find_element(By.ID, year_id))
            code_select.select_by_value('*All*')

    def choose_options(self, config):
        """Pick options given select_id:value pairs."""
        for s_id, option_value in config.items():
            code_select = Select(self._driver.find_element(By.ID, s_id))
            code_select.deselect_by_value('*All*')
            code_select.select_by_value(option_value)

    def enter_title(self, text):
        """Enter text in the title box."""
        input_element = self._driver.find_element(By.ID, 'TO_title')
        input_element.send_keys(text)

    def check_selected_years(self):
        if 'year' in CONFIG_MAP:
            year_config = CONFIG_MAP.get('year', '')
            year_list = year_config.get('include_list', '')
            year_id = year_config.get('element', '')
            code_select = Select(self._driver.find_element(By.ID, year_id))
            for year_val in year_list:
                code_select.select_by_value(year_val)


def create_driver(chrome_options):
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(FLAGS.website)
    driver.set_page_load_timeout(300000)
    return driver


def get_file_title(config):
    """Generates a title given a set of config."""
    title = []
    short_title = []
    for s_id, option in config.items():
        s_name = CONFIG_MAP['select'][s_id]['name']
        cleaned_option = option.replace(' ',
                                        '')  # Removing whitespace for filename
        if len(option) > 5:
            short_option = cleaned_option[:5] + '...'
            short_title.append(f'{s_name}={short_option}')
        else:
            short_title.append(f'{s_name}={cleaned_option}')
        title.append(f'{s_name}={cleaned_option}')
    title = '$$'.join(title)
    short_title = '$$'.join(short_title)
    return title.replace('*', ''), short_title.replace('*', '')


def map_select_option(select_ids, option_product):
    for c in option_product:
        yield dict(zip(select_ids, c))


#@retry
def scrape_job(config):
    """Scrape a file from the given config."""
    file_title, short_file_title = get_file_title(config)
    file_name = short_file_title + '.txt'

    download_file_path = os.path.join(FLAGS.download_path, file_name)
    if os.path.exists(download_file_path):
        print(f'{file_name} already exists')
        return

    print(f'Downloading {download_file_path}')
    # Open a browser for download
    chrome_options = webdriver.ChromeOptions()
    if FLAGS.headless:
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--window-size=1920,1080')
    prefs = {
        'download.default_directory': FLAGS.download_path,
        'download.prompt_for_download': 'false'
    }
    chrome_options.add_experimental_option('prefs', prefs)
    driver = create_driver(chrome_options)
    scraper = Scraper(driver)
    scraper.agree()
    scraper.choose_group_by()
    scraper.check_measures()
    scraper.enter_title(short_file_title)
    scraper.check_radio()
    scraper.choose_options(config)
    scraper.check_selected_years()
    scraper.send()
    while not os.path.exists(download_file_path):
        time.sleep(1)
    driver.close()

    # Writing file title to end of downloaded file
    with open(download_file_path, 'a') as f:
        f.write(f'\n{file_title}')

    time.sleep(10)


def main(unused_argv):
    global CONFIG_MAP
    chrome_options = webdriver.ChromeOptions()
    if FLAGS.headless:
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--window-size=1920,1080')
    driver = create_driver(chrome_options)
    scraper = Scraper(driver)
    scraper.agree()

    if not os.path.exists(FLAGS.download_path):
        pathlib.Path(FLAGS.download_path).mkdir(parents=True, exist_ok=True)

    with open(FLAGS.config_path, 'r') as f:
        CONFIG_MAP = json.load(f)

    all_options = scraper.get_options()
    driver.close()

    if FLAGS.test:
        for s_id, option_list in all_options.items():
            if len(option_list) > 1:
                all_options[s_id] = option_list[:2]  # Only retain 2 of each

    all_config = []
    if FLAGS.calculate_combinations:
        total_configs = 1
        for option_list in all_options.values():
            total_configs *= len(option_list)

        option_product = itertools.product(*list(all_options.values()))
        select_ids = list(all_options.keys())
        all_config = map_select_option(select_ids, option_product)

    else:
        total_configs = 0
        for s_id, option_list in all_options.items():
            total_configs += len(option_list)
            for option in option_list:
                all_config.append({s_id: option})

    print(f'{total_configs} files will be downloaded')

    if FLAGS.parallel_download:
        p = multiprocessing.Pool(FLAGS.parallel_download)
        p.map(scrape_job, all_config)
        p.terminate()
        p.join()
    else:
        for c in all_config:
            scrape_job(c)


if __name__ == '__main__':
    app.run(main)
