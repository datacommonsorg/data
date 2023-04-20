import csv
import requests
import os

BATCH = 20

cities = set()
for file in sorted(os.listdir('input')):
    code = file.removesuffix('.csv')
    with open('input/' + file) as f:
        reader = csv.DictReader(f)
        if '[Cities]' in reader.fieldnames:
            for row in reader:
                cities.add(row['[Cities]'].replace('_', ' ').title() + ', ' +
                           row['GeoAreaName'])
cities = sorted(cities)

with open('cities.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['name', 'dcid'])
    writer.writeheader()
    headers = {'X-API-Key': 'AIzaSyCTI4Xz-UW_G2Q2RfknhcfdAnTHq5X5XuI'}
    for i in range(0, len(cities), BATCH):
        json = {
            'entities': [{
                'description': city
            } for city in cities[i:i + BATCH]]
        }
        response = requests.post(
            'https://api.datacommons.org/v1/bulk/find/entities',
            headers=headers,
            json=json).json()
        for entity in response['entities']:
            dcid = entity['dcids'][0] if 'dcids' in entity else ''
            writer.writerow({'name': entity['description'], 'dcid': dcid})