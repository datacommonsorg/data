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
import json
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
flags.DEFINE_integer('pprof_port', 8081, 'HTTP port for pprof server.')

_FLAGS = flags.FLAGS

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), 'util'))

import common_flags
import file_util
import statvar_dcid_generator
import utils

from aggregation_util import aggregate_dict
from counters import Counters
from latlng_recon_geojson import LatLng2Places
from config_map import ConfigMap
from dc_api_wrapper import dc_api_batched_wrapper

# List of place types in increasing order of preference for name.
# This is used to pick the name of the place from the list of affectedPlaces
# for an event for the place type with the highest index.
_PLACE_TYPE_ORDER = [
    'Place',
    'OceanicBasin',
    'Continent',
    'Country',
    'CensusRegion',
    'CensusDivision',
    'State',
    'AdministrativeArea1',
    'County',
    'AdministrativeArea2',
    'CensusCountyDivision',
    'EurostatNUTS1',
    'EurostatNUTS2',
    'CongressionalDistrict',
    'UDISEDistrict',
    'CensusCoreBasedStatisticalArea',
    'EurostatNUTS3',
    'SuperfundSite',
    'Glacier',
    'AdministrativeArea3',
    'AdministrativeArea4',
    'PublicUtility',
    'CollegeOrUniversity',
    'EpaParentCompany',
    'UDISEBlock',
    'AdministrativeArea5',
    'EpaReportingFacility',
    'SchoolDistrict',
    'CensusZipCodeTabulationArea',
    'PrivateSchool',
    'CensusTract',
    'City',
    'AirQualitySite',
    'PublicSchool',
    'Neighborhood',
    'CensusBlockGroup',
    'AdministrativeArea',
    'Village',
]

