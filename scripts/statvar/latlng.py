import place_resolver
from absl import logging
logging.set_verbosity(2)
pr=place_resolver.PlaceResolver(maps_api_key='AIzaSyBI4cPCd6u4bvax84vwVm647j0HuLtxbU0', counters_dict={}, config_dict={'debug': True})
resp = pr.resolve_latlng({1:{'latitude': 12.0, 'longitude': 76.5}})
print(resp)
