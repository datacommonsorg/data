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
"""Script to generate Geo events and SVObs.
"""

import csv
import datetime
import os
import pickle
import sys
import time
import datacommons as dc

from absl import app
from absl import flags
from absl import logging
from datetime import timedelta
from dateutil import parser
from geopy import distance
from s2sphere import LatLng, CellId
from shapely.geometry import Polygon, mapping
from typing import Union

# Setup pprof
#os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
#from pypprof.net_http import start_pprof_server

flags.DEFINE_string('input_csv', '',
                    'CSV with place data to process into events')
flags.DEFINE_string('config', '', 'JSON config file')
flags.DEFINE_string('config_string', '',
                    'config settings that override config file')
flags.DEFINE_string('input_events', '', 'File with active events to be loaded')
flags.DEFINE_integer('input_rows', sys.maxsize,
                     'Number of input to process per file')
flags.DEFINE_string('output_path', '', 'Output path for events data')
flags.DEFINE_string('output_active_path', '',
                    'Output path for active events data')
flags.DEFINE_string('output_active_events_state', '',
                    'File into which active events are saved')
# Place dcid to containedInPlace mappings generated using the SQL query:
# SELECT id as dcid,
#   ARRAY_TO_STRING(linked_contained_in_place, ',') as containedInPlace
# FROM `datcom-store.dc_kg_latest.Place`
# WHERE  type = "S2CellLevel10"
flags.DEFINE_string('place_cache_file', '',
                    'CSV file with dcid to containedInPlace mapping')
flags.DEFINE_bool('debug', False, 'Enable debug messages')
flags.DEFINE_integer('pprof_port', 8081, 'HTTP port for pprof server.')

_FLAGS = flags.FLAGS

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)))

import utils

from util.counters import Counters
from util.latlng_recon_geojson import LatLng2Places
from util.config_map import ConfigMap
from util.dc_api_wrapper import dc_api_batched_wrapper

_DEBUG = False

_DEFAULT_CONFIG = {
    # Input settings.
    # Columms of input_csv that are added as event properties
    'input_columns': [],
    # Columns of input_csv that contains the place such as s2 cell id.
    'place_column': 's2CellId',
    # Input column for date.
    'date_column': 'observationDate',
    # Rename input columns to output columns.
    'input_rename_columns': {
        # Only output columns starting with lower case are added to tmcf.
        # '<input-column>': '<output-column>'
        #'date': 'observationDate',
    },

    # Processing settings
    # Maximum distance within which 2 events are merged.
    'max_overlap_distance_km': 10,
    # S2 level to which data is aggregated.
    's2_level': 10,  # Events are at resolution of level-10 S2 cells.
    'aggregate': 'sum',  # default aggregation for all properties
    # Per property filter params for input data.
    'input_filter_config': {
        # '<prop>' : {
        #   'min': <min>,
        #   'max': <max>,
        #   'regex': '<regex>',
        # },
    },
    # Per property filter params for output events
    'output_events_filter_config': {
        # '<prop>' : {
        #   'min': <min>,
        #   'max': <max>,
        #   'regex': '<regex>',
        # },
    },
    # Per property aggregation settings for an event across places and dates.
    # For different  per-date and per-place aggregations, use the settings
    # 'property_config_per_date' and 'property_config_across_dates'.
    'property_config': {
        'aggregate': 'max',
        'area': {
            'aggregate': 'sum',
            'unit': 'SquareKilometer',
        },
        'affectedPlace': {
            'aggregate': 'list',
        },
    },
    # Per property aggregation settings for a date across multiple places.
    # Falls back to 'property_config' if not set.
    # 'property_config_per_date': {
    #     # Default aggregation for all properties: pick max value across cells.
    #     'aggregate': 'max',
    #     'area': {
    #         'aggregate': 'sum',
    #         'unit': 'SquareKilometer',
    #     },
    #     's2CellId': {
    #         'aggregate': 'list',
    #     },
    # },
    # Per property aggregation settings across multiple dates.
    # Falls back to 'property_config' if not set.
    # 'property_config_across_dates': {
    #     # Default aggregation for all properties: pick max value across cells.
    #     'aggregate': 'max',
    #     'area': {
    #         'aggregate': 'max',
    #         'unit': 'SquareKilometer',
    #     },
    #     's2CellId': {
    #         'aggregate': 'list',
    #     },
    # },
    # Threshold for dates and places in events
    # Treat events at the same location more than 90 days apart as separate events.
    'max_event_interval_days': 90,
    'max_event_duration_days': 90,
    'max_event_places': 10000,

    # Output settings.
    'event_type': 'FloodEvent',
    'resolve_affected_place_latlng': True,
    'output_affected_place_polygon': 'geoJsonCoordinatesDP1',
    'polygon_simplification_factor': 0.1,

    # Disable svobs output until it can be used in UI
    'output_svobs': False,
    'output_active_svobs': False,
    # Disable place lookups for s2 cells to be added to affectedPlace.
    'lookup_contained_for_place': False,
}


