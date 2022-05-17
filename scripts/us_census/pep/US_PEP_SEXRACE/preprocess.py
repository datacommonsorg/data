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
