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
"""Script to process Geo events and SVObs.
"""

import csv
import datetime
import os
import pickle
import sys
import time

from absl import app
from absl import flags
from absl import logging
from datetime import timedelta
from dateutil import parser
from geopy import distance
from s2sphere import LatLng, CellId
from typing import Union

flags.DEFINE_string('input_csv', '', 'CSV with S2 cell data to process')
flags.DEFINE_string('config', '', 'JSON config file')
flags.DEFINE_string('input_events', '', 'File with active events to be loaded')
flags.DEFINE_integer('input_rows', sys.maxsize,
                     'Number of input ros to process per file')
flags.DEFINE_string('output_path', '', 'Output path for events data')
flags.DEFINE_string('output_events', '',
                    'File into which active events are saved')
flags.DEFINE_bool('debug', False, 'Enable debug messages')

_FLAGS = flags.FLAGS

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))

import utils

from util.counters import Counters
from util.config_map import ConfigMap, read_py_dict_from_file, write_py_dict_to_file

_DEBUG = False

_DEFAULT_CONFIG = {
    # Input settings.
    # Columms of input_csv that are added as event properties
    'data_columns': ['area'],
    # Columns of input_csv that contains the s2 cell id.
    's2_cell_column': 's2CellId',
    # Input column for date.
    'date_column': 'date',

    # Processing settings
    # Maximum distance within which 2 events are merged.
    'max_overlap_distance_km': 10,
    # S2 level to which data is aggregated.
    's2_level': 10,  # Events are at resolution of level-10 S2 cells.
    'aggregate': 'sum',  # default aggregation for all properties
    # Per property settings
    'property_config': {
        'area': {
            'aggregate': 'sum',
            'unit': 'SquareKilometer',
        },
    },
    # Treat events at the same location more than 90 days apart as separate events.
    'max_event_interval_days': 90,

    # Output settings.
    'event_type': 'FloodEvent',
}


