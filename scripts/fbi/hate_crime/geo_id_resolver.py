# Copyright 2021 Google LLC
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
"""
Resolving place dcid given the Pub_agency_name, Agency_type_name, State_Abbr
from FBI hate crime dataset
"""

import os
import sys
import csv

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../util'))  # For State and County map

from alpha2_to_dcid import USSTATE_MAP
from county_to_dcid import COUNTY_MAP

city_geocodes_csv_path = os.path.join(_SCRIPT_PATH,
                                      '../crime/city_geocodes.csv')

_US_GEO_CODE_UPDATE_MAP = {
    # Mapping geos in data to geos in csv / map
    'NB':
        'NE',
    'GM':
        'GU',
    'amherst town ny':
        'amherst ny',
    'montgomery town ny':
        'montgomery ny',
    'point pleasant beach nj':
        'point pleasant beach borough nj',
    'pompton lakes nj':
        'pompton lakes borough nj',
    'allendale nj':
        'allendale borough nj',
    'atlantic highlands nj':
        'atlantic highlands borough nj',
    'belleville nj':
        'bileville township nj',
    'belmar nj':
        'belmar borough nj',
    'bergenfield nj':
        'bergenfield borough nj',
    'berlin nj':
        'berlin borough nj',
    'bloomfield nj':
        'bloomfield township nj',
    'blooming grove town ny':
        'blooming grove ny',
    'bloomingdale nj':
        'bloomingdale borough nj',
    'bogota nj':
        'bogota borough nj',
    'boise id':
        'boise town id',
    'bordentown city nj':
        'bordentown nj',
    'bradley beach nj':
        'bradley beach borough nj',
    'brentwood pa':
        'brentwood borough pa',
    'burlington city nj':
        'burlington nj',
    'camden county police department nj':
        'camden nj',
    'carmel town ny':
        'carmel ny',
    'carteret nj':
        'carteret borough nj',
    'chatham nj':
        'chatham borough nj',
    'chester nj':
        'chester borough nj',
    'clarkstown town ny':
        'clarkstown ny',
    'cliffside park nj':
        'cliffside park borough nj',
    'collingdale pa':
        'collingdale borough pa',
    'colonie town ny':
        'colonie ny',
    'coraopolis pa':
        'coraopolis borough pa',
    'cresskill nj':
        'cresskill borough nj',
    'dunellen nj':
        'dunellen borough nj',
    'east lansdowne pa':
        'east lansdowne borough pa',
    'east newark nj':
        'east newark borough nj',
    'elmwood park nj':
        'elmwood park borough nj',
    'emerson nj':
        'emerson borough nj',
    'engelwood cliffs nj':
        'engelwood nj',
    'fair haven nj':
        'fair haven borough nj',
    'fair lawn nj':
        'fair lawn borough nj',
    'falls township, bucks county pa':
        'falls township pa',
    'fallsburg town ny':
        'fallsburg ny',
    'farmingdale nj':
        'farmingdale borough nj',
    'flemington nj':
        'flemington borough nj',
    'fort lee nj':
        'fort lee borough nj',
    'franklin township, gloucester county nj':
        'franklin borough nj',
    'fulton city ny':
        'fulton ny',
    'garwood nj':
        'garwood borough nj',
    'glassboro nj':
        'glassboro borough nj',
    'greenfield ma':
        'greenfield town ma',
    'greenwich township, warren county nj':
        'greenwich township nj',
    'guilderland town ny':
        'guilderland ny',
    'haddonfield nj':
        'haddonfield borough nj',
    'haledon nj':
        'haledon borough nj',
    'hamburg nj':
        'hamburg borough nj',
    'hamilton township, mercer county nj':
        'hamilton township nj',
    'hi-nella nj':
        'hi-nella borough nj',
    'high bridge nj':
        'high bridge borough nj',
    'highland park nj':
        'highland park borough nj',
    'highlands nj':
        'highlands borough nj',
    'hoosick falls village ny':
        'hoosick falls ny',
    'hopatcong nj':
        'hopatcong borough nj',
    'indiana pa':
        'indiana borough pa',
    'irvington nj':
        'irvington township nj',
    'jamesbug nj':
        'jamesburg borough nj',
    'keansburg nj':
        'keansburg borough nj',
    'keyport nj':
        'keyport borough nj',
    'kinnelon nj':
        'kinnelon borough nj',
    'lakehurst nj':
        'lakehurst borough nj',
    'lancaster village ny':
        'lancaster ny',
    'las vegas metropolitan police department nv':
        'las vegas nv',
    'lawrence township, mercer county nj':
        'lawrence township nj',
    'lincoln park nj':
        'lincoln park borough nj',
    'little silver nj':
        'little silver borough nj',
    'lodi nj':
        'lodi borough nj',
    'madison nj':
        'madison borough nj',
    'magnolia nj':
        'magnolia borough nj',
    'manasquan nj':
        'manasquan borough nj',
    'mansfield township, warren county nj':
        'mansfield township nj',
    'manville nj':
        'manville borough nj',
    'matawan nj':
        'matawan borough nj',
    'methuen ma':
        'methuen town ma',
    'metuchen nj':
        'metuchen borough nj',
    'millersville pa':
        'millersville borough pa',
    'monroe township, middlesex county nj':
        'monroe township nj',
    'moonachie nj':
        'moonachie borough nj',
    'morris plains nj':
        'morris plains borough nj',
    'mount ephraim nj':
        'mount ephraim borough nj',
    'national park nj':
        'national park borough nj',
    'new milford nj':
        'new milford borough nj',
    'north arlingtion nj':
        'north arlington borough nj',
    'north caldwell nj':
        'north caldwell borough nj',
    'north plainfield nj':
        'north plainfield borough nj',
    'northern york county regional pa':
        'north york borough pa',
    'norwood nj':
        'norwood borough nj',
    'oakland nj':
        'oakland borough nj',
    'ocean township, monmouth county nj':
        'ocean township nj',
    'olive town ny':
        'olive ny',
    'oneonta city ny':
        'oneonta ny',
    'orange city nj':
        'orange nj',
    'palisades park nj':
        'palisades park borough nj',
    'palmyra nj':
        'palmyra borough nj',
    'paramus nj':
        'paramus borough nj',
    'park ridge nj':
        'park ridge borough nj',
    'paulsboro nj':
        'paulsboro borough nj',
    'penn township, westmoreland county pa':
        'penn township pa',
    'pewaukee village wi':
        'pewaukee wi',
    'pine hill nj':
        'pine hill borough nj',
    'pitman nj':
        'pitman borough',
    'point pleasant nj':
        'point pleasant borough nj',
    'pottstown pa':
        'pottstown borough pa',
    'putnam valley town ny':
        'putnam valley ny',
    'ramsey nj':
        'ramsey borough nj',
    'red bank nj':
        'red bank borough',
    'ridgefield nj':
        'ridgefield borough nj',
    'ringwood nj':
        'ringwood borough nj',
    'roselle nj':
        'roselle borough nj',
    'roselle park nj':
        'roselle park borough nj',
    'rumson nj':
        'rumson borough nj',
    'runnemede nj':
        'runnemede borough nj',
    'sayreville nj':
        'sayreville borough nj',
    'scarsdale village ny':
        'scarsdale ny',
    'seaside heights nj':
        'seaside heights borough nj',
    'selinsgrove pa':
        'selinsgrove borough pa',
    'ship bottom nj':
        'ship bottom borough nj',
    'shrewsbury nj':
        'shrewsbury borough nj',
    'somerdale nj':
        'somerdale borough nj',
    'somerset pa':
        'somerset borough pa',
    'somerville nj':
        'somerville borough nj',
    'south orange village nj':
        'south orange village township nj',
    'south plainfield nj':
        'south plainfield borough nj',
    'south river nj':
        'south river borough nj',
    'southampton town ny':
        'southampton ny',
    'springfield township, union county nj':
        'springfield township nj',
    'stanhope nj':
        'stanhope borough nj',
    'state college pa':
        'state college borough pa',
    'swarthmore pa':
        'swarthmore borough pa',
    'tenafly nj':
        'tenafly borough nj',
    'teterboro nj':
        'teterboro borough nj',
    'tinton falls nj':
        'tinton falls borough nj',
    'tuckerton nj':
        'tuckerton borough nj',
    'verona nj':
        'verona township nj',
    'wanaque nj':
        'wanaque borough nj',
    'washington township, gloucester county nj':
        'washington township, glouchester county nj',
    'washington township, bergen county nj':
        'washington township, bergen county nj',
    'waynesburg pa':
        'waynesburg borough pa',
    'west chester pa':
        'wester chester pa',
    'west long branch nj':
        'west long branch borough nj',
    'west orange nj':
        'west orange township nj',
    'westville nj':
        'westville borough nj',
    'wharton nj':
        'wharton borough nj',
    'wildwood crest nj':
        'wildwood crest borough nj',
    'yorktown town ny':
        'yorktown ny',
    'allenhurst nj':
        'allenhurst borough nj',
    'allentown nj':
        'allentown borough nj',
    'alpha nj':
        'alpha borough nj',
    'bernardsville nj':
        'bernardsville borough nj',
    'frankfort village ny':
        'frankfort ny'
}

