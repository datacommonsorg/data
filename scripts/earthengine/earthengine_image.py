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
"""Script to extract geoTIFF image from EarthEngine.

Authenticate EarthEngine/GCloud API with the command, open the URL in a browser
and paste the token when prompted:
  earthengine authenticate

If running on a remote machine, authenticate with command:
  earthengine authenticate --quiet
then run the gcloud auth command as shown and enter back the token.

To extract flooded regions from the dynamic world dataset, run:
  python3 earthengine_image.py \
      --ee_dataset='dynamic_world' `# Pick an existing dataset` \
      --start_date='2022-10-1' `# Filter dataset for the date range` \
      --end_date='2022-10-31' \
      --band='water' `# Pick water band from dynamic world collection` \
      --band_min=0.7 `# Minimum value for a pixel to be considered flooded` \
      --ee_reducer='max' `# Get the maximal flood extent over the time period` \
      --ee_mask='land' `# filter by dataset land to remove permanent water `\
      --scale=1000 `# Reduce image to 1000m pixels` \
      |& tee /tmp/ee.log

This creates a task on Earth Engine.
To view task status, visit https://code.earthengine.google.com/tasks
    or run:
  earthengine task list
"""

import ast
import datetime
import ee
import glob
import os
import re
import sys
import time

from absl import app
from absl import flags
from absl import logging
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

flags.DEFINE_string('config', '',
                    'File with configuration parameters as a dictionary.')
flags.DEFINE_string('ee_dataset', '',
                    'Load earth engine data set define in config datasets.')
flags.DEFINE_string('gcs_output', '', 'Prefix for output file names on GCS.')
flags.DEFINE_string('gcs_project', '', 'GCS project for exporting images.')
flags.DEFINE_string('gcs_bucket', 'earth_engine_exports',
                    'GCS bucket for exporting images.')
flags.DEFINE_string('gcs_folder', '', 'GCS folder for exporting images.')
flags.DEFINE_string(
    'start_date', '',
    'Date from which image is to be loaded in YYYY-MM-DD format.')
flags.DEFINE_string(
    'end_date', '',
    'Date upto which image is to be loaded in YYYY-MM-DD format.')
flags.DEFINE_string(
    'time_period', 'P1M',
    'Time range of images to be aggregated into a single image in P<N><T> format, '
    'for example "P1Y" for images merged over a year')
flags.DEFINE_string('ee_image_collection', '',
                    'Name of the EarthEngine image collection asset.')
flags.DEFINE_string(
    'ee_reducer', 'mean',
    'EarthEngine Reducer to be applied when merging images in the collection.')
flags.DEFINE_string('band', '', 'Band to be extracted from the ee image.')
flags.DEFINE_integer('scale', 1000, 'Scale in meters for the output image.')
flags.DEFINE_string(
    'ee_mask', '', 'Dataset to be applied as a mask when extracting the image.')
flags.DEFINE_float('band_min', None,
                   'Minimum value for the pixels in the band.')
flags.DEFINE_float('band_max', None,
                   'Maximum value for the pixels in the band.')
flags.DEFINE_float('band_eq', None, 'Value for the pixels in the band.')
flags.DEFINE_bool(
    'ee_band_bool', True,
    'Filter band by thresholds into a bool image with 1 where values are met.'
    'If False, the originals values meeting thresholds are preserved, '
    'and image set to 0 everywhere else.')
flags.DEFINE_string(
    'ee_image_eval', None,
    'Get image by evaluating the python statements with ee commands.')
flags.DEFINE_string(
    'ee_bounds', None,
    'Rectangular bounds as "lat,lng:lat,lng" for filtering images.')
flags.DEFINE_string(
    'ee_output_data_type', None,
    'Convert output band values to the given type, such as float, int.')
flags.DEFINE_integer(
    'ee_image_count', 1,
    'Number of images to generate, each advanced by --time_period.')
flags.DEFINE_bool('ee_export_image', True,
                  'If true, submit a task to export image.')
flags.DEFINE_bool('debug', False, 'Enable debug messages.')

_FLAGS = flags.FLAGS
_FLAGS(sys.argv)  # Allow invocation without app.run()

