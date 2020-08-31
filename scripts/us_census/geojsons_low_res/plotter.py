# Copyright 2020 Google LLC
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
Plots and compares two Geojson files: before and after running simplify.py.

    Typical usage:
    python3 plotter.py --original_path original-data/geoId-01.geojson
                       --simplified_path simplified-data/geoId-01-simple.geojson
"""

from absl import flags
from absl import app
import geopandas as gpd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

_, (ax1, ax2) = plt.subplots(ncols=2, sharex=True, sharey=True)


def compare_plots(geojson1, geojson2, show=True):
    if show:
        _, (new_ax1, new_ax2) = plt.subplots(ncols=2, sharex=True, sharey=True)
        f1 = geojson1.plot(ax=new_ax1)
        f2 = geojson2.plot(ax=new_ax2)
        f1.set_title('Original.')
        f2.set_title('Simplified.')
    else:
        f1 = geojson1.plot(ax=ax1)
        f2 = geojson2.plot(ax=ax2)
        f1.set_title('Original.')
        f2.set_title('Simplified.')

    if show:
        plt.show()


def main(_):
    original = gpd.read_file(FLAGS.original_path)
    simple = gpd.read_file(FLAGS.simplified_path)
    compare_plots(original, simple)


if __name__ == '__main__':
    FLAGS = flags.FLAGS
    flags.DEFINE_string('original_path',
                        default=None,
                        help='Path to original geojson to be compared.')
    flags.DEFINE_string('simplified_path',
                        default=None,
                        help='Path to simplified geojson to be compared.')
    flags.mark_flag_as_required('original_path')
    flags.mark_flag_as_required('simplified_path')
    app.run(main)
