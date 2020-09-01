from WikiParser import get_wiki_id
from typing import Dict
import datacommons as dc


output = []

with open("test.txt", 'r') as f:
    for url in f:
        country = url.split('_medical_cases_chart')[-2]
        country = country.split('pandemic_data/')[-1]
        country = country.split('/')[-1]
        wiki_id = get_wiki_id('https://en.wikipedia.org/wiki/' + country)
        a = dc.get_observations(['country/USA'], 'count', 'measuredValue', '2018-12')
        print(a)
        break

        if wiki_id:
            output.append({'geoId': wiki_id, 'url': url})

with open('WikiIdParserOutput.txt', 'w+') as f:
    f.write(str(output))