# Default Earth Engine datasets with asset name and bands.
_DEFAULT_DATASETS = {
    # Land mask from Hansen global forest cover 2015
    'land': {
        'ee_image': 'UMD/hansen/global_forest_change_2015',
        'band': 'datamask',
        'band_eq': 1,
    },

    # Water band from dynamic world
    # https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1#bands
    'dynamic_world': {
        'ee_image_collection': 'GOOGLE/DYNAMICWORLD/V1',
        # 'band': 'water',
        # 'band_min': 0.7, # Probability of a pixel to be water
    },

    # Water from Sentinel-1 SAR GRD
    'sar': {
        # Get image with band VV
        'ee_image_eval':
            "ee.ImageCollection('COPERNICUS/S1_GRD').filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')).filter(ee.Filter.eq('instrumentMode', 'IW')).select('VV')",
        # 'band': 'VV',
        # 'band_max': -17,
    },

    # NASA FIRMS Fires
    # https://developers.google.com/earth-engine/datasets/catalog/FIRMS
    'fires': {
        'ee_image_collection': 'FIRMS',
        # 'band': 'T21',  # Brightness temperature of a fire pixel in K
    },

    # ERA5 Monthly Aggregates
    # https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_MONTHLY#bands
    'era5_monthly': {
        'ee_image_collection': 'ECMWF/ERA5/MONTHLY',
    },
    'nasa_gfs_realtime': {
        # Get NASA GFS mages with forecast_hours as 0
        'ee_image_eval':
            "ee.ImageCollection('NOAA/GFS0P25').filter(ee.Filter.eq('forecast_hours', 0))",
    },
}

EE_DEFAULT_CONFIG = {
    # Image loading settings.
    'datasets': _DEFAULT_DATASETS,  # Predefined assets
    'ee_dataset': _FLAGS.ee_dataset,  # Reference to an asset in 'datasets'
    # asset id for an image collection
    'ee_image_collection': _FLAGS.ee_image_collection,
    # Image processing settings.
    'ee_reducer':
        _FLAGS.ee_reducer,  # Reducer to convert image collection to an image
    'band': _FLAGS.band,

    # Filter settings
    # Filter by bounding box
    'ee_bounds': _FLAGS.ee_bounds,
    # Filter by time range
    'start_date': _FLAGS.start_date,
    'end_date': _FLAGS.end_date,
    'time_period': _FLAGS.time_period,
    # Filter by band value
    'band_min': _FLAGS.band_min,
    'band_max': _FLAGS.band_max,
    'band_eq': _FLAGS.band_eq,
    'ee_band_bool': _FLAGS.ee_band_bool,
    # Mask of points to be allowed.
    'ee_mask': _FLAGS.ee_mask,

    # Output image settings
    'scale': _FLAGS.scale,
    'ee_output_data_type': _FLAGS.ee_output_data_type,
    # GCS setting to export images
    'gcs_project': _FLAGS.gcs_project,
    'gcs_folder': _FLAGS.gcs_folder,
    'gcs_bucket': _FLAGS.gcs_bucket,
    'gcs_output': _FLAGS.gcs_output,
    'ee_export_image': _FLAGS.ee_export_image,
    'ee_image_count': _FLAGS.ee_image_count,

    # Debug options
    'debug': _FLAGS.debug,
}


def _update_dict(src_dict: dict, dst_dict: dict) -> dict:
    '''Merge the src and dst dict, merging dictionary values instead of overwriting.'''
    for k in src_dict.keys():
        if k in dst_dict:
            dst_val = dst_dict[k]
            if isinstance(dst_val, dict):
                # Merge dict values from both source and dst.
                _update_dict(src_dict.get(k, {}), dst_val)
            elif isinstance(dst_val, list):
                # Merge lists from both source and dst.
                for i in src_dict[k]:
                    if i not in dst_val:
                        dst_val.append(i)
        else:
            # Copy value for missing key from src to dst.
            dst_dict[k] = src_dict[k]
    return dst_dict