class GeoEvent:
    """Class for a Geo Event."""

    def __init__(self,
                 event_id: str,
                 s2_cell_id: int = None,
                 date: str = None,
                 pvs: dict = None,
                 config: ConfigMap = None):
        # Initialize members
        self._event_id = ''
        self._event_name = ''
        self._config = config
        self._s2_cells = {}
        # In case this event is merged into another, set the id.
        self._merged_into_event = None
        self.start_date = None
        # For events that have ended, an end_date is set.
        self.end_date = None

        # Set input values
        if not config:
            self._config = ConfigMap()
        if event_id:
            self.set_event_id(event_id)
        # Dictionary of S2 Cell Ids as int keys mapping to
        # a dictionary of event properties keyed by date strings.
        # _s2_cells[0x123] = { '2022-12-20': { 'area': 1.2 } }
        if s2_cell_id and date and pvs:
            self.add_s2_cell_pvs(s2_cell_id, date, pvs)

    def add_s2_cell_pvs(self, s2_cell_id: int, date: str, pvs: dict):
        '''Add an S2Cell for a given date into this event.'''
        if not self._event_id:
            self._generate_event_id(s2_cell_id, date)
        if s2_cell_id not in self._s2_cells:
            self._s2_cells[s2_cell_id] = dict()
        s2_cell_dates = self._s2_cells[s2_cell_id]
        if date not in s2_cell_dates:
            s2_cell_dates[date] = dict()
        s2_cell_date_pvs = s2_cell_dates[date]
        utils.dict_aggregate_values(pvs, s2_cell_date_pvs,
                                    self._config.get('property_config', {}))
        _DEBUG and logging.debug(
            f'Added {s2_cell_id}:{date}:{pvs} into event:{self._event_id}:{self._s2_cells}'
        )

    def event_id(self, parent_event: bool = True) -> str:
        if parent_event:
            return self.get_root_event()._event_id
        return self._event_id

    def get_event_name(self) -> str:
        return self.get_root_event()._event_name

    def get_s2_cells(self) -> dict:
        return self._s2_cells

    def merge_event(self, s2_event):
        '''Merge s2 cells and PVs from s2_event into this event.'''
        if s2_event.get_root_event() != s2_event:
            logging.fatal(
                f'Cannot merge non-root event {s2_event._event_id} into {self._event_id}'
            )
        for s2_cell_id, date_pvs in s2_event.get_s2_cells().items():
            for date, pvs in date_pvs.items():
                self.add_s2_cell_pvs(s2_cell_id, date, pvs)
        s2_event._merged_into_event = self
        _DEBUG and logging.debug(
            f'Merged events {s2_event.event_id()} into {self.event_id()}: {self._s2_cells}'
        )

    def get_root_event(self):
        event = self
        while event._merged_into_event:
            event = event._merged_into_event
        return event

    def get_event_dates(self) -> list:
        '''Returns a list of dates across all S2 cells for the event.'''
        dates = set()
        for date_pvs in self.get_s2_cells().values():
            for date in date_pvs.keys():
                dates.add(date)
        return sorted(list(dates))

    def get_event_s2_cells(self, dates: set = {}) -> list:
        '''Returns a list of s2Cells for the event on the date.'''
        s2_cell_ids = set()
        for s2_cell_id, date_pvs in self.get_s2_cells().items():
            for date in date_pvs.keys():
                if not dates or date in dates:
                    s2_cell_ids.add(s2_cell_id)
        return sorted(list(s2_cell_ids))

    def get_event_properties(self, dates: set = {}) -> dict:
        '''Returns the properties aggregated across all S2Cells for the dates.'''
        pvs = dict()
        for date_pvs in self.get_s2_cells().values():
            for date, date_pvs in date_pvs.items():
                if not dates or date in dates:
                    utils.dict_aggregate_values(
                        date_pvs, pvs, self._config.get('property_config', {}))
        return pvs

    def set_end_date(self, date: str):
        '''Set the end date for an event that has ended.'''
        self.end_date = date

    def set_event_id(self, event_id: str):
        '''Set the event id and name.'''
        if event_id and '/' in event_id:
            date_cell = event_id.split('/', 1)[1]
            if date_cell:
                date, cell = date_cell.split('_', 1)
                if date and cell:
                    self._generate_event_id(int(cell, 16), date)
        else:
            self._event_id = ''
            self._event_name = ''

    def _generate_event_id(self, s2_cell_id: int, date: str) -> str:
        '''Returns the event id.'''
        event_type = self._config.get('event_type', 'FloodEvent')
        prefix = event_type
        if event_type:
            prefix = event_type[0].lower() + event_type[1:]
        self._event_id = f'{prefix}/{date}_{s2_cell_id:#018x}'
        level = CellId(s2_cell_id).level()
        self.start_date = date
        self._event_name = f'{event_type} that started on {date} within Level {level} S2 cell {s2_cell_id:#018x}'