_IGNORE_STATE_ABBR = ['FS']  # Ignoring federal codes

city = {}
with open(os.path.join(city_geocodes_csv_path), encoding="utf8") as csvfile:
    csv_reader = csv.reader(csvfile)
    for a in csv_reader:
        city[a[0]] = a[1]


def state_to_dcid(state_code):
    if state_code in _IGNORE_STATE_ABBR:
        return ''

    if state_code in _US_GEO_CODE_UPDATE_MAP:
        state_code = _US_GEO_CODE_UPDATE_MAP[state_code]

    if state_code in USSTATE_MAP:
        return USSTATE_MAP[state_code]
    else:
        return ''


def get_county_variants(county):
    county = county.replace(" County Police Department", " County")
    county_variants = [
        county, county + " County", county + " Parish", county + " Borough"
    ]
    return county_variants


def county_to_dcid(state_abbr, county):
    _IGNORE_LIST = ['geoId/47157', 'geoId/21185']
    if state_abbr in _IGNORE_STATE_ABBR:
        return ''

    if state_abbr in _US_GEO_CODE_UPDATE_MAP:
        state_abbr = _US_GEO_CODE_UPDATE_MAP[state_abbr]

    county_valid_names = get_county_variants(county)

    if state_abbr in COUNTY_MAP:
        for county in county_valid_names:
            if county in COUNTY_MAP[state_abbr]:
                county_dcid = COUNTY_MAP[state_abbr][county]
                if county_dcid in _IGNORE_LIST:
                    return ''
                return COUNTY_MAP[state_abbr][county]
        return ''
    else:
        return ''