class GeoEvent:
    """Class for a Geo Event."""

    def __init__(self,
                 event_id: str,
                 place_id: str = None,
                 date: str = None,
                 pvs: dict = None,
                 config: ConfigMap = None):
        # Initialize members
        self._event_id = ''
        self._event_name = ''
        self._config = config
        # Dictionary of place ids mapped to
        # a dictionary of event properties keyed by date strings.
        #_places['s2CellId/0x123'] = {'2022-12-20' : {'area' : 1.2 } }
        self._places = {}
        # In case this event is merged into another, set the id of parent.
        self._merged_into_event = None
        self.start_date = ''
        self.end_date = ''

        # Set input values
        if not config:
            self._config = ConfigMap()
        if event_id:
            self.set_event_id(event_id)
        if place_id and date and pvs:
            self.add_place_pvs(place_id, date, pvs)

    def add_place_pvs(self, place_id: str, date: str, pvs: dict):
        '''Add an S2Cell for a given date into this event.'''
        if not self._event_id:
            self._generate_event_id(place_id, date)
        if place_id not in self._places:
            self._places[place_id] = dict()
        place_dates = self._places[place_id]
        if date not in place_dates:
            place_dates[date] = dict()
        self.end_date = max(self.end_date, date)
        place_date_pvs = place_dates[date]
        utils.dict_aggregate_values(
            pvs, place_date_pvs,
            self._config.get('property_config_per_date',
                             self._config.get('property_config', {})))
        _DEBUG and logging.debug(
            f'Added {place_id}:{date}:{pvs} into event:{self._event_id}:{self._places}'
        )

    def event_id(self, parent_event: bool = True) -> str:
        if parent_event:
            return self.get_root_event()._event_id
        return self._event_id

    def get_event_name(self) -> str:
        return self.get_root_event()._event_name

    def get_places(self) -> dict:
        return self._places

    def merge_event(self, place_event):
        '''Merge places and PVs from place_event into this event.'''
        # Check event to be merged doesn't have a parent.
        if self == place_event or place_event.get_root_event() != place_event:
            logging.fatal(
                f'Cannot merge non-root event {place_event._event_id} into {self._event_id}'
            )
        # Merge data from all places into current event.
        for place_id, date_pvs in place_event.get_places().items():
            for date, pvs in date_pvs.items():
                self.add_place_pvs(place_id, date, pvs)
        # Set current event as parent for merged event
        place_event._merged_into_event = self
        _DEBUG and logging.debug(
            f'Merged events {place_event.event_id()} into {self.event_id()}: {self._places}'
        )

    def get_root_event(self):
        event = self
        while event._merged_into_event:
            event = event._merged_into_event
        return event

    def get_event_dates(self) -> list:
        '''Returns a list of dates across all places for the event.'''
        dates = set()
        for date_pvs in self.get_places().values():
            for date in date_pvs.keys():
                dates.add(date)
        return sorted(list(dates))

    def get_event_places(self, dates: set = {}) -> list:
        '''Returns a list of places for the event on the given dates.'''
        place_ids = set()
        for place_id, date_pvs in self.get_places().items():
            for date, pvs in date_pvs.items():
                if not dates or date in dates:
                    place_ids.add(place_id)
                if 'affectedPlace' in pvs:
                    place_ids.update(pvs.get('affectedPlace', '').split(','))
        return sorted(list(place_ids))

    def get_event_properties(self, dates: set = {}) -> dict:
        '''Returns the properties aggregated across all places for the dates.'''
        pvs = dict()
        for place_id, date_pvs in self.get_places().items():
            per_place_pvs = {}
            for date, date_pvs in date_pvs.items():
                if not dates or date in dates:
                    utils.dict_aggregate_values(
                        date_pvs, per_place_pvs,
                        self._config.get(
                            'property_config_across_dates',
                            self._config.get('property_config', {})))
            utils.dict_aggregate_values(
                per_place_pvs, pvs,
                self._config.get('property_config_per_date',
                                 self._config.get('property_config', {})))
        return pvs

    def get_event_start_date(self) -> str:
        '''Returns the start date of the event.'''
        return self.start_date

    def get_event_end_date(self) -> str:
        '''Returns the end date of the event.'''
        if self.end_date:
            return self.end_date
        # End date is not set. Pick the last date as end date.
        event_dates = self.get_event_dates()
        if event_dates:
            self.end_date = event_dates[-1]
            return self.end_date
        return ''

    def get_event_properties_by_dates(self) -> dict:
        '''Returns the properties aggregated by dates across all S2Cells'''
        pvs_by_dates = dict()
        for place_id, date_pvs in self.get_places().items():
            for date, pvs in date_pvs.items():
                if date not in pvs_by_dates:
                    pvs_by_dates[date] = dict()
                pvs_for_date = pvs_by_dates[date]
                utils.dict_aggregate_values(
                    pvs, pvs_for_date,
                    self._config.get('property_config_per_date',
                                     self._config.get('property_config', {})))
        return pvs_by_dates

    def set_end_date(self, date: str):
        '''Set the end date for an event that has ended.'''
        self.end_date = date

    def set_event_id(self, event_id: str):
        '''Set the event id and name.'''
        if event_id and '/' in event_id:
            date_place = event_id.split('/', 1)[1]
            if date_place:
                date, place = date_place.split('_', 1)
                if date and place:
                    self._generate_event_id(place, date)
        else:
            self._event_id = ''
            self._event_name = ''

    def _generate_event_id(self, place_id: str, date: str) -> str:
        '''Returns the event id.'''
        event_type = self._config.get('event_type', 'FloodEvent')
        prefix = event_type
        if event_type:
            prefix = event_type[0].lower() + event_type[1:]
        place_suffix = place_id
        name_suffix = place_id
        if place_id.startswith('s2CellId/'):
            # Use the hex cell id alone in event id as it is unique.
            # For other places such as grid_1/<lat>_<lng> , use the place_id
            place_suffix = place_id.replace('s2CellId/', '')
            s2_cell_id = int(place_suffix, 16)
            level = CellId(s2_cell_id).level()
            name_suffix = f'Level {level} S2 cell {place_suffix}'
        self._event_id = f'{prefix}/{date}_{place_suffix}'
        self.start_date = date
        self._event_name = f'{event_type} that started on {date} within {name_suffix}'