class GeoEventsDict:
    """Class that maps s2 cell ids to GeoEvent objects."""

    def __init__(self, config: ConfigMap, counters: Counters = None):
        self._config = config
        # Dictionary of all events keyed by event-id.
        # Assumes events for the same place across different dates have
        # different ids.
        self._event_by_id = dict()
        # Dictionary of active events keyed by s2_cell_id (int)
        self._active_event_by_s2 = dict()
        # Properties across all events.
        self._event_props = set()
        # Max date seen across all events.
        self._max_date = ''
        self._counters = counters
        if counters is None:
            self._counters = Counters()

    def add_s2_event(self, s2_event: GeoEvent):
        '''Add an S2 event to the dict.'''
        self._event_by_id[s2_event.event_id()] = s2_event
        for s2_cell_id in s2_event.get_s2_cells().keys():
            self._active_event_by_s2[s2_cell_id] = s2_event
        self._counters.add_counter('s2_events_added', 1)
        _DEBUG and logging.debug(
            f'Added event {s2_event.event_id()}, num events: {len(self._event_by_id)}, num s2 cells: {len(self._active_event_by_s2)}'
        )

    def get_event_by_id(self,
                        event_id: str,
                        parent_event: bool = True) -> GeoEvent:
        event = self._event_by_id.get(event_id, None)
        if event and parent_event:
            return event.get_root_event()
        return event

    def get_active_event_by_s2_cell(self, s2_cell_id: int) -> GeoEvent:
        event = self._active_event_by_s2.get(s2_cell_id, None)
        if event:
            return event.get_root_event()
        return event

    def get_events_for_s2_cell(self, s2_cell_id: int) -> list:
        '''Returns a list of GeoEvent Ids that overlaps with the s2_cell.
        It considers a buffer of neighboring s2 cells of the same level
        for overlap upto a buffer distance specified.'''
        event_ids = set()
        s2_cell = CellId(s2_cell_id)
        cell_event = self._active_event_by_s2.get(s2_cell_id, None)
        if cell_event:
            event_ids.add(cell_event.event_id())

        # Collect any event_ids for neighboring cells within allowed distance.
        neighbour_cells = set({s2_cell_id})
        max_distance = self._config.get('max_overlap_distance_km', 10)
        cell_distance = 0
        while cell_distance < max_distance:
            # Get the neighbors of current cells.
            new_neighbours = set()
            for cell_id in neighbour_cells:
                s2_cell = CellId(cell_id)
                for n in s2_cell.get_all_neighbors(s2_cell.level()):
                    if n.id() not in neighbour_cells:
                        new_neighbours.add(n.id())
            if not new_neighbours:
                break
            cell_distance = utils.s2_cells_distance(s2_cell_id,
                                                    _first(new_neighbours))
            if cell_distance > max_distance:
                # Neighbours are too far. Ignore them
                break
            for n in new_neighbours:
                cell_event = self.get_active_event_by_s2_cell(n)
                if cell_event:
                    event_id = cell_event.event_id()
                    if event_id not in event_ids:
                        event_ids.add(event_id)
            neighbour_cells.update(new_neighbours)
        self._counters.max_counter('max_s2_neighbours_considered',
                                   len(neighbour_cells))

        _DEBUG and logging.debug(
            f'Got event_ids: {event_ids} for {len(neighbour_cells)} neighbors of {s2_cell_id}'
        )
        return list(event_ids)

    def is_event_active(self, event_id: str, min_date: str) -> bool:
        '''Returns true if all the dates in the event are less than min_date.'''
        event = self.get_event_by_id(event_id)
        if not event:
            return False
        event_end_date = ''
        if event.end_date:
            event_end_date = event.end_date
        else:
            event_dates = event.get_event_dates()
            if event_dates:
                event_end_date = event_dates[-1]
        if event_end_date and event_end_date < min_date:
            event.set_end_date(event_end_date)
            return False
        return True

    def get_active_event_ids(self, date: str = None) -> list:
        '''Returns a list of active event ids.
        An event with an end date within 'max_event_interval_days' days
        of the given date is considered active.
        '''
        if not date:
            date = self._max_date
        min_date = self._get_date_with_interval(date)
        active_ids = []
        for event_id in self._event_by_id.keys():
            if self.is_event_active(event_id, min_date):
                active_ids.append(event_id)
        return active_ids

    def deactivate_old_events(self, event_ids: list, date: str) -> list:
        '''Removes any events that ended long time ago compared to date.
        The events are retained in _event_by_id but removed from _active_event_by_s2 index.
        '''
        # Get the minimum date for active events compared to given date.
        min_date = self._get_date_with_interval(date)
        # Check for events with end date older than threshold.
        # Mark such events as inactive.
        active_ids = []
        for event_id in event_ids:
            if self.is_event_active(event_id, min_date):
                active_ids.append(event_id)
            else:
                # Event ended too long ago. Remove from active s2 cells.
                _DEBUG and logging.debug(
                    f'Deactivating event: {event_id} with end: {event_end_date} older than {min_date}'
                )
                self.remove_event_from_s2_index(event_id)
        return active_ids

    def remove_event_from_s2_index(self, event_id: str):
        '''Remove the s2 cells for this event from the _active_event_by_s2 index.'''
        event = self.get_event_by_id(event_id)
        s2_cells = event.get_s2_cells().keys()
        _DEBUG and logging.debug(
            f'Removing event {event_id} active s2 cells: {s2_cells}')
        for s2_cell_id in s2_cells:
            if s2_cell_id in self._active_event_by_s2:
                self._active_event_by_s2.pop(s2_cell_id)
        self._counters.add_counter('events_deactivated', 1, event_id)
        self._counters.add_counter('events_s2_cells_deactivated', len(s2_cells),
                                   event_id)

    def add_s2_data(self, s2_cell_id: int, date: str, pvs: dict) -> str:
        '''Returns the event id after adding s2 cell with PVs for a date.'''
        s2_event_ids = self.get_events_for_s2_cell(s2_cell_id)
        self._event_props.update(set(pvs.keys()))

        # Retire old events that ended too long compared to given date.
        # Assumes data is added in increasing order of dates.
        s2_event_ids = self.deactivate_old_events(s2_event_ids, date)

        if not s2_event_ids:
            # Add this as a new event.
            s2_event = GeoEvent(event_id='',
                                s2_cell_id=s2_cell_id,
                                date=date,
                                pvs=pvs,
                                config=self._config)
            self.add_s2_event(s2_event)
            event_id = s2_event.event_id()
            _DEBUG and logging.debug(
                f'Created new event: {event_id} for {s2_cell_id}:{date}:{pvs}')
            return event_id

        # Merge all events that new region overlaps with.
        sorted_ids = sorted(list(s2_event_ids))
        _DEBUG and logging.debug(
            f'Merging events for cell: {s2_cell_id}: {sorted_ids}')
        root_event_id = sorted_ids[0]
        root_event = self.get_event_by_id(root_event_id)
        if not root_event:
            logging.fatal(f'Unable to find event for {root_event_id}')
        root_event.add_s2_cell_pvs(s2_cell_id, date, pvs)
        for event_id in sorted_ids[1:]:
            event = self.get_event_by_id(event_id)
            root_event.merge_event(event)
        _DEBUG and logging.debug(
            f'Added {s2_cell_id}, {date}, {pvs} into event: {root_event_id}')
        self._counters.add_counter('s2_event_mergers', 1)
        self._counters.add_counter('s2_events_merged', len(sorted_ids))
        self._counters.max_counter('max_event_s2_cells',
                                   len(root_event.get_s2_cells()))
        self._max_date = max(self._max_date, date)
        return root_event_id

    def get_all_event_ids(self) -> set:
        '''Returns all root events ids.'''
        event_ids = set()
        for event_id in self._event_by_id.keys():
            event = self.get_event_by_id(event_id)
            event_ids.add(event.event_id())
        return event_ids

    def write_events_csv(self,
                         output_path: str,
                         event_ids: list = None,
                         output_ended_events: bool = False):
        '''Write the events into a csv file.'''
        output_csv = utils.file_get_name(output_path, 'events', '.csv')
        output_columns = ['eventId', 'typeOf', 'name', 'startDate', 'endDate']
        output_columns.append('startLocation')
        output_columns.extend(list(self._event_props))
        output_columns.append('s2Cells')
        output_columns.append('subEvents')
        if not event_ids:
            event_ids = self.get_all_event_ids()
        num_output_events = 0
        with open(output_csv, 'w') as csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=output_columns,
                                    escapechar='\\',
                                    extrasaction='ignore',
                                    quotechar='"',
                                    quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            for event_id in event_ids:
                event = self.get_event_by_id(event_id)
                if not event:
                    self._counters.add_counter('error-missing-event-for-id', 1,
                                               event_id)
                    logging.fatal(f'Unable to get event for {event_id}')
                    continue
                if output_ended_events and self.is_event_active(
                        event_id, self._max_date):
                    self._counters.add_counter(
                        'output_csv_ignored_active_events', 1, event_id)
                    continue
                data = dict()
                data['eventId'] = event_id
                data['typeOf'] = self._config.get('event_type', 'FloodEvent')
                data['name'] = event.get_event_name()
                dates = event.get_event_dates()
                if dates:
                    data['startDate'] = dates[0]
                    data['endDate'] = dates[-1]
                start_s2_cell_ids = event.get_event_s2_cells(
                    {data.get('startDate', None)})
                if start_s2_cell_ids:
                    start_s2_cell = CellId(start_s2_cell_ids[0])
                    latlng = start_s2_cell.to_lat_lng()
                    lat = latlng.lat().degrees
                    lng = latlng.lng().degrees
                    data['startLocation'] = f'[LatLong {lat:.5f} {lng:.5f}]'
                s2_cell_ids = event.get_s2_cells()
                if s2_cell_ids:
                    data['s2Cells'] = ','.join(
                        [f'{s2_cell_id:#018x}' for s2_cell_id in s2_cell_ids])
                event_pvs = event.get_event_properties({dates[-1]})
                data.update(
                    _format_property_values(
                        event_pvs, self._config.get('property_config', {})))
                writer.writerow(data)
                num_output_events += 1
                self._counters.add_counter('output_events', 1)
                self._counters.max_counter('max_output_events_dates',
                                           len(dates))
                self._counters.max_counter('max_output_events_s2_cells',
                                           len(s2_cell_ids))
        logging.info(
            f'Wrote {num_output_events} events into {output_csv} with columns: {output_columns}'
        )
        self._counters.print_counters()

    def write_events_svobs(self,
                           output_path: str,
                           event_ids: list = None,
                           output_ended_events: bool = False,
                           event_props: list = None,
                           min_date: str = '',
                           max_date: str = ''):
        '''Write SVObs for all events into a CSV.'''
        output_csv = utils.file_get_name(output_path, 'svobs', '.csv')
        output_columns = ['eventId', 'date']
        if not event_props:
            # No specific properties given. Generate SVObs for all properties.
            event_props = list(self._event_props)
        output_columns.extend(event_props)
        if not event_ids:
            event_ids = self.get_all_event_ids()
        with open(output_csv, 'w') as csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=output_columns,
                                    escapechar='\\',
                                    extrasaction='ignore',
                                    quotechar='"',
                                    quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            num_output_events = 0
            for event_id in event_ids:
                event = self.get_event_by_id(event_id)
                if not event:
                    self._counters.add_counter('error_missing_event_for_id', 1,
                                               event_id)
                    logging.fatal(f'Unable to get event for {event_id}')
                    continue
                event_dates = event.get_event_dates()
                if not event_dates:
                    self._counters.add_counter('ignored_event_no_dates', 1,
                                               event_id)
                    logging.debug(f'Ignoring event with no dates: {event}')
                    continue
                if output_ended_events and self.is_event_active(
                        event_id, self._max_date):
                    self._counters.add_counter(
                        'output_csv_ignored_active_events_svobs', 1, event_id)
                    continue
                # Generate observations for each event date.
                num_output_dates = 0
                for date in event_dates:
                    if min_date and date < min_date:
                        self._counters.add_counter('ignored_svobs_min_date', 1,
                                                   event_id)
                        continue
                    if max_date and date > max_date:
                        self._counters.add_counter('ignored_svobs_max_date', 1,
                                                   event_id)
                        continue
                    num_output_dates += 1
                    svobs_pvs = event.get_event_properties(date)
                    if svobs_pvs:
                        self._counters.add_counter('output_events_svobs_rows',
                                                   1, event_id)
                        self._counters.add_counter('output_events_svobs',
                                                   len(svobs_pvs), event_id)
                        svobs_pvs['eventId'] = event_id
                        svobs_pvs['date'] = date
                        writer.writerow(svobs_pvs)
                    # Track min/max counters for properties
                    for prop, value in svobs_pvs.items():
                        self._counters.min_counter(f'output_svobs_min_{prop}',
                                                   value)
                        self._counters.max_counter(f'output_svobs_max_{prop}',
                                                   value)
                if num_output_dates:
                    num_output_events += 1
                    self._counters.add_counter('output_events_with_svobs', 1)
                    self._counters.max_counter('max_output_events_svobs_dates',
                                               num_output_dates)
        logging.info(
            f'Wrote {num_output_events} events into {output_csv} with columns: {output_columns}'
        )
        self._counters.print_counters()

    def write_active_events(self, filename: str):
        '''Save active events into a file.'''
        # Get a dict of all active events by id.
        active_events = {}
        active_ids = self.get_active_event_ids(self._max_date)
        for event_id in active_ids:
            event = self.get_event_by_id(event_id)
            if event:
                active_events[event_id] = event.get_s2_cells()

        # Save the active events into a file.
        # with open(filename, 'wb') as file:
        #    pickle.dump(active_events, file)
        logging.info(f'Writing {len(active_events)} events to file: {filename}')
        write_py_dict_to_file(active_events, filename)
        self._counters.set_counter('active_events', len(active_events))

    def read_active_events(self, filename: str):
        '''Load active events from a file.'''
        # with open(filename, 'rb') as file:
        #    active_events = pickle.load(file)
        active_events = read_py_dict_from_file(filename)
        _DEBUG and logging.debug(f'Read events: {active_events}')

        for event_id, event_dict in active_events.items():
            s2_event = GeoEvent(event_id=event_id, config=self._config)
            for s2_cell_id, date_pvs in event_dict.items():
                for date in sorted(date_pvs.keys()):
                    pvs = date_pvs[date]
                    s2_event.add_s2_cell_pvs(s2_cell_id, date, pvs)
            self.add_s2_event(s2_event)
        logging.info(
            f'Loaded {len(active_events)} events from file: {filename}')

    def _get_date_with_interval(self, date: str) -> str:
        '''Returns the date with the interval 'max_event_interval_days' applied.'''
        interval_days = timedelta(
            days=self._config.get('max_event_interval_days', 30))
        min_date = (parser.parse(date) - interval_days).isoformat()
        return min_date