def city_to_dcid(state_abbr, city_name):
    if state_abbr in _IGNORE_STATE_ABBR:
        return ''

    if state_abbr in _US_GEO_CODE_UPDATE_MAP:
        state_abbr = _US_GEO_CODE_UPDATE_MAP[state_abbr]

    city_state = city_name.lower() + " " + state_abbr.lower()

    if city_state in _US_GEO_CODE_UPDATE_MAP:
        city_state = _US_GEO_CODE_UPDATE_MAP[city_state]

    if city_state in city:
        return "geoId/" + city[city_state]
    else:
        return ''


def convert_to_place_dcid(state_abbr, geo_name='', geo_type='State'):
    """resolves GEOID based on the FBI Hate crime dataset Agency Type and Name. 
    If a geoId could not be resolved, the function returns an empty string ('').
    """
    if state_abbr in _IGNORE_STATE_ABBR:
        return ''

    if state_abbr in _US_GEO_CODE_UPDATE_MAP:
        state_abbr = _US_GEO_CODE_UPDATE_MAP[state_abbr]

    if geo_type == 'State':
        return state_to_dcid(state_abbr)

    elif geo_type == 'County':
        return county_to_dcid(state_abbr, geo_name)

    elif geo_type == 'City':
        return city_to_dcid(state_abbr, geo_name)

    else:
        # geo type currently not handled
        return ''
