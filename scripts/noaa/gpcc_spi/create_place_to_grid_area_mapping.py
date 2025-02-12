# Copyright 2022 Google LLC
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
"""Processes a list of places into %area of place within 1 degree grids.

Input:
  csv with a single column that represents the places where geojson exists in dc.

Output:
  A single json file that maps
  place id -> list of ({"grid": grid key , "ratio": %area within grid})

"""

from shapely import geometry
import datacommons as dc
import concurrent.futures
from typing import List, Optional
import json
import csv

from absl import flags
from absl import app

FLAGS = flags.FLAGS

flags.DEFINE_string('gpcc_spi_places_with_csv',
                    'geojson_data/places_with_geojson.csv',
                    'Path to places with geojson.')
flags.DEFINE_string('gpcc_spi_place_grid_ratio_output_dir',
                    'geojson_data/place_to_one_degree_grid_mapping.json',
                    'Path where the result is written to.')

LAT_MIN = -90
LAT_MAX = 90
LNG_MIN = -180
LNG_MAX = 180


def construct_one_degree_grid_polygons() -> List[geometry.box]:
    """Returns a list of all 1 degree grids."""
    grids = dict()
    for lat in range(LAT_MIN, LAT_MAX):
        for lng in range(LNG_MIN, LNG_MAX):
            key = f"{lat}^{lng}"
            grids[key] = geometry.box(lng, lat, lng + 1, lat + 1)
    return grids


def get_place_by_type(parent_places, places_types: List[str]) -> List[str]:
    """Return the place ids of all places contained in a set of parent places."""
    all_types_of_places = []
    for place_type in places_types:
        parent_place_to_places = dc.get_places_in(parent_places, place_type)
        for places in parent_place_to_places.values():
            for place in places:
                all_types_of_places.extend(place)
    return all_types_of_places


def places_to_geo_jsons(places: List[str]):
    """Get geojsons for a list of places."""
    resp = dc.get_property_values(places, 'geoJsonCoordinates')
    geojsons = {}
    for p, gj in resp.items():
        if not gj:
            continue
        geojsons[p] = geometry.shape(json.loads(gj[0]))
    return geojsons


def fit_shape_in_grids(shape, grids):
    containment_data = []
    for grid_key, box in grids.items():
        # Place is completely inside the grid.
        if box.covers(shape):
            return [{'grid': grid_key, 'ratio': 1}]

        # 100% of the grid belongs to the place.
        if shape.covers(box):
            containment_data.append({
                'grid': grid_key,
                'ratio': box.area / shape.area
            })
            continue

        if not shape.intersects(box):
            continue
        # Part of the place belongs to the grid.
        intersection = shape.intersection(box)
        ratio = intersection.area / shape.area
        containment_data.append({'grid': grid_key, 'ratio': ratio})

    return containment_data


def read_input(places_with_csv: str):
    places_with_geojson = []
    with open(places_with_csv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            places_with_geojson.append(row['id'])
    return places_with_geojson


def get_geojsons(places_with_geojson: List[str]):
    """Batch call DC api to get geojsons."""
    BATCH_SIZE = 100
    batch = []

    geojsons = dict()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for place in places_with_geojson:
            batch.append(place)
            if len(batch) == BATCH_SIZE:
                futures.append(executor.submit(places_to_geo_jsons, batch))
                batch = []

        if batch:
            futures.append(executor.submit(places_to_geo_jsons, batch))

    for future in concurrent.futures.as_completed(futures):
        geojsons_partial = future.result()
        geojsons.update(geojsons_partial)

    return geojsons


def create_place_to_grid_mapping(places_with_geojson: List[str],
                                 output: Optional[str] = None,
                                 write_results: bool = True):
    """Fit all places in grids."""
    geojsons = get_geojsons(places_with_geojson)

    one_degree_grids = construct_one_degree_grid_polygons()

    place_to_grid_ratios = dict()
    for place, geojson in geojsons.items():
        grid_ratios = fit_shape_in_grids(geojson, one_degree_grids)
        place_to_grid_ratios[place] = grid_ratios

    if write_results:
        with open(output, 'w') as f:
            json.dump(place_to_grid_ratios, f)
        return

    return place_to_grid_ratios


def main(_):
    places_with_geojson = read_input(FLAGS.gpcc_spi_places_with_csv)
    create_place_to_grid_mapping(places_with_geojson,
                                 FLAGS.gpcc_spi_place_grid_ratio_output_dir)


if __name__ == "__main__":
    app.run(main)