class GeoEventsProcessor:
    """Class that maps s2 cell ids to GeoEvent objects."""

    def __init__(self, config: ConfigMap, counters: Counters = None):
        self._config = config
        # Dictionary of all events keyed by event-id.
        # Assumes events for the same place across different dates have
        # different ids.
        self._event_by_id = dict()
        # Dictionary of active events keyed by place_id
        self._active_event_by_place = dict()
        # Max date seen across all events.
        self._max_date = ''
        self._counters = counters
        if counters is None:
            self._counters = Counters()
        self._counters.set_prefix('0:init_')
        # Caches
        self._place_cache_modified = False
        # dictionary from latlng to places: { '<Lat>:<Lng>': [<geoId>] }
        self._latlng_to_place_cache = utils.file_load_csv_dict(
            filename=self._config.get('place_cache_file'),
            key_column=self._config.get('place_cache_key'),
            value_column=self._config.get('place_cache_value'),
            config=self._config.get('place_cache_config', {}))
        # dictionary from placeid to tuple { <placeid>: (lat, lng) }
        self._place_property_cache = utils.file_load_py_dict(
            self._config.get('place_property_cache_file', ''))
        self._place_cache_modified = False
        self._ll2p = None
        if self._config.get('lookup_contained_for_place', False):
            self._ll2p = LatLng2Places()
        # Get properties for events
        rename_columns = self._config.get('input_rename_columns', {})
        self._event_props = set(rename_columns.values())
        data_columns = self._config.get('data_columns', [])
        for prop in data_columns:
            self._event_props.add(rename_columns.get(prop, prop))
        self._event_props.add('area')

    def add_geo_event(self, geo_event: GeoEvent):
        '''Add a geo event to the dict.'''
        self._event_by_id[geo_event.event_id()] = geo_event
        for place_id in geo_event.get_places().keys():
            self._active_event_by_place[place_id] = geo_event
        self._counters.add_counter('geo_events_added', 1)
        _DEBUG and logging.debug(
            f'Added event {geo_event.event_id()}, num events: {len(self._event_by_id)}, num places: {len(self._active_event_by_place)}'
        )

    def get_event_by_id(self,
                        event_id: str,
                        parent_event: bool = True) -> GeoEvent:
        event = self._event_by_id.get(event_id, None)
        if event and parent_event:
            return event.get_root_event()
        return event

    def get_active_event_by_place_id(self, place_id: int) -> GeoEvent:
        event = self._active_event_by_place.get(place_id, None)
        if event:
            return event.get_root_event()
        return event

    def get_events_for_place(self, place_id: str) -> list:
        '''Returns a list of GeoEvent Ids that overlaps with the place.
        It considers a buffer of neighboring places
        for overlap upto a buffer distance specified.'''
        event_ids = set()
        place_event = self._active_event_by_place.get(place_id, None)
        if place_event:
            event_ids.add(place_event.event_id())

        # Collect any event_ids for neighboring places within allowed distance.
        neighbour_places = set({utils.strip_namespace(place_id)})
        max_distance_km = self._config.get('max_overlap_distance_km', 0)
        max_place_hop = self._config.get('max_overlap_place_hop', 1)
        place_hop = 0
        place_distance_km = 0
        max_event_places = self._config.get('max_event_places', sys.maxsize)
        while place_distance_km <= max_distance_km and place_hop <= max_place_hop:
            # Get the next set of neighbors of explored places.
            place_hop += 1
            if place_hop > max_place_hop:
                break
            new_neighbours = set()
            for place_id in neighbour_places:
                for n in _get_place_neighbors_ids(place_id):
                    n = utils.strip_namespace(n)
                    if n not in neighbour_places:
                        new_neighbours.add(n)
            if not new_neighbours:
                break
            if max_distance_km:
                place_distance_km = utils.place_distance(
                    place_id, _first(new_neighbours))
                if place_distance == 0 or place_distance_km > max_distance:
                    # Neighbours are too far. Ignore them
                    break
            for n in new_neighbours:
                place_event = self.get_active_event_by_place_id(n)
                if place_event:
                    if len(place_event.get_places()) < max_event_places:
                        event_id = place_event.event_id()
                        if event_id not in event_ids:
                            event_ids.add(event_id)
                    else:
                        self._counters.add_counter(
                            'events_skipped_with_max_places', 1)
            neighbour_places.update(new_neighbours)
        self._counters.max_counter('max_neighbours_considered',
                                   len(neighbour_places))

        _DEBUG and logging.debug(
            f'Got event_ids: {event_ids} for {len(neighbour_places)} neighbors of {place_id}'
        )
        return list(event_ids)

    def is_event_active(self, event_id: str, min_date: str) -> bool:
        '''Returns true if all the dates in the event are less than min_date.'''
        event = self.get_event_by_id(event_id)
        if not event:
            return False
        event_start_date = event.get_event_start_date()
        event_end_date = event.get_event_end_date()
        if event_end_date and event_end_date < min_date:
            self._counters.add_counter('events_inactive_by_max_interval', 1)
            return False
        if _get_dates_duration(event_start_date,
                               event_end_date) > self._config.get(
                                   'max_event_duration_days', sys.maxsize):
            self._counters.add_counter('events_inactive_by_max_duration', 1)
            return False
        if len(event.get_places()) >= self._config.get('max_event_places',
                                                       sys.maxsize):
            self._counters.add_counter('events_inactive_by_max_places', 1)
            return False
        return True

    def get_active_event_ids(self, date: str = None) -> list:
        '''Returns a list of active event ids.
        An event with an end date within 'max_event_interval_days' days
        of the given date is considered active.
        '''
        active_ids = []
        if not self._event_by_id:
            return active_ids
        if not date:
            date = self._max_date
        if not date:
            return active_ids
        min_date = self._get_date_with_interval(date)
        inactive_ids = []
        for event_id in self._event_by_id.keys():
            if self.is_event_active(event_id, min_date):
                active_ids.append(event_id)
            else:
                inactive_ids.append(event_id)
        self.deactivate_old_events(inactive_ids, self._max_date)
        return active_ids

    def deactivate_old_events(self, event_ids: list, date: str) -> list:
        '''Removes any events that ended long time ago compared to date.
        The events are retained in _event_by_id but removed from _active_event_by_place index.
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
                    f'Deactivating event: {event_id} with end date older than {min_date}'
                )
                self.remove_event_from_place_index(event_id)
        return active_ids

    def remove_event_from_place_index(self, event_id: str):
        '''Remove the s2 cells for this event from the _active_event_by_place index.'''
        event = self.get_event_by_id(event_id)
        places = event.get_places().keys()
        _DEBUG and logging.debug(
            f'Removing event {event_id} active places: {places}')
        for place_id in places:
            if place_id in self._active_event_by_place:
                self._active_event_by_place.pop(place_id)
        self._counters.add_counter('events_deactivated', 1, event_id)
        self._counters.add_counter('events_places_deactivated', len(places),
                                   event_id)

    def add_place_data(self, place_id: int, date: str, pvs: dict) -> str:
        '''Returns the event id after adding place with PVs for a date.'''
        event_ids = self.get_events_for_place(place_id)
        self._event_props.update(set(pvs.keys()))

        # Retire old events that ended too long compared to given date.
        # Assumes data is added in increasing order of dates.
        event_ids = self.deactivate_old_events(event_ids, date)

        if not event_ids:
            # Add this as a new event.
            event = GeoEvent(event_id='',
                             place_id=place_id,
                             date=date,
                             pvs=pvs,
                             config=self._config)
            self.add_geo_event(event)
            event_id = event.event_id()
            _DEBUG and logging.debug(
                f'Created new event: {event_id} for {place_id}:{date}:{pvs}')
            return event_id

        # Merge all events that new region overlaps with into a root event with
        # the earliest date.
        sorted_ids = sorted(list(event_ids))
        _DEBUG and logging.debug(
            f'Merging events for cell: {place_id}: {sorted_ids}')
        # Get the event with the earliest date.
        root_event_id = sorted_ids[0]
        root_event = self.get_event_by_id(root_event_id)
        if not root_event:
            logging.fatal(f'Unable to find event for {root_event_id}')
        root_event.add_place_pvs(place_id, date, pvs)
        self._counters.add_counter('event_places_added', 1, root_event_id)
        for event_id in sorted_ids[1:]:
            event = self.get_event_by_id(event_id)
            root_event.merge_event(event)
        _DEBUG and logging.debug(
            f'Added {place_id}, {date}, {pvs} into event: {root_event_id}')
        self._counters.add_counter('event_mergers', 1)
        self._counters.add_counter('events_merged', len(sorted_ids))
        self._counters.max_counter('max_event_places',
                                   len(root_event.get_places()))
        self._max_date = max(self._max_date, date)
        return root_event_id

    def get_all_event_ids(self) -> set:
        '''Returns all root events ids.'''
        event_ids = set()
        for event_id in self._event_by_id.keys():
            event = self.get_event_by_id(event_id)
            event_ids.add(event.event_id())
        return event_ids

    def cache_event_place_property(self, event_ids: list = None):
        '''Batch lookup properties for places in events.'''
        if not self._config.get('dc_api_enabled', True):
            logging.info(f'Skipping lookup for place properties.')
            return
        _set_counter_stage(self._counters, 'prefetch_place_property_')
        if event_ids is None:
            event_ids = self.get_all_event_ids()
        logging.info(
            f'Prefetching place properties for {len(event_ids)} events')
        # Get all places to lookup.
        # Skip grid places whose lat/lng can be computed.
        lookup_places = set()
        lookup_names = set()
        for event_id in event_ids:
            event = self.get_event_by_id(event_id)
            place_ids = event.get_event_places()
            for placeid in place_ids:
                if (not utils.is_grid_id(placeid)) and (
                        not utils.is_ipcc_id(placeid)):
                    lookup_places.add(placeid)
                parent_place_ids = self._get_contained_for_place(placeid)
                lookup_names.update(parent_place_ids)

        self._counters.set_counter('total', len(lookup_places))
        # Batch lookup latitude and longitude on DC API
        lookup_place_ids = list(lookup_places)
        if lookup_place_ids:
            self.prefetch_placeid_property('latitude', lookup_place_ids)
            self.prefetch_placeid_property('longitude', lookup_place_ids)
            self.prefetch_placeid_property('containedInPlace', lookup_place_ids)
        self._counters.set_counter('processed', len(lookup_places))

        # Lookup names for all places and parents
        if self._config.get('lookup_place_names', True):
            contained_place_dict = self._place_property_cache.get(
                'containedInPlace', {})
            for place_id, contained_place_ids in contained_place_dict.items():
                if contained_place_ids:
                    lookup_names.update(contained_place_ids)
            self._counters.add_counter('total', len(lookup_places))
            self.prefetch_placeid_property('name', lookup_names)
            self.prefetch_placeid_property('typeOf', lookup_names)
            self._counters.set_counter('processed', len(lookup_names))
            logging.info(
                f'Cached properties for {len(self._place_property_cache.get("name", {}))} places'
            )
        # Save the cache
        self.save_place_cache_file()

    def prefetch_placeid_property(self, prop: str, place_ids: list = None):
        '''Lookup placeid properties and cache the result.'''
        logging.info(
            f'Lookup DC API property: {prop} for {len(place_ids)} places')
        cache_dict = self._place_property_cache.get(prop, {})
        lookup_places = []
        for place in place_ids:
            places = place.split(',')
            for placeid in places:
                placeid = utils.strip_namespace(placeid)
                if placeid not in cache_dict:
                    lookup_places.append(placeid)

        if lookup_places:
            start_time = time.perf_counter()
            cache_dict.update(
                dc_api_batched_wrapper(function=dc.get_property_values,
                                       dcids=lookup_places,
                                       args={
                                           'prop': prop,
                                       },
                                       config=self._config))
            end_time = time.perf_counter()
            self._counters.add_counter(f'dc_api_lookup_{prop}_count',
                                       len(lookup_places))
            self._counters.add_counter(f'dc_api_lookup_{prop}_time',
                                       end_time - start_time)
            self._place_property_cache[prop] = cache_dict
            self._place_cache_modified = True

    def save_place_cache_file(self):
        '''Cleanup and save and caches.'''
        if self._place_cache_modified:
            utils.file_write_py_dict(
                self._place_property_cache,
                self._config.get('place_property_cache_file', ''))
        self._place_cache_modified = False

    def get_place_property(self, placeid: str, prop: str) -> str:
        '''Returns the property for the place from the cache.'''
        placeid = utils.strip_namespace(placeid)
        cache_dict = self._place_property_cache.get(prop, {})
        value = cache_dict.get(placeid, None)
        if value:
            self._counters.add_counter(f'cache_place_property_{prop}_hits', 1)
        else:
            self._counters.add_counter(f'cache_place_property_{prop}_miss', 1)
        return value

    def set_place_property(self, placeid: str, prop: str, value: str) -> bool:
        '''Set the property for the place id.'''
        if prop is None or value is None:
            return
        value_added = False
        if prop not in self._place_property_cache:
            self._place_property_cache[prop] = dict()
        cache_dict = self._place_property_cache.get(prop, {})
        # Convert value to be added into a list
        if not isinstance(value, list):
            if not isinstance(value, str):
                value = str(value)
            value = [value]
        # Add value to existing property values for the place
        cache_values = cache_dict.get(placeid, None)
        if cache_values is None:
            cache_dict[placeid] = value
            value_added = True
        else:
            # Add any new values not in cache.
            new_values = set(cache_values)
            new_values.update(value)
            if len(new_values) != len(cache_values):
                cache_dict[placeid] = list(new_values)
                value_added = True
        if value_added:
            self._place_cache_modified = True
            self._counters.add_counter(f'place_cache_add_{prop}', 1)
        return value_added

    def get_event_polygon(self, event_id: str) -> Polygon:
        '''Returns the polygon for the events affected area.
        Computes the union of all grid type places for the event.'''
        event = self.get_event_by_id(event_id)
        if not event:
            return None
        event_polygon = Polygon()
        places = event.get_places().keys()
        for place in places:
            place_polygon = utils.place_to_polygon(place)
            if place_polygon:
                event_polygon = event_polygon.union(place_polygon)
        simplification = self._config.get('polygon_simplification_factor', None)
        if simplification:
            event_polygon = event_polygon.simplify(simplification)
        return event_polygon

    def get_event_output_properties(self, event_id: str) -> dict:
        '''Returns the output properties for an event.'''
        event = self.get_event_by_id(event_id)
        if not event:
            self._counters.add_counter('error-missing-event-for-id', 1,
                                       event_id)
            logging.fatal(f'Unable to get event for {event_id}')
            return None
        event_pvs = dict()
        event_pvs['dcid'] = event_id
        event_pvs['typeOf'] = self._config.get('event_type', 'FloodEvent')
        # Set event duration from dates across all places in the event.
        dates = event.get_event_dates()
        if dates:
            event_pvs['startDate'] = dates[0]
            event_pvs['endDate'] = dates[-1]
            duration_days = _get_dates_duration(event_pvs['startDate'],
                                                event_pvs['endDate'])
            event_pvs['observationPeriod'] = f'P{duration_days}D'
            event_pvs['DurationDays'] = duration_days
            self._counters.max_counter('max_output_events_dates', len(dates))
        # Set the start location from the place with the earliest date
        start_place_ids = event.get_event_places(
            {event_pvs.get('startDate', None)})
        if start_place_ids:
            # Set lat/lng for start location.
            # Compute for grid from dcid or lookup using the DC API
            placeid = start_place_ids[0]
            lat, lng = self._get_place_lat_lng(placeid)
            if lat is None or lng is None:
                # No location available. Use the placeid itself
                event_pvs['startLocation'] = utils.add_namespace(placeid)
                self._counters.add_counter('events_without_lat_lng', 1)
            else:
                # Got lat long for place. Cache it
                event_pvs['startLocation'] = f'[LatLong {lat:.5f} {lng:.5f}]'
        event_data = event.get_event_properties()
        allow_pvs = utils.dict_filter_values(
            event_data, self._config.get('output_events_filter_config', {}))
        if not allow_pvs:
            return None
        # Save area as a number without units
        area_sqkm = event_data.get('area', 0)
        if area_sqkm:
            event_pvs['AreaSqKm'] = area_sqkm
        # Transform values into quantity ranges
        format_config = self._config.get('property_config', {})
        per_date_config = self._config.get('property_config_per_date', {})
        if per_date_config:
            format_config.update(per_date_config)
        event_pvs.update(_format_property_values(event_data, format_config))
        # Generate polygon for the event
        polygon_prop = self._config.get('output_affected_place_polygon', '')
        if polygon_prop:
            event_polygon = self.get_event_polygon(event_id)
            if event_polygon:
                geo_json = mapping(event_polygon)
                if geo_json:
                    event_pvs[polygon_prop] = geo_json
                    self._counters.add_counter('output_events_with_polygon', 1)
        if not event_pvs.get('name', None):
            event_pvs['name'] = self._get_event_name(event_pvs)
        # Set the affectedPlace and containedInPlace for the event.
        self._set_event_places(event, event_pvs)
        return event_pvs

    def write_events_csv(self,
                         output_path: str,
                         event_ids: list = None,
                         output_ended_events: bool = False):
        '''Write the events into a csv file.'''
        output_csv = utils.file_get_name(output_path, 'events', '.csv')
        # Default output columns for events
        output_columns = [
            'dcid',
            'typeOf',
            'name',
            'startDate',
            'endDate',
            'observationPeriod',
            'DurationDays',
            'startLocation',
            'affectedPlace',
            'AffectedPlaceCount',
            #'containedInPlace',
            'ContainedInPlaceCount',
            'area',
            'AreaSqKm',
            'subEvents',
        ]
        # Output additional event specific properties from data source
        for prop in sorted(list(self._event_props)):
            if prop not in output_columns:
                output_columns.append(prop)
        # Add column for affected place polygon
        polygon_prop = self._config.get('output_affected_place_polygon', '')
        if polygon_prop:
            output_columns.append(polygon_prop)
        if event_ids is None:
            event_ids = self.get_all_event_ids()
        counter_stage = self._counters.get_prefix()
        # Prefetch properties for event places.
        self.cache_event_place_property(event_ids)
        _set_counter_stage(self._counters, utils.strip_namespace(counter_stage))
        num_output_events = 0
        # Generate a csv row for each event
        with open(output_csv, 'w') as csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=output_columns,
                                    escapechar='\\',
                                    extrasaction='ignore',
                                    quotechar='"',
                                    quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            self._counters.set_counter('total', len(event_ids))
            for event_id in event_ids:
                event_pvs = self.get_event_output_properties(event_id)
                if event_pvs:
                    writer.writerow(event_pvs)
                    self._counters.add_counter('output_events', 1)
                else:
                    self._counters.add_counter('output_events_filtered', 1)
                num_output_events += 1
                self._counters.add_counter('processed', 1)
        logging.info(
            f'Wrote {num_output_events} events into {output_csv} with columns: {output_columns}'
        )
        self.write_tmcf(utils.file_get_name(output_path, 'events', '.tmcf'),
                        output_columns)
        self._counters.print_counters()

    def write_tmcf(self,
                   output_file: str,
                   columns: list,
                   fixed_props: dict = None,
                   prefix: str = 'Events'):
        '''Generate tMCF for columns with valid schema.'''
        if not prefix:
            prefix = 'Events'
        with open(output_file, 'w') as tmcf_file:
            tmcf_file.write(f'Node: E:{prefix}->E0')
            output_prop = list()
            skipped_prop = list()
            # Add fixed property:values
            if fixed_props:
                for prop, value in fixed_props.items():
                    if prop not in columns:
                        tmcf_file.write(f'\n{prop}: C:{prefix}->{value}')
            # Add properties for output columns
            for prop in columns:
                if _is_valid_property(prop):
                    output_prop.append(prop)
                    tmcf_file.write(f'\n{prop}: C:{prefix}->{prop}')
                else:
                    skipped_prop.append(prop)
        logging.info(
            f'Wrote tMCF: {output_file} with properties:{output_prop}, skipped properties: {skipped_prop}'
        )

    def write_events_svobs(self,
                           output_path: str,
                           event_ids: list = None,
                           output_ended_events: bool = False,
                           event_props: list = None,
                           min_date: str = '',
                           max_date: str = ''):
        '''Write SVObs for all events into a CSV.'''
        output_csv = utils.file_get_name(output_path, 'svobs', '.csv')
        output_columns = ['dcid', 'observationDate']
        if not event_props:
            # No specific properties given. Generate SVObs for all properties.
            event_props = sorted(list(self._event_props))
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
            self._counters.set_counter('total', len(event_ids))
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
                # Generate observations for each date in event.
                num_output_dates = 0
                event_date_pvs = event.get_event_properties_by_dates()
                for date, date_pvs in event_date_pvs.items():
                    if not utils.dict_filter_values(
                            date_pvs, self._config.get('svobs_filter_config',
                                                       {})):
                        self._counters.add_counter('dropped_svobs_filter', 1,
                                                   event_id)
                        continue
                    if date_pvs:
                        num_output_dates += 1
                        self._counters.add_counter('output_events_svobs_rows',
                                                   1, event_id)
                        self._counters.add_counter('output_events_svobs',
                                                   len(date_pvs), event_id)
                        date_pvs['dcid'] = event_id
                        date_pvs['observationDate'] = date
                        writer.writerow(date_pvs)
                        self._counters.add_counter('processed', 1)
                    # Track min/max counters for properties
                    for prop, value in date_pvs.items():
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
        self.write_tmcf(utils.file_get_name(output_path, 'svobs',
                                            '.tmcf'), output_columns,
                        {'typeOf': 'dcid:StatVarObservation'}, 'SVObs')
        self._counters.print_counters()

    def write_active_events(self, filename: str):
        '''Save active events into a file.'''
        # Get a dict of all active events by id.
        active_events = {}
        active_ids = self.get_active_event_ids(self._max_date)
        for event_id in active_ids:
            event = self.get_event_by_id(event_id)
            if event:
                active_events[event_id] = event.get_places()

        # Save the active events into a file.
        utils.file_write_py_dict(active_events, filename)
        self._counters.set_counter('active_events', len(active_events))

    def read_active_events(self, filename: str):
        '''Load active events from a file.'''
        _set_counter_stage(self._counters, 'load_active_events')
        active_events = utils.file_load_py_dict(filename)

        logging.info(
            f'Processing {len(active_events)} active events of size: {sys.getsizeof(active_events)} from file: {filename}'
        )
        self._counters.set_counter('total', len(active_events))
        for event_id, event_dict in active_events.items():
            event = GeoEvent(event_id=event_id, config=self._config)
            for place_id, date_pvs in event_dict.items():
                self._counters.max_counter('max_active_events_place_dates',
                                           len(date_pvs), filename)
                for date in sorted(date_pvs.keys()):
                    pvs = date_pvs[date]
                    event.add_place_pvs(place_id, date, pvs)
                    self._counters.add_counter('active_event_place_dates_added',
                                               1, event_id)
            self.add_geo_event(event)
            self._counters.add_counter('processed', 1, filename)
            self._counters.add_counter('active_events_places_loaded',
                                       len(event_dict), filename)
            self._counters.max_counter('max_active_event_places',
                                       len(event_dict))
        logging.info(
            f'Loaded {len(active_events)} events from file: {filename}')

    def process_csv(self,
                    csv_files: list,
                    output_path: str,
                    input_events_file: str = None,
                    output_active_events_path: str = None,
                    output_active_events_state: str = None):
        '''Process CSV files with data for places into events.
         Places can be s2 cells or grids with lat/lng.
         '''
        if input_events_file:
            self.read_active_events(input_events_file)
        _set_counter_stage(self._counters, 'process_csv_')
        input_files = utils.file_get_matching(csv_files)
        for filename in input_files:
            self._counters.add_counter('total',
                                       utils.file_estimate_num_rows(filename))
        logging.info(
            f'Processing data from files: {input_files} with config: {self._config.get_configs()}'
        )
        for filename in input_files:
            logging.info(f'Processing csv data file: {filename}')
            with open(filename) as csvfile:
                reader = csv.DictReader(csvfile)
                if len(self._event_props) <= 1:
                    # No event properties from config. Add all input properties.
                    self._event_props.update(reader.fieldnames)
                logging.info(
                    f'Processing columns: {self._event_props} from {filename}')
                self._counters.add_counter('input_files', 1, filename)
                num_rows = 0
                for input_row in reader:
                    num_rows += 1
                    if num_rows > self._config.get('input_rows', sys.maxsize):
                        break
                    self._counters.add_counter(f'csv_rows-{filename}', 1)
                    self._counters.add_counter('processed', 1)
                    self.process_event_data(input_row)
                # Deactivate old events before moving to next CSV file.
                # Assumes event files are in increasing order by date.
                self.deactivate_old_events(self.get_active_event_ids(),
                                           self._max_date)
                logging.info(
                    f'Created {len(self._event_by_id)} events for {num_rows} rows from file: {filename}'
                )
        self.output_events(output_path, output_active_events_path,
                           output_active_events_state)
        self.save_place_cache_file()

    def process_event_data(self, data: dict) -> bool:
        '''Process an input event with a dictionary of properties.
        The event is added to existing events or a new event is created if it is valid.
        Args:
          data: dictionary of property:values for the event.
        '''
        # Collect property:values for the event to be added.
        data_pvs = {}
        row = _rename_dict_keys(data,
                                self._config.get('input_rename_columns', {}))
        place_column = self._config.get('place_column', 'observationAbout')
        place = utils.strip_namespace(row.get(place_column, ''))
        place_id = self.get_place_id_for_event(place)
        if not place_id:
            self._counters.add_counter('input_dropped_invalid_placeid', 1)
            return False
        data_pvs['affectedPlace'] = place
        date_column = self._config.get('date_column', 'observationDate')
        date = row.get(date_column, '')
        if not date:
            self._counters.add_counter('error_input_rows_missing_date', 1)
            logging.error(f'Missing date in row:{filename}:{num_rows}:{row}')
            return False
        if date < self._max_date:
            self._counters.add_counter('error_input_rows_date_out_of_order', 1)
            logging.error(f'Old date in row:{filename}:{num_rows}:{row}')
            return False
        prev_date = date
        for p in self._event_props:
            if p in row:
                data = utils.str_get_numeric_value(row[p])
                if data is not None:
                    data_pvs[p] = data
                else:
                    data_pvs[p] = row[p]
        # Compute area if required.
        if 'area' in self._event_props and 'area' not in data_pvs:
            area = utils.place_area(place_id)
            if area > 0:
                data_pvs['area'] = area
        # Check if row passes input filters.
        input_filter = self._config.get('input_filter_config', None)
        if not input_filter or utils.dict_filter_values(data_pvs, input_filter):
            self.add_place_data(place_id, date, data_pvs)
        else:
            self._counters.add_counter('input_dropped_by_filter', 1)
            return False
        self._counters.add_counter('events_added', 1)
        return True

    def get_place_id_for_event(self, place_id: str) -> str:
        '''Returns the place_id for the event data.'''
        if not utils.is_grid_id(place_id) and self._config.get(
                'convert_place_to_grid', False):
            # Converting a non-grid place to a grid_1 place.
            # Multiple places mapping to same grid will be
            # aggregated using 'property_config_per_date'.
            lat, lng = self._get_place_lat_lng(place_id)
            if lat is not None and lng is not None:
                # Got a location. Convert it to a grid.
                grid_id = utils.grid_id_from_lat_lng(1, int(lat), int(lng))
                place_id = grid_id
                self._counters.add_counter(f'place_converted_to_grid_1', 1)
            else:
                self._counters.add_counter(f'place_without_lat_lng', 1)
        if utils.is_s2_cell_id(place_id):
            # Place is an s2 cell. Convert to the right s2 level.
            s2_cell = utils.s2_cell_from_dcid(place_id)
            s2_cell_level = s2_cell.level()
            output_s2_level = self._config.get('s2_level', s2_cell_level)
            if s2_cell_level > output_s2_level:
                # Incoming S2 cell is too small.
                # Convert it to a higher level.
                # Data from mutiple input cells mapping to same
                # output cell will be aggregated.
                place_id = utils.s2_cell_to_dcid(
                    s2_cell.parent(output_s2_level))
                self._counters.add_counter(
                    f's2_{s2_cell_level}_converted_to_{output_s2_level}', 1)
        return utils.strip_namespace(place_id)

    def output_events(self,
                      output_path: str,
                      output_active_events_path: str = None,
                      output_active_events_state: str = None):
        # Output all ended events
        output_ended_events = False
        if output_active_events_path:
            # No separate output path for active events.
            # Output all events, not just ended ones.
            output_ended_events = True
        if self._config.get('output_events', True):
            _set_counter_stage(self._counters, 'emit_events_csv_')
            self.write_events_csv(output_path=output_path,
                                  output_ended_events=output_ended_events)
        if self._config.get('output_svobs', False):
            _set_counter_stage(self._counters, 'emit_events_svobs_')
            self.write_events_svobs(output_path=output_path,
                                    output_ended_events=output_ended_events)
        # Output active events into a separate set of files.
        active_event_ids = self.get_active_event_ids(self._max_date)
        self._counters.set_counter('active_events', len(active_event_ids))
        if output_active_events_path:
            logging.info(
                f'Emitting {len(active_event_ids)} active events into: {output_active_events_path}'
            )
            if self._config.get('output_active_events', True):
                _set_counter_stage(self._counters, 'emit_active_events_csv_')
                self.write_events_csv(output_path=output_active_events_path,
                                      event_ids=active_event_ids,
                                      output_ended_events=False)
            if self._config.get('output_active_svobs', False):
                _set_counter_stage(self._counters, 'emit_active_events_svobs_')
                self.write_events_svobs(output_path=output_active_events_path,
                                        event_ids=active_event_ids,
                                        output_ended_events=False)
        if output_active_events_state:
            _set_counter_stage(self._counters, 'emit_active_events_data_')
            self.write_active_events(output_active_events_state)

    def _get_date_with_interval(self, date: str) -> str:
        '''Returns the date with the interval 'max_event_interval_days' applied.'''
        if not date:
            return date
        interval_days = timedelta(
            days=self._config.get('max_event_interval_days', 30))
        min_date = date
        try:
            min_date = (parser.parse(date) - interval_days).isoformat()
        except parser._parser.ParserError:
            logging.error(f'Unable to parse date: "{date}"')
            self._counters.add_counter('error_input_rows_invalid_date', 1)
            min_date = date
        return min_date

    def _get_contained_for_place(self, place_id: int) -> list:
        '''Returns a list of containdInPlace dcids for a place.'''
        new_places = set({place_id})
        parent_places = set()
        # Lookup parent places for all parents.
        while len(new_places) > 0:
            placeid = new_places.pop()
            new_parents = self.get_place_property(placeid, 'containedInPlace')
            if not new_parents:
                # No containedInPlace for place.
                # Lookup place by lat/lng.
                if utils.is_ipcc_id(placeid):
                    deg, lat, lng, suffix = utils.grid_id_to_deg_lat_lng(
                        placeid)
                    if suffix:
                        suffix = suffix.replace('_', '')
                        new_parents = [f'country/{suffix}']
                elif placeid in self._latlng_to_place_cache:
                    self._counters.add_counter('latlng_place_cache_hits', 1)
                    new_parents = self._latlng_to_place_cache[placeid].split(
                        ',')
                elif self._config.get('lookup_contained_for_place', False):
                    lat, lng = utils.placeid_to_lat_lng(
                        placeid, self._config.get('dc_api_enabled', True))
                    geo_ids = self._ll2p.resolve(lat, lng)
                    self._latlng_to_place_cache[placeid] = geo_ids
                    self._counters.add_counter('latlng_place_lookups', 1)
            if new_parents:
                # Get a list of place ids splitting comma separated strings.
                new_parents = ','.join(new_parents).split(',')
                for new_place in new_parents:
                    if new_place not in parent_places:
                        new_places.add(new_place)
                        parent_places.add(new_place)
        parent_places.add('Earth')
        contained_places = list(parent_places)
        self.set_place_property(place_id, 'containedInPlace', contained_places)
        return contained_places

    def _get_event_name(self, event_pvs: dict, locations: list = None) -> str:
        '''Get the name for the event.'''
        typeof = event_pvs.get('typeOf',
                               self._config.get('event_type', 'FloodEvent'))
        start_date = event_pvs.get('startDate')
        # Get a named location for the event
        start_location = event_pvs.get('startLocation')
        if not locations:
            locations = event_pvs.get('affectedPlace', '').split(',')
        location_name = ''
        for placeid in locations:
            placeid = utils.strip_namespace(placeid)
            if not utils.is_ipcc_id(placeid) and not utils.is_grid_id(placeid):
                location_name = self.get_place_property(placeid, 'name')
                if location_name:
                    #    place_type = self.get_place_property(placeid, 'typeOf')
                    #    if place_type:
                    #        location_name = f'{place_type[0]} {location_name[0]}'
                    location_name = f'{location_name[0]}'
                    break
        if not location_name:
            # Use the lat lng from start place.
            lat_lng = event_pvs.get('startLocation')
            if lat_lng:
                location_name = lat_lng.replace('[', '')
                location_name = location_name.replace(' ', '(', 1)
                location_name = location_name.replace(' ', ':')
                location_name = location_name.replace(']', ')')
        event_name = typeof
        if location_name:
            event_name += f' at {location_name}'
        if start_date:
            event_name += f' on {start_date}'
        return event_name

    def _set_event_places(self, event: GeoEvent, data: dict):
        '''Set the event place properties like affectedPlace and containedInPlace.'''
        # Set the affectedPlaces and containedInPlace for the event.
        affected_places = set()
        contained_places = set()
        place_ids = event.get_event_places()
        if place_ids:
            places = place_ids[:self._config.get('maximum_affected_places', 1000
                                                )]
            # Get the parent containment places for each affected place
            for place_id in places:
                affected_places.add(utils.add_namespace(place_id))
                parent_place_ids = self._get_contained_for_place(place_id)
                if parent_place_ids:
                    for geoid in parent_place_ids:
                        contained_places.add(utils.add_namespace(geoid))
                    self._counters.add_counter('places_with_parents', 1)
                    self._counters.add_counter('event_parent_places',
                                               len(parent_place_ids))
                else:
                    self._counters.add_counter('places_without_parents', 1)
            if affected_places:
                contained_places.update(affected_places)
                # TODO: Create a property for containedInPlaces for Events
                # Until then affectedPlace is used for place aggregation.
                # data['affectedPlace'] = ','.join(affected_places)
                data['affectedPlace'] = ','.join(contained_places)
                data['AffectedPlaceCount'] = len(affected_places)
                data['ContainedInPlaceCount'] = len(contained_places)
        self._counters.max_counter('max_output_events_places', len(place_ids))

    def _get_place_lat_lng(self, placeid: str) -> (float, float):
        placeid = utils.strip_namespace(placeid)
        lat, lng = utils.place_id_to_lat_lng(placeid, dc_api_lookup=False)
        if lat is not None and lng is not None:
            return (lat, lng)
        lat = self.get_place_property(placeid, 'latitude')
        lng = self.get_place_property(placeid, 'longitude')
        if lat and lng:
            return (utils.str_get_numeric_value(lat),
                    utils.str_get_numeric_value(lng))
        # Lat/Lng not in cache.
        # Compute for grid from dcid or lookup using the DC API
        lat, lng = utils.place_id_to_lat_lng(
            placeid,
            self._config.get('lookup_place_lat_lng',
                             self._config.get('dc_api_enabled', True)))
        if lat is not None and lng is not None:
            self.set_place_property(placeid, 'latitude', lat)
            self.set_place_property(placeid, 'longitude', lng)
        return (lat, lng)


def _rename_dict_keys(pvs: dict, rename_keys: dict) -> dict:
    '''Returns a dict with keys renamed.'''
    if not rename_keys:
        return pvs
    renamed_dict = {}
    for prop, value in pvs.items():
        renamed_prop = rename_keys.get(prop, '')
        if renamed_prop:
            renamed_dict[renamed_prop] = value
        else:
            renamed_dict[prop] = value
    return renamed_dict


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


def _reset_counter_stage(counters: Counters, stage_name: str):
    counters.reset_process_stage(stage_name)


def _get_dates_duration(start_date: str, end_date: str) -> int:
    return (parser.parse(end_date) - parser.parse(start_date)).days + 1


def _get_place_neighbors_ids(place_id: str) -> list:
    '''Return the neighbour ids for a place.'''
    if utils.is_s2_cell_id(place_id):
        return utils.s2_cell_get_neighbor_ids(place_id)
    if utils.is_grid_id(place_id) or utils.is_ipcc_id(place_id):
        return utils.grid_get_neighbor_ids(place_id)
    return []


def _is_valid_property(prop: str) -> bool:
    '''Returns true if prop is a valid schema property.'''
    if not prop or not prop[0].islower():
        return False
    if '_' in prop:
        return False
    return True


def _set_counter_stage(counters: Counters, name: str):
    '''Set the counter prefix to the stage.'''
    counter_prefix = counters.get_prefix()
    counter_prefix = counter_prefix[:counter_prefix.find(':')]
    stage_count = 0
    if counter_prefix:
        stage_count = int(counter_prefix)
    stage_count += 1
    counters.set_prefix(f'{stage_count}:{name}')


def process(csv_files: list,
            output_path: str,
            input_events_file: str = None,
            output_active_events_path: str = None,
            output_active_events_state: str = None,
            config: ConfigMap = None):
    counters = Counters()
    if config is None:
        config = ConfigMap(config_dict=_DEFAULT_CONFIG)
    events_processor = GeoEventsProcessor(config, counters)
    events_processor.process_csv(csv_files, output_path, input_events_file,
                                 output_active_events_path,
                                 output_active_events_state)


def main(_):
    _DEBUG = _FLAGS.debug
    if _DEBUG:
        logging.set_verbosity(2)
    #if _FLAGS.pprof_port > 0:
    # Enable pprof server.
    # To see pprof features, visit http://localhost:8081/debug/pprof
    # To collect a trace, run:
    # curl 'http://localhost:8081/debug/pprof/profile?seconds=30' -o py-profile
    # To generate the profile chart, run: pprof -pdf py-profile
    #    start_pprof_server(port=_FLAGS.pprof_port)
    config = ConfigMap(config_dict=_DEFAULT_CONFIG,
                       filename=_FLAGS.config,
                       config_string=_FLAGS.config_string)
    if _FLAGS.place_cache_file:
        config.set_config('place_cache_file', _FLAGS.place_cache_file)
    config.set_config('input_rows', _FLAGS.input_rows)
    config.set_config('debug', _FLAGS.debug)
    process(_FLAGS.input_csv, _FLAGS.output_path, _FLAGS.input_events,
            _FLAGS.output_active_path, _FLAGS.output_active_events_state,
            config)


if __name__ == '__main__':
    app.run(main)