def _load_config(config: str, default_config: dict = EE_DEFAULT_CONFIG) -> dict:
    '''Load config from string or file.'''
    config_dict = config
    # Load config from file or a string
    if isinstance(config, str):
        config_str = config
        if os.path.exists(config):
            with open(config, 'r') as config_file:
                config_str = config_file.read()
        if config_str:
            config_dict = ast.literal_eval(config_str)
        else:
            config_dict = {}
    # Merge with default config giving preference to new config.
    _update_dict(default_config, config_dict)
    logging.info(f'Using config: {config_dict}')
    return config_dict


def _parse_time_period(time_period: str) -> (int, str):
    '''Parse time period into a tuple of (number, unit), for eg: P1M: (1, month).'''
    re_pat = r'P?(?P<delta>[+-]?[0-9]+)(?P<unit>[A-Z])'
    m = re.search(re_pat, time_period.upper())
    if m:
        m_dict = m.groupdict()
        delta = int(m_dict.get('delta', '0'))
        unit = m_dict.get('unit', 'M')
        period_dict = {'D': 'days', 'M': 'months', 'Y': 'years'}
        period = period_dict.get(unit, 'day')
        return (delta, period)
    return (0, 'days')


def _advance_date(date_str: str,
                  time_period: str,
                  date_format: str = '%Y-%m-%d') -> str:
    '''Returns the date string advanced by the time period.'''
    next_date = ''
    if not date_str:
        return next_date
    dt = datetime.strptime(date_str, date_format)
    (delta, unit) = _parse_time_period(time_period)
    if not delta or not unit:
        logging.error(
            f'Unable to parse time period: {time_period} for date: {date_str}')
        return next_date
    next_dt = dt + relativedelta(**{unit: delta})
    return next_dt.strftime(date_format)


def _get_bbox_coordinates(bounds: str) -> ee.Geometry.BBox:
    '''Returns a bounding box coordinates dictionary for the bounds.
    bounds is a comma separated list of points of the form [lat,lng...].'''
    if not bounds:
        return None
    # Extract all coordinates.
    coords = list(filter(None, re.split(r'[^0-9\.+-]', bounds)))
    latitudes = [float(coords[l]) for l in range(0, len(coords), 2)]
    longitudes = [float(coords[l]) for l in range(1, len(coords), 2)]
    # Return the min/max latitude,longitude
    return {
        'west': min(longitudes),
        'south': min(latitudes),
        'east': max(longitudes),
        'north': max(latitudes),
    }


def ee_filter_bounds(col: ee.ImageCollection,
                     config: dict = {}) -> ee.ImageCollection:
    '''Retruns image or image collection filtered by the bounds
    in config[ee_bounds].
    Args:
      col: Image Collection
      config: dictionary with the key 'ee_bounds'
    Returns:
      filtered image collection.
    '''
    bbox_coords = _get_bbox_coordinates(config.get('ee_bounds', None))
    if bbox_coords:
        logging.info(f'Filtering image by bounds: {bbox_coords}')
        bbox = ee.Geometry.BBox(**bbox_coords)
        col = col.filterBounds(bbox)
    return col


def ee_filter_date(col: ee.ImageCollection,
                   config: dict = {}) -> ee.ImageCollection:
    '''Returns the image collection filtered for the date range.
    Args:
      col: image collection
      config: dictionary of parameters with keys:
        start_date, end_date, time_period
    Returns:
      filtered image collection.
    '''
    # Get start date or last week.
    start_date = config.get('start_date', None)
    end_date = config.get('end_date', None)
    if start_date is None and end_date is None:
        # No dates in the config. return original collection.
        return col
    time_period = config.get('time_period', 'P1M')
    if not start_date:
        # Pick 1 day ago if no start date is specified.
        start_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    start_dt = ee.Date(start_date)
    end_dt = None
    if end_date:
        end_dt = ee.Date(end_date)
    elif time_period:
        # Extract the delta and units from the period such as 'P1M'.
        end_date = _advance_date(start_date, time_period)
        end_dt = ee.Date(end_date)
    if end_dt is None:
        end_dt = ee.Date(date.today().strftime('%Y-%m-%d'))
    col = col.filterDate(start_dt, end_dt)
    logging.info(
        f'Filtering image collection {col.get("id")} by date [{start_date}:{end_date}] {start_dt.format()} - {end_dt.format()}'
    )
    return col


