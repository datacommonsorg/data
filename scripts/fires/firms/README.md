# Global fire events using NASA FIRMS dataset
This folder contains configs to generate global fire events using the fire data
from [NASA Fire Information for Resource Management System
(FIRMS)](https://firms.modaps.eosdis.nasa.gov/).

The active and historical fires can be viewed on the [FIRMS Fire
Map](https://firms.modaps.eosdis.nasa.gov/).

The [NASA API](https://firms.modaps.eosdis.nasa.gov/api/area/) provides the
fires data as a CSV with the location and area of each fire. This is used to
generate fire events by merging regions with fire that are next to each other
within time window.

The [events
pipeline](https://github.com/datacommonsorg/data/blob/master/scripts/earthengine/events_pipeline.py)
script is used with the `fire_events_pipeline_config.py` that downloads the
latest data form source incrementally and generates fire events for the current
year.

To run the script, get an API key from
[NASA](https://firms.modaps.eosdis.nasa.gov/api/area/), add it to the config
`fire_events_pipeline_config.py`, update the GCS project and buckets in the
config or set the `output_file` to a local foldea.
Then run the pipeline with the command:
```
pip install -r requirements.txt
python3 ../../earthengine/events_pipeline.config --pipeline_config=fire_events_pipeline_config.py
```

This generates the following output files:
   - events.{csv,tmcf}: Data for each fire event
   - events-svobs.{csv,tmcf}: StatVarObservations for area of each fire event
   - place-svobs.{csv,tmcf}: StatVarObservations for area and count of fires
     across places
