# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Script to process google spreadsheets using StatVatDataProcessor

For more details on configs and usage, please refer to the README.
"""

import cgi
import copy
from http import server
import multiprocessing
import os
import re
import socket
import subprocess
import sys
import threading
import time
from urllib import parse

from absl import app
from absl import flags
from absl import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import gspread

flags.DEFINE_string('input_sheet', '', 'URL of spreadsheet to process')
flags.DEFINE_string('output_prefix', '',
                    'Path prefix for output csv and mcf files.')
flags.DEFINE_string('credentials', '', 'File with credentials.')

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import stat_var_processor
import file_util
import config_flags
import process_http_server

_FLAGS = flags.FLAGS

_HOME_DIR = os.path.expanduser('~')

# If modifying these scopes, delete the file token.json.
_SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

_INPUT_SHEETS = [
    'metadata',
    'pv_map',
    'data',
    'context',
]

_OUTPUT_SHEETS = [
    'output_csv',
    'output_tmcf_file',
    'output_statvar_mcf',
    'output_schema_mcf',
    'output_counters',
    'output_sanity_check',
]


def file_is_gdrive_folder(filename: str) -> bool:
    """Returns True if the filename is a google folder url."""
    if isinstance(filename, str):
        return filename.startswith('https://drive.google.com/') and (
            '/drive/folders/' in filename)
    return False


def gdrive_get_credentials(token_file: str = 'tokens.json'):
    """Authorize user for Google drive API use"""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_files = file_util.file_get_matching(token_file)
    if token_files:
        logging.info(f'Loading credentials from {token_files}')
        creds = Credentials.from_authorized_user_file(token_files[0], _SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logging.info(f'Refreshing credentials')
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                f'{_HOME_DIR}/.config/gspread/credentials.json', _SCOPES)
            creds = flow.run_local_server(port=8100)
        # Save the credentials for the next run
        with file_utli.FileIO(token_file, 'w') as token:
            token.write(creds.to_json())
    return creds


def process_sheet_in_drive_path(
    data_processor_class: stat_var_processor.StatVarDataProcessor,
    input_drive_path: str,
    output_path: str,
    config_file: str,
    pv_map_files: list = None,
    parallelism: int = 1,
):
    """Reads the spreadsheets under the input drive folder and

  process them by calling process_spreadsheet
  """
    # Authorize user
    creds = gdrive_get_credentials()
    service = build('drive', 'v3', credentials=creds)
    if file_is_gdrive_folder(input_drive_path):
        folder_id = input_drive_path.split('/')[-1]
        logging.info(f'Getting sheets in gdrive folder: {folder_id}')

        # Get the spreadsheets within the Google drive folder
        query = (f"'{folder_id}' in parents and"
                 " mimeType='application/vnd.google-apps.spreadsheet'")
        page_token = None
        while True:
            try:
                results = (service.files().list(
                    q=query,
                    pageToken=page_token,
                    pageSize=100,
                    fields='nextPageToken, files(id, name, mimeType, parents)',
                ).execute())
                items = results.get('files', [])
                page_token = results.get('nextPageToken', None)
            except Exception as e:
                logging.error(f'Error listing file in foder {folder_id} - {e}')
                return
            if not items:
                logging.info('No sheet files to process in current page.')
                if page_token is not None:
                    # Current page does not have any sheets to process
                    continue

            for item in items:
                logging.info(f'Processing spreadsheet: {item}')
                drive_gsheet_url = ('https://docs.google.com/spreadsheets/d/' +
                                    item['id'])
                logging.info('Processing sheet : {0} - ({1})'.format(
                    item['name'], drive_gsheet_url))

                # Call the spreadsheet processor
                process_spreadsheets(
                    data_processor_class,
                    input_file=drive_gsheet_url,
                    output_path=output_path,
                    config_file=config_file,
                    pv_map_files=pv_map_files,
                )

            if page_token is None:
                # Exit the loop when nextPageToken is None - no more pages to process.
                break
    else:
        logging.error(
            'The argument input_drive_path is not a Google drive folder url')


def process_spreadsheets(
    data_processor_class: stat_var_processor.StatVarDataProcessor,
    input_file: str,
    output_path: str,
    config_file: str,
    pv_map_files: list = None,
    parallelism: int = 1,
) -> list:
    """Processes google spreadsheets.

  Returns files not processed.
  """
    unprocessed_files = []
    # Set up the default config.
    # It is updated with config per data sheet.
    config = config_flags.init_config_from_flags(config_file)
    config_dict = config.get_configs()
    if pv_map_files:
        config_dict['pv_map'].extend(pv_map_files)

    # Process all sheets.
    logging.info(f'Processing file: {input_file}')
    if file_is_gdrive_folder(input_file):
        process_sheet_in_drive_path(
            data_processor_class,
            input_file,
            output_path,
            config_file,
            pv_map_files,
            parallelism,
        )
    elif file_util.file_is_google_spreadsheet(input_file):
        gs = file_util.file_open_google_spreadsheet(input_file)
        if not gs:
            logging.fatal(f'Unable to open spreadsheet: {input_file}')

        # Get the worksheets for input and outputs by dataset suffix
        data_sets = {}
        sheets = list(_INPUT_SHEETS)
        sheets.extend(_OUTPUT_SHEETS)
        sheet_names = [re.sub(r'[^a-z0-9]', '', s.lower()) for s in sheets]
        for ws in gs.worksheets():
            title = ws.title.lower().replace('_', '')
            for prefix in sheet_names:
                if title.startswith(prefix):
                    suffix = title.replace(prefix, '')
                    if suffix not in data_sets:
                        data_sets[suffix] = {}
                    data_sets[suffix][prefix] = ws.url
                    break
        if not data_sets:
            # Sheet is a single data input_file. Process it.
            data_sets['0'] = {'data': input_file}

        # Process each set of data sheets.
        if not parallelism:
            parallelism = os.cpu_count()
        logging.info(
            f'Processing {len(data_sets)} sheets: {data_sets} with parallelism:'
            f' {parallelism}')
        with multiprocessing.get_context('spawn').Pool(parallelism) as pool:
            for index, data in data_sets.items():
                input_file = data.get('data', '')
                if not input_file:
                    continue

                # Setup config with data from metadata sheet
                data_config = copy.deepcopy(config_dict)
                metadata_sheet = data.get(
                    'metadata',
                    data_sets.get('', {}).get('metadata', ''))
                if metadata_sheet:
                    metadata_config = file_util.file_load_csv_dict(
                        metadata_sheet)
                    if metadata_config:
                        logging.info(
                            f'Using config from metadata {metadata_sheet}:'
                            f' {metadata_config}')
                        config_flags.update_config(metadata_config, data_config)

                # Set input, output configs.
                data_config['input_data'] = [input_file]
                pv_map = data.get('pvmap', '')
                if pv_map:
                    pv_maps = data_config.get('pv_map', [])
                    pv_maps.append(pv_map)
                    data_config['pv_map'] = pv_maps
                elif not data_config.get('pv_map'):
                    # Generate a pvmap if not set in config.
                    ws = _add_worksheet(gs, title=f'pvmap{index}')
                    data_config['pv_map'] = ws.url
                sv_map = data.get('sdg', data_config.get('sdg', ''))
                if sv_map:
                    data_config['statvar_dcid_remap_csv'] = sv_map
                if output_path:
                    # Generate output into the output path
                    data_config['output_path'] = (
                        output_path + '-' +
                        re.sub('[^A-Za-z0-9_-]+', '_', gs.title) + str(index))
                else:
                    # Generate outputs into sheets.
                    data_config['output_path'] = ''
                    for sheet_name in _OUTPUT_SHEETS:
                        s = sheet_name.replace('_', '').lower()
                        if s not in data_sets:
                            ws = _add_worksheet(gs,
                                                title=f'{sheet_name}{index}')
                            data_config[sheet_name] = ws.url

                # Process the sheet
                logging.info(f'Processing sheet: {data_config}')
                process_args = {
                    'data_processor_class': data_processor_class,
                    'input_data': data_config.get('input_data', []),
                    'output_path': data_config.get('output_path', ''),
                    'config': data_config,
                    'pv_map_files': [],
                }
                if parallelism > 1:
                    task = pool.apply_async(stat_var_processor.process,
                                            kwds=process_args)
                else:
                    stat_var_processor.process(**process_args)
            pool.close()
            logging.info(f'Waiting for {len(data_sets)} tasks to complete...')
            pool.join()
    else:
        # Process non-spreadsheet input.
        logging.info(f'Processing files: {unprocessed_files}')
        stat_var_processor.process(
            data_processor_class,
            input_data=input_file,
            output_path=output_path,
            config=config_file,
            pv_map_files=pv_map_files,
        )


def _add_worksheet(
    gs: gspread.spreadsheet.Spreadsheet,
    title: str,
    rows: int = 100,
    cols: int = 20,
) -> gspread.worksheet.Worksheet:
    """Add a worksheet if it doesn't exist."""
    for ws in gs.worksheets():
        if ws.title == title:
            return ws
    ws = gs.add_worksheet(title=title, rows=rows, cols=cols)
    logging.info(f'Added worksheet: {title}: {ws.url}')
    if not ws:
        raise RuntimeError(f'Unable to add worksheet: {title}')
    return ws


def main(_):
    # Launch a web server if --http_port is set.
    if process_http_server.run_http_server(script=__file__, module=__name__):
        return

    # Process the spreadsheet specified
    output_path = _FLAGS.output_prefix
    if not output_path:
        output_path = _FLAGS.output_path
    process_spreadsheets(
        stat_var_processor.StatVarDataProcessor,
        input_file=_FLAGS.input_sheet,
        output_path=output_path,
        config_file=_FLAGS.config_file,
        pv_map_files=_FLAGS.pv_map,
    )


if __name__ == '__main__':
    app.run(main)