def ee_reduce_image_collection(col: ee.ImageCollection,
                               config: dict = {}) -> ee.Image:
    '''Returns the image reduced from the image collection.
    Args:
      col: image collection
      config: dictionary of parameters with keys:
        ee_reducer which is one of (min/max/mean/sum/count/first/last).
        if ee_reducer is not set, the reducer is inferred from the band thresholds:
          band_min, band_max, band_eq
        If multiple reducers are set, then all are applied in sequence.
    Returns:
      image with bands changed to '<band>_<reducer>', eg: 'water_max'
    '''
    if not isinstance(col, ee.ImageCollection):
        logging.error(f'Cannot reduce image: {col.id()} with config: {config}')
        return col

    _REDUCER_DICT = {
        'min': ee.Reducer.min(),
        'max': ee.Reducer.max(),
        'minMax': ee.Reducer.minMax(),
        'mean': ee.Reducer.mean(),
        'sum': ee.Reducer.sum(),
        'first': ee.Reducer.first(),
        'last': ee.Reducer.last(),
        'count': ee.Reducer.count(),
    }

    reducers = config.get('ee_reducer', 'mean').split(',')
    if isinstance(reducers, str):
        reducers = reducers.split(',')
    if not reducers:
        # Get default reducer based on band value thresholds.
        if 'band_min' in config:
            # Get max value to filter by min threshold.
            reducers = ['max']
        if 'band_max' in config:
            if not reducer:
                # Get min value to filter by max threshold alone.
                reducer = ['min']
            else:
                # Get mean value if both min/max thresholds are set.
                reducer = ['mean']
        elif 'band_eq' in config:
            reducer = ['last']
    img = ee.Image()
    for reducer in reducers:
        if reducer not in _REDUCER_DICT:
            logging.fatal(
                f'Unknown reducer: {reducer} not one of {_REDUCER_DICT.keys()}')
        reducer_fn = _REDUCER_DICT[reducer]
        reduced_img = col.reduce(reducer_fn)
        logging.info(
            f'Reduced image from coll: {reduced_img.get("id")} using reducer: {reducer}'
        )
        img = img.addBands(reduced_img)
    logging.info(
        f'Reduced collection to image {img.get("id")} with reducers: {reducers}'
    )
    return img


def ee_filter_band(image: ee.Image, config: dict) -> ee.Image:
    '''Returns an image with pixels within the given band value range.
    Args:
      image: image to be processed
      config: dictionary of parameter:values with the following:
        band_min, band_max, bane_eq
    Returns:
      image with value 1 where the band values are in the range.
    '''
    logging.info(
        f'Filtering band with config {config} on image: {image.get("id")}')
    min_threshold = config.get('band_min', None)
    max_threshold = config.get('band_max', None)
    eq_threshold = config.get('band_eq', None)

    if min_threshold is None and max_threshold is None and eq_threshold is None:
        # No range in config. Return the original image.
        return image

    if isinstance(image, ee.ImageCollection):
        # Reduce input image collection to an image.
        image = ee_reduce_image_collection(image, config)

    # Remove pixels from image that are outside the band thresholds
    # by using a mask that filters for the band value range.
    if config.get('ee_band_bool', True):
        # Apply the band thresholds to get a bool image
        # with 1 for points that that meet the thresholds.
        if eq_threshold:
            image = image.eq(eq_threshold)
        elif max_threshold is not None:
            if min_threshold:
                image = image.gte(min_threshold).And(image.lte(max_threshold))
            else:
                image = image.lte(max_threshold)
        elif min_threshold is not None:
            image = image.gte(min_threshold)
        logging.info(f'Filtered band to bool image: {image.get("id")}')
    else:
        # Apply the threshold as a mask preserving pixel values that satisfy
        # threshold and setting others to 0.
        mask = None
        if min_threshold is not None:
            mask = image.gte(min_threshold)
        if max_threshold is not None:
            if mask:
                mask = mask.And(image.lte(max_threshold))
            else:
                mask = image.lte(max_threshold)
        if eq_threshold:
            mask = image.eq(eq_threshold)
        if mask:
            image = image.multiply(mask)
        logging.info(f'Filtered band with mask image: {image.get("id")}')
    return image


