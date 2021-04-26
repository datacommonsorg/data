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
"""

import os
import json

DATA_PATH = 'tmp_raw_data'

all_series = set()
all_categories = set()
all_parent_categories = set()

def explore_file(fp):
    count = 0
    series = set()
    categories = set()
    parent_categories = set()
    for line in fp:
        count += 1
        data = json.loads(line)
        series_id = data.get('series_id', None)
        category_id = data.get('category_id', None)
        parent_category_id = data.get('parent_category_id', None)
        if series_id:
            series.add(series_id)
        if category_id:
            categories.add(category_id)
        if parent_category_id:
            parent_categories.add(parent_category_id)
    all_series.update(series)
    all_categories.update(categories)
    all_parent_categories.update(parent_categories)
    return (len(series), len(categories), len(parent_categories), len(all_series), len(all_categories), len(all_parent_categories))

def main():
    print('subdir,file,series,categories,parent_categories,cumulative_series,cumulative_categories,cumulative_parent_categories')
    for subdir, dirs, files in os.walk(DATA_PATH):
        dirs.sort()
        for file in sorted(files):
            file_path = os.path.join(subdir, file)
            with open(file_path) as fp:
                counts = explore_file(fp)
                counts_csv = ','.join([str(x) for x in counts])
                print(f'{subdir},{file},{counts_csv}')
    print('============================')
    print('ACROSS ALL SETS')
    print(f'# series:\t{len(all_series)}')
    print(f'# categories:\t{len(all_categories)}')
    print(f'# parent categories:\t{len(all_parent_categories)}')

    with open('all_series.txt', 'w+') as fp:
        for s in all_series:
            fp.write(f'{s}\n')

    with open('all_categories.txt', 'w+') as fp:
        for s in all_categories:
            fp.write(f'{s}\n')

    with open('all_parent_categories.txt', 'w+') as fp:
        for s in all_parent_categories:
            fp.write(f'{s}\n')

if __name__ == '__main__':
    main()
