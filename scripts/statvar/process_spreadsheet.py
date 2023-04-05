# Copyright 2022 Google LLC
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
'''Script to process google spreadsheets using StatVatDataProcessor
For more details on configs and usage, please refer to the README.
'''

import gspread
import os
import re
import sys

from absl import app
from absl import flags
from absl import logging

_FLAGS = flags.FLAGS

flags.DEFINE_string('input_sheet', '', 'Spreadsheet to process.')

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import stat_var_processor
import file_util
import config_flags


def process_spreadsheets(
        data_processor_class: stat_var_processor.StatVarDataProcessor,
        input_file: str,
        output_path: str,
        config_file: str,
        pv_map_files: list = None) -> list:
    '''Processes google spreadsheets.
   Returns files not processed.'''
    unprocessed_files = []
    # Set up the default config.
    # It is updated with config per data sheet.
    config = config_flags.get_config_from_flags(config_file)
    config_dict = config.get_configs()
    if pv_map_files:
        config_dict['pv_map'].extend(pv_map_files)

    # Process all sheets.
    logging.info(f'Processing file: {input_file}')
    if file_util.file_is_google_spreadsheet(input_file):
        gs = file_util.file_open_google_spreadsheet(input_file)
        if not gs:
            logging.fatal(f'Unable to open spreadsheet: {input_file}')

        # Get the worksheets for data, pvmap, metadata
        data_sets = {}
        for ws in gs.worksheets():
            title = ws.title.lower().replace('_', '')
            for prefix in [
                    'data', 'pvmap', 'processedcsv', 'tmcf', 'mcf', 'metadata'
            ]:
                if title.startswith(prefix):
                    suffix = title.replace(prefix, '')
                    if not suffix:
                        sufffix = 0
                    if suffix not in data_sets:
                        data_sets[suffix] = {}
                    data_sets[suffix][prefix] = ws.url
                    break
        if not data_sets:
            # Sheet is a single data input_file. Process it.
            data_sets[0] = {'data': input_file}

        # Process each set of data sheets.
        logging.info(f'Processing {len(data_sets)} sheets: {data_sets}')
        for index, data in data_sets.items():
            input_file = data.get('data', '')
            if not input_file:
                continue

            # Setup config with data from metadata sheet
            data_config = dict(config_dict)
            metadata_sheet = data.get('metadata',
                                      data_sets.get(0, {}).get('metadata', ''))
            if metadata_sheet:
                metadata_config = file_util.file_load_csv_dict(metadata_sheet)
                if metadata_config:
                    logging.info(
                        f'Using config from metadata {metadata_sheet}: {metadata_config}'
                    )
                    data_config.update(metadata_config)

            # Set input, output configs.
            data_config['input_data'] = [input_file]
            pv_map = data.get('pvmap', '')
            if pv_map:
                pv_maps = config_dict.get('pv_map', [])
                pv_maps.append(pv_map)
                config_dict['pv_map'] = pv_maps
            if output_path:
                # Generate output into the output path
                data_config[
                    'output_path'] = output_path + '-' + gs.title.replace(
                        ' ', '_')
            else:
                # Generate outputs into sheets.
                data_config['output_path'] = ''
                if 'processedcsv' not in data_sets:
                    ws = _add_worksheet(gs, title=f'processed_csv{index}')
                    if not ws:
                        logging.fatal(
                            f'Unable to add worksheet: processed_csv{index}')
                    data_config['output_csv_file'] = ws.url
                if 'tmcf' not in data_sets:
                    ws = _add_worksheet(gs, title=f'tmcf{index}')
                    if not ws:
                        logging.fatal(f'Unable to add worksheet: tmcf{index}')
                    data_config['output_tmcf_file'] = ws.url
                if 'mcf' not in data_sets:
                    ws = _add_worksheet(gs, title=f'mcf{index}')
                    if not ws:
                        logging.fatal(f'Unable to add worksheet: mcf{index}')
                    data_config['output_mcf'] = ws.url

            # Process the sheet
            logging.info(f'Processing sheet: {data_config}')
            stat_var_processor.process(
                data_processor_class,
                input_data=data_config.get('input_data', []),
                output_path=data_config.get('output_path', ''),
                config=data_config,
                pv_map_files=[])
    else:
        # Process non-spreadsheet input.
        logging.info(f'Processing files: {unprocessed_files}')
        stat_var_processor.process(data_processor_class,
                                   input_data=input_file,
                                   output_path=output_path,
                                   config=config_file,
                                   pv_map_files=pv_map_files)


def _add_worksheet(gs: gspread.spreadsheet.Spreadsheet,
                   title: str,
                   rows: int = 100,
                   cols: int = 20) -> gspread.worksheet.Worksheet:
    '''Add a worksheet if it doesn't exist.'''
    for ws in gs.worksheets():
        if ws.title == title:
            return ws
    return gs.add_worksheet(title=title, rows=rows, cols=cols)


def main(_):
    process_spreadsheets(stat_var_processor.StatVarDataProcessor,
                         input_file=_FLAGS.input_sheet,
                         output_path=_FLAGS.output_path,
                         config_file=_FLAGS.config,
                         pv_map_files=_FLAGS.pv_map)


if __name__ == '__main__':
    app.run(main)