_PLACE_TYPE_RANK = {
    _PLACE_TYPE_ORDER[index]: index for index in range(len(_PLACE_TYPE_ORDER))
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
        self._is_valid = True

        # Set input values
        if not config:
            self._config = ConfigMap()
        if event_id:
            self.set_event_id(event_id)
        if place_id and date and pvs:
            self.add_place_pvs(place_id, date, pvs)

    def __str__(self):
        '''Returns a string representation of the object.'''
        return f'GeoEvent:{self._event_id}, Places:{self._places}'

    def __repr__(self):
        '''Returns a string representation of the object.'''
        return f'GeoEvent(\'{self._event_id}\': {self._places})'

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
        aggregate_dict(
            pvs, place_date_pvs,
            self._config.get('property_config_per_date',
                             self._config.get('property_config', {})))
        logging.level_debug() and logging.debug(
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
        if self == place_event:
            # Event is already merged.
            return
        if place_event.get_root_event() != place_event:
            logging.fatal(
                f'Cannot merge non-root event {place_event._event_id} into {self._event_id}'
            )
        # Merge data from all places into current event.
        for place_id, date_pvs in place_event.get_places().items():
            for date, pvs in date_pvs.items():
                self.add_place_pvs(place_id, date, pvs)
        # Set current event as parent for merged event
        place_event._merged_into_event = self
        logging.level_debug() and logging.debug(
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
                place_ids.update(_get_list(pvs.get('affectedPlace', '')))
        return sorted(list(place_ids))

    def get_event_properties(self, dates: set = {}) -> dict:
        '''Returns the properties aggregated across all places for the dates.'''
        pvs = dict()
        for place_id, date_pvs in self.get_places().items():
            per_place_pvs = {}
            for date, date_pvs in date_pvs.items():
                if not dates or date in dates:
                    aggregate_dict(
                        date_pvs, per_place_pvs,
                        self._config.get(
                            'property_config_across_dates',
                            self._config.get('property_config', {})))
            aggregate_dict(
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
                aggregate_dict(
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
        self._latlng_to_place_cache = file_util.file_load_csv_dict(
            filename=self._config.get('place_cache_file'),
            key_column=self._config.get('place_cache_key'),
            value_column=self._config.get('place_cache_value'),
            config=self._config.get('place_cache_config', {}))
        # dictionary from placeid to tuple { <placeid>: (lat, lng) }
        self._place_property_cache = file_util.file_load_py_dict(
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
        if self._config.get('debug', False):
            logging.set_verbosity(2)
        # dictionary of deleted events by id.
        # Events are not fully deleted to preserve any references.
        self._deleted_events = {}

    def get_events(self):
        '''Returns dictionary of all events by id.'''
        return self._event_by_id

    def add_geo_event(self, geo_event: GeoEvent):
        '''Add a geo event to the dict.'''
        self._event_by_id[geo_event.event_id()] = geo_event
        self.add_event_to_place_index(geo_event)
        self._counters.add_counter('geo_events_added', 1)
        logging.level_debug() and logging.debug(
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

        logging.level_debug() and logging.debug(
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
                logging.level_debug() and logging.debug(
                    f'Deactivating event: {event_id} with end date older than {min_date}'
                )
                event = self.get_event_by_id(event_id)
                if event:
                    places = event.get_places()
                    self.remove_event_from_place_index(event_id)
                    self._counters.add_counter('events_deactivated', 1,
                                               event_id)
                    self._counters.add_counter('events_places_deactivated',
                                               len(places), event_id)
        return active_ids

    def add_event_to_place_index(self, event: GeoEvent):
        '''Add places for an event into the lace index.'''
        if not event:
            return
        event_id = event.event_id()
        places = event.get_places().keys()
        logging.level_debug() and logging.debug(
            f'Adding event {event_id} to place index for: {places}')
        for place_id in places:
            self._active_event_by_place[place_id] = event

    def remove_event_from_place_index(self, event_id: str):
        '''Remove the s2 cells for this event from the _active_event_by_place index.'''
        event = self.get_event_by_id(event_id)
        if not event:
            return
        places = event.get_places().keys()
        logging.level_debug() and logging.debug(
            f'Removing event {event_id} active places: {places}')
        for place_id in places:
            place_event = self._active_event_by_place.get(place_id, None)
            if place_event and place_event.event_id() == event_id:
                self._active_event_by_place.pop(place_id)

    def merge_events(self, event_ids: list) -> GeoEvent:
        '''Returns a merged event combining all event_ids.

        This is called with a list of events_ids that have places that
        have started to overlap or have expanded to come close enough to each other
        with addition of new places to some of these events.
        They are merged into a single large event.
        The 'root_event' is the event id into whcih others events are merged.
        The event with the alphabetically sorted first event id,
        which would be the earliest since the start date is the event id prefix,
        is used as the root and others events are merged into it.

        Args:
          event_ids: list of events ids to be merged into a single event.
            The event with the lowest event_id is picked as the root
            and other events are merged into it.
            The places from all other events are added to the root event.
            References to the merged event in place map is also removed.
        Returns:
          the merged event.
          '''
        # Merge all events with into a root event with the earliest date.
        sorted_ids = sorted(list(event_ids))
        logging.level_debug() and logging.debug(f'Merging events: {sorted_ids}')
        if not sorted_ids:
            return None
        # Get the event with the earliest date.
        root_event_id = sorted_ids[0]
        root_event = self.get_event_by_id(root_event_id)
        if not root_event:
            logging.debug(f'Unable to find event for {root_event_id}')
            return None
        for event_id in sorted_ids[1:]:
            event = self.get_event_by_id(event_id)
            if event and event != root_event:
                # Merge the data from event into root and
                # remove references to the event.
                root_event.merge_event(event)
                self.delete_event(event_id)
        self.add_event_to_place_index(root_event)
        self._counters.add_counter('events_merged', len(sorted_ids))
        return root_event

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
            logging.level_debug() and logging.debug(
                f'Created new event: {event_id} for {place_id}:{date}:{pvs}')
            return event_id

        # Merge all events that new region overlaps with into a root event with
        # the earliest date.
        root_event = self.merge_events(event_ids)
        if not root_event:
            logging.debug(f'Unable to find event for {root_event_id}')
            return None
        root_event_id = root_event.event_id()
        root_event.add_place_pvs(place_id, date, pvs)
        self._counters.add_counter('event_places_added', 1, root_event_id)
        logging.level_debug() and logging.debug(
            f'Added {place_id}, {date}, {pvs} into event: {root_event_id}')
        self._counters.add_counter('event_mergers', 1)
        self._counters.max_counter('max_event_places',
                                   len(root_event.get_places()))
        self._max_date = max(self._max_date, date)
        return root_event_id

    def get_all_event_ids(self) -> set:
        '''Returns all root events ids.'''
        event_ids = set()
        for event_id in self._event_by_id.keys():
            event = self.get_event_by_id(event_id)
            if event:
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
            if not event:
                continue
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
                    lookup_names.update(_get_list(contained_place_ids))
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
            places = _get_list(place)
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
            file_util.file_write_py_dict(
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

    def get_place_property_list(self, placeid: str, prop: str) -> list:
        '''Returns the property values for the place as a list.'''
        return _get_list(self.get_place_property(placeid, prop))

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
        cache_values = _get_list(cache_dict.get(placeid, None))
        if cache_values is None:
            cache_dict[placeid] = value
            value_added = True
        else:
            # Add any new values not in cache.
            new_values = set(cache_values)
            new_values.update(_get_list(value))
            if len(new_values) != len(cache_values):
                cache_dict[placeid] = ','.join(new_values)
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
            logging.debug(f'Unable to get event for {event_id}')
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
            event_pvs['numberOfDays'] = len(dates)
            event_pvs['observationDate'] = ','.join(dates)
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
        # Save area as a number without units
        area_sqkm = event_data.get('area', 0)
        if area_sqkm:
            event_pvs['AreaSqKm'] = round(area_sqkm, 5)
        # Transform values into quantity ranges
        format_config = self._config.get('property_config', {})
        per_date_config = self._config.get('property_config_per_date', {})
        if per_date_config:
            format_config.update(per_date_config)
        event_pvs.update(_format_property_values(event_data, format_config))
        allow_pvs = utils.dict_filter_values(
            event_pvs, self._config.get('output_events_filter_config', {}))
        if not allow_pvs:
            return None
        # Generate polygon for the event
        polygon_prop = self._config.get('output_affected_place_polygon',
                                        'geoJsonCoordinates')
        if polygon_prop:
            event_polygon = self.get_event_polygon(event_id)
            if event_polygon:
                geo_json = mapping(event_polygon)
                if geo_json:
                    # TODO: remove config after confirming json format
                    if self._config.get('output_geojson_string', False):
                        event_pvs[polygon_prop] = str(geo_json)
                    else:
                        event_pvs[polygon_prop] = json.dumps(
                            json.dumps(geo_json))
                    self._counters.add_counter('output_events_with_polygon', 1)
        # Set the affectedPlace and containedInPlace for the event.
        self._set_event_places(event, event_pvs)
        if not event_pvs.get('name', None):
            event_pvs['name'] = self._get_event_name(event_pvs)
        return event_pvs

    def delete_event(self, event_id):
        '''Removes the event from list of events.'''
        event = self.get_event_by_id(event_id)
        if not event:
            return
        self.remove_event_from_place_index(event_id)
        if event_id in self._event_by_id:
            self._event_by_id.pop(event_id)
        self._deleted_events[event_id] = event
        self._counters.add_counter('events-deleted', 1)

    def get_place_date_output_properties(self, event_ids: list,
                                         event_props: list) -> dict:
        '''Returns a dict event properties {(place, date): {'area': NN},... }

        Args:
          event_ids: list of event ids to be used.
          event_props: List of event properties to add per place,date.
            Example: ['area', 'count']

        Returns:
          dictionary keyed by string '<place-dcid>,YYYY-MM-DD' with
            event property values, such as { 'area': 100 } aggregated
            by place and date
        '''
        # default aggregation settings for event properties across places for a date.
        property_config_per_date = dict(
            _DEFAULT_CONFIG['property_config_per_date'])
        property_config_per_date.update(
            self._config.get('property_config_per_date', {}))

        # Collect data for each event's (place, date)
        # as a dict: {(place, date): {'area': NN},... }
        place_date_pvs = dict()
        _set_counter_stage(self._counters, 'collect_place_date_svobs_')
        self._counters.set_counter('total', len(event_ids))
        for event_id in event_ids:
            self._counters.add_counter('processed', 1)
            event = self.get_event_by_id(event_id)
            if not event:
                self._counters.add_counter(
                    'error_place_svobs_missing_event_for_id', 1, event_id)
                logging.debug(f'Unable to get event for {event_id}')
                continue

            # Process all places with property:values per date for the event.
            for placeid, date_pvs in event.get_places().items():
                for date, pvs in date_pvs.items():
                    # Collect all property:values for a given place and date.
                    key = f'{placeid},{date}'
                    date_pvs = {}
                    if 'count' in event_props:
                        # Collect unique event ids to generate counts
                        date_pvs['EventId'] = set(
                            {utils.strip_namespace(event_id)})
                    for p, v in pvs.items():
                        if p in event_props:
                            date_pvs[p] = v
                    if key not in place_date_pvs:
                        place_date_pvs[key] = dict(date_pvs)
                    else:
                        aggregate_dict(date_pvs, place_date_pvs[key],
                                       property_config_per_date)
        logging.info(
            f'Generated {len(place_date_pvs)} svobs for event places and dates')
        return place_date_pvs

    def aggregate_by_time_period(self, place_date_pvs: dict,
                                 date_formats: list):
        '''Aggregates the properties across dates for each place.

        Args:
          place_date_pvs: dictionary of property:values keyed by '<dcid>,date>'
          date_formats: list of date formats to aggregate by, such as,
            ['YYYY', 'YYYY-MM' ]
        Returns:
          dictionary of properties keyed by 'place id,date'.
        '''
        if not date_formats:
            # No aggregation by time period.
            return
        # Aggregation settings for event properties across dates for a place.
        property_config_across_dates = {
            'aggregate': 'max',
            'area': {
                'aggregate': 'max'
            },
            'EventId': {
                'aggregate': 'set'
            }
        }
        property_config_across_dates.update(
            self._config.get('property_config_across_dates', {}))

        _set_counter_stage(self._counters, 'aggregate_by_date_')
        self._counters.set_counter('total', len(place_date_pvs))
        num_svobs = 0
        for place_date in list(place_date_pvs.keys()):
            self._counters.add_counter('processed', 1)
            pvs = place_date_pvs[place_date]
            placeid, date = place_date.split(',', 1)
            for date_format in date_formats:
                date_str = _get_date_by_format(date, date_format)
                if date_str and date_str != date:
                    key = f'{placeid},{date_str}'
                    if key == place_date:
                        continue
                    if key not in place_date_pvs:
                        place_date_pvs[key] = dict(pvs)
                        num_svobs += 1
                    else:
                        aggregate_dict(pvs, place_date_pvs[key],
                                       property_config_across_dates)
        logging.info(
            f'Generated {num_svobs} SVObs for time periods: {date_formats}')

    def aggregate_by_contained_in_place(self, place_date_pvs: dict):
        '''Aggregate dictionary by containedInPlace parent of each place.
        Dictionary is of the form { '<place>,<date>': { 'area': NN' } }
        The property:values for a place,date are aggregated into
        each of it's parent places for the same set of dates.
        '''
        _set_counter_stage(self._counters, 'aggregate_by_place_')
        self._counters.set_counter('total', len(place_date_pvs))
        num_parents = 0
        for place_date in list(place_date_pvs.keys()):
            self._counters.add_counter('processed', 1)
            pvs = place_date_pvs[place_date]
            placeid, date = place_date.split(',', 1)
            parent_places = self.get_place_property_list(
                placeid, 'containedInPlace')
            if not parent_places:
                self._counters.add_counter('aggr-no-parent-places', 1)
                continue
            parents = set(_get_list(parent_places))
            if placeid in parents:
                parents.remove(placeid)
            # Add an entry for each parent place
            for parent_place in parents:
                if not parent_place:
                    continue
                key = f'{parent_place},{date}'
                if key == place_date:
                    continue
                if key not in place_date_pvs:
                    place_date_pvs[key] = dict(pvs)
                    num_parents += 1
                else:
                    aggregate_dict(
                        pvs, place_date_pvs[key],
                        self._config.get('property_config_per_date',
                                         {'aggregate': 'sum'}))
        logging.info(f'Generated {num_parents} SVObs for parent places,dates')

    def write_events_csv(self,
                         output_path: str,
                         event_ids: list = None,
                         output_ended_events: bool = False) -> str:
        '''Write the events into a csv file.'''
        output_csv = file_util.file_get_name(output_path, 'events', '.csv')
        # Default output columns for events
        output_columns = [
            'dcid',
            'typeOf',
            'name',
            'startDate',
            'endDate',
            'observationPeriod',
            'DurationDays',
            'numberOfDays',
            'startLocation',
            'affectedPlace',
            'AffectedPlaceCount',
            #'containedInPlace',
            'area',
            'AreaSqKm',
        ]
        # Output additional event specific properties from data source
        for prop in sorted(list(self._event_props)):
            if prop not in output_columns:
                output_columns.append(prop)
        # Add column for affected place polygon
        polygon_prop = self._config.get('output_affected_place_polygon',
                                        'geoJsonCoordinates')
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
        with file_util.FileIO(output_csv, 'w') as csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=output_columns,
                                    delimiter=self._config.get(
                                        'output_delimiter', ','),
                                    escapechar='\\',
                                    extrasaction='ignore',
                                    quotechar='"',
                                    quoting=csv.QUOTE_NONNUMERIC,
                                    doublequote=False)
            writer.writeheader()
            self._counters.set_counter('total', len(event_ids))
            for event_id in event_ids:
                event_pvs = self.get_event_output_properties(event_id)
                if event_pvs:
                    writer.writerow(_format_property_values(event_pvs))
                    self._counters.add_counter('output_events', 1)
                else:
                    self.delete_event(event_id)
                    self._counters.add_counter('output_events_filtered', 1)
                num_output_events += 1
                self._counters.add_counter('processed', 1)
        logging.info(
            f'Wrote {num_output_events} events into {output_csv} with columns: {output_columns}'
        )
        self.write_tmcf(file_util.file_get_name(output_path, 'events', '.tmcf'),
                        output_columns)
        self._counters.print_counters()
        return output_csv

    def write_tmcf(self,
                   output_file: str,
                   columns: list,
                   fixed_props: dict = None,
                   prefix: str = 'Events') -> str:
        '''Generate tMCF for columns with valid schema.'''
        if not prefix:
            prefix = 'Events'
        with file_util.FileIO(output_file, 'w') as tmcf_file:
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
        return output_file

    def write_events_svobs(self,
                           output_path: str,
                           event_ids: list = None,
                           output_ended_events: bool = False,
                           event_props: list = None) -> list:
        '''Write SVObs for all events into a CSV.'''
        output_files = []
        output_csv = file_util.file_get_name(output_path, 'svobs', '.csv')
        output_columns = ['dcid', 'observationDate']
        if not event_props:
            # No specific properties given. Generate SVObs for all properties.
            event_props = sorted(list(self._event_props))
        for prop in event_props:
            if prop not in output_columns:
                output_columns.append(prop)
        if not event_ids:
            event_ids = self.get_all_event_ids()
        with file_util.FileIO(output_csv, 'w') as csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=output_columns,
                                    delimiter=self._config.get(
                                        'output_delimiter', ','),
                                    escapechar='\\',
                                    extrasaction='ignore',
                                    quotechar='"',
                                    quoting=csv.QUOTE_NONNUMERIC,
                                    doublequote=False)
            writer.writeheader()
            num_output_events = 0
            self._counters.set_counter('total', len(event_ids))
            for event_id in event_ids:
                event = self.get_event_by_id(event_id)
                if not event:
                    self._counters.add_counter('error_missing_event_for_id', 1,
                                               event_id)
                    logging.debug(f'Unable to get event for {event_id}')
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
                        writer.writerow(
                            _format_property_values(date_pvs, digits=3))
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
        output_files.append(output_csv)
        logging.info(
            f'Wrote {num_output_events} events into {output_csv} with columns: {output_columns}'
        )
        output_tmcf = self.write_tmcf(
            file_util.file_get_name(output_path, 'svobs', '.tmcf'),
            output_columns, {'typeOf': 'dcid:StatVarObservation'}, 'SVObs')
        output_files.append(output_tmcf)
        self._counters.print_counters()
        return output_files

    def write_active_events(self, filename: str) -> str:
        '''Save active events into a file.'''
        # Get a dict of all active events by id.
        active_events = {}
        active_ids = self.get_active_event_ids(self._max_date)
        for event_id in active_ids:
            event = self.get_event_by_id(event_id)
            if event:
                active_events[event_id] = event.get_places()

        # Save the active events into a file.
        file_util.file_write_py_dict(active_events, filename)
        self._counters.set_counter('active_events', len(active_events))
        return filename

    def read_active_events(self, filename: str):
        '''Load active events from a file.'''
        _set_counter_stage(self._counters, 'load_active_events_')
        active_events = file_util.file_load_py_dict(filename)

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

    def write_place_svobs_csv(self, place_date_pvs: dict, event_props: list,
                              output_path: str) -> str:
        '''Returns the filename into which the svobs_pvs dict is written as CSV.'''
        output_columns = [
            'observationAbout', 'observationDate', 'observationPeriod'
        ]
        output_columns.extend(event_props)
        output_csv = file_util.file_get_name(output_path, 'place_svobs', '.csv')
        logging.info(
            f'Writing {len(place_date_pvs)} place svobs with columns {output_columns} into {output_csv}'
        )
        with file_util.FileIO(output_csv, 'w') as csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=output_columns,
                                    delimiter=self._config.get(
                                        'output_delimiter', ','),
                                    escapechar='\\',
                                    extrasaction='ignore',
                                    quotechar='"',
                                    quoting=csv.QUOTE_NONNUMERIC,
                                    doublequote=False)
            writer.writeheader()

            _set_counter_stage(self._counters, 'write_place_svobs_')
            self._counters.set_counter('total', len(place_date_pvs))
            for place_date, pvs in place_date_pvs.items():
                self._counters.add_counter('processed', 1)
                placeid, date = place_date.split(',', 1)
                row_dict = {
                    'observationAbout': placeid,
                    'observationDate': date
                }
                # Get count of unique event ids.
                if 'count' in event_props and 'EventId' in pvs:
                    row_dict['count'] = len(pvs['EventId'])
                period = _get_observation_period_for_date(date)
                if period:
                    row_dict['observationPeriod'] = period
                # Get all other properties.
                for prop in event_props:
                    if prop in pvs:
                        row_dict[prop] = pvs[prop]
                writer.writerow(_format_property_values(row_dict, digits=3))
        return output_csv

    def write_place_svobs_tmcf(self, event_props: list,
                               output_path: str) -> str:
        '''Returns the filename into which the tMCF for the SVObs for places
        is generated.

        ArgsL
         event_props: list of event properties for whcih SVObs are generated.
           each property is converted into a statvar.

        Returns:
          output tMCF filename with the reference to all columns in the SVObs csv
        '''
        event_type = utils.strip_namespace(
            self._config.get('event_type', 'FloodEvent'))
        tmcf_nodes = []
        tmcf_prefix = 'EventPlaces'
        format_config = self._config.get('property_config',
                                         _DEFAULT_CONFIG.get('property_config'))
        # Get common PVs for the statvars
        # measuredProperty is set to each event_prop
        default_statvar_pvs = self._config.get('default_statvar_pvs', {
            'typeOf': 'dcs:StatistcalVariable',
            'statType': 'measuredValue',
        })
        if 'populationType' not in default_statvar_pvs:
            default_statvar_pvs['populationType'] = event_type

        for prop in event_props:
            if not prop[0].islower():
                # ignore invalid properties that don't begin with a lower case
                continue
            # Generate the statvar dcid with the event_prop as mProp
            statvar_pvs = dict(default_statvar_pvs)
            statvar_pvs['measuredProperty'] = prop
            statvar_dcid = statvar_pvs.get('Node', statvar_pvs.get('dcid', ''))
            if not statvar_dcid:
                statvar_dcid = statvar_dcid_generator.get_statvar_dcid(
                    statvar_pvs)

            # Generate the tMCF node for the statvar referring to the prop
            node = []
            node.append(f'Node: E:{tmcf_prefix}->E{len(tmcf_nodes)}')
            node.append(f'typeOf: dcs:StatVarObservation')
            node.append(f'variableMeasured: dcs:{statvar_dcid}')
            node.append(f'observationAbout: C:{tmcf_prefix}->observationAbout')
            node.append(f'observationDate: C:{tmcf_prefix}->observationDate')
            node.append(
                f'observationPeriod: C:{tmcf_prefix}->observationPeriod')
            node.append(f'value: C:{tmcf_prefix}->{prop}')
            # Add unit for property if needed.
            unit = format_config.get(prop, {}).get('unit', '')
            if unit:
                node.append(f'unit: {unit}')
            tmcf_nodes.append('\n'.join(node))
        output_tmcf = file_util.file_get_name(output_path, 'place_svobs',
                                              '.tmcf')
        logging.info(
            f'Writing tmcf with {len(tmcf_nodes)} nodes for place svobs columns {event_props} into {output_tmcf}'
        )
        with file_util.FileIO(output_tmcf, 'w') as tmcf_file:
            tmcf_file.write('\n\n'.join(tmcf_nodes))
        return output_tmcf

    def write_events_place_svobs(
            self,
            output_path: str,
            event_ids: list = None,
            event_props: list = ['area', 'count'],
            date_formats: list = ['YYYY-MM-DD', 'YYYY-MM', 'YYYY']) -> list:
        '''Returns a list of generated CSV/tMCF files with SVObs for
        the affected places of events.

        It aggregates event properties by place,date for all affected places
        and generates SVObs for each property in event_props with observationAbout as
        the place.

        If a list of date_formats are given, it also aggregates properties
        for each place across all dates in the time period, such as month or year
        using the property aggregation settings in 'property_config_across_dates'.

        If aggregate_by_contained_in_place is set in the config,
        the event porperties are also aggregated across all parent places for
        all dates using the property aggregation settings in config
        'property_config_across_dates'.

        Args:
          output_path: string file prefix for output files.
            It is combined with a suffix such as 'place_svobs.csv', 'place_svobs.tmcf'
          event_ids: A list of event ids to be processed into the output files.
          event_props: List of event properties for which SVObs are generated.
            properties that being with a Capital letter are considered internal
            and are ignored in the output.
          date_formats: List of date formats, such as , 'YYYY' for year,
            'YYYY-MM' for months into whcih properties are aggregated.

        Returns:
         a list of filenames for CSV and tMCF generated.
        '''
        if not event_ids:
            event_ids = self.get_all_event_ids()
        logging.info(
            f'Generating place svobs for {len(event_ids)} events for dates: {date_formats}'
        )

        # Collect data for each event place and date
        # as a dict: {(place, date): {'area': NN},... }
        place_date_pvs = self.get_place_date_output_properties(
            event_ids, event_props)

        # Aggregate property values by place across time periods
        self.aggregate_by_time_period(place_date_pvs, date_formats)

        # Aggregate by parent places
        if self._config.get('aggregate_by_contained_in_place', False):
            self.aggregate_by_contained_in_place(place_date_pvs)

        output_files = []
        # Write the place svobs.
        output_files.append(
            self.write_place_svobs_csv(place_date_pvs, event_props,
                                       output_path))

        # Generate tmcf for place svobs.
        output_files.append(
            self.write_place_svobs_tmcf(event_props, output_path))
        return output_files

    def process_csv(self,
                    csv_files: list,
                    output_path: str,
                    input_events_file: str = None,
                    output_active_events_path: str = None,
                    output_active_events_state: str = None) -> list:
        '''Process CSV files with data for places into events.
         Places can be s2 cells or grids with lat/lng.
         '''
        if input_events_file:
            self.read_active_events(input_events_file)
        _set_counter_stage(self._counters, 'process_csv_')
        input_files = file_util.file_get_matching(csv_files)
        for filename in input_files:
            self._counters.add_counter(
                'total', file_util.file_estimate_num_rows(filename))
        logging.info(
            f'Processing data from files: {input_files} with config: {self._config.get_configs()}'
        )
        for filename in input_files:
            logging.info(f'Processing csv data file: {filename}')
            with file_util.FileIO(filename) as csvfile:
                reader = csv.DictReader(csvfile,
                                        delimiter=self._config.get(
                                            'input_delimiter', ','))
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
                    self.process_event_data(input_row, filename, num_rows)
                # Deactivate old events before moving to next CSV file.
                # Assumes event files are in increasing order by date.
                self.deactivate_old_events(self.get_active_event_ids(),
                                           self._max_date)
                logging.info(
                    f'Created {len(self._event_by_id)} events for {num_rows} rows from file: {filename}'
                )
        output_files = self.output_events(output_path,
                                          output_active_events_path,
                                          output_active_events_state)
        self.save_place_cache_file()
        return output_files

    def process_event_data(self,
                           data: dict,
                           filename: str = '',
                           row_index: int = 0) -> bool:
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
        data_pvs['affectedPlace'] = utils.add_namespace(place)
        if place_id != place:
            data_pvs['affectedPlace'] += ',' + utils.add_namespace(place_id)
        date_column = self._config.get('date_column', 'observationDate')
        date = row.get(date_column, '')
        if not date:
            self._counters.add_counter('error_input_rows_missing_date', 1)
            logging.error(f'Missing date in row:{filename}:{row_index}:{row}')
            return False
        if date < self._max_date:
            self._counters.add_counter('error_input_rows_date_out_of_order', 1)
            logging.error(f'Old date in row:{filename}:{row_index}:{row}')
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
            area = utils.place_area(place)
            if not area:
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
        self._counters.set_counter('num_events', len(self._event_by_id))
        return True

    def get_place_id_for_event(self, place_id: str) -> str:
        '''Returns the place_id for the event data.'''
        output_place_type = self._config.get('convert_place_to_grid', '')
        if output_place_type:
            # Converting a non-grid place to a grid_1 place.
            # Multiple places mapping to same grid will be
            # aggregated using 'property_config_per_date'.
            lat, lng = self._get_place_lat_lng(place_id)
            if lat is not None and lng is not None:
                # Got a location. Convert it to a grid.
                if (output_place_type
                        == 'grid_1') and (not utils.is_grid_id(place_id)):
                    grid_id = utils.grid_id_from_lat_lng(1, lat, lng)
                    place_id = grid_id
                    self._counters.add_counter(f'place_converted_to_grid_1', 1)
                elif (output_place_type
                      == 's2_10') and (not utils.is_s2_cell_id(place_id)):
                    s2cell_id = utils.s2_cell_to_dcid(
                        utils.s2_cell_from_latlng(lat, lng, 10))
                    place_id = s2cell_id
                    self._counters.add_counter(f'place_converted_to_s2_level10',
                                               1)
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
                      output_active_events_state: str = None) -> list:
        output_files = []
        # Output all ended events
        output_ended_events = False
        if output_active_events_path:
            # No separate output path for active events.
            # Output all events, not just ended ones.
            output_ended_events = True
        if self._config.get('output_events', True):
            _set_counter_stage(self._counters, 'emit_events_csv_')
            output_files.append(
                self.write_events_csv(output_path=output_path,
                                      output_ended_events=output_ended_events))
        if self._config.get('output_svobs', False):
            _set_counter_stage(self._counters, 'emit_events_svobs_')
            output_files.extend(
                self.write_events_svobs(
                    output_path=_get_output_subdir_path(output_path,
                                                        'event_svobs'),
                    output_ended_events=output_ended_events))
        if self._config.get('output_place_svobs', False):
            output_files.extend(
                self.write_events_place_svobs(
                    output_path=_get_output_subdir_path(output_path,
                                                        'place_svobs'),
                    event_props=self._config.get(
                        'output_place_svobs_properties', ['area', 'count']),
                    date_formats=self._config.get(
                        'output_place_svobs_dates',
                        ['YYYY-MM-DD', 'YYYY-MM', 'YYYY'])))
        # Output active events into a separate set of files.
        active_event_ids = self.get_active_event_ids(self._max_date)
        self._counters.set_counter('active_events', len(active_event_ids))
        if output_active_events_path:
            logging.info(
                f'Emitting {len(active_event_ids)} active events into: {output_active_events_path}'
            )
            if self._config.get('output_active_events', False):
                _set_counter_stage(self._counters, 'emit_active_events_csv_')
                output_files.append(
                    self.write_events_csv(output_path=output_active_events_path,
                                          event_ids=active_event_ids,
                                          output_ended_events=False))
            if self._config.get('output_active_svobs', False):
                _set_counter_stage(self._counters, 'emit_active_events_svobs_')
                output_files.extend(
                    self.write_events_svobs(
                        output_path=output_active_events_path,
                        event_ids=active_event_ids,
                        output_ended_events=False))
        if output_active_events_state:
            _set_counter_stage(self._counters, 'emit_active_events_data_')
            output_files.append(
                self.write_active_events(output_active_events_state))
        return output_files

    def _get_date_with_interval(self, date: str) -> str:
        '''Returns the date with the interval 'max_event_interval_days' applied.'''
        if not date:
            return date
        interval_days = timedelta(
            days=self._config.get('max_event_interval_days', 30))
        min_date = _get_full_date(date)
        try:
            min_date = (parser.parse(min_date) - interval_days).isoformat()
        except parser._parser.ParserError:
            logging.error(f'Unable to parse date: "{min_date}"')
            self._counters.add_counter('error_input_rows_invalid_date', 1)
            min_date = date
        return min_date

    def _get_contained_for_place(self, place_id: str) -> list:
        '''Returns a list of containdInPlace dcids for a place.'''
        new_places = set({place_id})
        parent_places = set()
        # Lookup parent places for all parents.
        while len(new_places) > 0:
            placeid = new_places.pop()
            new_parents = self.get_place_property_list(placeid,
                                                       'containedInPlace')
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
                    new_parents = self._latlng_to_place_cache[placeid]
                elif self._config.get('lookup_contained_for_place', False):
                    lat, lng = utils.place_id_to_lat_lng(
                        placeid, self._config.get('dc_api_enabled', True))
                    if lat is not None and lng is not None:
                        new_parents = self._ll2p.resolve(lat, lng)
                        self._latlng_to_place_cache[placeid] = new_parents
                        self._counters.add_counter('latlng_place_lookups', 1)
                new_parents = _get_list(new_parents)
            if new_parents:
                # Collect all new parent places to be looked up again.
                for new_place in new_parents:
                    if new_place and new_place not in parent_places:
                        new_places.add(new_place)
                        parent_places.add(new_place)
        contained_places = sorted(list(parent_places))
        self.set_place_property(place_id, 'containedInPlace', contained_places)
        return contained_places

    def _get_smallest_place_name(self, place_ids: list) -> str:
        '''Returns the name of the smallest place in the place list.'''
        max_place_rank = -1
        place_name = ''
        # Get the place with the highest rank (smallest place)
        for place in _get_list(place_ids):
            place = utils.strip_namespace(place)
            if place == 'Earth' or utils.is_s2_cell_id(
                    place) or utils.is_grid_id(place) or utils.is_ipcc_id(
                        place):
                # Ignore non admin places
                continue
            place_types = self.get_place_property_list(place, 'typeOf')
            for place_type in place_types:
                place_rank = _PLACE_TYPE_RANK.get(place_type, -1)
                if place_rank > max_place_rank:
                    # This place is smaller. Use its name if available.
                    new_place_name = self.get_place_property_list(place, 'name')
                    if new_place_name:
                        new_place_name = new_place_name[0]
                    if new_place_name:
                        max_place_rank = place_rank
                        place_name = new_place_name
        return place_name

    def _get_event_name(self, event_pvs: dict, locations: list = None) -> str:
        '''Get the name for the event.'''
        typeof = event_pvs.get('typeOf',
                               self._config.get('event_type', 'FloodEvent'))
        start_date = event_pvs.get('startDate')
        # Get a named location for the event
        start_location = event_pvs.get('startLocation')
        if not locations:
            locations = _get_list(event_pvs.get('affectedPlace', ''))
        location_name = self._get_smallest_place_name(locations)
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
                data['affectedPlace'] = ','.join(sorted(contained_places))
                data['AffectedPlaceCount'] = len(affected_places)
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


def _format_property_values(pvs: dict,
                            config: dict = {},
                            digits: int = 5) -> dict:
    '''Returns a set of properties with formatted values.'''
    fmt_pvs = {}
    for prop, value in pvs.items():
        fmt_value = value
        if isinstance(value, float):
            # Round floats to 5 decimal places
            fmt_value = round(value, digits)
        prop_config = config.get(prop, None)
        if prop_config:
            prop_unit = prop_config.get('unit', None)
            if prop_unit:
                fmt_value = f'[{fmt_value} {prop_unit}]'
        fmt_pvs[prop] = fmt_value
    return fmt_pvs


def _reset_counter_stage(counters: Counters, stage_name: str):
    counters.reset_process_stage(stage_name)


def _get_full_date(date_str: str) -> str:
    parts = date_str.count('-')
    if parts == 0:
        # Add month to date
        return date_str + '-01-01'
    if parts == 1:
        # Add day to date
        return date_str + '-01'
    return date_str


def _get_dates_duration(start_date: str, end_date: str) -> int:
    return (parser.parse(_get_full_date(end_date)) -
            parser.parse(_get_full_date(start_date))).days + 1


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


def _get_date_by_format(date_str: str, date_format: str) -> str:
    '''Returns the date in the given format, YYYY-MM or YYYY.'''
    date_tokens = date_str.split('-')
    num_tokens = date_format.count('-') + 1
    if num_tokens > len(date_tokens):
        return None
    return '-'.join(date_tokens[:num_tokens])


def _get_observation_period_for_date(date_str: str) -> str:
    '''Returns the observation period for date string.'''
    date_parts = date_str.count('-')
    if date_parts == 0:
        return 'P1Y'
    if date_parts == 1:
        return 'P1M'
    return ''


def _set_counter_stage(counters: Counters, name: str):
    '''Set the counter prefix to the stage.'''
    counter_prefix = counters.get_prefix()
    counter_prefix = counter_prefix[:counter_prefix.find(':')]
    stage_count = 0
    if counter_prefix:
        stage_count = int(counter_prefix)
    stage_count += 1
    counters.set_prefix(f'{stage_count}:{name}')


def _get_list(items: str) -> list:
    '''Returns a list of unique items, splitting comma separated strings.'''
    items_set = set()
    if items:
        if isinstance(items, str):
            items = items.split(',')
        for item in items:
            items_set.update(item.split(','))
    return sorted(items_set)


def _get_output_subdir_path(path: str, sub_dir: str) -> str:
    '''Adds a sub directory for the path prefix.'''
    dirname = os.path.dirname(path)
    basename = os.path.basename(path)
    if dirname:
        sub_dir = os.path.join(dirname, sub_dir)
    return os.path.join(sub_dir, basename)


_DEFAULT_CONFIG = {
    # Aggregation settings for properties across events for a date.
    'property_config_per_date': {
        'aggregate': 'sum',
        'area': {
            'aggregate': 'sum',
            'unit': 'SquareKilometer',
        },
        'EventId': {
            'aggregate': 'set'
        },
        'affectedPlace': {
            'aggregate': 'list',
        },
    }
}


def get_default_config() -> dict:
    '''Returns dictionary with the default config GeoEventsProcessor
    from event_config.py.
    '''
    global _DEFAULT_CONFIG
    if not _DEFAULT_CONFIG:
        # Load default config from event_config.py
        _DEFAULT_CONFIG = file_util.file_load_py_dict(
            os.path.join(os.path.dirname(__file__), 'event_config.py'))
    return _DEFAULT_CONFIG


def process(csv_files: list,
            output_path: str,
            input_events_file: str = None,
            output_active_events_path: str = None,
            output_active_events_state: str = None,
            config: ConfigMap = None) -> list:
    counters = Counters()
    if config is None:
        config = ConfigMap(config_dict=get_default_config())
    events_processor = GeoEventsProcessor(config, counters)
    return events_processor.process_csv(csv_files, output_path,
                                        input_events_file,
                                        output_active_events_path,
                                        output_active_events_state)


def main(_):
    if _FLAGS.debug:
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
