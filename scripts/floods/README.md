# Flood events using Earth Engine

This folder contains scripts to generate global flood events using raster data sets
from Earth Engine. The [Dynamic
World](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1)
dataset from Earth Engine is used to find all places classified as water.
The places that are permanently covered in water such as lakes and rivers are
removed using the [land data
set](https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2021_v1_9).

The locations with non-permanent water over a period of a month are considered as flooded regions. The flooded pixels are aggregated into S2 cells of level 10 (roughly 10kmx10km). A flood event is generated combining neighbouring flooded S2 cells over successive months.

The scripts output flooded events starting from Jan of the current year along
with the area and count of floods per S2 cell.
These are aggregated to higher levels to generate flood counts and area for a country.


To generate new flooded events, run the script:
```
python generate_floods_events.py
```

This uses the events pipeline script
[earthengine/events_pipeline.py](https://github.com/datacommonsorg/data/blob/master/scripts/earthengine/events_pipeline.py)
along with the config
[flood_events_pipeline_config.py](https://github.com/datacommonsorg/data/blob/master/scripts/floods/flood_events_pipeline_config.py) for event generation and aggregation to generate the following outputs:
  - flood_events.{csv,tmcf}: Data for flood events
  - flood_event_svobs.{csv,tmcf}: Area and count of floods by flood event
  - flood_place_svobs.{csv,tmcf}: Area and count of flood events by places


