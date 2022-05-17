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
'''
This script is used to
run all the national state and
county python script and generate output csv
'''

import os

os.system('python Nationals/national_1900_1970.py')
os.system('python Nationals/national_1980_1990.py')
os.system('python Nationals/national_1990_2000.py')
os.system('python Nationals/national_2000_2010.py')
os.system('python Nationals/national_2010_2020.py')
os.system('python State/state_1970_1979.py')
os.system('python State/state_1980_1990.py')
os.system('python State/state_1990_2000.py')
os.system('python State/state_2000_2010.py')
os.system('python State/state_2010_2020.py')
os.system('python County/county_1970_1979.py')
os.system('python County/county_1980_1989.py')
os.system('python County/county_1990_2000.py')
os.system('python County/county_2000_2009.py')
os.system('python County/county_2010_2020.py')
