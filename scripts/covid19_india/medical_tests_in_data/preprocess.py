import json
import csv
import urllib.request

# 1. All counts are at India level, so geographic reference code will always be IN
# 2. Only cumulative counts are available at this point

INDIA = "IN"

output_columns = [
  'Date', 'isoCode', 'CumulativeCount_MedicalTest_COVID_19'
]


# Get the data from github.com/datameet/covid19n which scrapes the data
# On daily basis from the ICMR PDFs, get from master

with urllib.request.urlopen("https://raw.githubusercontent.com/datameet/covid19/master/data/icmr_testing_status.json") as response:
    data = json.load(response)
    rows = data["rows"]
    with open('COVID19_tests_india.csv', 'w', newline='') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=output_columns, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            processed_dict = {}
            processed_dict["Date"] = (row["value"]["report_time"])[:10]
            processed_dict["isoCode"] = INDIA
            processed_dict["CumulativeCount_MedicalTest_COVID_19"] = row["value"]["samples"]
            writer.writerow(processed_dict)