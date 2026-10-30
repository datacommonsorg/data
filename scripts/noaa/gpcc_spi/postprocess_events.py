# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Post-processes NOAA GPCC SPI drought event and observation CSVs.

1. Deduplicates event StatVarObservations in drought_spi_9m_polygon_svobs.csv
   by (dcid, observationDate) using area = max(area) and
   standardizedPrecipitationIndex = min(standardizedPrecipitationIndex) to
   prevent Sanity_InconsistentSvObsValues errors in dc-import.
2. Extracts all unique DroughtEvent DCIDs from both the events CSV and event
   observations CSV and writes drought_event_nodes.mcf so dc-import local
   resolution (RESOLUTION_MODE_LOCAL) resolves observationAbout references on
   input4 without Existence_MissingReference_observationAbout errors.
"""

import csv
import os
import sys
import tempfile
from typing import Any, Dict, Optional, Set, Tuple

from absl import app
from absl import flags
from absl import logging

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

DEFAULT_EVENTS_CSV = os.path.join(
    _SCRIPT_PATH,
    'output_files/events_spi_9m_polygon/events/drought_spi_9m_polygon_events.csv',
)
DEFAULT_SVOBS_CSV = os.path.join(
    _SCRIPT_PATH,
    'output_files/events_spi_9m_polygon/event_svobs/drought_spi_9m_polygon_svobs.csv',
)
DEFAULT_NODES_MCF = os.path.join(
    _SCRIPT_PATH,
    'output_files/events_spi_9m_polygon/events/drought_event_nodes.mcf',
)

FLAGS = flags.FLAGS
flags.DEFINE_string(
    'events_csv',
    DEFAULT_EVENTS_CSV,
    'Path to merged drought_spi_9m_polygon_events.csv.',
)
flags.DEFINE_string(
    'svobs_csv',
    DEFAULT_SVOBS_CSV,
    'Path to merged drought_spi_9m_polygon_svobs.csv to deduplicate in place.',
)
flags.DEFINE_string(
    'nodes_mcf',
    DEFAULT_NODES_MCF,
    'Output path for generated DroughtEvent entity MCF nodes.',
)


def _strip_namespace(value: str) -> str:
    """Strips dcid: or dcs: prefix from a DCID string."""
    val = value.strip()
    for prefix in ('dcid:', 'dcs:', 'schema:'):
        if val.startswith(prefix):
            return val[len(prefix):]
    return val


def deduplicate_event_svobs(svobs_csv_path: str) -> Tuple[Set[str], int, int]:
    """Deduplicates event observations CSV by (dcid, observationDate).

    Aggregates duplicate (dcid, observationDate) rows using:
      - area = max(area)
      - standardizedPrecipitationIndex = min(standardizedPrecipitationIndex)

    Args:
        svobs_csv_path: Path to drought_spi_9m_polygon_svobs.csv.

    Returns:
        Tuple of (unique bare event DCIDs, input row count, deduplicated row count).

    Raises:
        FileNotFoundError: If svobs_csv_path does not exist.
        ValueError: If required columns are missing from svobs_csv_path.
    """
    if not os.path.isfile(svobs_csv_path):
        raise FileNotFoundError(
            f'Event observations CSV not found: {svobs_csv_path}')

    csv.field_size_limit(sys.maxsize)
    aggregated: Dict[Tuple[str, str], Tuple[Optional[float],
                                            Optional[float]]] = {}
    event_dcids: Set[str] = set()
    input_rows = 0

    with open(svobs_csv_path, 'r', encoding='utf-8', newline='') as infile:
        reader = csv.DictReader(infile, escapechar='\\')
        required_cols = {
            'dcid', 'observationDate', 'area', 'standardizedPrecipitationIndex'
        }
        if not reader.fieldnames or not required_cols.issubset(
                set(reader.fieldnames)):
            raise ValueError(
                f'Missing required columns {required_cols} in {svobs_csv_path}; '
                f'found {reader.fieldnames}')

        for row in reader:
            dcid = _strip_namespace(row.get('dcid', ''))
            obs_date = (row.get('observationDate') or '').strip()
            if not dcid or not obs_date:
                continue
            input_rows += 1
            event_dcids.add(dcid)

            area_str = (row.get('area') or '').strip()
            spi_str = (row.get('standardizedPrecipitationIndex') or '').strip()
            area_val = float(area_str) if area_str != '' else None
            spi_val = float(spi_str) if spi_str != '' else None

            key = (dcid, obs_date)
            if key not in aggregated:
                aggregated[key] = (area_val, spi_val)
            else:
                prev_area, prev_spi = aggregated[key]
                new_area = (max(prev_area, area_val) if
                            prev_area is not None and area_val is not None else
                            (prev_area if prev_area is not None else area_val))
                new_spi = (min(prev_spi, spi_val)
                           if prev_spi is not None and spi_val is not None else
                           (prev_spi if prev_spi is not None else spi_val))
                aggregated[key] = (new_area, new_spi)

    output_dir = os.path.dirname(os.path.abspath(svobs_csv_path))
    os.makedirs(output_dir, exist_ok=True)
    fieldnames = [
        'dcid', 'observationDate', 'area', 'standardizedPrecipitationIndex'
    ]

    with tempfile.NamedTemporaryFile(mode='w',
                                     encoding='utf-8',
                                     newline='',
                                     dir=output_dir,
                                     delete=False,
                                     suffix='.tmp') as tmp_file:
        tmp_path = tmp_file.name
        writer = csv.DictWriter(tmp_file,
                                fieldnames=fieldnames,
                                delimiter=',',
                                escapechar='\\',
                                quotechar='"',
                                quoting=csv.QUOTE_MINIMAL,
                                lineterminator='\n',
                                doublequote=False)
        writer.writeheader()
        for dcid, obs_date in aggregated:
            area_val, spi_val = aggregated[(dcid, obs_date)]
            writer.writerow({
                'dcid':
                    dcid,
                'observationDate':
                    obs_date,
                'area':
                    round(area_val, 3) if area_val is not None else '',
                'standardizedPrecipitationIndex':
                    round(spi_val, 3) if spi_val is not None else '',
            })

    os.replace(tmp_path, svobs_csv_path)
    logging.info(
        'Deduplicated %s: %d input rows -> %d unique (dcid, observationDate) rows '
        '(%d duplicate rows merged).',
        svobs_csv_path,
        input_rows,
        len(aggregated),
        input_rows - len(aggregated),
    )
    return event_dcids, input_rows, len(aggregated)


def extract_event_dcids_from_events_csv(events_csv_path: str) -> Set[str]:
    """Extracts unique DroughtEvent DCIDs from drought_spi_9m_polygon_events.csv."""
    if not events_csv_path or not os.path.isfile(events_csv_path):
        logging.warning('Events CSV not found at %s; using svobs DCIDs only.',
                        events_csv_path)
        return set()

    csv.field_size_limit(sys.maxsize)
    event_dcids: Set[str] = set()
    with open(events_csv_path, 'r', encoding='utf-8', newline='') as infile:
        reader = csv.DictReader(infile, escapechar='\\')
        for row in reader:
            dcid = _strip_namespace(row.get('dcid', ''))
            if dcid:
                event_dcids.add(dcid)
    logging.info('Extracted %d unique DroughtEvent DCIDs from %s.',
                 len(event_dcids), events_csv_path)
    return event_dcids


def write_drought_event_nodes_mcf(event_dcids: Set[str],
                                  nodes_mcf_path: str) -> int:
    """Writes DroughtEvent instance nodes to an MCF file atomically."""
    output_dir = os.path.dirname(os.path.abspath(nodes_mcf_path))
    os.makedirs(output_dir, exist_ok=True)
    sorted_dcids = sorted(event_dcids)

    with tempfile.NamedTemporaryFile(mode='w',
                                     encoding='utf-8',
                                     dir=output_dir,
                                     delete=False,
                                     suffix='.tmp') as tmp_file:
        tmp_path = tmp_file.name
        for dcid in sorted_dcids:
            tmp_file.write(f'Node: dcid:{dcid}\n')
            tmp_file.write('typeOf: dcs:DroughtEvent\n\n')

    os.replace(tmp_path, nodes_mcf_path)
    logging.info('Wrote %d DroughtEvent nodes to %s.', len(sorted_dcids),
                 nodes_mcf_path)
    return len(sorted_dcids)


def postprocess_events(events_csv_path: str, svobs_csv_path: str,
                       nodes_mcf_path: str) -> Dict[str, Any]:
    """Deduplicates event observations CSV and writes DroughtEvent nodes MCF."""
    svobs_dcids, input_rows, deduped_rows = deduplicate_event_svobs(
        svobs_csv_path)
    events_dcids = extract_event_dcids_from_events_csv(events_csv_path)
    all_dcids = svobs_dcids | events_dcids
    num_nodes = write_drought_event_nodes_mcf(all_dcids, nodes_mcf_path)
    return {
        'input_svobs_rows': input_rows,
        'deduped_svobs_rows': deduped_rows,
        'duplicates_removed': input_rows - deduped_rows,
        'event_nodes_written': num_nodes,
    }


def main(_):
    try:
        postprocess_events(FLAGS.events_csv, FLAGS.svobs_csv, FLAGS.nodes_mcf)
    except Exception as exc:  # pylint: disable=broad-except
        logging.fatal('Failed to postprocess drought events: %s', exc)


if __name__ == '__main__':
    app.run(main)