def ee_convert_band_output_type(img: ee.Image, config: dict) -> ee.Image:
    '''Returns an image with bands converted to a consistent type
    as set in config 'ee_output_data_type'.
    Args:
      img: Image with bands to be converted
      config: dictionary of parameter:values with the parameters:
        ee_output_data_type: set to one of int/float.
    Returns:
      image with bands set to the given output type.
    '''
    data_type = config.get('ee_output_data_type', None)
    if not data_type:
        return img
    data_type = data_type.lower()
    logging.info(f'Changing bands in image to {data_type}: {img.get("id")}')
    if data_type == 'float':
        return img.toFloat()
    if data_type == 'int':
        return img.toInt()
    logging.fatal(f'Unsupported data type: {data_type}')
    return img


def ee_generate_image(config: dict) -> ee.Image:
    '''Generate an image from the collection filtered by  the date and period,
    with the band having values within min and max thresholds.
    Args:
      config: dictionary of parameter:values
        specifying the asset to load as ee_image or ee_image_collection or ee_dataset
        and filtering conditions such as date, band, values.
    Returns:
      image or image collection.
    '''
    # If dataset specified, load it.
    img = None
    if config.get('ee_dataset'):
        dataset = config['ee_dataset']
        if dataset in config['datasets']:
            logging.info(f'Loading dataset: {dataset} from {config}')
            img = ee_generate_image(config['datasets'][dataset])
            if img == None:
                logging.error(f'Unable to get image for dataset {dataset}')

    # Load image from the config parameters and filter.
    if img is None:
        if config.get('ee_image_eval'):
            logging.info(f'Loading image from eval: {config["ee_image_eval"]}')
            img = eval(config['ee_image_eval'])
        elif config.get('ee_image_collection'):
            logging.info(
                f'Loading image collection: {config["ee_image_collection"]}')
            img = ee.ImageCollection(config['ee_image_collection'])
        elif config.get('ee_image'):
            logging.info(f'Loading image: {config["ee_image"]}')
            img = ee.Image(config['ee_image'])
        else:
            return None

    if config.get('band'):
        img = img.select(config['band'])
        logging.info(
            f'Selected band: {config["band"]} in image {img.get("id")}')

    if isinstance(img, ee.ImageCollection):
        img = ee_filter_date(img, config)
        # Filter by bounds.
        img = ee_filter_bounds(img, config)
        logging.info(f'Filtered image {img.get("id")} by config: {config}')

    # Apply the band value threshold
    img = ee_filter_band(img, config)

    # Apply mask if any
    if config.get('ee_mask'):
        mask = None
        mask_config = config['ee_mask']
        if isinstance(mask_config, str):
            # Mask refers to an image in the data set. Load that.
            if config.get('datasets'):
                if mask_config in config['datasets']:
                    mask = ee_generate_image(config['datasets'][mask_config])
        else:
            # Mask refers to another config dictionary. Load that image.
            mask = ee_generate_image(config['ee_mask'])
        if mask:
            if isinstance(img, ee.ImageCollection):
                # Reduce input image collection to an image.
                img = ee_reduce_image_collection(img, config)
            img = img.updateMask(mask)
            logging.info(
                f'Applied mask: {mask.id()} for image: {img.get("id")}')

    # Change all output bands to a consistent type.
    if config.get('ee_output_data_type', None):
        img = ee_convert_band_output_type(img, config)

    return img