def process_csv(csv_files: list, input_events_file: str, output_path: str,
                output_events_file: str, config: ConfigMap):
    '''Process CSV files with data for S2cells into events.
    '''
    counters = Counters()
    s2_events_dict = GeoEventsDict(config, counters)
    if input_events_file:
        s2_events_dict.read_active_events(input_events_file)
    props = config.get('data_columns', ['area'])
    s2_cell_column = config.get('s2_cell_column', 's2CellId')
    date_column = config.get('date_column', 'date')
    input_files = utils.file_get_matching(csv_files)
    for filename in input_files:
        counters.add_counter('total', utils.file_estimate_num_rows(filename))
    for filename in input_files:
        with open(filename) as csvfile:
            logging.info(f'Processing csv data file: {filename}')
            reader = csv.DictReader(csvfile)
            counters.add_counter('input-files', 1, filename)
            num_rows = 0
            for row in reader:
                num_rows += 1
                if num_rows > config.get('input_rows', sys.maxsize):
                    break
                counters.add_counter('inputs', 1, filename)
                s2_cell_str = row[s2_cell_column]
                s2_cell_id = int(s2_cell_str[s2_cell_str.find('/') + 1:], 16)
                s2_cell = CellId(s2_cell_id)
                output_s2_cell_id = s2_cell.parent(
                    config.get('s2_level', s2_cell.level())).id()
                date = row[date_column]
                data_pvs = {}
                for p in props:
                    if p in row:
                        data = utils.str_get_numeric_value(row[p])
                        if data is not None:
                            data_pvs[p] = data
                s2_events_dict.add_s2_data(output_s2_cell_id, date, data_pvs)
            logging.info(
                f'Created {len(s2_events_dict._event_by_id)} events for {num_rows} rows from file: {filename}'
            )
    # Output all ended events
    s2_events_dict.write_events_csv(output_path=output_path,
                                    output_ended_events=True)
    s2_events_dict.write_events_svobs(output_path=output_path,
                                      output_ended_events=True)
    # Output active events into a separate set of files.
    active_event_ids = s2_events_dict.get_active_event_ids(
        s2_events_dict._max_date)
    s2_events_dict.write_events_csv(output_path=output_path + '_active_',
                                    event_ids=active_event_ids,
                                    output_ended_events=False)
    s2_events_dict.write_events_svobs(output_path=output_path + '_active_',
                                      event_ids=active_event_ids,
                                      output_ended_events=False)
    if output_events_file:
        s2_events_dict.write_active_events(output_events_file)


def _first(s: set):
    for item in s:
        break
    return item


def _format_property_values(pvs: dict, config: dict) -> dict:
    '''Returns a set of properties with formatted values.'''
    fmt_pvs = {}
    for prop, value in pvs.items():
        fmt_value = value
        prop_config = config.get(prop, None)
        if prop_config:
            prop_unit = prop_config.get('unit', None)
            if prop_unit:
                fmt_value = f'[{fmt_value} {prop_unit}]'
        fmt_pvs[prop] = fmt_value
    return fmt_pvs


def main(_):
    _DEBUG = _FLAGS.debug
    if _DEBUG:
        logging.set_verbosity(2)
    config = ConfigMap(filename=_FLAGS.config)
    config.set_config('input_rows', _FLAGS.input_rows)
    config.set_config('debug', _FLAGS.debug)
    process_csv(_FLAGS.input_csv, _FLAGS.input_events, _FLAGS.output_path,
                _FLAGS.output_events, config)


if __name__ == '__main__':
    app.run(main)