def export_ee_image_to_gcs(ee_image: ee.Image, config: dict = {}) -> str:
    '''Launch a task to export an EE image and returns the task id.
    View task status on https://code.earthengine.google.com/tasks.
    Assumes ee.Authenticate() has been run and user has access to the gcs_project.
    Args:
      ee_image: earth engine image to export
      config: dictionary with parameter:values including GCS settings
        gcs_bucket, gcs_folder, gcs_output for name prefix for the image.
        if 'ee_bounds' is provided, the image only for the region is exported.
    Returns
      task for the image.
      Once complete, the GCS folder will have multiple files with the name prefix.
    '''
    # Get the image region to export.
    region_bbox = None
    bbox_coords = None
    if config.get('ee_bounds'):
        bbox_coords = _get_bbox_coordinates(config['ee_bounds'])
        region_bbox = ee.Geometry.BBox(**bbox_coords)
    file_prefix = config.get('gcs_output')
    if not file_prefix:
        # Create name from config parameters.
        img_config = [
            ('ee_image',
             config.get(
                 'ee_dataset',
                 config.get('ee_image',
                            config.get('ee_image_collection', 'ee_image'))))
        ]
        img_config.append(('band', config.get('band', '')))
        reducers = config.get('ee_reducer')
        if reducers:
            img_config.append(('r', str(reducers)))
        img_config.append(('mask', config.get('ee_mask', '')))
        img_config.append(('s', str(config.get('scale', ''))))
        img_config.append(('from', config.get('start_date', '')))
        img_config.append(('to', config.get('end_date', '')))
        if bbox_coords:
            img_config.append(
                ('bbox', '_'.join([f'{p:.2f}' for p in bbox_coords.values()])))
        file_prefix = '-'.join(
            '_'.join((p, v)) for p, v in img_config if v and isinstance(v, str))
        file_prefix = re.sub(r'[^A-Za-z0-9_-]', '_', file_prefix)
    scale = config.get('scale', 1000)
    gcs_bucket = config.get('gcs_bucket', '')
    gcs_folder = config.get('gcs_folder', '')
    if gcs_folder and gcs_folder[-1] != '/':
        gcs_folder = gcs_folder + '/'
    logging.info(
        f'Exporting image: {ee_image.id()} to GCS bucket:{gcs_bucket}, {gcs_folder}{file_prefix}'
    )
    task = ee.batch.Export.image.toCloudStorage(
        description=file_prefix[:90],
        image=ee_image,
        region=region_bbox,
        scale=scale,
        bucket=gcs_bucket,
        fileNamePrefix=f'{gcs_folder}{file_prefix}',
        maxPixels=10000000000000,
        fileFormat='GeoTIFF')
    task.start()
    print(f'Created EE task: {task}')
    print(f'Visit https://code.earthengine.google.com/tasks to view status.')
    return task


def ee_process(config) -> list:
    '''Generate earth engine images and export to GCS.
    Called should wait for the task to complete.
    Args:
      config: dictionary with parameter: values.
        For supported params, refer to _DEFAULT_CONFIG.
        if ee_image_count > 1, then multiple images are exported with
        the start_time, end_time advanced by time_period.
    '''
    ee_tasks = []
    ee.Initialize()
    config['ee_image_count'] = config.get('ee_image_count', 1)
    while config['ee_image_count'] > 0:
        logging.info(f'Getting image for config: {config}')
        img = ee_generate_image(config)
        if isinstance(img, ee.ImageCollection):
            # Reduce input image collection to an image.
            img = ee_reduce_image_collection(img, config)
        if img:
            logging.info(f'Generated image {img.get("id")}')
            if config.get('ee_export_image', True):
                task = export_ee_image_to_gcs(img, config)
                ee_tasks.append(task)
        else:
            logging.error(f'Failed to generate image for config: {config}')
        # Advance time to next period.
        time_period = config.get('time_period', 'P1M')
        for ts in ['start_date', 'end_date']:
            dt = _advance_date(config.get(ts, ''), time_period)
            if dt:
                config[ts] = dt
        config['ee_image_count'] = config['ee_image_count'] - 1
        logging.info(f'Advanced dates by {time_period}: {config}')

    # Wait for tasks to complete
    if config.get('ee_wait_task', True):
        pending_tasks = set(ee_tasks)
        while len(pending_tasks) > 0:
            task = pending_tasks.pop()
            if task.active():
                pending_tasks.add(task)
                logging.info(f'Waiting for task: {task}')
                time.sleep(10)
            else:
                task_status = ee.data.getTaskStatus(task.id)
                logging.info(f'EE task completed: {task_status}')


def main(_):
    config = _load_config(_FLAGS.config)
    if config.get('debug', False):
        logging.set_verbosity(2)
    # Authenticate using `earthengine authenticate`
    # ee.Authenticate()
    ee_process(config)


if __name__ == '__main__':
    app.run(main)
